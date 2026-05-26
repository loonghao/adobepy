from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adobe.core import BrokerClient
from adobe.core.session import HostSession


class InDesignSession(HostSession):
    def __init__(self, client: BrokerClient | None = None) -> None:
        super().__init__("indesign", client)
        self.app = InDesignApp(self)


class InDesign(InDesignSession):
    def __init__(
        self,
        *,
        broker_url: str | None = None,
        token: str | None = None,
        target: str = "default",
        timeout: float = 30.0,
        client: BrokerClient | None = None,
    ) -> None:
        super().__init__(client or BrokerClient(broker_url=broker_url, token=token, target=target, timeout=timeout))

    @property
    def version(self) -> str:
        return self.app.version

    @property
    def activeDocument(self) -> "DocumentProxy | None":
        return self.app.activeDocument

    @property
    def active_document(self) -> "DocumentProxy | None":
        return self.app.active_document

    @property
    def active_page(self) -> "PageProxy | None":
        return self.app.active_page

    @property
    def activePage(self) -> "PageProxy | None":
        return self.active_page

    @property
    def active_spread(self) -> "SpreadProxy | None":
        return self.app.active_spread

    @property
    def activeSpread(self) -> "SpreadProxy | None":
        return self.active_spread


class InDesignApp:
    def __init__(self, session: InDesignSession) -> None:
        self._session = session

    @property
    def version(self) -> str:
        return str(self._session.invoke("app", "getVersion"))

    @property
    def active_document(self) -> "DocumentProxy | None":
        payload = self._session.invoke("document", "getActive")
        return DocumentProxy(self._session, payload) if payload else None

    @property
    def activeDocument(self) -> "DocumentProxy | None":
        return self.active_document

    @property
    def active_page(self) -> "PageProxy | None":
        document = self.active_document
        if document is None:
            return None
        return document.active_page

    @property
    def activePage(self) -> "PageProxy | None":
        return self.active_page

    @property
    def active_spread(self) -> "SpreadProxy | None":
        document = self.active_document
        if document is None:
            return None
        return document.active_spread

    @property
    def activeSpread(self) -> "SpreadProxy | None":
        return self.active_spread


@dataclass
class DocumentProxy:
    _session: InDesignSession
    _payload: dict[str, Any]

    @property
    def id(self) -> int | str | None:
        return self._payload.get("id")

    @property
    def name(self) -> str | None:
        return self._payload.get("name")

    @property
    def path(self) -> str | None:
        return self._payload.get("path")

    @property
    def width(self) -> Any:
        return self._payload.get("width")

    @property
    def height(self) -> Any:
        return self._payload.get("height")

    @property
    def page_count(self) -> int:
        return int(self._payload.get("pageCount") or 0)

    @property
    def pageCount(self) -> int:
        return self.page_count

    @property
    def spread_count(self) -> int:
        return int(self._payload.get("spreadCount") or 0)

    @property
    def spreadCount(self) -> int:
        return self.spread_count

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")

    @property
    def pages(self) -> list["PageProxy"]:
        payload = self._session.invoke("page", "getPages", self.id)
        return [PageProxy(self._session, self.id, page) for page in payload or []]

    @property
    def spreads(self) -> list["SpreadProxy"]:
        payload = self._session.invoke("spread", "getSpreads", self.id)
        return [SpreadProxy(self._session, self.id, spread) for spread in payload or []]

    @property
    def active_page(self) -> "PageProxy | None":
        payload = self._session.invoke("page", "getActive", self.id)
        return PageProxy(self._session, self.id, payload) if payload else None

    @property
    def activePage(self) -> "PageProxy | None":
        return self.active_page

    @property
    def active_spread(self) -> "SpreadProxy | None":
        payload = self._session.invoke("spread", "getActive", self.id)
        return SpreadProxy(self._session, self.id, payload) if payload else None

    @property
    def activeSpread(self) -> "SpreadProxy | None":
        return self.active_spread

    def get_page(self, name: str) -> "PageProxy | None":
        payload = self._session.invoke("page", "getByName", self.id, name)
        return PageProxy(self._session, self.id, payload) if payload else None

    def getPage(self, name: str) -> "PageProxy | None":
        return self.get_page(name)

    def get_spread(self, name: str) -> "SpreadProxy | None":
        payload = self._session.invoke("spread", "getByName", self.id, name)
        return SpreadProxy(self._session, self.id, payload) if payload else None

    def getSpread(self, name: str) -> "SpreadProxy | None":
        return self.get_spread(name)


@dataclass
class PageProxy:
    _session: InDesignSession
    _document_id: int | str | None
    _payload: dict[str, Any]

    @property
    def id(self) -> int | str | None:
        return self._payload.get("id")

    @property
    def name(self) -> str | None:
        return self._payload.get("name")

    @property
    def index(self) -> Any:
        return self._payload.get("index")

    @property
    def document_offset(self) -> Any:
        return self._payload.get("documentOffset")

    @property
    def documentOffset(self) -> Any:
        return self.document_offset

    @property
    def side(self) -> Any:
        return self._payload.get("side")

    @property
    def bounds(self) -> list[Any]:
        value = self._payload.get("bounds")
        return list(value) if isinstance(value, list) else []

    @property
    def parent_id(self) -> int | str | None:
        return self._payload.get("parentId")

    @property
    def parentId(self) -> int | str | None:
        return self.parent_id

    @property
    def parent_name(self) -> str | None:
        return self._payload.get("parentName")

    @property
    def parentName(self) -> str | None:
        return self.parent_name

    @property
    def is_valid(self) -> bool | None:
        value = self._payload.get("isValid")
        return bool(value) if value is not None else None

    @property
    def isValid(self) -> bool | None:
        return self.is_valid

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")

    def select(self, existing_selection: Any | None = None) -> "PageProxy":
        payload = self._session.invoke("page", "select", self._document_id, self.id or self.name, existing_selection)
        self._payload = payload or {}
        return self


@dataclass
class SpreadProxy:
    _session: InDesignSession
    _document_id: int | str | None
    _payload: dict[str, Any]

    @property
    def id(self) -> int | str | None:
        return self._payload.get("id")

    @property
    def name(self) -> str | None:
        return self._payload.get("name")

    @property
    def label(self) -> str | None:
        return self._payload.get("label")

    @property
    def index(self) -> Any:
        return self._payload.get("index")

    @property
    def page_count(self) -> int:
        return int(self._payload.get("pageCount") or 0)

    @property
    def pageCount(self) -> int:
        return self.page_count

    @property
    def page_names(self) -> list[str]:
        value = self._payload.get("pageNames")
        return [str(name) for name in value] if isinstance(value, list) else []

    @property
    def pageNames(self) -> list[str]:
        return self.page_names

    @property
    def parent_id(self) -> int | str | None:
        return self._payload.get("parentId")

    @property
    def parentId(self) -> int | str | None:
        return self.parent_id

    @property
    def parent_name(self) -> str | None:
        return self._payload.get("parentName")

    @property
    def parentName(self) -> str | None:
        return self.parent_name

    @property
    def is_valid(self) -> bool | None:
        value = self._payload.get("isValid")
        return bool(value) if value is not None else None

    @property
    def isValid(self) -> bool | None:
        return self.is_valid

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")


def connect(
    *,
    broker_url: str | None = None,
    token: str | None = None,
    target: str = "default",
    timeout: float = 30.0,
) -> InDesignSession:
    return InDesign(broker_url=broker_url, token=token, target=target, timeout=timeout)


async def connect_async(
    *,
    broker_url: str | None = None,
    token: str | None = None,
    target: str = "default",
    timeout: float = 30.0,
) -> InDesignSession:
    return connect(broker_url=broker_url, token=token, target=target, timeout=timeout)
