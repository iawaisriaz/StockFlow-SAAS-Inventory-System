
from django.conf import settings
from django.db import models
from django.db.models import Q


class Customer(models.Model):
    business = models.ForeignKey(
    "accounts.Business",
    on_delete=models.CASCADE,
    related_name="customers",
)

    name = models.CharField(
        max_length=150,
        blank=True,
        default="",
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
        default="",
    )

    normalized_phone = models.CharField(
        max_length=30,
        blank=True,
        default="",
        db_index=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.CheckConstraint(
                condition=~(
                    Q(name="") & Q(phone="")
                ),
                name="customer_requires_name_or_phone",
            )
        ]

    @property
    def display_name(self):
        return self.name or "Unknown Customer"

    @property
    def customer_code(self):
        return f"CUS-{self.pk:05d}"

    def __str__(self):
        return f"{self.display_name} - {self.phone or self.customer_code}"
