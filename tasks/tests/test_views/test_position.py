from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Permission

from tasks.models import Worker, Position
from tasks.views import PositionListView
from tasks.tests.test_views.test_redirect_base import BaseRedirectTests


class BasePositionTests(TestCase):
    def setUp(self):
        self.url_list = reverse("tasks:position-list")
        self.url_create = reverse("tasks:position-create")
        self.worker = Worker.objects.create_user(
            username="john_doe",
            password="testpassword123"
        )

        self.client.login(username="john_doe", password="testpassword123")
        self.expected_paginate_by = PositionListView.paginate_by

        Position.objects.create(name="QA")
        Position.objects.create(name="Developer")
        self.position = Position.objects.create(name="OldName")
        self.url_update = reverse(
            "tasks:position-update", args=[self.position.pk])
        self.url_delete = reverse(
            "tasks:position-delete",args=[self.position.pk])

        for i in range(6):
            Position.objects.create(name=f"Position{i}")


class PositionRedirectTests(BasePositionTests, BaseRedirectTests):
    def setUp(self):
        super().setUp()
        self.client.logout()
        self.urls_to_test = {
            "list": self.url_list,
            "create": self.url_create,
            "update": self.url_update,
            "delete": self.url_delete,
        }


class PositionListViewTests(BasePositionTests):
    def setUp(self):
        super().setUp()
        self.response = self.client.get(self.url_list)

    def test_list_view_access_logged_in(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertIn("positions", self.response.context)

    def test_pagination_limit(self):
        positions = self.response.context["positions"]
        self.assertEqual(len(positions), self.expected_paginate_by)

    def test_search_filter(self):
        response = self.client.get(self.url_list, {"search": "QA"})
        positions = response.context["positions"]
        self.assertEqual(len(positions), 1)
        self.assertEqual(positions[0].name, "QA")


class PositionCreateViewTests(BasePositionTests):
    def setUp(self):
        super().setUp()
        self.perm = Permission.objects.get(codename="add_position")
        self.worker.user_permissions.add(self.perm)

    def test_access_without_permission(self):
        self.worker.user_permissions.remove(self.perm)
        response = self.client.get(self.url_create)
        self.assertEqual(response.status_code, 403)

    def test_access_with_permission(self):
        response = self.client.get(self.url_create)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/position_form.html")

    def test_create_success(self):
        response = self.client.post(self.url_create, {"name": "NewPosition"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url_list)
        self.assertTrue(Position.objects.filter(name="NewPosition").exists())

    def test_create_invalid_data(self):
        response = self.client.post(self.url_create, {"name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "name",
            "This field is required."
        )


class PositionUpdateViewTests(BasePositionTests):
    def setUp(self):
        super().setUp()
        self.perm = Permission.objects.get(codename="change_position")
        self.worker.user_permissions.add(self.perm)

    def test_access_without_permission(self):
        self.worker.user_permissions.remove(self.perm)
        response = self.client.get(self.url_update)
        self.assertEqual(response.status_code, 403)

    def test_access_with_permission(self):
        response = self.client.get(self.url_update)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "tasks/position_form.html")

    def test_update_success(self):
        response = self.client.post(self.url_update, {"name": "UpdateName"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url_list)
        self.position.refresh_from_db()
        self.assertEqual(self.position.name, "UpdateName")

    def test_update_invalid_data(self):
        response = self.client.post(self.url_update, {"name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "name",
            "This field is required."
        )


class PositionDeleteViewTests(BasePositionTests):
    def setUp(self):
        super().setUp()
        self.perm = Permission.objects.get(codename="delete_position")
        self.worker.user_permissions.add(self.perm)

    def test_access_without_permission(self):
        self.worker.user_permissions.remove(self.perm)
        response = self.client.get(self.url_delete)
        self.assertEqual(response.status_code, 403)

    def test_access_with_permission(self):
        response = self.client.get(self.url_delete)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/confirm_delete.html")
        self.assertEqual(response.context["delete_type"], "position")
        self.assertIn("position_workers_display", response.context)
        self.assertIn("position_extra_workers_count", response.context)
        self.assertIn("confirm_message", response.context)
        self.assertIn("warning_message", response.context)

    def test_delete_success(self):
        response = self.client.post(self.url_delete)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url_list)
        self.assertFalse(Position.objects.filter(pk=self.position.pk).exists())
