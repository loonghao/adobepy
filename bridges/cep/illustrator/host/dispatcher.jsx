function adobepyDispatch(payload) {
  var request = JSON.parse(payload);
  try {
    if (request.namespace === "app" && request.method === "getVersion") {
      return adobepyResult(request.id, String(app.version || ""));
    }
    if (request.namespace === "document" && request.method === "getActive") {
      return adobepyResult(request.id, adobepyIllustratorDocument());
    }
    if (request.namespace === "raw" && request.method === "evalExtendScript") {
      return adobepyResult(request.id, eval((request.args || [])[0]));
    }
    return adobepyError(request.id, -32601, "unsupported method " + request.namespace + "." + request.method);
  } catch (error) {
    return adobepyError(request.id, -32004, error && error.message ? error.message : String(error), {
      line: error && error.line,
      source: error && error.source
    });
  }
}

function adobepyIllustratorDocument() {
  if (!app.documents || app.documents.length === 0) return null;
  var document = app.activeDocument;
  var path = null;
  try {
    path = document.fullName ? String(document.fullName.fsName || document.fullName) : null;
  } catch (_) {
    path = null;
  }
  return {
    name: String(document.name || ""),
    path: path,
    width: Number(document.width || 0),
    height: Number(document.height || 0)
  };
}

function adobepyResult(id, value) {
  return JSON.stringify({ jsonrpc: "2.0", id: id, result: typeof value === "undefined" ? null : value });
}

function adobepyError(id, code, message, data) {
  var response = { jsonrpc: "2.0", id: id, error: { code: code, message: message } };
  if (data) response.error.data = data;
  return JSON.stringify(response);
}
