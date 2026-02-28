from __future__ import annotations

import ast
from abc import ABC, abstractmethod
from typing import Any, cast


class ActionsParser:
    def __init__(self, args: list[str]) -> None:
        self._args = args

    def parse(self) -> list[BaseAction]:
        actions: list[BaseAction] = []
        action_index = 0

        while action_index < len(self._args):
            action = self._args[action_index].strip()
            if not action:
                raise ValueError("Action cannot be empty.")

            if self._is_assignment_token(action):
                raise ValueError(f"Unexpected argument token without method: {action!r}.")

            if self._has_kwargs_tokens_after(action_index):
                method_action, consumed_tokens = self._parse_kwargs_method_action(
                    action=action,
                    action_index=action_index,
                )
                actions.append(method_action)
                action_index += consumed_tokens
                continue

            actions.append(self._parse_action(action))
            action_index += 1

        return actions

    def _is_assignment_token(self, action: str) -> bool:
        if "=" not in action:
            return False

        first_equals = action.find("=")
        first_open_parenthesis = action.find("(")
        if first_open_parenthesis == -1:
            return True

        return first_equals < first_open_parenthesis

    def _has_kwargs_tokens_after(self, action_index: int) -> bool:
        if action_index + 1 >= len(self._args):
            return False

        action = self._args[action_index].strip()
        if not action.isidentifier():
            return False

        next_action = self._args[action_index + 1].strip()
        return self._is_assignment_token(next_action)

    def _parse_kwargs_method_action(
        self,
        action: str,
        action_index: int,
    ) -> tuple[MethodCallAction, int]:
        self._validate_identifier(action=action, kind="method")

        method_kwargs: dict[str, Any] = {}
        consumed_tokens = 1

        for raw_argument in self._args[action_index + 1 :]:
            argument = raw_argument.strip()
            if not argument:
                raise ValueError("Action cannot be empty.")

            if not self._is_assignment_token(argument):
                break

            key, value = self._parse_assignment_argument(argument=argument)
            if key in method_kwargs:
                raise ValueError(
                    f"Duplicate keyword argument {key!r} in action: {action!r}.",
                )

            method_kwargs[key] = value
            consumed_tokens += 1

        return MethodCallAction(method_name=action, method_kwargs=method_kwargs), consumed_tokens

    def _parse_assignment_argument(self, argument: str) -> tuple[str, Any]:
        argument_name, _, raw_argument_value = argument.partition("=")
        if not argument_name:
            raise ValueError(f"Invalid keyword argument syntax: {argument!r}.")

        self._validate_identifier(action=argument_name, kind="keyword argument")

        return argument_name, self._parse_assignment_value(raw_argument_value)

    def _parse_assignment_value(self, raw_argument_value: str) -> Any:
        normalized_value = raw_argument_value.strip()
        if not normalized_value:
            return ""

        lowered_value = normalized_value.lower()
        if lowered_value == "true":
            return True
        if lowered_value == "false":
            return False
        if lowered_value in {"none", "null"}:
            return None

        try:
            return ast.literal_eval(normalized_value)
        except (SyntaxError, TypeError, ValueError):
            return normalized_value

    def _parse_action(self, action: str) -> BaseAction:
        if "(" not in action and ")" not in action:
            self._validate_identifier(action=action, kind="property")
            return PropertyAccessAction(action)

        if "(" not in action or not action.endswith(")"):
            raise ValueError(f"Invalid method action syntax: {action!r}.")

        method_name, _, method_signature = action.partition("(")
        self._validate_identifier(action=method_name, kind="method")
        method_args_string = method_signature[:-1]

        method_args, method_kwargs = self._parse_method_arguments(
            method_args_string=method_args_string,
            action=action,
        )
        return MethodCallAction(
            method_name=method_name,
            method_args=method_args,
            method_kwargs=method_kwargs,
        )

    def _validate_identifier(self, action: str, kind: str) -> None:
        if not action.isidentifier():
            raise ValueError(f"Invalid {kind} name: {action!r}.")

    def _parse_method_arguments(
        self,
        method_args_string: str,
        action: str,
    ) -> tuple[tuple[Any, ...], dict[str, Any]]:
        if not method_args_string:
            return (), {}

        try:
            parsed_call_expression = ast.parse(f"_action({method_args_string})", mode="eval")
        except SyntaxError as error:
            raise ValueError(f"Invalid method arguments in action: {action!r}.") from error

        parsed_call = cast("ast.Call", parsed_call_expression.body)

        method_args = tuple(
            self._parse_literal(node=argument_node, action=action)
            for argument_node in parsed_call.args
        )
        method_kwargs: dict[str, Any] = {}

        for keyword_node in parsed_call.keywords:
            if keyword_node.arg is None:
                raise ValueError(f"Unsupported kwargs unpacking in action: {action!r}.")

            method_kwargs[keyword_node.arg] = self._parse_literal(
                node=keyword_node.value,
                action=action,
            )

        return method_args, method_kwargs

    def _parse_literal(self, node: ast.AST, action: str) -> Any:
        try:
            return ast.literal_eval(node)
        except (TypeError, ValueError) as error:
            raise ValueError(
                f"Only Python literals are supported in action arguments: {action!r}.",
            ) from error


class BaseAction(ABC):
    @abstractmethod
    def __call__(self, current_object: Any) -> Any: ...


class PropertyAccessAction(BaseAction):
    def __init__(self, property_name: str) -> None:
        self._property_name = property_name

    def __call__(self, current_object: Any) -> Any:
        return getattr(current_object, self._property_name)


class MethodCallAction(BaseAction):
    def __init__(
        self,
        method_name: str,
        method_args: tuple[Any, ...] = (),
        method_kwargs: dict[str, Any] | None = None,
    ) -> None:
        self._method_name = method_name
        self._method_args = method_args
        self._method_kwargs = method_kwargs or {}

    def __call__(self, current_object: Any) -> Any:
        method = getattr(current_object, self._method_name)
        return method(*self._method_args, **self._method_kwargs)
