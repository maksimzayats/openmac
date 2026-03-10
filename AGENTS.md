# Agent Notes for openmac

This repository is a Python 3.14+ typed macOS automation library built around
AppleScript and `appscript`. The current codebase focuses on browser automation
for Chrome and Safari, plus higher-level page objects for real web apps. Use
strict linting, typing, and testing standards. Prefer uv for all tooling.

## Project maturity

- This project is in an EARLY stage.
- There is no stable public API yet; breaking changes are acceptable by default.

## Quick commands

- Install deps (dev): `uv sync --group dev`
- Format: `make format`
- Lint (all): `make lint`
- Test (all): `make test`
- Build docs: `make docs`

## Build

- Build wheel/sdist: `uv build`
- Versioning is derived from Git via `uv-dynamic-versioning`.
- Clean build artifacts manually if needed (no scripted clean target)

## Lint and type checks

- Always keep linting and type-checking clean; do not proceed with changes that introduce errors.
- Ruff lint: `uv run ruff check .`
- Ruff auto-fix (limited): `uv run ruff check --fix-only .`
- Ruff format: `uv run ruff format .`
- mypy (strict): `uv run mypy .`

## Tests

- Run all tests (coverage): `make test`
- Run a single test file: `uv run pytest tests/test_some.py`
- Run a single test: `uv run pytest tests/test_some.py::test_some`
- Run tests with keyword filter: `uv run pytest -k "dependency" tests/`
- Coverage (recommended for new work):
  `uv run pytest tests/ --cov=src/openmac --cov-report=term-missing`

## Repo structure

- Library code lives under `src/openmac`.
- Public exports are centered in `src/openmac/__init__.py`.
- Browser integrations currently include Chrome and Safari under
  `src/openmac/apps/browsers`.
- Real-page abstractions live under `src/openmac/apps/browsers/pages`.
- Shared helpers live under `src/openmac/apps/shared` and
  `src/openmac/apps/system_events`.
- Tests are split into `tests/unit` and `tests/integration`.
- Sphinx docs live under `docs/`.

## Style and formatting

- Just run `make format` to apply all formatting rules (Ruff and any additional formatting).
- Line length: 100 (Ruff).
- Quotes: double quotes (Ruff format).
- Indent: 4 spaces.
- Format with Ruff before linting.
- Use ASCII unless the file already contains non-ASCII characters.

## Imports

- No relative imports in library code (Ruff tidy-imports bans them).
- Prefer explicit imports from `openmac` modules.
- Combine `as` imports when appropriate (`combine-as-imports = true`).
- Avoid unused imports; `__init__.py` is allowed to re-export.

## Typing and types

- Always use __future__ annotations for forward references and to enable postponed evaluation of annotations.
- Python minimum version is 3.10 with future annotation (use `|` unions, `list[str]`, etc.).
- All new public APIs must be fully typed.
- mypy is strict; keep types precise and avoid use `Any` if is unavoidable, document why and keep scope minimal.
- Do not use `| object` unions in new annotations - use Any instead.
- Use `typing.Protocol` or `collections.abc` for public contracts.
- Prefer `Final` for constants that should not change.

## Naming conventions

- Classes: `PascalCase`.
- Functions and variables: `snake_case`.
- Constants: `UPPER_SNAKE_CASE`.
- Public API names should be stable and descriptive.
- Test names should describe the behavior and expectation.

## Error handling

- Prefer explicit error messages over implicit failures.
- Avoid catching `Exception` unless re-raising with context.
- When adding new errors, update tests and docs/examples as needed.

## Docstrings and docs

## Testing guidelines

- Aim for maximum coverage and edge cases for all new features.
- Maintain 100% coverage overall; every change must keep coverage at 100%.
- Tests live in `tests/` and mirror module naming when possible.
- Use pytest fixtures from `tests/conftest.py` for shared setup.
- Prefer small, focused tests for pure logic, but for browser apps/page objects
  favor integration tests against real browser pages and real app behavior.
- When building apps/pages, treat real-page integration coverage as the primary
  confidence signal; mocks should only support isolated logic that cannot be
  exercised cleanly end-to-end.
- Prevent data leaks in integration tests: use dedicated test accounts, safe
  fixtures, and non-sensitive pages whenever possible.
- Never encode personal data, secrets, tokens, private URLs, or production-only
  content in tests, fixtures, logs, assertions, screenshots, or snapshots.
- Prefer local, synthetic, staging, or explicitly disposable test data, and
  keep assertions focused on structure/behavior rather than sensitive content.
- Keep tests deterministic; avoid time-based assertions unless necessary.

## Docs and README

- Keep `README.md` aligned with the actual public surface and repository
  workflow.
- When adding or changing browser/page capabilities, update docs/examples so
  they reflect the current supported apps and testing approach.
- Do not document stale APIs or unsupported workflows.

## Quality gates

- Always ensure linting and type-checking run clean with no errors.
- Every new change must preserve 100% test coverage.
- After making changes, always run `make lint` and `make test` and report results.

## Ruff configuration highlights

- `select = ["ALL"]` with targeted ignores.
- Tests allow `assert`, unused args, and some pytest patterns.

## Agent behavior

- Do not add new lint ignores without justification.
- Preserve existing formatting and file organization.
- Update or add tests whenever behavior changes.
