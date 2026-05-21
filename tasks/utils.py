from pathlib import Path
from typing import List, Dict

from django.db.models import Q, QuerySet
from django.http import QueryDict
from django.utils.translation import ngettext

from .messages import POSITION_MESSAGES, TASKTYPE_MESSAGES, TASK_MESSAGES


def user_avatar_path(instance: "Worker", filename: str) -> str:
    ext = filename.split(".")[-1]
    filename = f"user_{instance.id}.{ext}"
    return str(Path("avatars") / filename)


def pluralize_noun(singular: str, plural: str, count: int) -> str:
    return ngettext(singular, plural, count)


def get_position_messages(
    position: "Position", total_count: int, extra_count: int
) -> Dict[str, str]:
    return {
        "confirm_message": POSITION_MESSAGES["CONFIRM"].format(object=position),
        "warning_message": POSITION_MESSAGES["WARNING"].format(
            worker_noun=pluralize_noun(
                "worker", "workers", total_count)
        ),
        "assigned_message": POSITION_MESSAGES["ASSIGNED"].format(
            worker_noun=pluralize_noun(
                "worker", "workers", total_count)
        ),
        "extra_message": POSITION_MESSAGES["EXTRA"].format(
            count=extra_count,
            worker_noun=pluralize_noun(
                "worker", "workers", extra_count),
        ),
    }


def get_tasktype_messages(
    tasktype: "TaskType", total_count: int, extra_count: int
) -> Dict[str, str]:
    return {
        "confirm_message": TASKTYPE_MESSAGES["CONFIRM"].format(object=tasktype),
        "assigned_message": TASKTYPE_MESSAGES["ASSIGNED"].format(
            task_noun=pluralize_noun("task", "tasks", total_count)
        ),
        "extra_message": TASKTYPE_MESSAGES["EXTRA"].format(
            count=extra_count,
            task_noun=pluralize_noun(
                "task", "tasks", extra_count)
        ),
    }


def get_task_messages(task: "Task") -> Dict[str, str]:
    return {
        "confirm_message": TASK_MESSAGES["CONFIRM"].format(object=task),
    }


def apply_search(
        queryset: QuerySet,
        params: QueryDict,
        fields: List[str]
) -> QuerySet:
    search = params.get("search")

    if not fields:
        return queryset

    if search:
        q = Q()
        for field in fields:
            q |= Q(**{f"{field}__icontains": search})
        queryset = queryset.filter(q)

    return queryset


def filter_tasks(queryset: QuerySet, params: QueryDict) -> QuerySet:
    keys = params.getlist("key")
    values = params.getlist("value")

    for key, value in zip(keys, values):
        if key and value:
            if key == "is_completed":
                queryset = queryset.filter(
                    is_completed=(value.lower() == "true"))
            elif key == "priority":
                queryset = queryset.filter(priority=value.lower())
            elif key == "task_type":
                queryset = queryset.filter(task_type__name__icontains=value)

    deadline_from = params.get("deadline_from")
    deadline_to = params.get("deadline_to")

    if deadline_from and deadline_to:
        queryset = queryset.filter(deadline__range=(deadline_from, deadline_to))
    elif deadline_from:
        queryset = queryset.filter(deadline__gte=deadline_from)
    elif deadline_to:
        queryset = queryset.filter(deadline__lte=deadline_to)

    return queryset
