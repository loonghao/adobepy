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
  async function evalJavaScript(source, args) {
    try {
      return await (0, eval)(source);
    } catch (error) {
      if (!(error instanceof SyntaxError)) throw error;
      const fn = new Function("args", source);
      return await fn(args);
    }
  }

  // bridges/uxp/indesign/src/host.ts
  var indesignAdapter = {
    capabilities() {
      return {
        host: "indesign",
        bridgeKind: "uxp",
        bridgeVersion: "0.1.0",
        hostVersion: indesignVersion(),
        namespaces: ["app", "document", "raw"],
        features: ["dom"],
        methods: { app: ["getVersion"], document: ["getActive"], raw: ["evalJs"] }
      };
    },
    async dispatch(request) {
      if (request.namespace === "app" && request.method === "getVersion") return indesignVersion();
      if (request.namespace === "document" && request.method === "getActive") return serializeDocument(property(indesignApp(), "activeDocument"));
      if (request.namespace === "raw" && request.method === "evalJs") return evalJavaScript(asString(request.args?.[0]) ?? "", request.args?.slice(1) ?? []);
      methodNotFound(request.namespace, request.method);
    }
  };
  function indesignModule() {
    return optionalRequire("indesign") ?? globalThis.indesign ?? {};
  }
  function indesignApp() {
    return property(indesignModule(), "app") ?? globalThis.app ?? {};
  }
  function indesignVersion() {
    const app = indesignApp();
    return asString(property(app, "version")) ?? asString(property(property(app, "scriptPreferences"), "version")) ?? "unknown";
  }
  function serializeDocument(document) {
    if (!isObject(document)) return null;
    return {
      id: property(document, "id"),
      name: asString(property(document, "name")),
      path: asString(property(property(document, "fullName"), "fsName")) ?? asString(property(document, "path")),
      width: asNumber(property(document, "width")) ?? property(document, "width"),
      height: asNumber(property(document, "height")) ?? property(document, "height")
    };
  }

  // bridges/uxp/indesign/src/main.ts
  connectBridge(indesignAdapter);
})();
//# sourceMappingURL=main.js.map
