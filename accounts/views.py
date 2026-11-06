
from django.shortcuts import render, redirect

from django.contrib.auth import (
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetConfirmView,
)
from django.contrib import messages
from django.core.exceptions import PermissionDenied

from django.db import transaction, IntegrityError
from django.db.models.deletion import ProtectedError
from django.views.decorators.http import require_POST
from django.urls import reverse

from .forms import (
    SignupForm,
    PersonalSettingsForm,
    BusinessSettingsForm,
    SecuritySettingsForm,
)
from .models import (
    Business,
    BusinessMembership,
)
from .utils import get_current_membership
from employees.permissions import get_allowed_modules, owner_required


# ============================================================
# SIGNUP
# ============================================================

def signup_view(request):

    if request.user.is_authenticated:
        return redirect(get_user_home_url(request.user))

    if request.method == "POST":
        form = SignupForm(request.POST)

        if form.is_valid():

            try:
                with transaction.atomic():

                    user = form.save()

                    business = Business.objects.create(
                        name=form.cleaned_data["business_name"],
                        email=user.email,
                    )

                    BusinessMembership.objects.create(
                        user=user,
                        business=business,
                        role=BusinessMembership.Role.OWNER,
                    )

            except IntegrityError:
                messages.error(
                    request,
                    "Account could not be created. "
                    "Please check your details and try again.",
                )

            else:
                messages.success(
                    request,
                    "Account created successfully! Please sign in.",
                )

                return redirect("login")

    else:
        form = SignupForm()

    return render(
        request,
        "accounts/signup.html",
        {"form": form},
    )


# ============================================================
# LOGIN
# ============================================================

def get_user_home_url(user):
    """Send an owner to Dashboard and an employee to an allowed page."""
    membership = get_current_membership(user)

    if membership.role == BusinessMembership.Role.OWNER:
        return "dashboard"

    allowed = get_allowed_modules(user)
    destinations = (
        ("dashboard", "dashboard"),
        ("categories", "categories:list"),
        ("products", "products:list"),
        ("suppliers", "suppliers:list"),
        ("purchases", "purchases:list"),
        ("customers", "customers:list"),
        ("sales", "sales:list"),
        ("returns", "returns:list"),
        ("reports", "reports:overview"),
    )

    for module, url_name in destinations:
        if module in allowed:
            return url_name

    return "employees:no_access"


def login_view(request):
    if request.user.is_authenticated:
        try:
            return redirect(get_user_home_url(request.user))
        except PermissionDenied:
            logout(request)
            messages.error(request, "Your business membership is inactive.")
            return redirect("login")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            try:
                destination = get_user_home_url(user)
            except PermissionDenied:
                messages.error(
                    request,
                    "This account does not have an active business "
                    "membership. Contact your business owner.",
                )
            else:
                login(request, user)
                return redirect(destination)
    else:
        form = AuthenticationForm(request)

    return render(request, "accounts/login.html", {"form": form})


# ============================================================
# LOGOUT
# ============================================================

@login_required
def logout_view(request):

    if request.method == "POST":
        logout(request)

    return redirect("landing")


# ============================================================
# SETTINGS
# ============================================================

@login_required
@owner_required
def settings_view(request):

    membership = get_current_membership(
        request.user
    )

    business = membership.business

    is_owner = (
        membership.role
        == BusinessMembership.Role.OWNER
    )

    # Initial forms
    personal_form = PersonalSettingsForm(
        instance=request.user,
        prefix="personal",
    )

    business_form = BusinessSettingsForm(
        instance=business,
        prefix="business",
    )

    security_form = SecuritySettingsForm(
        user=request.user,
        prefix="security",
    )

    if request.method == "POST":

        action = request.POST.get("action")

        # ----------------------------------------------------
        # SAVE PERSONAL + BUSINESS INFORMATION
        # ----------------------------------------------------

        if action == "information":

            personal_form = PersonalSettingsForm(
                request.POST,
                request.FILES,
                instance=request.user,
                prefix="personal",
            )

            if is_owner:

                business_form = BusinessSettingsForm(
                    request.POST,
                    request.FILES,
                    instance=business,
                    prefix="business",
                )

                personal_valid = personal_form.is_valid()
                business_valid = business_form.is_valid()

                if personal_valid and business_valid:

                    with transaction.atomic():
                        personal_form.save()
                        business_form.save()

                    messages.success(
                        request,
                        "Personal and business information "
                        "updated successfully.",
                    )

                    return redirect("settings")

            else:

                # Employees can update personal information,
                # but cannot update shared Business details.
                if personal_form.is_valid():

                    personal_form.save()

                    messages.success(
                        request,
                        "Personal information updated successfully.",
                    )

                    return redirect("settings")

        # ----------------------------------------------------
        # CHANGE PASSWORD
        # ----------------------------------------------------

        elif action == "security":

            security_form = SecuritySettingsForm(
                user=request.user,
                data=request.POST,
                prefix="security",
            )

            if security_form.is_valid():

                user = security_form.save()

                update_session_auth_hash(
                    request,
                    user,
                )

                messages.success(
                    request,
                    "Password changed successfully.",
                )

                return redirect("settings")

        else:
            messages.error(
                request,
                "Invalid settings action.",
            )

    return render(
        request,
        "accounts/settings.html",
        {
            "personal_form": personal_form,
            "business_form": business_form,
            "security_form": security_form,
            "business": business,
            "is_owner": is_owner,
        },
    )


# ============================================================
# DELETE ACCOUNT
# ============================================================

@login_required
@require_POST
def delete_account_view(request):

    membership = get_current_membership(
        request.user
    )

    password = request.POST.get(
        "password",
        "",
    )

    confirmation = request.POST.get(
        "confirmation",
        "",
    )

    if confirmation != "DELETE":

        messages.error(
            request,
            "Type DELETE to confirm account deletion.",
        )

        return redirect("settings")

    if not request.user.check_password(password):

        messages.error(
            request,
            "Incorrect password.",
        )

        return redirect("settings")

    # Employees must be managed by the Owner.
    # Their User records can be referenced by
    # Sales and Returns for audit purposes.
    if membership.role != BusinessMembership.Role.OWNER:

        messages.error(
            request,
            "Employee accounts cannot be deleted here. "
            "Contact the business owner.",
        )

        return redirect("settings")

    business = membership.business

    # Do not delete a business with other memberships.
    # Inactive memberships count too.
    other_members_exist = (
        BusinessMembership.objects.filter(
            business=business,
        )
        .exclude(
            user=request.user,
        )
        .exists()
    )

    if other_members_exist:

        messages.error(
            request,
            "This business has staff records. "
            "Remove or resolve staff memberships "
            "before deleting the business.",
        )

        return redirect("settings")

    try:
        with transaction.atomic():

            # Removing the Business cascades to its
            # business-scoped records where configured.
            # Protected references can block deletion.
            business.delete()

            user = request.user
            user.delete()

    except ProtectedError:

        messages.error(
            request,
            "This account cannot be deleted because "
            "protected transaction records exist.",
        )

        return redirect("settings")

    logout(request)

    messages.success(
        request,
        "Your account has been deleted.",
    )

    return redirect("landing")


# ============================================================
# FORGOT PASSWORD
# ============================================================

class StockFlowPasswordResetView(PasswordResetView):

    template_name = "accounts/forgot_password.html"

    email_template_name = (
        "accounts/password_reset_email.html"
    )

    subject_template_name = (
        "accounts/password_reset_subject.txt"
    )

    def get_success_url(self):
        return reverse("forgot_password")

    def form_valid(self, form):

        response = super().form_valid(form)

        self.request.session[
            "password_reset_email_sent"
        ] = True

        return response

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        context["email_sent"] = (
            self.request.session.pop(
                "password_reset_email_sent",
                False,
            )
        )

        return context


# ============================================================
# RESET PASSWORD
# ============================================================

class StockFlowPasswordResetConfirmView(
    PasswordResetConfirmView
):

    template_name = "accounts/reset_password.html"

    def get_success_url(self):
        return reverse("password_reset_complete")

    def form_valid(self, form):

        response = super().form_valid(form)

        self.request.session[
            "password_reset_complete"
        ] = True

        return response


# ============================================================
# PASSWORD RESET COMPLETE
# ============================================================

def stockflow_password_reset_complete(request):

    completed = request.session.pop(
        "password_reset_complete",
        False,
    )

    if not completed:
        return redirect("login")

    return render(
        request,
        "accounts/reset_password.html",
        {
            "reset_complete": True,
        },
    )
