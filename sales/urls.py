
from django.urls import path
from . import views

app_name = "sales"

urlpatterns = [
    path(
        "",
        views.sales_list,
        name="list",
    ),

    path(
        "new/",
        views.new_sale,
        name="new",
    ),

    path(
        "<int:pk>/",
        views.sale_detail,
        name="detail",
    ),

    path(
        "<int:pk>/receipt/",
        views.sale_receipt,
        name="receipt",
    ),

    path(
        "<int:pk>/cancel/",
        views.sale_cancel,
        name="cancel",
    ),

    path(
        "<int:pk>/delete/",
        views.sale_delete,
        name="delete",
    ),
]
