from datetime import date, timedelta

from django.test import TestCase
from django.urls import reverse

from tasks.models import TaskType, Worker, Task


class IndexRedirectTests(TestCase):
    def setUp(self):
        self.worker = Worker.objects.create_user(
            username="john_doe",
            password="testpassword123"
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("tasks:index"))
        self.assertEqual(response.status_code, 302)


class IndexTests(TestCase):
    def setUp(self):
        self.worker = Worker.objects.create_user(
            username="john_doe",
            password="testpassword123",
            first_name="John",
            last_name="Doe"
        )
        self.task_type = TaskType.objects.create(name="Bug")

        Task.objects.create(
            name="Completed",
            deadline=date.today(),
            task_type=self.task_type,
            created_by=self.worker,
            is_completed=True
        ).assignees.add(self.worker)

        Task.objects.create(
            name="Recent Open1",
            deadline=date.today() + timedelta(days=2),
            task_type=self.task_type,
            created_by=self.worker,
            is_completed=False
        ).assignees.add(self.worker)

        Task.objects.create(
            name="Overdue Open2",
            deadline=date.today() - timedelta(days=2),
            task_type=self.task_type,
            created_by=self.worker,
            is_completed=False
        ).assignees.add(self.worker)

        self.client.login(username="john_doe", password="testpassword123")
        self.response = self.client.get(reverse("tasks:index"))
        self.context = self.response.context

    def test_index_access_logged_in(self):
        self.assertEqual(self.response.status_code, 200)

    def test_index_context_counts(self):
        num_tasks = Task.objects.filter(assignees=self.worker).count()
        num_completed = Task.objects.filter(
            assignees=self.worker, is_completed=True).count()

        expected_percentage = round(
            (num_completed / num_tasks) * 100) if num_tasks > 0 else 0

        self.assertEqual(self.context["num_tasks"], num_tasks)
        self.assertEqual(
            self.context["num_open_tasks"], num_tasks - num_completed)
        self.assertEqual(self.context["num_completed_tasks"], num_completed)
        self.assertEqual(
            self.context["completion_percentage"], expected_percentage)

    def test_recent_and_overdue_tasks(self):
        recent_names = [task.name for task in self.context["recent_tasks"]]
        overdue_names = [task.name for task in self.context["overdue_tasks"]]

        self.assertIn("Recent Open1", recent_names)
        self.assertIn("Overdue Open2", overdue_names)
