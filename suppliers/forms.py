
from django import forms

from products.models import Product

from .models import Supplier


class SupplierForm(forms.ModelForm):

    is_active = forms.TypedChoiceField(
        choices=(
            ("true", "Active"),
            ("false", "Inactive"),
        ),
        coerce=lambda value: value == "true",
        empty_value=True,
        required=True,
    )

    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.none(),
        required=False,
    )

    class Meta:
        model = Supplier

        fields = [
            "name",
            "contact_person",
            "email",
            "phone",
            "address",
            "city",
            "country",
            "is_active",
            "notes",
            "products",
        ]

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.business = business

        self.fields["products"].queryset = (
            Product.objects.filter(
                business=business
            ).order_by("name", "sku")
            if business is not None
            else Product.objects.none()
        )

        if not self.is_bound:
            self.initial["is_active"] = (
                "true" if self.instance.is_active else "false"
            )

            if self.instance.pk:
                self.initial["products"] = list(
                    self.instance.products.filter(
                        business=business
                    ).values_list(
                        "pk",
                        flat=True
                    )
                )

    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        if not name:
            raise forms.ValidationError(
                "Supplier name is required."
            )

        if self.business is None:
            raise forms.ValidationError(
                "Supplier business is required."
            )

        duplicates = Supplier.objects.filter(
            business=self.business,
            name__iexact=name
        )

        if self.instance.pk:
            duplicates = duplicates.exclude(
                pk=self.instance.pk
            )

        if duplicates.exists():
            raise forms.ValidationError(
                "A supplier with this name already exists."
            )

        return name
