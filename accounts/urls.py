from django.urls import path
from django.contrib.auth import views as auth_views

from .views import (
    UserLoginView,
    register,
    UserPasswordResetView,
    UserPasswordResetConfirmView,
    UserPasswordChangeView,
)


app_name = "accounts"


urlpatterns = [
    path("login/", UserLoginView.as_view(), name="login"),
    path(
        "logout/",
        auth_views.LogoutView.as_view(
            template_name="registration/logged_out.html"
        ),
        name="logout",
    ),
    path("register/", register, name="register"),
    path(
        "password-change/",
        UserPasswordChangeView.as_view(),
        name="password_change"
    ),
    path(
        "password-change-done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="registration/password_change_done.html"
        ),
        name="password_change_done",
    ),
    path(
        "password-reset/",
        UserPasswordResetView.as_view(),
        name="password_reset"
    ),
    path(
        "password-reset-confirm/<uidb64>/<token>/",
        UserPasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "password-reset-done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="accounts/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "password-reset-complete/",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="accounts/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
]
