
from django.contrib import admin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):

    list_display = (
        "customer_code",
        "display_name",
        "phone",
        "business",
        "created_at",
    )

    list_filter = (
        "created_at",
    )

    search_fields = (
        "name",
        "phone",
        "normalized_phone",
    )

    readonly_fields = (
        "business",
        "normalized_phone",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False
