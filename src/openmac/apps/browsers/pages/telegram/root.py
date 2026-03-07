from __future__ import annotations

from dataclasses import dataclass, field
from time import sleep

from openmac import SafariTab
from openmac.apps.browsers.pages.base import BasePage, BasePageElement
from openmac.apps.shared.base import BaseManager


class RootTelegramPage(BasePage):
    @property
    def is_loaded(self) -> bool:
        return self.tab.execute(
            """
            Boolean(document.querySelector("#page-chats") && document.querySelector("#column-left"))
            """,
        )

    @property
    def folders(self) -> FoldersManager:
        return FoldersManager(_tab=self.tab)


@dataclass(slots=True, kw_only=True)
class Folder(BasePageElement):
    id: str
    name: str
    selector: str

    def click(self) -> None:
        self.tab.execute(
            f"""
            document.querySelector('{self.selector}').click();
            """,
        )
        sleep(0.5)

    @property
    def chats(self) -> ChatsManager:
        return ChatsManager(_tab=self.tab, _folder=self)


@dataclass(slots=True, kw_only=True)
class FoldersManager(BaseManager[Folder]):
    _tab: SafariTab = field(repr=False)

    def _load(self) -> list[Folder]:
        folders_data = self._tab.execute(
            """
            function getFolderSelectors() {
              const container = document.querySelector("#folders-tabs");
              if (!container) return [];

              const folders = container.querySelectorAll(".menu-horizontal-div-item");

              return [...folders].map((el) => {
                const id = el.getAttribute("data-filter-id");

                const label =
                  el.querySelector(".text-super")?.innerText?.trim() ?? "unknown";

                const selector = `#folders-tabs .menu-horizontal-div-item[data-filter-id="${id}"]`;

                return {
                  name: label,
                  filter_id: id,
                  selector: selector
                };
              });
            }

            getFolderSelectors();
            """,
        )

        return [
            Folder(
                name=folder["name"],
                id=folder["filter_id"],
                selector=folder["selector"],
                tab=self._tab,
            )
            for folder in folders_data
        ]


@dataclass(slots=True, kw_only=True)
class Chat(BasePageElement):
    name: str
    peer_id: str
    selector: str

    def click(self) -> None:
        self.tab.execute(
            f"""
            function realClick(el) {{
              const rect = el.getBoundingClientRect();
              const x = rect.left + rect.width / 2;
              const y = rect.top + rect.height / 2;

              ["pointerdown", "mousedown", "mouseup", "click"].forEach(type => {{
                el.dispatchEvent(new MouseEvent(type, {{
                  view: window,
                  bubbles: true,
                  cancelable: true,
                  clientX: x,
                  clientY: y,
                  button: 0
                }}));
              }});
            }}

            realClick(document.querySelector('{self.selector}'));
            """,
        )
        sleep(0.5)


@dataclass(slots=True, kw_only=True)
class ChatsManager(BaseManager[Chat]):
    _tab: SafariTab = field(repr=False)
    _folder: Folder = field(repr=False)

    def _load(self) -> list[Chat]:
        self._folder.click()

        chats_data = self._tab.execute(
            """
            function getChatSelectors() {
              const chats = document.querySelectorAll(
                '#folders-container a.chatlist-chat[data-peer-id]'
              );

              return [...chats].map((chat) => {
                const peerId = chat.getAttribute("data-peer-id");

                // Chat title only (never subtitle sender)
                const titleEl = chat.querySelector(
                  '.row-title-row .peer-title'
                );

                const name = titleEl ? titleEl.textContent.trim() : "unknown";

                const selector = `#folders-container a.chatlist-chat[data-peer-id="${peerId}"]`;

                return {
                  name,
                  peer_id: peerId,
                  selector
                };
              });
            }

            getChatSelectors();
            """,
        )

        return [
            Chat(
                name=chat["name"],
                peer_id=chat["peer_id"],
                selector=chat["selector"],
                tab=self._tab,
            )
            for chat in chats_data
        ]

    def _scroll_down(self) -> None:
        """Scroll down the chat list.

        Returns True if the chat list scrolls down, False otherwise.
        """
        self._tab.execute(
            """
            function getElementByXpath(path) {
              return document.evaluate(
                path,
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
              ).singleNodeValue;
            }

            function scrollDown() {
                const chats = getElementByXpath('//*[@id="folders-container"]/div[5]')
                chats.scrollTop += windowSize.height
            }

            scrollDown();
            """,
        )

    def _scroll_to_top(self) -> None:
        self._tab.execute(
            """
            function getElementByXpath(path) {
              return document.evaluate(
                path,
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
              ).singleNodeValue;
            }

            function scrollToTop() {
                const chats = getElementByXpath('//*[@id="folders-container"]/div[5]')
                chats.scrollTop = 0;
            }

            scrollToTop();
            """,
        )
