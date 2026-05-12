from django.test import TestCase
from django.urls import reverse

from tasks.models import Worker
from tasks.tests.test_views.test_redirect_base import BaseRedirectTests


class ProfileRedirectTests(BaseRedirectTests):
    def setUp(self):
        super().setUp()
        self.urls_to_test = {
            "profile": reverse("tasks:profile"),
        }


class ProfileTests(TestCase):
    def setUp(self):
        self.worker = Worker.objects.create_user(
            username="john_doe",
            password="testpassword123",
            first_name="John",
            last_name="Doe",
        )
        self.client.login(username="john_doe", password="testpassword123")
        self.response = self.client.get(reverse("tasks:profile"))

    def test_profile_access_logged_in(self):
        self.assertEqual(self.response.status_code, 200)

    def test_profile_context_worker(self):
        self.assertEqual(self.response.context["worker"], self.worker)

    def test_profile_template_used(self):
        self.assertTemplateUsed(self.response, "tasks/profile.html")
