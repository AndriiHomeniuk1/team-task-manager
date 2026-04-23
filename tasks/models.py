from PIL import Image

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models

from .utils import user_avatar_path


class Priority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    URGENT = "urgent", "Urgent"


class Position(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class TaskType(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Worker(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="workers",
    )
    avatar = models.ImageField(
        upload_to=user_avatar_path,
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(
                allowed_extensions=["jpg", "jpeg", "png", "gif", "webp"]
            )
        ],
    )

    class Meta:
        ordering = (
            "position",
            "username",
        )

    def __str__(self):
        return f"{self.username}: ({self.first_name} {self.last_name})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.avatar:
            img = Image.open(self.avatar.path)
            max_size = (800, 800)
            img.thumbnail(max_size)
            img.save(self.avatar.path)


class Task(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    deadline = models.DateField()
    is_completed = models.BooleanField(default=False)
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )
    task_type = models.ForeignKey(
        TaskType, on_delete=models.PROTECT, related_name="tasks"
    )
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="tasks"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_tasks"
    )

    class Meta:
        ordering = (
            "deadline",
            "priority",
        )

    def __str__(self):
        return f"{self.name} (Till: {self.deadline.strftime('%Y-%m-%d')})"
