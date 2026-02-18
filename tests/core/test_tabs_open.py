from __future__ import annotations

import base64
import json
from typing import cast

import pytest
from openmac.core._internal.apple_scripts.runner import AppleScriptRunner
from openmac.core._internal.context import Context
from openmac.core._internal.tab_commands import NOT_FOUND_SENTINEL
from openmac.core.exceptions import DoesNotExistError
from openmac.core.tabs import Tab, TabsManager


class _SpyAppleScriptRunner:
    def __init__(self, responses: str | list[str]) -> None:
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


def _make_context(response: str | list[str]) -> tuple[Context, _SpyAppleScriptRunner]:
    runner = _SpyAppleScriptRunner(response)
    return Context(runner=cast("AppleScriptRunner", runner)), runner


def test_global_open_creates_new_window_and_returns_tab_with_context() -> None:
    context, runner = _make_context(
        [
            json.dumps(
                {
                    "id": 501,
                    "window_id": 21,
                },
            ),
            json.dumps(
                {
                    "title": "Example",
                    "url": "https://example.com",
                    "loading": False,
                    "is_active": True,
                },
            ),
        ],
    )
    existing_tab = Tab(
        id=1,
        window_id=2,
    )
    existing_tab.set_context(context)
    tabs_manager = TabsManager(_context=context, _items=[existing_tab])

    tab = tabs_manager.open("https://example.com")

    open_script = runner.scripts[0]
    refresh_script = runner.scripts[1]
    expected_b64 = base64.b64encode(b"https://example.com").decode("ascii")
    assert tab.id == 501
    assert tab.window_id == 21
    assert tab._context is context
    assert tab.title == "Example"
    assert 'tell application "Google Chrome"' in open_script
    assert "make new window" in open_script
    assert "active tab of targetWindow" in open_script
    assert "set URL of t to urlText" in open_script
    assert f'set urlBase64 to "{expected_b64}"' in open_script
    assert "set targetWindowId to 21" in refresh_script
    assert "set targetTabId to 501" in refresh_script
    assert len(runner.scripts) == 2


def test_window_bound_open_creates_new_tab_in_target_window() -> None:
    context, runner = _make_context(
        [
            json.dumps(
                {
                    "id": 777,
                },
            ),
            json.dumps(
                {
                    "title": "Example 2",
                    "url": "https://example.com/2",
                    "loading": False,
                    "is_active": True,
                },
            ),
        ],
    )
    tabs_manager = TabsManager(_context=context, _window_id=7)

    tab = tabs_manager.open("https://example.com")

    open_script = runner.scripts[0]
    refresh_script = runner.scripts[1]
    assert tab.id == 777
    assert tab.window_id == 7
    assert tab._context is context
    assert tab.title == "Example 2"
    assert "set targetWindowId to 7" in open_script
    assert "repeat with w in windows" in open_script
    assert "if ((id of w) as integer) is targetWindowId then" in open_script
    assert (
        "make new tab at end of tabs of targetWindow with properties {URL:urlText}" in open_script
    )
    assert "set active tab index of targetWindow to (count of tabs of targetWindow)" in open_script
    assert "set targetWindowId to 7" in refresh_script
    assert "set targetTabId to 777" in refresh_script
    assert len(runner.scripts) == 2


def test_window_bound_open_raises_when_window_not_found() -> None:
    context, _runner = _make_context(NOT_FOUND_SENTINEL)
    tabs_manager = TabsManager(_context=context, _window_id=7)

    with pytest.raises(DoesNotExistError) as exc_info:
        tabs_manager.open("https://example.com")

    assert str(exc_info.value) == "Cannot open tab in window id=7: not found."
