"use strict";
(() => {
  var __require = /* @__PURE__ */ ((x) => typeof require !== "undefined" ? require : typeof Proxy !== "undefined" ? new Proxy(x, {
    get: (a, b) => (typeof require !== "undefined" ? require : a)[b]
  }) : x)(function(x) {
    if (typeof require !== "undefined") return require.apply(this, arguments);
    throw Error('Dynamic require of "' + x + '" is not supported');
  });

  // bridges/uxp/core/src/protocol.ts
  var ERROR_CODES = Object.freeze({
    ERROR_PARSE: -32700,
    ERROR_INVALID_REQUEST: -32600,
    ERROR_METHOD_NOT_FOUND: -32601,
    ERROR_HOST_NOT_RUNNING: -32001,
    ERROR_BRIDGE_NOT_INSTALLED: -32002,
    ERROR_CAPABILITY: -32003,
    ERROR_HOST_SCRIPT: -32004,
    ERROR_PERMISSION: -32005,
    ERROR_MODAL_REQUIRED: -32006,
    ERROR_TIMEOUT: -32007,
    ERROR_SERIALIZATION: -32008,
    ERROR_UNAUTHORIZED: -32009
  });

  // bridges/uxp/core/src/errors.ts
  var ERROR_METHOD_NOT_FOUND = ERROR_CODES.ERROR_METHOD_NOT_FOUND;
  var ERROR_HOST_SCRIPT = ERROR_CODES.ERROR_HOST_SCRIPT;
  var BridgeRpcError = class extends Error {
    constructor(code, message, data) {
      super(message);
      this.name = "BridgeRpcError";
      this.code = code;
      this.data = data;
    }
  };
  function methodNotFound(namespace, method) {
    throw new BridgeRpcError(ERROR_METHOD_NOT_FOUND, `unsupported method ${namespace}.${method}`);
  }
  function unavailable(feature) {
    throw new BridgeRpcError(ERROR_HOST_SCRIPT, `${feature} is unavailable in this host runtime`);
  }

  // bridges/uxp/core/src/rpc.ts
  function connectBridge(adapter) {
    const url = globalThis.__ADOBEPY_BROKER_URL || `ws://127.0.0.1:47391/v1/bridge/${adapter.capabilities().host}/ws`;
    const token = globalThis.__ADOBEPY_TOKEN || "dev-token";
    const target = globalThis.__ADOBEPY_TARGET || "default";
    const socket = new WebSocket(url);
    socket.addEventListener("open", () => {
      socket.send(JSON.stringify({ type: "hello", token, target, capabilities: adapter.capabilities() }));
    });
    socket.addEventListener("message", async (event) => {
      const message = JSON.parse(event.data);
      if (message.type !== "request") return;
      const request = message.request;
      try {
        const result = await adapter.dispatch(request);
        socket.send(JSON.stringify({ type: "response", response: { jsonrpc: "2.0", id: request.id, result: result ?? null } }));
      } catch (error) {
        socket.send(JSON.stringify({ type: "error", error: hostError(request.id, error) }));
      }
    });
  }
  function hostError(id, error) {
    const code = error instanceof BridgeRpcError ? error.code : ERROR_HOST_SCRIPT;
    const message = error instanceof Error ? error.message : String(error);
    const data = error instanceof BridgeRpcError ? error.data : void 0;
    return { jsonrpc: "2.0", id, error: { code, message, ...data === void 0 ? {} : { data } } };
  }

  // bridges/uxp/core/src/runtime.ts
  function optionalRequire(moduleName) {
    const loader = globalThis.require ?? __require;
    if (typeof loader !== "function") return void 0;
    try {
      const loaded = loader(moduleName);
      return isObject(loaded) ? loaded : void 0;
    } catch {
      return void 0;
    }
  }
  function isObject(value) {
    return typeof value === "object" && value !== null;
  }
  function asArray(value) {
    if (Array.isArray(value)) return value;
    if (!isObject(value)) return [];
    const iterable = value;
    if (typeof iterable[Symbol.iterator] === "function") return Array.from(iterable);
    const length = value.length;
    if (typeof length === "number") {
      return Array.from({ length }, (_, index) => value[index]).filter((item) => item !== void 0);
    }
    return [];
  }
  function asString(value) {
    if (typeof value === "string" && value.length > 0) return value;
    if (typeof value === "number" || typeof value === "boolean") return String(value);
    return void 0;
  }
  function asNumber(value) {
    if (typeof value === "number") return value;
    if (isObject(value) && typeof value.valueOf === "function") {
      const converted = value.valueOf();
      if (typeof converted === "number") return converted;
    }
    return void 0;
  }
  function property(value, name) {
    if (!isObject(value)) return void 0;
    return value[name];
  }
  async function maybePromise(value) {
    return await value;
  }
  async function evalJavaScript(source, args) {
    try {
      return await (0, eval)(source);
    } catch (error) {
      if (!(error instanceof SyntaxError)) throw error;
      const fn = new Function("args", source);
      return await fn(args);
    }
  }

  // bridges/uxp/premiere/src/host.ts
  var premiereAdapter = {
    capabilities() {
      return {
        host: "premiere",
        bridgeKind: "uxp",
        bridgeVersion: "0.1.0",
        hostVersion: premiereVersion(),
        namespaces: ["app", "project", "sequence", "track", "clip", "marker", "raw"],
        features: ["project", "sequence", "track", "clip", "marker"],
        methods: {
          app: ["getVersion"],
          project: ["getActive", "getSequences", "getActiveSequence"],
          sequence: ["getVideoTracks", "getAudioTracks"],
          track: ["getClips"],
          clip: ["getSelected"],
          marker: ["getMarkers", "create"],
          raw: ["evalJs"]
        }
      };
    },
    async dispatch(request) {
      if (request.namespace === "app" && request.method === "getVersion") return premiereVersion();
      if (request.namespace === "project" && request.method === "getActive") return serializeProject(await activeProject());
      if (request.namespace === "project" && request.method === "getSequences") return serializeSequences(await projectSequences(await activeProject()));
      if (request.namespace === "project" && request.method === "getActiveSequence") return serializeSequence(await activeSequence());
      if (request.namespace === "sequence" && request.method === "getVideoTracks") {
        return serializeTracks(sequenceTracks(await requireSequence(request.args?.[0]), "video"), "video");
      }
      if (request.namespace === "sequence" && request.method === "getAudioTracks") {
        return serializeTracks(sequenceTracks(await requireSequence(request.args?.[0]), "audio"), "audio");
      }
      if (request.namespace === "track" && request.method === "getClips") return trackClips(request);
      if (request.namespace === "clip" && request.method === "getSelected") return selectedClips(await requireSequence(request.args?.[0]));
      if (request.namespace === "marker" && request.method === "getMarkers") return sequenceMarkers(await requireSequence(request.args?.[0]));
      if (request.namespace === "marker" && request.method === "create") return createMarker(request);
      if (request.namespace === "raw" && request.method === "evalJs") return evalJavaScript(asString(request.args?.[0]) ?? "", request.args?.slice(1) ?? []);
      methodNotFound(request.namespace, request.method);
    }
  };
  function premiereModule() {
    return optionalRequire("premierepro") ?? globalThis.premierepro ?? {};
  }
  function uxpModule() {
    return optionalRequire("uxp") ?? globalThis.uxp ?? {};
  }
  function premiereVersion() {
    const premiere = premiereModule();
    const host = property(uxpModule(), "host");
    return asString(property(premiere, "version")) ?? asString(property(host, "version")) ?? "unknown";
  }
  async function activeProject() {
    const premiere = premiereModule();
    const projectApi = property(premiere, "Project");
    const getActiveProject = property(projectApi, "getActiveProject") ?? property(projectApi, "getActive");
    if (getActiveProject) return await maybePromise(getActiveProject.call(projectApi));
    return property(premiere, "project") ?? property(property(premiere, "app"), "project");
  }
  async function projectSequences(project) {
    if (!project) return [];
    const getSequences = property(project, "getSequences");
    if (getSequences) return collectionItems(await maybePromise(getSequences.call(project)));
    const sequences = property(project, "sequences") ?? property(project, "sequenceCollection");
    return collectionItems(sequences);
  }
  async function activeSequence() {
    const project = await activeProject();
    const direct = property(project, "activeSequence") ?? property(project, "active_sequence");
    if (direct) return direct;
    const getActiveSequence = property(project, "getActiveSequence") ?? property(project, "getActiveSequenceProjectItem");
    if (getActiveSequence) return await maybePromise(getActiveSequence.call(project));
    const premiere = premiereModule();
    return property(premiere, "activeSequence") ?? property(property(premiere, "app"), "activeSequence");
  }
  async function findSequence(idOrName) {
    const active = await activeSequence();
    if (sequenceMatches(active, idOrName) || idOrName === void 0 || idOrName === null) return active;
    const sequences = await projectSequences(await activeProject());
    return sequences.find((sequence) => sequenceMatches(sequence, idOrName));
  }
  async function requireSequence(idOrName) {
    const sequence = await findSequence(idOrName);
    if (!sequence) unavailable("Premiere sequence");
    return sequence;
  }
  function sequenceMatches(sequence, idOrName) {
    if (!isObject(sequence)) return false;
    if (idOrName === void 0 || idOrName === null) return true;
    const values = [
      property(sequence, "id"),
      property(sequence, "guid"),
      property(sequence, "sequenceId"),
      property(sequence, "sequenceID"),
      property(sequence, "name")
    ];
    return values.some((value) => value !== void 0 && String(value) === String(idOrName));
  }
  function serializeProject(project) {
    if (!isObject(project)) return null;
    return {
      id: property(project, "guid") ?? property(project, "id"),
      guid: property(project, "guid"),
      name: asString(property(project, "name")),
      path: asString(property(project, "path")),
      itemCount: asNumber(property(project, "itemCount")) ?? asNumber(property(project, "numItems"))
    };
  }
  function serializeSequences(sequences) {
    return sequences.map(serializeSequence).filter((sequence) => sequence !== null);
  }
  function serializeSequence(sequence) {
    if (!isObject(sequence)) return null;
    return {
      id: property(sequence, "id") ?? property(sequence, "guid") ?? property(sequence, "sequenceId") ?? property(sequence, "sequenceID"),
      guid: property(sequence, "guid"),
      sequenceId: property(sequence, "sequenceId") ?? property(sequence, "sequenceID"),
      name: asString(property(sequence, "name")),
      duration: serializeTime(property(sequence, "duration") ?? property(sequence, "end")),
      timebase: property(sequence, "timebase") ?? property(sequence, "videoDisplayFormat"),
      typename: asString(property(sequence, "typename")) ?? asString(property(sequence, "typeName"))
    };
  }
  function sequenceTracks(sequence, mediaType) {
    const propertyName = mediaType === "video" ? "videoTracks" : "audioTracks";
    return collectionItems(property(sequence, propertyName));
  }
  function serializeTracks(tracks, mediaType) {
    return tracks.map((track, index) => serializeTrack(track, index, mediaType)).filter((track) => track !== null);
  }
  function serializeTrack(track, index, mediaType) {
    if (!isObject(track)) return null;
    return {
      id: property(track, "id") ?? property(track, "trackID") ?? property(track, "trackId") ?? index,
      name: asString(property(track, "name")),
      index: asNumber(property(track, "index")) ?? index,
      mediaType,
      isLocked: booleanValue(property(track, "isLocked") ?? property(track, "locked")),
      isMuted: booleanValue(property(track, "isMuted") ?? property(track, "muted")),
      isTargeted: booleanValue(property(track, "isTargeted") ?? property(track, "targeted")),
      typename: asString(property(track, "typename")) ?? asString(property(track, "typeName"))
    };
  }
  async function trackClips(request) {
    const sequence = await requireSequence(request.args?.[0]);
    const mediaType = normalizeMediaType(request.args?.[1]);
    const track = findTrack(sequence, mediaType, request.args?.[2]);
    if (!track) unavailable("Premiere track");
    return collectionItems(property(track, "clips")).map(serializeClip).filter((clip) => clip !== null);
  }
  function selectedClips(sequence) {
    const clips = [
      ...sequenceTracks(sequence, "video").flatMap((track) => collectionItems(property(track, "clips"))),
      ...sequenceTracks(sequence, "audio").flatMap((track) => collectionItems(property(track, "clips")))
    ];
    return clips.filter((clip) => booleanValue(property(clip, "isSelected") ?? property(clip, "selected")) === true).map(serializeClip).filter((clip) => clip !== null);
  }
  function findTrack(sequence, mediaType, idOrIndex) {
    const tracks = sequenceTracks(sequence, mediaType);
    if (idOrIndex === void 0 || idOrIndex === null) return tracks[0];
    return tracks.find((track, index) => {
      const values = [property(track, "id"), property(track, "trackID"), property(track, "trackId"), property(track, "name"), property(track, "index"), index];
      return values.some((value) => value !== void 0 && String(value) === String(idOrIndex));
    });
  }
  function serializeClip(clip) {
    if (!isObject(clip)) return null;
    const projectItem = property(clip, "projectItem");
    return {
      id: property(clip, "id") ?? property(clip, "nodeId") ?? property(clip, "nodeID"),
      name: asString(property(clip, "name")) ?? asString(property(projectItem, "name")),
      projectItemId: property(projectItem, "id") ?? property(projectItem, "nodeId") ?? property(projectItem, "nodeID"),
      mediaPath: asString(property(clip, "mediaPath")) ?? asString(property(projectItem, "mediaPath")) ?? asString(property(projectItem, "treePath")),
      start: serializeTime(property(clip, "start")),
      end: serializeTime(property(clip, "end")),
      inPoint: serializeTime(property(clip, "inPoint")),
      outPoint: serializeTime(property(clip, "outPoint")),
      duration: serializeTime(property(clip, "duration")),
      isEnabled: booleanValue(property(clip, "isEnabled") ?? property(clip, "enabled")),
      isSelected: booleanValue(property(clip, "isSelected") ?? property(clip, "selected")),
      typename: asString(property(clip, "typename")) ?? asString(property(clip, "typeName"))
    };
  }
  async function sequenceMarkers(sequence) {
    const markers = property(sequence, "markers") ?? property(sequence, "markerCollection");
    const getMarkers = property(markers, "getMarkers") ?? property(sequence, "getMarkers");
    if (getMarkers) return collectionItems(await maybePromise(getMarkers.call(markers ?? sequence))).map(serializeMarker).filter((marker) => marker !== null);
    return markerItems(markers).map(serializeMarker).filter((marker) => marker !== null);
  }
  async function createMarker(request) {
    const sequence = await requireSequence(request.args?.[0]);
    const payload = isObject(request.args?.[1]) ? request.args?.[1] : {};
    const markers = property(sequence, "markers") ?? property(sequence, "markerCollection");
    const create = property(markers, "createMarker") ?? property(sequence, "createMarker");
    if (!create) unavailable("Premiere marker.createMarker");
    const start = property(payload, "start") ?? property(payload, "time") ?? 0;
    const marker = await maybePromise(create.call(markers ?? sequence, start));
    if (isObject(marker)) applyMarkerPayload(marker, payload);
    return serializeMarker(marker);
  }
  function applyMarkerPayload(marker, payload) {
    const assignments = [
      ["name", property(payload, "name")],
      ["comments", property(payload, "comments") ?? property(payload, "comment")],
      ["end", property(payload, "end")],
      ["duration", property(payload, "duration")],
      ["markerType", property(payload, "markerType") ?? property(payload, "marker_type")]
    ];
    for (const [key, value] of assignments) {
      if (value !== void 0) marker[key] = value;
    }
  }
  function markerItems(markers) {
    const direct = collectionItems(markers);
    if (direct.length > 0) return direct;
    const getFirstMarker = property(markers, "getFirstMarker");
    const getNextMarker = property(markers, "getNextMarker");
    if (getFirstMarker && getNextMarker) {
      const result = [];
      let current = getFirstMarker.call(markers);
      for (let guard = 0; current && guard < 1e4; guard += 1) {
        result.push(current);
        current = getNextMarker.call(markers, current);
      }
      return result;
    }
    return [];
  }
  function serializeMarker(marker) {
    if (!isObject(marker)) return null;
    return {
      id: property(marker, "id") ?? property(marker, "guid") ?? property(marker, "markerID") ?? property(marker, "markerId"),
      name: asString(property(marker, "name")),
      comments: asString(property(marker, "comments")) ?? asString(property(marker, "comment")),
      start: serializeTime(property(marker, "start") ?? property(marker, "time")),
      end: serializeTime(property(marker, "end")),
      duration: serializeTime(property(marker, "duration")),
      markerType: asString(property(marker, "markerType")) ?? asString(property(marker, "marker_type")),
      typename: asString(property(marker, "typename")) ?? asString(property(marker, "typeName"))
    };
  }
  function collectionItems(value) {
    const direct = asArray(value);
    if (direct.length > 0) return direct;
    const count = asNumber(property(value, "numItems")) ?? asNumber(property(value, "numTracks")) ?? asNumber(property(value, "numMarkers")) ?? asNumber(property(value, "length"));
    if (count === void 0 || count <= 0) return [];
    const at = property(value, "at") ?? property(value, "getAt") ?? property(value, "item");
    if (!at) return [];
    const result = [];
    for (let index = 0; index < count; index += 1) {
      const item = at.call(value, index);
      if (item !== void 0 && item !== null) result.push(item);
    }
    return result;
  }
  function normalizeMediaType(value) {
    return asString(value)?.toLowerCase() === "audio" ? "audio" : "video";
  }
  function booleanValue(value) {
    if (typeof value === "boolean") return value;
    if (typeof value === "number") return value !== 0;
    if (typeof value === "string") {
      if (value.toLowerCase() === "true") return true;
      if (value.toLowerCase() === "false") return false;
    }
    return void 0;
  }
  function serializeTime(value) {
    if (!isObject(value)) return asNumber(value) ?? asString(value) ?? value;
    const seconds = asNumber(property(value, "seconds"));
    const ticks = asString(property(value, "ticks")) ?? asString(property(value, "ticksPerSecond"));
    if (seconds !== void 0 && ticks !== void 0) return { seconds, ticks };
    if (seconds !== void 0) return seconds;
    if (ticks !== void 0) return ticks;
    return asNumber(value) ?? value;
  }

  // bridges/uxp/premiere/src/main.ts
  connectBridge(premiereAdapter);
})();
//# sourceMappingURL=main.js.map
