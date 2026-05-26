from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adobe.core import BrokerClient
from adobe.core.session import HostSession


class AfterEffectsSession(HostSession):
    def __init__(self, client: BrokerClient | None = None) -> None:
        super().__init__("after-effects", client)
        self.app = AfterEffectsApp(self)


class AfterEffects(AfterEffectsSession):
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

    @property
    def active_item(self) -> "ProjectItemProxy | None":
        return self.app.active_item

    @property
    def activeItem(self) -> "ProjectItemProxy | None":
        return self.active_item

    @property
    def selected_items(self) -> list["ProjectItemProxy"]:
        return self.app.selected_items

    @property
    def selectedItems(self) -> list["ProjectItemProxy"]:
        return self.selected_items


class AfterEffectsApp:
    def __init__(self, session: AfterEffectsSession) -> None:
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

    @property
    def active_item(self) -> "ProjectItemProxy | None":
        payload = self._session.invoke("project", "getActiveItem")
        return ProjectItemProxy(payload) if payload else None

    @property
    def activeItem(self) -> "ProjectItemProxy | None":
        return self.active_item

    @property
    def selected_items(self) -> list["ProjectItemProxy"]:
        payload = self._session.invoke("project", "getSelectedItems")
        return [ProjectItemProxy(item) for item in payload or []]

    @property
    def selectedItems(self) -> list["ProjectItemProxy"]:
        return self.selected_items


@dataclass
class ProjectProxy:
    _session: AfterEffectsSession
    _payload: dict[str, Any]

    @property
    def name(self) -> str | None:
        return self._payload.get("name")

    @property
    def path(self) -> str | None:
        return self._payload.get("path")

    @property
    def item_count(self) -> int | None:
        return _optional_int(_payload_value(self._payload, "itemCount", "item_count"))

    @property
    def itemCount(self) -> int | None:
        return self.item_count

    @property
    def items(self) -> list["ProjectItemProxy"]:
        payload = self._session.invoke("project", "getItems")
        return [ProjectItemProxy(item) for item in payload or []]

    @property
    def compositions(self) -> list["CompositionProxy"]:
        payload = self._session.invoke("project", "getCompositions")
        return [CompositionProxy(item) for item in payload or []]

    @property
    def footage_items(self) -> list["FootageItemProxy"]:
        payload = self._session.invoke("project", "getFootageItems")
        return [FootageItemProxy(item) for item in payload or []]

    @property
    def footageItems(self) -> list["FootageItemProxy"]:
        return self.footage_items

    @property
    def folders(self) -> list["FolderItemProxy"]:
        payload = self._session.invoke("project", "getFolders")
        return [FolderItemProxy(item) for item in payload or []]

    @property
    def active_item(self) -> "ProjectItemProxy | None":
        payload = self._session.invoke("project", "getActiveItem")
        return ProjectItemProxy(payload) if payload else None

    @property
    def activeItem(self) -> "ProjectItemProxy | None":
        return self.active_item

    @property
    def selected_items(self) -> list["ProjectItemProxy"]:
        payload = self._session.invoke("project", "getSelectedItems")
        return [ProjectItemProxy(item) for item in payload or []]

    @property
    def selectedItems(self) -> list["ProjectItemProxy"]:
        return self.selected_items

    def get_item_by_id(self, item_id: Any) -> "ProjectItemProxy | None":
        payload = self._session.invoke("item", "getById", item_id)
        return ProjectItemProxy(payload) if payload else None

    def getItemById(self, itemId: Any) -> "ProjectItemProxy | None":
        return self.get_item_by_id(itemId)

    def get_items_by_name(self, name: str) -> list["ProjectItemProxy"]:
        payload = self._session.invoke("item", "getByName", name)
        return [ProjectItemProxy(item) for item in payload or []]

    def getItemsByName(self, name: str) -> list["ProjectItemProxy"]:
        return self.get_items_by_name(name)


@dataclass
class ProjectItemProxy:
    _payload: dict[str, Any]

    @property
    def id(self) -> Any:
        return self._payload.get("id")

    @property
    def index(self) -> int | None:
        return _optional_int(self._payload.get("index"))

    @property
    def name(self) -> str | None:
        return self._payload.get("name")

    @property
    def type_name(self) -> str | None:
        return self._payload.get("typeName") or self._payload.get("type_name")

    @property
    def typeName(self) -> str | None:
        return self.type_name

    @property
    def item_type(self) -> str | None:
        return self._payload.get("itemType") or self._payload.get("item_type")

    @property
    def itemType(self) -> str | None:
        return self.item_type

    @property
    def parent_folder_id(self) -> Any:
        return self._payload.get("parentFolderId") or self._payload.get("parent_folder_id")

    @property
    def parentFolderId(self) -> Any:
        return self.parent_folder_id

    @property
    def parent_folder_name(self) -> str | None:
        return self._payload.get("parentFolderName") or self._payload.get("parent_folder_name")

    @property
    def parentFolderName(self) -> str | None:
        return self.parent_folder_name

    @property
    def selected(self) -> bool | None:
        return _optional_bool(self._payload.get("selected"))

    @property
    def is_active(self) -> bool | None:
        return _optional_bool(_payload_value(self._payload, "isActive", "is_active"))

    @property
    def isActive(self) -> bool | None:
        return self.is_active

    @property
    def width(self) -> int | None:
        return _optional_int(self._payload.get("width"))

    @property
    def height(self) -> int | None:
        return _optional_int(self._payload.get("height"))

    @property
    def duration(self) -> float | None:
        return _optional_float(self._payload.get("duration"))

    @property
    def frame_rate(self) -> float | None:
        return _optional_float(_payload_value(self._payload, "frameRate", "frame_rate"))

    @property
    def frameRate(self) -> float | None:
        return self.frame_rate

    @property
    def has_video(self) -> bool | None:
        return _optional_bool(_payload_value(self._payload, "hasVideo", "has_video"))

    @property
    def hasVideo(self) -> bool | None:
        return self.has_video

    @property
    def has_audio(self) -> bool | None:
        return _optional_bool(_payload_value(self._payload, "hasAudio", "has_audio"))

    @property
    def hasAudio(self) -> bool | None:
        return self.has_audio

    @property
    def file_path(self) -> str | None:
        return self._payload.get("filePath") or self._payload.get("file_path")

    @property
    def filePath(self) -> str | None:
        return self.file_path

    @property
    def missing_footage(self) -> bool | None:
        return _optional_bool(_payload_value(self._payload, "missingFootage", "missing_footage"))

    @property
    def missingFootage(self) -> bool | None:
        return self.missing_footage

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")


@dataclass
class CompositionProxy:
    _payload: dict[str, Any]

    @property
    def id(self) -> Any:
        return self._payload.get("id")

    @property
    def index(self) -> int | None:
        return _optional_int(self._payload.get("index"))

    @property
    def name(self) -> str | None:
        return self._payload.get("name")

    @property
    def type_name(self) -> str | None:
        return self._payload.get("typeName") or self._payload.get("type_name")

    @property
    def typeName(self) -> str | None:
        return self.type_name

    @property
    def item_type(self) -> str | None:
        return self._payload.get("itemType") or self._payload.get("item_type")

    @property
    def itemType(self) -> str | None:
        return self.item_type

    @property
    def parent_folder_id(self) -> Any:
        return self._payload.get("parentFolderId") or self._payload.get("parent_folder_id")

    @property
    def parentFolderId(self) -> Any:
        return self.parent_folder_id

    @property
    def parent_folder_name(self) -> str | None:
        return self._payload.get("parentFolderName") or self._payload.get("parent_folder_name")

    @property
    def parentFolderName(self) -> str | None:
        return self.parent_folder_name

    @property
    def selected(self) -> bool | None:
        return _optional_bool(self._payload.get("selected"))

    @property
    def is_active(self) -> bool | None:
        return _optional_bool(_payload_value(self._payload, "isActive", "is_active"))

    @property
    def isActive(self) -> bool | None:
        return self.is_active

    @property
    def width(self) -> int | None:
        return _optional_int(self._payload.get("width"))

    @property
    def height(self) -> int | None:
        return _optional_int(self._payload.get("height"))

    @property
    def duration(self) -> float | None:
        return _optional_float(self._payload.get("duration"))

    @property
    def frame_rate(self) -> float | None:
        return _optional_float(_payload_value(self._payload, "frameRate", "frame_rate"))

    @property
    def frameRate(self) -> float | None:
        return self.frame_rate

    @property
    def num_layers(self) -> int | None:
        return _optional_int(_payload_value(self._payload, "numLayers", "num_layers"))

    @property
    def numLayers(self) -> int | None:
        return self.num_layers

    @property
    def work_area_start(self) -> float | None:
        return _optional_float(_payload_value(self._payload, "workAreaStart", "work_area_start"))

    @property
    def workAreaStart(self) -> float | None:
        return self.work_area_start

    @property
    def work_area_duration(self) -> float | None:
        return _optional_float(_payload_value(self._payload, "workAreaDuration", "work_area_duration"))

    @property
    def workAreaDuration(self) -> float | None:
        return self.work_area_duration

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")


@dataclass
class FootageItemProxy:
    _payload: dict[str, Any]

    @property
    def id(self) -> Any:
        return self._payload.get("id")

    @property
    def index(self) -> int | None:
        return _optional_int(self._payload.get("index"))

    @property
    def name(self) -> str | None:
        return self._payload.get("name")

    @property
    def type_name(self) -> str | None:
        return self._payload.get("typeName") or self._payload.get("type_name")

    @property
    def typeName(self) -> str | None:
        return self.type_name

    @property
    def item_type(self) -> str | None:
        return self._payload.get("itemType") or self._payload.get("item_type")

    @property
    def itemType(self) -> str | None:
        return self.item_type

    @property
    def parent_folder_id(self) -> Any:
        return self._payload.get("parentFolderId") or self._payload.get("parent_folder_id")

    @property
    def parentFolderId(self) -> Any:
        return self.parent_folder_id

    @property
    def parent_folder_name(self) -> str | None:
        return self._payload.get("parentFolderName") or self._payload.get("parent_folder_name")

    @property
    def parentFolderName(self) -> str | None:
        return self.parent_folder_name

    @property
    def selected(self) -> bool | None:
        return _optional_bool(self._payload.get("selected"))

    @property
    def is_active(self) -> bool | None:
        return _optional_bool(_payload_value(self._payload, "isActive", "is_active"))

    @property
    def isActive(self) -> bool | None:
        return self.is_active

    @property
    def width(self) -> int | None:
        return _optional_int(self._payload.get("width"))

    @property
    def height(self) -> int | None:
        return _optional_int(self._payload.get("height"))

    @property
    def duration(self) -> float | None:
        return _optional_float(self._payload.get("duration"))

    @property
    def frame_rate(self) -> float | None:
        return _optional_float(_payload_value(self._payload, "frameRate", "frame_rate"))

    @property
    def frameRate(self) -> float | None:
        return self.frame_rate

    @property
    def has_video(self) -> bool | None:
        return _optional_bool(_payload_value(self._payload, "hasVideo", "has_video"))

    @property
    def hasVideo(self) -> bool | None:
        return self.has_video

    @property
    def has_audio(self) -> bool | None:
        return _optional_bool(_payload_value(self._payload, "hasAudio", "has_audio"))

    @property
    def hasAudio(self) -> bool | None:
        return self.has_audio

    @property
    def file_path(self) -> str | None:
        return self._payload.get("filePath") or self._payload.get("file_path")

    @property
    def filePath(self) -> str | None:
        return self.file_path

    @property
    def missing_footage(self) -> bool | None:
        return _optional_bool(_payload_value(self._payload, "missingFootage", "missing_footage"))

    @property
    def missingFootage(self) -> bool | None:
        return self.missing_footage

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")


@dataclass
class FolderItemProxy:
    _payload: dict[str, Any]

    @property
    def id(self) -> Any:
        return self._payload.get("id")

    @property
    def index(self) -> int | None:
        return _optional_int(self._payload.get("index"))

    @property
    def name(self) -> str | None:
        return self._payload.get("name")

    @property
    def type_name(self) -> str | None:
        return self._payload.get("typeName") or self._payload.get("type_name")

    @property
    def typeName(self) -> str | None:
        return self.type_name

    @property
    def item_type(self) -> str | None:
        return self._payload.get("itemType") or self._payload.get("item_type")

    @property
    def itemType(self) -> str | None:
        return self.item_type

    @property
    def parent_folder_id(self) -> Any:
        return self._payload.get("parentFolderId") or self._payload.get("parent_folder_id")

    @property
    def parentFolderId(self) -> Any:
        return self.parent_folder_id

    @property
    def parent_folder_name(self) -> str | None:
        return self._payload.get("parentFolderName") or self._payload.get("parent_folder_name")

    @property
    def parentFolderName(self) -> str | None:
        return self.parent_folder_name

    @property
    def selected(self) -> bool | None:
        return _optional_bool(self._payload.get("selected"))

    @property
    def is_active(self) -> bool | None:
        return _optional_bool(_payload_value(self._payload, "isActive", "is_active"))

    @property
    def isActive(self) -> bool | None:
        return self.is_active

    @property
    def item_count(self) -> int | None:
        return _optional_int(_payload_value(self._payload, "itemCount", "item_count"))

    @property
    def itemCount(self) -> int | None:
        return self.item_count

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")


def connect(
    *,
    broker_url: str | None = None,
    token: str | None = None,
    target: str = "default",
    timeout: float = 30.0,
) -> AfterEffectsSession:
    return AfterEffects(broker_url=broker_url, token=token, target=target, timeout=timeout)


async def connect_async(
    *,
    broker_url: str | None = None,
    token: str | None = None,
    target: str = "default",
    timeout: float = 30.0,
) -> AfterEffectsSession:
    return connect(broker_url=broker_url, token=token, target=target, timeout=timeout)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    return int(value)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _optional_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
    return None


def _payload_value(payload: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in payload:
            return payload[key]
    return None
