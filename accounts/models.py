
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser


# ============================================================
# CUSTOM USER
# ============================================================

class User(AbstractUser):

    email = models.EmailField(
        unique=True
    )

    profile_photo = models.ImageField(
        upload_to="profiles/",
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.username


# ============================================================
# BUSINESS
# ============================================================

class Business(models.Model):

    name = models.CharField(
        max_length=150
    )

    email = models.EmailField(
        blank=True
    )

    address = models.TextField(
        blank=True
    )

    logo = models.ImageField(
        upload_to="businesses/",
        blank=True,
        null=True,
    )

    timezone = models.CharField(
        max_length=64,
        default="Europe/London",
    )

    currency = models.CharField(
        max_length=3,
        default="GBP",
    )

    exchange_rate = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        default=1,
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name


# ============================================================
# BUSINESS MEMBERSHIP
# ============================================================

class BusinessMembership(models.Model):

    class Role(models.TextChoices):
        OWNER = "OWNER", "Owner"
        EMPLOYEE = "EMPLOYEE", "Employee"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="business_memberships",
    )

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="memberships",
    )

    role = models.CharField(
        max_length=10,
        choices=Role.choices,
    )

    is_active = models.BooleanField(
        default=True
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "business"],
                name="unique_user_business_membership",
            )
        ]

    def __str__(self):
        return (
            f"{self.user.username} - "
            f"{self.business.name} ({self.role})"
        )
