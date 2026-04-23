from pathlib import Path


def user_avatar_path(instance: "Worker", filename: str) -> str:
    ext = filename.split(".")[-1]
    filename = f"user_{instance.id}.{ext}"
    return str(Path("avatars") / filename)
