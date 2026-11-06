from django.urls import path

from . import views


app_name = "products"


urlpatterns = [

    path(
        "",
        views.product_list,
        name="list"
    ),

    path(
        "add/",
        views.product_add,
        name="add"
    ),

    path(
        "<int:pk>/edit/",
        views.product_edit,
        name="edit"
    ),

    path(
        "<int:pk>/delete/",
        views.product_delete,
        name="delete"
    ),

    path(
        "<int:pk>/mark-reviewed/",
        views.product_mark_reviewed,
        name="mark_reviewed"
    ),

]