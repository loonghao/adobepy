function adobepyDispatch(payload) {
  var request = JSON.parse(payload);
  try {
    if (request.namespace === "app" && request.method === "getVersion") {
      return adobepyResult(request.id, String(app.version || ""));
    }
    if (request.namespace === "project" && request.method === "getActive") {
      return adobepyResult(request.id, adobepyAfterEffectsProject(app.project));
    }
    if (request.namespace === "project" && request.method === "getItems") {
      return adobepyResult(request.id, adobepyAfterEffectsItems(app.project));
    }
    if (request.namespace === "project" && request.method === "getCompositions") {
      return adobepyResult(request.id, adobepyAfterEffectsItemsByType(app.project, "composition"));
    }
    if (request.namespace === "project" && request.method === "getFootageItems") {
      return adobepyResult(request.id, adobepyAfterEffectsItemsByType(app.project, "footage"));
    }
    if (request.namespace === "project" && request.method === "getFolders") {
      return adobepyResult(request.id, adobepyAfterEffectsItemsByType(app.project, "folder"));
    }
    if (request.namespace === "project" && request.method === "getActiveItem") {
      return adobepyResult(request.id, adobepyAfterEffectsItem(app.project && app.project.activeItem, app.project));
    }
    if (request.namespace === "project" && request.method === "getSelectedItems") {
      return adobepyResult(request.id, adobepyAfterEffectsSelectedItems(app.project));
    }
    if (request.namespace === "item" && request.method === "getById") {
      return adobepyResult(request.id, adobepyAfterEffectsItem(adobepyAfterEffectsFindItemById(app.project, (request.args || [])[0]), app.project));
    }
    if (request.namespace === "item" && request.method === "getByName") {
      return adobepyResult(request.id, adobepyAfterEffectsItemsByName(app.project, String((request.args || [])[0] || "")));
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

function adobepyAfterEffectsItems(project) {
  var result = [];
  if (!project) return result;
  for (var index = 1; index <= Number(project.numItems || 0); index += 1) {
    var item = project.item(index);
    var serialized = adobepyAfterEffectsItem(item, project, index);
    if (serialized) result.push(serialized);
  }
  return result;
}

function adobepyAfterEffectsItemsByType(project, itemType) {
  var items = adobepyAfterEffectsItems(project);
  var result = [];
  for (var index = 0; index < items.length; index += 1) {
    if (items[index].itemType === itemType) result.push(items[index]);
  }
  return result;
}

function adobepyAfterEffectsSelectedItems(project) {
  var items = adobepyAfterEffectsItems(project);
  var result = [];
  for (var index = 0; index < items.length; index += 1) {
    if (items[index].selected === true) result.push(items[index]);
  }
  return result;
}

function adobepyAfterEffectsItemsByName(project, name) {
  var items = adobepyAfterEffectsItems(project);
  var result = [];
  for (var index = 0; index < items.length; index += 1) {
    if (items[index].name === name) result.push(items[index]);
  }
  return result;
}

function adobepyAfterEffectsFindItemById(project, id) {
  if (!project) return null;
  for (var index = 1; index <= Number(project.numItems || 0); index += 1) {
    var item = project.item(index);
    if (String(adobepySafeValue(item, "id")) === String(id)) return item;
  }
  return null;
}

function adobepyAfterEffectsItem(item, project, index) {
  if (!item) return null;
  var parent = adobepySafeValue(item, "parentFolder");
  var source = adobepySafeValue(item, "mainSource");
  var sourceFile = source ? adobepySafeValue(source, "file") : null;
  var file = adobepySafeValue(item, "file") || sourceFile;
  var itemType = adobepyAfterEffectsItemType(item);
  var missingFootage = adobepySafeValue(item, "footageMissing");
  if (typeof missingFootage === "undefined") missingFootage = adobepySafeValue(source, "missingFootage");
  return {
    id: adobepySafeValue(item, "id"),
    index: typeof index === "number" ? index : adobepyAfterEffectsItemIndex(project, item),
    name: String(adobepySafeValue(item, "name") || ""),
    typeName: String(adobepySafeValue(item, "typeName") || ""),
    itemType: itemType,
    parentFolderId: parent ? adobepySafeValue(parent, "id") : null,
    parentFolderName: parent ? String(adobepySafeValue(parent, "name") || "") : null,
    selected: Boolean(adobepySafeValue(item, "selected")),
    isActive: Boolean(project && project.activeItem === item),
    width: adobepyNumberOrNull(adobepySafeValue(item, "width")),
    height: adobepyNumberOrNull(adobepySafeValue(item, "height")),
    duration: adobepyNumberOrNull(adobepySafeValue(item, "duration")),
    frameRate: adobepyNumberOrNull(adobepySafeValue(item, "frameRate")),
    hasVideo: adobepyBooleanOrNull(adobepySafeValue(item, "hasVideo")),
    hasAudio: adobepyBooleanOrNull(adobepySafeValue(item, "hasAudio")),
    filePath: file ? String(adobepySafeValue(file, "fsName") || adobepySafeValue(file, "fullName") || "") : null,
    missingFootage: adobepyBooleanOrNull(missingFootage),
    itemCount: adobepyNumberOrNull(adobepySafeValue(item, "numItems")),
    numLayers: adobepyNumberOrNull(adobepySafeValue(item, "numLayers")),
    workAreaStart: adobepyNumberOrNull(adobepySafeValue(item, "workAreaStart")),
    workAreaDuration: adobepyNumberOrNull(adobepySafeValue(item, "workAreaDuration")),
    typename: itemType === "composition" ? "CompItem" : itemType === "footage" ? "FootageItem" : itemType === "folder" ? "FolderItem" : "Item"
  };
}

function adobepyAfterEffectsItemType(item) {
  var typeName = String(adobepySafeValue(item, "typeName") || "").toLowerCase();
  if (typeName.indexOf("composition") >= 0 || typeof adobepySafeValue(item, "numLayers") !== "undefined") return "composition";
  if (typeName.indexOf("footage") >= 0 || adobepySafeValue(item, "mainSource")) return "footage";
  if (typeName.indexOf("folder") >= 0 || typeof adobepySafeValue(item, "numItems") !== "undefined") return "folder";
  return typeName || "item";
}

function adobepyAfterEffectsItemIndex(project, item) {
  if (!project || !item) return null;
  for (var index = 1; index <= Number(project.numItems || 0); index += 1) {
    if (project.item(index) === item) return index;
  }
  return null;
}

function adobepySafeValue(object, key) {
  try {
    return object ? object[key] : undefined;
  } catch (error) {
    return undefined;
  }
}

function adobepyNumberOrNull(value) {
  return typeof value === "undefined" || value === null || isNaN(Number(value)) ? null : Number(value);
}

function adobepyBooleanOrNull(value) {
  if (typeof value === "undefined" || value === null) return null;
  return Boolean(value);
}

function adobepyResult(id, value) {
  return JSON.stringify({ jsonrpc: "2.0", id: id, result: typeof value === "undefined" ? null : value });
}

function adobepyError(id, code, message, data) {
  var response = { jsonrpc: "2.0", id: id, error: { code: code, message: message } };
  if (data) response.error.data = data;
  return JSON.stringify(response);
}
