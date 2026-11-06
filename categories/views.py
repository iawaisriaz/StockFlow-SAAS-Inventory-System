
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.utils import get_current_business

from employees.permissions import (
    has_permission,
    permission_or_404,
)

from .forms import CategoryForm
from .models import Category


# ============================================================
# CATEGORY LIST - VIEW PERMISSION
# ============================================================

@permission_or_404("categories", "view")
def category_list(request):

    business = get_current_business(request.user)

    search_query = request.GET.get("q", "").strip()

    categories = Category.objects.filter(
        business=business
    ).order_by("-created_at", "-id")

    total_categories = categories.count()

    if search_query:

        categories = categories.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    paginator = Paginator(categories, 10)

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    context = {
        "page_obj": page_obj,
        "total_categories": total_categories,
        "search_query": search_query,

        # Add permission
        "can_add_category": has_permission(
            request.user,
            "categories",
            "add",
        ),

        # Edit permission
        "can_edit_category": has_permission(
            request.user,
            "categories",
            "edit",
        ),

        # Delete permission
        "can_delete_category": has_permission(
            request.user,
            "categories",
            "delete",
        ),
    }

    return render(
        request,
        "categories/categories.html",
        context,
    )


# ============================================================
# ADD CATEGORY - ADD PERMISSION
# ============================================================

@permission_or_404("categories", "add")
@require_POST
def category_add(request):

    business = get_current_business(request.user)

    form = CategoryForm(
        request.POST,
        business=business,
    )

    if form.is_valid():

        category = form.save(commit=False)

        category.business = business

        category.save()

        messages.success(
            request,
            "Category added successfully.",
        )

    else:

        messages.error(
            request,
            " ".join(
                str(error)
                for errors in form.errors.values()
                for error in errors
            ),
        )

    return redirect("categories:list")


# ============================================================
# EDIT CATEGORY - EDIT PERMISSION
# ============================================================

@permission_or_404("categories", "edit")
@require_POST
def category_edit(request, pk):

    business = get_current_business(request.user)

    category = get_object_or_404(
        Category,
        pk=pk,
        business=business,
    )

    form = CategoryForm(
        request.POST,
        instance=category,
        business=business,
    )

    if form.is_valid():

        form.save()

        messages.success(
            request,
            "Category updated successfully.",
        )

    else:

        messages.error(
            request,
            " ".join(
                str(error)
                for errors in form.errors.values()
                for error in errors
            ),
        )

    return redirect("categories:list")


# ============================================================
# DELETE CATEGORY - DELETE PERMISSION
# ============================================================

@permission_or_404("categories", "delete")
@require_POST
def category_delete(request, pk):

    business = get_current_business(request.user)

    category = get_object_or_404(
        Category,
        pk=pk,
        business=business,
    )

    try:

        category.delete()

        messages.success(
            request,
            "Category deleted successfully.",
        )

    except ProtectedError:

        messages.error(
            request,
            "This category cannot be deleted because "
            "it is being used by existing products.",
        )

    return redirect("categories:list")
