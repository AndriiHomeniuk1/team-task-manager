from django.urls import path

from tasks.views import (
    index,
    PositionView,
    TaskTypeView,
    WorkerView,
    TaskView,
)


app_name = "tasks"

urlpatterns = [
    path("", index, name="index"),
    path("positions/", PositionView.as_view(), name="position-list"),
    path("task-types/", TaskTypeView.as_view(), name="task-type-list"),
    path("workers/", WorkerView.as_view(), name="worker-list"),
    path("tasks/", TaskView.as_view(), name="task-list"),
]
