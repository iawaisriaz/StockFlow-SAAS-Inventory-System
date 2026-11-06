
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class SalesReturn(models.Model):
    RETURN_TYPES = [
        ("with_receipt", "With Receipt"),
        ("without_receipt", "Without Receipt"),
    ]

    REASONS = [
        ("damaged", "Damaged Product"),
        ("not_needed", "Changed Mind"),
        ("wrong_item", "Wrong Item"),
        ("other", "Other"),
        # Legacy choices retained for existing records.
        ("defective", "Defective Product"),
        ("wrong_model", "Wrong Size / Model"),
        ("not_described", "Not as Described"),
        ("quality", "Quality Issue"),
        ("duplicate", "Duplicate Purchase"),
    ]

    return_type = models.CharField(
        max_length=20,
        choices=RETURN_TYPES,
        default="with_receipt",
    )

    sale = models.ForeignKey(
        "sales.Sale",
        on_delete=models.PROTECT,
        related_name="returns",
        null=True,
        blank=True,
    )


    business = models.ForeignKey(
    "accounts.Business",
    on_delete=models.CASCADE,
    related_name="sales_returns",
)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_returns",
    )

    reference = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
    )

    customer_name = models.CharField(
        max_length=150,
        blank=True,
    )

    customer_phone = models.CharField(
        max_length=30,
        blank=True,
    )

    reason = models.CharField(
        max_length=30,
        choices=REASONS,
    )

    notes = models.TextField(
        blank=True,
        max_length=1000,
    )

    refund_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
    )

    is_voided = models.BooleanField(
        default=False,
        db_index=True,
    )

    voided_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.reference or f"Return #{self.pk}"

    @property
    def is_active(self):
        return not self.is_voided


class ReturnItem(models.Model):
    CONDITIONS = [
        ("resellable", "Good - Restock"),
        ("damaged", "Damaged - No Restock"),
    ]

    sales_return = models.ForeignKey(
        SalesReturn,
        on_delete=models.CASCADE,
        related_name="items",
    )

    sale_item = models.ForeignKey(
        "sales.SaleItem",
        on_delete=models.PROTECT,
        related_name="return_items",
        null=True,
        blank=True,
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="return_items",
        null=True,
        blank=True,
    )

    product_name = models.CharField(
        max_length=255,
        blank=True,
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    condition = models.CharField(
        max_length=15,
        choices=CONDITIONS,
    )

    refund_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    unit_cost_snapshot = models.DecimalField(
        max_digits=16,
        decimal_places=6,
        default=Decimal("0.000000"),
    )

    def __str__(self):
        name = self.product_name

        if not name and self.sale_item_id:
            name = self.sale_item.product_name

        if not name and self.product_id:
            name = self.product.name

        return f"{name or 'Product'} x {self.quantity}"
