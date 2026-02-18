from __future__ import annotations

from pathlib import Path

import xmltodict

from tools.sdef.models import Dictionary


def load_sdef(path: Path) -> Dictionary:
    _ = xmltodict


def main() -> None:
    path = Path("suite.sdef")
    dictionary = load_sdef(path)
    print(dictionary)


if __name__ == "__main__":
    main()
