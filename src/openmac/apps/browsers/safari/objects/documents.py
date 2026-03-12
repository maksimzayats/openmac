from __future__ import annotations

import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from appscript import GenericReference, Keyword

from openmac._logging import preview_text
from openmac.apps.shared.base import BaseManager, BaseObject

if TYPE_CHECKING:
    from openmac.apps.browsers.safari.objects.application import Safari

logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class SafariDocument(BaseObject):
    ae_document: GenericReference

    # region Properties

    @property
    def name(self) -> str:
        return self.ae_document.name()

    @property
    def modified(self) -> bool:
        return self.ae_document.modified()

    @property
    def file(self) -> Any | None:
        file_value = self.ae_document.file()
        if hasattr(file_value, "AS_name") and file_value.AS_name == "missing_value":
            return None

        return file_value

    @property
    def url(self) -> str:
        return self.ae_document.URL()

    @property
    def text(self) -> str:
        return self.ae_document.text()

    @property
    def source(self) -> str:
        return self.ae_document.source()

    @property
    def properties(self) -> SafariDocumentProperties:
        ae_properties = self.ae_document.properties()
        file_value = ae_properties[Keyword("file")]
        if hasattr(file_value, "AS_name") and file_value.AS_name == "missing_value":
            file_value = None

        return SafariDocumentProperties(
            name=ae_properties[Keyword("name")],
            modified=ae_properties[Keyword("modified")],
            file=file_value,
            url=ae_properties[Keyword("URL")],
            text=ae_properties[Keyword("text")],
            source=ae_properties[Keyword("source")],
        )

    # endregion Properties

    # region Actions

    def close(self) -> None:
        logger.info("Closing Safari document url=%s name=%r", self.url, self.name)
        self.ae_document.close()

    def execute(self, javascript: str) -> Any | None:
        logger.debug(
            "Executing JavaScript in Safari document url=%s: %s",
            self.url,
            preview_text(javascript),
        )
        result = self.ae_document.do_JavaScript(javascript)
        if hasattr(result, "AS_name") and result.AS_name == "missing_value":
            logger.debug(
                "JavaScript execution in Safari document url=%s returned missing value",
                self.url,
            )
            return None

        logger.debug("JavaScript execution in Safari document url=%s completed", self.url)
        return result

    def email_contents(self) -> None:
        logger.info("Emailing contents of Safari document url=%s", self.url)
        self.ae_document.email_contents()

    def search_the_web(self, query: str) -> None:
        logger.info("Searching the web from Safari document url=%s query=%r", self.url, query)
        self.ae_document.search_the_web(for_=query)

    # endregion Actions

    # region Custom Actions

    def wait_until_loaded(
        self,
        timeout: float = 10.0,
        delay: float = 0.1,
    ) -> None:
        logger.info(
            "Waiting for Safari document url=%s to finish loading timeout=%s delay=%s",
            self.url,
            timeout,
            delay,
        )
        start_time = time.perf_counter()
        poll_count = 0

        while True:
            poll_count += 1
            ready_state = self.execute("document.readyState")
            if ready_state == "complete":
                logger.info(
                    "Safari document url=%s finished loading after %s polls",
                    self.url,
                    poll_count,
                )
                return
            if time.perf_counter() - start_time > timeout:
                logger.warning(
                    "Safari document url=%s timed out while loading after %s seconds",
                    self.url,
                    timeout,
                )
                raise TimeoutError(
                    f"SafariDocument did not finish loading within {timeout} seconds.",
                )

            logger.debug(
                "Safari document url=%s still loading at poll=%s ready_state=%r",
                self.url,
                poll_count,
                ready_state,
            )
            time.sleep(delay)

    # endregion Custom Actions


@dataclass(slots=True)
class SafariDocumentProperties:
    name: str
    modified: bool
    file: Any | None
    url: str
    text: str
    source: str


@dataclass(slots=True, kw_only=True)
class SafariDocumentsManager(BaseManager[SafariDocument]):
    safari: Safari

    def _iter_objects(self) -> Iterator[SafariDocument]:
        logger.debug("Enumerating Safari documents")
        for ae_document in self.safari.ae_safari.documents():
            yield SafariDocument(ae_document=ae_document)
