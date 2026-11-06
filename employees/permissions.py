
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404

from accounts.models import BusinessMembership
from accounts.utils import get_current_membership

from .models import EmployeePermission


# ============================================================
# MODULE PERMISSIONS
# ============================================================

MODULE_ACTIONS = {
    "dashboard": ("view",),
    "categories": ("view", "add", "edit", "delete"),
    "products": ("view", "add", "edit", "delete"),
    "suppliers": ("view", "add", "edit", "delete"),
    "purchases": ("view", "add", "edit", "delete"),
    "customers": ("view",),
    "sales": ("view", "add", "delete"),
    "returns": ("view", "add", "delete"),
    "reports": ("view",),
}

MODULES = set(MODULE_ACTIONS.keys())

ACTIONS = ("view", "add", "edit", "delete")


# ============================================================
# MODULE URLS
# ============================================================

MODULE_URLS = {
    "dashboard": "dashboard",
    "categories": "categories:list",
    "products": "products:list",
    "suppliers": "suppliers:list",
    "purchases": "purchases:list",
    "customers": "customers:list",
    "sales": "sales:list",
    "returns": "returns:list",
    "reports": "reports:overview",
}


# ============================================================
# CHECK PERMISSION
# ============================================================

def has_permission(user, module, action="view"):

    # Reject invalid modules and actions.
    if action not in MODULE_ACTIONS.get(module, ()):
        return False

    if not user.is_authenticated or not user.is_active:
        return False

    try:
        membership = get_current_membership(user)

    except PermissionDenied:
        return False

    # Owner has access to all valid actions.
    if membership.role == BusinessMembership.Role.OWNER:
        return True

    # Only employees use assigned permissions.
    if membership.role != BusinessMembership.Role.EMPLOYEE:
        return False

    permission = EmployeePermission.objects.filter(
        membership=membership,
        module=module,
    ).first()

    if permission is None:
        return False

    # Add/Edit/Delete require View permission.
    if not permission.can_view:
        return False

    return bool(
        getattr(permission, f"can_{action}", False)
    )


# ============================================================
# REQUIRE PERMISSION - 403
# ============================================================

def require_permission(user, module, action="view"):

    if not has_permission(user, module, action):
        raise PermissionDenied(
            f"You do not have permission to {action} {module}."
        )

    return True


# ============================================================
# PERMISSION DECORATOR - 403
# ============================================================

def permission_required(module, action="view"):

    def decorator(view_func):

        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):

            require_permission(
                request.user,
                module,
                action,
            )

            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


# ============================================================
# PERMISSION DECORATOR - 404
# ============================================================

def permission_or_404(module, action="view"):

    def decorator(view_func):

        @login_required
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):

            if not has_permission(
                request.user,
                module,
                action,
            ):
                raise Http404("Page not found.")

            return view_func(request, *args, **kwargs)

        return wrapped

    return decorator


# ============================================================
# OWNER ONLY DECORATOR
# ============================================================

def owner_required(view_func):

    @login_required
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):

        membership = get_current_membership(request.user)

        if membership.role != BusinessMembership.Role.OWNER:
            raise PermissionDenied(
                "Only the business owner can access this page."
            )

        return view_func(request, *args, **kwargs)

    return wrapped


# ============================================================
# GET ALLOWED MODULES
# ============================================================

def get_allowed_modules(user):

    if not user.is_authenticated or not user.is_active:
        return set()

    try:
        membership = get_current_membership(user)

    except PermissionDenied:
        return set()

    if membership.role == BusinessMembership.Role.OWNER:
        return MODULES.copy()

    if membership.role != BusinessMembership.Role.EMPLOYEE:
        return set()

    return set(
        EmployeePermission.objects.filter(
            membership=membership,
            can_view=True,
            module__in=MODULES,
        ).values_list("module", flat=True)
    )


# ============================================================
# USER HOME URL
# ============================================================

def get_user_home_url(user):

    membership = get_current_membership(user)

    if membership.role == BusinessMembership.Role.OWNER:
        return "dashboard"

    allowed = get_allowed_modules(user)

    for module, url_name in MODULE_URLS.items():

        if module in allowed:
            return url_name

    return "employees:no_access"
