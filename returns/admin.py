
from django.contrib import admin

from .models import SalesReturn, ReturnItem


class ReturnItemInline(admin.TabularInline):
    model = ReturnItem
    extra = 0

    readonly_fields = (
        "sale_item",
        "product",
        "product_name",
        "quantity",
        "condition",
        "refund_amount",
        "unit_cost_snapshot",
    )

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SalesReturn)
class SalesReturnAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "return_type",
        "sale",
        "refund_amount",
        "created_by",
        "created_at",
    )

    list_filter = (
        "return_type",
        "reason",
        "created_at",
    )

    search_fields = (
        "reference",
        "sale__reference",
        "customer_name",
    )

    readonly_fields = (
        "reference",
        "return_type",
        "sale",
        "created_by",
        "customer_name",
        "customer_phone",
        "reason",
        "notes",
        "refund_amount",
        "created_at",
    )

    inlines = [ReturnItemInline]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
