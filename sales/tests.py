
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from products.models import Product

from .models import Sale, SaleItem


# ============================================================
# PRODUCT FIELD CONFIGURATION
# ============================================================

# IMPORTANT:
# These field names must match your existing Product model.

STOCK_FIELD = "stock_quantity"
PRICE_FIELD = "sale_price"
COST_FIELD = "average_cost"
NAME_FIELD = "name"

MONEY = Decimal("0.01")


# ============================================================
# MONEY ROUNDING
# ============================================================

def money(value):
    """
    Convert a value to Decimal with 2 decimal places.

    Example:
        12.345 -> 12.35
        15.555 -> 15.56
        20.000 -> 20.00
    """

    try:
        result = Decimal(str(value)).quantize(
            MONEY,
            rounding=ROUND_HALF_UP
        )

    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(
            "Invalid monetary amount."
        )

    if not result.is_finite():
        raise ValidationError(
            "Invalid monetary amount."
        )

    return result


# ============================================================
# CREATE SALE
# ============================================================

def create_sale(*, user, data, items):
    """
    Create a new sale and automatically decrease stock.

    Features:
        - Multiple products
        - Stock validation
        - Automatic stock deduction
        - Average cost snapshot
        - Discount calculation
        - Payment validation
        - Atomic database transaction
    """

    if not items:
        raise ValidationError(
            "Please add at least one product."
        )

    with transaction.atomic():

        # ----------------------------------------------------
        # STEP 1: VALIDATE AND MERGE PRODUCT QUANTITIES
        # ----------------------------------------------------

        quantities = {}

        for item in items:

            try:
                product_id = int(item["product_id"])
                quantity = int(item["quantity"])

            except (KeyError, TypeError, ValueError):
                raise ValidationError(
                    "Invalid product or quantity."
                )

            if product_id <= 0 or quantity <= 0:
                raise ValidationError(
                    "Product quantity must be positive."
                )

            quantities[product_id] = (
                quantities.get(product_id, 0)
                + quantity
            )

        # ----------------------------------------------------
        # STEP 2: LOCK AND FETCH PRODUCTS
        # ----------------------------------------------------

        products = list(
            Product.objects.select_for_update()
            .filter(pk__in=quantities.keys())
            .order_by("pk")
        )

        if len(products) != len(quantities):
            raise ValidationError(
                "One or more products were not found."
            )

        # IMPORTANT:
        # Apply your existing business/account ownership
        # filter here before enabling multi-user sales.

        # ----------------------------------------------------
        # STEP 3: VALIDATE STOCK AND CALCULATE SUBTOTAL
        # ----------------------------------------------------

        subtotal = Decimal("0.00")
        prepared_items = []

        for product in products:

            quantity = quantities[product.pk]

            current_stock = getattr(
                product,
                STOCK_FIELD
            )

            if current_stock < quantity:
                raise ValidationError(
                    f"Insufficient stock for "
                    f"{getattr(product, NAME_FIELD)}. "
                    f"Available: {current_stock}"
                )

            selling_price = money(
                getattr(product, PRICE_FIELD)
            )

            average_cost = money(
                getattr(product, COST_FIELD) or 0
            )

            if selling_price < 0 or average_cost < 0:
                raise ValidationError(
                    "Product price or cost is invalid."
                )

            line_total = money(
                selling_price * quantity
            )

            subtotal += line_total

            prepared_items.append({
                "product": product,
                "quantity": quantity,
                "price": selling_price,
                "cost": average_cost,
                "line_total": line_total,
            })

        # ----------------------------------------------------
        # STEP 4: CALCULATE TOTAL AND VALIDATE PAYMENT
        # ----------------------------------------------------

        discount = money(
            data["discount"]
        )

        amount_received = money(
            data["amount_received"]
        )

        if discount < 0:
            raise ValidationError(
                "Discount cannot be negative."
            )

        if discount > subtotal:
            raise ValidationError(
                "Discount cannot exceed subtotal."
            )

        total = money(
            subtotal - discount
        )

        if amount_received < 0:
            raise ValidationError(
                "Amount received cannot be negative."
            )

        if amount_received < total:
            raise ValidationError(
                "Amount received is less than total."
            )

        # ----------------------------------------------------
        # STEP 5: CREATE SALE
        # ----------------------------------------------------

        sale = Sale.objects.create(
            customer_name=data.get(
                "customer_name", ""
            ),
            customer_phone=data.get(
                "customer_phone", ""
            ),
            subtotal=subtotal,
            discount=discount,
            total=total,
            amount_received=amount_received,
            payment_method=data["payment_method"],
            created_by=user,
            status="completed",
        )

        # Generate unique sale reference.
        sale.reference = f"SAL-{sale.pk:05d}"

        sale.save(
            update_fields=["reference"]
        )

        # ----------------------------------------------------
        # STEP 6: CREATE SALE ITEMS AND DECREASE STOCK
        # ----------------------------------------------------

        for entry in prepared_items:

            product = entry["product"]
            quantity = entry["quantity"]

            SaleItem.objects.create(
                sale=sale,
                product=product,
                product_name=getattr(
                    product,
                    NAME_FIELD
                ),
                quantity=quantity,
                unit_price=entry["price"],
                cost_price=entry["cost"],
                line_total=entry["line_total"],
            )

            current_stock = getattr(
                product,
                STOCK_FIELD
            )

            new_stock = current_stock - quantity

            setattr(
                product,
                STOCK_FIELD,
                new_stock
            )

            product.save(
                update_fields=[STOCK_FIELD]
            )

        # ----------------------------------------------------
        # STEP 7: RETURN COMPLETED SALE
        # ----------------------------------------------------

        return sale


# ============================================================
# CANCEL SALE
# ============================================================

def cancel_sale(sale_id):
    """
    Cancel a completed sale.

    Features:
        - Restore sold product quantities
        - Prevent double cancellation
        - Preserve sale history
        - Atomic database transaction
    """

    with transaction.atomic():

        # ----------------------------------------------------
        # STEP 1: LOCK SALE
        # ----------------------------------------------------

        sale = (
            Sale.objects.select_for_update()
            .get(pk=sale_id)
        )

        if sale.status == "cancelled":
            raise ValidationError(
                "This sale is already cancelled."
            )

        # ----------------------------------------------------
        # STEP 2: FETCH SALE ITEMS
        # ----------------------------------------------------

        items = list(
            sale.items.select_related("product").all()
        )

        product_ids = sorted({
            item.product_id
            for item in items
        })

        # ----------------------------------------------------
        # STEP 3: LOCK PRODUCTS
        # ----------------------------------------------------

        products = {
            product.pk: product
            for product in (
                Product.objects.select_for_update()
                .filter(pk__in=product_ids)
                .order_by("pk")
            )
        }

        if len(products) != len(product_ids):
            raise ValidationError(
                "A sale product could not be found."
            )

        # ----------------------------------------------------
        # STEP 4: RESTORE STOCK
        # ----------------------------------------------------

        for item in items:

            product = products[item.product_id]

            current_stock = getattr(
                product,
                STOCK_FIELD
            )

            restored_stock = (
                current_stock + item.quantity
            )

            setattr(
                product,
                STOCK_FIELD,
                restored_stock
            )

            product.save(
                update_fields=[STOCK_FIELD]
            )

        # ----------------------------------------------------
        # STEP 5: UPDATE SALE STATUS
        # ----------------------------------------------------

        sale.status = "cancelled"
        sale.cancelled_at = timezone.now()

        sale.save(
            update_fields=[
                "status",
                "cancelled_at",
            ]
        )

        return sale
