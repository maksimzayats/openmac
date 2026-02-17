from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from types import TracebackType
from typing import TYPE_CHECKING, cast

from achrome.core._internal.chome_api import ChromeAPI

if TYPE_CHECKING:
    from typing_extensions import Self

_context_var = ContextVar["Context"]("achrome.core._internal.context.Context")


@dataclass(slots=True)
class Context:
    chrome_api: ChromeAPI

    _token: Token[Context] = field(init=False)

    def __enter__(self) -> Self:
        self._token = _context_var.set(self)

        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        _context_var.reset(self._token)


class _ContextProxy:
    def __getattr__(self, item: str) -> object:
        ctx = _context_var.get(None)
        if ctx is None:
            raise RuntimeError("Context accessed outside of active scope.")

        return getattr(ctx, item)


context = cast("Context", _ContextProxy())
"""Global context proxy. Accessing attributes on this proxy will retrieve the active context from the context variable. If no context is active, a RuntimeError is raised."""
