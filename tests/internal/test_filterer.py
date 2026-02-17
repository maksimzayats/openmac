from __future__ import annotations

from dataclasses import dataclass

import pytest

from achrome.core._internal.filterer import GenericFilterer


@dataclass(frozen=True)
class _Candidate:
    name: str
    age: int
    tags: tuple[str, ...]


def test_filter_uses_equality_operator_by_default() -> None:
    candidates = [
        _Candidate(name="Alice", age=21, tags=("premium", "vip")),
        _Candidate(name="Bob", age=19, tags=("basic",)),
        _Candidate(name="Alice", age=17, tags=("basic",)),
    ]

    filterer = GenericFilterer[_Candidate]({"name": "Alice"})

    assert filterer.filter(candidates) == [candidates[0], candidates[2]]


def test_filter_supports_operator_suffixes() -> None:
    candidates = [
        _Candidate(name="Alice", age=21, tags=("premium", "vip")),
        _Candidate(name="Bob", age=19, tags=("basic",)),
        _Candidate(name="Carol", age=17, tags=("vip",)),
    ]

    filterer = GenericFilterer[_Candidate]({"age__ge": 18, "tags__contains": "vip"})

    assert filterer.filter(candidates) == [candidates[0]]


def test_filter_returns_empty_list_when_no_items_match() -> None:
    candidates = [
        _Candidate(name="Alice", age=21, tags=("premium", "vip")),
        _Candidate(name="Bob", age=19, tags=("basic",)),
    ]

    filterer = GenericFilterer[_Candidate]({"age__lt": 10})

    assert filterer.filter(candidates) == []


def test_filter_uses_none_for_missing_attributes() -> None:
    candidates = [
        _Candidate(name="Alice", age=21, tags=("premium", "vip")),
        _Candidate(name="Bob", age=19, tags=("basic",)),
    ]

    filterer = GenericFilterer[_Candidate]({"nickname": None})

    assert filterer.filter(candidates) == candidates


def test_filter_raises_for_unsupported_operator() -> None:
    candidates = [_Candidate(name="Alice", age=21, tags=("premium", "vip"))]
    filterer = GenericFilterer[_Candidate]({"age__unknown": 18})

    with pytest.raises(ValueError, match="Unsupported operator: unknown"):
        filterer.filter(candidates)
