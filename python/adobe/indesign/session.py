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
