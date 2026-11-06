
from django.urls import path

from . import views


app_name = "reports"


urlpatterns = [
    path(
        "",
        views.overview,
        name="overview",
    ),
    path(
        "sales/",
        views.sales_report,
        name="sales",
    ),
    path(
        "profit/",
        views.profit_report,
        name="profit",
    ),
    path(
        "purchases/",
        views.purchase_report,
        name="purchases",
    ),
    path(
        "inventory/",
        views.inventory_report,
        name="inventory",
    ),
    path(
        "stock-movement/",
        views.stock_movement_report,
        name="stock_movement",
    ),
    path(
        "returns/",
        views.returns_report,
        name="returns",
    ),
]
