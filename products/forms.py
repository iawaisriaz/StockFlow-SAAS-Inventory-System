
from django import forms

from categories.models import Category

from .models import Product


class ProductForm(forms.ModelForm):

    remove_image = forms.BooleanField(
        required=False
    )

    class Meta:
        model = Product

        fields = [
            "name",
            "sku",
            "category",
            "description",
            "cost_price",
            "selling_price",
            "stock_quantity",
            "low_stock_threshold",
            "image",
        ]

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.business = business

        self.fields["category"].queryset = (
            Category.objects.filter(
                business=business
            ).order_by("name")
            if business is not None
            else Category.objects.none()
        )

    def clean_sku(self):
        sku = self.cleaned_data["sku"].strip()

        if not sku:
            raise forms.ValidationError(
                "Product SKU is required."
            )

        if self.business is None:
            raise forms.ValidationError(
                "Business is required."
            )

        queryset = Product.objects.filter(
            business=self.business,
            sku__iexact=sku,
        )

        if self.instance.pk:
            queryset = queryset.exclude(
                pk=self.instance.pk
            )

        if queryset.exists():
            raise forms.ValidationError(
                "A product with this SKU already exists."
            )

        return sku

    def clean_image(self):
        image = self.cleaned_data.get("image")

        if not image:
            return image

        # Validate newly uploaded images.
        if hasattr(image, "size"):

            if image.size > 5 * 1024 * 1024:
                raise forms.ValidationError(
                    "Image must not exceed 5 MB."
                )

            allowed_types = [
                "image/jpeg",
                "image/png",
                "image/webp",
            ]

            content_type = getattr(
                image,
                "content_type",
                None
            )

            if content_type and content_type not in allowed_types:
                raise forms.ValidationError(
                    "Only JPG, PNG and WEBP images are allowed."
                )

        return image


class ProductEditForm(ProductForm):
    pass
