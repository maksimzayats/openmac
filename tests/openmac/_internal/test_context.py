from __future__ import annotations

from openmac._internal.context import Context
from openmac._internal.runner import AppleScriptRunner


def test_context_stores_runner() -> None:
    runner = AppleScriptRunner()
    context = Context(runner=runner)

    assert context.runner is runner
