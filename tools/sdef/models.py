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

    type_elements: list[TypeElement] = Field(default_factory=list, alias="type_element")
    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")


class Element(BaseModel):
    type: str | None = None
    description: str | None = None
    hidden: YesNo | None = None
    access: AccessType | None = None

    type_elements: list[TypeElement] = Field(default_factory=list, alias="type_element")
    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")


class RespondsTo(BaseModel):
    command: str
    hidden: YesNo | None = None
    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")


class DirectParameter(BaseModel):
    type: str | None = None
    description: str | None = None
    optional: YesNo | None = None

    type_elements: list[TypeElement] = Field(default_factory=list, alias="type_element")


class Parameter(BaseModel):
    name: str | None = None
    code: str | None = None
    type: str | None = None
    description: str | None = None
    optional: YesNo | None = None

    type_elements: list[TypeElement] = Field(default_factory=list, alias="type_element")
    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")


class Result(BaseModel):
    type: str | None = None
    description: str | None = None

    type_elements: list[TypeElement] = Field(default_factory=list, alias="type_element")


class AccessGroup(BaseModel):
    identifier: str | None = None


class Command(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None

    access_groups: list[AccessGroup] = Field(default_factory=list, alias="access_group")
    parameters: list[Parameter] = Field(default_factory=list, alias="parameter")
    direct_parameters: list[DirectParameter] = Field(default_factory=list, alias="direct_parameter")
    results: list[Result] = Field(default_factory=list, alias="result")
    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")


class Class(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    hidden: YesNo | None = None

    properties: list[Property] = Field(default_factory=list, alias="property")
    elements: list[Element] = Field(default_factory=list, alias="element")
    responds_tos: list[RespondsTo] = Field(default_factory=list, alias="responds_to")
    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")


class ClassExtension(BaseModel):
    extends: str | None = None
    description: str | None = None
    hidden: YesNo | None = None

    properties: list[Property] = Field(default_factory=list, alias="property")
    elements: list[Element] = Field(default_factory=list, alias="element")
    responds_tos: list[RespondsTo] = Field(default_factory=list, alias="responds_to")
    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")


class Suite(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None

    classes: list[Class] = Field(default_factory=list, alias="class")
    class_extensions: list[ClassExtension] = Field(default_factory=list, alias="class_extension")
    commands: list[Command] = Field(default_factory=list, alias="command")


class Dictionary(BaseModel):
    title: str | None = None
    suites: list[Suite] = Field(default_factory=list, alias="suite")
