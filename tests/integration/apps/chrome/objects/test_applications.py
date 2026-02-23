from __future__ import annotations

from dataclasses import fields

from openmac.apps.chrome.objects.application import Chrome


def test_application_properties_complete(chrome: Chrome) -> None:
    properties = chrome.properties
    properties_keys = {field.name for field in fields(properties)}

    ae_properties = chrome.ae_chrome.properties()
    ae_properties_keys = {keyword.AS_name for keyword in ae_properties}

    diff = properties_keys.symmetric_difference(ae_properties_keys)

    # TODO(Maksim): add "bookmarks_bar", "other_bookmarks"
    assert diff == {"bookmarks_bar", "other_bookmarks", "class_"}
