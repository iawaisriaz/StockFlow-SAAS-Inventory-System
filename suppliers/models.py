
from django.conf import settings
from django.db import models


class Supplier(models.Model):

    business = models.ForeignKey(
    "accounts.Business",
    on_delete=models.CASCADE,
    related_name="suppliers",
)

    name = models.CharField(max_length=150)

    contact_person = models.CharField(
        max_length=120,
        blank=True
    )

    email = models.EmailField(blank=True)

    phone = models.CharField(
        max_length=30,
        blank=True
    )

    address = models.TextField(
        max_length=500,
        blank=True
    )

    city = models.CharField(
        max_length=100,
        blank=True
    )

    country = models.CharField(
        max_length=100,
        blank=True
    )

    is_active = models.BooleanField(default=True)

    notes = models.TextField(
        max_length=1000,
        blank=True
    )

    products = models.ManyToManyField(
        "products.Product",
        related_name="suppliers",
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

        constraints = [
            models.UniqueConstraint(
    fields=["business", "name"],
    name="unique_supplier_name_per_business",
)
        ]

    def __str__(self):
        return self.name
