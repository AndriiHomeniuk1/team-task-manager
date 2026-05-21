from django.test import TestCase
from django.contrib.auth import get_user_model
from accounts.forms import (
    RegistrationForm,
    LoginForm,
    UserPasswordResetForm,
    UserSetPasswordForm,
    UserPasswordChangeForm,
)


User = get_user_model()

class BaseUserFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="OldPass123!"
        )


class RegistrationFormTests(TestCase):
    def test_form_has_correct_fields(self):
        form = RegistrationForm()
        self.assertIn("username", form.fields)
        self.assertIn("email", form.fields)
        self.assertIn("password1", form.fields)
        self.assertIn("password2", form.fields)
        self.assertEqual(
            form.fields["username"].widget.attrs["placeholder"],
            "Username"
        )
        self.assertEqual(
            form.fields["email"].widget.attrs["placeholder"],
            "Email"
        )
        self.assertEqual(
            form.fields["password1"].widget.attrs["placeholder"],
            "Password"
        )
        self.assertEqual(
            form.fields["password2"].widget.attrs["placeholder"],
            "Password Confirmation"
        )

    def test_valid_data_creates_user(self):
        form = RegistrationForm(data={
            "username": "newuser",
            "email": "new@example.com",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        })
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertIsInstance(user, User)
        self.assertEqual(user.username, "newuser")
        self.assertEqual(user.email, "new@example.com")

    def test_passwords_do_not_match(self):
        form = RegistrationForm(data={
            "username": "newuser",
            "email": "new@example.com",
            "password1": "StrongPass123!",
            "password2": "WrongPass456!",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)


class LoginFormTests(BaseUserFormTests):
    def test_form_has_correct_fields(self):
        form = LoginForm()
        self.assertIn("username", form.fields)
        self.assertIn("password", form.fields)
        self.assertEqual(
            form.fields["username"].widget.attrs["placeholder"],
            "Username"
        )
        self.assertEqual(
            form.fields["password"].widget.attrs["placeholder"],
            "Password"
        )

    def test_valid_login(self):
        form = LoginForm(data={
            "username": "testuser",
            "password": "OldPass123!"
        })
        self.assertTrue(form.is_valid())

    def test_invalid_password(self):
        form = LoginForm(data={
            "username": "testuser",
            "password": "WrongPass456!"
        })
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)


class UserPasswordResetFormTests(BaseUserFormTests):
    def test_form_has_email_field(self):
        form = UserPasswordResetForm()
        self.assertIn("email", form.fields)
        self.assertEqual(
            form.fields["email"].widget.attrs["placeholder"], "Email"
        )

    def test_valid_email_existing_user(self):
        form = UserPasswordResetForm(data={"email": "test@example.com"})
        self.assertTrue(form.is_valid())

    def test_invalid_email_format(self):
        form = UserPasswordResetForm(data={"email": "not-an-email"})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_nonexistent_user_email(self):
        form = UserPasswordResetForm(data={"email": "nouser@example.com"})
        self.assertTrue(form.is_valid())


class UserSetPasswordFormTests(BaseUserFormTests):
    def test_form_has_correct_fields(self):
        form = UserSetPasswordForm(user=self.user)
        self.assertIn("new_password1", form.fields)
        self.assertIn("new_password2", form.fields)
        self.assertEqual(
            form.fields["new_password1"].widget.attrs["placeholder"],
            "New Password"
        )
        self.assertEqual(
            form.fields["new_password2"].widget.attrs["placeholder"],
            "Confirm New Password"
        )

    def test_valid_passwords_update_user_password(self):
        form = UserSetPasswordForm(user=self.user, data={
            "new_password1": "StrongPass123!",
            "new_password2": "StrongPass123!",
        })
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password("StrongPass123!"))

    def test_passwords_do_not_match(self):
        form = UserSetPasswordForm(user=self.user, data={
            "new_password1": "StrongPass123!",
            "new_password2": "WrongPass456!",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("new_password2", form.errors)


class UserPasswordChangeFormTests(BaseUserFormTests):
    def test_form_has_correct_fields(self):
        form = UserPasswordChangeForm(user=self.user)
        self.assertIn("old_password", form.fields)
        self.assertIn("new_password1", form.fields)
        self.assertIn("new_password2", form.fields)
        self.assertEqual(
            form.fields["old_password"].widget.attrs["placeholder"],
            "Old Password"
        )
        self.assertEqual(
            form.fields["new_password1"].widget.attrs["placeholder"],
            "New Password"
        )
        self.assertEqual(
            form.fields["new_password2"].widget.attrs["placeholder"],
            "Confirm New Password"
        )

    def test_valid_password_change(self):
        form = UserPasswordChangeForm(user=self.user, data={
            "old_password": "OldPass123!",
            "new_password1": "StrongPass123!",
            "new_password2": "StrongPass123!",
        })
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password("StrongPass123!"))

    def test_invalid_old_password(self):
        form = UserPasswordChangeForm(user=self.user, data={
            "old_password": "WrongOldPass!",
            "new_password1": "StrongPass123!",
            "new_password2": "StrongPass123!",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("old_password", form.errors)

    def test_new_passwords_do_not_match(self):
        form = UserPasswordChangeForm(user=self.user, data={
            "old_password": "OldPass123!",
            "new_password1": "StrongPass123!",
            "new_password2": "WrongPass456!",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("new_password2", form.errors)
