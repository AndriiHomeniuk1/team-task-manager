from typing import Dict
from django.test import TestCase


class BaseRedirectTests(TestCase):
    # Mapping: action name ("list", "create", etc.) -> URL string
    urls_to_test: Dict[str, str] = {}

    def test_redirects_if_not_logged_in(self):
        for name, url in self.urls_to_test.items():
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 302, f"Failed for {name} ({url})")
