from __future__ import annotations

import pytest

from openmac._internal.applescript.runner import AppleScriptSDEFCommandRunner
from openmac.apps.finder.sdef.suites.standard.commands import CountCommand, ExistsCommand

pytestmark = pytest.mark.integration


def test_run_raw_returns_raw_applescript_literal_for_exists_command(
    finder_runner: AppleScriptSDEFCommandRunner,
) -> None:
    command = ExistsCommand.model_validate({"direct_parameter": "startup disk"})
    assert finder_runner.run_raw(command) == "true"


def test_run_deserializes_bool_result_for_exists_command(
    finder_runner: AppleScriptSDEFCommandRunner,
) -> None:
    command = ExistsCommand.model_validate({"direct_parameter": "startup disk"})
    result = finder_runner.run(command)
    assert result is True
    assert isinstance(result, bool)


def test_run_deserializes_int_result_for_count_command(
    finder_runner: AppleScriptSDEFCommandRunner,
) -> None:
    command = CountCommand.model_validate({"direct_parameter": "desktop", "each": "item"})
    result = finder_runner.run(command)
    assert isinstance(result, int)
    assert result >= 0
