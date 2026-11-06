
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction, IntegrityError
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import require_POST

from accounts.models import BusinessMembership
from accounts.utils import get_current_business

from .forms import EmployeeCreateForm, EmployeeEditForm
from .models import EmployeePermission
from .permissions import (
    MODULE_ACTIONS,
    get_user_home_url,
    owner_required,
)


User = get_user_model()

ACTIONS = ("view", "add", "edit", "delete")


# ============================================================
# GET EMPLOYEE - CURRENT BUSINESS ONLY
# ============================================================

def get_employee(business, pk):

    return get_object_or_404(
        BusinessMembership.objects.select_related("user"),
        pk=pk,
        business=business,
        role=BusinessMembership.Role.EMPLOYEE,
    )


# ============================================================
# EMPLOYEE LIST
# ============================================================

@owner_required
def employee_list(request):

    business = get_current_business(request.user)

    employees = BusinessMembership.objects.filter(
        business=business,
        role=BusinessMembership.Role.EMPLOYEE,
    ).select_related("user").order_by("-joined_at")

    total = employees.count()

    active = employees.filter(
        is_active=True,
        user__is_active=True,
    ).count()

    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")

    if query:
        employees = employees.filter(
            Q(user__first_name__icontains=query)
            | Q(user__last_name__icontains=query)
            | Q(user__username__icontains=query)
            | Q(user__email__icontains=query)
        )

    if status == "active":
        employees = employees.filter(
            is_active=True,
            user__is_active=True,
        )

    elif status == "inactive":
        employees = employees.exclude(
            is_active=True,
            user__is_active=True,
        )

    return render(
        request,
        "employees/employee_list.html",
        {
            "employees": employees,
            "total_employees": total,
            "active_employees": active,
            "inactive_employees": total - active,
            "query": query,
            "status": status,
        },
    )


# ============================================================
# CREATE EMPLOYEE
# ============================================================

@owner_required
def employee_create(request):

    form = EmployeeCreateForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():

        business = get_current_business(request.user)

        try:
            with transaction.atomic():

                user = User.objects.create_user(
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data["email"],
                    password=form.cleaned_data["password"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    is_active=True,
                )

                BusinessMembership.objects.create(
                    user=user,
                    business=business,
                    role=BusinessMembership.Role.EMPLOYEE,
                    is_active=True,
                )

        except IntegrityError:
            form.add_error(
                None,
                "Employee could not be created. "
                "Please check the username and email.",
            )

        else:
            messages.success(
                request,
                "Employee account created. "
                "No permissions assigned yet.",
            )

            return redirect("employees:list")

    return render(
        request,
        "employees/employee_form.html",
        {
            "form": form,
            "is_edit": False,
        },
    )


# ============================================================
# EDIT EMPLOYEE
# ============================================================

@owner_required
def employee_edit(request, pk):

    business = get_current_business(request.user)
    membership = get_employee(business, pk)
    user = membership.user

    initial = {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "email": user.email,
        "is_active": membership.is_active and user.is_active,
    }

    form = EmployeeEditForm(
        request.POST or None,
        initial=initial,
        user=user,
    )

    if request.method == "POST" and form.is_valid():

        with transaction.atomic():

            user.username = form.cleaned_data["username"]
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.email = form.cleaned_data["email"]
            user.is_active = form.cleaned_data["is_active"]
            if form.cleaned_data.get("new_password"):
                user.set_password(form.cleaned_data["new_password"])
            user.save()

            membership.is_active = form.cleaned_data["is_active"]
            membership.save(update_fields=["is_active"])

        messages.success(
            request,
            "Employee updated successfully.",
        )

        return redirect("employees:list")

    return render(
        request,
        "employees/employee_form.html",
        {
            "form": form,
            "is_edit": True,
            "employee": membership,
        },
    )


# ============================================================
# EMPLOYEE PERMISSIONS
# ============================================================

@owner_required
def employee_permissions(request, pk):

    business = get_current_business(request.user)
    membership = get_employee(business, pk)

    existing = {
        item.module: item
        for item in EmployeePermission.objects.filter(
            membership=membership
        )
    }

    if request.method == "POST":

        with transaction.atomic():

            for module, allowed_actions in MODULE_ACTIONS.items():

                values = {
                    action: (
                        action in allowed_actions
                        and request.POST.get(
                            f"{module}_{action}"
                        ) == "on"
                    )
                    for action in ACTIONS
                }

                # Add/Edit/Delete requires View.
                if any(
                    values[action]
                    for action in ("add", "edit", "delete")
                ):
                    values["view"] = True

                if values["view"]:

                    EmployeePermission.objects.update_or_create(
                        membership=membership,
                        module=module,
                        defaults={
                            "can_view": values["view"],
                            "can_add": values["add"],
                            "can_edit": values["edit"],
                            "can_delete": values["delete"],
                        },
                    )

                else:

                    EmployeePermission.objects.filter(
                        membership=membership,
                        module=module,
                    ).delete()

        messages.success(
            request,
            "Employee permissions updated successfully.",
        )

        return redirect("employees:list")

    permission_rows = []

    for module, label in EmployeePermission.MODULE_CHOICES:

        permission = existing.get(module)
        allowed_actions = MODULE_ACTIONS[module]

        permission_rows.append({
            "key": module,
            "label": label,

            "allow_view": "view" in allowed_actions,
            "allow_add": "add" in allowed_actions,
            "allow_edit": "edit" in allowed_actions,
            "allow_delete": "delete" in allowed_actions,

            "view": bool(
                "view" in allowed_actions
                and permission
                and permission.can_view
            ),
            "add": bool(
                "add" in allowed_actions
                and permission
                and permission.can_add
            ),
            "edit": bool(
                "edit" in allowed_actions
                and permission
                and permission.can_edit
            ),
            "delete": bool(
                "delete" in allowed_actions
                and permission
                and permission.can_delete
            ),
        })

    return render(
        request,
        "employees/employee_permissions.html",
        {
            "employee": membership,
            "permission_rows": permission_rows,
        },
    )


# ============================================================
# DEACTIVATE EMPLOYEE
# ============================================================

@owner_required
@require_POST
def employee_delete(request, pk):

    business = get_current_business(request.user)
    membership = get_employee(business, pk)

    with transaction.atomic():

        membership.is_active = False
        membership.save(update_fields=["is_active"])

        user = membership.user
        user.is_active = False
        user.save(update_fields=["is_active"])

    messages.success(
        request,
        "Employee account deactivated.",
    )

    return redirect("employees:list")


# ============================================================
# NO ACCESS
# ============================================================

@login_required
def no_access(request):

    home_url = get_user_home_url(request.user)

    if home_url != "employees:no_access":
        return redirect(home_url)

    return render(
        request,
        "no_access.html",
    )
