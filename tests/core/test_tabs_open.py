from __future__ import annotations

import base64
import json
from typing import cast

import pytest

from achrome.core._internal.apple_script import AppleScriptRunner
from achrome.core._internal.context import Context
from achrome.core._internal.tab_commands import NOT_FOUND_SENTINEL
from achrome.core.exceptions import DoesNotExistError
from achrome.core.tabs import Tab, TabsManager


class _SpyAppleScriptRunner:
    def __init__(self, response: str) -> None:
        self.response = response
        self.scripts: list[str] = []

    def run(self, script: str) -> str:
        self.scripts.append(script)
        return self.response


def _make_context(response: str) -> tuple[Context, _SpyAppleScriptRunner]:
    runner = _SpyAppleScriptRunner(response)
    return Context(runner=cast("AppleScriptRunner", runner)), runner


def test_global_open_creates_new_window_and_returns_tab_with_context() -> None:
    payload = json.dumps(
        {
            "id": 501,
            "window_id": 21,
        },
    )
    context, runner = _make_context(payload)
    existing_tab = Tab(
        id=1,
        window_id=2,
    )
    existing_tab.set_context(context)
    tabs_manager = TabsManager(_context=context, _items=[existing_tab])

    tab = tabs_manager.open("https://example.com")

    script = runner.scripts[-1]
    expected_b64 = base64.b64encode(b"https://example.com").decode("ascii")
    assert tab.id == 501
    assert tab.window_id == 21
    assert tab._context is context
    assert 'tell application "Google Chrome"' in script
    assert "make new window" in script
    assert "active tab of targetWindow" in script
    assert "set URL of t to urlText" in script
    assert f'set urlBase64 to "{expected_b64}"' in script


def test_window_bound_open_creates_new_tab_in_target_window() -> None:
    payload = json.dumps(
        {
            "id": 777,
        },
    )
    context, runner = _make_context(payload)
    tabs_manager = TabsManager(_context=context, _window_id=7)

    tab = tabs_manager.open("https://example.com")

    script = runner.scripts[-1]
    assert tab.id == 777
    assert tab.window_id == 7
    assert tab._context is context
    assert "set targetWindowId to 7" in script
    assert "repeat with w in windows" in script
    assert "if ((id of w) as integer) is targetWindowId then" in script
    assert "make new tab at end of tabs of targetWindow with properties {URL:urlText}" in script
    assert "set active tab index of targetWindow to (count of tabs of targetWindow)" in script


def test_window_bound_open_raises_when_window_not_found() -> None:
    context, _runner = _make_context(NOT_FOUND_SENTINEL)
    tabs_manager = TabsManager(_context=context, _window_id=7)

    with pytest.raises(DoesNotExistError) as exc_info:
        tabs_manager.open("https://example.com")

    assert str(exc_info.value) == "Cannot open tab in window id=7: not found."
