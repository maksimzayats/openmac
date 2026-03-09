from __future__ import annotations

from openmac.apps.shared.base import UniqueIterationTracker


def test_add_tracks_unique_objects_only_once() -> None:
    tracker = UniqueIterationTracker[str]()

    tracker.new_iteration()

    assert tracker.add("1") is True
    assert tracker.add("1") is False
    assert tracker.add("2") is True
    assert len(tracker) == 2


def test_new_iteration_increments_empty_iterations_when_no_new_objects_were_added() -> None:
    tracker = UniqueIterationTracker[str]()

    tracker.new_iteration()
    tracker.new_iteration()
    tracker.new_iteration()

    assert tracker.empty_iterations_in_a_row == 2


def test_new_iteration_resets_empty_iteration_counter_after_finding_new_objects() -> None:
    tracker = UniqueIterationTracker[str]()

    tracker.new_iteration()
    tracker.new_iteration()
    tracker.new_iteration()
    tracker.add("1")
    tracker.new_iteration()

    assert tracker.empty_iterations_in_a_row == 0


def test_empty_iteration_count_can_be_checked_by_caller() -> None:
    tracker = UniqueIterationTracker[str]()

    tracker.new_iteration()
    tracker.new_iteration()
    tracker.new_iteration()
    tracker.new_iteration()

    assert tracker.empty_iterations_in_a_row == 3
