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

    @property
    def artboard_count(self) -> int | None:
        return _optional_int(_payload_value(self._payload, "artboardCount", "artboard_count"))

    @property
    def artboardCount(self) -> int | None:
        return self.artboard_count

    @property
    def layer_count(self) -> int | None:
        return _optional_int(_payload_value(self._payload, "layerCount", "layer_count"))

    @property
    def layerCount(self) -> int | None:
        return self.layer_count

    @property
    def page_item_count(self) -> int | None:
        return _optional_int(_payload_value(self._payload, "pageItemCount", "page_item_count"))

    @property
    def pageItemCount(self) -> int | None:
        return self.page_item_count

    @property
    def selection_count(self) -> int | None:
        return _optional_int(_payload_value(self._payload, "selectionCount", "selection_count"))

    @property
    def selectionCount(self) -> int | None:
        return self.selection_count

    @property
    def artboards(self) -> list["ArtboardProxy"]:
        payload = self._session.invoke("artboard", "getArtboards")
        return [ArtboardProxy(item) for item in payload or []]

    @property
    def active_artboard(self) -> "ArtboardProxy | None":
        payload = self._session.invoke("artboard", "getActive")
        return ArtboardProxy(payload) if payload else None

    @property
    def activeArtboard(self) -> "ArtboardProxy | None":
        return self.active_artboard

    @property
    def active_artboard_index(self) -> int | None:
        return _optional_int(self._session.invoke("artboard", "getActiveIndex"))

    @property
    def activeArtboardIndex(self) -> int | None:
        return self.active_artboard_index

    @property
    def layers(self) -> list["LayerProxy"]:
        payload = self._session.invoke("layer", "getLayers")
        return [LayerProxy(self._session, item) for item in payload or []]

    @property
    def page_items(self) -> list["PageItemProxy"]:
        payload = self._session.invoke("pageItem", "getPageItems")
        return [PageItemProxy(item) for item in payload or []]

    @property
    def pageItems(self) -> list["PageItemProxy"]:
        return self.page_items

    @property
    def selection(self) -> list["PageItemProxy"]:
        payload = self._session.invoke("pageItem", "getSelected")
        return [PageItemProxy(item) for item in payload or []]

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")

    def get_layer_by_name(self, name: str) -> "LayerProxy | None":
        payload = self._session.invoke("layer", "getByName", name)
        return LayerProxy(self._session, payload) if payload else None

    def getLayerByName(self, name: str) -> "LayerProxy | None":
        return self.get_layer_by_name(name)

    def get_page_item_by_name(self, name: str) -> "PageItemProxy | None":
        payload = self._session.invoke("pageItem", "getByName", name)
        return PageItemProxy(payload) if payload else None

    def getPageItemByName(self, name: str) -> "PageItemProxy | None":
        return self.get_page_item_by_name(name)


@dataclass
class ArtboardProxy:
    _payload: dict[str, Any]

    @property
    def index(self) -> int | None:
        return _optional_int(self._payload.get("index"))

    @property
    def name(self) -> str | None:
        return self._payload.get("name")

    @property
    def artboard_rect(self) -> Any:
        return self._payload.get("artboardRect") or self._payload.get("artboard_rect")

    @property
    def artboardRect(self) -> Any:
        return self.artboard_rect

    @property
    def ruler_origin(self) -> Any:
        return self._payload.get("rulerOrigin") or self._payload.get("ruler_origin")

    @property
    def rulerOrigin(self) -> Any:
        return self.ruler_origin

    @property
    def ruler_par(self) -> Any:
        return _payload_value(self._payload, "rulerPAR", "rulerPar", "ruler_par")

    @property
    def rulerPar(self) -> Any:
        return self.ruler_par

    @property
    def show_center(self) -> bool | None:
        return _optional_bool(_payload_value(self._payload, "showCenter", "show_center"))

    @property
    def showCenter(self) -> bool | None:
        return self.show_center

    @property
    def show_cross_hairs(self) -> bool | None:
        return _optional_bool(_payload_value(self._payload, "showCrossHairs", "show_cross_hairs"))

    @property
    def showCrossHairs(self) -> bool | None:
        return self.show_cross_hairs

    @property
    def show_safe_areas(self) -> bool | None:
        return _optional_bool(_payload_value(self._payload, "showSafeAreas", "show_safe_areas"))

    @property
    def showSafeAreas(self) -> bool | None:
        return self.show_safe_areas

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")


@dataclass
class LayerProxy:
    _session: IllustratorSession
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
    def visible(self) -> bool | None:
        return _optional_bool(self._payload.get("visible"))

    @property
    def locked(self) -> bool | None:
        return _optional_bool(self._payload.get("locked"))

    @property
    def printable(self) -> bool | None:
        return _optional_bool(self._payload.get("printable"))

    @property
    def preview(self) -> bool | None:
        return _optional_bool(self._payload.get("preview"))

    @property
    def opacity(self) -> float | None:
        return _optional_float(self._payload.get("opacity"))

    @property
    def has_selected_artwork(self) -> bool | None:
        return _optional_bool(_payload_value(self._payload, "hasSelectedArtwork", "has_selected_artwork"))

    @property
    def hasSelectedArtwork(self) -> bool | None:
        return self.has_selected_artwork

    @property
    def parent_name(self) -> str | None:
        return self._payload.get("parentName") or self._payload.get("parent_name")

    @property
    def parentName(self) -> str | None:
        return self.parent_name

    @property
    def parent_typename(self) -> str | None:
        return self._payload.get("parentTypename") or self._payload.get("parent_typename")

    @property
    def parentTypename(self) -> str | None:
        return self.parent_typename

    @property
    def layer_count(self) -> int | None:
        return _optional_int(_payload_value(self._payload, "layerCount", "layer_count"))

    @property
    def layerCount(self) -> int | None:
        return self.layer_count

    @property
    def page_item_count(self) -> int | None:
        return _optional_int(_payload_value(self._payload, "pageItemCount", "page_item_count"))

    @property
    def pageItemCount(self) -> int | None:
        return self.page_item_count

    @property
    def layers(self) -> list["LayerProxy"]:
        payload = self._session.invoke("layer", "getChildren", self._layer_key)
        return [LayerProxy(self._session, item) for item in payload or []]

    @property
    def page_items(self) -> list["PageItemProxy"]:
        payload = self._session.invoke("pageItem", "getLayerItems", self._layer_key)
        return [PageItemProxy(item) for item in payload or []]

    @property
    def pageItems(self) -> list["PageItemProxy"]:
        return self.page_items

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")

    @property
    def _layer_key(self) -> Any:
        return self.id or self.name or self.index


@dataclass
class PageItemProxy:
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
    def item_type(self) -> str | None:
        return self._payload.get("itemType") or self._payload.get("item_type")

    @property
    def itemType(self) -> str | None:
        return self.item_type

    @property
    def hidden(self) -> bool | None:
        return _optional_bool(self._payload.get("hidden"))

    @property
    def locked(self) -> bool | None:
        return _optional_bool(self._payload.get("locked"))

    @property
    def selected(self) -> bool | None:
        return _optional_bool(self._payload.get("selected"))

    @property
    def editable(self) -> bool | None:
        return _optional_bool(self._payload.get("editable"))

    @property
    def sliced(self) -> bool | None:
        return _optional_bool(self._payload.get("sliced"))

    @property
    def position(self) -> Any:
        return self._payload.get("position")

    @property
    def geometric_bounds(self) -> Any:
        return self._payload.get("geometricBounds") or self._payload.get("geometric_bounds")

    @property
    def geometricBounds(self) -> Any:
        return self.geometric_bounds

    @property
    def visible_bounds(self) -> Any:
        return self._payload.get("visibleBounds") or self._payload.get("visible_bounds")

    @property
    def visibleBounds(self) -> Any:
        return self.visible_bounds

    @property
    def control_bounds(self) -> Any:
        return self._payload.get("controlBounds") or self._payload.get("control_bounds")

    @property
    def controlBounds(self) -> Any:
        return self.control_bounds

    @property
    def width(self) -> Any:
        return self._payload.get("width")

    @property
    def height(self) -> Any:
        return self._payload.get("height")

    @property
    def opacity(self) -> float | None:
        return _optional_float(self._payload.get("opacity"))

    @property
    def parent_name(self) -> str | None:
        return self._payload.get("parentName") or self._payload.get("parent_name")

    @property
    def parentName(self) -> str | None:
        return self.parent_name

    @property
    def parent_typename(self) -> str | None:
        return self._payload.get("parentTypename") or self._payload.get("parent_typename")

    @property
    def parentTypename(self) -> str | None:
        return self.parent_typename

    @property
    def layer_name(self) -> str | None:
        return self._payload.get("layerName") or self._payload.get("layer_name")

    @property
    def layerName(self) -> str | None:
        return self.layer_name

    @property
    def note(self) -> str | None:
        return self._payload.get("note")

    @property
    def url(self) -> str | None:
        return self._payload.get("url")

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")


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
