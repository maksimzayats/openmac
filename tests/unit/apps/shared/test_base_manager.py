from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import pytest

from openmac.apps.exceptions import MultipleObjectsReturnedError, ObjectDoesNotExistError
from openmac.apps.shared.base import BaseManager


@dataclass(slots=True)
class Item:
    id: str
    title: str
    category: str


@dataclass(slots=True, kw_only=True)
class ItemManager(BaseManager[Item]):
    items: list[Item]

    def _iter_objects(self) -> Iterator[Item]:
        """Load every item from the backing store without consulting the filterer."""
        return iter(self.items)


@pytest.fixture()
def items() -> list[Item]:
    return [
        Item(id="1", title="One", category="odd"),
        Item(id="2", title="Two", category="even"),
        Item(id="3", title="Three", category="odd"),
    ]


def test_manager_iterates_all_objects_by_default(items: list[Item]) -> None:
    manager = ItemManager(items=items)

    assert list(manager) == items
    assert manager.all == items
    assert manager.count == 3
    assert manager.first == items[0]
    assert manager.last == items[-1]


def test_manager_filter_limits_iteration_and_all_methods(items: list[Item]) -> None:
    manager = ItemManager(items=items)

    filtered = manager.filter(category="odd")

    assert filtered is manager
    assert list(manager._iter_objects()) == items
    assert [item.id for item in manager] == ["1", "3"]
    assert manager.all == [items[0], items[2]]
    assert manager.count == 2
    assert manager.first == items[0]
    assert manager.last == items[2]


def test_manager_filter_accumulates_with_and_semantics(items: list[Item]) -> None:
    manager = ItemManager(items=items)

    manager.filter(category="odd").filter(title__contains="hre")

    assert manager.all == [items[2]]


def test_manager_exclude_negates_lookup_and_can_chain_after_filter(items: list[Item]) -> None:
    manager = ItemManager(items=items)

    manager.filter(title__contains="O").exclude(id="2")

    assert list(manager._iter_objects()) == items
    assert manager.all == [items[0]]


def test_manager_get_returns_matching_object(items: list[Item]) -> None:
    manager = ItemManager(items=items)

    assert manager.get(id="2") == items[1]


def test_manager_get_raises_when_no_match(items: list[Item]) -> None:
    manager = ItemManager(items=items)

    with pytest.raises(
        ObjectDoesNotExistError,
        match=r"ItemManager\.get\(\) found 0 objects for criteria \{'id': '9'\}",
    ):
        manager.get(id="9")


def test_manager_get_raises_when_multiple_match(items: list[Item]) -> None:
    manager = ItemManager(items=items)

    with pytest.raises(
        MultipleObjectsReturnedError,
        match=r"ItemManager\.get\(\) found 2 objects for criteria \{'category': 'odd'\}, expected 1",
    ):
        manager.get(category="odd")


def test_manager_first_raises_for_empty_result(items: list[Item]) -> None:
    manager = ItemManager(items=items).filter(id="9")

    with pytest.raises(ObjectDoesNotExistError, match=r"ItemManager contains no objects\."):
        _ = manager.first


def test_manager_last_raises_for_empty_result(items: list[Item]) -> None:
    manager = ItemManager(items=items).exclude(id__in={"1", "2", "3"})

    with pytest.raises(ObjectDoesNotExistError, match=r"ItemManager contains no objects\."):
        _ = manager.last
