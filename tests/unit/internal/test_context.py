from __future__ import annotations

from openmac._internal.applescript.executor import AppleScriptExecutor
from openmac._internal.context import Context


def test_context_stores_executor() -> None:
    executor = AppleScriptExecutor()
    context = Context(executor=executor)

    assert context.executor is executor
