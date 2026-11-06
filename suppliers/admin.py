
from django.contrib import admin

from .models import Supplier


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "business",
        "contact_person",
        "email",
        "phone",
        "is_active",
        "created_at",
    )

    list_filter = (
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "contact_person",
        "email",
        "phone",
        "business__name",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )
