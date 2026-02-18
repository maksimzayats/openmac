from __future__ import annotations

import base64
import json
from collections.abc import Iterator
from typing import cast

import pytest

from achrome.core._internal.apple_script import AppleScriptRunner
from achrome.core._internal.context import Context
from achrome.core._internal.tab_commands import (
    EXECUTE_MISSING_RESULT_SENTINEL,
    NOT_FOUND_SENTINEL,
)
from achrome.core.exceptions import DoesNotExistError
from achrome.core.tabs import Tab


class _SpyAppleScriptRunner:
    def __init__(self, responses: str | list[str] = "ok") -> None:
        if isinstance(responses, str):
            self._responses = [responses]
        else:
            self._responses = responses
        self.scripts: list[str] = []

    def run(self, script: str) -> str:
        self.scripts.append(script)
        if len(self._responses) > 1:
            return self._responses.pop(0)

        return self._responses[0]


def _make_tab(*, response: str | list[str] = "ok") -> tuple[Tab, _SpyAppleScriptRunner]:
    runner = _SpyAppleScriptRunner(responses=response)
    tab = Tab(
        id=42,
        window_id=7,
    )
    tab._context = Context(runner=cast("AppleScriptRunner", runner))
    return tab, runner


@pytest.mark.parametrize(
    ("method_name", "expected_command"),
    [
        ("back", "go back t"),
        ("forward", "go forward t"),
        ("close", "close t"),
    ],
)
def test_tab_void_commands_emit_expected_script(method_name: str, expected_command: str) -> None:
    tab, runner = _make_tab()

    getattr(tab, method_name)()

    script = runner.scripts[-1]
    assert "set targetWindowId to 7" in script
    assert "set targetTabId to 42" in script
    assert expected_command in script


def test_tab_reload_emits_reload_script_then_refreshes_state() -> None:
    tab, runner = _make_tab(
        response=[
            "ok",
            json.dumps(
                {
                    "title": "Reloaded",
                    "url": "https://example.com",
                    "loading": False,
                    "is_active": True,
                },
            ),
        ],
    )

    tab.reload()

    reload_script = runner.scripts[0]
    refresh_script = runner.scripts[1]
    assert "set targetWindowId to 7" in reload_script
    assert "set targetTabId to 42" in reload_script
    assert "reload t" in reload_script
    assert "set targetWindowId to 7" in refresh_script
    assert "set targetTabId to 42" in refresh_script
    assert tab.title == "Reloaded"
    assert len(runner.scripts) == 2


def test_tab_activate_emits_expected_script() -> None:
    tab, runner = _make_tab()

    tab.activate()

    script = runner.scripts[-1]
    assert "set targetWindowId to 7" in script
    assert "set targetTabId to 42" in script
    assert "set active tab index of targetWindow to tabIndex" in script
    assert "activate" in script


def test_tab_execute_emits_expected_script_and_returns_runner_output() -> None:
    tab, runner = _make_tab(response="execution-result")
    javascript = "return document.title;"
    javascript_base64 = base64.b64encode(javascript.encode("utf-8")).decode("ascii")

    result = tab.execute(javascript)

    script = runner.scripts[-1]
    assert result == "execution-result"
    assert "set targetWindowId to 7" in script
    assert "set targetTabId to 42" in script
    assert f'set jsBase64 to "{javascript_base64}"' in script
    assert "set resultValue to execute t javascript jsText" in script
    assert "if resultValue is missing value then" in script


def test_tab_execute_returns_none_on_missing_result_sentinel() -> None:
    tab, _runner = _make_tab(response=EXECUTE_MISSING_RESULT_SENTINEL)

    result = tab.execute("console.log('x')")

    assert result is None


def test_tab_execute_with_return_type_raises_when_result_is_missing() -> None:
    tab, _runner = _make_tab(response=EXECUTE_MISSING_RESULT_SENTINEL)

    with pytest.raises(RuntimeError) as exc_info:
        tab.execute("1 + 1", return_type=int)

    assert (
        str(exc_info.value)
        == "Expected a return value from executing JavaScript in tab id=42 in window id=7, but got none."
    )


def test_tab_execute_with_return_type_parses_json_result() -> None:
    tab, _runner = _make_tab(response="123")

    result = tab.execute("1 + 2", return_type=int)

    assert result == 123


def test_tab_execute_with_invalid_return_type_raises_parse_error() -> None:
    tab, _runner = _make_tab(response='"not-an-int"')

    with pytest.raises(RuntimeError) as exc_info:
        tab.execute("document.title", return_type=int)

    assert "Failed to parse JavaScript execution result as <class 'int'>:" in str(exc_info.value)


def test_tab_source_uses_outer_html_javascript() -> None:
    tab, runner = _make_tab(response="<html>source</html>")
    source_javascript_base64 = base64.b64encode(
        b"document.documentElement.outerHTML",
    ).decode("ascii")

    source = tab.source

    script = runner.scripts[-1]
    assert source == "<html>source</html>"
    assert f'set jsBase64 to "{source_javascript_base64}"' in script


def test_tab_source_raises_runtime_error_when_execute_returns_missing_result() -> None:
    tab, _runner = _make_tab(response=EXECUTE_MISSING_RESULT_SENTINEL)

    with pytest.raises(RuntimeError) as exc_info:
        _ = tab.source

    assert (
        str(exc_info.value)
        == "Cannot read source for tab id=42 in window id=7: JavaScript returned no value."
    )


def test_tab_snapshot_parses_source_to_tree_and_refs() -> None:
    tab, _runner = _make_tab(
        response=(
            "<html><body><main><h1>Home</h1><button id='start'>Start</button></main></body></html>"
        ),
    )

    snapshot = tab.snapshot

    assert snapshot.tree != "(empty)"
    assert any(ref.role == "button" and ref.name == "Start" for ref in snapshot.refs.values())
    assert any(ref.role == "heading" and ref.name == "Home" for ref in snapshot.refs.values())


def test_tab_wait_to_load_returns_self_after_loading_finishes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    responses = [
        json.dumps(
            {
                "title": "Loading",
                "url": "https://example.com",
                "loading": True,
                "is_active": True,
            },
        ),
        json.dumps(
            {
                "title": "Ready",
                "url": "https://example.com",
                "loading": False,
                "is_active": True,
            },
        ),
    ]
    tab, runner = _make_tab(response=responses[0])
    response_iterator: Iterator[str] = iter(responses)

    def _run(script: str) -> str:
        runner.scripts.append(script)
        return next(response_iterator)

    monkeypatch.setattr(runner, "run", _run)
    monkeypatch.setattr("achrome.core.tabs.time.sleep", lambda _seconds: None)

    result = tab.wait_to_load(timeout=1.0)

    assert result is tab


def test_tab_wait_to_load_raises_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    response = json.dumps(
        {
            "title": "Still Loading",
            "url": "https://example.com",
            "loading": True,
            "is_active": True,
        },
    )
    tab, _runner = _make_tab(response=response)
    monotonic_values = iter([0.0, 1.0])

    monkeypatch.setattr("achrome.core.tabs.time.monotonic", lambda: next(monotonic_values))
    monkeypatch.setattr("achrome.core.tabs.time.sleep", lambda _seconds: None)

    with pytest.raises(TimeoutError) as exc_info:
        tab.wait_to_load(timeout=0.5)

    assert str(exc_info.value) == "Timed out waiting for tab id=42 in window id=7 to load."


@pytest.mark.parametrize(
    ("method_name", "expected_command"),
    [
        ("enter_presentation_mode", "enter presentation mode targetWindow"),
        ("exit_presentation_mode", "exit presentation mode targetWindow"),
    ],
)
def test_tab_presentation_commands_emit_expected_script(
    method_name: str,
    expected_command: str,
) -> None:
    tab, runner = _make_tab()

    getattr(tab, method_name)()

    script = runner.scripts[-1]
    assert "set targetWindowId to 7" in script
    assert "set targetTabId to 42" not in script
    assert expected_command in script


@pytest.mark.parametrize(
    ("method_name", "action"),
    [
        ("reload", "reload"),
        ("back", "go back"),
        ("forward", "go forward"),
        ("close", "close"),
        ("activate", "activate"),
        ("enter_presentation_mode", "enter presentation mode"),
        ("exit_presentation_mode", "exit presentation mode"),
    ],
)
def test_tab_methods_raise_does_not_exist_on_not_found(method_name: str, action: str) -> None:
    tab, _runner = _make_tab(response=NOT_FOUND_SENTINEL)

    with pytest.raises(DoesNotExistError) as exc_info:
        getattr(tab, method_name)()

    assert str(exc_info.value) == f"Cannot {action} tab id=42 in window id=7: not found."


def test_tab_execute_raises_does_not_exist_on_not_found() -> None:
    tab, _runner = _make_tab(response=NOT_FOUND_SENTINEL)

    with pytest.raises(DoesNotExistError) as exc_info:
        tab.execute("return 1;")

    assert (
        str(exc_info.value) == "Cannot execute JavaScript in tab id=42 in window id=7: not found."
    )
