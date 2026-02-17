from __future__ import annotations

from dataclasses import dataclass, field

from achrome.core._internal.context import Context


@dataclass(kw_only=True)
class ChromeModel:
    _context: Context = field(init=False, repr=False, compare=False)

    def set_context(self, context: Context) -> None:
        self._context = context
