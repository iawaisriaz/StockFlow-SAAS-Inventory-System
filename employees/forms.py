
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()


class EmployeeCreateForm(forms.Form):

    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    password = forms.CharField(
        widget=forms.PasswordInput,
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput,
    )

    def clean_username(self):
        username = self.cleaned_data["username"].strip()

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "This email is already registered."
            )

        return email

    def clean(self):
        cleaned = super().clean()

        password = cleaned.get("password")
        confirm = cleaned.get("confirm_password")

        if password and confirm and password != confirm:
            self.add_error(
                "confirm_password",
                "Passwords do not match.",
            )

        if password:
            candidate = User(
                username=cleaned.get("username", ""),
                email=cleaned.get("email", ""),
                first_name=cleaned.get("first_name", ""),
                last_name=cleaned.get("last_name", ""),
            )

            try:
                validate_password(password, user=candidate)
            except ValidationError as exc:
                self.add_error("password", exc)

        return cleaned


class EmployeeEditForm(forms.Form):

    username = forms.CharField(max_length=150)
    new_password = forms.CharField(
        required=False,
        label="New Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    confirm_new_password = forms.CharField(
        required=False,
        label="Confirm New Password",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField()
    is_active = forms.BooleanField(required=False)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee_user = user

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()

        qs = User.objects.filter(email__iexact=email)

        if self.employee_user:
            qs = qs.exclude(pk=self.employee_user.pk)

        if qs.exists():
            raise forms.ValidationError(
                "This email is already registered."
            )

        return email

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        qs = User.objects.filter(username__iexact=username)
        if self.employee_user is not None:
            qs = qs.exclude(pk=self.employee_user.pk)
        if qs.exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("new_password")
        confirm = cleaned.get("confirm_new_password")
        if password or confirm:
            if not password:
                self.add_error("new_password", "Enter a new password.")
            elif password != confirm:
                self.add_error("confirm_new_password", "Passwords do not match.")
            else:
                candidate = User(
                    username=cleaned.get("username", ""),
                    email=cleaned.get("email", ""),
                    first_name=cleaned.get("first_name", ""),
                    last_name=cleaned.get("last_name", ""),
                )
                try:
                    validate_password(password, user=candidate)
                except ValidationError as exc:
                    self.add_error("new_password", exc)
        return cleaned
