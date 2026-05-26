from __future__ import annotations

from typing import Any
from adobe.core import BrokerClient
from adobe.core.session import HostSession

class PremiereSession(HostSession):
    def __init__(self, client: BrokerClient | None = ...) -> None: ...


class Premiere(PremiereSession):
    def __init__(self, *, broker_url: str | None = ..., token: str | None = ..., target: str = "default", timeout: float = ..., client: BrokerClient | None = ...) -> None: ...
    @property
    def version(self) -> str: ...
    @property
    def active_project(self) -> ProjectProxy | None: ...
    @property
    def activeProject(self) -> ProjectProxy | None: ...


class PremiereApp:
    @property
    def version(self) -> str: ...
    @property
    def active_project(self) -> ProjectProxy | None: ...
    @property
    def activeProject(self) -> ProjectProxy | None: ...


class ProjectProxy:
    @property
    def name(self) -> str | None: ...
