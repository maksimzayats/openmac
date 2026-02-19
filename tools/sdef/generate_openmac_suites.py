# ruff: noqa: C901, FURB113, PERF401, PLR0911, PLR0912, PLR0913, PLR0914, PLR0915, PLR0917

from __future__ import annotations

import argparse
import builtins
import json
import keyword
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from pydantic import BaseModel

ROOT: Final[Path] = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.sdef.models import (  # noqa: E402
    Class,
    ClassExtension,
    Command,
    Dictionary,
    DirectParameter,
    Element,
    Enumeration,
    Enumerator,
    Parameter,
    Property,
    Result,
    Suite,
    TypeElement,
    ValueType,
)
from tools.sdef.parser import load_sdef  # noqa: E402

SCRIPT_PATH: Final[Path] = ROOT / "tools" / "sdef" / "generate_openmac_suites.py"


@dataclass(frozen=True, slots=True)
class AppTarget:
    app: str
    package: str
    sdef_path: Path
    suites_dir: Path


APP_TARGETS: Final[dict[str, AppTarget]] = {
    "chrome": AppTarget(
        app="chrome",
        package="openmac.chrome.sdef.suites",
        sdef_path=ROOT / "src" / "openmac" / "chrome" / "chrome.sdef",
        suites_dir=ROOT / "src" / "openmac" / "chrome" / "sdef" / "suites",
    ),
    "finder": AppTarget(
        app="finder",
        package="openmac.finder.sdef.suites",
        sdef_path=ROOT / "src" / "openmac" / "finder" / "finder.sdef",
        suites_dir=ROOT / "src" / "openmac" / "finder" / "sdef" / "suites",
    ),
}

PRIMITIVE_TYPE_MAP: Final[dict[str, str]] = {
    "any": "object",
    "boolean": "bool",
    "double integer": "int",
    "double real": "float",
    "integer": "int",
    "number": "float",
    "real": "float",
    "small integer": "int",
    "text": "str",
    "type": "str",
    "unsigned integer": "int",
}

SDEF_TYPE_MAP: Final[dict[str, str]] = {
    "date": "sdef_types.Date",
    "file": "sdef_types.File",
    "location specifier": "sdef_types.LocationSpecifier",
    "point": "sdef_types.Point",
    "record": "sdef_types.Record",
    "rectangle": "sdef_types.Rectangle",
    "specifier": "sdef_types.Specifier",
}

SDEF_TEXT_SANITIZE_TABLE: Final[dict[int, str]] = str.maketrans({
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2026": "...",
    "\u2013": "-",
    "\u2014": "-",
    "\u00a0": " ",
})

RESERVED_NAMES: Final[set[str]] = {
    *keyword.kwlist,
    *dir(builtins),
    "self",
}


@dataclass(frozen=True, slots=True)
class NamedDefinition:
    module_name: str
    python_name: str
    code: str | None


@dataclass(frozen=True, slots=True)
class LookupTables:
    suite_by_name: dict[str, Suite]
    command_by_name: dict[str, Command]
    class_by_name: dict[str, NamedDefinition]
    enum_by_name: dict[str, NamedDefinition]
    value_type_by_name: dict[str, NamedDefinition]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate OpenMAC suite modules from SDEF XML.")
    parser.add_argument(
        "--app",
        choices=("chrome", "finder", "all"),
        default="all",
        help="App to generate suites for (default: all).",
    )
    return parser.parse_args()


def sanitize_text(value: str) -> str:
    return value.translate(SDEF_TEXT_SANITIZE_TABLE).replace("\r\n", "\n").replace("\r", "\n")


def sanitize_optional_text(value: str | None) -> str | None:
    return sanitize_text(value) if value is not None else None


def normalize_name(value: str) -> str:
    return " ".join(sanitize_text(value).strip().split()).casefold()


def to_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    if value == "yes":
        return True
    if value == "no":
        return False
    msg = f"Unsupported yes/no value: {value!r}"
    raise ValueError(msg)


def strip_trailing_suite(name: str) -> str:
    return re.sub(r"\s+suite$", "", name, flags=re.IGNORECASE).strip()


def snake_case(name: str) -> str:
    sanitized = sanitize_text(name)
    with_boundaries = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", sanitized)
    compact = re.sub(r"[^A-Za-z0-9]+", "_", with_boundaries)
    collapsed = re.sub(r"_+", "_", compact).strip("_").lower()
    if not collapsed:
        collapsed = "value"
    if collapsed[0].isdigit():
        collapsed = f"value_{collapsed}"
    return collapsed


def pascal_case(name: str) -> str:
    words = [word for word in re.split(r"[^A-Za-z0-9]+", sanitize_text(name)) if word]
    if not words:
        return "Generated"

    parts: list[str] = []
    for word in words:
        part = word.capitalize() if word.isupper() else word[:1].upper() + word[1:]
        parts.append(part)

    joined = "".join(parts)
    if joined[0].isdigit():
        return f"Value{joined}"
    return joined


def ensure_identifier(name: str) -> str:
    identifier = snake_case(name)
    if identifier in RESERVED_NAMES:
        return f"{identifier}_"
    return identifier


def suite_module_name(suite_name: str) -> str:
    base_name = strip_trailing_suite(suite_name)
    return f"{snake_case(base_name)}_suite"


def suite_class_name(suite_name: str) -> str:
    class_name = pascal_case(suite_name)
    if not class_name.endswith("Suite"):
        class_name = f"{class_name}Suite"
    return class_name


def class_name(sdef_name: str) -> str:
    return pascal_case(sdef_name)


def command_method_name(command_name: str) -> str:
    return ensure_identifier(command_name)


def command_class_name(command_name: str) -> str:
    class_name_value = pascal_case(command_name)
    if not class_name_value.endswith("Command"):
        class_name_value = f"{class_name_value}Command"
    return class_name_value


def tuple_expression(expressions: list[str]) -> str:
    if not expressions:
        return "()"
    if len(expressions) == 1:
        return f"({expressions[0]},)"
    return f"({', '.join(expressions)},)"


def render_py(value: object) -> str:
    if value is None:
        return "None"
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, int | float):
        return repr(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=True)
    if isinstance(value, tuple):
        items = [render_py(item) for item in value]
        return tuple_expression(items)
    if isinstance(value, list):
        list_items = ", ".join(render_py(item) for item in value)
        return f"[{list_items}]"
    if isinstance(value, dict):
        parts = [
            f"{render_py(str(key))}: {render_py(value[key])}" for key in sorted(value, key=str)
        ]
        return "{" + ", ".join(parts) + "}"
    msg = f"Unsupported literal value for rendering: {value!r}"
    raise TypeError(msg)


def sanitize_data(value: object) -> object:
    if isinstance(value, str):
        return sanitize_text(value)
    if isinstance(value, list):
        return [sanitize_data(item) for item in value]
    if isinstance(value, tuple):
        return tuple(sanitize_data(item) for item in value)
    if isinstance(value, dict):
        return {str(key): sanitize_data(item) for key, item in value.items()}
    return value


def serialize_models(models: list[BaseModel]) -> list[dict[str, object]]:
    serialized: list[dict[str, object]] = []
    for model in models:
        dumped = model.model_dump(by_alias=True, exclude_none=True)
        dumped_dict = cast("dict[str, object]", dumped)
        serialized.append(cast("dict[str, object]", sanitize_data(dumped_dict)))
    return serialized


def non_empty_dict(data: dict[str, object]) -> dict[str, object] | None:
    return data or None


def build_docstring(description: str | None, extras: dict[str, object] | None = None) -> str:
    sanitized_description = sanitize_optional_text(description)
    text = sanitized_description or "Generated from SDEF."
    if extras:
        text = f"{text}\n\nSDEF extras: {json.dumps(extras, ensure_ascii=True, sort_keys=True)}"
    return text


def first_type_element(elements: list[TypeElement]) -> TypeElement | None:
    for element in elements:
        if element.type:
            return element
    return None


def resolve_base_type(
    raw_type: str | None,
    current_suite_module: str,
    lookups: LookupTables,
) -> str:
    if raw_type is None:
        return "object"

    normalized = normalize_name(raw_type)
    if normalized in PRIMITIVE_TYPE_MAP:
        return PRIMITIVE_TYPE_MAP[normalized]
    if normalized in SDEF_TYPE_MAP:
        return SDEF_TYPE_MAP[normalized]

    for definitions in (lookups.class_by_name, lookups.enum_by_name, lookups.value_type_by_name):
        named_definition = definitions.get(normalized)
        if named_definition is None:
            continue
        if named_definition.module_name == current_suite_module:
            return named_definition.python_name
        return "sdef_types.Specifier"

    if normalized.endswith("specifier"):
        return "sdef_types.Specifier"

    return "object"


def resolve_annotation(
    raw_type: str | None,
    type_elements: list[TypeElement],
    current_suite_module: str,
    lookups: LookupTables,
) -> str:
    selected_type = raw_type
    list_type = False

    selected_element = first_type_element(type_elements)
    if selected_element is not None:
        selected_type = selected_element.type
        list_type = selected_element.list == "yes"

    base_type = resolve_base_type(selected_type, current_suite_module, lookups)
    if list_type:
        return f"list[{base_type}]"
    return base_type


def unique_name(name: str, in_use: set[str]) -> str:
    if name not in in_use:
        in_use.add(name)
        return name

    index = 2
    while True:
        candidate = f"{name}_{index}"
        if candidate not in in_use:
            in_use.add(candidate)
            return candidate
        index += 1


def build_lookup_tables(dictionary: Dictionary) -> LookupTables:
    suite_by_name: dict[str, Suite] = {}
    command_by_name: dict[str, Command] = {}
    class_by_name: dict[str, NamedDefinition] = {}
    enum_by_name: dict[str, NamedDefinition] = {}
    value_type_by_name: dict[str, NamedDefinition] = {}

    for suite in dictionary.suites:
        if suite.name is None:
            continue
        suite_key = normalize_name(suite.name)
        existing_suite = suite_by_name.get(suite_key)
        if existing_suite is not None and existing_suite.code != suite.code:
            msg = f"Suite name collision for {suite.name!r} with different codes."
            raise ValueError(msg)
        suite_by_name[suite_key] = suite

        module_name = suite_module_name(suite.name)
        for command in suite.commands:
            if command.name is None:
                continue
            command_key = normalize_name(command.name)
            existing_command = command_by_name.get(command_key)
            if existing_command is not None and existing_command.code != command.code:
                msg = f"Command name collision for {command.name!r} with different codes."
                raise ValueError(msg)
            command_by_name[command_key] = command

        for class_definition in suite.classes:
            if class_definition.name is None:
                continue
            class_key = normalize_name(class_definition.name)
            existing_class = class_by_name.get(class_key)
            if existing_class is not None and existing_class.code != class_definition.code:
                msg = f"Class name collision for {class_definition.name!r} with different codes."
                raise ValueError(msg)
            class_by_name[class_key] = NamedDefinition(
                module_name=module_name,
                python_name=class_name(class_definition.name),
                code=class_definition.code,
            )

        for enumeration in suite.enumerations:
            if enumeration.name is None:
                continue
            enum_key = normalize_name(enumeration.name)
            existing_enum = enum_by_name.get(enum_key)
            if existing_enum is not None and existing_enum.code != enumeration.code:
                msg = f"Enumeration name collision for {enumeration.name!r} with different codes."
                raise ValueError(msg)
            enum_by_name[enum_key] = NamedDefinition(
                module_name=module_name,
                python_name=class_name(enumeration.name),
                code=enumeration.code,
            )

        for value_type in suite.value_types:
            if value_type.name is None:
                continue
            value_type_key = normalize_name(value_type.name)
            existing_value_type = value_type_by_name.get(value_type_key)
            if existing_value_type is not None and existing_value_type.code != value_type.code:
                msg = f"Value type name collision for {value_type.name!r} with different codes."
                raise ValueError(msg)
            value_type_by_name[value_type_key] = NamedDefinition(
                module_name=module_name,
                python_name=class_name(value_type.name),
                code=value_type.code,
            )

    return LookupTables(
        suite_by_name=suite_by_name,
        command_by_name=command_by_name,
        class_by_name=class_by_name,
        enum_by_name=enum_by_name,
        value_type_by_name=value_type_by_name,
    )


def access_group_tuples_from_command(command: Command) -> tuple[tuple[str | None, str | None], ...]:
    groups: list[tuple[str | None, str | None]] = []
    for access_group in command.access_groups:
        groups.append((sanitize_optional_text(access_group.identifier), access_group.access))
    for direct_parameter in command.direct_parameters:
        for access_group in direct_parameter.access_groups:
            groups.append((sanitize_optional_text(access_group.identifier), access_group.access))
    return tuple(groups)


def command_direct_parameter_type(command: Command) -> str | None:
    if not command.direct_parameters:
        return None
    direct_parameter = command.direct_parameters[0]
    selected_type = direct_parameter.type
    selected_element = first_type_element(direct_parameter.type_elements)
    if selected_element is not None:
        selected_type = selected_element.type
    return sanitize_optional_text(selected_type)


def parameter_meta_expr(parameter: Parameter) -> str:
    parameter_name = sanitize_optional_text(parameter.name) or "parameter"
    return (
        "sdef_meta.ParameterMeta("
        f"name={render_py(parameter_name)}, "
        f"code={render_py(sanitize_optional_text(parameter.code))}, "
        f"type={render_py(sanitize_optional_text(parameter.type))}, "
        f"description={render_py(sanitize_optional_text(parameter.description))}, "
        f"optional={render_py(to_bool(parameter.optional))}, "
        f"hidden={render_py(to_bool(parameter.hidden))}, "
        f"requires_access={render_py(parameter.requires_access)}"
        ")"
    )


def result_meta_expr(result: Result) -> str:
    return (
        "sdef_meta.ResultMeta("
        f"type={render_py(sanitize_optional_text(result.type))}, "
        f"description={render_py(sanitize_optional_text(result.description))}, "
        f"optional={render_py(to_bool(result.optional))}"
        ")"
    )


def property_meta_expr(property_: Property) -> str:
    property_name = sanitize_optional_text(property_.name) or "property"
    return (
        "sdef_meta.PropertyMeta("
        f"name={render_py(property_name)}, "
        f"code={render_py(sanitize_optional_text(property_.code))}, "
        f"type={render_py(sanitize_optional_text(property_.type))}, "
        f"description={render_py(sanitize_optional_text(property_.description))}, "
        f"hidden={render_py(to_bool(property_.hidden))}, "
        f"access={render_py(property_.access)}, "
        f"in_properties={render_py(to_bool(property_.in_properties))}"
        ")"
    )


def element_meta_expr(element: Element) -> str:
    element_type = sanitize_optional_text(element.type) or "element"
    return (
        "sdef_meta.ElementMeta("
        f"type={render_py(element_type)}, "
        f"description={render_py(sanitize_optional_text(element.description))}, "
        f"hidden={render_py(to_bool(element.hidden))}, "
        f"access={render_py(element.access)}"
        ")"
    )


def class_meta_expr(class_definition: Class) -> str:
    class_name_value = sanitize_optional_text(class_definition.name) or "class"
    responds_to_value = tuple(
        (
            sanitize_text(responds_to.command),
            to_bool(responds_to.hidden),
        )
        for responds_to in class_definition.responds_tos
    )
    properties_expr = tuple_expression([
        property_meta_expr(property_) for property_ in class_definition.properties
    ])
    elements_expr = tuple_expression([
        element_meta_expr(element) for element in class_definition.elements
    ])
    return (
        "sdef_meta.ClassMeta("
        f"name={render_py(class_name_value)}, "
        f"code={render_py(sanitize_optional_text(class_definition.code))}, "
        f"description={render_py(sanitize_optional_text(class_definition.description))}, "
        f"hidden={render_py(to_bool(class_definition.hidden))}, "
        f"inherits={render_py(sanitize_optional_text(class_definition.inherits))}, "
        f"plural={render_py(sanitize_optional_text(class_definition.plural))}, "
        f"id={render_py(sanitize_optional_text(class_definition.id))}, "
        f"properties={properties_expr}, "
        f"elements={elements_expr}, "
        f"responds_to={render_py(responds_to_value)}"
        ")"
    )


def class_extension_meta_expr(class_extension: ClassExtension) -> str:
    class_name_value = sanitize_optional_text(class_extension.extends) or "class"
    responds_to_value = tuple(
        (
            sanitize_text(responds_to.command),
            to_bool(responds_to.hidden),
        )
        for responds_to in class_extension.responds_tos
    )
    properties_expr = tuple_expression([
        property_meta_expr(property_) for property_ in class_extension.properties
    ])
    elements_expr = tuple_expression([
        element_meta_expr(element) for element in class_extension.elements
    ])
    return (
        "sdef_meta.ClassMeta("
        f"name={render_py(class_name_value)}, "
        "code=None, "
        f"description={render_py(sanitize_optional_text(class_extension.description))}, "
        f"hidden={render_py(to_bool(class_extension.hidden))}, "
        f"inherits={render_py(sanitize_optional_text(class_extension.extends))}, "
        "plural=None, "
        "id=None, "
        f"properties={properties_expr}, "
        f"elements={elements_expr}, "
        f"responds_to={render_py(responds_to_value)}"
        ")"
    )


def command_meta_expr(command: Command) -> str:
    command_name_value = sanitize_optional_text(command.name) or "command"
    parameter_expr = tuple_expression([
        parameter_meta_expr(parameter) for parameter in command.parameters
    ])
    result_expr = tuple_expression([result_meta_expr(result) for result in command.results])
    access_groups = access_group_tuples_from_command(command)
    return (
        "sdef_meta.CommandMeta("
        f"name={render_py(command_name_value)}, "
        f"code={render_py(sanitize_optional_text(command.code))}, "
        f"description={render_py(sanitize_optional_text(command.description))}, "
        f"hidden={render_py(to_bool(command.hidden))}, "
        f"direct_parameter_type={render_py(command_direct_parameter_type(command))}, "
        f"parameters={parameter_expr}, "
        f"results={result_expr}, "
        f"access_groups={render_py(access_groups)}"
        ")"
    )


def suite_meta_expr(suite: Suite) -> str:
    suite_name_value = sanitize_optional_text(suite.name) or "Suite"
    return (
        "sdef_meta.SuiteMeta("
        f"name={render_py(suite_name_value)}, "
        f"code={render_py(sanitize_optional_text(suite.code))}, "
        f"description={render_py(sanitize_optional_text(suite.description))}, "
        f"hidden={render_py(to_bool(suite.hidden))}"
        ")"
    )


def enumeration_meta_expr(enumeration: Enumeration) -> str:
    enumeration_name = sanitize_optional_text(enumeration.name) or "Enumeration"
    enumerator_expr = tuple_expression([
        enumerator_meta_expr(item) for item in enumeration.enumerators
    ])
    return (
        "sdef_meta.EnumerationMeta("
        f"name={render_py(enumeration_name)}, "
        f"code={render_py(sanitize_optional_text(enumeration.code))}, "
        f"description={render_py(sanitize_optional_text(enumeration.description))}, "
        f"hidden={render_py(to_bool(enumeration.hidden))}, "
        f"enumerators={enumerator_expr}"
        ")"
    )


def enumerator_meta_expr(enumerator: Enumerator) -> str:
    enumerator_name = sanitize_optional_text(enumerator.name) or "Enumerator"
    return (
        "sdef_meta.EnumeratorMeta("
        f"name={render_py(enumerator_name)}, "
        f"code={render_py(sanitize_optional_text(enumerator.code))}, "
        f"description={render_py(sanitize_optional_text(enumerator.description))}"
        ")"
    )


def value_type_meta_expr(value_type: ValueType) -> str:
    value_type_name = sanitize_optional_text(value_type.name) or "ValueType"
    return (
        "sdef_meta.ValueTypeMeta("
        f"name={render_py(value_type_name)}, "
        f"code={render_py(sanitize_optional_text(value_type.code))}, "
        f"description={render_py(sanitize_optional_text(value_type.description))}"
        ")"
    )


def command_extras(command: Command) -> dict[str, object] | None:
    extras: dict[str, object] = {}
    direct_parameter_payload = serialize_models([
        cast("BaseModel", direct_parameter) for direct_parameter in command.direct_parameters
    ])
    parameter_payload = serialize_models([
        cast("BaseModel", parameter) for parameter in command.parameters
    ])
    result_payload = serialize_models([cast("BaseModel", result) for result in command.results])
    if direct_parameter_payload:
        extras["direct_parameters"] = direct_parameter_payload
    if parameter_payload:
        extras["parameters"] = parameter_payload
    if result_payload:
        extras["results"] = result_payload
    if command.cocoas:
        extras["cocoas"] = serialize_models([cast("BaseModel", cocoa) for cocoa in command.cocoas])
    if command.documentation:
        extras["documentation"] = serialize_models([
            cast("BaseModel", documentation) for documentation in command.documentation
        ])
    return non_empty_dict(extras)


def property_field_extra(property_: Property) -> dict[str, object] | None:
    extras: dict[str, object] = {}
    if property_.type_elements:
        extras["type_elements"] = serialize_models([
            cast("BaseModel", type_element) for type_element in property_.type_elements
        ])
    if property_.cocoas:
        extras["cocoas"] = serialize_models([
            cast("BaseModel", cocoa) for cocoa in property_.cocoas
        ])
    if property_.documentation:
        extras["documentation"] = serialize_models([
            cast("BaseModel", documentation) for documentation in property_.documentation
        ])
    if property_.synonyms:
        extras["synonyms"] = serialize_models([
            cast("BaseModel", synonym) for synonym in property_.synonyms
        ])
    return non_empty_dict(extras)


def class_extras(class_definition: Class) -> dict[str, object] | None:
    extras: dict[str, object] = {}
    if class_definition.cocoas:
        extras["cocoas"] = serialize_models([
            cast("BaseModel", cocoa) for cocoa in class_definition.cocoas
        ])
    if class_definition.access_groups:
        extras["access_groups"] = serialize_models([
            cast("BaseModel", access_group) for access_group in class_definition.access_groups
        ])
    if class_definition.type_elements:
        extras["type_elements"] = serialize_models([
            cast("BaseModel", type_element) for type_element in class_definition.type_elements
        ])
    if class_definition.documentation:
        extras["documentation"] = serialize_models([
            cast("BaseModel", documentation) for documentation in class_definition.documentation
        ])
    if class_definition.synonyms:
        extras["synonyms"] = serialize_models([
            cast("BaseModel", synonym) for synonym in class_definition.synonyms
        ])
    return non_empty_dict(extras)


def class_extension_extras(class_extension: ClassExtension) -> dict[str, object] | None:
    extras: dict[str, object] = {}
    if class_extension.cocoas:
        extras["cocoas"] = serialize_models([
            cast("BaseModel", cocoa) for cocoa in class_extension.cocoas
        ])
    if class_extension.synonyms:
        extras["synonyms"] = serialize_models([
            cast("BaseModel", synonym) for synonym in class_extension.synonyms
        ])
    return non_empty_dict(extras)


def suite_extras(suite: Suite) -> dict[str, object] | None:
    extras: dict[str, object] = {}
    if suite.access_groups:
        extras["access_groups"] = serialize_models([
            cast("BaseModel", access_group) for access_group in suite.access_groups
        ])
    if suite.cocoas:
        extras["cocoas"] = serialize_models([cast("BaseModel", cocoa) for cocoa in suite.cocoas])
    if suite.xi_includes:
        extras["x_includes"] = serialize_models([
            cast("BaseModel", x_include) for x_include in suite.xi_includes
        ])
    return non_empty_dict(extras)


def enumeration_extras(enumeration: Enumeration) -> dict[str, object] | None:
    extras: dict[str, object] = {}
    enumerator_extras: dict[str, dict[str, object]] = {}
    for enumerator in enumeration.enumerators:
        payload: dict[str, object] = {}
        if enumerator.cocoas:
            payload["cocoas"] = serialize_models([
                cast("BaseModel", cocoa) for cocoa in enumerator.cocoas
            ])
        if enumerator.synonyms:
            payload["synonyms"] = serialize_models([
                cast("BaseModel", synonym) for synonym in enumerator.synonyms
            ])
        if payload:
            enumerator_key = sanitize_optional_text(enumerator.name) or "enumerator"
            enumerator_extras[enumerator_key] = payload

    if enumerator_extras:
        extras["enumerator_extras"] = enumerator_extras

    return non_empty_dict(extras)


def value_type_extras(value_type: ValueType) -> dict[str, object] | None:
    extras: dict[str, object] = {}
    if value_type.cocoas:
        extras["cocoas"] = serialize_models([
            cast("BaseModel", cocoa) for cocoa in value_type.cocoas
        ])
    if value_type.synonyms:
        extras["synonyms"] = serialize_models([
            cast("BaseModel", synonym) for synonym in value_type.synonyms
        ])
    return non_empty_dict(extras)


def command_field_line(
    *,
    name: str,
    annotation: str,
    description: str | None,
    optional: bool,
    alias: str | None = None,
    schema_extra: dict[str, object] | None = None,
) -> str:
    field_annotation = annotation
    kwargs: list[str] = []
    if optional:
        field_annotation = f"{annotation} | None"
        kwargs.append("default=None")
    else:
        kwargs.append("...")
    if alias is not None:
        kwargs.append(f"alias={render_py(alias)}")
    kwargs.append(f"description={render_py(description)}")
    if schema_extra:
        kwargs.append(f"json_schema_extra={render_py(schema_extra)}")
    return f"    {name}: {field_annotation} = Field({', '.join(kwargs)})"


def direct_parameter_field_extra(direct_parameter: DirectParameter) -> dict[str, object] | None:
    extras: dict[str, object] = {}
    if direct_parameter.type_elements:
        extras["type_elements"] = serialize_models([
            cast("BaseModel", type_element) for type_element in direct_parameter.type_elements
        ])
    if direct_parameter.access_groups:
        extras["access_groups"] = serialize_models([
            cast("BaseModel", access_group) for access_group in direct_parameter.access_groups
        ])
    return non_empty_dict(extras)


def parameter_field_extra(parameter: Parameter) -> dict[str, object] | None:
    extras: dict[str, object] = {}
    if parameter.type_elements:
        extras["type_elements"] = serialize_models([
            cast("BaseModel", type_element) for type_element in parameter.type_elements
        ])
    if parameter.cocoas:
        extras["cocoas"] = serialize_models([
            cast("BaseModel", cocoa) for cocoa in parameter.cocoas
        ])
    return non_empty_dict(extras)


def first_direct_parameter(command: Command) -> DirectParameter | None:
    if command.direct_parameters:
        return command.direct_parameters[0]
    return None


def command_return_annotation(command: Command, module_name: str, lookups: LookupTables) -> str:
    if not command.results:
        return "None"
    if len(command.results) > 1:
        return "object"
    result = command.results[0]
    annotation = resolve_annotation(result.type, result.type_elements, module_name, lookups)
    if result.optional == "yes":
        return f"{annotation} | None"
    return annotation


def command_class_lines(
    command: Command,
    module_name: str,
    lookups: LookupTables,
    command_class: str,
) -> list[str]:
    lines = [f"class {command_class}(SDEFCommand):"]
    lines.append(f"    {render_py(build_docstring(command.description, command_extras(command)))}")
    lines.append(f"    SDEF_META: ClassVar[sdef_meta.CommandMeta] = {command_meta_expr(command)}")

    in_use_names: set[str] = set()
    direct_parameter = first_direct_parameter(command)
    if direct_parameter is not None:
        direct_annotation = resolve_annotation(
            direct_parameter.type,
            direct_parameter.type_elements,
            module_name,
            lookups,
        )
        lines.append(
            command_field_line(
                name="direct_parameter",
                annotation=direct_annotation,
                description=sanitize_optional_text(direct_parameter.description),
                optional=direct_parameter.optional == "yes",
                schema_extra=direct_parameter_field_extra(direct_parameter),
            ),
        )
        in_use_names.add("direct_parameter")

    for parameter in command.parameters:
        raw_name = parameter.name or "parameter"
        parameter_name = unique_name(ensure_identifier(raw_name), in_use_names)
        parameter_annotation = resolve_annotation(
            parameter.type,
            parameter.type_elements,
            module_name,
            lookups,
        )
        lines.append(
            command_field_line(
                name=parameter_name,
                annotation=parameter_annotation,
                description=sanitize_optional_text(parameter.description),
                optional=parameter.optional == "yes",
                alias=sanitize_text(raw_name),
                schema_extra=parameter_field_extra(parameter),
            ),
        )

    lines.append("")
    return_annotation = command_return_annotation(command, module_name, lookups)
    lines.append(f"    def __call__(self) -> {return_annotation}:")
    lines.append("        raise NotImplementedError")
    lines.append("")
    return lines


def field_line(
    property_: Property,
    module_name: str,
    lookups: LookupTables,
    in_use_names: set[str],
) -> str:
    raw_name = property_.name or "property"
    python_name = unique_name(ensure_identifier(raw_name), in_use_names)
    annotation = resolve_annotation(property_.type, property_.type_elements, module_name, lookups)
    kwargs: list[str] = ["..."]
    kwargs.append(f"alias={render_py(sanitize_text(raw_name))}")
    kwargs.append(f"description={render_py(sanitize_optional_text(property_.description))}")
    schema_extra = property_field_extra(property_)
    if schema_extra:
        kwargs.append(f"json_schema_extra={render_py(schema_extra)}")
    return f"    {python_name}: {annotation} = Field({', '.join(kwargs)})"


def class_base_name(
    class_definition: Class,
    module_name: str,
    lookups: LookupTables,
) -> str:
    if class_definition.inherits is None:
        return "SDEFClass"
    inherited_name = normalize_name(class_definition.inherits)
    inherited_definition = lookups.class_by_name.get(inherited_name)
    if inherited_definition is None:
        return "SDEFClass"
    if inherited_definition.module_name != module_name:
        return "SDEFClass"
    return inherited_definition.python_name


def class_lines(
    class_definition: Class,
    module_name: str,
    lookups: LookupTables,
) -> list[str]:
    sdef_class_name = class_definition.name or "class"
    python_class_name = class_name(sdef_class_name)
    base_class_name = class_base_name(class_definition, module_name, lookups)
    lines = [f"class {python_class_name}({base_class_name}):"]
    lines.append(
        f"    {render_py(build_docstring(class_definition.description, class_extras(class_definition)))}",
    )
    lines.append(
        f"    SDEF_META: ClassVar[sdef_meta.ClassMeta] = {class_meta_expr(class_definition)}",
    )
    in_use_names: set[str] = set()
    for property_ in class_definition.properties:
        lines.append(field_line(property_, module_name, lookups, in_use_names))
    if not class_definition.properties:
        lines.append("    pass")
    lines.append("")
    return lines


def class_extension_lines(
    class_extension: ClassExtension,
    module_name: str,
    lookups: LookupTables,
) -> tuple[list[str], str | None]:
    if class_extension.extends is None:
        return ([], None)

    python_class_name = class_name(class_extension.extends)
    parent_class_name = "SDEFClass"
    import_module: str | None = None
    parent_definition = lookups.class_by_name.get(normalize_name(class_extension.extends))
    if parent_definition is not None:
        parent_class_name = parent_definition.python_name
        if parent_definition.module_name != module_name:
            import_module = parent_definition.module_name
            parent_class_name = (
                f"{parent_definition.module_name}_module.{parent_definition.python_name}"
            )

    lines = [f"class {python_class_name}({parent_class_name}):"]
    lines.append(
        f"    {render_py(build_docstring(class_extension.description, class_extension_extras(class_extension)))}",
    )
    lines.append(
        f"    SDEF_META: ClassVar[sdef_meta.ClassMeta] = {class_extension_meta_expr(class_extension)}",
    )

    in_use_names: set[str] = set()
    for property_ in class_extension.properties:
        lines.append(field_line(property_, module_name, lookups, in_use_names))
    if not class_extension.properties:
        lines.append("    pass")
    lines.append("")
    return (lines, import_module)


def enum_member_name(name: str, in_use_names: set[str]) -> str:
    uppercase = snake_case(name).upper()
    if not uppercase:
        uppercase = "VALUE"
    if uppercase[0].isdigit():
        uppercase = f"VALUE_{uppercase}"
    if uppercase in RESERVED_NAMES:
        uppercase = f"{uppercase}_"
    return unique_name(uppercase, in_use_names)


def enumeration_lines(enumeration: Enumeration) -> list[str]:
    enumeration_name = class_name(enumeration.name or "Enumeration")
    lines = [f"class {enumeration_name}(str, Enum):"]
    lines.append(
        f"    {render_py(build_docstring(enumeration.description, enumeration_extras(enumeration)))}",
    )
    in_use_names: set[str] = set()
    if not enumeration.enumerators:
        lines.append("    pass")
    else:
        for enumerator in enumeration.enumerators:
            raw_name = enumerator.name or "enumerator"
            member_name = enum_member_name(raw_name, in_use_names)
            member_value = sanitize_optional_text(enumerator.code) or sanitize_text(raw_name)
            lines.append(f"    {member_name} = {render_py(member_value)}")
    lines.append("")
    constant_name = f"{snake_case(enumeration_name).upper()}_ENUMERATION_META"
    lines.append(
        f"{constant_name}: Final[sdef_meta.EnumerationMeta] = {enumeration_meta_expr(enumeration)}",
    )
    lines.append("")
    return lines


def value_type_lines(value_type: ValueType) -> list[str]:
    value_type_name = class_name(value_type.name or "ValueType")
    constant_name = f"{snake_case(value_type_name).upper()}_VALUE_TYPE_META"
    value_docstring = build_docstring(value_type.description, value_type_extras(value_type))
    lines = [
        f"class {value_type_name}:",
        f"    {render_py(value_docstring)}",
        "    pass",
        "",
    ]
    lines.append(
        f"{constant_name}: Final[sdef_meta.ValueTypeMeta] = {value_type_meta_expr(value_type)}",
    )
    lines.append("")
    return lines


def generate_suite_module(
    target: AppTarget,
    suite: Suite,
    lookups: LookupTables,
) -> tuple[str, str]:
    suite_name_value = suite.name or "Suite"
    module_name = suite_module_name(suite_name_value)
    suite_class = suite_class_name(suite_name_value)

    needs_command_fields = any(
        command.direct_parameters or command.parameters for command in suite.commands
    )
    needs_field = (
        any(class_definition.properties for class_definition in suite.classes)
        or any(class_extension.properties for class_extension in suite.class_extensions)
        or needs_command_fields
    )
    needs_enum = bool(suite.enumerations)

    cross_module_imports: set[str] = set()
    class_extension_blocks: list[list[str]] = []
    extension_names: set[str] = set()
    for class_extension in suite.class_extensions:
        extension_lines, import_module = class_extension_lines(
            class_extension,
            module_name,
            lookups,
        )
        if extension_lines:
            extension_name_match = re.match(r"^class ([A-Za-z0-9_]+)\(", extension_lines[0])
            if extension_name_match:
                extension_name = extension_name_match.group(1)
                if extension_name in extension_names:
                    msg = f"Duplicate class-extension output name {extension_name!r} in suite {suite_name_value!r}"
                    raise ValueError(msg)
                extension_names.add(extension_name)
            class_extension_blocks.append(extension_lines)
        if import_module is not None:
            cross_module_imports.add(import_module)

    command_class_names: list[str] = []
    command_class_blocks: list[list[str]] = []
    in_use_command_class_names: set[str] = set()
    for command in suite.commands:
        command_name_value = command.name or "command"
        generated_command_class_name = unique_name(
            command_class_name(command_name_value),
            in_use_command_class_names,
        )
        command_class_names.append(generated_command_class_name)
        command_class_blocks.append(
            command_class_lines(
                command,
                module_name,
                lookups,
                generated_command_class_name,
            ),
        )

    lines: list[str] = [
        "from __future__ import annotations",
        "# ruff: noqa: D301, D400, D415, PIE796",
        "",
        f"# Generated by {SCRIPT_PATH.relative_to(ROOT)}. Do not edit manually.",
        "",
        "from typing import ClassVar, Final",
    ]
    if needs_enum:
        lines.append("from enum import Enum")
    if needs_field:
        lines.append("from pydantic import Field")
    lines.extend([
        "",
        "import openmac._internal.sdef as sdef_types",
        "import openmac._internal.sdef_meta as sdef_meta",
        "from openmac._internal.models import SDEFClass, SDEFCommand",
    ])

    for imported_module in sorted(cross_module_imports):
        lines.append(
            f"import openmac.{target.app}.sdef.suites.{imported_module} as {imported_module}_module",
        )

    lines.extend(["", f"SUITE_META: Final[sdef_meta.SuiteMeta] = {suite_meta_expr(suite)}", ""])

    for class_definition in suite.classes:
        lines.extend(class_lines(class_definition, module_name, lookups))

    for block in class_extension_blocks:
        lines.extend(block)

    for enumeration in suite.enumerations:
        lines.extend(enumeration_lines(enumeration))

    for value_type in suite.value_types:
        lines.extend(value_type_lines(value_type))

    for command_class_block in command_class_blocks:
        lines.extend(command_class_block)

    lines.append(f"class {suite_class}:")
    lines.append(f"    {render_py(build_docstring(suite.description, suite_extras(suite)))}")
    command_expr = tuple_expression(command_class_names)
    lines.append(f"    COMMANDS: ClassVar[tuple[type[SDEFCommand], ...]] = {command_expr}")
    lines.append("")

    exported_names: list[str] = []
    for class_definition in suite.classes:
        if class_definition.name is not None:
            exported_names.append(class_name(class_definition.name))
    for class_extension in suite.class_extensions:
        if class_extension.extends is not None:
            exported_names.append(class_name(class_extension.extends))
    for enumeration in suite.enumerations:
        if enumeration.name is not None:
            exported_names.append(class_name(enumeration.name))
    for value_type in suite.value_types:
        if value_type.name is not None:
            exported_names.append(class_name(value_type.name))
    exported_names.extend(command_class_names)
    exported_names.append(suite_class)

    deduped_exports: list[str] = []
    seen_exports: set[str] = set()
    for export_name in exported_names:
        if export_name in seen_exports:
            continue
        seen_exports.add(export_name)
        deduped_exports.append(export_name)
    lines.append(f"__all__ = {render_py(deduped_exports)}")
    lines.append("")

    module_text = "\n".join(lines)
    return (module_name, module_text)


def generate_init_module(target: AppTarget, suites: list[Suite]) -> str:
    suite_exports: list[tuple[str, str]] = []
    for suite in suites:
        if suite.name is None:
            continue
        suite_exports.append((suite_module_name(suite.name), suite_class_name(suite.name)))

    lines = [
        "from __future__ import annotations",
        "",
        f"# Generated by {SCRIPT_PATH.relative_to(ROOT)}. Do not edit manually.",
        "",
    ]
    for module_name, class_name_value in suite_exports:
        lines.append(f"from {target.package}.{module_name} import {class_name_value}")
    lines.append("")
    lines.append(
        f"__all__ = {render_py([class_name_value for _, class_name_value in suite_exports])}",
    )
    lines.append("")
    return "\n".join(lines)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def generate_for_target(target: AppTarget) -> None:
    dictionary = load_sdef(target.sdef_path)
    lookups = build_lookup_tables(dictionary)
    generated_modules: dict[str, str] = {}
    suite_ordered_modules: list[str] = []
    suite_by_module: dict[str, Suite] = {}

    for suite in dictionary.suites:
        if suite.name is None:
            continue
        module_name, module_content = generate_suite_module(target, suite, lookups)
        suite_ordered_modules.append(module_name)
        suite_by_module[module_name] = suite
        generated_modules[module_name] = module_content

    expected_files = {f"{module_name}.py" for module_name in suite_ordered_modules}
    for existing_file in target.suites_dir.glob("*_suite.py"):
        if existing_file.name not in expected_files:
            existing_file.unlink()

    for module_name in suite_ordered_modules:
        write_text(target.suites_dir / f"{module_name}.py", generated_modules[module_name])

    suite_list = [suite_by_module[module_name] for module_name in suite_ordered_modules]
    write_text(target.suites_dir / "__init__.py", generate_init_module(target, suite_list))


def selected_targets(app: str) -> list[AppTarget]:
    if app == "all":
        return [APP_TARGETS["chrome"], APP_TARGETS["finder"]]
    return [APP_TARGETS[app]]


def main() -> None:
    args = parse_args()
    for target in selected_targets(args.app):
        generate_for_target(target)


if __name__ == "__main__":
    main()
