
from django.contrib.auth.decorators import login_required
from django.db.models import (
    DecimalField,
    ExpressionWrapper,
    F,
    Sum,
)
from django.shortcuts import render

from accounts.utils import get_current_business
from products.models import Product
from purchases.models import PurchaseItem

from .services import (
    get_period,
    get_sales_summary,
    get_profit_summary,
    get_purchase_summary,
    get_inventory_summary,
    get_daily_sales,
    get_weekly_chart,
    completed_sales,
    active_returns,
    received_purchases,
    get_returns_report,
    get_stock_movement_report,
)





# ============================================================
# BASE CONTEXT
# ============================================================

def base_context(request, active_tab):

    period = get_period(request)

    return {
        "active_tab": active_tab,
        "filter": period,
        "period_label": period["label"],
    }


# ============================================================
# OVERVIEW
# ============================================================

@login_required
def overview(request):

    business = get_current_business(request.user)

    context = base_context(
        request,
        "overview",
    )

    period = context["filter"]

    context.update({
        "sales_summary": get_sales_summary(
            business,
            period,
        ),
        "profit_summary": get_profit_summary(
            business,
            period,
        ),
        "purchase_summary": get_purchase_summary(
            business,
            period,
        ),
        "inventory_summary": get_inventory_summary(
            business,
        ),
        "weekly_chart": get_weekly_chart(
            business,
        ),
    })

    return render(
        request,
        "reports/overview.html",
        context,
    )


# ============================================================
# SALES REPORT
# ============================================================

@login_required
def sales_report(request):

    business = get_current_business(request.user)

    context = base_context(
        request,
        "sales",
    )

    period = context["filter"]

    context.update({
        "summary": get_sales_summary(
            business,
            period,
        ),
        "daily_rows": get_daily_sales(
            business,
            period,
        ),
        "recent_sales": (
            completed_sales(
                business,
                period,
            )
            .select_related("customer")
            .order_by("-sale_date")[:50]
        ),
        "recent_returns": (
            active_returns(
                business,
                period,
            )
            .order_by("-created_at")[:50]
        ),
    })

    return render(
        request,
        "reports/sales_report.html",
        context,
    )


# ============================================================
# PROFIT REPORT
# ============================================================

@login_required
def profit_report(request):

    business = get_current_business(request.user)

    context = base_context(
        request,
        "profit",
    )

    period = context["filter"]

    context.update({
        "summary": get_profit_summary(
            business,
            period,
        ),
    })

    return render(
        request,
        "reports/profit_report.html",
        context,
    )


# ============================================================
# PURCHASE REPORT
# ============================================================

@login_required
def purchase_report(request):

    business = get_current_business(request.user)

    context = base_context(
        request,
        "purchases",
    )

    period = context["filter"]

    purchases = received_purchases(
        business,
        period,
    )

    cost_expression = ExpressionWrapper(
        F("quantity") * F("unit_cost"),
        output_field=DecimalField(
            max_digits=20,
            decimal_places=2,
        ),
    )

    supplier_rows = (
        PurchaseItem.objects.filter(
            purchase__in=purchases,
        )
        .values(
            "purchase__supplier_id",
            "purchase__supplier__name",
        )
        .annotate(
            total_value=Sum(cost_expression),
            total_units=Sum("quantity"),
        )
        .order_by("-total_value")
    )

    context.update({
        "summary": get_purchase_summary(
            business,
            period,
        ),
        "supplier_rows": supplier_rows,
        "recent_purchases": (
            purchases.select_related("supplier")
            .prefetch_related("items")
            .order_by("-received_at")[:50]
        ),
    })

    return render(
        request,
        "reports/purchase_report.html",
        context,
    )


# ============================================================
# INVENTORY REPORT
# ============================================================

@login_required
def inventory_report(request):

    business = get_current_business(request.user)

    context = base_context(
        request,
        "inventory",
    )

    products = (
        Product.objects.filter(
            business=business,
        )
        .select_related("category")
        .order_by("name")
    )

    status = request.GET.get(
        "status",
        "all",
    )

    if status == "low":
        products = products.filter(
            stock_quantity__gt=0,
            stock_quantity__lte=F(
                "low_stock_threshold"
            ),
        )

    elif status == "out":
        products = products.filter(
            stock_quantity=0,
        )

    elif status == "in":
        products = products.filter(
            stock_quantity__gt=F(
                "low_stock_threshold"
            ),
        )

    else:
        status = "all"

    context.update({
        "summary": get_inventory_summary(
            business,
        ),
        "products": products[:100],
        "selected_status": status,
    })

    return render(
        request,
        "reports/inventory_report.html",
        context,
    )


# ============================================================
# RETURNS REPORT
# ============================================================

@login_required
def returns_report(request):

    business = get_current_business(request.user)

    context = base_context(
        request,
        "returns",
    )

    period = context["filter"]

    returns = active_returns(
        business,
        period,
    )

    context.update({
        "summary": get_returns_report(
            business,
            period,
        ),
        "recent_returns": (
            returns.select_related("sale")
            .prefetch_related("items")
            .order_by("-created_at", "-id")[:100]
        ),
    })

    return render(
        request,
        "reports/returns_report.html",
        context,
    )


# ============================================================
# STOCK MOVEMENT REPORT
# ============================================================

@login_required
def stock_movement_report(request):

    business = get_current_business(request.user)

    context = base_context(
        request,
        "stock_movement",
    )

    context.update(
        get_stock_movement_report(
            business,
            context["filter"],
        )
    )

    return render(
        request,
        "reports/stock_movement_report.html",
        context,
    )
