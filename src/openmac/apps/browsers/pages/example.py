from __future__ import annotations

from openmac import SafariTab
from openmac.apps.browsers.pages.base import BasePage, BasePageElement


class ExampleComPage(BasePage):
    @property
    def heading(self) -> Heading:
        return Heading(tab=self.tab)

    @property
    def description(self) -> Description:
        return Description(tab=self.tab)

    @property
    def learn_more_button(self) -> LearnMoreButton:
        return LearnMoreButton(tab=self.tab)


class Heading(BasePageElement):
    @property
    def text(self) -> str:
        return self.tab.execute(
            """
            document.querySelector("body > div > h1").innerText
            """,
        )


class Description(BasePageElement):
    @property
    def text(self) -> str:
        return self.tab.execute(
            """
            document.querySelector("body > div > p:nth-child(2)").innerText
            """,
        )


class LearnMoreButton(BasePageElement):
    @property
    def text(self) -> str:
        return self.tab.execute(
            """
            document.querySelector("body > div > p:nth-child(3) > a").innerText
            """,
        )

    @property
    def href(self) -> str:
        return self.tab.execute(
            """
            document.querySelector("body > div > p:nth-child(3) > a").href
            """,
        )

    def click(self) -> SafariTab:
        return self.tab.from_window.tabs.open(self.href)
