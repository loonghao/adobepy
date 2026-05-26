import { methodNotFound, unavailable } from "../../core/src/errors";
import type { HostAdapter } from "../../core/src/host-adapter";
import type { RpcRequest } from "../../core/src/protocol";
import { asArray, asNumber, asString, evalJavaScript, isObject, maybePromise, optionalRequire, property } from "../../core/src/runtime";

export const indesignAdapter: HostAdapter = {
  capabilities() {
    return {
      host: "indesign",
      bridgeKind: "uxp",
      bridgeVersion: "0.1.0",
      hostVersion: indesignVersion(),
      namespaces: ["app", "document", "page", "spread", "raw"],
      features: ["dom"],
      methods: {
        app: ["getVersion"],
        document: ["getActive"],
        page: ["getPages", "getActive", "getByName", "select"],
        spread: ["getSpreads", "getActive", "getByName"],
        raw: ["evalJs"]
      }
    };
  },
  async dispatch(request: RpcRequest) {
    if (request.namespace === "app" && request.method === "getVersion") return indesignVersion();
    if (request.namespace === "document" && request.method === "getActive") return serializeDocument(activeDocument());
    if (request.namespace === "page" && request.method === "getPages") return documentPages(request);
    if (request.namespace === "page" && request.method === "getActive") return serializePage(activePage(request.args?.[0]));
    if (request.namespace === "page" && request.method === "getByName") return serializePage(findPage(request.args?.[0], request.args?.[1]));
    if (request.namespace === "page" && request.method === "select") return pageSelect(request);
    if (request.namespace === "spread" && request.method === "getSpreads") return documentSpreads(request);
    if (request.namespace === "spread" && request.method === "getActive") return serializeSpread(activeSpread(request.args?.[0]));
    if (request.namespace === "spread" && request.method === "getByName") return serializeSpread(findSpread(request.args?.[0], request.args?.[1]));
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

function activeDocument() {
  return property(indesignApp(), "activeDocument");
}

function openDocuments() {
  return asArray(property(indesignApp(), "documents"));
}

function findDocument(id: unknown) {
  const active = activeDocument();
  if (id === undefined || id === null) return active;
  const match = openDocuments().find((document) => String(property(document, "id")) === String(id));
  return match ?? (String(property(active, "id")) === String(id) ? active : undefined);
}

function serializeDocument(document: unknown) {
  if (!isObject(document)) return null;
  const pages = asArray(property(document, "pages"));
  const spreads = asArray(property(document, "spreads"));
  return {
    id: property(document, "id"),
    name: asString(property(document, "name")),
    path: asString(property(property(document, "fullName"), "fsName")) ?? asString(property(document, "path")),
    width: asNumber(property(document, "width")) ?? property(document, "width"),
    height: asNumber(property(document, "height")) ?? property(document, "height"),
    pageCount: pages.length,
    spreadCount: spreads.length,
    typename: asString(property(document, "typename"))
  };
}

function serializePage(page: unknown) {
  if (!isObject(page)) return null;
  const parent = property(page, "parent");
  return {
    id: property(page, "id"),
    name: asString(property(page, "name")),
    index: asNumber(property(page, "index")) ?? property(page, "index"),
    documentOffset: asNumber(property(page, "documentOffset")) ?? property(page, "documentOffset"),
    side: asString(property(page, "side")) ?? property(page, "side"),
    bounds: serializeBounds(property(page, "bounds")),
    parentId: property(parent, "id"),
    parentName: asString(property(parent, "name")),
    isValid: property(page, "isValid"),
    typename: asString(property(page, "typename"))
  };
}

function serializeSpread(spread: unknown) {
  if (!isObject(spread)) return null;
  const parent = property(spread, "parent");
  const pages = asArray(property(spread, "pages"));
  return {
    id: property(spread, "id"),
    name: asString(property(spread, "name")),
    label: asString(property(spread, "label")),
    index: asNumber(property(spread, "index")) ?? property(spread, "index"),
    pageCount: pages.length,
    pageNames: pages.map((page) => asString(property(page, "name"))).filter((name) => name !== undefined),
    parentId: property(parent, "id"),
    parentName: asString(property(parent, "name")),
    isValid: property(spread, "isValid"),
    typename: asString(property(spread, "typename"))
  };
}

function serializeBounds(bounds: unknown) {
  return asArray(bounds).map((value) => asNumber(value) ?? value);
}

function documentPages(request: RpcRequest) {
  const document = findDocument(request.args?.[0]);
  if (!document) return [];
  return asArray(property(document, "pages")).map(serializePage).filter((page) => page !== null);
}

function documentSpreads(request: RpcRequest) {
  const document = findDocument(request.args?.[0]);
  if (!document) return [];
  return asArray(property(document, "spreads")).map(serializeSpread).filter((spread) => spread !== null);
}

function activePage(documentId: unknown) {
  const activeWindow = property(indesignApp(), "activeWindow");
  const page = property(activeWindow, "activePage");
  if (page) return page;
  const document = findDocument(documentId);
  return asArray(property(document, "pages"))[0];
}

function activeSpread(documentId: unknown) {
  const activeWindow = property(indesignApp(), "activeWindow");
  const spread = property(activeWindow, "activeSpread");
  if (spread) return spread;
  const pageParent = property(activePage(documentId), "parent");
  if (pageParent) return pageParent;
  const document = findDocument(documentId);
  return asArray(property(document, "spreads"))[0];
}

function findPage(documentId: unknown, idOrName: unknown) {
  if (idOrName === undefined || idOrName === null) return activePage(documentId);
  const document = findDocument(documentId);
  const pages = property(document, "pages");
  const byName = property<(...args: unknown[]) => unknown>(pages, "itemByName");
  if (byName && typeof idOrName === "string") {
    try {
      const page = byName.call(pages, idOrName);
      if (page) return page;
    } catch {
      // Continue with manual matching when the host throws for a missing page.
    }
  }
  return asArray(pages).find((page) => String(property(page, "id")) === String(idOrName) || asString(property(page, "name")) === String(idOrName));
}

function findSpread(documentId: unknown, idOrName: unknown) {
  if (idOrName === undefined || idOrName === null) return activeSpread(documentId);
  const document = findDocument(documentId);
  const spreads = property(document, "spreads");
  const byName = property<(...args: unknown[]) => unknown>(spreads, "itemByName");
  if (byName && typeof idOrName === "string") {
    try {
      const spread = byName.call(spreads, idOrName);
      if (spread) return spread;
    } catch {
      // Continue with manual matching when the host throws for a missing spread.
    }
  }
  return asArray(spreads).find((spread) => String(property(spread, "id")) === String(idOrName) || asString(property(spread, "name")) === String(idOrName));
}

async function pageSelect(request: RpcRequest) {
  const page = findPage(request.args?.[0], request.args?.[1]);
  if (!page) unavailable("InDesign page");
  const select = property<(...args: unknown[]) => unknown>(page, "select");
  if (!select) unavailable("InDesign page.select");
  await maybePromise(select.call(page, request.args?.[2]));
  return serializePage(page);
}
