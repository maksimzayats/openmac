from __future__ import annotations

from typing import Any

from diwire import Injected, resolver_context
from rich.console import Console


@resolver_context.inject
def display_object(
    obj: Any,
    *,
    console: Injected[Console],
) -> None:
    if isinstance(obj, list | tuple):
        for item in obj:
            display_object(item)

        return

    if hasattr(obj, "properties"):
        console.print(obj.properties)
    else:
        console.print(obj)
