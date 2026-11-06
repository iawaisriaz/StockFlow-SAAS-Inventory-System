
from django.contrib import admin

from .models import Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "business",
        "created_at",
    )

    search_fields = (
        "name",
        "business__name",
    )

    list_filter = (
        "created_at",
    )
