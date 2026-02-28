from __future__ import annotations

import pytest

from openmac.adapters.cli._internal.actions import (
    ActionsParser,
    MethodCallAction,
    PropertyAccessAction,
)


class SampleObject:
    def __init__(self) -> None:
        self.title = "openmac"

    def greet(self) -> str:
        return "hello"

    def combine(
        self,
        *values: object,
        **options: object,
    ) -> tuple[tuple[object, ...], dict[str, object]]:
        return values, options


class TabsManagerObject:
    def __init__(self) -> None:
        self.applied_filters: dict[str, object] | None = None

    def filter(self, **filters: object) -> TabsManagerObject:
        self.applied_filters = filters
        return self

    @property
    def first(self) -> str:
        return "first-tab"


class RootObject:
    def __init__(self) -> None:
        self.tabs = TabsManagerObject()


def test_parse_property_actions() -> None:
    actions = ActionsParser(["title", "title"]).parse()

    assert [type(action) for action in actions] == [PropertyAccessAction, PropertyAccessAction]
    assert actions[0](SampleObject()) == "openmac"


def test_parse_method_action_without_arguments() -> None:
    [action] = ActionsParser(["greet()"]).parse()

    assert isinstance(action, MethodCallAction)
    assert action(SampleObject()) == "hello"


def test_parse_method_action_with_arguments() -> None:
    [action] = ActionsParser(
        [
            "combine(1, 'two', [3], {'four': 4}, enabled=True, retries=2, optional=None)",
        ],
    ).parse()

    assert action(SampleObject()) == (
        (1, "two", [3], {"four": 4}),
        {"enabled": True, "retries": 2, "optional": None},
    )


def test_parse_raises_for_empty_action() -> None:
    with pytest.raises(ValueError, match=r"Action cannot be empty\."):
        ActionsParser([" "]).parse()


def test_parse_raises_for_invalid_property_name() -> None:
    with pytest.raises(ValueError, match="Invalid property name"):
        ActionsParser(["bad-name"]).parse()


def test_parse_raises_for_invalid_method_name() -> None:
    with pytest.raises(ValueError, match="Invalid method name"):
        ActionsParser(["bad-name()"]).parse()


def test_parse_raises_for_invalid_method_action_syntax() -> None:
    with pytest.raises(ValueError, match="Invalid method action syntax"):
        ActionsParser(["combine("]).parse()


def test_parse_raises_for_invalid_method_arguments_syntax() -> None:
    with pytest.raises(ValueError, match="Invalid method arguments in action"):
        ActionsParser(["combine(,)"]).parse()


def test_parse_raises_for_non_literal_method_argument() -> None:
    with pytest.raises(ValueError, match="Only Python literals are supported"):
        ActionsParser(["combine(object())"]).parse()


def test_parse_raises_for_kwargs_unpacking() -> None:
    with pytest.raises(ValueError, match="Unsupported kwargs unpacking"):
        ActionsParser(["combine(**{'x': 1})"]).parse()


def test_method_call_action_passes_arguments() -> None:
    action = MethodCallAction(
        method_name="combine",
        method_args=(1, "two"),
        method_kwargs={"enabled": True},
    )

    assert action(SampleObject()) == ((1, "two"), {"enabled": True})


def test_parse_supports_keyword_argument_tokens_after_method_name() -> None:
    [action] = ActionsParser(["filter", "source__contains=google"]).parse()

    manager = TabsManagerObject()
    _ = action(manager)

    assert manager.applied_filters == {"source__contains": "google"}


def test_parse_supports_keyword_argument_tokens_with_typed_values() -> None:
    [action] = ActionsParser(
        ["filter", "count=2", "enabled=true", "note='google'", "none_value=null"],
    ).parse()

    manager = TabsManagerObject()
    _ = action(manager)

    assert manager.applied_filters == {
        "count": 2,
        "enabled": True,
        "note": "google",
        "none_value": None,
    }


def test_parse_supports_filter_chain_without_filter_parentheses() -> None:
    actions = ActionsParser(
        ["tabs", "filter", "source__contains=google", "first"],
    ).parse()

    root = RootObject()
    current_object: object = root
    for action in actions:
        current_object = action(current_object)

    assert current_object == "first-tab"
    assert root.tabs.applied_filters == {"source__contains": "google"}


def test_parse_raises_for_orphan_keyword_argument_token() -> None:
    with pytest.raises(ValueError, match="Unexpected argument token without method"):
        ActionsParser(["source__contains=google"]).parse()
