from __future__ import annotations

import openmac.core.chrome as chrome_module
import pytest


class _FakeTab:
    def execute(self, javascript: str, *, return_type: type[int]) -> int:
        assert javascript == "123"
        assert return_type is int
        return 321


class _FakeTabs:
    active = _FakeTab()


class _FakeWindow:
    tabs = _FakeTabs()


class _FakeWindows:
    front = _FakeWindow()


class _FakeChrome:
    def __init__(self) -> None:
        self.windows = _FakeWindows()


def test_main_prints_active_tab_execution_result(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(chrome_module, "Chrome", _FakeChrome)

    chrome_module.main()

    assert capsys.readouterr().out.strip() == "321"
