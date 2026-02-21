from __future__ import annotations

import pytest

from openmac.apps.chrome.objects.application import Chrome


@pytest.fixture(scope="module")
def chrome() -> Chrome:
    return Chrome()


def test_application_properties_complete(chrome: Chrome) -> None:
    properties = chrome.properties
    ae_properties = chrome._ae_object.properties()

    assert properties == ae_properties
