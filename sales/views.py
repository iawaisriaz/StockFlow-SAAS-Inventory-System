
import json

from datetime import date
from decimal import Decimal

from django.contrib import messages
from employees.permissions import permission_or_404, has_permission
from django.core.exceptions import ValidationError
from django.db.models import Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.utils import get_current_business
from products.models import Product

from .forms import SaleForm
from .models import Sale
from .services import (
    create_sale,
    cancel_sale,
    delete_cancelled_sale,
)


# ============================================================
# QUERY HELPERS
# ============================================================

def get_sales_for_business(business):
    return Sale.objects.filter(business=business)


def get_products_for_business(business):
    return Product.objects.filter(business=business)


def get_sale_or_404(business, pk):
    return get_object_or_404(
        get_sales_for_business(business),
        pk=pk,
    )


# ============================================================
# DATE HELPER
# ============================================================

def parse_sale_date(value, today):
    """
    Return a valid date that is not in the future.
    Invalid dates return None.
    """
    try:
        parsed = date.fromisoformat(value)

        if parsed > today:
            return None

        return parsed

    except (ValueError, TypeError):
        return None


# ============================================================
# SALES LIST
# ============================================================

@permission_or_404("sales", "view")
def sales_list(request):

    business = get_current_business(request.user)
    all_sales = get_sales_for_business(business)

    today = timezone.localdate()

    period = request.GET.get(
        "period", "today"
    ).strip()

    selected_date = request.GET.get(
        "date", ""
    ).strip()

    start_date = request.GET.get(
        "start_date", ""
    ).strip()

    end_date = request.GET.get(
        "end_date", ""
    ).strip()

    selected_status = request.GET.get(
        "status", ""
    ).strip()

    search = request.GET.get(
        "search", ""
    ).strip()

    # Validate filter options
    if period not in ("today", "date", "range", "all"):
        period = "today"

    if selected_status not in ("completed", "cancelled"):
        selected_status = ""

    period_sales = all_sales
    period_label = "Today's Sales"

    # Period filter
    if period == "today":
        period_sales = period_sales.filter(
            sale_date__date=today
        )

    elif period == "date":
        chosen_date = (
            parse_sale_date(selected_date, today)
            or today
        )

        selected_date = chosen_date.isoformat()

        period_sales = period_sales.filter(
            sale_date__date=chosen_date
        )

        period_label = (
            f"Sales for {chosen_date:%d %b %Y}"
        )

    elif period == "range":
        start = (
            parse_sale_date(start_date, today)
            or today
        )

        end = (
            parse_sale_date(end_date, today)
            or today
        )

        if start > end:
            start, end = end, start

        start_date = start.isoformat()
        end_date = end.isoformat()

        period_sales = period_sales.filter(
            sale_date__date__range=(start, end)
        )

        period_label = (
            f"Sales from {start:%d %b %Y} "
            f"to {end:%d %b %Y}"
        )

    else:
        period_label = "All Sales History"

    # Summary cards
    completed = period_sales.filter(
        status="completed"
    )

    revenue = completed.aggregate(
        value=Sum("total")
    )["value"] or Decimal("0.00")

    total_sales = period_sales.count()
    completed_sales = completed.count()

    cancelled_sales = period_sales.filter(
        status="cancelled"
    ).count()

    # Table filters
    sales = period_sales

    if selected_status:
        sales = sales.filter(
            status=selected_status
        )

    if search:
        sales = sales.filter(
            Q(reference__icontains=search)
            | Q(customer_name__icontains=search)
            | Q(customer_phone__icontains=search)
        )

    sales = sales.order_by(
        "-sale_date",
        "-pk",
    )

    has_filters = (
        period != "today"
        or bool(selected_status)
        or bool(search)
    )

    context = {
        "sales": sales,
        "search": search,
        "selected_status": selected_status,
        "period": period,
        "selected_date": selected_date,
        "start_date": start_date,
        "end_date": end_date,
        "today": today.isoformat(),
        "period_label": period_label,
        "has_filters": has_filters,
        "total_sales": total_sales,
        "completed_sales": completed_sales,
        "cancelled_sales": cancelled_sales,
        "total_revenue": revenue,
        "can_add_sale": has_permission(request.user, "sales", "add"),
        "can_delete_sale": has_permission(request.user, "sales", "delete"),
    }

    return render(
        request,
        "sales/sales_list.html",
        context,
    )


# ============================================================
# NEW SALE
# ============================================================

@permission_or_404("sales", "add")
def new_sale(request):

    business = get_current_business(request.user)

    products = get_products_for_business(
        business
    ).order_by("name")

    product_data = [
        {
            "id": product.pk,
            "name": product.name,
            "sku": product.sku,
            "stock": product.stock_quantity,
            "price": str(product.selling_price),
        }
        for product in products
    ]

    if request.method == "POST":
        form = SaleForm(request.POST)

        try:
            raw_items = json.loads(
                request.POST.get("items", "[]")
            )

            if not isinstance(raw_items, list):
                raise ValueError

        except (ValueError, TypeError):
            raw_items = []

        if form.is_valid():
            try:
                sale_data = form.cleaned_data.copy()

                sale_data["discount_type"] = (
                    request.POST.get(
                        "discount_type",
                        "percent",
                    ).strip()
                )

                sale_data["discount_value"] = (
                    request.POST.get(
                        "discount_value",
                        "0",
                    ).strip()
                )

                sale = create_sale(
                    user=request.user,
                    data=sale_data,
                    items=raw_items,
                )

                messages.success(
                    request,
                    f"Sale {sale.reference} "
                    "completed successfully.",
                )

                return redirect(
                    "sales:detail",
                    pk=sale.pk,
                )

            except ValidationError as error:
                for message in error.messages:
                    messages.error(
                        request,
                        message,
                    )

    else:
        form = SaleForm()

    return render(
        request,
        "sales/new_sale.html",
        {
            "form": form,
            "products_json": product_data,
        },
    )


# ============================================================
# SALE DETAIL
# ============================================================

@permission_or_404("sales", "view")
def sale_detail(request, pk):

    business = get_current_business(request.user)

    sale = get_object_or_404(
        get_sales_for_business(
            business
        ).prefetch_related("items"),
        pk=pk,
    )

    return render(
        request,
        "sales/sale_detail.html",
        {
            "sale": sale,
            "can_cancel_sale": has_permission(request.user, "sales", "edit"),
        },
    )


# ============================================================
# SALE RECEIPT
# ============================================================

@permission_or_404("sales", "view")
def sale_receipt(request, pk):

    business = get_current_business(request.user)

    sale = get_object_or_404(
        get_sales_for_business(
            business
        ).prefetch_related("items"),
        pk=pk,
    )

    return render(
        request,
        "sales/sale_receipt.html",
        {
            "sale": sale,
        },
    )


# ============================================================
# CANCEL SALE
# ============================================================

@permission_or_404("sales", "edit")
@require_POST
def sale_cancel(request, pk):

    business = get_current_business(request.user)

    sale = get_sale_or_404(
        business,
        pk,
    )

    try:
        cancel_sale(
            sale.pk,
            business=business,
        )

        messages.success(
            request,
            "Sale cancelled and stock restored.",
        )

    except ValidationError as error:
        for message in error.messages:
            messages.error(
                request,
                message,
            )

    return redirect(
        "sales:detail",
        pk=pk,
    )


# ============================================================
# DELETE SALE
# ============================================================

@permission_or_404("sales", "delete")
@require_POST
def sale_delete(request, pk):

    business = get_current_business(request.user)

    sale = get_sale_or_404(
        business,
        pk,
    )

    if sale.status != "cancelled":
        messages.error(
            request,
            "To delete this sale, "
            "please cancel it first.",
        )

        return redirect(
            "sales:detail",
            pk=pk,
        )

    try:
        reference = delete_cancelled_sale(
            sale.pk,
            business=business,
        )

        messages.success(
            request,
            f"Sale {reference} deleted permanently.",
        )

        return redirect("sales:list")

    except ValidationError as error:
        for message in error.messages:
            messages.error(
                request,
                message,
            )

    except Sale.DoesNotExist:
        raise Http404("Sale not found.")

    return redirect(
        "sales:detail",
        pk=pk,
    )
