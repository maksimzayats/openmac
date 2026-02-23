# openmac

## Installation

`openmac` is a Python library for automating macOS applications (focused on Chrome)
through AppleScript.

### Prerequisites

- macOS
- Python 3.10+
- Google Chrome installed
- [UV](https://docs.astral.sh/uv/) (recommended) and Git

### Install

```bash
git clone https://github.com/maksimzayats/openmac.git
cd openmac
uv sync --group dev
```

For a non-development installation:

```bash
uv pip install -e .
```

## Usage

```python
from openmac import Chrome

chrome = Chrome()
print(chrome.title)
print(chrome.version)
print(f"Windows open: {chrome.windows.count}")

if chrome.windows.count:
    window = chrome.windows.first
    print(window.title, window.mode)
```

If you want more details about how to run and use higher-level helpers, check the
package API (`Chrome`, `ChromeWindow`, and `ChromeTab`) in `src/openmac`.

## Platform Requirements

- macOS-only support (AppleScript/appscript integration).
- Supported macOS versions are not explicitly listed in the repository.
- Python-level version requirement: Python `>=3.10`.
