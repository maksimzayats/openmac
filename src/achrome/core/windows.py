from __future__ import annotations

from dataclasses import dataclass, field
from textwrap import dedent
from typing import TYPE_CHECKING, Literal, NamedTuple, TypedDict

from pydantic import TypeAdapter

from achrome.core._internal.manager import BaseManager
from achrome.core._internal.models import ChromeModel
from achrome.core._internal.tab_commands import NOT_FOUND_SENTINEL, build_void_tab_command_script
from achrome.core._internal.window_commands import (
    build_void_window_command_script,
    build_window_info_script,
    build_windows_info_list_script,
)
from achrome.core.exceptions import DoesNotExistError
from achrome.core.tabs import Tab, TabsManager

if TYPE_CHECKING:
    from typing_extensions import NotRequired, Self, Unpack


class Bounds(NamedTuple):
    x: int
    y: int
    width: int
    height: int


@dataclass(slots=True, frozen=True)
class _WindowInfo:
    name: str
    bounds: Bounds
    index: int
    closeable: bool
    minimizable: bool
    minimized: bool
    resizable: bool
    visible: bool
    zoomable: bool
    zoomed: bool
    mode: str
    active_tab_index: int
    presenting: bool
    active_tab_id: int


@dataclass(slots=True, frozen=True)
class _WindowListInfo:
    id: int
    name: str
    bounds: Bounds
    index: int
    closeable: bool
    minimizable: bool
    minimized: bool
    resizable: bool
    visible: bool
    zoomable: bool
    zoomed: bool
    mode: str
    active_tab_index: int
    presenting: bool
    active_tab_id: int


@dataclass(slots=True)  # noqa: PLR0904 - required public API surface
class Window(ChromeModel):
    id: int
    _info: _WindowInfo | None = field(default=None, repr=False, compare=False, kw_only=True)

    @property
    def active_tab(self) -> Tab:
        return self.tabs.get(id=self.active_tab_id)

    @property
    def tabs(self) -> TabsManager:
        return TabsManager(_context=self._context, _window_id=self.id)

    def _require_info(self) -> _WindowInfo:
        if self._info is None:
            raise RuntimeError(
                f"Window id={self.id} state is not hydrated. "
                "Call `window.refresh()` before accessing properties.",
            )
        return self._info

    def refresh(self) -> Self:
        script = build_window_info_script(self.id)
        result = self._context.runner.run(script)
        if result == NOT_FOUND_SENTINEL:
            raise DoesNotExistError(f"Cannot read window id={self.id}: not found.")
        self._info = TypeAdapter(_WindowInfo).validate_json(result)
        return self

    @property
    def name(self) -> str:
        return self._require_info().name

    @property
    def bounds(self) -> Bounds:
        return self._require_info().bounds

    @property
    def index(self) -> int:
        return self._require_info().index

    @property
    def closeable(self) -> bool:
        return self._require_info().closeable

    @property
    def minimizable(self) -> bool:
        return self._require_info().minimizable

    @property
    def minimized(self) -> bool:
        return self._require_info().minimized

    @property
    def resizable(self) -> bool:
        return self._require_info().resizable

    @property
    def visible(self) -> bool:
        return self._require_info().visible

    @property
    def zoomable(self) -> bool:
        return self._require_info().zoomable

    @property
    def zoomed(self) -> bool:
        return self._require_info().zoomed

    @property
    def mode(self) -> str:
        return self._require_info().mode

    @property
    def active_tab_index(self) -> int:
        return self._require_info().active_tab_index

    @property
    def presenting(self) -> bool:
        return self._require_info().presenting

    @property
    def active_tab_id(self) -> int:
        return self._require_info().active_tab_id

    def close(self) -> None:
        self._run_window_command("close", "close targetWindow")

    def activate(self) -> None:
        self._run_window_command(
            "activate",
            """
set index of targetWindow to 1
activate
""",
        )

    def set_bounds(self, bounds: Bounds) -> None:
        self._run_window_command(
            "set bounds",
            f"set bounds of targetWindow to {{{bounds.x}, {bounds.y}, {bounds.width}, {bounds.height}}}",
        )

    def minimize(self) -> None:
        self._run_window_command("minimize", "set minimized of targetWindow to true")

    def unminimize(self) -> None:
        self._run_window_command("unminimize", "set minimized of targetWindow to false")

    def show(self) -> None:
        self._run_window_command("show", "set visible of targetWindow to true")

    def hide(self) -> None:
        self._run_window_command("hide", "set visible of targetWindow to false")

    def zoom(self) -> None:
        self._run_window_command("zoom", "set zoomed of targetWindow to true")

    def unzoom(self) -> None:
        self._run_window_command("unzoom", "set zoomed of targetWindow to false")

    def enter_presentation_mode(self) -> None:
        self._run_window_command(
            "enter presentation mode",
            "enter presentation mode targetWindow",
        )

    def exit_presentation_mode(self) -> None:
        self._run_window_command(
            "exit presentation mode",
            "exit presentation mode targetWindow",
        )

    def activate_tab_index(self, tab_index: int) -> None:
        script = build_void_window_command_script(
            self.id,
            command_body=f"""
set active tab index of targetWindow to {tab_index}
activate
""",
        )
        result = self._context.runner.run(script)
        if result == NOT_FOUND_SENTINEL:
            raise DoesNotExistError(
                f"Cannot activate tab index={tab_index} in window id={self.id}: not found.",
            )

    def activate_tab(self, tab_id: int) -> None:
        script = build_void_tab_command_script(
            self.id,
            tab_id,
            command_body="""
set active tab index of targetWindow to tabIndex
activate
""",
        )
        result = self._context.runner.run(script)
        if result == NOT_FOUND_SENTINEL:
            raise DoesNotExistError(
                f"Cannot activate tab id={tab_id} in window id={self.id}: not found.",
            )

    def _run_window_command(self, action: str, command_body: str) -> None:
        script = build_void_window_command_script(self.id, command_body=command_body)
        result = self._context.runner.run(script)
        if result == NOT_FOUND_SENTINEL:
            raise DoesNotExistError(f"Cannot {action} window id={self.id}: not found.")


class WindowsFilterCriteria(TypedDict):
    id: NotRequired[int]
    id__in: NotRequired[list[int]]
    name: NotRequired[str]
    name__in: NotRequired[list[str]]
    name__contains: NotRequired[str]
    bounds: NotRequired[Bounds]
    bounds__contains: NotRequired[int]
    index: NotRequired[int]
    index__in: NotRequired[list[int]]
    closeable: NotRequired[bool]
    minimizable: NotRequired[bool]
    minimized: NotRequired[bool]
    resizable: NotRequired[bool]
    visible: NotRequired[bool]
    zoomable: NotRequired[bool]
    zoomed: NotRequired[bool]
    mode: NotRequired[str]
    mode__contains: NotRequired[str]
    mode__in: NotRequired[list[str]]
    active_tab_index: NotRequired[int]
    active_tab_index__in: NotRequired[list[int]]
    presenting: NotRequired[bool]
    active_tab_id: NotRequired[int]
    active_tab_id__in: NotRequired[list[int]]


class WindowsManager(BaseManager[Window]):
    @property
    def front(self) -> Window:
        return self.get(index=1)

    def create(self, *, mode: Literal["normal", "incognito"] = "normal") -> Window:
        create_window_command = "set targetWindow to make new window"
        if mode == "incognito":
            create_window_command = (
                'set targetWindow to make new window with properties {mode:"incognito"}'
            )

        script = dedent(
            f"""
            use AppleScript version "2.8"
            use scripting additions

            tell application "Google Chrome"
                {create_window_command}
                return ((id of targetWindow) as integer) as text
            end tell
            """,
        ).strip()

        result = self._context.runner.run(script)
        window_id = TypeAdapter(int).validate_json(result)
        window = Window(id=window_id)
        window.set_context(self._context)
        return window.refresh()

    def _load_items(self) -> list[Window]:
        script = build_windows_info_list_script()
        result = self._context.runner.run(script)
        window_infos = TypeAdapter(list[_WindowListInfo]).validate_json(result)
        windows = [
            Window(
                id=window_info.id,
                _info=_WindowInfo(
                    name=window_info.name,
                    bounds=window_info.bounds,
                    index=window_info.index,
                    closeable=window_info.closeable,
                    minimizable=window_info.minimizable,
                    minimized=window_info.minimized,
                    resizable=window_info.resizable,
                    visible=window_info.visible,
                    zoomable=window_info.zoomable,
                    zoomed=window_info.zoomed,
                    mode=window_info.mode,
                    active_tab_index=window_info.active_tab_index,
                    presenting=window_info.presenting,
                    active_tab_id=window_info.active_tab_id,
                ),
            )
            for window_info in window_infos
        ]

        for window in windows:
            window.set_context(self._context)

        return windows

    if TYPE_CHECKING:

        def filter(self, **criteria: Unpack[WindowsFilterCriteria]) -> Self: ...  # type: ignore[override]
        def get(self, **criteria: Unpack[WindowsFilterCriteria]) -> Window: ...  # type: ignore[override]
