from __future__ import annotations

import os
import platform
from typing import Final

import pytest

from openmac._internal.applescript.executor import AppleScriptExecutor

OSASCRIPT_PATH: Final[str] = "/usr/bin/osascript"


@pytest.fixture(scope="session")
def integration_executor() -> AppleScriptExecutor:
    if platform.system() != "Darwin":
        pytest.skip("Integration tests require macOS (Darwin).")

    if not os.access(OSASCRIPT_PATH, os.X_OK):
        pytest.skip("Integration tests require /usr/bin/osascript.")

    return AppleScriptExecutor(executable=OSASCRIPT_PATH)
