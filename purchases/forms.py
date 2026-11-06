
from django import forms
from django.db.models import Q
from django.forms import BaseInlineFormSet, inlineformset_factory
from django.utils import timezone

from products.models import Product
from suppliers.models import Supplier

from .models import Purchase, PurchaseItem


class PurchaseForm(forms.ModelForm):

    class Meta:
        model = Purchase
        fields = ["supplier", "purchase_date", "notes"]

        widgets = {
            "purchase_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={
                    "type": "date",
                    "class": (
                        "w-full rounded-xl border border-border-light "
                        "bg-white px-4 py-3 text-sm text-dark-green "
                        "outline-none focus:border-primary"
                    ),
                },
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "placeholder": "Additional purchase information...",
                    "class": (
                        "w-full rounded-xl border border-border-light "
                        "bg-white px-4 py-3 text-sm outline-none "
                        "focus:border-primary"
                    ),
                },
            ),
        }

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.business = business

        suppliers = Supplier.objects.none()

        if business is not None:
            suppliers = Supplier.objects.filter(
                business=business,
                is_active=True,
            )

            if self.instance.pk and self.instance.supplier_id:
                suppliers = Supplier.objects.filter(
                    business=business
                ).filter(
                    Q(is_active=True)
                    | Q(pk=self.instance.supplier_id)
                )

        self.fields["supplier"].queryset = suppliers

        today = timezone.localdate()

        self.fields["purchase_date"].widget.attrs["max"] = (
            today.isoformat()
        )

        if not self.is_bound and not self.instance.pk:
            self.fields["purchase_date"].initial = today

    def clean_purchase_date(self):
        value = self.cleaned_data["purchase_date"]

        if value > timezone.localdate():
            raise forms.ValidationError(
                "Purchase date cannot be in the future."
            )

        return value

    def clean_supplier(self):
        supplier = self.cleaned_data["supplier"]

        if self.business is None:
            raise forms.ValidationError(
                "Business is required."
            )

        if supplier.business_id != self.business.pk:
            raise forms.ValidationError(
                "Invalid supplier for this business."
            )

        if not supplier.is_active:
            if not (
                self.instance.pk
                and self.instance.supplier_id == supplier.pk
            ):
                raise forms.ValidationError(
                    "Please select an active supplier."
                )

        return supplier


class BasePurchaseItemFormSet(BaseInlineFormSet):

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.business = business
        self.selected_supplier_id = None

        products = (
            Product.objects.filter(business=business)
            if business is not None
            else Product.objects.none()
        )

        for form in self.forms:
            form.fields["product"].queryset = products

    @property
    def empty_form(self):
        form = super().empty_form

        form.fields["product"].queryset = (
            Product.objects.filter(business=self.business)
            if self.business is not None
            else Product.objects.none()
        )

        return form

    def clean(self):
        super().clean()

        if any(self.errors):
            return

        if self.business is None:
            raise forms.ValidationError(
                "Business is required."
            )

        seen = set()
        count = 0

        if self.selected_supplier_id is None:
            raise forms.ValidationError(
                "Select a supplier first."
            )

        supplier = Supplier.objects.filter(
            pk=self.selected_supplier_id,
            business=self.business,
        ).first()

        if supplier is None:
            raise forms.ValidationError(
                "Invalid supplier selected."
            )

        linked_products = supplier.products.filter(
            business=self.business
        )

        has_linked_products = linked_products.exists()

        for form in self.forms:
            data = form.cleaned_data

            if not data or data.get("DELETE"):
                continue

            product = data.get("product")

            if not product:
                continue

            count += 1

            if product.business_id != self.business.pk:
                raise forms.ValidationError(
                    "Invalid product for this business."
                )

            if product.pk in seen:
                raise forms.ValidationError(
                    "The same product cannot be added twice."
                )

            seen.add(product.pk)

            if has_linked_products:
                if not linked_products.filter(
                    pk=product.pk
                ).exists():
                    raise forms.ValidationError(
                        f"{product.name} is not linked to "
                        "the selected supplier."
                    )

            if (data.get("quantity") or 0) <= 0:
                raise forms.ValidationError(
                    "Quantity must be greater than zero."
                )

            if data.get("unit_cost") is None:
                raise forms.ValidationError(
                    "Unit cost is required."
                )

        if count == 0:
            raise forms.ValidationError(
                "Add at least one product."
            )


PurchaseItemFormSet = inlineformset_factory(
    Purchase,
    PurchaseItem,
    fields=["product", "quantity", "unit_cost"],
    formset=BasePurchaseItemFormSet,
    extra=0,
    min_num=1,
    validate_min=True,
    can_delete=True,
    widgets={
        "quantity": forms.NumberInput(
            attrs={"min": 1, "step": 1}
        ),
        "unit_cost": forms.NumberInput(
            attrs={"min": 0, "step": "0.01"}
        ),
    },
)
