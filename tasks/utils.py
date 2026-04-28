from pathlib import Path
from typing import List, Dict

from django.db.models import Q, QuerySet
from django.http import QueryDict
from django.utils.translation import ngettext

from .messages import POSITION_MESSAGES


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
