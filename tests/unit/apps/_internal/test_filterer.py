from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import pytest

from openmac.apps._internal.filterer import Filterer
from openmac.apps.exceptions import InvalidFilterError


@dataclass(slots=True)
class Tab:
    id: str
    title: str


@dataclass(slots=True)
class Window:
    id: str
    tabs: list[Tab]


@dataclass(slots=True)
class ManagerTab:
    id: str
    title: str
    url: str


@dataclass(slots=True)
class TabsManager:
    _tabs: list[ManagerTab]

    def __iter__(self) -> Iterator[ManagerTab]:
        return iter(self._tabs)

    @property
    def active(self) -> ManagerTab:
        return self._tabs[0]


@dataclass(slots=True)
class WindowWithTabsManager:
    id: str
    tabs: TabsManager


def test_filter_supports_nested_in_lookup() -> None:
    windows = [
        Window(id="w1", tabs=[Tab(id="t1", title="One"), Tab(id="t2", title="Two")]),
        Window(id="w2", tabs=[Tab(id="t3", title="Three")]),
        Window(id="w3", tabs=[]),
    ]

    filterer = Filterer[Window]({"tabs__id__in": {"t2", "t9"}})

    assert [window.id for window in filterer.filter(windows)] == ["w1"]


def test_filter_supports_nested_exact_lookup() -> None:
    windows = [
        Window(id="w1", tabs=[Tab(id="t1", title="One"), Tab(id="t2", title="Two")]),
        Window(id="w2", tabs=[Tab(id="t3", title="Three")]),
    ]

    filterer = Filterer[Window]({"tabs__title": "Three"})

    assert [window.id for window in filterer.filter(windows)] == ["w2"]


def test_filter_supports_nested_lookup_through_manager_property() -> None:
    windows = [
        WindowWithTabsManager(
            id="w1",
            tabs=TabsManager(
                [
                    ManagerTab(id="t1", title="Python", url="https://python.org"),
                    ManagerTab(id="t2", title="PyPI", url="https://pypi.org"),
                ],
            ),
        ),
        WindowWithTabsManager(
            id="w2",
            tabs=TabsManager(
                [
                    ManagerTab(id="t3", title="GitHub", url="https://github.com/openmac"),
                ],
            ),
        ),
    ]

    filterer = Filterer[WindowWithTabsManager]({"tabs__active__url__contains": "github"})

    assert [window.id for window in filterer.filter(windows)] == ["w2"]


def test_filter_keeps_iterable_lookup_behavior_for_manager_values() -> None:
    windows = [
        WindowWithTabsManager(
            id="w1",
            tabs=TabsManager(
                [
                    ManagerTab(id="t1", title="Docs", url="https://docs.example.com"),
                    ManagerTab(id="t2", title="Blog", url="https://blog.example.com"),
                ],
            ),
        ),
        WindowWithTabsManager(
            id="w2",
            tabs=TabsManager(
                [
                    ManagerTab(id="t3", title="Search", url="https://search.example.com"),
                ],
            ),
        ),
    ]

    filterer = Filterer[WindowWithTabsManager]({"tabs__title": "Docs"})

    assert [window.id for window in filterer.filter(windows)] == ["w1"]


def test_exclude_supports_nested_lookup() -> None:
    windows = [
        Window(id="w1", tabs=[Tab(id="t1", title="One"), Tab(id="t2", title="Two")]),
        Window(id="w2", tabs=[Tab(id="t3", title="Three")]),
        Window(id="w3", tabs=[]),
    ]

    filterer = Filterer[Window]({"tabs__id__in": {"t1", "t3"}})

    assert [window.id for window in filterer.exclude(windows)] == ["w3"]


def test_filter_keeps_existing_operator_behavior() -> None:
    windows = [
        Window(id="w1", tabs=[]),
        Window(id="w2", tabs=[]),
    ]

    filterer = Filterer[Window]({"id__ne": "w1"})

    assert [window.id for window in filterer.filter(windows)] == ["w2"]


def test_filter_raises_for_unknown_top_level_field() -> None:
    windows = [Window(id="w1", tabs=[])]

    filterer = Filterer[Window]({"abc": 123})

    with pytest.raises(InvalidFilterError, match="Invalid filter field 'abc' in lookup 'abc'"):
        filterer.filter(windows)


def test_filter_raises_for_unknown_nested_field() -> None:
    windows = [Window(id="w1", tabs=[Tab(id="t1", title="One")])]

    filterer = Filterer[Window]({"tabs__abc__in": {"t1"}})

    with pytest.raises(
        InvalidFilterError,
        match="Invalid filter field 'abc' in lookup 'tabs__abc__in'",
    ):
        filterer.filter(windows)
