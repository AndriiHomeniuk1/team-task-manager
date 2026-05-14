from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model

from tasks.models import Task, TaskType
from tasks.views import TaskListView
from tasks.tests.test_views.test_redirect_base import BaseRedirectTests


User = get_user_model()

class BaseTaskTests(TestCase):
    def setUp(self):
        self.worker = User.objects.create_user(
            username="john_doe",
            password="testpassword123",
            first_name="John",
            last_name="Doe",
            is_active=True,
        )
        self.client.login(username="john_doe", password="testpassword123")

        self.other_user = User.objects.create_user(
            username="anna_dev",
            password="pass123",
            first_name="Anna",
            last_name="Smith",
            is_active=True,
        )

        self.task_type_bug = TaskType.objects.create(name="Bug")
        self.task_type_feature = TaskType.objects.create(name="Feature")

        self.task1 = Task.objects.create(
            name="Fix login bug",
            description="Critical bug in login flow",
            deadline=date.today() + timedelta(days=3),
            is_completed=False,
            priority="high",
            task_type=self.task_type_bug,
            created_by=self.worker,
        )
        self.task1.assignees.add(self.worker)

        self.task2 = Task.objects.create(
            name="Add search feature",
            description="Implement search in task list",
            deadline=date.today() - timedelta(days=2),
            is_completed=True,
            priority="medium",
            task_type=self.task_type_feature,
            created_by=self.other_user,
        )
        self.task2.assignees.add(self.other_user)

        self.url_list = reverse("tasks:task-list")
        self.url_detail = reverse(
            "tasks:task-detail", args=[self.task1.pk])
        self.url_create = reverse("tasks:task-create")
        self.url_update = reverse(
            "tasks:task-update", args=[self.task1.pk])
        self.url_update_other = reverse(
            "tasks:task-update", args=[self.task2.pk])
        self.url_delete = reverse(
            "tasks:task-delete", args=[self.task1.pk])
        self.url_delete_other = reverse(
            "tasks:task-delete", args=[self.task2.pk])

        self.expected_paginate_by = TaskListView.paginate_by

        for i in range(5):
            task = Task.objects.create(
                name=f"Task{i}",
                description="Test task",
                deadline=date.today() + timedelta(days=i+1),
                is_completed=False,
                priority="low",
                task_type=self.task_type_bug,
                created_by=self.worker,
            )
            task.assignees.add(self.worker)


class TaskRedirectTests(BaseTaskTests, BaseRedirectTests):
    def setUp(self):
        super().setUp()
        self.client.logout()
        self.urls_to_test = {
            "list": self.url_list,
            "detail": self.url_detail,
            "create": self.url_create,
            "update": self.url_update,
            "delete": self.url_delete,
        }


class TaskListViewTests(BaseTaskTests):
    def setUp(self):
        super().setUp()
        self.response = self.client.get(self.url_list)

    def test_list_view_access_logged_in(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertIn("tasks", self.response.context)

    def test_pagination_limit(self):
        tasks = self.response.context["tasks"]
        self.assertLessEqual(len(tasks), self.expected_paginate_by)

    def test_search_filter_by_name(self):
        response = self.client.get(
            self.url_list,
            {"search": " ".join(self.task1.name.split()[:2])}
        )
        tasks = response.context["tasks"]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].name, self.task1.name)

    def test_search_filter_by_pk(self):
        response = self.client.get(
            self.url_list, {"search": str(self.task2.pk)})
        tasks = response.context["tasks"]
        self.assertIn(self.task2, tasks)

    def test_filter_by_completed(self):
        response = self.client.get(
            self.url_list, {"key": "is_completed", "value": "true"})
        tasks = response.context["tasks"]
        self.assertTrue(all(t.is_completed for t in tasks))

    def test_filter_by_deadline_range(self):
        deadline_from = (date.today()).isoformat()
        deadline_to = (date.today() + timedelta(days=3)).isoformat()

        response = self.client.get(self.url_list, {
            "deadline_from": deadline_from,
            "deadline_to": deadline_to,
        })
        tasks = response.context["tasks"]

        for t in tasks:
            self.assertTrue(
                date.fromisoformat(
                    deadline_from) <= t.deadline <= date.fromisoformat(
                    deadline_to)
            )

        self.assertNotIn(self.task2, tasks)

    def test_priorities_in_context(self):
        self.assertIn("priorities", self.response.context)
        priorities = self.response.context["priorities"]
        self.assertTrue({"low", "medium", "high", "urgent"}.issubset(
            dict(priorities).keys()))

    def test_completed_choices_in_context(self):
        self.assertIn("completed_choices", self.response.context)
        self.assertEqual(
            self.response.context["completed_choices"],
            [("true", "True"), ("false", "False")]
        )

    def test_task_types_in_context(self):
        self.assertIn("task_types", self.response.context)
        task_types = self.response.context["task_types"]
        self.assertIn(self.task_type_bug, task_types)
        self.assertIn(self.task_type_feature, task_types)

    def test_next_url_in_context(self):
        self.assertIn("next_url", self.response.context)
        self.assertEqual(self.response.context["next_url"], self.url_list)


class TaskDetailViewTests(BaseTaskTests):
    def setUp(self):
        super().setUp()
        self.response = self.client.get(self.url_detail)

    def test_access_logged_in(self):
        self.assertEqual(self.response.status_code, 200)

    def test_template_used(self):
        self.assertTemplateUsed(self.response, "tasks/task_detail.html")

    def test_context_contains_task(self):
        self.assertIn("task", self.response.context)
        self.assertEqual(self.response.context["task"], self.task1)

    def test_next_url_in_context(self):
        self.assertIn("next_url", self.response.context)
        self.assertEqual(self.response.context["next_url"], self.url_list)


class TaskCreateViewTests(BaseTaskTests):
    def test_access_logged_in(self):
        response = self.client.get(self.url_create)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/task_form.html")

    def test_create_success(self):
        response = self.client.post(self.url_create, {
            "name": "New Task",
            "description": "Test description",
            "deadline": date.today() + timedelta(days=5),
            "is_completed": False,
            "priority": "medium",
            "task_type": self.task_type_bug.pk,
            "assignees": [self.worker.pk],
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url_list)

        task = Task.objects.get(name="New Task")
        self.assertEqual(task.description, "Test description")
        self.assertEqual(task.created_by, self.worker)
        self.assertIn(self.worker, task.assignees.all())

    def test_create_invalid_data(self):
        response = self.client.post(self.url_create, {
            "name": "",
            "description": "Invalid task",
            "deadline": date.today() + timedelta(days=5),
            "priority": "medium",
            "task_type": self.task_type_bug.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"], "name", "This field is required.")


class TaskUpdateViewTests(BaseTaskTests):
    def test_access_logged_in_owner(self):
        response = self.client.get(self.url_update)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/task_form.html")

    def test_access_other_user_forbidden(self):
        response = self.client.get(self.url_update_other)
        self.assertEqual(response.status_code, 403)

    def test_access_with_permission(self):
        permission = Permission.objects.get(codename="change_task")
        self.worker.user_permissions.add(permission)
        response = self.client.get(self.url_update_other)
        self.assertEqual(response.status_code, 200)

    def test_update_success(self):
        response = self.client.post(self.url_update, {
            "name": "Updated Task",
            "description": "Updated description",
            "deadline": date.today() + timedelta(days=20),
            "is_completed": True,
            "priority": "low",
            "task_type": self.task_type_feature.pk,
            "assignees": [self.worker.pk],
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url_detail)
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.name, "Updated Task")
        self.assertTrue(self.task1.is_completed)

    def test_update_success_with_next_param(self):
        url_with_next = f"{self.url_update}?next={self.url_list}"
        response = self.client.post(url_with_next, {
            "name": "Task With Next",
            "description": "Next param test",
            "deadline": date.today() + timedelta(days=10),
            "is_completed": False,
            "priority": "medium",
            "task_type": self.task_type_bug.pk,
            "assignees": [self.worker.pk],
        })
        self.assertEqual(response.status_code, 302)
        expected_redirect = (
            f"{self.url_detail}"
            f"?next={self.url_list}"
        )
        self.assertRedirects(response, expected_redirect)

    def test_update_invalid_data(self):
        response = self.client.post(self.url_update, {
            "name": "",
            "description": "Invalid update",
            "deadline": date.today() + timedelta(days=5),
            "priority": "medium",
            "task_type": self.task_type_bug.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"], "name", "This field is required.")

    def test_next_url_in_context(self):
        response = self.client.get(self.url_update)
        self.assertIn("next_url", response.context)
        self.assertEqual(
            response.context["next_url"], self.url_list)


class TaskDeleteViewTests(BaseTaskTests):
    def test_access_logged_in_owner(self):
        response = self.client.get(self.url_delete)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/confirm_delete.html")

    def test_access_other_user_forbidden(self):
        response = self.client.get(self.url_delete_other)
        self.assertEqual(response.status_code, 403)

    def test_access_with_permission(self):
        permission = Permission.objects.get(codename="delete_task")
        self.worker.user_permissions.add(permission)
        response = self.client.get(self.url_delete_other)
        self.assertEqual(response.status_code, 200)

    def test_delete_success_owner(self):
        response = self.client.post(self.url_delete)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url_list)
        self.assertFalse(Task.objects.filter(pk=self.task1.pk).exists())

    def test_delete_success_with_next_param(self):
        url_with_next = f"{self.url_delete}?next={self.url_list}"
        response = self.client.post(url_with_next)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.url_list)
        self.assertFalse(Task.objects.filter(pk=self.task1.pk).exists())

    def test_delete_forbidden_other_user(self):
        response = self.client.post(self.url_delete_other)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Task.objects.filter(pk=self.task2.pk).exists())

    def test_context_contains_expected_keys(self):
        response = self.client.get(self.url_delete)
        self.assertIn("delete_type", response.context)
        self.assertEqual(response.context["delete_type"], "task")
        self.assertIn("success_url", response.context)
        self.assertIn("cancel_url", response.context)
