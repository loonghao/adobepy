function adobepyDispatch(payload) {
  var request = JSON.parse(payload);
  try {
    if (request.namespace === "app" && request.method === "getVersion") {
      return adobepyResult(request.id, String(app.version || ""));
    }
    if (request.namespace === "project" && request.method === "getActive") {
      return adobepyResult(request.id, adobepyAfterEffectsProject(app.project));
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

function adobepyAfterEffectsProject(project) {
  if (!project) return null;
  var file = project.file || null;
  return {
    name: file ? String(file.name || "") : "Untitled Project",
    path: file ? String(file.fsName || file.fullName || "") : null,
    itemCount: Number(project.numItems || 0)
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
