from __future__ import annotations

from appscript import Keyword

from openmac.apps.chrome.objects.tab import Tab, TabProperties
from openmac.apps.chrome.objects.window import Window, WindowProperties


class StubTabAE:
    def __init__(self, *, url: str, title: str, loading: bool, tab_id: str) -> None:
        self._url = url
        self._title = title
        self._loading = loading
        self._tab_id = tab_id

    def _url_method(self) -> str:
        return self._url

    def __getattr__(self, name: str) -> object:
        if name == "URL":
            return self._url_method

        msg = f"{type(self).__name__!s} has no attribute {name!r}"
        raise AttributeError(msg)

    def title(self) -> str:
        return self._title

    def loading(self) -> bool:
        return self._loading

    def id(self) -> str:
        return self._tab_id

    def properties(self) -> dict[Keyword, object]:
        return {
            Keyword("URL"): self._url,
            Keyword("title"): self._title,
            Keyword("loading"): self._loading,
            Keyword("id"): self._tab_id,
        }


class StubWindowAE:
    def __init__(self, *, tabs: list[StubTabAE]) -> None:
        self._tabs = tabs

    def id(self) -> str:
        return "window-1"

    def closeable(self) -> bool:
        return True

    def zoomed(self) -> bool:
        return False

    def active_tab_index(self) -> int:
        return 2

    def index(self) -> int:
        return 1

    def visible(self) -> bool:
        return True

    def given_name(self) -> str:
        return "Main"

    def title(self) -> str:
        return "Chrome"

    def minimizable(self) -> bool:
        return True

    def mode(self) -> str:
        return "normal"

    def active_tab(self) -> int:
        return 2

    def tabs(self) -> list[StubTabAE]:
        return self._tabs

    def properties(self) -> dict[Keyword, object]:
        return {
            Keyword("id"): self.id(),
            Keyword("closeable"): self.closeable(),
            Keyword("zoomed"): self.zoomed(),
            Keyword("active_tab_index"): self.active_tab_index(),
            Keyword("index"): self.index(),
            Keyword("visible"): self.visible(),
            Keyword("given_name"): self.given_name(),
            Keyword("title"): self.title(),
            Keyword("minimizable"): self.minimizable(),
            Keyword("mode"): self.mode(),
            Keyword("active_tab"): self.active_tab(),
        }


def test_tab_property_accessors_return_underlying_values() -> None:
    tab = Tab(
        _ae_object=StubTabAE(url="https://example.com", title="Example", loading=False, tab_id="1"),
    )

    assert tab.url == "https://example.com"
    assert tab.title == "Example"
    assert tab.loading is False
    assert tab.id == "1"


def test_tab_properties_returns_dataclass_snapshot() -> None:
    tab = Tab(
        _ae_object=StubTabAE(url="https://example.com", title="Example", loading=True, tab_id="2"),
    )

    assert tab.properties == TabProperties(
        url="https://example.com",
        title="Example",
        loading=True,
        id="2",
    )


def test_window_property_accessors_return_underlying_values() -> None:
    window = Window(_ae_object=StubWindowAE(tabs=[]))

    assert window.id == "window-1"
    assert window.closeable is True
    assert window.zoomed is False
    assert window.active_tab_index == 2
    assert window.index == 1
    assert window.visible is True
    assert window.given_name == "Main"
    assert window.title == "Chrome"
    assert window.minimizable is True
    assert window.mode == "normal"
    assert window.active_tab == 2


def test_window_tabs_wraps_ae_tabs_as_tab_objects() -> None:
    ae_tabs = [
        StubTabAE(url="https://first.example", title="First", loading=False, tab_id="a"),
        StubTabAE(url="https://second.example", title="Second", loading=True, tab_id="b"),
    ]
    window = Window(_ae_object=StubWindowAE(tabs=ae_tabs))

    tabs = window.tabs

    assert tabs.count() == 2
    first = tabs.first()
    assert first is not None
    assert first.title == "First"
    last = tabs.last()
    assert last is not None
    assert last.id == "b"


def test_window_properties_returns_dataclass_snapshot() -> None:
    window = Window(_ae_object=StubWindowAE(tabs=[]))

    assert window.properties == WindowProperties(
        id="window-1",
        closeable=True,
        zoomed=False,
        active_tab_index=2,
        index=1,
        visible=True,
        given_name="Main",
        title="Chrome",
        minimizable=True,
        mode="normal",
        active_tab=2,
    )
