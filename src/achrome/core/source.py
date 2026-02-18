from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Source:
    html: str
    snapshot: Snapshot

    @classmethod
    def from_html(cls, html: str) -> Source:
        return cls(html=html, snapshot=Snapshot.from_html(html))


class Snapshot:
    @classmethod
    def from_html(cls, html: str) -> Snapshot:
        return cls()
