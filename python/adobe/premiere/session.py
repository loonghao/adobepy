from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adobe.core import BrokerClient
from adobe.core.session import HostSession


class PremiereSession(HostSession):
    def __init__(self, client: BrokerClient | None = None) -> None:
        super().__init__("premiere", client)
        self.app = PremiereApp(self)


class Premiere(PremiereSession):
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
    def activeProject(self) -> "ProjectProxy | None":
        return self.app.activeProject

    @property
    def active_project(self) -> "ProjectProxy | None":
        return self.app.active_project

    @property
    def project(self) -> "ProjectProxy | None":
        return self.app.active_project


class PremiereApp:
    def __init__(self, session: PremiereSession) -> None:
        self._session = session

    @property
    def version(self) -> str:
        return str(self._session.invoke("app", "getVersion"))

    @property
    def active_project(self) -> "ProjectProxy | None":
        payload = self._session.invoke("project", "getActive")
        return ProjectProxy(self._session, payload) if payload else None

    @property
    def activeProject(self) -> "ProjectProxy | None":
        return self.active_project


@dataclass
class ProjectProxy:
    _session: PremiereSession
    _payload: dict[str, Any]

    @property
    def name(self) -> str | None:
        return self._payload.get("name")


def connect(
    *,
    broker_url: str | None = None,
    token: str | None = None,
    target: str = "default",
    timeout: float = 30.0,
) -> PremiereSession:
    return Premiere(broker_url=broker_url, token=token, target=target, timeout=timeout)


async def connect_async(
    *,
    broker_url: str | None = None,
    token: str | None = None,
    target: str = "default",
    timeout: float = 30.0,
) -> PremiereSession:
    return connect(broker_url=broker_url, token=token, target=target, timeout=timeout)
