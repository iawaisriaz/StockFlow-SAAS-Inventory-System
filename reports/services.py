
from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.db.models import (
    Count,
    DecimalField,
    ExpressionWrapper,
    F,
    Sum,
)
from django.db.models.functions import TruncDate
from django.utils import timezone

from products.models import Product
from purchases.models import Purchase, PurchaseItem
from sales.models import Sale, SaleItem
from returns.models import SalesReturn, ReturnItem


ZERO = Decimal("0.00")
CENT = Decimal("0.01")


# ============================================================
# MONEY HELPER
# ============================================================

def money(value):
    return Decimal(value or 0).quantize(
        CENT,
        rounding=ROUND_HALF_UP,
    )


# ============================================================
# DATE FILTERS
# ============================================================

def parse_date(value):
    try:
        return date.fromisoformat(value)

    except (TypeError, ValueError):
        return None


def get_period(request):
    today = timezone.localdate()

    period = request.GET.get(
        "period",
        "today",
    )

    if period not in ("today", "date", "range", "all"):
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

    if period == "today":
        start = end = today
        label = "Today"

    elif period == "date":
        start = end = selected_date or today
        label = start.strftime("%d %b %Y")

    elif period == "range":
        start = start_date or today
        end = end_date or today

        if start > end:
            start, end = end, start

        label = (
            f"{start:%d %b %Y} - "
            f"{end:%d %b %Y}"
        )

    else:
        start = None
        end = None
        label = "All Time"

    return {
        "period": period,
        "start": start,
        "end": end,
        "label": label,
        "selected_date": (
            start.isoformat()
            if period == "date"
            else ""
        ),
        "start_date": (
            start.isoformat()
            if period == "range"
            else ""
        ),
        "end_date": (
            end.isoformat()
            if period == "range"
            else ""
        ),
        "today": today.isoformat(),
    }


def apply_period(queryset, field, period):

    if period["start"] is None:
        return queryset

    filters = {
        f"{field}__date__range": (
            period["start"],
            period["end"],
        )
    }

    return queryset.filter(**filters)


# ============================================================
# BASE QUERYSETS
# ============================================================

def completed_sales(business, period):

    qs = Sale.objects.filter(
        business=business,
        status="completed",
    )

    return apply_period(
        qs,
        "sale_date",
        period,
    )


def active_returns(business, period):

    qs = SalesReturn.objects.filter(
        business=business,
        is_voided=False,
    )

    return apply_period(
        qs,
        "created_at",
        period,
    )


def received_purchases(business, period):

    qs = Purchase.objects.filter(
        business=business,
        status=Purchase.STATUS_RECEIVED,
        stock_applied=True,
        received_at__isnull=False,
    )

    return apply_period(
        qs,
        "received_at",
        period,
    )


# ============================================================
# SALES SUMMARY
# ============================================================

def get_sales_summary(business, period):

    sales = completed_sales(
        business,
        period,
    )

    returns = active_returns(
        business,
        period,
    )

    gross_sales = money(
        sales.aggregate(
            value=Sum("total")
        )["value"]
    )

    refunds = money(
        returns.aggregate(
            value=Sum("refund_amount")
        )["value"]
    )

    return {
        "gross_sales": gross_sales,
        "refunds": refunds,
        "net_sales": gross_sales - refunds,
        "sales_count": sales.count(),
        "returns_count": returns.count(),
    }


# ============================================================
# PROFIT SUMMARY
# ============================================================

def get_profit_summary(business, period):

    sales_summary = get_sales_summary(
        business,
        period,
    )

    sales = completed_sales(
        business,
        period,
    )

    returns = active_returns(
        business,
        period,
    )

    # Original cost recorded when each sale occurred
    sold_items = SaleItem.objects.filter(
        sale__in=sales,
    )

    cost_expression = ExpressionWrapper(
        F("cost_price") * F("quantity"),
        output_field=DecimalField(
            max_digits=20,
            decimal_places=6,
        ),
    )

    original_cogs = money(
        sold_items.aggregate(
            value=Sum(cost_expression)
        )["value"]
    )

    # Only resellable returns reverse COGS
    good_return_items = ReturnItem.objects.filter(
        sales_return__in=returns,
        condition="resellable",
    )

    return_cost_expression = ExpressionWrapper(
        F("unit_cost_snapshot") * F("quantity"),
        output_field=DecimalField(
            max_digits=20,
            decimal_places=6,
        ),
    )

    returned_cogs = money(
        good_return_items.aggregate(
            value=Sum(return_cost_expression)
        )["value"]
    )

    net_cogs = (
        original_cogs - returned_cogs
    )

    gross_profit = (
        sales_summary["net_sales"] - net_cogs
    )

    net_sales = sales_summary["net_sales"]

    margin = ZERO

    if net_sales != 0:
        margin = (
            gross_profit
            / net_sales
            * Decimal("100")
        ).quantize(
            CENT,
            rounding=ROUND_HALF_UP,
        )

    return {
        **sales_summary,
        "original_cogs": original_cogs,
        "returned_cogs": returned_cogs,
        "net_cogs": net_cogs,
        "gross_profit": gross_profit,
        "profit_margin": margin,
    }


# ============================================================
# PURCHASE SUMMARY
# ============================================================

def get_purchase_summary(business, period):

    purchases = received_purchases(
        business,
        period,
    )

    items = PurchaseItem.objects.filter(
        purchase__in=purchases,
    )

    cost_expression = ExpressionWrapper(
        F("quantity") * F("unit_cost"),
        output_field=DecimalField(
            max_digits=20,
            decimal_places=2,
        ),
    )

    total_value = money(
        items.aggregate(
            value=Sum(cost_expression)
        )["value"]
    )

    total_units = (
        items.aggregate(
            value=Sum("quantity")
        )["value"]
        or 0
    )

    return {
        "purchase_count": purchases.count(),
        "total_value": total_value,
        "total_units": total_units,
        "supplier_count": (
            purchases.values("supplier_id")
            .distinct()
            .count()
        ),
    }


# ============================================================
# INVENTORY SUMMARY
# ============================================================

def get_inventory_summary(business):

    products = Product.objects.filter(
        business=business
    )

    total_value = money(
        products.aggregate(
            value=Sum("inventory_value")
        )["value"]
    )

    low_stock = products.filter(
        stock_quantity__gt=0,
        stock_quantity__lte=F(
            "low_stock_threshold"
        ),
    )

    out_of_stock = products.filter(
        stock_quantity=0,
    )

    return {
        "total_products": products.count(),
        "total_units": (
            products.aggregate(
                value=Sum("stock_quantity")
            )["value"]
            or 0
        ),
        "inventory_value": total_value,
        "low_stock_count": low_stock.count(),
        "out_of_stock_count": out_of_stock.count(),
        "in_stock_count": products.filter(
            stock_quantity__gt=F(
                "low_stock_threshold"
            )
        ).count(),
    }


# ============================================================
# DAILY SALES BREAKDOWN
# ============================================================

def get_daily_sales(business, period):

    sales = completed_sales(
        business,
        period,
    )

    returns = active_returns(
        business,
        period,
    )

    sales_rows = (
        sales.annotate(
            day=TruncDate("sale_date")
        )
        .values("day")
        .annotate(
            gross=Sum("total"),
            count=Count("id"),
        )
        .order_by("day")
    )

    return_rows = (
        returns.annotate(
            day=TruncDate("created_at")
        )
        .values("day")
        .annotate(
            refunds=Sum("refund_amount"),
            count=Count("id"),
        )
        .order_by("day")
    )

    data = {}

    for row in sales_rows:
        day = row["day"]

        data[day] = {
            "day": day,
            "gross": money(row["gross"]),
            "refunds": ZERO,
            "sales_count": row["count"],
            "returns_count": 0,
        }

    for row in return_rows:
        day = row["day"]

        if day not in data:
            data[day] = {
                "day": day,
                "gross": ZERO,
                "refunds": ZERO,
                "sales_count": 0,
                "returns_count": 0,
            }

        data[day]["refunds"] = money(
            row["refunds"]
        )

        data[day]["returns_count"] = (
            row["count"]
        )

    result = []

    for day in sorted(
        data,
        reverse=True,
    ):
        row = data[day]

        row["net"] = (
            row["gross"] - row["refunds"]
        )

        result.append(row)

    return result


# ============================================================
# LAST 7 DAYS CHART
# ============================================================

def get_weekly_chart(business):

    today = timezone.localdate()

    period = {
        "start": today - timedelta(days=6),
        "end": today,
    }

    daily_rows = get_daily_sales(
        business,
        period,
    )

    lookup = {
        row["day"]: row
        for row in daily_rows
    }

    chart = []

    for offset in range(6, -1, -1):
        day = today - timedelta(
            days=offset
        )

        row = lookup.get(day, {})

        chart.append({
            "label": day.strftime("%a"),
            "date": day.isoformat(),
            "gross": float(
                row.get("gross", ZERO)
            ),
            "refunds": float(
                row.get("refunds", ZERO)
            ),
            "net": float(
                row.get("net", ZERO)
            ),
        })

    return chart


# ============================================================
# RETURNS REPORT
# ============================================================

def get_returns_report(business, period):

    returns = active_returns(
        business,
        period,
    )

    items = ReturnItem.objects.filter(
        sales_return__in=returns,
    )

    total_refunds = money(
        returns.aggregate(
            value=Sum("refund_amount")
        )["value"]
    )

    total_units = (
        items.aggregate(
            value=Sum("quantity")
        )["value"]
        or 0
    )

    restocked_units = (
        items.filter(
            condition="resellable",
        ).aggregate(
            value=Sum("quantity")
        )["value"]
        or 0
    )

    damaged_units = (
        items.filter(
            condition="damaged",
        ).aggregate(
            value=Sum("quantity")
        )["value"]
        or 0
    )

    reason_rows = (
        returns.values("reason")
        .annotate(
            total=Count("id"),
            refunds=Sum("refund_amount"),
        )
        .order_by("-total", "reason")
    )

    return {
        "total_returns": returns.count(),
        "total_refunds": total_refunds,
        "total_units": total_units,
        "restocked_units": restocked_units,
        "damaged_units": damaged_units,
        "with_receipt": returns.filter(
            return_type="with_receipt",
        ).count(),
        "without_receipt": returns.filter(
            return_type="without_receipt",
        ).count(),
        "reason_rows": reason_rows,
    }


# ============================================================
# STOCK MOVEMENT REPORT
# Requires products.StockMovement
# ============================================================

def get_stock_movement_report(business, period):

    from products.models import StockMovement

    movements = StockMovement.objects.filter(
        business=business,
    )

    if period["start"] is not None:
        movements = movements.filter(
            created_at__date__range=(
                period["start"],
                period["end"],
            )
        )

    stock_in = (
        movements.filter(
            quantity_change__gt=0,
        ).aggregate(
            total=Sum("quantity_change")
        )["total"]
        or 0
    )

    stock_out = abs(
        movements.filter(
            quantity_change__lt=0,
        ).aggregate(
            total=Sum("quantity_change")
        )["total"]
        or 0
    )

    product_rows = (
        movements.values(
            "product_id",
            "product__name",
            "product__sku",
        )
        .annotate(
            net_change=Sum("quantity_change"),
            movement_count=Count("id"),
        )
        .order_by("product__name")
    )

    recent_movements = (
        movements.select_related("product")
        .order_by("-created_at", "-id")[:100]
    )

    return {
        "stock_in": stock_in,
        "stock_out": stock_out,
        "net_change": stock_in - stock_out,
        "movement_count": movements.count(),
        "product_rows": product_rows,
        "recent_movements": recent_movements,
    }
