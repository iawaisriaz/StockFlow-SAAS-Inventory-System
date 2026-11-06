
from django import forms


NEW_REASONS = [
    ("not_needed", "Changed Mind"),
    ("wrong_item", "Wrong Item"),
    ("damaged", "Damaged Product"),
    ("other", "Other"),
]


class ReturnForm(forms.Form):
    sale_id = forms.IntegerField(
        min_value=1,
        required=True,
    )

    reason = forms.ChoiceField(
        choices=NEW_REASONS,
        required=True,
    )

    notes = forms.CharField(
        required=False,
        max_length=1000,
        widget=forms.Textarea,
    )
