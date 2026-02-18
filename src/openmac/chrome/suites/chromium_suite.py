"""Common classes and commands for all applications."""

from __future__ import annotations

from pydantic import BaseModel

from openmac._internal import sdef
from openmac._internal.manager import Manager


class Application(BaseModel):
    """Desc from xml"""

    name: sdef.Text
    """The name of the application."""
    frontmost: sdef.Boolean
    """Is this the frontmost (active) application?"""
    version: sdef.Text
    """The version of the application."""
    windows: Manager[Window]
    """The windows contained within this application, ordered front to back."""


class Window(BaseModel):
    """Desc from xml"""

    id: sdef.Integer
    """The unique identifier of the window."""
    name: sdef.Text
    """The name of the window."""
    bounds: sdef.List[sdef.Integer]
    """The position and size of the window on the screen, specified as a list of four integers: {left, top, right, bottom}."""
    index: sdef.Integer
    """The index of the window in the application’s list of windows."""
    closeable: sdef.Boolean
    """Whether the window can be closed."""
    minimizable: sdef.Boolean
    """Whether the window can be minimized."""
    minimized: sdef.Boolean
    """Whether the window is currently minimized."""
    resizable: sdef.Boolean
    """Whether the window can be resized."""
    visible: sdef.Boolean
    """Whether the window is currently visible."""
    zoomable: sdef.Boolean
    """Whether the window can be zoomed."""
    zoomed: sdef.Boolean
    """Whether the window is currently zoomed."""
    mode: sdef.Text
    """The display mode of the window (e.g., "normal", "fullscreen")."""
    active_tab_index: sdef.Integer
    """The index of the active tab in the window’s list of tabs."""
