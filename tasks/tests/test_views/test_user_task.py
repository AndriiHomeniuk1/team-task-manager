from django.urls import reverse
from tasks.tests.test_views.test_task import BaseTaskTests
from tasks.tests.test_views.test_redirect_base import BaseRedirectTests


class UserTaskRedirectTests(BaseRedirectTests):
    def setUp(self):
        super().setUp()
        self.urls_to_test = {
            "user_tasks": reverse("tasks:user-task-list"),
        }


class UserTaskListViewTests(BaseTaskTests):
    def setUp(self):
        super().setUp()
        self.url_user_tasks = reverse("tasks:user-task-list")
        self.response = self.client.get(self.url_user_tasks)

    def test_list_view_access_logged_in(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertIn("tasks", self.response.context)

    def test_queryset_only_user_tasks(self):
        tasks = self.response.context["tasks"]
        self.assertIn(self.task1, tasks)
        self.assertNotIn(self.task2, tasks)

    def test_pagination_limit(self):
        tasks = self.response.context["tasks"]
        self.assertLessEqual(len(tasks), self.expected_paginate_by)

    def test_search_filter_by_name(self):
        response = self.client.get(self.url_user_tasks, {
            "search": " ".join(self.task1.name.split()[:2])
        })
        tasks = response.context["tasks"]
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].name, self.task1.name)

    def test_search_filter_by_pk(self):
        response = self.client.get(
            self.url_user_tasks, {"search": str(self.task1.pk)})
        tasks = response.context["tasks"]
        self.assertIn(self.task1, tasks)

    def test_filter_by_completed(self):
        response = self.client.get(
            self.url_user_tasks, {"key": "is_completed", "value": "true"}
        )
        tasks = response.context["tasks"]
        self.assertTrue(all(t.is_completed for t in tasks))

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
        self.assertEqual(
            self.response.context["next_url"], self.url_user_tasks)
