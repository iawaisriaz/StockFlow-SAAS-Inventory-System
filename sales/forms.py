
from decimal import Decimal

from django import forms

from .models import Sale


class SaleForm(forms.Form):
    customer_name = forms.CharField(
        max_length=150,
        required=False,
    )

    customer_phone = forms.CharField(
        max_length=30,
        required=False,
    )

    payment_method = forms.ChoiceField(
        choices=Sale.PAYMENT_CHOICES,
    )

    discount = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
        initial=Decimal("0.00"),
    )

    amount_received = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal("0.00"),
    )

    def clean_customer_name(self):
        return self.cleaned_data["customer_name"].strip()

    def clean_customer_phone(self):
        return self.cleaned_data["customer_phone"].strip()
