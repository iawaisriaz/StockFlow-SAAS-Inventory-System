from django.conf import settings
from django.db import models


class Category(models.Model):
    business = models.ForeignKey(
    "accounts.Business",
    on_delete=models.CASCADE,
    related_name="categories",
    )

    name = models.CharField(
        max_length=100,
    )

    description = models.TextField(
        max_length=500,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["name"]

        constraints = [
            models.UniqueConstraint(
            fields=["business", "name"],
            name="unique_category_per_business",
        )
        ]

    def __str__(self):
        return self.name