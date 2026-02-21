from __future__ import annotations

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
