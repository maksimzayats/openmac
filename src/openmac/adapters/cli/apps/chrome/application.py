from __future__ import annotations

from diwire import Injected, Scope, resolver_context
from rich.console import Console
from typer import Typer

from openmac import Chrome
from openmac.adapters.cli._internal.display import display_object
from openmac.adapters.cli.apps.chrome.windows import chrome_windows_cli

chrome_app_cli = Typer(
    name="chrome",
    help="Commands for interacting with Google Chrome.",
)
chrome_app_cli.add_typer(chrome_windows_cli)


@chrome_app_cli.command(
    name="version",
    help="Print the version of Google Chrome.",
)
@resolver_context.inject(scope=Scope.REQUEST)
def version_command(
    chrome: Injected[Chrome],
    console: Injected[Console],
) -> None:
    console.print(chrome.version)


"""
class Chrome(BaseApplication):
    ae_chrome: GenericReference = field(default_factory=lambda: app(id="com.google.Chrome"))

    # region Properties

    @property
    def version(self) -> str:
        return self.ae_chrome.version()

    @property
    def title(self) -> str:
        return self.ae_chrome.title()

    @property
    def frontmost(self) -> bool:
        return self.ae_chrome.frontmost()

    @property
    def properties(self) -> ChromeProperties:
        ae_properties = self.ae_chrome.properties()
        return ChromeProperties(
            version=ae_properties[Keyword("version")],
            title=ae_properties[Keyword("title")],
            frontmost=ae_properties[Keyword("frontmost")],
        )

    # endregion Properties

    # region Managers

    @property
    def windows(self) -> ChromeWindowsManager:
        return ChromeWindowsManager(chrome=self)

    # endregion Managers

    # region Custom Managers

    @property
    def tabs(self) -> ChromeWindowsTabsManager:
        return self.windows.tabs

    # endregion Custom Managers

    # region Actions

    def activate(self) -> None:
        self.ae_chrome.activate()

    # endregion Actions
"""


# all chrome properties
@chrome_app_cli.command(
    name="title",
    help="Print the title of the frontmost Google Chrome window.",
)
@resolver_context.inject(scope=Scope.REQUEST)
def title_command(
    chrome: Injected[Chrome],
) -> None:
    display_object(chrome.title)


@chrome_app_cli.command(
    name="frontmost",
    help="Print whether Google Chrome is the frontmost application.",
)
@resolver_context.inject(scope=Scope.REQUEST)
def frontmost_command(
    chrome: Injected[Chrome],
) -> None:
    display_object(chrome.frontmost)


@chrome_app_cli.command(
    name="properties",
    help="Print all properties of the frontmost Google Chrome window.",
)
@resolver_context.inject(scope=Scope.REQUEST)
def properties_command(
    chrome: Injected[Chrome],
) -> None:
    display_object(chrome.properties)
