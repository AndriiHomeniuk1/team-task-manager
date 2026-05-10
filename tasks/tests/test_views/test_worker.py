from django.test import TestCase
from django.urls import reverse

from tasks.models import Worker, Position
from tasks.views import WorkerListView


class BaseWorkerTests(TestCase):
    def setUp(self):
        self.position_dev = Position.objects.create(name="Developer")
        self.position_qa = Position.objects.create(name="QA")

        self.worker = Worker.objects.create_user(
            username="john_doe",
            password="testpassword123",
            first_name="John",
            last_name="Doe",
            position=self.position_qa,
            is_active=True,
        )
        self.client.login(username="john_doe", password="testpassword123")

        self.other_worker = Worker.objects.create_user(
            username="anna_dev",
            password="pass345",
            first_name="Anna",
            last_name="Smith",
            position=self.position_dev,
            is_active=True,
        )
        Worker.objects.create_user(
            username="inactive_user",
            password="pass321",
            first_name="Inactive",
            last_name="Guy",
            is_active=False,
        )

        self.url_list = reverse("tasks:worker-list")
        self.url_detail = reverse(
            "tasks:worker-detail", args=[self.worker.pk])
        self.url_update_self = reverse(
            "tasks:worker-update", args=[self.worker.pk])
        self.url_update_other = reverse(
            "tasks:worker-update", args=[self.other_worker.pk])
        self.url_deactivate_self = reverse(
            "tasks:worker-deactivate", args=[self.worker.pk])
        self.url_deactivate_other = reverse(
            "tasks:worker-deactivate", args=[self.other_worker.pk])

        self.expected_paginate_by = WorkerListView.paginate_by

        for i in range(5):
            Worker.objects.create_user(
                username=f"user{i}",
                password="pass123",
                first_name=f"First{i}",
                last_name=f"Last{i}",
                is_active=True,
            )


class WorkerRedirectTests(BaseWorkerTests):
    def setUp(self):
        super().setUp()
        self.client.logout()

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, 302)

    def test_redirect_detail_if_not_logged_in(self):
        response = self.client.get(self.url_detail)
        self.assertEqual(response.status_code, 302)

    def test_redirect_update_if_not_logged_in(self):
        response = self.client.get(self.url_update_self)
        self.assertEqual(response.status_code, 302)

    def test_redirect_deactivate_if_not_logged_in_self(self):
        response = self.client.get(self.url_deactivate_self)
        self.assertEqual(response.status_code, 302)


class WorkerListViewTests(BaseWorkerTests):
    def setUp(self):
        super().setUp()
        self.response = self.client.get(self.url_list)

    def test_list_view_access_logged_in(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertIn("workers", self.response.context)

    def test_pagination_limit(self):
        workers = self.response.context["workers"]
        self.assertLessEqual(len(workers), self.expected_paginate_by)

    def test_only_active_workers_displayed(self):
        workers = self.response.context["workers"]
        self.assertTrue(all(w.is_active for w in workers))

    def test_search_filter_by_username(self):
        response = self.client.get(self.url_list, {"search": "anna"})
        workers = response.context["workers"]
        self.assertEqual(len(workers), 1)
        self.assertEqual(workers[0].username, "anna_dev")

    def test_search_filter_by_full_name(self):
        response = self.client.get(self.url_list, {"search": "John Doe"})
        workers = response.context["workers"]
        self.assertEqual(len(workers), 1)
        self.assertEqual(workers[0].username, "john_doe")

    def test_filter_by_position(self):
        response = self.client.get(self.url_list, {"position": ["Developer"]})
        workers = response.context["workers"]
        self.assertTrue(all(w.position.name == "Developer" for w in workers))

    def test_positions_in_context(self):
        self.assertIn("positions", self.response.context)
        positions = self.response.context["positions"]
        self.assertIn(self.position_dev, positions)
        self.assertIn(self.position_qa, positions)


class WorkerDetailViewTests(BaseWorkerTests):
    def setUp(self):
        super().setUp()
        self.response = self.client.get(self.url_detail)

    def test_access_logged_in(self):
        self.assertEqual(self.response.status_code, 200)
        self.assertTemplateUsed(self.response, "tasks/profile.html")

    def test_context_contains_worker(self):
        self.assertIn("worker", self.response.context)
        self.assertEqual(self.response.context["worker"], self.worker)


class WorkerUpdateViewTests(BaseWorkerTests):
    def setUp(self):
        super().setUp()

    def test_access_self_profile(self):
        response = self.client.get(self.url_update_self)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "tasks/worker_form.html")

    def test_access_other_profile_forbidden(self):
        response = self.client.get(self.url_update_other)
        self.assertEqual(response.status_code, 403)

    def test_update_success(self):
        response = self.client.post(self.url_update_self, {
            "username": "john_doe",
            "first_name": "Johnny",
            "last_name": "Doe",
            "email": "john@example.com",
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("tasks:profile"))
        self.worker.refresh_from_db()
        self.assertEqual(self.worker.first_name, "Johnny")
        self.assertEqual(self.worker.email, "john@example.com")

    def test_update_invalid_data(self):
        response = self.client.post(self.url_update_self, {
            "username": "",
            "first_name": "John",
            "last_name": "Doe",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFormError(
            response.context["form"], "username", "This field is required.")


class WorkerSelfDeactivateViewTests(BaseWorkerTests):
    def setUp(self):
        super().setUp()

    def test_access_self_profile(self):
        response = self.client.get(self.url_deactivate_self)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "tasks/worker_confirm_deactivate.html")

    def test_access_other_profile_forbidden(self):
        response = self.client.get(self.url_deactivate_other)
        self.assertEqual(response.status_code, 403)

    def test_deactivate_success(self):
        response = self.client.post(self.url_deactivate_self)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("accounts:login"))
        self.worker.refresh_from_db()
        self.assertFalse(self.worker.is_active)

    def test_deactivate_other_forbidden(self):
        response = self.client.post(self.url_deactivate_other)
        self.assertEqual(response.status_code, 403)
        self.other_worker.refresh_from_db()
        self.assertTrue(self.other_worker.is_active)
