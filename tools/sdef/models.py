from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

YesNo = Literal["yes", "no"]
AccessType = Literal["r", "w", "rw"]


class Synonym(BaseModel):
    name: str | None = None
    code: str | None = None


class Documentation(BaseModel):
    html: str | None = None


class Accessor(BaseModel):
    style: str | None = None


class TypeElement(BaseModel):
    type: str
    list: YesNo | None = None
    hidden: YesNo | None = None


class Cocoa(BaseModel):
    class_: str | None = Field(default=None, alias="class")
    key: str | None = None
    method: str | None = None
    name: str | None = None
    boolean_value: str | None = None
    integer_value: str | None = None
    string_value: str | None = None


class AccessGroup(BaseModel):
    identifier: str | None = None
    access: AccessType | None = None


class Property(BaseModel):
    name: str | None = None
    code: str | None = None
    type: str | None = None
    description: str | None = None
    hidden: YesNo | None = None
    access: AccessType | None = None
    in_properties: YesNo | None = None

    type_elements: list[TypeElement] = Field(default_factory=list, alias="type_element")
    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")
    documentation: list[Documentation] = Field(default_factory=list, alias="documentation")
    synonyms: list[Synonym] = Field(default_factory=list, alias="synonym")


class Element(BaseModel):
    type: str | None = None
    description: str | None = None
    hidden: YesNo | None = None
    access: AccessType | None = None

    type_elements: list[TypeElement] = Field(default_factory=list, alias="type_element")
    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")
    accessors: list[Accessor] = Field(default_factory=list, alias="accessor")


class RespondsTo(BaseModel):
    command: str
    hidden: YesNo | None = None
    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")


class DirectParameter(BaseModel):
    type: str | None = None
    description: str | None = None
    optional: YesNo | None = None
    requires_access: AccessType | None = None

    type_elements: list[TypeElement] = Field(default_factory=list, alias="type_element")


class Parameter(BaseModel):
    name: str | None = None
    code: str | None = None
    type: str | None = None
    description: str | None = None
    optional: YesNo | None = None
    hidden: YesNo | None = None
    requires_access: AccessType | None = None

    type_elements: list[TypeElement] = Field(default_factory=list, alias="type_element")
    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")


class Result(BaseModel):
    type: str | None = None
    description: str | None = None
    optional: YesNo | None = None

    type_elements: list[TypeElement] = Field(default_factory=list, alias="type_element")


class Command(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    hidden: YesNo | None = None

    access_groups: list[AccessGroup] = Field(default_factory=list, alias="access_group")
    parameters: list[Parameter] = Field(default_factory=list, alias="parameter")
    direct_parameters: list[DirectParameter] = Field(default_factory=list, alias="direct_parameter")
    results: list[Result] = Field(default_factory=list, alias="result")
    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")
    documentation: list[Documentation] = Field(default_factory=list, alias="documentation")


class Class(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    hidden: YesNo | None = None
    inherits: str | None = None
    plural: str | None = None
    id: str | None = None

    properties: list[Property] = Field(default_factory=list, alias="property")
    elements: list[Element] = Field(default_factory=list, alias="element")
    responds_tos: list[RespondsTo] = Field(default_factory=list, alias="responds_to")
    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")
    access_groups: list[AccessGroup] = Field(default_factory=list, alias="access_group")
    type_elements: list[TypeElement] = Field(default_factory=list, alias="type_element")
    documentation: list[Documentation] = Field(default_factory=list, alias="documentation")
    synonyms: list[Synonym] = Field(default_factory=list, alias="synonym")


class ClassExtension(BaseModel):
    extends: str | None = None
    description: str | None = None
    hidden: YesNo | None = None

    properties: list[Property] = Field(default_factory=list, alias="property")
    elements: list[Element] = Field(default_factory=list, alias="element")
    responds_tos: list[RespondsTo] = Field(default_factory=list, alias="responds_to")
    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")
    synonyms: list[Synonym] = Field(default_factory=list, alias="synonym")


class Enumerator(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None

    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")
    synonyms: list[Synonym] = Field(default_factory=list, alias="synonym")


class Enumeration(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None

    enumerators: list[Enumerator] = Field(default_factory=list, alias="enumerator")


class ValueType(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None

    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")
    synonyms: list[Synonym] = Field(default_factory=list, alias="synonym")


class RecordType(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None

    properties: list[Property] = Field(default_factory=list, alias="property")
    documentation: list[Documentation] = Field(default_factory=list, alias="documentation")


class XInclude(BaseModel):
    href: str | None = None
    xpointer: str | None = None


class Suite(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    hidden: YesNo | None = None

    classes: list[Class] = Field(default_factory=list, alias="class")
    class_extensions: list[ClassExtension] = Field(default_factory=list, alias="class_extension")
    commands: list[Command] = Field(default_factory=list, alias="command")
    access_groups: list[AccessGroup] = Field(default_factory=list, alias="access_group")
    cocoas: list[Cocoa] = Field(default_factory=list, alias="cocoa")
    enumerations: list[Enumeration] = Field(default_factory=list, alias="enumeration")
    value_types: list[ValueType] = Field(default_factory=list, alias="value_type")
    record_types: list[RecordType] = Field(default_factory=list, alias="record_type")
    xi_includes: list[XInclude] = Field(default_factory=list, alias="xi:include")


class Dictionary(BaseModel):
    title: str | None = None
    xmlns_xi: str | None = Field(default=None, alias="xmlns:xi")

    suites: list[Suite] = Field(default_factory=list, alias="suite")
    xi_includes: list[XInclude] = Field(default_factory=list, alias="xi:include")
