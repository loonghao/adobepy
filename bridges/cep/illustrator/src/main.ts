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
    namespaces: ["app", "document", "artboard", "layer", "pageItem", "raw"],
    features: ["extendscript", "document", "artboards", "layers", "pageItems", "selection"],
    methods: {
      app: ["getVersion"],
      document: ["getActive"],
      artboard: ["getArtboards", "getActive", "getActiveIndex"],
      layer: ["getLayers", "getByName", "getChildren"],
      pageItem: ["getPageItems", "getSelected", "getByName", "getLayerItems"],
      raw: ["evalExtendScript"]
    }
  }
});
