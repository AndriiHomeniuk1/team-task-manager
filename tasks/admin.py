from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from  tasks.models import (
    Position,
    TaskType,
    Worker,
    Task,
)


admin.site.unregister(Group)
admin.site.register(Position)
admin.site.register(TaskType)

@admin.register(Worker)
class WorkerAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ("position", )
    fieldsets = UserAdmin.fieldsets + (
        ("Additional info", {"fields": ("position",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Additional info", {"fields": ("first_name", "last_name", "position",)}),
    )

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["task_type", "name", "priority", "deadline", "is_completed",]
    list_filter = ["priority", "deadline", "is_completed", "task_type",]
    search_fields = ["name",]
    list_editable = ["is_completed",]
