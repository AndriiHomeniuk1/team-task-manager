from django.http import HttpRequest
from typing import Dict


def get_segment(request: HttpRequest) -> Dict[str, str]:
    parts = [p for p in request.path.split("/") if p]
    segment = " / ".join(parts) if parts else "index"

    display_names = {
        "index": "Dashboard",
    }
    return {
        "segment": segment,
        "segment_display": display_names.get(segment, segment)
    }
