
import json

from datetime import datetime
from decimal import Decimal

from django.contrib import messages
from employees.permissions import permission_or_404, has_permission
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.utils import get_current_business
from sales.models import Sale

from .forms import ReturnForm, NEW_REASONS
from .models import SalesReturn
from .services import (
    create_receipt_return,
    get_remaining_quantity,
    get_sale_allocations,
    void_return,
)


# ============================================================
# DATE HELPER
# ============================================================

def parse_date(value):
    try:
        return datetime.strptime(
            value,
            "%Y-%m-%d",
        ).date()

    except (ValueError, TypeError):
        return None


# ============================================================
# RETURNS LIST
# ============================================================

@permission_or_404("returns", "view")
def returns_list(request):

    business = get_current_business(request.user)
    today = timezone.localdate()

    period = request.GET.get(
        "period",
        "today",
    )

    search = request.GET.get(
        "search",
        "",
    ).strip()

    if period not in (
        "today",
        "date",
        "range",
        "all",
    ):
        period = "today"

    selected_date = parse_date(
        request.GET.get("date")
    )

    start_date = parse_date(
        request.GET.get("start_date")
    )

    end_date = parse_date(
        request.GET.get("end_date")
    )

    # Active returns of current business
    returns = (
        SalesReturn.objects.filter(
            business=business,
            is_voided=False,
        )
        .select_related("sale")
    )

    # Date filters
    if period == "today":
        returns = returns.filter(
            created_at__date=today
        )

        period_label = "Today's Returns"

    elif period == "date":
        selected_date = selected_date or today

        returns = returns.filter(
            created_at__date=selected_date
        )

        period_label = "Returns by Date"

    elif period == "range":
        start_date = start_date or today
        end_date = end_date or today

        if start_date > end_date:
            start_date, end_date = (
                end_date,
                start_date,
            )

        returns = returns.filter(
            created_at__date__range=(
                start_date,
                end_date,
            )
        )

        period_label = "Returns by Date Range"

    else:
        period_label = "All Returns"

    # Search
    if search:
        returns = returns.filter(
            Q(reference__icontains=search)
            | Q(sale__reference__icontains=search)
            | Q(customer_name__icontains=search)
            | Q(customer_phone__icontains=search)
            | Q(items__product_name__icontains=search)
        ).distinct()

    # Summary
    total_returns = returns.count()

    total_refunded = (
        returns.aggregate(
            value=Sum("refund_amount")
        )["value"]
        or Decimal("0.00")
    )

    context = {
        "returns": returns.order_by(
            "-created_at",
            "-pk",
        ),
        "total_returns": total_returns,
        "total_refunded": total_refunded,
        "period": period,
        "period_label": period_label,
        "today": today.isoformat(),
        "selected_date": (
            selected_date.isoformat()
            if selected_date
            else ""
        ),
        "start_date": (
            start_date.isoformat()
            if start_date
            else ""
        ),
        "end_date": (
            end_date.isoformat()
            if end_date
            else ""
        ),
        "search": search,
        "has_filters": bool(
            search
            or period != "today"
        ),
    }

    context["can_view_sales"] = has_permission(request.user, "sales", "view")
    context["can_add_return"] = has_permission(request.user, "returns", "add")
    context["can_delete_return"] = has_permission(request.user, "returns", "delete")

    return render(
        request,
        "returns/returns_list.html",
        context,
    )


# ============================================================
# NEW RETURN - WITH RECEIPT ONLY
# ============================================================

@permission_or_404("returns", "add")
def new_return(request):

    business = get_current_business(request.user)

    sale_ref = request.GET.get(
        "sale",
        "",
    ).strip()

    # Preserve selected Sale if POST validation fails
    if request.method == "POST":
        posted_sale_id = request.POST.get(
            "sale_id"
        )

        if posted_sale_id:
            try:
                sale_id = int(posted_sale_id)

                posted_sale = Sale.objects.filter(
                    pk=sale_id,
                    business=business,
                ).first()

                if posted_sale:
                    sale_ref = (
                        posted_sale.reference or ""
                    )

            except (ValueError, TypeError):
                pass

    sale = None
    sale_rows = []
    error_message = ""

    # Find original Sale
    if sale_ref:
        sale = (
            Sale.objects.filter(
                business=business,
                reference__iexact=sale_ref,
                status="completed",
            )
            .prefetch_related("items")
            .first()
        )

        if sale is None:
            error_message = (
                "Completed sale not found."
            )

        else:
            allocations = get_sale_allocations(
                sale
            )

            for item in sale.items.all():
                remaining = get_remaining_quantity(
                    item
                )

                if remaining > 0:
                    sale_rows.append({
                        "item": item,
                        "remaining": remaining,
                        "allocated_total": allocations.get(
                            item.pk,
                            Decimal("0.00"),
                        ),
                    })

            if not sale_rows:
                error_message = (
                    "All products from this sale "
                    "have already been returned."
                )

    # Create return
    if request.method == "POST":
        form = ReturnForm(
            request.POST
        )

        if form.is_valid():
            try:
                items = json.loads(
                    request.POST.get(
                        "items",
                        "[]",
                    )
                )

                sales_return = create_receipt_return(
                    user=request.user,
                    sale_id=form.cleaned_data["sale_id"],
                    reason=form.cleaned_data["reason"],
                    notes=form.cleaned_data["notes"],
                    items=items,
                )

                messages.success(
                    request,
                    f"Return {sales_return.reference} "
                    "recorded successfully.",
                )

                return redirect(
                    "returns:detail",
                    pk=sales_return.pk,
                )

            except ValidationError as error:
                for message in error.messages:
                    messages.error(
                        request,
                        message,
                    )

            except (ValueError, TypeError):
                messages.error(
                    request,
                    "Invalid return information.",
                )

        else:
            for errors in form.errors.values():
                for error in errors:
                    messages.error(
                        request,
                        error,
                    )

    return render(
        request,
        "returns/new_return.html",
        {
            "sale": sale,
            "sale_ref": sale_ref,
            "sale_rows": sale_rows,
            "error_message": error_message,
            "reasons": NEW_REASONS,
        },
    )


# ============================================================
# RETURN DETAIL
# ============================================================

@permission_or_404("returns", "view")
def return_detail(request, pk):

    business = get_current_business(request.user)

    sales_return = get_object_or_404(
        SalesReturn.objects.filter(
            business=business,
            is_voided=False,
        )
        .select_related("sale")
        .prefetch_related(
            "items__sale_item",
            "items__product",
        ),
        pk=pk,
    )

    return render(
        request,
        "returns/return_detail.html",
        {
            "sales_return": sales_return,
            "can_view_sales": has_permission(request.user, "sales", "view"),
        },
    )


# ============================================================
# DELETE / VOID RETURN
# ============================================================

@permission_or_404("returns", "delete")
@require_POST
def return_delete(request, pk):

    business = get_current_business(request.user)

    try:
        sales_return = void_return(
            return_id=pk,
            business=business,
        )

        messages.success(
            request,
            f"Return {sales_return.reference} "
            "removed from active records.",
        )

    except ValidationError as error:
        for message in error.messages:
            messages.error(
                request,
                message,
            )

    return redirect(
        "returns:list"
    )
