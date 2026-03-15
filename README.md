# openmac

`openmac` is a Python library for automating macOS applications through
AppleScript and `appscript`.

The current codebase is centered on browser automation:

- Chrome automation via typed window, tab, and bookmark objects
- Safari automation via typed window, tab, and document objects

The project is still in an early stage, so breaking API changes are acceptable.

## Requirements

- macOS
- Python 3.14+
- [uv](https://docs.astral.sh/uv/) for development workflows
- Installed target applications such as Google Chrome or Safari

## Installation

Clone the repository and install development dependencies:

```bash
git clone https://github.com/maksimzayats/openmac.git
cd openmac
uv sync --group dev
```

For a local editable install without the full dev group:

```bash
uv pip install -e .
```

## Development commands

```bash
make format
make lint
make test
make docs
uv build
```

## Usage

Basic browser automation:

```python
from openmac import Chrome, Safari

chrome = Chrome()
print(chrome.version)
print(chrome.windows.count)

safari = Safari()
tab = safari.tabs.open("https://example.com", wait_until_loaded=True)
print(tab.title)
print(tab.url)
```

Public exports are currently defined in `src/openmac/__init__.py`. More
specialized app APIs live under `src/openmac/apps`.

## Project layout

- `src/openmac`: library source
- `src/openmac/apps/browsers`: browser integrations and typed objects
- `tests/unit`: isolated tests
- `tests/integration`: browser integration tests
- `docs`: Sphinx documentation

## Testing approach

For browser automation, prefer integration tests against real browsers and real
application behavior. This repository already uses browser-backed integration
tests for browser objects, and new browser work should follow that pattern.

Prevent data leaks while doing this:

- use dedicated test accounts and disposable test data
- prefer public, local, synthetic, or staging sites over personal or
  production-only data
- do not commit secrets, private URLs, session artifacts, screenshots, or
  assertions that expose sensitive content
- keep assertions focused on behavior and structure rather than personal data

## Platform support

- macOS only
- Python `>=3.14`

## Documentation

Project metadata points to [docs.openmac.dev](https://docs.openmac.dev). Build
the local docs with:

```bash
make docs
```
