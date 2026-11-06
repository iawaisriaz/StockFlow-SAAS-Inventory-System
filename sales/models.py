from decimal import Decimal

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator


class Sale(models.Model):

    STATUS_CHOICES = [
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    PAYMENT_CHOICES = [
        ("cash", "Cash"),
        ("card", "Card"),
        ("bank", "Bank Transfer"),
    ]

    reference = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
    )

    # Optional link to the Customers module.
    customer = models.ForeignKey(
        "customers.Customer",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sales",
    )

    # Keep customer details as sale-time snapshots.
    customer_name = models.CharField(
        max_length=150,
        blank=True,
        default="",
    )

    customer_phone = models.CharField(
        max_length=30,
        blank=True,
        default="",
    )

    sale_date = models.DateTimeField(
        auto_now_add=True,
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
    )

    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    amount_received = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_CHOICES,
        default="cash",
    )

    status = models.CharField(
        max_length=12,
        choices=STATUS_CHOICES,
        default="completed",
    )

    business = models.ForeignKey(
    "accounts.Business",
    on_delete=models.CASCADE,
    related_name="sales",
)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_sales",
    )

    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-sale_date", "-id"]

    def __str__(self):
        return self.reference or f"Sale #{self.pk}"

    @property
    def change_amount(self):
        return max(
            Decimal("0.00"),
            self.amount_received - self.total,
        )

    @property
    def total_profit(self):
        if self.status == "cancelled":
            return Decimal("0.00")

        cost = sum(
            (
                item.cost_price * item.quantity
                for item in self.items.all()
            ),
            Decimal("0.00"),
        )

        return self.total - cost


class SaleItem(models.Model):

    sale = models.ForeignKey(
        Sale,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="sale_items",
    )

    product_name = models.CharField(
        max_length=255,
    )

    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
    )

    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    cost_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
    )

    def __str__(self):
        return f"{self.product_name} x {self.quantity}"
