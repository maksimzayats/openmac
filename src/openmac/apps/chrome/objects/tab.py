from __future__ import annotations

from dataclasses import dataclass

from appscript import Keyword

from openmac.apps._internal.base import BaseManager, BaseObject


class Tab(BaseObject):
    @property
    def properties(self) -> TabProperties:
        ae_properties = self._ae_object.properties()
        return TabProperties(
            url=ae_properties[Keyword("URL")],
            title=ae_properties[Keyword("title")],
            loading=ae_properties[Keyword("loading")],
            id=ae_properties[Keyword("id")],
        )


@dataclass(slots=True)
class TabProperties:
    url: str
    title: str
    loading: bool
    id: str


class TabsManager(BaseManager[Tab]):
    pass
