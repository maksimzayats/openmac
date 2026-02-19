from __future__ import annotations

from dataclasses import dataclass, field

AccessGroupMeta = tuple[str | None, str | None]
RespondsToMeta = tuple[str, bool | None]


@dataclass(slots=True, frozen=True)
class SuiteMeta:
    name: str
    code: str | None
    description: str | None
    hidden: bool | None


@dataclass(slots=True, frozen=True)
class ParameterMeta:
    name: str
    code: str | None
    type: str | None
    description: str | None
    optional: bool | None
    hidden: bool | None
    requires_access: str | None


@dataclass(slots=True, frozen=True)
class ResultMeta:
    type: str | None
    description: str | None
    optional: bool | None


@dataclass(slots=True, frozen=True)
class CommandMeta:
    name: str
    code: str | None
    description: str | None
    hidden: bool | None
    bundle_id: str
    direct_parameter_type: str | None
    parameters: tuple[ParameterMeta, ...] = field(default_factory=tuple)
    results: tuple[ResultMeta, ...] = field(default_factory=tuple)
    access_groups: tuple[AccessGroupMeta, ...] = field(default_factory=tuple)


@dataclass(slots=True, frozen=True)
class PropertyMeta:
    name: str
    code: str | None
    type: str | None
    description: str | None
    hidden: bool | None
    access: str | None
    in_properties: bool | None


@dataclass(slots=True, frozen=True)
class ElementMeta:
    type: str
    description: str | None
    hidden: bool | None
    access: str | None


@dataclass(slots=True, frozen=True)
class ClassMeta:
    name: str
    code: str | None
    description: str | None
    hidden: bool | None
    inherits: str | None
    plural: str | None
    id: str | None
    properties: tuple[PropertyMeta, ...] = field(default_factory=tuple)
    elements: tuple[ElementMeta, ...] = field(default_factory=tuple)
    responds_to: tuple[RespondsToMeta, ...] = field(default_factory=tuple)


@dataclass(slots=True, frozen=True)
class EnumeratorMeta:
    name: str
    code: str | None
    description: str | None


@dataclass(slots=True, frozen=True)
class EnumerationMeta:
    name: str
    code: str | None
    description: str | None
    hidden: bool | None
    enumerators: tuple[EnumeratorMeta, ...] = field(default_factory=tuple)


@dataclass(slots=True, frozen=True)
class ValueTypeMeta:
    name: str
    code: str | None
    description: str | None
