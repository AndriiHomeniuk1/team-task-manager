from django.urls import path

from tasks.views import (
    index,
    profile,
    PositionListView,
    TaskTypeListView,
    WorkerListView,
    TaskListView,
)


app_name = "tasks"

urlpatterns = [
    path("", index, name="index"),
    path("profile/", profile, name="profile"),
    path("positions/", PositionListView.as_view(), name="position-list"),
    path("task-types/", TaskTypeListView.as_view(), name="task-type-list"),
    path("workers/", WorkerListView.as_view(), name="worker-list"),
    path("tasks/", TaskListView.as_view(), name="task-list"),
]
