from __future__ import annotations

import os
import platform
from typing import Final

import pytest

from openmac._internal.applescript.executor import AppleScriptExecutor
from openmac._internal.applescript.runner import AppleScriptSDEFCommandRunner

FINDER_PROBE_SCRIPT: Final[str] = 'tell application id "com.apple.finder" to exists startup disk'
OSASCRIPT_PATH: Final[str] = "/usr/bin/osascript"
FINDER_PERMISSION_ERROR_MARKERS: Final[tuple[str, ...]] = ("not authorized", "-1743")
FINDER_PERMISSION_SKIP_REASON: Final[str] = (
    "Finder automation permission is missing. "
    "Allow your terminal in System Settings > Privacy & Security > Automation, then rerun."
)


def _is_finder_permission_error(message: str) -> bool:
    normalized_message = message.lower()
    return any(marker in normalized_message for marker in FINDER_PERMISSION_ERROR_MARKERS)


@pytest.fixture(scope="session")
def integration_executor() -> AppleScriptExecutor:
    if platform.system() != "Darwin":
        pytest.skip("Integration tests require macOS (Darwin).")

    if not os.access(OSASCRIPT_PATH, os.X_OK):
        pytest.skip("Integration tests require /usr/bin/osascript.")

    return AppleScriptExecutor(executable=OSASCRIPT_PATH)


@pytest.fixture(scope="session")
def finder_ready_executor(integration_executor: AppleScriptExecutor) -> AppleScriptExecutor:
    try:
        integration_executor.execute(FINDER_PROBE_SCRIPT)
    except RuntimeError as error:
        if _is_finder_permission_error(str(error)):
            pytest.skip(FINDER_PERMISSION_SKIP_REASON)
        pytest.fail(f"Unexpected Finder probe failure: {error}", pytrace=False)

    return integration_executor


@pytest.fixture(scope="session")
def finder_runner(
    finder_ready_executor: AppleScriptExecutor,
) -> AppleScriptSDEFCommandRunner:
    return AppleScriptSDEFCommandRunner(executor=finder_ready_executor)
