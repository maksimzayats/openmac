from __future__ import annotations

from dataclasses import dataclass

from achrome.core._internal.chome_api import ChromeAPI


@dataclass
class Context:
    chrome_api: ChromeAPI
