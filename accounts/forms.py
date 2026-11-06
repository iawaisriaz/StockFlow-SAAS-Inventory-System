
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    UserCreationForm,
    PasswordChangeForm,
)

from .models import Business


User = get_user_model()


# ============================================================
# SIGNUP FORM
# ============================================================

class SignupForm(UserCreationForm):

    email = forms.EmailField(
        required=True
    )

    business_name = forms.CharField(
        max_length=150,
        required=True,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "business_name",
            "password1",
            "password2",
        ]

    def clean_email(self):

        email = (
            self.cleaned_data["email"]
            .strip()
            .lower()
        )

        if User.objects.filter(
            email__iexact=email
        ).exists():
            raise forms.ValidationError(
                "An account with this email already exists."
            )

        return email

    def clean_business_name(self):

        name = self.cleaned_data[
            "business_name"
        ].strip()

        if not name:
            raise forms.ValidationError(
                "Business name is required."
            )

        return name


# ============================================================
# PERSONAL SETTINGS FORM
# ============================================================

class PersonalSettingsForm(forms.ModelForm):

    class Meta:
        model = User
        fields = [
            "profile_photo",
            "first_name",
            "last_name",
            "username",
            "email",
        ]

    def clean_username(self):

        username = (
            self.cleaned_data["username"]
            .strip()
        )

        if User.objects.filter(
            username__iexact=username
        ).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError(
                "This username is already taken."
            )

        return username

    def clean_email(self):

        email = (
            self.cleaned_data["email"]
            .strip()
            .lower()
        )

        if User.objects.filter(
            email__iexact=email
        ).exclude(
            pk=self.instance.pk
        ).exists():
            raise forms.ValidationError(
                "This email is already registered."
            )

        return email

    def clean_profile_photo(self):

        photo = self.cleaned_data.get(
            "profile_photo"
        )

        if photo and hasattr(photo, "size"):
            if photo.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    "Profile photo must not exceed 10 MB."
                )

        return photo


# ============================================================
# BUSINESS SETTINGS FORM
# ============================================================

class BusinessSettingsForm(forms.ModelForm):

    class Meta:
        model = Business
        fields = [
            "logo",
            "name",
            "email",
            "address",
        ]

    def clean_name(self):

        name = self.cleaned_data[
            "name"
        ].strip()

        if not name:
            raise forms.ValidationError(
                "Business name is required."
            )

        return name

    def clean_logo(self):

        logo = self.cleaned_data.get(
            "logo"
        )

        if logo and hasattr(logo, "size"):
            if logo.size > 10 * 1024 * 1024:
                raise forms.ValidationError(
                    "Business logo must not exceed 10 MB."
                )

        return logo


# ============================================================
# CHANGE PASSWORD FORM
# ============================================================

class SecuritySettingsForm(PasswordChangeForm):
    pass
