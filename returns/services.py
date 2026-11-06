
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from accounts.utils import get_current_business
from products.models import Product
from sales.models import Sale, SaleItem

from .models import SalesReturn, ReturnItem


# ============================================================
# CONSTANTS
# ============================================================

CENT = Decimal("0.01")
VALUE_PRECISION = Decimal("0.0001")
COST_PRECISION = Decimal("0.000001")
MAX_STOCK = 2147483647

VALID_CONDITIONS = {"resellable", "damaged"}

VALID_REASONS = {
    "not_needed",
    "wrong_item",
    "damaged",
    "other",
}


# ============================================================
# MONEY HELPER
# ============================================================

def money(value):
    try:
        result = Decimal(str(value))

        if not result.is_finite():
            raise ValueError

        return result.quantize(
            CENT,
            rounding=ROUND_HALF_UP,
        )

    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(
            "Invalid monetary amount."
        )


# ============================================================
# POSITIVE INTEGER HELPER
# ============================================================

def positive_integer(value, label):

    if isinstance(value, bool):
        raise ValidationError(
            f"Invalid {label}."
        )

    try:
        result = int(value)

        if str(result) != str(value):
            raise ValueError

    except (TypeError, ValueError, OverflowError):
        raise ValidationError(
            f"Invalid {label}."
        )

    if result <= 0:
        raise ValidationError(
            f"{label} must be greater than zero."
        )

    return result


# ============================================================
# VALIDATE RETURN
# ============================================================

def validate_return(reason, notes, items):

    if reason not in VALID_REASONS:
        raise ValidationError(
            "Invalid return reason."
        )

    if len(notes or "") > 1000:
        raise ValidationError(
            "Return notes are too long."
        )

    if not isinstance(items, list) or not items:
        raise ValidationError(
            "Select at least one product to return."
        )

    if len(items) > 100:
        raise ValidationError(
            "Too many products in one return."
        )


# ============================================================
# RETURNED QUANTITY
# ============================================================

def get_returned_quantity(sale_item):

    return (
        ReturnItem.objects.filter(
            sale_item=sale_item,
            sales_return__business_id=(
                sale_item.sale.business_id
            ),
            sales_return__is_voided=False,
        ).aggregate(
            total=Sum("quantity")
        )["total"]
        or 0
    )


def get_remaining_quantity(sale_item):

    return max(
        0,
        sale_item.quantity
        - get_returned_quantity(sale_item),
    )


# ============================================================
# SALE REFUND ALLOCATIONS
# ============================================================

def get_sale_allocations(sale):
    """
    Allocate the original discounted sale total
    across sale items.

    Calculations use pennies so allocated amounts
    always add up to the original sale total.
    """

    items = list(
        sale.items.all().order_by("pk")
    )

    if not items:
        return {}

    total_cents = int(
        money(sale.total) * 100
    )

    weights = [
        Decimal(item.line_total)
        for item in items
    ]

    total_weight = sum(
        weights,
        Decimal("0"),
    )

    if total_weight <= 0:

        if total_cents != 0:
            raise ValidationError(
                "Invalid original sale amounts."
            )

        return {
            item.pk: Decimal("0.00")
            for item in items
        }

    if (
        total_cents < 0
        or any(weight < 0 for weight in weights)
    ):
        raise ValidationError(
            "Invalid original sale amounts."
        )

    base_cents = []
    remainders = []

    for index, weight in enumerate(weights):

        exact = (
            Decimal(total_cents)
            * weight
            / total_weight
        )

        base = int(exact)

        base_cents.append(base)

        remainders.append(
            (exact - base, index)
        )

    remaining = (
        total_cents - sum(base_cents)
    )

    remainders.sort(
        key=lambda entry: (
            -entry[0],
            entry[1],
        )
    )

    for _, index in remainders[:remaining]:
        base_cents[index] += 1

    return {
        item.pk: (
            Decimal(base_cents[index]) / 100
        )
        for index, item in enumerate(items)
    }


# ============================================================
# CUMULATIVE ITEM REFUND
# ============================================================

def cumulative_item_refund(
    allocated_total,
    returned_quantity,
    sold_quantity,
):
    """
    Calculate cumulative refund for one item.

    Final returned unit receives any rounding
    remainder.
    """

    if sold_quantity <= 0:
        raise ValidationError(
            "Invalid original sold quantity."
        )

    if returned_quantity <= 0:
        return Decimal("0.00")

    if returned_quantity >= sold_quantity:
        return money(allocated_total)

    return money(
        Decimal(allocated_total)
        * Decimal(returned_quantity)
        / Decimal(sold_quantity)
    )


# ============================================================
# RESTORE SELLABLE STOCK
# ============================================================

def restore_stock(product, quantity, unit_cost):
    """
    Restore a resellable returned product.

    Caller must already hold a product row lock.
    """

    quantity = positive_integer(
        quantity,
        "Quantity",
    )

    if product.stock_quantity + quantity > MAX_STOCK:
        raise ValidationError(
            f"Stock limit exceeded for {product.name}."
        )

    try:
        cost = Decimal(
            str(unit_cost)
        ).quantize(
            COST_PRECISION,
            rounding=ROUND_HALF_UP,
        )

    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(
            "Invalid inventory cost."
        )

    if not cost.is_finite() or cost < 0:
        raise ValidationError(
            "Invalid inventory cost."
        )

    added_value = (
        cost * Decimal(quantity)
    ).quantize(
        VALUE_PRECISION,
        rounding=ROUND_HALF_UP,
    )

    product.stock_quantity += quantity

    product.inventory_value = (
        Decimal(product.inventory_value)
        + added_value
    ).quantize(
        VALUE_PRECISION,
        rounding=ROUND_HALF_UP,
    )

    product.average_cost = (
        product.inventory_value
        / Decimal(product.stock_quantity)
    ).quantize(
        COST_PRECISION,
        rounding=ROUND_HALF_UP,
    )

    product.inventory_revision += 1

    product.save(
        update_fields=[
            "stock_quantity",
            "inventory_value",
            "average_cost",
            "inventory_revision",
            "updated_at",
        ]
    )


# ============================================================
# CREATE RECEIPT RETURN
# ============================================================

@transaction.atomic
def create_receipt_return(
    *,
    user,
    sale_id,
    reason,
    notes,
    items,
):
    """
    Create a return against a completed Sale.

    Resellable:
        Refund + stock restored.

    Damaged:
        Refund + no sellable stock restoration.

    Refund uses the original discounted Sale total.
    """

    business = get_current_business(user)

    validate_return(
        reason,
        notes,
        items,
    )

    # STEP 1: LOCK SALE OF CURRENT BUSINESS
    sale = (
        Sale.objects.select_for_update()
        .filter(
            pk=sale_id,
            business=business,
            status="completed",
        )
        .first()
    )

    if sale is None:
        raise ValidationError(
            "Completed sale not found."
        )

    # STEP 2: PARSE REQUESTED ITEMS
    requested = {}

    for entry in items:

        if not isinstance(entry, dict):
            raise ValidationError(
                "Invalid return item."
            )

        item_id = positive_integer(
            entry.get("sale_item_id"),
            "Sale item",
        )

        quantity = positive_integer(
            entry.get("quantity"),
            "Quantity",
        )

        condition = entry.get("condition")

        if condition not in VALID_CONDITIONS:
            raise ValidationError(
                "Invalid product condition."
            )

        if item_id in requested:
            raise ValidationError(
                "Duplicate product in return."
            )

        requested[item_id] = {
            "quantity": quantity,
            "condition": condition,
        }

    # STEP 3: VALIDATE SALE ITEMS
    sale_items = list(
        SaleItem.objects.filter(
            sale=sale,
            pk__in=requested.keys(),
        ).order_by("pk")
    )

    if len(sale_items) != len(requested):
        raise ValidationError(
            "One or more products do not belong "
            "to this sale."
        )

    product_ids = sorted({
        item.product_id
        for item in sale_items
    })

    # STEP 4: LOCK PRODUCTS OF CURRENT BUSINESS
    products = {
        product.pk: product
        for product in (
            Product.objects.select_for_update()
            .filter(
                pk__in=product_ids,
                business=business,
            )
            .order_by("pk")
        )
    }

    if len(products) != len(product_ids):
        raise ValidationError(
            "One or more products are unavailable."
        )

    # STEP 5: CALCULATE REFUNDS
    allocations = get_sale_allocations(sale)

    prepared = []
    total_refund = Decimal("0.00")
    restock_quantities = {}

    for sale_item in sale_items:

        data = requested[sale_item.pk]

        quantity = data["quantity"]
        condition = data["condition"]

        already_returned = get_returned_quantity(
            sale_item
        )

        if (
            already_returned + quantity
            > sale_item.quantity
        ):
            raise ValidationError(
                "Return quantity exceeds remaining "
                f"quantity for {sale_item.product_name}."
            )

        allocated = allocations[sale_item.pk]

        refund_before = cumulative_item_refund(
            allocated,
            already_returned,
            sale_item.quantity,
        )

        refund_after = cumulative_item_refund(
            allocated,
            already_returned + quantity,
            sale_item.quantity,
        )

        refund = (
            refund_after - refund_before
        )

        if refund < 0:
            raise ValidationError(
                "Calculated refund cannot be negative."
            )

        product = products[
            sale_item.product_id
        ]

        unit_cost = Decimal(
            sale_item.cost_price
        ).quantize(
            COST_PRECISION,
            rounding=ROUND_HALF_UP,
        )

        prepared.append({
            "sale_item": sale_item,
            "product": product,
            "quantity": quantity,
            "condition": condition,
            "refund": refund,
            "unit_cost": unit_cost,
        })

        total_refund += refund

        if condition == "resellable":
            restock_quantities[product.pk] = (
                restock_quantities.get(
                    product.pk,
                    0,
                )
                + quantity
            )

    # STEP 6: CHECK REFUND LIMIT
    previous_refunds = (
        SalesReturn.objects.filter(
            business=business,
            sale=sale,
            is_voided=False,
        ).aggregate(
            total=Sum("refund_amount")
        )["total"]
        or Decimal("0.00")
    )

    total_refund = money(total_refund)

    if (
        previous_refunds + total_refund
        > sale.total
    ):
        raise ValidationError(
            "Refund exceeds original sale total."
        )

    # STEP 7: CHECK STOCK LIMIT
    for product_id, quantity in restock_quantities.items():

        product = products[product_id]

        if (
            product.stock_quantity + quantity
            > MAX_STOCK
        ):
            raise ValidationError(
                f"Stock limit exceeded for {product.name}."
            )

    # STEP 8: CREATE RETURN
    sales_return = SalesReturn.objects.create(
        business=business,
        return_type="with_receipt",
        sale=sale,
        created_by=user,
        customer_name=sale.customer_name,
        customer_phone=sale.customer_phone,
        reason=reason,
        notes=notes or "",
        refund_amount=total_refund,
        is_voided=False,
    )

    sales_return.reference = (
        f"RET-{sales_return.pk:05d}"
    )

    sales_return.save(
        update_fields=["reference"]
    )

    # STEP 9: RESTORE STOCK AND CREATE RETURN ITEMS
    for entry in prepared:

        product = entry["product"]

        if entry["condition"] == "resellable":
            restore_stock(
                product,
                entry["quantity"],
                entry["unit_cost"],
            )

        ReturnItem.objects.create(
            sales_return=sales_return,
            sale_item=entry["sale_item"],
            product=product,
            product_name=(
                entry["sale_item"].product_name
            ),
            quantity=entry["quantity"],
            condition=entry["condition"],
            refund_amount=entry["refund"],
            unit_cost_snapshot=(
                entry["unit_cost"]
                if entry["condition"] == "resellable"
                else Decimal("0.000000")
            ),
        )

    return sales_return


# ============================================================
# VOID RETURN
# ============================================================

@transaction.atomic
def void_return(*, return_id, business):
    """
    Void a return and reverse resellable
    stock restoration.

    Historical return and refund records
    are kept for audit.

    This does not reverse an actual cash refund.
    """

    # STEP 1: LOCK RETURN OF CURRENT BUSINESS
    sales_return = (
        SalesReturn.objects.select_for_update()
        .filter(
            pk=return_id,
            business=business,
        )
        .first()
    )

    if sales_return is None:
        raise ValidationError(
            "Return not found."
        )

    if sales_return.is_voided:
        raise ValidationError(
            "This return has already been voided."
        )

    # STEP 2: LOCK ORIGINAL SALE
    if sales_return.sale_id:

        sale_exists = (
            Sale.objects.select_for_update()
            .filter(
                pk=sales_return.sale_id,
                business=business,
            )
            .exists()
        )

        if not sale_exists:
            raise ValidationError(
                "Original sale is unavailable."
            )

    # STEP 3: GET RETURN ITEMS
    items = list(
        sales_return.items.select_related(
            "sale_item",
            "product",
        ).order_by("pk")
    )

    restocked = {}

    for item in items:

        if item.condition != "resellable":
            continue

        product_id = item.product_id

        if not product_id and item.sale_item_id:
            product_id = (
                item.sale_item.product_id
            )

        if not product_id:
            raise ValidationError(
                "Returned product could not be identified."
            )

        data = restocked.setdefault(
            product_id,
            {
                "quantity": 0,
                "value": Decimal("0.0000"),
            },
        )

        data["quantity"] += item.quantity

        value = (
            Decimal(item.unit_cost_snapshot)
            * Decimal(item.quantity)
        ).quantize(
            VALUE_PRECISION,
            rounding=ROUND_HALF_UP,
        )

        data["value"] += value

    # STEP 4: LOCK BUSINESS PRODUCTS
    products = {
        product.pk: product
        for product in (
            Product.objects.select_for_update()
            .filter(
                pk__in=sorted(restocked.keys()),
                business=business,
            )
            .order_by("pk")
        )
    }

    if len(products) != len(restocked):
        raise ValidationError(
            "A returned product is unavailable."
        )

    # STEP 5: VALIDATE REVERSAL
    for product_id, data in restocked.items():

        product = products[product_id]

        if product.stock_quantity < data["quantity"]:
            raise ValidationError(
                "Cannot void this return. "
                f"Not enough available stock for {product.name}."
            )

        if (
            Decimal(product.inventory_value)
            < data["value"]
        ):
            raise ValidationError(
                "Cannot reverse inventory value for "
                f"{product.name}. Inventory reconciliation "
                "is required."
            )

    # STEP 6: REVERSE STOCK RESTORATION
    for product_id, data in restocked.items():

        product = products[product_id]

        product.stock_quantity -= data["quantity"]

        product.inventory_value = (
            Decimal(product.inventory_value)
            - data["value"]
        ).quantize(
            VALUE_PRECISION,
            rounding=ROUND_HALF_UP,
        )

        if product.stock_quantity == 0:

            product.inventory_value = Decimal(
                "0.0000"
            )

            product.average_cost = Decimal(
                "0.000000"
            )

        else:

            product.average_cost = (
                product.inventory_value
                / Decimal(product.stock_quantity)
            ).quantize(
                COST_PRECISION,
                rounding=ROUND_HALF_UP,
            )

        product.inventory_revision += 1

        product.save(
            update_fields=[
                "stock_quantity",
                "inventory_value",
                "average_cost",
                "inventory_revision",
                "updated_at",
            ]
        )

    # STEP 7: MARK RETURN VOIDED
    sales_return.is_voided = True
    sales_return.voided_at = timezone.now()

    sales_return.save(
        update_fields=[
            "is_voided",
            "voided_at",
        ]
    )

    return sales_return
