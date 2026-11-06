
from django.urls import path

from . import views

from .views import (
    StockFlowPasswordResetView,
    StockFlowPasswordResetConfirmView,
    stockflow_password_reset_complete,
)


urlpatterns = [
    path(
        "signup/",
        views.signup_view,
        name="signup",
    ),

    path(
        "login/",
        views.login_view,
        name="login",
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout",
    ),

    path(
        "settings/",
        views.settings_view,
        name="settings",
    ),

    path(
        "settings/delete-account/",
        views.delete_account_view,
        name="delete_account",
    ),

    path(
        "forgot-password/",
        StockFlowPasswordResetView.as_view(),
        name="forgot_password",
    ),

    path(
        "reset-password/<uidb64>/<token>/",
        StockFlowPasswordResetConfirmView.as_view(),
        name="reset_password",
    ),

    path(
        "password-reset/complete/",
        stockflow_password_reset_complete,
        name="password_reset_complete",
    ),
]
