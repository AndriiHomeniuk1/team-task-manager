from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.views import generic

from tasks.models import Position, TaskType, Worker, Task


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "tasks/index.html")

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
