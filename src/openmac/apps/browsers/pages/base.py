from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from time import sleep
from typing import TYPE_CHECKING, Any, Self, overload

from bs4 import BeautifulSoup

from openmac.apps.browsers.pages.exceptions import InvalidDataError
from openmac.apps.browsers.pages.scripts import IS_ELEMENT_IN_VIEWPORT_FUNCTION, REAL_CLICK_FUNCTION

if TYPE_CHECKING:
    from openmac.apps.browsers.base.objects.tabs import IBrowserTab

logger = logging.getLogger(__name__)


@dataclass(kw_only=True)
class BasePage(ABC):
    tab: IBrowserTab

    @classmethod
    @abstractmethod
    def from_tab(cls, tab: IBrowserTab, **kwargs: Any) -> Self: ...

    @property
    def snapshot(self) -> BeautifulSoup:
        html = self.tab.execute("document.documentElement.outerHTML")
        return BeautifulSoup(html, "lxml")

    def real_click(self, element_getter: str) -> None:
        script = REAL_CLICK_FUNCTION + f"\nrealClick({element_getter});"
        self.tab.execute(script)

    def is_element_visible(self, element_getter: str) -> bool:
        script = IS_ELEMENT_IN_VIEWPORT_FUNCTION + f"\nisElementInViewport({element_getter});"
        return self.tab.execute(script)


@dataclass(kw_only=True)
class BasePageElement:
    pass


@overload
def must_get[T](
    getter: Callable[[], T | None],
    error_description: str,
    *,
    exit_condition: Callable[[T], bool] = lambda result: result is not None,
    tries: int = 100,
    delay: float = 0.1,
    raise_error: bool = True,
) -> T: ...


@overload
def must_get[T](
    getter: Callable[[], T],
    error_description: str,
    *,
    exit_condition: Callable[[T], bool] = lambda result: result is not None,
    tries: int = 100,
    delay: float = 0.1,
    raise_error: bool = True,
) -> T: ...


def must_get[T](  # noqa: PLR0913
    getter: Callable[[], T | None],
    error_description: str,
    *,
    exit_condition: Callable[[Any], bool] = lambda result: result is not None,
    tries: int = 100,
    delay: float = 0.1,
    raise_error: bool = True,
) -> T | None:
    for _ in range(tries):
        result = getter()
        if exit_condition(result):
            return result

        sleep(delay)

    if raise_error:
        raise InvalidDataError(error_description)

    logger.warning(error_description)

    return None
