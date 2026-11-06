from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Product(models.Model):

    business = models.ForeignKey(
    "accounts.Business",
    on_delete=models.CASCADE,
    related_name="products",
)

    category = models.ForeignKey(
        "categories.Category",
        on_delete=models.PROTECT,
        related_name="products"
    )

    name = models.CharField(max_length=150)
    sku = models.CharField(max_length=50)

    description = models.TextField(
        blank=True,
        max_length=1000
    )

    # Current/latest cost.
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Moving weighted-average cost.
    average_cost = models.DecimalField(
        max_digits=16,
        decimal_places=6,
        default=Decimal("0.000000"),
        validators=[MinValueValidator(0)],
    )

    # Inventory value is stored separately
    # to avoid repeated rounding.
    inventory_value = models.DecimalField(
        max_digits=20,
        decimal_places=4,
        default=Decimal("0.0000"),
        validators=[MinValueValidator(0)],
    )

    # Incremented for each inventory/cost state change.
    inventory_revision = models.PositiveBigIntegerField(default=0)

    # Cost before the most recent change.
    previous_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)]
    )

    cost_review_required = models.BooleanField(
        default=False
    )

    cost_changed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    selling_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    stock_quantity = models.PositiveIntegerField(
        default=0
    )

    low_stock_threshold = models.PositiveIntegerField(
        default=5
    )

    image = models.ImageField(
        upload_to="products/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

        constraints = [
            models.UniqueConstraint(
    fields=["business", "sku"],
    name="unique_product_sku_per_business",
)
        ]

    def __str__(self):
        return self.name

    @property
    def stock_status(self):
        if self.stock_quantity == 0:
            return "out_of_stock"

        if self.stock_quantity <= self.low_stock_threshold:
            return "low_stock"

        return "in_stock"

    @property
    def cost_change_type(self):
        if self.previous_cost is None:
            return "none"

        if self.cost_price > self.previous_cost:
            return "increased"

        if self.cost_price < self.previous_cost:
            return "decreased"

        return "unchanged"

    def apply_latest_cost(self, new_cost):
        """
        Update the latest product cost.

        Used by the Purchases app when a
        purchase is marked as Received.

        Caller must use transaction.atomic()
        and select_for_update().
        """

        new_cost = Decimal(str(new_cost))

        if not new_cost.is_finite() or new_cost < 0:
            raise ValueError("Invalid product cost.")

        if new_cost > Decimal("99999999.99"):
            raise ValueError(
                "Product cost is too large."
            )

        new_cost = new_cost.quantize(
            Decimal("0.01")
        )

        if self.cost_price == new_cost:
            return False

        self.previous_cost = self.cost_price
        self.cost_price = new_cost
        self.cost_review_required = True
        self.cost_changed_at = timezone.now()
        self.inventory_revision += 1

        self.save(
            update_fields=[
                "previous_cost",
                "cost_price",
                "cost_review_required",
                "cost_changed_at",
                "inventory_revision",
                "updated_at",
            ]
        )

        return True

    def recalculate_average(self):
        """
        Recalculate average cost from
        current inventory value and stock.
        """

        if self.stock_quantity:
            self.average_cost = (
                self.inventory_value
                / Decimal(self.stock_quantity)
            ).quantize(
                Decimal("0.000001")
            )
        else:
            self.inventory_value = Decimal("0.0000")
            self.average_cost = Decimal("0.000000")

    def receive_stock(self, quantity, unit_cost):
        """Apply one receipt to a locked product inside transaction.atomic()."""
        quantity = int(quantity)
        unit_cost = Decimal(str(unit_cost))
        if quantity <= 0 or not unit_cost.is_finite() or unit_cost < 0:
            raise ValueError("Invalid stock receipt.")
        if unit_cost > Decimal("99999999.99"):
            raise ValueError("Product cost is too large.")
        unit_cost = unit_cost.quantize(Decimal("0.01"))
        if self.stock_quantity + quantity > 2147483647:
            raise ValueError("Stock quantity exceeds supported limit.")

        self.inventory_value += Decimal(quantity) * unit_cost
        self.stock_quantity += quantity
        self.recalculate_average()
        if self.cost_price != unit_cost:
            self.previous_cost = self.cost_price
            self.cost_price = unit_cost
            self.cost_review_required = True
            self.cost_changed_at = timezone.now()
        self.inventory_revision += 1
        self.save(update_fields=[
            "stock_quantity", "inventory_value", "average_cost",
            "cost_price", "previous_cost", "cost_review_required",
            "cost_changed_at", "inventory_revision", "updated_at",
        ])

    def restore_receipt_snapshot(self, item):
        """Restore exact pre-receipt state; caller must lock row and check revision."""
        if item.receipt_revision_after is None:
            raise ValueError("Legacy receipt has no reversal snapshot.")
        if self.inventory_revision != item.receipt_revision_after:
            raise ValueError(
                "Later inventory/cost changes exist. Reverse those first "
                "or reconcile manually."
            )
        self.stock_quantity = item.stock_before
        self.inventory_value = item.inventory_value_before
        self.average_cost = item.average_cost_before
        self.cost_price = item.cost_before
        self.previous_cost = item.previous_cost_before
        self.cost_review_required = item.cost_review_before
        self.cost_changed_at = item.cost_changed_at_before
        self.inventory_revision = item.receipt_revision_before
        self.save(update_fields=[
            "stock_quantity", "inventory_value", "average_cost",
            "cost_price", "previous_cost", "cost_review_required",
            "cost_changed_at", "inventory_revision", "updated_at",
        ])


# ============================================================
# STOCK MOVEMENT HISTORY
# ============================================================

class StockMovement(models.Model):

    MOVEMENT_TYPES = [
        ("opening", "Opening Stock"),
        ("purchase", "Purchase Received"),
        ("sale", "Sale"),
        ("sale_cancel", "Sale Cancellation"),
        ("return", "Customer Return"),
        ("return_void", "Return Voided"),
        ("purchase_reverse", "Purchase Reversal"),
        ("adjustment", "Stock Adjustment"),
    ]

    business = models.ForeignKey(
        "accounts.Business",
        on_delete=models.CASCADE,
        related_name="stock_movements",
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="stock_movements",
    )

    movement_type = models.CharField(
        max_length=30,
        choices=MOVEMENT_TYPES,
        db_index=True,
    )

    quantity_change = models.IntegerField()

    stock_before = models.PositiveIntegerField()

    stock_after = models.PositiveIntegerField()

    reference = models.CharField(
        max_length=100,
        blank=True,
        default="",
    )

    notes = models.TextField(
        blank=True,
        default="",
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return (
            f"{self.product.name} | "
            f"{self.get_movement_type_display()} | "
            f"{self.quantity_change:+d}"
        )