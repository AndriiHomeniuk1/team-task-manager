from django.test import TestCase, RequestFactory

from tasks.views import PageSizeMixin


class MixinTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_valid_page_size(self):
        request = self.factory.get("/?page_size=10")
        mixin = PageSizeMixin()
        mixin.request = request
        self.assertEqual(mixin.get_paginate_by(None), 10)

    def test_invalid_page_size(self):
        request = self.factory.get("/?page_size=abc")
        mixin = PageSizeMixin()
        mixin.request = request
        self.assertEqual(mixin.get_paginate_by(None), 5)

    def test_missing_page_size_default(self):
        request = self.factory.get("/")
        mixin = PageSizeMixin()
        mixin.request = request
        self.assertEqual(mixin.get_paginate_by(None), 5)

    def test_custom_paginate_by_attribute(self):
        request = self.factory.get("/")

        class CustomView(PageSizeMixin):
            paginate_by = 20

        view = CustomView()
        view.request = request
        self.assertEqual(view.get_paginate_by(None), 20)
