import { methodNotFound } from "../../core/src/errors";
import type { HostAdapter } from "../../core/src/host-adapter";
import type { RpcRequest } from "../../core/src/protocol";
import { asNumber, asString, evalJavaScript, isObject, maybePromise, optionalRequire, property } from "../../core/src/runtime";

type Callable = (...args: unknown[]) => unknown;

export const premiereAdapter: HostAdapter = {
  capabilities() {
    return {
      host: "premiere",
      bridgeKind: "uxp",
      bridgeVersion: "0.1.0",
      hostVersion: premiereVersion(),
      namespaces: ["app", "project", "raw"],
      features: ["project"],
      methods: { app: ["getVersion"], project: ["getActive"], raw: ["evalJs"] }
    };
  },
  async dispatch(request: RpcRequest) {
    if (request.namespace === "app" && request.method === "getVersion") return premiereVersion();
    if (request.namespace === "project" && request.method === "getActive") return serializeProject(await activeProject());
    if (request.namespace === "raw" && request.method === "evalJs") return evalJavaScript(asString(request.args?.[0]) ?? "", request.args?.slice(1) ?? []);
    methodNotFound(request.namespace, request.method);
  }
};

function premiereModule() {
  return optionalRequire("premierepro") ?? (globalThis as { premierepro?: Record<string, unknown> }).premierepro ?? {};
}

function uxpModule() {
  return optionalRequire("uxp") ?? (globalThis as { uxp?: Record<string, unknown> }).uxp ?? {};
}

function premiereVersion(): string {
  const premiere = premiereModule();
  const host = property(uxpModule(), "host");
  return asString(property(premiere, "version")) ?? asString(property(host, "version")) ?? "unknown";
}

async function activeProject() {
  const premiere = premiereModule();
  const projectApi = property(premiere, "Project");
  const getActiveProject = property<Callable>(projectApi, "getActiveProject") ?? property<Callable>(projectApi, "getActive");
  if (getActiveProject) return await maybePromise(getActiveProject.call(projectApi));
  return property(premiere, "project") ?? property(property(premiere, "app"), "project");
}

function serializeProject(project: unknown) {
  if (!isObject(project)) return null;
  return {
    id: property(project, "guid") ?? property(project, "id"),
    guid: property(project, "guid"),
    name: asString(property(project, "name")),
    path: asString(property(project, "path")),
    itemCount: asNumber(property(project, "itemCount")) ?? asNumber(property(project, "numItems"))
  };
}
