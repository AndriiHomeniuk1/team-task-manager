from datetime import date

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Permission

from tasks.models import Worker, TaskType, Task
from tasks.views import TaskTypeListView


class BaseTaskTypeTests(TestCase):
    def setUp(self):
        self.url_list = reverse("tasks:task-type-list")
        self.url_create = reverse("tasks:task-type-create")
        self.worker = Worker.objects.create_user(
            username="john_doe",
            password="testpassword123"
        )
        self.client.login(username="john_doe", password="testpassword123")
        self.expected_paginate_by = TaskTypeListView.paginate_by

        TaskType.objects.create(name="Bug")
        TaskType.objects.create(name="Feature")
        self.task_type = TaskType.objects.create(name="OldTaskType")
        self.url_update = reverse(
            "tasks:task-type-update", args=[self.task_type.pk])
        self.url_delete = reverse(
            "tasks:task-type-delete", args=[self.task_type.pk])

        for i in range(6):
            TaskType.objects.create(name=f"TaskType{i}")


class TaskTypeRedirectTests(BaseTaskTypeTests):
    def setUp(self):
        super().setUp()
        self.client.logout()

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, 302)

    def test_redirect_create_if_not_logged_in(self):
        response = self.client.get(self.url_create)
        self.assertEqual(response.status_code, 302)

    def test_redirect_update_if_not_logged_in(self):
        response = self.client.get(self.url_update)
        self.assertEqual(response.status_code, 302)

    def test_redirect_delete_if_not_logged_in(self):
        response = self.client.get(self.url_delete)
        self.assertEqual(response.status_code, 302)


class TaskTypeListViewTests(BaseTaskTypeTests):
    def setUp(self):
        super().setUp()
        self.response = self.client.get(self.url_list)

    def test_list_view_access_logged_in(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertIn("task_types", self.response.context)

    def test_pagination_limit(self):
        task_types = self.response.context["task_types"]
        self.assertEqual(len(task_types), self.expected_paginate_by)

    def test_search_filter(self):
        response = self.client.get(self.url_list, {"search": "Bug"})
        task_types = response.context["task_types"]

        self.assertEqual(len(task_types), 1)
        self.assertEqual(task_types[0].name, "Bug")


class TaskTypeCreateViewTests(BaseTaskTypeTests):
    def setUp(self):
        super().setUp()
        self.perm = Permission.objects.get(codename="add_tasktype")
        self.worker.user_permissions.add(self.perm)

    def test_access_without_permission(self):
        self.worker.user_permissions.remove(self.perm)
        response = self.client.get(self.url_create)
        self.assertEqual(response.status_code, 403)

    def test_access_with_permission(self):
        response = self.client.get(self.url_create)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/task_type_form.html")

    def test_create_success(self):
        response = self.client.post(self.url_create, {"name": "NewTaskType"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url_list)
        self.assertTrue(TaskType.objects.filter(name="NewTaskType").exists())

    def test_create_invalid_data(self):
        response = self.client.post(self.url_create, {"name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "name",
            "This field is required."
        )


class TaskTypeUpdateViewTests(BaseTaskTypeTests):
    def setUp(self):
        super().setUp()
        self.perm = Permission.objects.get(codename="change_tasktype")
        self.worker.user_permissions.add(self.perm)

    def test_access_without_permission(self):
        self.worker.user_permissions.remove(self.perm)
        response = self.client.get(self.url_update)
        self.assertEqual(response.status_code, 403)

    def test_access_with_permission(self):
        response = self.client.get(self.url_update)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/task_type_form.html")

    def test_update_success(self):
        response = self.client.post(
            self.url_update, {"name": "UpdatedTaskType"})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url_list)
        self.task_type.refresh_from_db()
        self.assertEqual(self.task_type.name, "UpdatedTaskType")

    def test_update_invalid_data(self):
        response = self.client.post(self.url_update, {"name": ""})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"],
            "name",
            "This field is required."
        )


class TaskTypeDeleteViewTests(BaseTaskTypeTests):
    def setUp(self):
        super().setUp()
        self.perm = Permission.objects.get(codename="delete_tasktype")
        self.worker.user_permissions.add(self.perm)

    def test_access_without_permission(self):
        self.worker.user_permissions.remove(self.perm)
        response = self.client.get(self.url_delete)
        self.assertEqual(response.status_code, 403)

    def test_access_with_permission(self):
        response = self.client.get(self.url_delete)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/confirm_delete.html")
        self.assertEqual(response.context["delete_type"], "tasktype")
        self.assertIn("tasks_display", response.context)
        self.assertIn("extra_tasks_count", response.context)
        self.assertIn("confirm_message", response.context)
        self.assertIn("assigned_message", response.context)
        self.assertIn("extra_message", response.context)

    def test_delete_success_without_tasks(self):
        response = self.client.post(self.url_delete)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url_list)
        self.assertFalse(TaskType.objects.filter(
            pk=self.task_type.pk).exists())

    def test_delete_redirect_with_tasks(self):
        task = Task.objects.create(
            name="TestTask",
            description="desc",
            deadline=date.today(),
            task_type=self.task_type,
            created_by=self.worker,
        )
        response = self.client.post(self.url_delete)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url_delete)
        self.assertTrue(TaskType.objects.filter(pk=self.task_type.pk).exists())
