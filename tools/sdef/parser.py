from __future__ import annotations

from pathlib import Path
from typing import Any

import xmltodict
from pydantic import ValidationError

from tools.sdef.models import Dictionary

FORCE_LIST: tuple[str, ...] = (
    "suite",
    "class",
    "class-extension",
    "command",
    "enumeration",
    "enumerator",
    "value-type",
    "record-type",
    "property",
    "element",
    "responds-to",
    "parameter",
    "direct-parameter",
    "result",
    "type",
    "cocoa",
    "access-group",
    "synonym",
    "documentation",
    "accessor",
    "xi:include",
)


def _normalize_key(key: str) -> str:
    return key.replace("-", "_")


def _normalize_sdef_data(value: Any) -> Any:
    if isinstance(value, list):
        return [_normalize_sdef_data(item) for item in value]

    if isinstance(value, dict):
        normalized: dict[str, Any] = {}

        for key, item in value.items():
            if not key.startswith("@"):
                continue

            normalized[_normalize_key(key[1:])] = _normalize_sdef_data(item)

        for key, item in value.items():
            if key.startswith("@"):
                continue

            normalized_key = _normalize_key(key)
            normalized_value = _normalize_sdef_data(item)

            if normalized_key == "type":
                normalized["type_element"] = normalized_value
                continue

            normalized[normalized_key] = normalized_value

        return normalized

    return value


def load_sdef(path: Path) -> Dictionary:
    xml_content = path.read_text(encoding="utf-8")

    try:
        raw_data = xmltodict.parse(
            xml_content,
            force_list=FORCE_LIST,
            disable_entities=False,
        )
    except xmltodict.expat.ExpatError as exc:
        msg = f"Failed to parse SDEF XML at {path}: {exc}"
        raise ValueError(msg) from exc

    try:
        dictionary_data = raw_data["dictionary"]
    except KeyError as exc:
        msg = f"Missing <dictionary> root element in SDEF XML at {path}"
        raise ValueError(msg) from exc

    normalized_dictionary = _normalize_sdef_data(dictionary_data)

    try:
        return Dictionary.model_validate(normalized_dictionary, extra="forbid")
    except ValidationError as exc:
        msg = f"Failed to validate SDEF XML at {path}: {exc}"
        raise ValueError(msg) from exc


def main() -> None:
    path = Path("suite.sdef")
    dictionary = load_sdef(path)
    print(dictionary)

    Path("suite.json").write_text(dictionary.model_dump_json(indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
