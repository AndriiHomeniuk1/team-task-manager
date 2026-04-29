from typing import Any, Optional

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
    PermissionRequiredMixin,
)
from django.db.models import Value, QuerySet
from django.db.models.functions import Concat
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views import generic

from tasks.models import Position, TaskType, Worker, Task
from .forms import WorkerUpdateForm, TaskForm
from .utils import (
    get_position_messages,
    get_tasktype_messages,
    get_task_messages,
    apply_search,
    filter_tasks,
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


class TaskTypeListView(LoginRequiredMixin, PageSizeMixin, generic.ListView):
    model = TaskType
    template_name = "tasks/task_type_list.html"
    context_object_name = "task_types"
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = apply_search(queryset, self.request.GET, ["name"])
        return queryset


class TaskTypeCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.CreateView
):
    model = TaskType
    fields = ["name"]
    template_name = "tasks/task_type_form.html"
    success_url = reverse_lazy("tasks:task-type-list")
    permission_required = "tasks.add_tasktype"


class TaskTypeUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.UpdateView
):
    model = TaskType
    fields = ["name"]
    template_name = "tasks/task_type_form.html"
    success_url = reverse_lazy("tasks:task-type-list")
    permission_required = "tasks.change_tasktype"


class TaskTypeDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, generic.DeleteView
):
    model = TaskType
    template_name = "tasks/confirm_delete.html"
    success_url = reverse_lazy("tasks:task-type-list")
    permission_required = "tasks.delete_tasktype"
    MAX_DISPLAY = 5

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.tasks.exists():
            return redirect("tasks:task-type-delete", pk=self.object.pk)
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = self.object.tasks.all()
        total_count = tasks.count()
        extra_tasks_count = tasks.count() - self.MAX_DISPLAY

        context.update(
            {
                "delete_type": "tasktype",
                "success_url": self.success_url,
                "tasks_display": tasks[: self.MAX_DISPLAY],
                "extra_tasks_count": extra_tasks_count,
            }
        )
        context.update(
            get_tasktype_messages(self.object, total_count, extra_tasks_count)
        )

        return context


class WorkerListView(LoginRequiredMixin, PageSizeMixin, generic.ListView):
    model = Worker
    context_object_name = "workers"
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(is_active=True)
        queryset = queryset.annotate(
            full_name=Concat("first_name", Value(" "), "last_name")
        )
        queryset = apply_search(
            queryset,
            self.request.GET,
            ["username", "first_name", "last_name", "full_name"],
        )

        positions = self.request.GET.getlist("position")
        if positions:
            queryset = queryset.filter(position__name__in=positions)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["positions"] = Position.objects.all()
        return context


class WorkerDetailView(LoginRequiredMixin, generic.DetailView):
    model = Worker
    template_name = "tasks/profile.html"
    context_object_name = "worker"


class WorkerUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    generic.UpdateView
):
    model = Worker
    form_class = WorkerUpdateForm
    template_name = "tasks/worker_form.html"
    context_object_name = "worker"
    success_url = reverse_lazy("tasks:worker-list")

    def test_func(self):
        worker = self.get_object()
        return worker == self.request.user


class WorkerSelfDeactivateView(
    LoginRequiredMixin, UserPassesTestMixin, generic.UpdateView
):
    model = Worker
    template_name = "tasks/worker_confirm_deactivate.html"
    context_object_name = "worker"
    fields = []
    success_url = reverse_lazy("accounts:login")

    def test_func(self):
        worker = self.get_object()
        return worker == self.request.user

    def form_valid(self, form):
        worker = form.instance
        worker.is_active = False
        worker.save(update_fields=["is_active"])
        return super().form_valid(form)


class TaskListView(LoginRequiredMixin, PageSizeMixin, generic.ListView):
    model = Task
    context_object_name = "tasks"
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = apply_search(
            queryset,
            self.request.GET,
            [
                "name",
                "pk",
            ],
        )
        queryset = filter_tasks(queryset, self.request.GET)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "priorities": Task._meta.get_field("priority").choices,
                "completed_choices": [("true", "True"), ("false", "False")],
                "task_types": TaskType.objects.all(),
                "next_url": reverse("tasks:task-list"),
            }
        )
        return context


class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    model = Task

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next_url"] = reverse("tasks:task-list")
        return context


class TaskCreateView(LoginRequiredMixin, generic.CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"
    success_url = reverse_lazy("tasks:task-list")

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


class TaskUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    generic.UpdateView
):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def test_func(self):
        task = self.get_object()
        user = self.request.user
        if user.is_superuser or user.has_perm("tasks.change_task"):
            return True
        return task.created_by == user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["next_url"] = self.request.GET.get(
            "next", reverse("tasks:task-list"))
        return context

    def get_success_url(self):
        next_param = self.request.GET.get("next")
        url = reverse(
            "tasks:task-detail", kwargs={"pk": self.object.pk})
        return f"{url}?next={next_param}" if next_param else url


class TaskDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    generic.DeleteView
):
    model = Task
    template_name = "tasks/confirm_delete.html"

    def test_func(self):
        task = self.get_object()
        user = self.request.user
        if user.is_superuser or user.has_perm("tasks.delete_task"):
            return True
        return task.created_by == user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        next_url = self.request.GET.get(
            "next", reverse_lazy("tasks:task-list"))
        context.update(
            {
                "delete_type": "task",
                "success_url": next_url,
                "cancel_url": reverse_lazy(
                    "tasks:task-detail", kwargs={"pk": self.object.pk}
                )
                + f"?next={next_url}",
            }
        )
        context.update(get_task_messages(self.object))
        return context

    def get_success_url(self):
        return self.request.GET.get(
            "next", str(reverse_lazy("tasks:task-list")))


class UserTaskListView(LoginRequiredMixin, PageSizeMixin, generic.ListView):
    model = Task
    context_object_name = "tasks"
    paginate_by = 5
    template_name = "tasks/task_list.html"

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(assignees=self.request.user)
        queryset = apply_search(
            queryset, self.request.GET, ["name", "pk"])
        queryset = filter_tasks(queryset, self.request.GET)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "priorities": Task._meta.get_field("priority").choices,
                "completed_choices": [("true", "True"), ("false", "False")],
                "task_types": TaskType.objects.all(),
                "next_url": reverse("tasks:user-task-list"),
            }
        )
        return context
