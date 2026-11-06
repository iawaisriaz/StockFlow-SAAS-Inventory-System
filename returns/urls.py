
from django.urls import path

from . import views

app_name = "returns"

urlpatterns = [
    path(
        "",
        views.returns_list,
        name="list",
    ),
    path(
        "new/",
        views.new_return,
        name="new",
    ),
    path(
        "<int:pk>/",
        views.return_detail,
        name="detail",
    ),
    path(
        "<int:pk>/delete/",
        views.return_delete,
        name="delete",
    ),
]
