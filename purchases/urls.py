
from django.urls import path
from . import views

app_name = "purchases"

urlpatterns = [
    path("", views.purchase_list, name="list"),
    path("new/", views.purchase_create, name="create"),
    path("<int:pk>/", views.purchase_detail, name="detail"),
    path("<int:pk>/edit/", views.purchase_edit, name="edit"),
    path(
        "<int:pk>/receive/",
        views.purchase_receive,
        name="receive",
    ),
    path(
        "<int:pk>/cancel/",
        views.purchase_cancel,
        name="cancel",
    ),
    path(
        "<int:pk>/delete/",
        views.purchase_delete,
        name="delete",
    ),
]
