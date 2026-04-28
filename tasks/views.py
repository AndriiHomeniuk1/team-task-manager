from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.views import generic

from tasks.models import Position, TaskType, Worker, Task


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

class PositionListView(generic.ListView):
    model = Position

class TaskTypeListView(generic.ListView):
    model = TaskType
    template_name = "tasks/task_type_list.html"
    context_object_name = "task_type_list"

class WorkerListView(generic.ListView):
    model = Worker

class TaskListView(generic.ListView):
    model = Task
