
from django.contrib import admin

from .models import Purchase, PurchaseItem


# ============================================================
# PURCHASE ITEM INLINE
# ============================================================

class PurchaseItemInline(admin.TabularInline):

    model = PurchaseItem
    extra = 0

    readonly_fields = [
        "line_total_display",
    ]

    @admin.display(description="Line Total")
    def line_total_display(self, obj):
        return obj.line_total if obj.pk else "—"


# ============================================================
# PURCHASE ADMIN
# ============================================================

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):

    list_display = [
        "reference",
        "business",
        "supplier",
        "purchase_date",
        "status",
        "total_display",
    ]

    list_filter = [
        "status",
        "purchase_date",
    ]

    search_fields = [
        "reference",
        "supplier__name",
    ]

    inlines = [
        PurchaseItemInline,
    ]

    @admin.display(description="Total")
    def total_display(self, obj):
        return obj.total_amount

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
