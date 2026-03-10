# openmac

`openmac` is a Python library for automating macOS applications through
AppleScript and `appscript`.

The current codebase is centered on browser automation:

- Chrome automation via typed window, tab, and bookmark objects
- Safari automation via typed window, tab, and document objects
- Higher-level page objects for real web apps under `openmac.apps.browsers.pages`

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

Page objects are available for higher-level workflows:

```python
from openmac import Safari
from openmac.apps.browsers.pages.telegram.web import TelegramWebPage

safari = Safari()
tab = safari.tabs.open("https://web.telegram.org/a/", wait_until_loaded=True)
page = tab.as_page(TelegramWebPage)

print(page.folders.active.name)
```

Public exports are currently defined in `src/openmac/__init__.py`. More
specialized app and page APIs live under `src/openmac/apps`.

## Project layout

- `src/openmac`: library source
- `src/openmac/apps/browsers`: browser integrations and typed objects
- `src/openmac/apps/browsers/pages`: higher-level page abstractions
- `tests/unit`: isolated tests
- `tests/integration`: browser and page integration tests
- `docs`: Sphinx documentation

## Testing approach

For app and page automation, prefer integration tests against real browser pages
and real application behavior. This repository already uses browser-backed
integration tests for browser objects and page models, and new app/page work
should follow that pattern.

Prevent data leaks while doing this:

- use dedicated test accounts and disposable test data
- prefer public, local, synthetic, or staging pages over personal or
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
