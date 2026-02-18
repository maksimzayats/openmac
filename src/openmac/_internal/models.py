from __future__ import annotations

from pydantic import BaseModel

from openmac._internal.context import Context


class MacModel(BaseModel):
    _context: Context
