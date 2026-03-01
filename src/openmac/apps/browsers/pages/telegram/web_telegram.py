from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel

# ============================================================
# Core Enums
# ============================================================


class ChatType(str, Enum):
    PRIVATE = "private"
    GROUP = "group"
    FORUM = "forum"
    CHANNEL = "channel"
    SAVED = "saved"


class PresenceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class MessageDeliveryStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"


# ============================================================
# Root Application
# ============================================================


class TelegramWebApp(BaseModel):
    account: UserAccount
    navigation: NavigationLayer
    conversation: ConversationLayer | None
    context_panel: ContextPanel | None
    overlay_system: OverlaySystem


# ============================================================
# Account
# ============================================================


class UserAccount(BaseModel):
    user_id: int
    display_name: str
    avatar_url: str | None
    is_premium: bool
    menu: AccountMenu


class AccountMenu(BaseModel):
    items: list[MenuItem]


class MenuItem(BaseModel):
    label: str
    action: str
    icon: str | None


# ============================================================
# Navigation Layer (Left Column)
# ============================================================


class NavigationLayer(BaseModel):
    search: GlobalSearch
    emoji_status: EmojiStatus
    folders: list[ChatFolder]
    chat_list: ChatList
    compose_button: ComposeMenu


class GlobalSearch(BaseModel):
    query: str
    placeholder: str


class EmojiStatus(BaseModel):
    emoji: str | None


class ChatFolder(BaseModel):
    id: str
    title: str
    unread_count: int
    is_active: bool


class ChatList(BaseModel):
    chats: list[ChatListItem]


class ChatListItem(BaseModel):
    chat_id: int
    title: str
    type: ChatType
    avatar_url: str | None
    presence: PresenceStatus
    is_muted: bool
    is_pinned: bool
    unread_count: int
    last_message: LastMessagePreview | None


class LastMessagePreview(BaseModel):
    sender_name: str | None
    text: str
    timestamp: datetime | None
    delivery_status: MessageDeliveryStatus | None


class ComposeMenu(BaseModel):
    actions: list[ComposeAction]


class ComposeAction(BaseModel):
    label: str
    action: Literal["new_channel", "new_group", "new_message"]


# ============================================================
# Conversation Layer (Middle Column)
# ============================================================


class ConversationLayer(BaseModel):
    chat_id: int
    header: ChatHeader
    messages: list[Message]
    composer: MessageComposer


class ChatHeader(BaseModel):
    title: str
    subtitle: str | None
    avatar_url: str | None


class Message(BaseModel):
    message_id: int
    sender_id: int
    sender_name: str
    text: str
    timestamp: datetime
    is_outgoing: bool
    delivery_status: MessageDeliveryStatus | None
    attachments: list[Attachment]


class Attachment(BaseModel):
    type: Literal["image", "video", "file", "link"]
    url: str
    filename: str | None


class MessageComposer(BaseModel):
    draft_text: str
    attachments: list[Attachment]
    is_recording_voice: bool


# ============================================================
# Context Panel (Right Column)
# ============================================================


class ContextPanel(BaseModel):
    chat_id: int
    profile: ChatProfile
    shared_media: list[Attachment]
    shared_files: list[Attachment]


class ChatProfile(BaseModel):
    title: str
    description: str | None
    members_count: int | None
    avatar_url: str | None


# ============================================================
# Overlay System
# ============================================================


class OverlaySystem(BaseModel):
    active_modals: list[Modal]
    context_menus: list[ContextMenu]


class Modal(BaseModel):
    id: str
    type: str
    is_open: bool


class ContextMenu(BaseModel):
    id: str
    items: list[MenuItem]
