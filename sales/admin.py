
from django.contrib import admin

from .models import Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    can_delete = False

    readonly_fields = [
        "product",
        "product_name",
        "quantity",
        "unit_price",
        "cost_price",
        "line_total",
    ]


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):

    list_display = [
        "reference",
        "customer_name",
        "sale_date",
        "total",
        "payment_method",
        "status",
    ]

    list_filter = [
        "status",
        "payment_method",
        "sale_date",
    ]

    search_fields = [
        "reference",
        "customer_name",
    ]

    readonly_fields = [
        "reference",
        "customer_name",
        "customer_phone",
        "sale_date",
        "subtotal",
        "discount",
        "total",
        "amount_received",
        "payment_method",
        "status",
        "created_by",
        "cancelled_at",
        "created_at",
    ]

    inlines = [SaleItemInline]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):

    list_display = [
        "sale",
        "product_name",
        "quantity",
        "unit_price",
        "line_total",
    ]

    readonly_fields = [
        "sale",
        "product",
        "product_name",
        "quantity",
        "unit_price",
        "cost_price",
        "line_total",
    ]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False
