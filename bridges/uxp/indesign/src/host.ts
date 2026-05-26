import { methodNotFound } from "../../core/src/errors";
import type { HostAdapter } from "../../core/src/host-adapter";
import type { RpcRequest } from "../../core/src/protocol";
import { asNumber, asString, evalJavaScript, isObject, optionalRequire, property } from "../../core/src/runtime";

export const indesignAdapter: HostAdapter = {
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
  async dispatch(request: RpcRequest) {
    if (request.namespace === "app" && request.method === "getVersion") return indesignVersion();
    if (request.namespace === "document" && request.method === "getActive") return serializeDocument(property(indesignApp(), "activeDocument"));
    if (request.namespace === "raw" && request.method === "evalJs") return evalJavaScript(asString(request.args?.[0]) ?? "", request.args?.slice(1) ?? []);
    methodNotFound(request.namespace, request.method);
  }
};

function indesignModule() {
  return optionalRequire("indesign") ?? (globalThis as { indesign?: Record<string, unknown> }).indesign ?? {};
}

function indesignApp() {
  return property(indesignModule(), "app") ?? (globalThis as { app?: Record<string, unknown> }).app ?? {};
}

function indesignVersion(): string {
  const app = indesignApp();
  return (
    asString(property(app, "version")) ??
    asString(property(property(app, "scriptPreferences"), "version")) ??
    "unknown"
  );
}

function serializeDocument(document: unknown) {
  if (!isObject(document)) return null;
  return {
    id: property(document, "id"),
    name: asString(property(document, "name")),
    path: asString(property(property(document, "fullName"), "fsName")) ?? asString(property(document, "path")),
    width: asNumber(property(document, "width")) ?? property(document, "width"),
    height: asNumber(property(document, "height")) ?? property(document, "height")
  };
}
