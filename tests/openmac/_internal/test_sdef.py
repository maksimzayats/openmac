from __future__ import annotations

from types import NoneType

from pydantic import BaseModel

from openmac._internal.manager import Manager
from openmac._internal.sdef.base import SDEFClass, SDEFCommand
from openmac._internal.sdef.types import (
    Date,
    File,
    LocationSpecifier,
    Point,
    Record,
    Rectangle,
    Specifier,
)


class SdefPayload(BaseModel):
    specifier: Specifier[SDEFClass]
    location: LocationSpecifier
    record: Record
    date: Date
    file: File
    point: Point
    rectangle: Rectangle


class DemoSdefClass(SDEFClass):
    value: int


class DemoSdefCommand(SDEFCommand[NoneType]):
    argument: int


def test_sdef_custom_types_validate_with_pydantic() -> None:
    payload = SdefPayload.model_validate({
        "specifier": "window 1",
        "location": "location specifier",
        "record": {"foo": "bar"},
        "date": "2026-02-18",
        "file": "test.txt",
        "point": {"x": 1, "y": 2},
        "rectangle": {"left": 1, "top": 2, "right": 3, "bottom": 4},
    })

    assert isinstance(payload.specifier, Specifier)
    assert isinstance(payload.location, LocationSpecifier)
    assert isinstance(payload.record, Record)
    assert isinstance(payload.date, Date)
    assert isinstance(payload.file, File)
    assert isinstance(payload.point, Point)
    assert isinstance(payload.rectangle, Rectangle)


def test_sdef_model_validates_without_context() -> None:
    model = DemoSdefClass.model_validate({"value": 7})

    assert model.value == 7


def test_manager_can_be_specialized() -> None:
    class StringManager(Manager[str]):
        pass

    assert issubclass(StringManager, Manager)


def test_sdef_command_is_not_callable() -> None:
    command = DemoSdefCommand.model_validate({"argument": 3})

    assert not callable(command)
