function adobepyDispatch(payload) {
  var request = JSON.parse(payload);
  try {
    if (request.namespace === "app" && request.method === "getVersion") {
      return adobepyResult(request.id, String(app.version || ""));
    }
    if (request.namespace === "document" && request.method === "getActive") {
      return adobepyResult(request.id, adobepyIllustratorDocument());
    }
    if (request.namespace === "artboard" && request.method === "getArtboards") {
      return adobepyResult(request.id, adobepyIllustratorArtboards(adobepyIllustratorActiveDocument()));
    }
    if (request.namespace === "artboard" && request.method === "getActive") {
      return adobepyResult(request.id, adobepyIllustratorActiveArtboard(adobepyIllustratorActiveDocument()));
    }
    if (request.namespace === "artboard" && request.method === "getActiveIndex") {
      return adobepyResult(request.id, adobepyIllustratorActiveArtboardIndex(adobepyIllustratorActiveDocument()));
    }
    if (request.namespace === "layer" && request.method === "getLayers") {
      return adobepyResult(request.id, adobepyIllustratorLayers(adobepyIllustratorActiveDocument()));
    }
    if (request.namespace === "layer" && request.method === "getByName") {
      return adobepyResult(request.id, adobepyIllustratorLayerByName(adobepyIllustratorActiveDocument(), String((request.args || [])[0] || "")));
    }
    if (request.namespace === "layer" && request.method === "getChildren") {
      return adobepyResult(request.id, adobepyIllustratorLayerChildren(adobepyIllustratorActiveDocument(), (request.args || [])[0]));
    }
    if (request.namespace === "pageItem" && request.method === "getPageItems") {
      return adobepyResult(request.id, adobepyIllustratorPageItems(adobepyIllustratorActiveDocument()));
    }
    if (request.namespace === "pageItem" && request.method === "getSelected") {
      return adobepyResult(request.id, adobepyIllustratorSelectedPageItems(adobepyIllustratorActiveDocument()));
    }
    if (request.namespace === "pageItem" && request.method === "getByName") {
      return adobepyResult(request.id, adobepyIllustratorPageItemByName(adobepyIllustratorActiveDocument(), String((request.args || [])[0] || "")));
    }
    if (request.namespace === "pageItem" && request.method === "getLayerItems") {
      return adobepyResult(request.id, adobepyIllustratorLayerPageItems(adobepyIllustratorActiveDocument(), (request.args || [])[0]));
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
  var document = adobepyIllustratorActiveDocument();
  if (!document) return null;
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
    height: Number(document.height || 0),
    artboardCount: adobepyCollectionLength(document.artboards),
    layerCount: adobepyCollectionLength(document.layers),
    pageItemCount: adobepyCollectionLength(document.pageItems),
    selectionCount: adobepyIllustratorSelectedPageItems(document).length,
    typename: "Document"
  };
}

function adobepyIllustratorActiveDocument() {
  if (!app.documents || app.documents.length === 0) return null;
  return app.activeDocument;
}

function adobepyIllustratorArtboards(document) {
  var result = [];
  var artboards = document ? document.artboards : null;
  var count = adobepyCollectionLength(artboards);
  for (var index = 0; index < count; index += 1) {
    result.push(adobepyIllustratorArtboard(adobepyCollectionItem(artboards, index), index));
  }
  return result;
}

function adobepyIllustratorActiveArtboard(document) {
  if (!document) return null;
  var index = adobepyIllustratorActiveArtboardIndex(document);
  var artboards = document.artboards;
  return index === null ? null : adobepyIllustratorArtboard(adobepyCollectionItem(artboards, index), index);
}

function adobepyIllustratorActiveArtboardIndex(document) {
  if (!document || !document.artboards) return null;
  try {
    if (typeof document.artboards.getActiveArtboardIndex === "function") return Number(document.artboards.getActiveArtboardIndex());
  } catch (_) {
    return null;
  }
  return 0;
}

function adobepyIllustratorArtboard(artboard, index) {
  if (!artboard) return null;
  return {
    index: index,
    name: adobepyStringOrNull(adobepySafeValue(artboard, "name")),
    artboardRect: adobepyArrayValue(adobepySafeValue(artboard, "artboardRect")),
    rulerOrigin: adobepyArrayValue(adobepySafeValue(artboard, "rulerOrigin")),
    rulerPAR: adobepySafeValue(artboard, "rulerPAR"),
    showCenter: adobepyBooleanOrNull(adobepySafeValue(artboard, "showCenter")),
    showCrossHairs: adobepyBooleanOrNull(adobepySafeValue(artboard, "showCrossHairs")),
    showSafeAreas: adobepyBooleanOrNull(adobepySafeValue(artboard, "showSafeAreas")),
    typename: "Artboard"
  };
}

function adobepyIllustratorLayers(document) {
  return adobepyIllustratorLayerCollection(document ? document.layers : null, null);
}

function adobepyIllustratorLayerChildren(document, layerKey) {
  var layer = adobepyIllustratorFindLayer(document, layerKey);
  return adobepyIllustratorLayerCollection(layer ? layer.layers : null, layer);
}

function adobepyIllustratorLayerCollection(layers, parent) {
  var result = [];
  var count = adobepyCollectionLength(layers);
  for (var index = 0; index < count; index += 1) {
    result.push(adobepyIllustratorLayer(adobepyCollectionItem(layers, index), index, parent));
  }
  return result;
}

function adobepyIllustratorLayerByName(document, name) {
  return adobepyIllustratorLayer(adobepyIllustratorFindLayer(document, name), null, null);
}

function adobepyIllustratorFindLayer(document, key) {
  if (!document) return null;
  var queue = [];
  var topLayers = document.layers;
  var topCount = adobepyCollectionLength(topLayers);
  for (var index = 0; index < topCount; index += 1) queue.push(adobepyCollectionItem(topLayers, index));
  while (queue.length > 0) {
    var layer = queue.shift();
    if (!layer) continue;
    var values = [adobepySafeValue(layer, "id"), adobepySafeValue(layer, "name"), adobepySafeValue(layer, "zOrderPosition")];
    for (var valueIndex = 0; valueIndex < values.length; valueIndex += 1) {
      if (String(values[valueIndex]) === String(key)) return layer;
    }
    var children = adobepySafeValue(layer, "layers");
    var childCount = adobepyCollectionLength(children);
    for (var childIndex = 0; childIndex < childCount; childIndex += 1) queue.push(adobepyCollectionItem(children, childIndex));
  }
  return null;
}

function adobepyIllustratorLayer(layer, index, parent) {
  if (!layer) return null;
  var actualParent = parent || adobepySafeValue(layer, "parent");
  return {
    id: adobepySafeValue(layer, "id") || adobepySafeValue(layer, "uuid") || adobepySafeValue(layer, "name") || index,
    index: typeof index === "number" ? index : adobepyNumberOrNull(adobepySafeValue(layer, "zOrderPosition")),
    name: adobepyStringOrNull(adobepySafeValue(layer, "name")),
    visible: adobepyBooleanOrNull(adobepySafeValue(layer, "visible")),
    locked: adobepyBooleanOrNull(adobepySafeValue(layer, "locked")),
    printable: adobepyBooleanOrNull(adobepySafeValue(layer, "printable")),
    preview: adobepyBooleanOrNull(adobepySafeValue(layer, "preview")),
    opacity: adobepyNumberOrNull(adobepySafeValue(layer, "opacity")),
    hasSelectedArtwork: adobepyBooleanOrNull(adobepySafeValue(layer, "hasSelectedArtwork")),
    parentName: actualParent ? adobepyStringOrNull(adobepySafeValue(actualParent, "name")) : null,
    parentTypename: actualParent ? adobepyStringOrNull(adobepySafeValue(actualParent, "typename")) : null,
    layerCount: adobepyCollectionLength(adobepySafeValue(layer, "layers")),
    pageItemCount: adobepyCollectionLength(adobepySafeValue(layer, "pageItems")),
    typename: "Layer"
  };
}

function adobepyIllustratorPageItems(document) {
  return adobepyIllustratorPageItemCollection(document ? document.pageItems : null);
}

function adobepyIllustratorSelectedPageItems(document) {
  return adobepyIllustratorPageItemCollection(document ? document.selection : null);
}

function adobepyIllustratorLayerPageItems(document, layerKey) {
  var layer = adobepyIllustratorFindLayer(document, layerKey);
  return adobepyIllustratorPageItemCollection(layer ? layer.pageItems : null);
}

function adobepyIllustratorPageItemByName(document, name) {
  var items = adobepyIllustratorPageItems(document);
  for (var index = 0; index < items.length; index += 1) {
    if (items[index].name === name) return items[index];
  }
  return null;
}

function adobepyIllustratorPageItemCollection(items) {
  var result = [];
  var count = adobepyCollectionLength(items);
  for (var index = 0; index < count; index += 1) {
    var item = adobepyCollectionItem(items, index);
    if (item) result.push(adobepyIllustratorPageItem(item, index));
  }
  return result;
}

function adobepyIllustratorPageItem(item, index) {
  if (!item) return null;
  var parent = adobepySafeValue(item, "parent");
  var layer = adobepySafeValue(item, "layer");
  return {
    id: adobepySafeValue(item, "uuid") || adobepySafeValue(item, "id") || adobepySafeValue(item, "name") || index,
    index: index,
    name: adobepyStringOrNull(adobepySafeValue(item, "name")),
    itemType: adobepyStringOrNull(adobepySafeValue(item, "typename")),
    hidden: adobepyBooleanOrNull(adobepySafeValue(item, "hidden")),
    locked: adobepyBooleanOrNull(adobepySafeValue(item, "locked")),
    selected: adobepyBooleanOrNull(adobepySafeValue(item, "selected")),
    editable: adobepyBooleanOrNull(adobepySafeValue(item, "editable")),
    sliced: adobepyBooleanOrNull(adobepySafeValue(item, "sliced")),
    position: adobepyArrayValue(adobepySafeValue(item, "position")),
    geometricBounds: adobepyArrayValue(adobepySafeValue(item, "geometricBounds")),
    visibleBounds: adobepyArrayValue(adobepySafeValue(item, "visibleBounds")),
    controlBounds: adobepyArrayValue(adobepySafeValue(item, "controlBounds")),
    width: adobepySafeValue(item, "width"),
    height: adobepySafeValue(item, "height"),
    opacity: adobepyNumberOrNull(adobepySafeValue(item, "opacity")),
    parentName: parent ? adobepyStringOrNull(adobepySafeValue(parent, "name")) : null,
    parentTypename: parent ? adobepyStringOrNull(adobepySafeValue(parent, "typename")) : null,
    layerName: layer ? adobepyStringOrNull(adobepySafeValue(layer, "name")) : null,
    note: adobepyStringOrNull(adobepySafeValue(item, "note")),
    url: adobepyStringOrNull(adobepySafeValue(item, "uRL") || adobepySafeValue(item, "url")),
    typename: adobepyStringOrNull(adobepySafeValue(item, "typename")) || "PageItem"
  };
}

function adobepyCollectionLength(value) {
  if (!value) return 0;
  var length = adobepyNumberOrNull(adobepySafeValue(value, "length"));
  if (length !== null) return length;
  return 0;
}

function adobepyCollectionItem(value, index) {
  if (!value) return null;
  if (typeof value[index] !== "undefined") return value[index];
  if (typeof value.item === "function") {
    try {
      return value.item(index);
    } catch (_) {
      try {
        return value.item(index + 1);
      } catch (ignored) {
        return null;
      }
    }
  }
  return null;
}

function adobepySafeValue(object, key) {
  try {
    return object ? object[key] : undefined;
  } catch (_) {
    return undefined;
  }
}

function adobepyArrayValue(value) {
  if (!value) return null;
  var result = [];
  var length = adobepyNumberOrNull(adobepySafeValue(value, "length"));
  if (length === null) return value;
  for (var index = 0; index < length; index += 1) result.push(value[index]);
  return result;
}

function adobepyNumberOrNull(value) {
  return typeof value === "undefined" || value === null || isNaN(Number(value)) ? null : Number(value);
}

function adobepyBooleanOrNull(value) {
  if (typeof value === "undefined" || value === null) return null;
  return Boolean(value);
}

function adobepyStringOrNull(value) {
  if (typeof value === "undefined" || value === null) return null;
  return String(value);
}

function adobepyResult(id, value) {
  return JSON.stringify({ jsonrpc: "2.0", id: id, result: typeof value === "undefined" ? null : value });
}

function adobepyError(id, code, message, data) {
  var response = { jsonrpc: "2.0", id: id, error: { code: code, message: message } };
  if (data) response.error.data = data;
  return JSON.stringify(response);
}
