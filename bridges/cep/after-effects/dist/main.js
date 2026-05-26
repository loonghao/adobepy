"use strict";
(() => {
  // bridges/cep/core/src/rpc.ts
  function startCepBridge(config) {
    const socket = new WebSocket(config.brokerUrl);
    const cs = new CSInterface();
    socket.addEventListener("open", () => {
      socket.send(JSON.stringify({ type: "hello", token: config.token, target: config.target, capabilities: config.capabilities }));
      console.log("adobepy CEP bridge connected", config.capabilities);
    });
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      if (message.type !== "request") return;
      const request = message.request;
      const encoded = encodeURIComponent(JSON.stringify(request)).replace(/'/g, "%27");
      try {
        cs.evalScript(`adobepyDispatch(decodeURIComponent('${encoded}'))`, (raw) => {
          var _a;
          try {
            const parsed = raw ? JSON.parse(raw) : { jsonrpc: "2.0", id: request.id, result: null };
            if (parsed.error) {
              socket.send(JSON.stringify({ type: "error", error: { ...parsed, id: (_a = parsed.id) != null ? _a : request.id } }));
              return;
            }
            if (!Object.prototype.hasOwnProperty.call(parsed, "result")) parsed.result = null;
            socket.send(JSON.stringify({ type: "response", response: parsed }));
          } catch (error) {
            socket.send(JSON.stringify({ type: "error", error: hostScriptError(request.id, error) }));
          }
        });
      } catch (error) {
        socket.send(JSON.stringify({ type: "error", error: hostScriptError(request.id, error) }));
      }
    });
  }
  function hostScriptError(id, error) {
    return { jsonrpc: "2.0", id, error: { code: -32004, message: (error == null ? void 0 : error.message) || String(error) } };
  }

  // bridges/cep/after-effects/src/main.ts
  startCepBridge({
    host: "after-effects",
    brokerUrl: globalThis.__ADOBEPY_BROKER_URL || "ws://127.0.0.1:47391/v1/bridge/after-effects/ws",
    token: globalThis.__ADOBEPY_TOKEN || "dev-token",
    target: globalThis.__ADOBEPY_TARGET || "default",
    capabilities: {
      host: "after-effects",
      bridgeKind: "cep",
      bridgeVersion: "0.1.0",
      namespaces: ["app", "project", "raw"],
      features: ["extendscript", "projectInfo"],
      methods: { app: ["getVersion"], project: ["getActive"], raw: ["evalExtendScript"] }
    }
  });
})();
//# sourceMappingURL=main.js.map
