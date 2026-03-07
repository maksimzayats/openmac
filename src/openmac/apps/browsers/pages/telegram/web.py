from __future__ import annotations

from collections.abc import Iterator

from typing_extensions import Self  # noqa: UP035

from openmac.apps.browsers.pages.base import BasePage, BasePageElement
from openmac.apps.shared.base import BaseManager


class TelegramPage(BasePage):
    @property
    def folders(self) -> TelegramChatsFolder:
        return TelegramChatsFolder()


class TelegramChatsFolder(BasePageElement):
    @property
    def chats(self) -> TelegramChatsManager:
        return TelegramChatsManager()

    @property
    def forums(self) -> TelegramForumsManager:
        return TelegramForumsManager()


class TelegramChat(BasePageElement):
    @property
    def messages(self) -> TelegramChatMessagesManager:
        return TelegramChatMessagesManager()

    def go_to_bottom(self) -> Self:
        raise NotImplementedError


class TelegramForum(BasePageElement):
    @property
    def topics(self) -> TelegramForumTopicsManager:
        return TelegramForumTopicsManager()


class TelegramForumTopic(TelegramChat):
    pass


class TelegramChatMessage(BasePageElement):
    pass


# region Managers


class TelegramFoldersManager(BaseManager[TelegramChatsFolder]):
    def _iter_objects(self) -> Iterator[TelegramChatsFolder]:
        raise NotImplementedError


class TelegramChatsManager(BaseManager[TelegramChat]):
    def _iter_objects(self) -> Iterator[TelegramChat]:
        raise NotImplementedError


class TelegramForumsManager(BaseManager[TelegramForum]):
    def _iter_objects(self) -> Iterator[TelegramForum]:
        raise NotImplementedError


class TelegramForumTopicsManager(BaseManager[TelegramForumTopic]):
    def _iter_objects(self) -> Iterator[TelegramForumTopic]:
        raise NotImplementedError


class TelegramChatMessagesManager(BaseManager[TelegramChatMessage]):
    def _iter_objects(self) -> Iterator[TelegramChatMessage]:
        raise NotImplementedError


# endregion Managers
