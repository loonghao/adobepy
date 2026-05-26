from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from adobe.core import BrokerClient
from adobe.core.session import HostSession


class PremiereSession(HostSession):
    def __init__(self, client: BrokerClient | None = None) -> None:
        super().__init__("premiere", client)
        self.app = PremiereApp(self)

    def modal_options(
        self,
        *,
        modal: bool | None = None,
        command_name: str | None = None,
        default_command_name: str | None = None,
        timeout_ms: int | None = None,
    ) -> dict[str, Any]:
        active_command = command_name or default_command_name
        should_modal = modal if modal is not None else active_command is not None
        options: dict[str, Any] = {"modal": should_modal}
        if active_command:
            options["commandName"] = active_command
        if timeout_ms is not None:
            options["timeoutMs"] = timeout_ms
        return options


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

    @property
    def sequences(self) -> list["SequenceProxy"]:
        return self.app.sequences

    @property
    def active_sequence(self) -> "SequenceProxy | None":
        return self.app.active_sequence

    @property
    def activeSequence(self) -> "SequenceProxy | None":
        return self.active_sequence


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

    @property
    def project(self) -> "ProjectProxy | None":
        return self.active_project

    @property
    def sequences(self) -> list["SequenceProxy"]:
        project = self.active_project
        return project.sequences if project else []

    @property
    def active_sequence(self) -> "SequenceProxy | None":
        payload = self._session.invoke("project", "getActiveSequence")
        return SequenceProxy(self._session, payload) if payload else None

    @property
    def activeSequence(self) -> "SequenceProxy | None":
        return self.active_sequence


@dataclass
class ProjectProxy:
    _session: PremiereSession
    _payload: dict[str, Any]

    @property
    def id(self) -> Any:
        return self._payload.get("id")

    @property
    def guid(self) -> str | None:
        return self._payload.get("guid")

    @property
    def name(self) -> str | None:
        return self._payload.get("name")

    @property
    def path(self) -> str | None:
        return self._payload.get("path")

    @property
    def item_count(self) -> int:
        return int(self._payload.get("itemCount") or 0)

    @property
    def itemCount(self) -> int:
        return self.item_count

    @property
    def active_sequence(self) -> "SequenceProxy | None":
        payload = self._session.invoke("project", "getActiveSequence")
        return SequenceProxy(self._session, payload) if payload else None

    @property
    def activeSequence(self) -> "SequenceProxy | None":
        return self.active_sequence

    @property
    def sequences(self) -> list["SequenceProxy"]:
        payload = self._session.invoke("project", "getSequences")
        return [SequenceProxy(self._session, sequence) for sequence in payload or []]

    def get_sequence(self, id_or_name: Any) -> "SequenceProxy | None":
        for sequence in self.sequences:
            if id_or_name in {sequence.id, sequence.sequence_id, sequence.name}:
                return sequence
        return None

    def getSequence(self, idOrName: Any) -> "SequenceProxy | None":
        return self.get_sequence(idOrName)


@dataclass
class SequenceProxy:
    _session: PremiereSession
    _payload: dict[str, Any]

    @property
    def id(self) -> Any:
        return self._payload.get("id")

    @property
    def guid(self) -> Any:
        return self._payload.get("guid")

    @property
    def sequence_id(self) -> Any:
        return self._payload.get("sequenceId") or self._payload.get("sequenceID") or self.id

    @property
    def sequenceId(self) -> Any:
        return self.sequence_id

    @property
    def name(self) -> str | None:
        return self._payload.get("name")

    @property
    def duration(self) -> Any:
        return self._payload.get("duration")

    @property
    def timebase(self) -> Any:
        return self._payload.get("timebase")

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")

    @property
    def video_tracks(self) -> list["TrackProxy"]:
        payload = self._session.invoke("sequence", "getVideoTracks", self._sequence_key)
        return [TrackProxy(self._session, self._sequence_key, "video", track) for track in payload or []]

    @property
    def videoTracks(self) -> list["TrackProxy"]:
        return self.video_tracks

    @property
    def audio_tracks(self) -> list["TrackProxy"]:
        payload = self._session.invoke("sequence", "getAudioTracks", self._sequence_key)
        return [TrackProxy(self._session, self._sequence_key, "audio", track) for track in payload or []]

    @property
    def audioTracks(self) -> list["TrackProxy"]:
        return self.audio_tracks

    @property
    def markers(self) -> list["MarkerProxy"]:
        payload = self._session.invoke("marker", "getMarkers", self._sequence_key)
        return [MarkerProxy(marker) for marker in payload or []]

    @property
    def selected_clips(self) -> list["ClipProxy"]:
        payload = self._session.invoke("clip", "getSelected", self._sequence_key)
        return [ClipProxy(clip) for clip in payload or []]

    @property
    def selectedClips(self) -> list["ClipProxy"]:
        return self.selected_clips

    def create_marker(
        self,
        name: str | None = None,
        *,
        start: Any = None,
        comments: str | None = None,
        end: Any = None,
        duration: Any = None,
        marker_type: str | None = None,
        command_name: str | None = None,
        timeout_ms: int | None = None,
        **properties: Any,
    ) -> "MarkerProxy":
        payload = {**properties}
        for key, value in {
            "name": name,
            "start": start,
            "comments": comments,
            "end": end,
            "duration": duration,
            "markerType": marker_type,
        }.items():
            if value is not None:
                payload[key] = value
        marker = self._session.invoke(
            "marker",
            "create",
            self._sequence_key,
            payload,
            options=self._session.modal_options(
                command_name=command_name,
                default_command_name="Create marker",
                timeout_ms=timeout_ms,
            ),
        )
        return MarkerProxy(marker or {})

    def createMarker(
        self,
        name: str | None = None,
        *,
        start: Any = None,
        comments: str | None = None,
        end: Any = None,
        duration: Any = None,
        markerType: str | None = None,
        commandName: str | None = None,
        timeoutMs: int | None = None,
        **properties: Any,
    ) -> "MarkerProxy":
        return self.create_marker(
            name,
            start=start,
            comments=comments,
            end=end,
            duration=duration,
            marker_type=markerType,
            command_name=commandName,
            timeout_ms=timeoutMs,
            **properties,
        )

    @property
    def _sequence_key(self) -> Any:
        return self.id or self.sequence_id or self.name


@dataclass
class TrackProxy:
    _session: PremiereSession
    _sequence_id: Any
    _media_type: str
    _payload: dict[str, Any]

    @property
    def id(self) -> Any:
        return self._payload.get("id")

    @property
    def name(self) -> str | None:
        return self._payload.get("name")

    @property
    def index(self) -> int | None:
        value = self._payload.get("index")
        return int(value) if value is not None else None

    @property
    def media_type(self) -> str | None:
        return self._payload.get("mediaType") or self._payload.get("media_type") or self._media_type

    @property
    def mediaType(self) -> str | None:
        return self.media_type

    @property
    def is_locked(self) -> bool | None:
        return self._payload.get("isLocked")

    @property
    def isLocked(self) -> bool | None:
        return self.is_locked

    @property
    def is_muted(self) -> bool | None:
        return self._payload.get("isMuted")

    @property
    def isMuted(self) -> bool | None:
        return self.is_muted

    @property
    def is_targeted(self) -> bool | None:
        return self._payload.get("isTargeted")

    @property
    def isTargeted(self) -> bool | None:
        return self.is_targeted

    @property
    def clips(self) -> list["ClipProxy"]:
        payload = self._session.invoke("track", "getClips", self._sequence_id, self.media_type, self._track_key)
        return [ClipProxy(clip) for clip in payload or []]

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")

    @property
    def _track_key(self) -> Any:
        return self.id if self.id is not None else self.index


@dataclass
class ClipProxy:
    _payload: dict[str, Any]

    @property
    def id(self) -> Any:
        return self._payload.get("id")

    @property
    def name(self) -> str | None:
        return self._payload.get("name")

    @property
    def project_item_id(self) -> Any:
        return self._payload.get("projectItemId") or self._payload.get("project_item_id")

    @property
    def projectItemId(self) -> Any:
        return self.project_item_id

    @property
    def media_path(self) -> str | None:
        return self._payload.get("mediaPath") or self._payload.get("media_path")

    @property
    def mediaPath(self) -> str | None:
        return self.media_path

    @property
    def start(self) -> Any:
        return self._payload.get("start")

    @property
    def end(self) -> Any:
        return self._payload.get("end")

    @property
    def in_point(self) -> Any:
        return self._payload.get("inPoint") or self._payload.get("in_point")

    @property
    def inPoint(self) -> Any:
        return self.in_point

    @property
    def out_point(self) -> Any:
        return self._payload.get("outPoint") or self._payload.get("out_point")

    @property
    def outPoint(self) -> Any:
        return self.out_point

    @property
    def duration(self) -> Any:
        return self._payload.get("duration")

    @property
    def is_enabled(self) -> bool | None:
        return self._payload.get("isEnabled")

    @property
    def isEnabled(self) -> bool | None:
        return self.is_enabled

    @property
    def is_selected(self) -> bool | None:
        return self._payload.get("isSelected")

    @property
    def isSelected(self) -> bool | None:
        return self.is_selected

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")


@dataclass
class MarkerProxy:
    _payload: dict[str, Any]

    @property
    def id(self) -> Any:
        return self._payload.get("id")

    @property
    def name(self) -> str | None:
        return self._payload.get("name")

    @property
    def comments(self) -> str | None:
        return self._payload.get("comments")

    @property
    def start(self) -> Any:
        return self._payload.get("start")

    @property
    def end(self) -> Any:
        return self._payload.get("end")

    @property
    def duration(self) -> Any:
        return self._payload.get("duration")

    @property
    def marker_type(self) -> str | None:
        return self._payload.get("markerType") or self._payload.get("marker_type")

    @property
    def markerType(self) -> str | None:
        return self.marker_type

    @property
    def typename(self) -> str | None:
        return self._payload.get("typename")


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
