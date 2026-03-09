from __future__ import annotations

from datetime import UTC, datetime, tzinfo

import pytest

import openmac.apps.browsers.pages.telegram.chat as telegram_chat


class FrozenDateTime(datetime):
    @classmethod
    def now(cls, tz: tzinfo | None = None) -> FrozenDateTime:
        frozen_now = cls(2026, 3, 10, 15, 45, tzinfo=UTC)
        if tz is None:
            return frozen_now.replace(tzinfo=None)

        return frozen_now.astimezone(tz)


def test_parse_telegram_message_datetime_uses_today_for_time_only_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(telegram_chat, "datetime", FrozenDateTime)

    parsed_datetime = telegram_chat._parse_telegram_message_datetime("10:30")

    assert parsed_datetime == FrozenDateTime(
        2026,
        3,
        10,
        10,
        30,
        tzinfo=telegram_chat.LOCAL_TIMEZONE,
    )


def test_parse_telegram_message_datetime_preserves_explicit_date() -> None:
    parsed_datetime = telegram_chat._parse_telegram_message_datetime("2026-02-03 10:30")

    assert parsed_datetime == datetime(2026, 2, 3, 10, 30, tzinfo=telegram_chat.LOCAL_TIMEZONE)
