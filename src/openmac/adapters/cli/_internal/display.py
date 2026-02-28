from __future__ import annotations

from typing import Any


def display_object(obj: Any) -> None:
    if isinstance(obj, list | tuple):
        for item in obj:
            display_object(item)

        return

    if hasattr(obj, "properties"):
        print(obj.properties)
    else:
        print(repr(obj))
