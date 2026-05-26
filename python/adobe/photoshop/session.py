from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from adobe.core import BrokerClient
from adobe.core.session import HostSession


class PhotoshopSession(HostSession):
    def __init__(self, client: BrokerClient | None = None) -> None:
        super().__init__("photoshop", client)
        self.app = PhotoshopApp(self)
        self.action = PhotoshopAction(self)
        self.dom = PhotoshopDomProxy(self, [])
        self._modal_stack: list[str] = []

    @contextmanager
    def modal(self, command_name: str) -> Iterator[None]:
        self._modal_stack.append(command_name)
        try:
            yield
        finally:
            self._modal_stack.pop()

    def modal_options(
        self,
        *,
        modal: bool | None = None,
        command_name: str | None = None,
        default_command_name: str | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        active_command = command_name or (self._modal_stack[-1] if self._modal_stack else None) or default_command_name
        should_modal = modal if modal is not None else active_command is not None
        options: dict[str, Any] = {"modal": should_modal}
        if active_command:
            options["commandName"] = active_command
        if timeout_ms is not None:
            options["timeoutMs"] = timeout_ms
        return options


class Photoshop(PhotoshopSession):
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
    def documents(self) -> list["DocumentProxy"]:
        return self.app.documents

    @property
    def activeDocument(self) -> "DocumentProxy | None":
        return self.app.activeDocument

    @property
    def active_document(self) -> "DocumentProxy | None":
        return self.app.active_document

    @property
    def activeLayer(self) -> "LayerProxy | None":
        return self.app.activeLayer

    @property
    def active_layer(self) -> "LayerProxy | None":
        return self.app.active_layer

    @property
    def activeLayers(self) -> list["LayerProxy"]:
        return self.app.activeLayers

    @property
    def active_layers(self) -> list["LayerProxy"]:
        return self.app.active_layers

    def eval_js(self, source: str, *args: Any, timeout_ms: int | None = None) -> Any:
        return self.invoke("raw", "evalJs", source, *args, options=_timeout_options(timeout_ms))

    def evalJs(self, source: str, *args: Any, timeoutMs: int | None = None) -> Any:
        return self.eval_js(source, *args, timeout_ms=timeoutMs)

    def batchPlay(
        self,
        descriptors: list[dict[str, Any]],
        options: dict[str, Any] | None = None,
        *,
        modal: bool | None = None,
        commandName: str | None = None,
        command_name: str | None = None,
        timeoutMs: int | None = None,
        timeout_ms: int | None = None,
    ) -> Any:
        return self.action.batchPlay(
            descriptors,
            options,
            modal=modal,
            commandName=commandName,
            command_name=command_name,
            timeoutMs=timeoutMs,
            timeout_ms=timeout_ms,
        )

    def batch_play(
        self,
        descriptors: list[dict[str, Any]],
        options: dict[str, Any] | None = None,
        *,
        modal: bool | None = None,
        command_name: str | None = None,
        timeout_ms: int | None = None,
    ) -> Any:
        return self.action.batch_play(
            descriptors,
            options,
            modal=modal,
            command_name=command_name,
            timeout_ms=timeout_ms,
        )

    def executeAsModal(
        self,
        callback: Any | None = None,
        *,
        commandName: str | None = None,
        command_name: str | None = None,
    ) -> Any:
        command = commandName or command_name or "Adobe Python command"
        context = self.modal(command)
        if callback is None:
            return context
        with context:
            return callback()

    def execute_as_modal(
        self,
        callback: Any | None = None,
        *,
        command_name: str | None = None,
    ) -> Any:
        return self.executeAsModal(callback, command_name=command_name)


class PhotoshopApp:
    def __init__(self, session: PhotoshopSession) -> None:
        self._session = session

    @property
    def version(self) -> str:
        return str(self._session.invoke("app", "getVersion"))

    @property
    def documents(self) -> list["DocumentProxy"]:
        payload = self._session.invoke("app", "getDocuments")
        return [DocumentProxy(self._session, document) for document in payload or []]

    @property
    def active_document(self) -> "DocumentProxy | None":
        payload = self._session.invoke("document", "getActive")
        return DocumentProxy(self._session, payload) if payload else None

    @property
    def activeDocument(self) -> "DocumentProxy | None":
        return self.active_document

    @property
    def active_layer(self) -> "LayerProxy | None":
        payload = self._session.invoke("layer", "getActive")
        return LayerProxy(self._session, payload) if payload else None

    @property
    def activeLayer(self) -> "LayerProxy | None":
        return self.active_layer

    @property
    def active_layers(self) -> list["LayerProxy"]:
        document = self.active_document
        return document.active_layers if document else []

    @property
    def activeLayers(self) -> list["LayerProxy"]:
        return self.active_layers


class PhotoshopAction:
    def __init__(self, session: PhotoshopSession) -> None:
        self._session = session

    def batch_play(
        self,
        descriptors: list[dict[str, Any]],
        options: dict[str, Any] | None = None,
        *,
        modal: bool | None = None,
        command_name: str | None = None,
        default_command_name: str | None = None,
        timeout_ms: int | None = None,
    ) -> Any:
        return self._session.invoke(
            "action",
            "batchPlay",
            descriptors,
            options or {},
            options=self._session.modal_options(
                modal=modal,
                command_name=command_name,
                default_command_name=default_command_name,
                timeout_ms=timeout_ms,
            ),
        )

    def batchPlay(
        self,
        descriptors: list[dict[str, Any]],
        options: dict[str, Any] | None = None,
        *,
        modal: bool | None = None,
        commandName: str | None = None,
        command_name: str | None = None,
        timeoutMs: int | None = None,
        timeout_ms: int | None = None,
    ) -> Any:
        return self.batch_play(
            descriptors,
            options,
            modal=modal,
            command_name=commandName or command_name,
            timeout_ms=timeoutMs if timeoutMs is not None else timeout_ms,
        )


class PhotoshopDomProxy:
    def __init__(self, session: PhotoshopSession, path: list[str | int]) -> None:
        self._session = session
        self._path = path

    def __repr__(self) -> str:
        return f"PhotoshopDomProxy({'.'.join(str(item) for item in self._path) or 'photoshop'})"

    def __getattr__(self, name: str) -> "PhotoshopDomProxy":
        if name.startswith("_"):
            raise AttributeError(name)
        return PhotoshopDomProxy(self._session, [*self._path, name])

    def __getitem__(self, key: int | str) -> "PhotoshopDomProxy":
        return PhotoshopDomProxy(self._session, [*self._path, key])

    def get(self, *, depth: int = 2, timeout_ms: int | None = None) -> Any:
        return self._session.invoke(
            "raw",
            "getPath",
            self._path,
            depth,
            options=_timeout_options(timeout_ms),
        )

    def call(
        self,
        *args: Any,
        modal: bool | None = None,
        command_name: str | None = None,
        timeout_ms: int | None = None,
        depth: int = 2,
    ) -> Any:
        return self._session.invoke(
            "raw",
            "callPath",
            self._path,
            list(args),
            depth,
            options=self._session.modal_options(modal=modal, command_name=command_name, timeout_ms=timeout_ms),
        )

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self.call(*args, **kwargs)


@dataclass
class DocumentProxy:
    _session: PhotoshopSession
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
    def resolution(self) -> Any:
        return self._payload.get("resolution")

    @property
    def saved(self) -> bool | None:
        return self._payload.get("saved")

    @property
    def mode(self) -> str | None:
        return self._payload.get("mode")

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")

    @property
    def layers(self) -> list["LayerProxy"]:
        payload = self._session.invoke("document", "getLayers", self.id)
        return [LayerProxy(self._session, layer) for layer in payload or []]

    @property
    def active_layers(self) -> list["LayerProxy"]:
        payload = self._session.invoke("document", "getActiveLayers", self.id)
        return [LayerProxy(self._session, layer) for layer in payload or []]

    @property
    def activeLayers(self) -> list["LayerProxy"]:
        return self.active_layers

    @property
    def dom(self) -> PhotoshopDomProxy:
        return PhotoshopDomProxy(self._session, ["app", "activeDocument"])

    def refresh(self) -> "DocumentProxy":
        payload = self._session.invoke("document", "getById", self.id)
        self._payload = payload or {}
        return self

    def save_as(
        self,
        path: str,
        *,
        format: str = "psd",
        modal: bool | None = None,
        command_name: str | None = None,
        timeout_ms: int | None = None,
    ) -> Any:
        return self._session.invoke(
            "document",
            "saveAs",
            {"id": self.id, "path": path, "format": format},
            options=self._session.modal_options(
                modal=modal,
                command_name=command_name,
                default_command_name="Save document",
                timeout_ms=timeout_ms,
            ),
        )

    def saveAs(
        self,
        path: str,
        *,
        format: str = "psd",
        modal: bool | None = None,
        commandName: str | None = None,
        timeoutMs: int | None = None,
    ) -> Any:
        return self.save_as(path, format=format, modal=modal, command_name=commandName, timeout_ms=timeoutMs)

    def export(
        self,
        path: str,
        *,
        format: str = "png",
        modal: bool | None = None,
        command_name: str | None = None,
        timeout_ms: int | None = None,
    ) -> Any:
        return self._session.invoke(
            "document",
            "export",
            {"id": self.id, "path": path, "format": format},
            options=self._session.modal_options(
                modal=modal,
                command_name=command_name,
                default_command_name="Export document",
                timeout_ms=timeout_ms,
            ),
        )


@dataclass
class LayerProxy:
    _session: PhotoshopSession
    _payload: dict[str, Any]

    @property
    def id(self) -> int | str | None:
        return self._payload.get("id")

    @property
    def name(self) -> str | None:
        return self._payload.get("name")

    @property
    def kind(self) -> str | None:
        return self._payload.get("kind")

    @property
    def opacity(self) -> Any:
        return self._payload.get("opacity")

    @property
    def visible(self) -> bool | None:
        return self._payload.get("visible")

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")

    @property
    def has_children(self) -> bool:
        return bool(self._payload.get("hasChildren"))

    @property
    def hasChildren(self) -> bool:
        return self.has_children

    @property
    def layers(self) -> list["LayerProxy"]:
        payload = self._session.invoke("layer", "getChildren", self.id)
        return [LayerProxy(self._session, layer) for layer in payload or []]

    def hide(self, *, command_name: str | None = None) -> Any:
        return self._session.action.batch_play(
            [{"_obj": "hide", "_target": [{"_ref": "layer", "_id": self.id}]}],
            modal=True,
            command_name=command_name,
            default_command_name="Hide layer",
        )


def connect(
    *,
    broker_url: str | None = None,
    token: str | None = None,
    target: str = "default",
    timeout: float = 30.0,
) -> PhotoshopSession:
    return Photoshop(broker_url=broker_url, token=token, target=target, timeout=timeout)


async def connect_async(
    *,
    broker_url: str | None = None,
    token: str | None = None,
    target: str = "default",
    timeout: float = 30.0,
) -> PhotoshopSession:
    return connect(broker_url=broker_url, token=token, target=target, timeout=timeout)


def _timeout_options(timeout_ms: int | None) -> dict[str, Any]:
    return {"timeoutMs": timeout_ms} if timeout_ms is not None else {}
