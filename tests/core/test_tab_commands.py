from __future__ import annotations

import base64
from typing import cast

import pytest

from achrome.core._internal.apple_script import AppleScriptRunner
from achrome.core._internal.context import Context
from achrome.core._internal.tab_commands import NOT_FOUND_SENTINEL
from achrome.core.exceptions import DoesNotExistError
from achrome.core.tabs import Tab


class _SpyAppleScriptRunner:
    def __init__(self, response: str = "ok") -> None:
        self.response = response
        self.scripts: list[str] = []

    def run(self, script: str) -> str:
        self.scripts.append(script)
        return self.response


def _make_tab(*, response: str = "ok") -> tuple[Tab, _SpyAppleScriptRunner]:
    runner = _SpyAppleScriptRunner(response=response)
    tab = Tab(
        id=42,
        window_id=7,
    )
    tab._context = Context(runner=cast("AppleScriptRunner", runner))
    return tab, runner


@pytest.mark.parametrize(
    ("method_name", "expected_command"),
    [
        ("reload", "reload t"),
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


def test_tab_source_uses_outer_html_javascript() -> None:
    tab, runner = _make_tab(response="<html>source</html>")
    source_javascript_base64 = base64.b64encode(
        b"document.documentElement.outerHTML",
    ).decode("ascii")

    source = tab.source

    script = runner.scripts[-1]
    assert source == "<html>source</html>"
    assert f'set jsBase64 to "{source_javascript_base64}"' in script


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
