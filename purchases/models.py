
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Sum, F, DecimalField, ExpressionWrapper
from django.utils import timezone

from suppliers.models import Supplier
from products.models import Product


class Purchase(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_RECEIVED = "received"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_RECEIVED, "Received"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    business = models.ForeignKey(
    "accounts.Business",
    on_delete=models.CASCADE,
    related_name="purchases",
)

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        related_name="purchases",
    )

    reference = models.CharField(
        max_length=30,
        blank=True,
        unique=True,
    )

    purchase_date = models.DateField(
        default=timezone.localdate,
    )

    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
        db_index=True,
    )

    notes = models.TextField(
        blank=True,
        max_length=1000,
    )

    received_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    stock_applied = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.reference or f"Purchase #{self.pk}"

    @property
    def total_amount(self):
        total = self.items.aggregate(
            total=Sum(
                ExpressionWrapper(
                    F("quantity") * F("unit_cost"),
                    output_field=DecimalField(
                        max_digits=16,
                        decimal_places=2,
                    ),
                )
            )
        )["total"]

        return total or Decimal("0.00")


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="purchase_items",
    )

    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    # Snapshot captured immediately before receipt, for safe LIFO reversal.
    stock_before = models.PositiveIntegerField(null=True, blank=True)
    inventory_value_before = models.DecimalField(
        max_digits=20, decimal_places=4, null=True, blank=True
    )
    average_cost_before = models.DecimalField(
        max_digits=16, decimal_places=6, null=True, blank=True
    )
    cost_before = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    previous_cost_before = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    cost_review_before = models.BooleanField(null=True, blank=True)
    cost_changed_at_before = models.DateTimeField(null=True, blank=True)
    receipt_revision_before = models.PositiveBigIntegerField(null=True, blank=True)
    receipt_revision_after = models.PositiveBigIntegerField(null=True, blank=True)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["purchase", "product"],
                name="unique_product_per_purchase",
            )
        ]

    @property
    def line_total(self):
        return self.quantity * self.unit_cost

    def __str__(self):
        return f"{self.product} × {self.quantity}"
