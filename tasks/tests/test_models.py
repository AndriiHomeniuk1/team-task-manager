import tempfile
import shutil
from datetime import date

from PIL import Image

from django.test import TestCase, override_settings
from django.db import IntegrityError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError

from tasks.models import Position, TaskType, Worker, Task


TEST_MEDIA_ROOT = tempfile.mkdtemp()

@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ModelTests(TestCase):
    def setUp(self):
        self.worker = Worker.objects.create(
            username="john_doe",
            password="testpassword123",
            first_name="John",
            last_name="Doe"
        )
        self.assignee = Worker.objects.create(
            username="assignee",
            password="pass123"
        )
        self.position = Position.objects.create(name="QA")
        self.task_type = TaskType.objects.create(name="Bug")
        self.task = Task.objects.create(
            name="Base task",
            description="Universal task for tests",
            deadline=date(2026, 5, 3),
            task_type=self.task_type,
            created_by=self.worker
        )

    def test_position_str(self):
        self.assertEqual(str(self.position), "QA")

    def test_position_unique_constraint(self):
        with self.assertRaises(IntegrityError):
            Position.objects.create(name="QA")

    def test_tasktype_str(self):
        self.assertEqual(str(self.task_type), "Bug")

    def test_tasktype_unique_constraint(self):
        with self.assertRaises(IntegrityError):
            TaskType.objects.create(name="Bug")

    def test_worker_str(self):
        self.assertEqual(str(self.worker), "john_doe: (John Doe)")

    def test_worker_avatar_invalid_file(self):
        invalid_file = SimpleUploadedFile(
            "test.txt",
            b"file_content",
            content_type="text/plain"
        )
        self.worker.avatar = invalid_file
        with self.assertRaises(ValidationError):
            self.worker.full_clean()

    def test_worker_avatar_valid_file(self):
        valid_file = SimpleUploadedFile(
            "test.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        self.worker.avatar = valid_file
        self.worker.full_clean()
        self.assertIsNotNone(self.worker.avatar)

    def test_worker_avatar_resized_on_save(self):
        img = Image.new("RGB", (2000, 1500), color="red")
        tmp_file = tempfile.NamedTemporaryFile(suffix=".jpg")
        img.save(tmp_file, format="JPEG")
        tmp_file.seek(0)

        uploaded = SimpleUploadedFile(
            "big.jpg",
            tmp_file.read(),
            content_type="image/jpeg"
        )

        self.worker.avatar = uploaded
        self.worker.save()

        img_after = Image.open(self.worker.avatar.path)

        self.assertLessEqual(img_after.width, 800)
        self.assertLessEqual(img_after.height, 800)

    def test_task_str(self):
        self.assertEqual(str(self.task), "Base task (Till: 2026-05-03)")

    def test_task_priority_default(self):
        self.assertEqual(self.task.priority, "medium")

    def test_task_is_completed_default(self):
        self.assertFalse(self.task.is_completed)

    def test_task_assignees_relationship(self):
        self.task.assignees.add(self.assignee)
        self.assertIn(self.assignee, self.task.assignees.all())

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)
