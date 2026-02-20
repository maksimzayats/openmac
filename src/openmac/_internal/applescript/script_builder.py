from __future__ import annotations

from collections.abc import Mapping

from pydantic.fields import FieldInfo

from openmac._internal.applescript.serializer import dumps
from openmac._internal.sdef import SDEFCommand


class AppleScriptSDEFScriptBuilder:
    def __init__(self, command: SDEFCommand[object]) -> None:
        self._command = command
        self._meta = command.SDEF_META
        self._model_fields: Mapping[str, FieldInfo] = command.__class__.model_fields
        self._command_parts: list[str] = []

    def build_script(self) -> str:
        self._command_parts = [self._meta.name]
        self._append_direct_parameter()
        self._append_named_parameters()
        script_lines = [
            f"tell application id {dumps(self._meta.bundle_id)}",
            f"    {' '.join(self._command_parts)}",
            "end tell",
        ]
        return "\n".join(script_lines)

    def _append_direct_parameter(self) -> None:
        command_name = self._meta.name
        has_direct_parameter = self._meta.has_direct_parameter or (
            self._meta.direct_parameter_type is not None
            and "direct_parameter" in self._model_fields
        )
        if not has_direct_parameter:
            return
        if "direct_parameter" not in self._model_fields:
            msg = (
                f"Command {command_name!r} metadata expects direct_parameter, "
                "but the model field is missing."
            )
            raise ValueError(msg)

        direct_parameter_value = self._read_value(
            "direct_parameter",
            f"Command {command_name!r} metadata expects direct_parameter, but the model value is missing.",
        )
        direct_parameter_optional = self._meta.direct_parameter_optional
        if direct_parameter_optional is None:
            direct_parameter_optional = not self._model_fields["direct_parameter"].is_required()
        if direct_parameter_value is None:
            if not direct_parameter_optional:
                msg = f"Command {command_name!r} requires direct_parameter, but value is missing."
                raise ValueError(msg)
            return
        self._command_parts.append(dumps(direct_parameter_value))

    def _append_named_parameters(self) -> None:
        command_name = self._meta.name
        for parameter_meta in self._meta.parameters:
            field_name = parameter_meta.field_name
            if field_name is None:
                msg = (
                    f"Command {command_name!r} parameter {parameter_meta.name!r} is missing "
                    "field_name metadata."
                )
                raise ValueError(msg)
            if field_name not in self._model_fields:
                msg = (
                    f"Command {command_name!r} parameter {parameter_meta.name!r} references "
                    f"unknown model field {field_name!r}."
                )
                raise ValueError(msg)

            parameter_value = self._read_value(
                field_name,
                f"Command {command_name!r} requires parameter {parameter_meta.name!r} (field {field_name!r}), but the model value is missing.",
            )
            if parameter_value is None:
                if parameter_meta.optional is True:
                    continue
                msg = (
                    f"Command {command_name!r} requires parameter {parameter_meta.name!r} "
                    f"(field {field_name!r}), but value is missing."
                )
                raise ValueError(msg)
            self._command_parts.append(f"{parameter_meta.name} {dumps(parameter_value)}")

    def _read_value(self, field_name: str, error_message: str) -> object:
        try:
            return getattr(self._command, field_name)
        except AttributeError as error:
            raise ValueError(error_message) from error
