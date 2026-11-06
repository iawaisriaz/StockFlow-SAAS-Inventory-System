
from django.core.exceptions import PermissionDenied

from accounts.models import BusinessMembership
from accounts.utils import get_current_membership

from .permissions import get_allowed_modules


def employee_access(request):

    context = {
        "allowed_modules": set(),
        "is_business_owner": False,
        "is_employee": False,
        "employee_has_access": False,
    }

    if not request.user.is_authenticated:
        return context

    try:
        membership = get_current_membership(
            request.user
        )

    except PermissionDenied:
        return context

    is_owner = (
        membership.role
        == BusinessMembership.Role.OWNER
    )

    allowed = get_allowed_modules(
        request.user
    )

    context.update({
        "allowed_modules": allowed,
        "is_business_owner": is_owner,
        "is_employee": (
            membership.role
            == BusinessMembership.Role.EMPLOYEE
        ),
        "employee_has_access": bool(allowed),
    })

    return context
