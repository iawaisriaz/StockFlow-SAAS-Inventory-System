
from django import forms

from .models import Category


class CategoryForm(forms.ModelForm):

    class Meta:
        model = Category

        fields = [
            "name",
            "description",
        ]

    def __init__(self, *args, business=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.business = business

        self.fields["name"].widget.attrs.update({
            "placeholder": "Enter category name",
        })

        self.fields["description"].widget.attrs.update({
            "placeholder": "Enter category description",
        })

    def clean_name(self):
        name = self.cleaned_data["name"].strip()

        if not name:
            raise forms.ValidationError(
                "Category name is required."
            )

        if self.business is None:
            raise forms.ValidationError(
                "Business is required."
            )

        existing_categories = Category.objects.filter(
            business=self.business,
            name__iexact=name,
        )

        if self.instance.pk:
            existing_categories = existing_categories.exclude(
                pk=self.instance.pk
            )

        if existing_categories.exists():
            raise forms.ValidationError(
                "A category with this name already exists."
            )

        return name
