
from django.core.exceptions import PermissionDenied

from .models import BusinessMembership


# ============================================================
# CURRENT MEMBERSHIP
# ============================================================

def get_current_membership(user):

    if not user.is_authenticated:
        raise PermissionDenied(
            "Authentication required."
        )

    if not user.is_active:
        raise PermissionDenied(
            "This user account is inactive."
        )

    memberships = list(
        BusinessMembership.objects
        .select_related("business")
        .filter(
            user=user,
            is_active=True,
        )[:2]
    )

    # StockFlow v1: exactly one active business
    if len(memberships) != 1:
        raise PermissionDenied(
            "User must belong to exactly one active business."
        )

    return memberships[0]


# ============================================================
# CURRENT BUSINESS
# ============================================================

def get_current_business(user):

    membership = get_current_membership(user)

    return membership.business


# ============================================================
# OWNER CHECK
# ============================================================

def is_business_owner(user):

    membership = get_current_membership(user)

    return (
        membership.role
        == BusinessMembership.Role.OWNER
    )


def require_business_owner(user):

    membership = get_current_membership(user)

    if membership.role != BusinessMembership.Role.OWNER:
        raise PermissionDenied(
            "Only the business owner can perform this action."
        )

    return membership.business
