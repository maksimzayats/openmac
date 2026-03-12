from __future__ import annotations

from typing import Final

DEFAULT_PREVIEW_LENGTH: Final[int] = 120


def preview_text(value: str, *, max_length: int = DEFAULT_PREVIEW_LENGTH) -> str:
    """Return a compact single-line preview suitable for log messages."""

    normalized_value = " ".join(value.split())
    if len(normalized_value) <= max_length:
        return normalized_value

    return f"{normalized_value[: max_length - 3]}..."
