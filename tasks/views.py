from typing import Any, Optional

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    PermissionRequiredMixin,
)
from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic

from tasks.models import Position, TaskType, Worker, Task
from .utils import (
    get_position_messages,
    apply_search,
)


class PageSizeMixin:
    request: HttpRequest

    def get_paginate_by(self, queryset: QuerySet[Any]) -> Optional[int]:
        page_size = self.request.GET.get("page_size")
        if page_size:
            try:
                return int(page_size)
            except ValueError:
                pass
        return getattr(self, "paginate_by", 5)


@login_required
def index(request: HttpRequest) -> HttpResponse:
    worker = request.user
    tasks_assigned = Task.objects.filter(assignees=worker)

    num_tasks = tasks_assigned.count()
    num_open_tasks = tasks_assigned.filter(is_completed=False).count()
    num_completed_tasks = tasks_assigned.filter(is_completed=True).count()

    completion_percentage = 0
    if num_tasks > 0:
        completion_percentage = round((num_completed_tasks / num_tasks) * 100)

    recent_tasks = tasks_assigned.filter(
        is_completed=False, deadline__gte=timezone.now().date()
    ).order_by("deadline")[:5]

    overdue_tasks = tasks_assigned.filter(
        is_completed=False, deadline__lt=timezone.now().date()
    ).order_by("deadline")[:5]

    context = {
        "num_tasks": num_tasks,
        "num_open_tasks": num_open_tasks,
        "num_completed_tasks": num_completed_tasks,
        "completion_percentage": completion_percentage,
        "recent_tasks": recent_tasks,
        "overdue_tasks": overdue_tasks,
    }

    return render(request, "tasks/index.html", context)


@login_required
def profile(request):
    return render(
        request,
        "tasks/profile.html",
        {"worker": request.user}
    )


class PositionListView(LoginRequiredMixin, PageSizeMixin, generic.ListView):
    model = Position
    context_object_name = "positions"
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = apply_search(queryset, self.request.GET, ["name"])
        return queryset


class PositionCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView
):
    model = Position
    fields = [
        "name",
    ]
    template_name = "tasks/position_form.html"
    success_url = reverse_lazy("tasks:position-list")
    permission_required = "tasks.add_position"


class PositionUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView
):
    model = Position
    fields = [
        "name",
    ]
    template_name = "tasks/position_form.html"
    success_url = reverse_lazy("tasks:position-list")
    permission_required = "tasks.change_position"


class PositionDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView
):
    model = Position
    template_name = "tasks/confirm_delete.html"
    success_url = reverse_lazy("tasks:position-list")
    permission_required = "tasks.delete_position"
    MAX_DISPLAY = 5

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workers = self.object.workers.all()
        total_count = workers.count()
        extra_workers_count = workers.count() - self.MAX_DISPLAY

        context.update(
            {
                "delete_type": "position",
                "success_url": self.success_url,
                "position_workers_display": workers[: self.MAX_DISPLAY],
                "position_extra_workers_count": extra_workers_count,
            }
        )

        context.update(
            get_position_messages(
                self.object, total_count, extra_workers_count)
        )

        return context


class TaskTypeListView(generic.ListView):
    model = TaskType
    template_name = "tasks/task_type_list.html"
    context_object_name = "task_type_list"


class WorkerListView(generic.ListView):
    model = Worker


class TaskListView(generic.ListView):
    model = Task
