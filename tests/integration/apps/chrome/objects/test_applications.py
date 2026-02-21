from __future__ import annotations

from openmac.apps.chrome.objects.application import Chrome


def test_application_properties_complete(chrome: Chrome) -> None:
    properties = chrome.properties
    properties_keys = set(properties.__dataclass_fields__.keys())

    ae_properties = chrome._ae_object.properties()
    ae_properties_keys = {keyword.AS_name for keyword in ae_properties}

    diff = properties_keys.symmetric_difference(ae_properties_keys)

    # TODO(Maksim): add "bookmarks_bar", "other_bookmarks"
    assert diff == {"bookmarks_bar", "other_bookmarks", "class_"}
