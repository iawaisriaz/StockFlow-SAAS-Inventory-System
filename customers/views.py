
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import (
    Count,
    DecimalField,
    F,
    Max,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.utils import get_current_business
from returns.models import SalesReturn

from .models import Customer
from .services import normalize_name, normalize_phone


MONEY_FIELD = DecimalField(
    max_digits=16,
    decimal_places=2,
)


# =====================================================
# HELPERS
# =====================================================

def customer_queryset(business):
    return Customer.objects.filter(
        business=business
    )


# =====================================================
# CUSTOMER LIST
# =====================================================

@login_required
def customer_list(request):

    business = get_current_business(request.user)

    search = request.GET.get(
        "search",
        "",
    ).strip()

    customers = customer_queryset(business)

    total_customers = customers.count()

    # Calculate refunds separately to prevent
    # duplicate totals from joined Sale records.
    refund_subquery = (
        SalesReturn.objects.filter(
            business=business,
            sale__business=business,
            sale__customer_id=OuterRef("pk"),
            return_type="with_receipt",
            is_voided=False,
        )
        .order_by()
        .values("sale__customer_id")
        .annotate(
            value=Sum("refund_amount")
        )
        .values("value")[:1]
    )

    customers = customers.annotate(
        total_orders=Count(
            "sales",
            filter=Q(
                sales__business=business,
                sales__status="completed",
            ),
        ),

        gross_spent=Coalesce(
            Sum(
                "sales__total",
                filter=Q(
                    sales__business=business,
                    sales__status="completed",
                ),
            ),
            Value(
                Decimal("0.00"),
                output_field=MONEY_FIELD,
            ),
            output_field=MONEY_FIELD,
        ),

        total_refunded=Coalesce(
            Subquery(
                refund_subquery,
                output_field=MONEY_FIELD,
            ),
            Value(
                Decimal("0.00"),
                output_field=MONEY_FIELD,
            ),
            output_field=MONEY_FIELD,
        ),

        last_purchase=Max(
            "sales__sale_date",
            filter=Q(
                sales__business=business,
                sales__status="completed",
            ),
        ),
    ).annotate(
        total_spent=(
            F("gross_spent")
            - F("total_refunded")
        )
    )

    repeat_customers = customers.filter(
        total_orders__gte=2
    ).count()

    if search:
        normalized = normalize_phone(search)

        query = (
            Q(name__icontains=search)
            | Q(phone__icontains=search)
        )

        if normalized:
            query |= Q(
                normalized_phone__icontains=normalized
            )

        customers = customers.filter(query)

    context = {
        "customers": customers.order_by(
            "-created_at",
            "-pk",
        ),
        "search": search,
        "total_customers": total_customers,
        "repeat_customers": repeat_customers,
    }

    return render(
        request,
        "customers/customer_list.html",
        context,
    )


# =====================================================
# CUSTOMER DETAILS
# =====================================================

@login_required
def customer_detail(request, pk):

    business = get_current_business(request.user)

    customer = get_object_or_404(
        customer_queryset(business),
        pk=pk,
    )

    sales = customer.sales.filter(
        business=business
    ).order_by(
        "-sale_date",
        "-pk",
    )

    completed = sales.filter(
        status="completed"
    )

    total_orders = completed.count()

    gross_spent = (
        completed.aggregate(
            value=Sum("total")
        )["value"]
        or Decimal("0.00")
    )

    total_refunded = (
        SalesReturn.objects.filter(
            business=business,
            sale__business=business,
            sale__customer=customer,
            return_type="with_receipt",
            is_voided=False,
        )
        .aggregate(
            value=Sum("refund_amount")
        )["value"]
        or Decimal("0.00")
    )

    total_spent = (
        gross_spent - total_refunded
    )

    last_purchase = completed.aggregate(
        value=Max("sale_date")
    )["value"]

    return render(
        request,
        "customers/customer_detail.html",
        {
            "customer": customer,
            "sales": sales,
            "total_orders": total_orders,
            "total_spent": total_spent,
            "gross_spent": gross_spent,
            "total_refunded": total_refunded,
            "last_purchase": last_purchase,
        },
    )


# =====================================================
# UPDATE CUSTOMER
# =====================================================

@login_required
@require_POST
def customer_update(request, pk):

    business = get_current_business(request.user)

    customer = get_object_or_404(
        customer_queryset(business),
        pk=pk,
    )

    name = normalize_name(
        request.POST.get("name", "")
    )

    phone = request.POST.get(
        "phone",
        "",
    ).strip()

    if not name and not phone:
        messages.error(
            request,
            "Customer name or phone is required.",
        )

        return redirect(
            "customers:detail",
            pk=pk,
        )

    if len(name) > 150 or len(phone) > 30:
        messages.error(
            request,
            "Customer details are too long.",
        )

        return redirect(
            "customers:detail",
            pk=pk,
        )

    normalized = normalize_phone(phone)

    customer.name = name
    customer.phone = phone
    customer.normalized_phone = normalized

    customer.save(
        update_fields=[
            "name",
            "phone",
            "normalized_phone",
            "updated_at",
        ]
    )

    messages.success(
        request,
        "Customer information updated successfully.",
    )

    return redirect(
        "customers:detail",
        pk=pk,
    )
