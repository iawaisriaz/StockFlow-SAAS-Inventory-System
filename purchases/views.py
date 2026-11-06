
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from accounts.utils import get_current_business
from employees.permissions import has_permission, permission_or_404

from .forms import PurchaseForm, PurchaseItemFormSet
from .models import Purchase
from .services import (
    receive_purchase,
    cancel_purchase,
    delete_purchase,
)


# =====================================================
# HELPERS
# =====================================================

def get_purchase(business, pk):
    return get_object_or_404(
        Purchase.objects.select_related("supplier")
        .prefetch_related("items__product"),
        pk=pk,
        business=business,
    )


def get_error_message(exc):
    if isinstance(exc, ValidationError):
        return " ".join(exc.messages)

    return str(exc)


# =====================================================
# PURCHASE LIST
# =====================================================

@permission_or_404("purchases", "view")
def purchase_list(request):

    business = get_current_business(request.user)

    purchases = (
        Purchase.objects.filter(business=business)
        .select_related("supplier")
    )

    search_query = request.GET.get("q", "").strip()
    selected_status = request.GET.get("status", "").strip()

    if search_query:
        purchases = purchases.filter(
            Q(reference__icontains=search_query)
            | Q(supplier__name__icontains=search_query)
        )

    valid_statuses = {
        Purchase.STATUS_DRAFT,
        Purchase.STATUS_RECEIVED,
        Purchase.STATUS_CANCELLED,
    }

    if selected_status in valid_statuses:
        purchases = purchases.filter(
            status=selected_status
        )
    else:
        selected_status = ""

    all_purchases = Purchase.objects.filter(
        business=business
    )

    page_obj = Paginator(
        purchases.order_by("-created_at", "-id"),
        10,
    ).get_page(
        request.GET.get("page")
    )

    context = {
        "page_obj": page_obj,
        "search_query": search_query,
        "selected_status": selected_status,
        "total_purchases": all_purchases.count(),
        "draft_count": all_purchases.filter(
            status=Purchase.STATUS_DRAFT
        ).count(),
        "received_count": all_purchases.filter(
            status=Purchase.STATUS_RECEIVED
        ).count(),
        "can_add_purchase": has_permission(request.user, "purchases", "add"),
        "can_edit_purchase": has_permission(request.user, "purchases", "edit"),
        "can_delete_purchase": has_permission(request.user, "purchases", "delete"),
        "cancelled_count": all_purchases.filter(
            status=Purchase.STATUS_CANCELLED
        ).count(),
    }

    return render(
        request,
        "purchases/purchases.html",
        context,
    )


# =====================================================
# CREATE / EDIT PURCHASE
# =====================================================

def render_purchase_form(
    request,
    *,
    purchase=None,
    is_edit=False,
):

    business = get_current_business(request.user)

    if purchase is None:
        purchase = Purchase(
            business=business
        )

    if request.method == "POST":

        form = PurchaseForm(
            request.POST,
            instance=purchase,
            business=business,
        )

        formset = PurchaseItemFormSet(
            request.POST,
            instance=purchase,
            business=business,
            prefix="items",
        )

    else:

        form = PurchaseForm(
            instance=purchase,
            business=business,
        )

        formset = PurchaseItemFormSet(
            instance=purchase,
            business=business,
            prefix="items",
        )

    if request.method == "POST":

        form_valid = form.is_valid()

        if form_valid:
            formset.selected_supplier_id = (
                form.cleaned_data["supplier"].pk
            )

        if form_valid and formset.is_valid():

            with transaction.atomic():

                saved = form.save(
                    commit=False
                )

                saved.business = business
                saved.save()

                if not saved.reference:
                    saved.reference = (
                        f"PUR-{saved.pk:05d}"
                    )

                    saved.save(
                        update_fields=[
                            "reference"
                        ]
                    )

                formset.instance = saved
                formset.save()

            messages.success(
                request,
                "Purchase saved successfully.",
            )

            return redirect(
                f"{reverse('purchases:list')}"
                f"?view={saved.pk}"
            )

    return render(
        request,
        "purchases/purchase_form.html",
        {
            "form": form,
            "formset": formset,
            "purchase": purchase,
            "is_edit": is_edit,
            "page_title": (
                "Edit Purchase"
                if is_edit
                else "New Purchase"
            ),
            "submit_label": (
                "Save Changes"
                if is_edit
                else "Save Purchase"
            ),
        },
    )


@permission_or_404("purchases", "add")
def purchase_create(request):
    return render_purchase_form(
        request
    )


@permission_or_404("purchases", "edit")
def purchase_edit(request, pk):

    business = get_current_business(request.user)

    purchase = get_purchase(
        business,
        pk
    )

    if purchase.status != Purchase.STATUS_DRAFT:

        messages.error(
            request,
            "Only draft purchases can be edited.",
        )

        return redirect(
            "purchases:list"
        )

    return render_purchase_form(
        request,
        purchase=purchase,
        is_edit=True,
    )


# =====================================================
# PURCHASE DETAILS
# =====================================================

@permission_or_404("purchases", "view")
def purchase_detail(request, pk):

    business = get_current_business(request.user)

    purchase = get_purchase(
        business,
        pk
    )

    return render(
        request,
        "purchases/partials/_purchase_detail_modal.html",
        {
            "purchase": purchase,
            "can_edit_purchase": has_permission(request.user, "purchases", "edit"),
            "can_delete_purchase": has_permission(request.user, "purchases", "delete"),
        },
    )


# =====================================================
# RECEIVE PURCHASE
# =====================================================

@permission_or_404("purchases", "edit")
@require_POST
def purchase_receive(request, pk):

    business = get_current_business(request.user)

    try:

        receive_purchase(
            pk,
            business
        )

        messages.success(
            request,
            "Purchase received successfully. "
            "Inventory stock, latest cost and "
            "weighted average cost have been updated.",
        )

    except Purchase.DoesNotExist:

        messages.error(
            request,
            "Purchase not found.",
        )

    except ValidationError as exc:

        messages.error(
            request,
            get_error_message(exc),
        )

    return redirect(
        "purchases:list"
    )


# =====================================================
# CANCEL PURCHASE
# =====================================================

@permission_or_404("purchases", "edit")
@require_POST
def purchase_cancel(request, pk):

    business = get_current_business(request.user)

    try:

        cancel_purchase(
            pk,
            business
        )

        messages.success(
            request,
            "Draft purchase cancelled successfully.",
        )

    except Purchase.DoesNotExist:

        messages.error(
            request,
            "Purchase not found.",
        )

    except ValidationError as exc:

        messages.error(
            request,
            get_error_message(exc),
        )

    return redirect(
        "purchases:list"
    )


# =====================================================
# DELETE PURCHASE
# =====================================================

@permission_or_404("purchases", "delete")
@require_POST
def purchase_delete(request, pk):

    business = get_current_business(request.user)

    try:

        reference = delete_purchase(
            pk,
            business
        )

        messages.success(
            request,
            f"{reference} deleted successfully. "
            "Inventory stock, costs and value have been "
            "restored if applicable.",
        )

    except Purchase.DoesNotExist:

        messages.error(
            request,
            "Purchase not found or already deleted.",
        )

    except ValidationError as exc:

        messages.error(
            request,
            get_error_message(exc),
        )

    return redirect(
        "purchases:list"
    )
