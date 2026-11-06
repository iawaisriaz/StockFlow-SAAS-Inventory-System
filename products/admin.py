
from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "sku",
        "category",
        "business",
        "selling_price",
        "stock_quantity",
        "created_at",
    )

    search_fields = (
        "name",
        "sku",
        "business__name",
    )

    list_filter = (
        "category",
        "created_at",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )
