from __future__ import annotations

from typing import Final

import pytest

INTEGRATION_SKIP_REASON: Final[str] = "integration tests are opt-in and require --run-integration."


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run tests marked with 'integration'.",
    )


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "integration: opt-in tests that run real macOS integrations.",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-integration"):
        return

    skip_integration = pytest.mark.skip(reason=INTEGRATION_SKIP_REASON)
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
