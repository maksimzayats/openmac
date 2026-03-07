from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from typing_extensions import Self  # noqa: UP035

from openmac import IBrowserTab
from openmac.apps.browsers.pages.base import BasePage, BasePageElement
from openmac.apps.browsers.pages.scripts import REAL_CLICK_FUNCTION
from openmac.apps.shared.base import BaseManager


@dataclass(slots=True, kw_only=True)
class TelegramPage(BasePage):
    tab: IBrowserTab

    @classmethod
    def from_tab(cls, tab: IBrowserTab, **_kwargs: Any) -> Self:
        return cls(tab=tab)

    @property
    def folders(self) -> TelegramFoldersManager:
        return TelegramFoldersManager(page=self)


@dataclass(slots=True, kw_only=True)
class TelegramChatsFolder(BasePageElement):
    page: TelegramPage
    selector: str

    # region Properties

    @property
    def name(self) -> str:
        script = f"""
        function getFolderName(selector) {{
            const element = document.querySelector(selector);
            return element ? element.innerText.split("\\n")[0] : "";
        }}

        getFolderName('{self.selector}');
        """

        return self.page.tab.execute(script) or ""

    @property
    def number_of_unread_messages(self) -> int:
        script = f"""
        function getUnreadCount(selector) {{
            const element = document.querySelector(selector);
            if (!element) return 0;

            const countText = element.innerText;
            const count = parseInt(countText, 10);
            return isNaN(count) ? 0 : count;
        }}

        getUnreadCount('{self.selector} > .Tab_inner > .badge');
        """

        return int(self.page.tab.execute(script)) or 0

    # endregion Properties

    def click(self) -> Self:
        script = f"""
        {REAL_CLICK_FUNCTION}

        function doClick(selector) {{
            const element = document.querySelector(selector);
            if (element) {{
                realClick(element);
            }}
        }}

        doClick('{self.selector}');
        """

        self.page.tab.execute(script)

        return self

    @property
    def chats(self) -> TelegramChatsManager:
        return TelegramChatsManager(folder=self)

    @property
    def forums(self) -> TelegramForumsManager:
        return TelegramForumsManager(folder=self)


@dataclass(slots=True, kw_only=True)
class TelegramChat(BasePageElement):
    folder: TelegramChatsFolder

    @property
    def messages(self) -> TelegramChatMessagesManager:
        return TelegramChatMessagesManager(chat=self)

    def go_to_bottom(self) -> Self:
        raise NotImplementedError


@dataclass(slots=True, kw_only=True)
class TelegramForum(BasePageElement):
    @property
    def topics(self) -> TelegramForumTopicsManager:
        return TelegramForumTopicsManager(forum=self)


class TelegramForumTopic(TelegramChat):
    pass


class TelegramChatMessage(BasePageElement):
    pass


# region Managers


@dataclass(slots=True, kw_only=True)
class TelegramFoldersManager(BaseManager[TelegramChatsFolder]):
    page: TelegramPage

    @property
    def active(self) -> TelegramChatsFolder:
        return TelegramChatsFolder(
            page=self.page,
            selector=".Tab--active",
        )

    def _iter_objects(self) -> Iterator[TelegramChatsFolder]:
        script = """
        function getFolderSelectors() {
            const tabs = document.querySelectorAll('.Tab');

            return [...tabs].map((_, index) => {
                const selector = `.Tab:nth-of-type(${index + 1})`;

                return {
                    selector,
                };
            });
        }

        getFolderSelectors();
        """

        folders_data = self.page.tab.execute(script)
        for folder in folders_data:
            yield TelegramChatsFolder(
                page=self.page,
                selector=folder["selector"],
            )


@dataclass(slots=True, kw_only=True)
class TelegramChatsManager(BaseManager[TelegramChat]):
    folder: TelegramChatsFolder

    def _iter_objects(self) -> Iterator[TelegramChat]:
        raise NotImplementedError


@dataclass(slots=True, kw_only=True)
class TelegramForumsManager(BaseManager[TelegramForum]):
    folder: TelegramChatsFolder

    def _iter_objects(self) -> Iterator[TelegramForum]:
        raise NotImplementedError


@dataclass(slots=True, kw_only=True)
class TelegramForumTopicsManager(BaseManager[TelegramForumTopic]):
    forum: TelegramForum

    def _iter_objects(self) -> Iterator[TelegramForumTopic]:
        raise NotImplementedError


@dataclass(slots=True, kw_only=True)
class TelegramChatMessagesManager(BaseManager[TelegramChatMessage]):
    chat: TelegramChat

    def _iter_objects(self) -> Iterator[TelegramChatMessage]:
        raise NotImplementedError


# endregion Managers
