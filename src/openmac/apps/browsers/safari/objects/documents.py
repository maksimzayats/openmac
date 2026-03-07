from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from appscript import GenericReference, Keyword

from openmac.apps.shared.base import BaseManager, BaseObject

if TYPE_CHECKING:
    from openmac import Safari


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
        self.ae_document.close()

    def execute(self, javascript: str) -> Any | None:
        result = self.ae_document.do_JavaScript(javascript)
        if hasattr(result, "AS_name") and result.AS_name == "missing_value":
            return None

        return result

    def email_contents(self) -> None:
        self.ae_document.email_contents()

    def search_the_web(self, query: str) -> None:
        self.ae_document.search_the_web(for_=query)

    # endregion Actions

    # region Custom Actions

    def wait_until_loaded(
        self,
        timeout: float = 10.0,
        delay: float = 0.1,
    ) -> None:
        start_time = time.perf_counter()

        while True:
            ready_state = self.execute("document.readyState")
            if ready_state == "complete":
                return
            if time.perf_counter() - start_time > timeout:
                raise TimeoutError(
                    f"SafariDocument did not finish loading within {timeout} seconds.",
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

    def _load(self) -> list[SafariDocument]:
        return [
            SafariDocument(ae_document=ae_document)
            for ae_document in self.safari.ae_safari.documents()
        ]
