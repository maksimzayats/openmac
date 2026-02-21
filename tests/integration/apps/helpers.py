from __future__ import annotations

from openmac.apps._internal.base import BaseApplication


def get_apple_script_properties(app: BaseApplication) -> set[str]:
    apple_script_references = app._app.AS_appdata.referencebyname()

    apple_script_properties = set()
    for name, (kind, _) in apple_script_references.items():
        if kind != b"p":
            continue

        apple_script_properties.add(name)

    return apple_script_properties


def get_app_properties(app: BaseApplication) -> set[str]:
    return {name for name, member in app.__class__.__dict__.items() if isinstance(member, property)}
