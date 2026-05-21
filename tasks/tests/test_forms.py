import tempfile
from datetime import date, timedelta

from PIL import Image

from django import forms
from django.test import TestCase, SimpleTestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model

from tasks.forms import CustomClearableFileInput, WorkerUpdateForm, TaskForm
from tasks.models import TaskType


User = get_user_model()

class CustomClearableFileInputTests(SimpleTestCase):
    def setUp(self):
        self.widget = CustomClearableFileInput()

    def test_render_without_value(self):
        html = self.widget.render("avatar", None, attrs={})
        self.assertIn('<input type="file"', html)
        self.assertNotIn("<img", html)
        self.assertNotIn("Remove avatar", html)

    def test_render_with_value_and_url(self):
        file = SimpleUploadedFile("avatar.png", b"file_content")
        file.url = "/media/avatar.png"
        html = self.widget.render("avatar", file, attrs={})
        self.assertIn('<input type="file"', html)
        self.assertIn('<img src="/media/avatar.png"', html)
        self.assertIn("Remove avatar", html)

    def test_render_with_value_without_url(self):
        file = SimpleUploadedFile("avatar.png", b"file_content")
        html = self.widget.render("avatar", file, attrs={})
        self.assertIn('<input type="file"', html)
        self.assertNotIn("<img", html)
        self.assertIn("Remove avatar", html)


class WorkerUpdateFormTests(TestCase):
    def setUp(self):
        self.worker = User.objects.create_user(
            username="john_doe",
            password="testpassword123",
            email = "john@example.com"
        )

        self.valid_data = {
            "username": "john_doe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
        }

    def test_form_has_expected_fields(self):
        form = WorkerUpdateForm()
        expected_fields = [
            "username",
            "first_name",
            "last_name",
            "position",
            "phone_number",
            "email",
            "location",
            "github_url",
            "avatar",
        ]
        self.assertEqual(list(form.fields.keys()), expected_fields)

    def test_avatar_field_uses_custom_widget(self):
        form = WorkerUpdateForm()
        widget = form.fields["avatar"].widget
        self.assertIsInstance(widget, CustomClearableFileInput)
        self.assertIn("form-control", widget.attrs["class"])
        self.assertIn("rounded-pill", widget.attrs["class"])

    def test_form_valid_with_allowed_avatar_extension(self):
        img = Image.new("RGB", (100, 100), color="red")
        tmp_file = tempfile.NamedTemporaryFile(suffix=".png")
        img.save(tmp_file, format="PNG")
        tmp_file.seek(0)

        file = SimpleUploadedFile(
            "avatar.png", tmp_file.read(), content_type="image/png")

        form = WorkerUpdateForm(
            data=self.valid_data,
            files={"avatar": file},
            instance=self.worker,
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_with_disallowed_avatar_extension(self):
        file = SimpleUploadedFile(
            "avatar.txt", b"file_content", content_type="text/plain")
        form = WorkerUpdateForm(
            data=self.valid_data,
            files={"avatar": file},
            instance=self.worker,
        )
        self.assertFalse(form.is_valid())
        self.assertIn("avatar", form.errors)


class TaskFormTests(TestCase):
    def setUp(self):
        self.creator = User.objects.create_user(
            username="creator", password="pass123", email="creator@example.com"
        )
        self.assignee = User.objects.create_user(
            username="assignee",
            password="pass123",
            email="assignee@example.com"
        )
        self.task_type = TaskType.objects.create(name="Bug")

        self.valid_data = {
            "name": "Fix login bug",
            "description": "Resolve login issue",
            "deadline": date.today() + timedelta(days=2),
            "priority": "medium",
            "is_completed": False,
            "task_type": self.task_type.pk,
            "assignees": [self.assignee.pk],
        }

    def test_form_has_expected_fields(self):
        form = TaskForm()
        expected_fields = [
            "name",
            "description",
            "deadline",
            "priority",
            "is_completed",
            "task_type",
            "assignees",
        ]
        self.assertEqual(list(form.fields.keys()), expected_fields)

    def test_assignees_field_uses_checkbox_widget(self):
        form = TaskForm()
        widget = form.fields["assignees"].widget
        self.assertIsInstance(widget, forms.CheckboxSelectMultiple)

    def test_deadline_field_uses_dateinput_widget(self):
        form = TaskForm()
        widget = form.fields["deadline"].widget
        html = str(form["deadline"])
        self.assertIsInstance(widget, forms.DateInput)
        self.assertIn('type="date"', html)

    def test_is_completed_field_uses_checkboxinput_widget(self):
        form = TaskForm()
        widget = form.fields["is_completed"].widget
        self.assertIsInstance(widget, forms.CheckboxInput)
        self.assertIn("form-check-input", widget.attrs.get("class", ""))

    def test_form_valid_with_correct_data(self):
        form = TaskForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_without_name(self):
        invalid_data = self.valid_data.copy()
        invalid_data.pop("name")
        form = TaskForm(data=invalid_data)
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)
