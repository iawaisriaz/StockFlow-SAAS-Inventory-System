
from decimal import Decimal

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.utils import get_current_business
from categories.models import Category
from employees.permissions import has_permission, permission_or_404

from .forms import ProductForm, ProductEditForm
from .models import Product


# ============================================================
# FORM ERRORS
# ============================================================

def get_form_errors(form):
    errors = []

    for field_errors in form.errors.values():
        for error in field_errors:
            errors.append(str(error))

    return " ".join(errors)


# ============================================================
# PRODUCT LIST
# ============================================================

@permission_or_404("products", "view")
def product_list(request):

    business = get_current_business(request.user)

    search_query = request.GET.get("q", "").strip()
    selected_category = request.GET.get("category", "").strip()
    selected_stock = request.GET.get("stock", "").strip()
    selected_review = request.GET.get("review", "").strip()

    categories = Category.objects.filter(
        business=business
    ).order_by("name")

    products = Product.objects.filter(
        business=business
    ).select_related("category")

    total_products = products.count()

    # SEARCH
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(sku__icontains=search_query)
        )

    # CATEGORY FILTER
    if selected_category:
        if selected_category.isdecimal():
            products = products.filter(
                category_id__in=categories.filter(
                    pk=selected_category
                ).values("pk")
            )
        else:
            products = products.none()

    # STOCK FILTER
    if selected_stock == "in_stock":
        products = products.filter(
            stock_quantity__gt=F("low_stock_threshold")
        )

    elif selected_stock == "low_stock":
        products = products.filter(
            stock_quantity__gt=0,
            stock_quantity__lte=F("low_stock_threshold")
        )

    elif selected_stock == "out_of_stock":
        products = products.filter(
            stock_quantity=0
        )

    elif selected_stock:
        selected_stock = ""

    # COST REVIEW FILTER
    if selected_review == "increased":
        products = products.filter(
            cost_review_required=True,
            previous_cost__isnull=False,
            cost_price__gt=F("previous_cost")
        )

    elif selected_review == "decreased":
        products = products.filter(
            cost_review_required=True,
            previous_cost__isnull=False,
            cost_price__lt=F("previous_cost")
        )

    elif selected_review == "no_pending":
        products = products.filter(
            cost_review_required=False
        )

    elif selected_review:
        selected_review = ""

    products = products.order_by(
        "-created_at",
        "-id"
    )

    paginator = Paginator(products, 10)

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "page_obj": page_obj,
        "categories": categories,
        "total_products": total_products,
        "search_query": search_query,
        "selected_category": selected_category,
        "selected_stock": selected_stock,
        "selected_review": selected_review,
        "can_add_product": has_permission(request.user, "products", "add"),
        "can_edit_product": has_permission(request.user, "products", "edit"),
        "can_delete_product": has_permission(request.user, "products", "delete"),
    }

    return render(
        request,
        "products/products.html",
        context
    )


# ============================================================
# ADD PRODUCT
# ============================================================

@permission_or_404("products", "add")
@require_POST
def product_add(request):

    business = get_current_business(request.user)

    form = ProductForm(
        request.POST,
        request.FILES,
        business=business
    )

    if form.is_valid():

        product = form.save(commit=False)
        product.business = business

        product.previous_cost = None
        product.cost_review_required = False
        product.cost_changed_at = None

        # Opening stock valuation.
        product.inventory_value = (
            Decimal(product.stock_quantity)
            * product.cost_price
        )

        product.recalculate_average()
        product.save()

        messages.success(
            request,
            "Product added successfully."
        )

    else:
        messages.error(
            request,
            get_form_errors(form)
        )

    return redirect("products:list")


# ============================================================
# EDIT PRODUCT
# ============================================================

@permission_or_404("products", "edit")
@require_POST
def product_edit(request, pk):

    business = get_current_business(request.user)

    old_image_name = None
    old_image_storage = None
    current_image_name = None

    with transaction.atomic():

        product = get_object_or_404(
            Product.objects.select_for_update(),
            pk=pk,
            business=business
        )

        old_cost = product.cost_price
        old_quantity = product.stock_quantity
        old_inventory_value = product.inventory_value

        if product.image:
            old_image_name = product.image.name
            old_image_storage = product.image.storage

        form = ProductEditForm(
            request.POST,
            request.FILES,
            instance=product,
            business=business
        )

        if not form.is_valid():
            messages.error(
                request,
                get_form_errors(form)
            )
            return redirect("products:list")

        remove_image = form.cleaned_data.get(
            "remove_image",
            False
        )

        new_image = request.FILES.get("image")

        product = form.save(commit=False)

        if remove_image and not new_image:
            product.image = None

        # Track latest cost changes.
        if product.cost_price != old_cost:
            product.previous_cost = old_cost
            product.cost_review_required = True
            product.cost_changed_at = timezone.now()

        new_quantity = product.stock_quantity

        # Manual stock additions use the
        # latest cost entered in the form.
        if new_quantity > old_quantity:
            added_quantity = (
                new_quantity - old_quantity
            )

            product.inventory_value = (
                old_inventory_value
                + Decimal(added_quantity)
                * product.cost_price
            )

        # Manual stock reductions use the
        # existing weighted average.
        elif new_quantity < old_quantity:

            if old_quantity > 0:
                old_average = (
                    old_inventory_value
                    / Decimal(old_quantity)
                )
            else:
                old_average = Decimal("0")

            removed_quantity = (
                old_quantity - new_quantity
            )

            product.inventory_value = (
                old_inventory_value
                - Decimal(removed_quantity)
                * old_average
            ).quantize(
                Decimal("0.0001")
            )

        if new_quantity != old_quantity or product.cost_price != old_cost:
            product.inventory_revision += 1

        # A latest-cost edit alone does not
        # revalue previously held stock.
        product.recalculate_average()
        product.save()

        if product.image:
            current_image_name = product.image.name

    if (
        old_image_name
        and old_image_storage
        and old_image_name != current_image_name
    ):
        transaction.on_commit(
            lambda storage=old_image_storage, name=old_image_name:
                storage.delete(name)
        )

    messages.success(
        request,
        "Product updated successfully."
    )

    return redirect("products:list")


# ============================================================
# MARK COST AS REVIEWED
# ============================================================

@permission_or_404("products", "edit")
@require_POST
def product_mark_reviewed(request, pk):

    business = get_current_business(request.user)

    with transaction.atomic():

        product = get_object_or_404(
            Product.objects.select_for_update(),
            pk=pk,
            business=business
        )

        if product.cost_review_required:

            product.cost_review_required = False
            product.inventory_revision += 1

            product.save(
                update_fields=[
                    "cost_review_required",
                    "inventory_revision",
                    "updated_at",
                ]
            )

            messages.success(
                request,
                "Product cost marked as reviewed."
            )

        else:
            messages.info(
                request,
                "This product has no pending cost review."
            )

    return redirect("products:list")


# ============================================================
# DELETE PRODUCT
# ============================================================

@permission_or_404("products", "delete")
@require_POST
def product_delete(request, pk):

    business = get_current_business(request.user)

    product = get_object_or_404(
        Product,
        pk=pk,
        business=business
    )

    image_name = (
        product.image.name
        if product.image
        else None
    )

    image_storage = (
        product.image.storage
        if product.image
        else None
    )

    try:
        product.delete()

        if image_name and image_storage:
            image_storage.delete(image_name)

        messages.success(
            request,
            "Product deleted successfully."
        )

    except ProtectedError:
        messages.error(
            request,
            "This product cannot be deleted "
            "because it has related records."
        )

    return redirect("products:list")
