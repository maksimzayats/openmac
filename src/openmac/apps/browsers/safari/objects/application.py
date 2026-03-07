from __future__ import annotations

from dataclasses import dataclass, field

from appscript import GenericReference, Keyword, app

from openmac.apps.browsers.base.objects.application import IBrowser
from openmac.apps.browsers.safari.objects.documents import SafariDocumentsManager
from openmac.apps.browsers.safari.objects.tabs import SafariWindowsTabsManager
from openmac.apps.browsers.safari.objects.windows import SafariWindowsManager
from openmac.apps.shared.base import BaseApplication


@dataclass(slots=True, kw_only=True)
class Safari(BaseApplication, IBrowser):
    ae_safari: GenericReference = field(default_factory=lambda: app(id="com.apple.Safari"))

    # region Properties

    @property
    def name(self) -> str:
        return self.ae_safari.name()

    @property
    def title(self) -> str:
        return self.name

    @property
    def version(self) -> str:
        return self.ae_safari.version()

    @property
    def frontmost(self) -> bool:
        return self.ae_safari.frontmost()

    @property
    def properties(self) -> SafariProperties:
        ae_properties = self.ae_safari.properties()
        return SafariProperties(
            name=ae_properties[Keyword("name")],
            version=ae_properties[Keyword("version")],
            frontmost=ae_properties[Keyword("frontmost")],
        )

    # endregion Properties

    # region Managers

    @property
    def windows(self) -> SafariWindowsManager:
        return SafariWindowsManager(safari=self)

    @property
    def documents(self) -> SafariDocumentsManager:
        return SafariDocumentsManager(safari=self)

    # endregion Managers

    # region Custom Managers

    @property
    def tabs(self) -> SafariWindowsTabsManager:
        return self.windows.tabs

    # endregion Custom Managers

    # region Actions

    def activate(self) -> None:
        self.ae_safari.activate()

    def quit(self) -> None:
        self.ae_safari.quit()

    def show_bookmarks(self) -> None:
        self.ae_safari.show_bookmarks()

    def add_reading_list_item(
        self,
        url: str,
        *,
        with_title: str | None = None,
        and_preview_text: str | None = None,
    ) -> None:
        command_kwargs: dict[str, str] = {}
        if with_title is not None:
            command_kwargs["with_title"] = with_title
        if and_preview_text is not None:
            command_kwargs["and_preview_text"] = and_preview_text

        self.ae_safari.add_reading_list_item(url, **command_kwargs)

    # endregion Actions


@dataclass(slots=True)
class SafariProperties:
    name: str
    version: str
    frontmost: bool
