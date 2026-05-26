"use strict";
(() => {
  var __require = /* @__PURE__ */ ((x) => typeof require !== "undefined" ? require : typeof Proxy !== "undefined" ? new Proxy(x, {
    get: (a, b) => (typeof require !== "undefined" ? require : a)[b]
  }) : x)(function(x) {
    if (typeof require !== "undefined") return require.apply(this, arguments);
    throw Error('Dynamic require of "' + x + '" is not supported');
  });

  // bridges/uxp/core/src/errors.ts
  var ERROR_METHOD_NOT_FOUND = -32601;
  var ERROR_HOST_SCRIPT = -32004;
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
  function fileName(path) {
    return path.split(/[\\/]/).filter(Boolean).pop() ?? path;
  }
  function toFileUrl(path) {
    if (/^file:\/\//i.test(path)) return path;
    const normalized = path.replace(/\\/g, "/");
    if (/^[A-Za-z]:\//.test(normalized)) return `file:///${encodeURI(normalized)}`;
    if (normalized.startsWith("/")) return `file://${encodeURI(normalized)}`;
    return normalized;
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

  // bridges/uxp/photoshop/src/host.ts
  var photoshopAdapter = {
    capabilities() {
      return {
        host: "photoshop",
        bridgeKind: "uxp",
        bridgeVersion: "0.1.0",
        hostVersion: photoshopVersion(),
        namespaces: ["app", "document", "layer", "action", "raw"],
        features: ["batchPlay", "executeAsModal"],
        methods: {
          app: ["getVersion", "getDocuments"],
          document: ["getActive", "getById", "getLayers", "getActiveLayers", "saveAs", "export"],
          layer: ["getActive", "getChildren"],
          action: ["batchPlay"],
          raw: ["evalJs", "getPath", "callPath"]
        }
      };
    },
    async dispatch(request) {
      if (request.namespace === "app" && request.method === "getVersion") return photoshopVersion();
      if (request.namespace === "app" && request.method === "getDocuments") return serializeDocuments(openDocuments());
      if (request.namespace === "document" && request.method === "getActive") return serializeDocument(activeDocument());
      if (request.namespace === "document" && request.method === "getById") return serializeDocument(findDocument(request.args?.[0]));
      if (request.namespace === "document" && request.method === "getLayers") return documentLayers(request);
      if (request.namespace === "document" && request.method === "getActiveLayers") return documentActiveLayers(request);
      if (request.namespace === "document" && request.method === "saveAs") return saveDocument(request, false);
      if (request.namespace === "document" && request.method === "export") return saveDocument(request, true);
      if (request.namespace === "layer" && request.method === "getActive") return serializeLayer(activeLayer());
      if (request.namespace === "layer" && request.method === "getChildren") return layerChildren(request);
      if (request.namespace === "action" && request.method === "batchPlay") return batchPlay(request);
      if (request.namespace === "raw" && request.method === "evalJs") return evalJavaScript(asString(request.args?.[0]) ?? "", request.args?.slice(1) ?? []);
      if (request.namespace === "raw" && request.method === "getPath") return getPath(request);
      if (request.namespace === "raw" && request.method === "callPath") return callPath(request);
      methodNotFound(request.namespace, request.method);
    }
  };
  function photoshopModule() {
    return optionalRequire("photoshop") ?? globalThis.photoshop ?? {};
  }
  function uxpModule() {
    return optionalRequire("uxp") ?? globalThis.uxp ?? {};
  }
  function photoshopApp() {
    return property(photoshopModule(), "app") ?? globalThis.app ?? {};
  }
  function photoshopVersion() {
    const app = photoshopApp();
    const uxp = uxpModule();
    return asString(property(app, "version")) ?? asString(property(property(uxp, "host"), "version")) ?? asString(property(photoshopModule(), "version")) ?? "unknown";
  }
  function activeDocument() {
    return property(photoshopApp(), "activeDocument");
  }
  function openDocuments() {
    return asArray(property(photoshopApp(), "documents"));
  }
  function findDocument(id) {
    const active = activeDocument();
    if (id === void 0 || id === null) return active;
    const match = openDocuments().find((document) => String(property(document, "id")) === String(id));
    return match ?? (String(property(active, "id")) === String(id) ? active : void 0);
  }
  function activeLayer() {
    const document = activeDocument();
    return asArray(property(document, "activeLayers"))[0] ?? property(document, "activeLayer");
  }
  function serializeDocument(document) {
    if (!isObject(document)) return null;
    return {
      id: property(document, "id"),
      name: asString(property(document, "title")) ?? asString(property(document, "name")),
      path: asString(property(property(document, "fullName"), "fsName")) ?? asString(property(document, "path")),
      width: asNumber(property(document, "width")) ?? property(document, "width"),
      height: asNumber(property(document, "height")) ?? property(document, "height"),
      resolution: asNumber(property(document, "resolution")) ?? property(document, "resolution"),
      saved: property(document, "saved"),
      mode: asString(property(document, "mode")),
      typename: asString(property(document, "typename"))
    };
  }
  function serializeLayer(layer) {
    if (!isObject(layer)) return null;
    return {
      id: property(layer, "id"),
      name: asString(property(layer, "name")),
      kind: asString(property(layer, "kind")),
      opacity: asNumber(property(layer, "opacity")) ?? property(layer, "opacity"),
      visible: property(layer, "visible"),
      typename: asString(property(layer, "typename")),
      hasChildren: asArray(property(layer, "layers")).length > 0
    };
  }
  function serializeDocuments(documents) {
    return documents.map(serializeDocument).filter((document) => document !== null);
  }
  function serializeLayers(layers) {
    return asArray(layers).map(serializeLayer).filter((layer) => layer !== null);
  }
  function documentLayers(request) {
    const document = findDocument(request.args?.[0]);
    if (!document) return [];
    return serializeLayers(property(document, "layers"));
  }
  function documentActiveLayers(request) {
    const document = findDocument(request.args?.[0]);
    if (!document) return [];
    return serializeLayers(property(document, "activeLayers"));
  }
  function layerChildren(request) {
    const layer = findLayer(request.args?.[0]);
    if (!layer) return [];
    return serializeLayers(property(layer, "layers"));
  }
  function findLayer(id) {
    if (id === void 0 || id === null) return activeLayer();
    for (const document of openDocuments()) {
      const match = findLayerInTree(property(document, "layers"), id) ?? findLayerInTree(property(document, "activeLayers"), id);
      if (match) return match;
    }
    return void 0;
  }
  function findLayerInTree(layers, id) {
    for (const layer of asArray(layers)) {
      if (String(property(layer, "id")) === String(id)) return layer;
      const child = findLayerInTree(property(layer, "layers"), id);
      if (child) return child;
    }
    return void 0;
  }
  async function batchPlay(request) {
    const action = property(photoshopModule(), "action");
    const runBatchPlay = property(action, "batchPlay");
    if (!runBatchPlay) unavailable("Photoshop action.batchPlay");
    const descriptors = request.args?.[0] ?? [];
    const actionOptions = isObject(request.args?.[1]) ? request.args?.[1] : {};
    return withModal(request, "Run batchPlay", () => maybePromise(runBatchPlay.call(action, descriptors, actionOptions)));
  }
  function getPath(request) {
    const path = normalizePath(request.args?.[0]);
    const depth = asNumber(request.args?.[1]) ?? 2;
    return serializeDomValue(resolvePath(path), depth);
  }
  async function callPath(request) {
    const path = normalizePath(request.args?.[0]);
    const callArgs = asArray(request.args?.[1]);
    return withModal(request, `Call ${path.join(".")}`, async () => {
      const parentPath = path.slice(0, -1);
      const member = path[path.length - 1];
      const parent = parentPath.length ? resolvePath(parentPath) : photoshopModule();
      const fn = typeof member === "number" ? asArray(parent)[member] : property(parent, String(member));
      if (typeof fn !== "function") unavailable(`Photoshop DOM method ${path.join(".")}`);
      return serializeDomValue(await maybePromise(fn.apply(parent, callArgs)), asNumber(request.args?.[2]) ?? 2);
    });
  }
  function normalizePath(path) {
    return asArray(path).map((segment) => {
      const number = asNumber(segment);
      return number === void 0 ? String(segment) : number;
    });
  }
  function resolvePath(path) {
    if (!path.length) return photoshopModule();
    let index = 0;
    let value;
    const first = path[0];
    if (first === "uxp") {
      value = uxpModule();
      index = 1;
    } else if (first === "photoshop") {
      value = photoshopModule();
      index = 1;
    } else if (first === "app") {
      value = photoshopApp();
      index = 1;
    } else {
      value = photoshopModule();
    }
    for (; index < path.length; index++) {
      const segment = path[index];
      value = typeof segment === "number" ? asArray(value)[segment] : property(value, segment);
    }
    return value;
  }
  function serializeDomValue(value, depth, seen = /* @__PURE__ */ new WeakSet()) {
    const scalar = scalarValue(value);
    if (!isObject(scalar)) return scalar ?? null;
    if (seen.has(scalar)) return "[Circular]";
    seen.add(scalar);
    if (Array.isArray(scalar) || typeof scalar[Symbol.iterator] === "function") {
      return asArray(scalar).map((item) => serializeDomValue(item, depth - 1, seen));
    }
    if (depth <= 0) {
      return {
        id: scalarValue(property(scalar, "id")),
        name: scalarValue(property(scalar, "name") ?? property(scalar, "title")),
        typename: scalarValue(property(scalar, "typename"))
      };
    }
    const output = {};
    for (const key of ["id", "name", "title", "path", "width", "height", "resolution", "saved", "typename", "kind", "opacity", "visible", "mode"]) {
      try {
        const item = property(scalar, key);
        if (item !== void 0 && typeof item !== "function") output[key] = serializeDomValue(item, depth - 1, seen);
      } catch {
      }
    }
    for (const key of ["documents", "layers", "activeLayers", "linkedLayers"]) {
      try {
        const item = property(scalar, key);
        if (item !== void 0 && typeof item !== "function") output[key] = serializeDomValue(item, depth - 1, seen);
      } catch {
      }
    }
    return output;
  }
  function scalarValue(value) {
    if (isObject(value)) {
      const valueOf = property(value, "valueOf");
      if (valueOf) {
        try {
          const converted = valueOf.call(value);
          if (!isObject(converted)) return converted;
        } catch {
          return value;
        }
      }
    }
    return value;
  }
  async function saveDocument(request, asCopy) {
    const payload = requestPayload(request);
    const document = findDocument(payload.id);
    if (!document) unavailable("Photoshop document");
    const path = asString(payload.path);
    if (!path) unavailable("Photoshop save path");
    const format = normalizeFormat(asString(payload.format) ?? "psd");
    return withModal(request, asCopy ? "Export document" : "Save document", async () => {
      const entry = await fileEntry(path);
      const saveAs = property(document, "saveAs");
      const saveFormat = property(saveAs, format);
      if (saveFormat) {
        await maybePromise(saveFormat.call(saveAs, entry, {}, asCopy));
        return serializeDocument(document);
      }
      const directSaveAs = property(document, "saveAs");
      if (directSaveAs) {
        await maybePromise(directSaveAs.call(document, entry, { format }, asCopy));
        return serializeDocument(document);
      }
      unavailable(`Photoshop document.saveAs.${format}`);
    });
  }
  function requestPayload(request) {
    const payload = request.args?.[0];
    return isObject(payload) ? payload : {};
  }
  function normalizeFormat(format) {
    const normalized = format.toLowerCase();
    return normalized === "jpeg" ? "jpg" : normalized;
  }
  async function fileEntry(path) {
    const localFileSystem = property(property(uxpModule(), "storage"), "localFileSystem");
    const createEntryWithUrl = property(localFileSystem, "createEntryWithUrl");
    if (createEntryWithUrl) {
      try {
        return await maybePromise(createEntryWithUrl.call(localFileSystem, toFileUrl(path), { type: "file", overwrite: true }));
      } catch {
      }
    }
    const getFileForSaving = property(localFileSystem, "getFileForSaving");
    if (getFileForSaving) return await maybePromise(getFileForSaving.call(localFileSystem, fileName(path)));
    return path;
  }
  async function withModal(request, defaultCommandName, work) {
    const options = request.options ?? {};
    const shouldUseModal = options.modal === true || typeof options.commandName === "string";
    if (!shouldUseModal) return work();
    const core = property(photoshopModule(), "core");
    const executeAsModal = property(core, "executeAsModal");
    if (!executeAsModal) unavailable("Photoshop core.executeAsModal");
    const commandName = asString(options.commandName) ?? defaultCommandName;
    return await maybePromise(executeAsModal.call(core, () => work(), { commandName }));
  }

  // bridges/uxp/photoshop/src/main.ts
  connectBridge(photoshopAdapter);
})();
//# sourceMappingURL=main.js.map
