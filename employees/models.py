
from django.db import models


class EmployeePermission(models.Model):

    MODULE_CHOICES = [
        ("dashboard", "Dashboard"),
        ("categories", "Categories"),
        ("products", "Products"),
        ("suppliers", "Suppliers"),
        ("purchases", "Purchases"),
        ("customers", "Customers"),
        ("sales", "Sales"),
        ("returns", "Returns"),
        ("reports", "Reports"),
    ]

    membership = models.ForeignKey(
        "accounts.BusinessMembership",
        on_delete=models.CASCADE,
        related_name="employee_permissions",
    )

    module = models.CharField(
        max_length=30,
        choices=MODULE_CHOICES,
    )

    can_view = models.BooleanField(default=False)
    can_add = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["membership", "module"],
                name="unique_employee_module_permission",
            )
        ]

    def __str__(self):
        return (
            f"{self.membership.user.username}: "
            f"{self.get_module_display()}"
        )
