
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from accounts.utils import get_current_business
from sales.models import Sale

from reports.services import (
    get_period,
    get_sales_summary,
    get_profit_summary,
    get_inventory_summary,
    get_weekly_chart,
)


# ============================================================
# DASHBOARD
# ============================================================

@login_required
def dashboard_view(request):

    # --------------------------------------------------------
    # CURRENT BUSINESS
    # --------------------------------------------------------

    business = get_current_business(request.user)

    # --------------------------------------------------------
    # TODAY'S FINANCIAL SUMMARY
    # --------------------------------------------------------
    # Reuse Reports date logic.
    # Dashboard always displays today's financial figures.

    # Force today's period, even if the URL
    # contains different date filters.

    original_get = request.GET
    today_get = original_get.copy()

    today_get["period"] = "today"

    try:
        request.GET = today_get
        period = get_period(request)

    finally:
        request.GET = original_get

    # Sales summary for current business
    sales_summary = get_sales_summary(
        business,
        period,
    )

    # Profit summary for current business
    profit_summary = get_profit_summary(
        business,
        period,
    )

    # --------------------------------------------------------
    # INVENTORY OVERVIEW
    # --------------------------------------------------------
    # Current stock, independent of today's sales date.

    inventory_summary = get_inventory_summary(
        business
    )

    # --------------------------------------------------------
    # LAST 7 DAYS CHART
    # --------------------------------------------------------

    weekly_chart = get_weekly_chart(
        business
    )

    # --------------------------------------------------------
    # RECENT SALES
    # --------------------------------------------------------
    # Latest 3 completed sales from current business.
    # Includes sales created by Owner and Employees.

    recent_sales = (
        Sale.objects.filter(
            business=business,
            status="completed",
        )
        .prefetch_related("items")
        .order_by(
            "-sale_date",
            "-pk",
        )[:3]
    )

    # --------------------------------------------------------
    # TEMPLATE CONTEXT
    # --------------------------------------------------------

    context = {
        "sales_summary": sales_summary,
        "profit_summary": profit_summary,
        "inventory_summary": inventory_summary,
        "weekly_chart": weekly_chart,
        "recent_sales": recent_sales,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )
