from __future__ import annotations


class Snapshot:
    @classmethod
    def from_source(cls, html: str) -> Snapshot:
        return cls()
