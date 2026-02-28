from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ActionsParser:
    def __init__(self, args: list[str]) -> None:
        self._args = args

    def parse(self) -> list[BaseAction]:
        raise NotImplementedError("ActionsParser.parse is not implemented yet.")


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
        return method()
