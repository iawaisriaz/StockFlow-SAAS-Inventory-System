
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.utils import get_current_business
from products.models import Product
from customers.services import resolve_customer

from .models import Sale, SaleItem


# ============================================================
# FIELD CONFIGURATION
# ============================================================

STOCK_FIELD = "stock_quantity"
PRICE_FIELD = "selling_price"
COST_FIELD = "average_cost"
NAME_FIELD = "name"

CENT = Decimal("0.01")
VALUE_PRECISION = Decimal("0.0001")
COST_PRECISION = Decimal("0.000001")


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
# DISCOUNT CALCULATION
# ============================================================

def calculate_discount(
    subtotal,
    discount_type,
    discount_value,
):
    value = money(discount_value)

    if value < 0:
        raise ValidationError(
            "Discount cannot be negative."
        )

    if discount_type == "percent":

        if value > 100:
            raise ValidationError(
                "Percentage discount cannot exceed 100%."
            )

        discount = money(
            subtotal * value / Decimal("100")
        )

    elif discount_type == "fixed":
        discount = value

    else:
        raise ValidationError(
            "Invalid discount type."
        )

    if discount > subtotal:
        raise ValidationError(
            "Discount cannot exceed subtotal."
        )

    return discount


# ============================================================
# SALE ITEMS VALIDATION
# ============================================================

def parse_items(items):

    if not isinstance(items, list) or not items:
        raise ValidationError(
            "Please add at least one product."
        )

    quantities = {}

    for item in items:

        if not isinstance(item, dict):
            raise ValidationError(
                "Invalid sale item."
            )

        try:
            raw_id = item["product_id"]
            raw_quantity = item["quantity"]

            if (
                isinstance(raw_id, bool)
                or isinstance(raw_quantity, bool)
            ):
                raise ValueError

            product_id = int(raw_id)
            quantity = int(raw_quantity)

            if str(raw_id) != str(product_id):
                raise ValueError

            if str(raw_quantity) != str(quantity):
                raise ValueError

        except (
            KeyError,
            TypeError,
            ValueError,
            OverflowError,
        ):
            raise ValidationError(
                "Invalid product or quantity."
            )

        if product_id <= 0 or quantity <= 0:
            raise ValidationError(
                "Quantity must be a positive integer."
            )

        quantities[product_id] = (
            quantities.get(product_id, 0)
            + quantity
        )

    return quantities


# ============================================================
# CREATE SALE
# ============================================================

@transaction.atomic
def create_sale(*, user, data, items):

    business = get_current_business(user)

    # STEP 1: VALIDATE SALE ITEMS
    quantities = parse_items(items)

    # STEP 2: LOCK PRODUCTS OF CURRENT BUSINESS
    products = list(
        Product.objects.select_for_update()
        .filter(
            business=business,
            pk__in=quantities.keys(),
        )
        .order_by("pk")
    )

    if len(products) != len(quantities):
        raise ValidationError(
            "One or more products are unavailable."
        )

    # STEP 3: CHECK STOCK AND PREPARE ITEMS
    subtotal = Decimal("0.00")
    prepared = []

    for product in products:

        quantity = quantities[product.pk]

        if product.stock_quantity < quantity:
            raise ValidationError(
                f"Insufficient stock for {product.name}. "
                f"Available: {product.stock_quantity}"
            )

        price = money(product.selling_price)

        cost = Decimal(
            product.average_cost or 0
        )

        if price < 0 or cost < 0:
            raise ValidationError(
                "Invalid product price or cost."
            )

        line_total = money(
            price * quantity
        )

        subtotal += line_total

        prepared.append({
            "product": product,
            "quantity": quantity,
            "price": price,
            "cost": cost,
            "line_total": line_total,
        })

    subtotal = money(subtotal)

    # STEP 4: CALCULATE DISCOUNT AND TOTAL
    discount = calculate_discount(
        subtotal,
        data.get("discount_type", "fixed"),
        data.get(
            "discount_value",
            data.get("discount", 0),
        ),
    )

    total = money(
        subtotal - discount
    )

    received = money(
        data.get("amount_received", 0)
    )

    if received < total:
        raise ValidationError(
            "Amount received is less than the grand total."
        )

    # STEP 5: VALIDATE PAYMENT METHOD
    payment_method = data.get(
        "payment_method",
        "cash",
    )

    if payment_method not in (
        "cash",
        "card",
        "bank",
    ):
        raise ValidationError(
            "Invalid payment method."
        )

    # STEP 6: CUSTOMER TRACKING
    customer_name = (
        data.get("customer_name") or ""
    ).strip()

    customer_phone = (
        data.get("customer_phone") or ""
    ).strip()

    customer = resolve_customer(
        business=business,
        name=customer_name,
        phone=customer_phone,
    )

    # STEP 7: CREATE SALE
    sale = Sale.objects.create(
        business=business,
        customer=customer,
        customer_name=customer_name,
        customer_phone=customer_phone,
        subtotal=subtotal,
        discount=discount,
        total=total,
        amount_received=received,
        payment_method=payment_method,
        created_by=user,
        status="completed",
    )

    sale.reference = f"SAL-{sale.pk:05d}"

    sale.save(
        update_fields=["reference"]
    )

    # STEP 8: CREATE ITEMS AND DECREASE STOCK
    for entry in prepared:

        product = entry["product"]
        quantity = entry["quantity"]

        # SaleItem stores a 2-decimal cost snapshot.
        stored_cost = money(
            entry["cost"]
        )

        SaleItem.objects.create(
            sale=sale,
            product=product,
            product_name=product.name,
            quantity=quantity,
            unit_price=entry["price"],
            cost_price=stored_cost,
            line_total=entry["line_total"],
        )

        old_stock = product.stock_quantity
        new_stock = old_stock - quantity

        # Weighted average inventory deduction
        if new_stock == 0:
            new_value = Decimal("0.0000")

        else:
            deduction = (
                Decimal(product.inventory_value)
                * Decimal(quantity)
                / Decimal(old_stock)
            ).quantize(
                VALUE_PRECISION,
                rounding=ROUND_HALF_UP,
            )

            new_value = (
                Decimal(product.inventory_value)
                - deduction
            ).quantize(
                VALUE_PRECISION
            )

        product.stock_quantity = new_stock
        product.inventory_value = new_value

        # Recalculate average cost
        if new_stock:
            product.average_cost = (
                new_value / Decimal(new_stock)
            ).quantize(
                COST_PRECISION,
                rounding=ROUND_HALF_UP,
            )

        else:
            product.average_cost = Decimal(
                "0.000000"
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

    return sale


# ============================================================
# CANCEL SALE
# ============================================================

@transaction.atomic
def cancel_sale(sale_id, *, business):

    # STEP 1: LOCK SALE WITH BUSINESS CHECK
    sale = (
        Sale.objects.select_for_update()
        .get(
            pk=sale_id,
            business=business,
        )
    )

    # STEP 2: PREVENT CANCELLATION AFTER RETURNS
    if sale.returns.exists():
        raise ValidationError(
            "This sale has processed returns. "
            "It cannot be cancelled using normal cancellation."
        )

    # STEP 3: VALIDATE STATUS
    if sale.status == "cancelled":
        raise ValidationError(
            "This sale is already cancelled."
        )

    if sale.status != "completed":
        raise ValidationError(
            "This sale cannot be cancelled."
        )

    # STEP 4: GET SALE ITEMS
    items = list(
        sale.items.all()
    )

    product_ids = sorted({
        item.product_id
        for item in items
    })

    # STEP 5: LOCK PRODUCTS OF SAME BUSINESS
    products = {
        product.pk: product
        for product in (
            Product.objects.select_for_update()
            .filter(
                business=business,
                pk__in=product_ids,
            )
            .order_by("pk")
        )
    }

    if len(products) != len(product_ids):
        raise ValidationError(
            "A sale product could not be found."
        )

    # STEP 6: RESTORE STOCK
    for item in items:

        product = products[item.product_id]

        # Restore using recorded sale cost.
        # This is not an exact historical rollback.
        restored_value = (
            Decimal(item.cost_price)
            * Decimal(item.quantity)
        ).quantize(
            VALUE_PRECISION,
            rounding=ROUND_HALF_UP,
        )

        product.stock_quantity += item.quantity

        product.inventory_value = (
            Decimal(product.inventory_value)
            + restored_value
        ).quantize(
            VALUE_PRECISION
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

    # STEP 7: MARK SALE AS CANCELLED
    sale.status = "cancelled"
    sale.cancelled_at = timezone.now()

    sale.save(
        update_fields=[
            "status",
            "cancelled_at",
        ]
    )

    return sale


# ============================================================
# DELETE CANCELLED SALE
# ============================================================

@transaction.atomic
def delete_cancelled_sale(sale_id, *, business):

    # STEP 1: LOCK SALE WITH BUSINESS CHECK
    sale = (
        Sale.objects.select_for_update()
        .get(
            pk=sale_id,
            business=business,
        )
    )

    # STEP 2: VALIDATE STATUS
    if sale.status != "cancelled":
        raise ValidationError(
            "To delete this sale, please cancel it first."
        )

    if sale.returns.exists():
        raise ValidationError(
            "A sale with processed returns "
            "cannot be deleted."
        )

    # STEP 3: SAVE REFERENCE AND CUSTOMER
    reference = sale.reference
    customer_id = sale.customer_id
    business_id = sale.business_id

    # STEP 4: DELETE SALE
    sale.delete()

    # STEP 5: CLEAN UP CUSTOMER
    if customer_id:

        from customers.models import Customer

        customer = (
            Customer.objects.select_for_update()
            .filter(
                pk=customer_id,
                business_id=business_id,
            )
            .first()
        )

        if customer and not customer.sales.exists():
            customer.delete()

    return reference
