
from collections import defaultdict
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from products.models import Product
from .models import Purchase


# =====================================================
# HELPERS
# =====================================================

def _get_locked_purchase(purchase_id, business):
    return Purchase.objects.select_for_update().get(
        pk=purchase_id,
        business=business,
    )


def _get_quantities(purchase):
    quantities = defaultdict(int)

    for item in purchase.items.all():
        quantities[item.product_id] += item.quantity

    return quantities


def _get_locked_products(business, quantities):
    products = {
        product.pk: product
        for product in (
            Product.objects.select_for_update()
            .filter(
                business=business,
                pk__in=quantities.keys(),
            )
            .order_by("pk")
        )
    }

    if len(products) != len(quantities):
        raise ValidationError(
            "One or more products could not be found."
        )

    return products


def _get_newer_purchase(purchase, product_id, business):
    return (
        Purchase.objects.filter(
            business=business,
            status=Purchase.STATUS_RECEIVED,
            stock_applied=True,
            items__product_id=product_id,
            received_at__gt=purchase.received_at,
        )
        .exclude(pk=purchase.pk)
        .order_by("-received_at", "-id")
        .first()
    )


# =====================================================
# VALIDATE PURCHASE REVERSAL
# =====================================================

def _validate_receipt_reversal(
    purchase,
    item,
    product,
    business,
):
    """
    Check whether the purchase can be reversed.
    """

    # 1. Check receipt snapshot
    if (
        item.receipt_revision_before is None
        or item.receipt_revision_after is None
        or item.stock_before is None
        or item.inventory_value_before is None
        or item.average_cost_before is None
        or item.cost_before is None
    ):
        raise ValidationError(
            f"Cannot delete '{product.name}'. "
            "This purchase has an old or incomplete record."
        )

    # 2. Check newer purchases
    newer_purchase = _get_newer_purchase(
        purchase,
        product.pk,
        business,
    )

    if newer_purchase:
        raise ValidationError(
            f"Cannot delete '{product.name}'. "
            f"Delete newer purchase "
            f"{newer_purchase.reference} first."
        )

    # 3. Check stock quantity
    expected_stock = (
        item.stock_before + item.quantity
    )

    if product.stock_quantity != expected_stock:
        raise ValidationError(
            f"Cannot delete '{product.name}'. "
            "Stock quantity has changed since this purchase."
        )

    # 4. Check inventory value
    expected_value = (
        item.inventory_value_before
        + Decimal(item.quantity) * item.unit_cost
    ).quantize(Decimal("0.0001"))

    current_value = product.inventory_value.quantize(
        Decimal("0.0001")
    )

    if current_value != expected_value:
        raise ValidationError(
            f"Cannot delete '{product.name}'. "
            "Inventory value has changed since this purchase."
        )

    # 5. Check latest purchase cost
    expected_cost = item.unit_cost.quantize(
        Decimal("0.01")
    )

    if product.cost_price != expected_cost:
        raise ValidationError(
            f"Cannot delete '{product.name}'. "
            "Purchase cost has changed since this purchase."
        )

    # 6. Check weighted average cost
    if expected_stock > 0:
        expected_average = (
            expected_value / Decimal(expected_stock)
        ).quantize(Decimal("0.000001"))
    else:
        expected_average = Decimal("0.000000")

    if product.average_cost != expected_average:
        raise ValidationError(
            f"Cannot delete '{product.name}'. "
            "Average cost has changed since this purchase."
        )

    # 7. Check inventory revision
    if (
        product.inventory_revision
        != item.receipt_revision_after
    ):
        raise ValidationError(
            f"Cannot delete '{product.name}'. "
            "Product was updated after receiving. "
            "Please check its changes."
        )


# =====================================================
# RECEIVE PURCHASE
# =====================================================

@transaction.atomic
def receive_purchase(purchase_id, business):
    """
    Receive a draft purchase.

    Updates product stock, latest cost,
    inventory value and weighted average cost.

    Saves receipt snapshots for reversal.
    """

    purchase = _get_locked_purchase(
        purchase_id,
        business,
    )

    if purchase.status != Purchase.STATUS_DRAFT:
        raise ValidationError(
            "Only draft purchases can be received."
        )

    if purchase.stock_applied:
        raise ValidationError(
            "This purchase has already been received."
        )

    if purchase.supplier.business_id != business.pk:
        raise ValidationError(
            "Invalid supplier for this business."
        )

    quantities = _get_quantities(purchase)

    if not quantities:
        raise ValidationError(
            "Add at least one product before receiving."
        )

    products = _get_locked_products(
        business,
        quantities,
    )

    items = list(purchase.items.all())

    # Validate supplier-product relationships.
    # Suppliers with no linked products may supply
    # any product belonging to their business.

    linked_product_ids = set(
        purchase.supplier.products.filter(
            business=business
        ).values_list("pk", flat=True)
    )

    if linked_product_ids:
        for item in items:
            product = products[item.product_id]

            if product.pk not in linked_product_ids:
                raise ValidationError(
                    f"'{product.name}' is not linked "
                    "to the selected supplier."
                )

    # Receive products
    for item in items:
        product = products[item.product_id]

        # Save state before receiving
        item.stock_before = product.stock_quantity

        item.inventory_value_before = (
            product.inventory_value
        )

        item.average_cost_before = (
            product.average_cost
        )

        item.cost_before = product.cost_price

        item.previous_cost_before = (
            product.previous_cost
        )

        item.cost_review_before = (
            product.cost_review_required
        )

        item.cost_changed_at_before = (
            product.cost_changed_at
        )

        item.receipt_revision_before = (
            product.inventory_revision
        )

        # Update stock and weighted average cost
        try:
            product.receive_stock(
                item.quantity,
                item.unit_cost,
            )
        except ValueError as exc:
            raise ValidationError(
                str(exc)
            ) from exc

        item.receipt_revision_after = (
            product.inventory_revision
        )

        # Save receipt snapshot
        item.save(
            update_fields=[
                "stock_before",
                "inventory_value_before",
                "average_cost_before",
                "cost_before",
                "previous_cost_before",
                "cost_review_before",
                "cost_changed_at_before",
                "receipt_revision_before",
                "receipt_revision_after",
            ]
        )

    # Update purchase status
    purchase.status = Purchase.STATUS_RECEIVED
    purchase.received_at = timezone.now()
    purchase.stock_applied = True

    purchase.save(
        update_fields=[
            "status",
            "received_at",
            "stock_applied",
            "updated_at",
        ]
    )

    return purchase


# =====================================================
# CANCEL PURCHASE
# =====================================================

@transaction.atomic
def cancel_purchase(purchase_id, business):
    """
    Cancel a draft purchase.
    """

    purchase = _get_locked_purchase(
        purchase_id,
        business,
    )

    if purchase.status == Purchase.STATUS_RECEIVED:
        raise ValidationError(
            "Received purchases cannot be cancelled. "
            "Use Delete & Reverse Stock instead."
        )

    if purchase.status == Purchase.STATUS_CANCELLED:
        raise ValidationError(
            "This purchase is already cancelled."
        )

    if purchase.status != Purchase.STATUS_DRAFT:
        raise ValidationError(
            "Only draft purchases can be cancelled."
        )

    if purchase.stock_applied:
        raise ValidationError(
            "Cannot cancel. Purchase stock needs checking."
        )

    purchase.status = Purchase.STATUS_CANCELLED
    purchase.cancelled_at = timezone.now()
    purchase.stock_applied = False

    purchase.save(
        update_fields=[
            "status",
            "cancelled_at",
            "stock_applied",
            "updated_at",
        ]
    )

    return purchase


# =====================================================
# DELETE PURCHASE
# =====================================================

@transaction.atomic
def delete_purchase(purchase_id, business):
    """
    Delete a purchase.

    Draft/Cancelled:
        Delete without changing stock.

    Received:
        Validate and restore product snapshots.
    """

    purchase = _get_locked_purchase(
        purchase_id,
        business,
    )

    # ---------------------------------------------
    # RECEIVED PURCHASE
    # ---------------------------------------------

    if purchase.status == Purchase.STATUS_RECEIVED:

        if not purchase.stock_applied:
            raise ValidationError(
                "Cannot delete purchase. "
                "Stock records need checking."
            )

        quantities = _get_quantities(purchase)

        if not quantities:
            raise ValidationError(
                "Cannot delete purchase. "
                "No purchase items were found."
            )

        products = _get_locked_products(
            business,
            quantities,
        )

        items = list(purchase.items.all())

        # Validate all items before changing stock
        for item in items:
            product = products[item.product_id]

            _validate_receipt_reversal(
                purchase,
                item,
                product,
                business,
            )

        # Restore previous stock and costs
        for item in items:
            product = products[item.product_id]

            try:
                product.restore_receipt_snapshot(
                    item
                )
            except ValueError as exc:
                raise ValidationError(
                    f"Cannot delete '{product.name}'. "
                    f"{exc}"
                ) from exc

    # ---------------------------------------------
    # DRAFT OR CANCELLED PURCHASE
    # ---------------------------------------------

    elif purchase.status in (
        Purchase.STATUS_DRAFT,
        Purchase.STATUS_CANCELLED,
    ):

        if purchase.stock_applied:
            raise ValidationError(
                "Cannot delete purchase. "
                "Stock records need checking."
            )

    # ---------------------------------------------
    # INVALID STATUS
    # ---------------------------------------------

    else:
        raise ValidationError(
            "Cannot delete purchase. Invalid status."
        )

    # ---------------------------------------------
    # DELETE RECORD
    # ---------------------------------------------

    reference = purchase.reference

    purchase.delete()

    return reference
