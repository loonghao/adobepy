from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adobe.core import BrokerClient
from adobe.core.session import HostSession


class IllustratorSession(HostSession):
    def __init__(self, client: BrokerClient | None = None) -> None:
        super().__init__("illustrator", client)
        self.app = IllustratorApp(self)


class Illustrator(IllustratorSession):
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


class IllustratorApp:
    def __init__(self, session: IllustratorSession) -> None:
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
    _session: IllustratorSession
    _payload: dict[str, Any]

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


def connect(
    *,
    broker_url: str | None = None,
    token: str | None = None,
    target: str = "default",
    timeout: float = 30.0,
) -> IllustratorSession:
    return Illustrator(broker_url=broker_url, token=token, target=target, timeout=timeout)


async def connect_async(
    *,
    broker_url: str | None = None,
    token: str | None = None,
    target: str = "default",
    timeout: float = 30.0,
) -> IllustratorSession:
    return connect(broker_url=broker_url, token=token, target=target, timeout=timeout)
