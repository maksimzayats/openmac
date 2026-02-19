from __future__ import annotations

from collections.abc import Mapping

from openmac._internal.applescript.executor import AppleScriptExecutor
from openmac._internal.applescript.serializer import dumps
from openmac._internal.sdef import SDEFCommand


class AppleScriptSDEFCommandRunner:
    def __init__(self, executor: AppleScriptExecutor) -> None:
        self._executor = executor

    def run(self, command: SDEFCommand) -> str:
        script = self._generate_applescript(command)
        return self._executor.execute(script)

    def _generate_applescript(self, command: SDEFCommand) -> str:
        meta = command.SDEF_META
        command_parts = [meta.name]
        model_fields = command.__class__.model_fields
        self._append_direct_parameter(command, command_parts, model_fields)
        self._append_named_parameters(command, command_parts, model_fields)
        script_lines = [
            f"tell application id {dumps(meta.bundle_id)}",
            f"    {' '.join(command_parts)}",
            "end tell",
        ]
        return "\n".join(script_lines)

    def _append_direct_parameter(
        self,
        command: SDEFCommand,
        command_parts: list[str],
        model_fields: Mapping[str, object],
    ) -> None:
        meta = command.SDEF_META
        command_name = meta.name
        has_direct_parameter = meta.has_direct_parameter or (
            meta.direct_parameter_type is not None and "direct_parameter" in model_fields
        )
        if not has_direct_parameter:
            return
        if "direct_parameter" not in model_fields:
            msg = (
                f"Command {command_name!r} metadata expects direct_parameter, "
                "but the model field is missing."
            )
            raise ValueError(msg)

        direct_parameter_value = self._read_value(
            command,
            "direct_parameter",
            f"Command {command_name!r} metadata expects direct_parameter, but the model value is missing.",
        )
        direct_parameter_optional = meta.direct_parameter_optional
        if direct_parameter_optional is None:
            direct_parameter_optional = not command.__class__.model_fields[
                "direct_parameter"
            ].is_required()
        if direct_parameter_value is None:
            if not direct_parameter_optional:
                msg = f"Command {command_name!r} requires direct_parameter, but value is missing."
                raise ValueError(msg)
            return
        command_parts.append(dumps(direct_parameter_value))

    def _append_named_parameters(
        self,
        command: SDEFCommand,
        command_parts: list[str],
        model_fields: Mapping[str, object],
    ) -> None:
        command_name = command.SDEF_META.name
        for parameter_meta in command.SDEF_META.parameters:
            field_name = parameter_meta.field_name
            if field_name is None:
                msg = (
                    f"Command {command_name!r} parameter {parameter_meta.name!r} is missing "
                    "field_name metadata."
                )
                raise ValueError(msg)
            if field_name not in model_fields:
                msg = (
                    f"Command {command_name!r} parameter {parameter_meta.name!r} references "
                    f"unknown model field {field_name!r}."
                )
                raise ValueError(msg)

            parameter_value = self._read_value(
                command,
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
            command_parts.append(f"{parameter_meta.name} {dumps(parameter_value)}")

    def _read_value(self, command: SDEFCommand, field_name: str, error_message: str) -> object:
        try:
            return getattr(command, field_name)
        except AttributeError as error:
            raise ValueError(error_message) from error
