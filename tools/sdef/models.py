from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

YesNo = Literal["yes", "no"]
AccessType = Literal["r", "w", "rw"]


class TypeElement(BaseModel):
    type: str
    list: YesNo | None = None


class Cocoa(BaseModel):
    class_: str | None = Field(default=None, alias="class")
    key: str | None = None
    method: str | None = None
    name: str | None = None


class Property(BaseModel):
    name: str | None = None
    code: str | None = None
    type: str | None = None
    description: str | None = None
    hidden: YesNo | None = None
    access: AccessType | None = None

    type_element: list[TypeElement] = Field(default_factory=list)
    cocoa: list[Cocoa] = Field(default_factory=list)


class Element(BaseModel):
    type: str | None = None
    description: str | None = None
    hidden: YesNo | None = None
    access: AccessType | None = None

    type_element: list[TypeElement] = Field(default_factory=list)
    cocoa: list[Cocoa] = Field(default_factory=list)


class RespondsTo(BaseModel):
    command: str
    hidden: YesNo | None = None
    cocoa: list[Cocoa] = Field(default_factory=list)


class DirectParameter(BaseModel):
    type: str | None = None
    description: str | None = None
    optional: YesNo | None = None

    type_element: list[TypeElement] = Field(default_factory=list)


class Parameter(BaseModel):
    name: str | None = None
    code: str | None = None
    type: str | None = None
    description: str | None = None
    optional: YesNo | None = None

    type_element: list[TypeElement] = Field(default_factory=list)
    cocoa: list[Cocoa] = Field(default_factory=list)


class Result(BaseModel):
    type: str | None = None
    description: str | None = None

    type_element: list[TypeElement] = Field(default_factory=list)


class Command(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None

    parameter: list[Parameter] = Field(default_factory=list)
    direct_parameter: list[DirectParameter] = Field(default_factory=list)
    result: list[Result] = Field(default_factory=list)
    cocoa: list[Cocoa] = Field(default_factory=list)


class Class(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    hidden: YesNo | None = None

    property: list[Property] = Field(default_factory=list)
    element: list[Element] = Field(default_factory=list)
    responds_to: list[RespondsTo] = Field(default_factory=list)
    cocoa: list[Cocoa] = Field(default_factory=list)


class ClassExtension(BaseModel):
    extends: str | None = None
    description: str | None = None
    hidden: YesNo | None = None

    property: list[Property] = Field(default_factory=list)
    element: list[Element] = Field(default_factory=list)
    responds_to: list[RespondsTo] = Field(default_factory=list)
    cocoa: list[Cocoa] = Field(default_factory=list)


class Suite(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None

    class_: list[Class] = Field(default_factory=list, alias="class")
    class_extension: list[ClassExtension] = Field(default_factory=list)
    command: list[Command] = Field(default_factory=list)


class Dictionary(BaseModel):
    title: str | None = None
    suite: list[Suite] = Field(default_factory=list)
