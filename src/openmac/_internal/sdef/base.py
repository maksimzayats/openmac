from __future__ import annotations

from typing import ClassVar, Generic, TypeVar

from pydantic import BaseModel

from openmac._internal.sdef import meta as sdef_meta


class SDEFClass(BaseModel):
    SDEF_META: ClassVar[sdef_meta.ClassMeta]


_ResultT_co = TypeVar("_ResultT_co", covariant=True)


class SDEFCommand(BaseModel, Generic[_ResultT_co]):
    SDEF_META: ClassVar[sdef_meta.CommandMeta]
