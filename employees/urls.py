
from django.urls import path

from . import views


app_name = "employees"


urlpatterns = [

    path(
        "",
        views.employee_list,
        name="list",
    ),

    path(
        "add/",
        views.employee_create,
        name="add",
    ),

    path(
        "<int:pk>/edit/",
        views.employee_edit,
        name="edit",
    ),

    path(
        "<int:pk>/permissions/",
        views.employee_permissions,
        name="permissions",
    ),

    path(
        "<int:pk>/delete/",
        views.employee_delete,
        name="delete",
    ),

    path(
        "no-access/",
        views.no_access,
        name="no_access",
    ),

]
