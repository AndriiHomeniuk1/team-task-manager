from django.test import TestCase
from django.test import SimpleTestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from accounts.forms import (
    UserPasswordResetForm,
    UserSetPasswordForm,
    UserPasswordChangeForm,
    LoginForm
)
from accounts.views import (
    UserPasswordResetConfirmView,
    UserPasswordChangeView
)


User = get_user_model()

class UserLoginViewTests(TestCase):
    def test_get_login_returns_form(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")
        self.assertIsInstance(response.context["form"], LoginForm)


class RegisterViewTests(TestCase):
    def setUp(self):
        self.register_url = reverse("accounts:register")
        self.login_url = reverse("accounts:login")

    def test_get_register_returns_form(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<form")

    def test_post_valid_data_creates_user_and_redirects(self):
        response = self.client.post(self.register_url, {
            "username": "newuser",
            "email": "new@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertRedirects(response, self.login_url)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_post_invalid_data_shows_errors(self):
        response = self.client.post(self.register_url, {
            "username": "",
            "email": "bademail",
            "password1": "123",
            "password2": "456",
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "errorlist")


class UserPasswordResetViewTests(TestCase):
    def setUp(self):
        self.password_reset_url = reverse("accounts:password_reset")
        self.password_reset_done_url = reverse("accounts:password_reset_done")

    def test_view_uses_correct_template_and_form(self):
        response = self.client.get(self.password_reset_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/password_reset.html")
        self.assertIsInstance(response.context["form"], UserPasswordResetForm)

    def test_post_valid_email_redirects(self):
        self.client.post(reverse("accounts:register"), {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        response = self.client.post(self.password_reset_url, {
            "email": "test@example.com"
        })
        self.assertRedirects(response, self.password_reset_done_url)


class UserPasswordResetConfirmViewTests(SimpleTestCase):
    def test_view_configuration(self):
        view = UserPasswordResetConfirmView()
        self.assertEqual(
            view.template_name, "accounts/password_reset_confirm.html")
        self.assertEqual(view.form_class, UserSetPasswordForm)
        self.assertEqual(
            str(view.success_url), reverse("accounts:password_reset_complete"))


class UserPasswordChangeViewTests(SimpleTestCase):
    def test_view_configuration(self):
        view = UserPasswordChangeView()
        self.assertEqual(
            view.template_name, "registration/password_change_form.html")
        self.assertEqual(view.form_class, UserPasswordChangeForm)
        self.assertEqual(
            str(view.success_url), reverse("accounts:password_change_done"))
