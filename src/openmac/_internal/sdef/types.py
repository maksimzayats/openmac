from __future__ import annotations

from collections import UserDict, UserString
from typing import Any, NamedTuple

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema


class Specifier(UserString):
    """A specifier returned from Apple Script, represented as a string."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))


class LocationSpecifier(Specifier):
    """A location specifier returned from Apple Script, represented as a string."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))


class Record(UserDict[str, Any]):
    """A record returned from Apple Script, represented as a dictionary."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(dict))


class Date(UserString):
    """A date returned from Apple Script, represented as a string."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))


class File(UserString):
    """A file returned from Apple Script, represented as a string."""

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source_type: Any,
        handler: GetCoreSchemaHandler,
    ) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))


class Point(NamedTuple):
    """A point returned from Apple Script, represented as a dictionary with keys 'x' and 'y'."""

    x: int
    y: int


class Rectangle(NamedTuple):
    """A rectangle returned from Apple Script, represented as a dictionary with keys 'left', 'top', 'right', and 'bottom'."""

    left: int
    top: int
    right: int
    bottom: int
