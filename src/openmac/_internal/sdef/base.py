from __future__ import annotations

from pydantic import BaseModel

from openmac._internal.context import Context


class SDEFClass(BaseModel):
    _context: Context


class SDEFCommand(BaseModel):
    def __call__(self) -> object:
        raise NotImplementedError
