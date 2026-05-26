import { startCepBridge } from "../../core/src/rpc";

startCepBridge({
  host: "illustrator",
  brokerUrl: (globalThis as any).__ADOBEPY_BROKER_URL || "ws://127.0.0.1:47391/v1/bridge/illustrator/ws",
  token: (globalThis as any).__ADOBEPY_TOKEN || "dev-token",
  target: (globalThis as any).__ADOBEPY_TARGET || "default",
  capabilities: {
    host: "illustrator",
    bridgeKind: "cep",
    bridgeVersion: "0.1.0",
    namespaces: ["app", "document", "raw"],
    features: ["extendscript"],
    methods: { app: ["getVersion"], document: ["getActive"], raw: ["evalExtendScript"] }
  }
});
