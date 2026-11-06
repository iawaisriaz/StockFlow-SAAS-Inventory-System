
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.utils import get_current_business
from products.models import Product
from employees.permissions import has_permission, permission_or_404

from .forms import SupplierForm
from .models import Supplier


# =====================================================
# 1. SUPPLIERS LIST
# =====================================================

@permission_or_404("suppliers", "view")
def supplier_list(request):

    business = get_current_business(request.user)

    suppliers = (
        Supplier.objects
        .filter(business=business)
        .annotate(products_count=Count("products"))
        .prefetch_related("products")
    )

    total_suppliers = suppliers.count()

    search_query = request.GET.get(
        "q", ""
    ).strip()

    selected_status = request.GET.get(
        "status", ""
    ).strip()

    if search_query:
        suppliers = suppliers.filter(
            Q(name__icontains=search_query)
            | Q(contact_person__icontains=search_query)
            | Q(email__icontains=search_query)
            | Q(phone__icontains=search_query)
        )

    if selected_status == "active":
        suppliers = suppliers.filter(is_active=True)

    elif selected_status == "inactive":
        suppliers = suppliers.filter(is_active=False)

    paginator = Paginator(
        suppliers.order_by("-created_at", "-id"),
        10
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    available_products = (
        Product.objects
        .filter(business=business)
        .order_by("name", "sku")
    )

    context = {
        "page_obj": page_obj,
        "total_suppliers": total_suppliers,
        "search_query": search_query,
        "selected_status": selected_status,
        "available_products": available_products,
        "can_add_supplier": has_permission(request.user, "suppliers", "add"),
        "can_edit_supplier": has_permission(request.user, "suppliers", "edit"),
        "can_delete_supplier": has_permission(request.user, "suppliers", "delete"),
    }

    return render(
        request,
        "suppliers/suppliers.html",
        context
    )


# =====================================================
# 2. ADD SUPPLIER
# =====================================================

@permission_or_404("suppliers", "add")
@require_POST
def supplier_add(request):

    business = get_current_business(request.user)

    form = SupplierForm(
        request.POST,
        business=business
    )

    if form.is_valid():

        with transaction.atomic():

            supplier = form.save(commit=False)
            supplier.business = business
            supplier.save()

            form.save_m2m()

        messages.success(
            request,
            "Supplier added successfully."
        )

    else:

        error_messages = [
            str(error)
            for errors in form.errors.values()
            for error in errors
        ]

        messages.error(
            request,
            "Could not add supplier: "
            + " ".join(error_messages)
        )

    return redirect("suppliers:list")


# =====================================================
# 3. EDIT SUPPLIER
# =====================================================

@permission_or_404("suppliers", "edit")
@require_POST
def supplier_edit(request, pk):

    business = get_current_business(request.user)

    supplier = get_object_or_404(
        Supplier,
        pk=pk,
        business=business
    )

    form = SupplierForm(
        request.POST,
        instance=supplier,
        business=business
    )

    if form.is_valid():

        with transaction.atomic():
            form.save()

        messages.success(
            request,
            "Supplier updated successfully."
        )

    else:

        error_messages = [
            str(error)
            for errors in form.errors.values()
            for error in errors
        ]

        messages.error(
            request,
            "Could not update supplier: "
            + " ".join(error_messages)
        )

    return redirect("suppliers:list")


# =====================================================
# 4. DELETE SUPPLIER
# =====================================================

@permission_or_404("suppliers", "delete")
@require_POST
def supplier_delete(request, pk):

    business = get_current_business(request.user)

    supplier = get_object_or_404(
        Supplier,
        pk=pk,
        business=business
    )

    try:

        supplier.delete()

        messages.success(
            request,
            "Supplier deleted successfully."
        )

    except ProtectedError:

        messages.error(
            request,
            "This supplier has linked purchases "
            "and cannot be deleted. "
            "Mark it inactive instead."
        )

    return redirect("suppliers:list")
