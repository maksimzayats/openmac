from __future__ import annotations

from openmac.apps._internal.base import BaseObject


def get_apple_script_properties(
    obj: BaseObject,
    mapping: dict[str, str] | None = None,
) -> set[str]:
    mapping = mapping or {}

    apple_script_references = obj._ae_object.AS_appdata.referencebyname()

    apple_script_properties = set()
    for name, (kind, _) in apple_script_references.items():
        if kind != b"p":
            continue

        apple_script_properties.add(mapping.get(name, name))

    return apple_script_properties


def get_app_properties(app: BaseObject) -> set[str]:
    return {name for name, member in app.__class__.__dict__.items() if isinstance(member, property)}
