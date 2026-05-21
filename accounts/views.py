from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import (
    LoginView,
    PasswordResetView,
    PasswordChangeView,
    PasswordResetConfirmView,
)

from .forms import (
    RegistrationForm,
    LoginForm,
    UserPasswordResetForm,
    UserSetPasswordForm,
    UserPasswordChangeForm,
)


class UserLoginView(LoginView):
    template_name = "accounts/login.html"
    form_class = LoginForm


def register(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/accounts/login/")

    else:
        form = RegistrationForm()

    context = {"form": form}
    return render(request, "accounts/register.html", context)


class UserPasswordResetView(PasswordResetView):
    template_name = "accounts/password_reset.html"
    form_class = UserPasswordResetForm
    email_template_name = "accounts/password_reset_email.html"
    success_url = reverse_lazy("accounts:password_reset_done")


class UserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "accounts/password_reset_confirm.html"
    form_class = UserSetPasswordForm
    success_url = reverse_lazy("accounts:password_reset_complete")


class UserPasswordChangeView(PasswordChangeView):
    template_name = "registration/password_change_form.html"
    form_class = UserPasswordChangeForm
    success_url = reverse_lazy("accounts:password_change_done")
