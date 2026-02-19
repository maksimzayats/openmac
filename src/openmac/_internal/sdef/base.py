from __future__ import annotations

from typing import ClassVar

from pydantic import BaseModel

from openmac._internal.sdef import meta as sdef_meta


class SDEFClass(BaseModel):
    SDEF_META: ClassVar[sdef_meta.ClassMeta]


class SDEFCommand(BaseModel):
    SDEF_META: ClassVar[sdef_meta.CommandMeta]
