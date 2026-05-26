import { startCepBridge } from "../../core/src/rpc";

startCepBridge({
  host: "after-effects",
  brokerUrl: (globalThis as any).__ADOBEPY_BROKER_URL || "ws://127.0.0.1:47391/v1/bridge/after-effects/ws",
  token: (globalThis as any).__ADOBEPY_TOKEN || "dev-token",
  target: (globalThis as any).__ADOBEPY_TARGET || "default",
  capabilities: {
    host: "after-effects",
    bridgeKind: "cep",
    bridgeVersion: "0.1.0",
    namespaces: ["app", "project", "raw"],
    features: ["extendscript", "projectInfo"],
    methods: { app: ["getVersion"], project: ["getActive"], raw: ["evalExtendScript"] }
  }
});
