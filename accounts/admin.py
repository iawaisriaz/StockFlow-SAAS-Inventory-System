
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    User,
    Business,
    BusinessMembership,
)


# ============================================================
# USERS
# ============================================================

@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        "id",
        "username",
        "email",
        "is_active",
        "is_staff",
    )

    search_fields = (
        "username",
        "email",
    )


# ============================================================
# BUSINESSES
# ============================================================

@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "name",
        "email",
        "created_at",
    )

    search_fields = (
        "name",
        "email",
    )


# ============================================================
# BUSINESS MEMBERSHIPS
# ============================================================

@admin.register(BusinessMembership)
class BusinessMembershipAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "user",
        "business",
        "role",
        "is_active",
        "joined_at",
    )

    list_filter = (
        "role",
        "is_active",
    )

    search_fields = (
        "user__username",
        "business__name",
    )
