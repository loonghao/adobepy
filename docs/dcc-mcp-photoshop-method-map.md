# dcc-mcp-photoshop Method Map

This table maps the legacy `dcc-mcp-photoshop` `ps.*` bridge dialect to the
stable `adobepy` facade and protocol surfaces. The machine-readable version is
`contracts/dcc_mcp_photoshop_methods.json`, and the regression test
`python/tests/test_dcc_mcp_photoshop_method_map.py` keeps this list covered.

Typed facades are preferred when `adobepy` has a stable host object. `batchPlay`
and DOM path escape hatches remain explicit for operations that are better
represented as Photoshop Action Manager descriptors or broad DOM reflection.

| Legacy method | adobepy route | Replacement |
| --- | --- | --- |
| `ps.getDocumentInfo` | typed facade | `Photoshop().activeDocument` / `active_document` |
| `ps.listDocuments` | typed facade | `Photoshop().documents` |
| `ps.createDocument` | DOM escape hatch | `Photoshop().dom.app.documents.add({...}, modal=True)` |
| `ps.saveDocument` | DOM escape hatch | `Photoshop().dom.app.activeDocument.save(modal=True)` |
| `ps.closeDocument` | DOM escape hatch | `Photoshop().dom.app.activeDocument.close(..., modal=True)` |
| `ps.exportDocument` | typed facade | `Photoshop().activeDocument.export(...)` or `export_with_preset(...)` |
| `ps.resizeCanvas` | DOM escape hatch | `Photoshop().dom.app.activeDocument.resizeCanvas(..., modal=True)` |
| `ps.resizeImage` | DOM escape hatch | `Photoshop().dom.app.activeDocument.resizeImage(..., modal=True)` |
| `ps.flattenImage` | DOM escape hatch | `Photoshop().dom.app.activeDocument.flatten(..., modal=True)` |
| `ps.mergeVisibleLayers` | DOM escape hatch | `Photoshop().dom.app.activeDocument.mergeVisibleLayers(..., modal=True)` |
| `ps.listLayers` | typed facade | `Photoshop().activeLayers` or `Photoshop().activeDocument.layers` |
| `ps.createLayer` | `batchPlay` | Action descriptor `make layer` through `Photoshop().batch_play(..., modal=True)` |
| `ps.deleteLayer` | `batchPlay` | Action descriptor `delete layer` through `Photoshop().batch_play(..., modal=True)` |
| `ps.setLayerVisibility` | `batchPlay` | Action descriptor `hide` / `show` through `Photoshop().batch_play(..., modal=True)` |
| `ps.renameLayer` | `batchPlay` | Action descriptor `set name` through `Photoshop().batch_play(..., modal=True)` |
| `ps.setLayerOpacity` | `batchPlay` | Action descriptor `set opacity` through `Photoshop().batch_play(..., modal=True)` |
| `ps.duplicateLayer` | `batchPlay` | Action descriptor `duplicate layer` through `Photoshop().batch_play(..., modal=True)` |
| `ps.setLayerBlendMode` | `batchPlay` | Action descriptor `set blend mode` through `Photoshop().batch_play(..., modal=True)` |
| `ps.fillLayer` | `batchPlay` | Action descriptor `fill` through `Photoshop().batch_play(..., modal=True)` |
| `ps.createTextLayer` | `batchPlay` | Action descriptor `make textLayer` through `Photoshop().batch_play(..., modal=True)` |
| `ps.updateTextLayer` | typed facade | `LayerProxy.textItem.set_contents(...)`, `set_character_style(...)`, `set_paragraph_style(...)` |
| `ps.getTextLayerInfo` | typed facade | `LayerProxy.textItem` or `Photoshop().activeText` |
| `ps.executeScript` | raw eval | `Photoshop().eval_js(...)` or `adobe.raw.RawSession("photoshop").eval_js(...)` |
| `ps.executeAction` | `batchPlay` | Use recorded Photoshop action descriptors through `Photoshop().batch_play(...)` |
| `ps.describeApi` | capability contract | `Photoshop().capabilities()` plus `docs/protocol.md` |
| `ps.invoke` | DOM escape hatch | `Photoshop().dom.<path>.get()` / `.call(..., modal=True)` |
| `ps.batchPlay` | `batchPlay` | `Photoshop().batch_play(...)` / `Photoshop().action.batchPlay(...)` |

## Adapter Guidance

New DCC MCP skills should use typed `adobepy` calls first. For broad Photoshop
operations that are naturally Action Manager commands, keep descriptors in the
skill or in a small adapter-local recipe module and call `batch_play` with an
explicit modal policy. Avoid reintroducing a private WebSocket dialect.

The relevant Adobe UXP concepts are the Photoshop DOM, `executeAsModal`, and
`action.batchPlay`; `adobepy` keeps those available while presenting Pythonic
aliases such as `active_document`, `active_layers`, and `batch_play`.

## References

- [Adobe Photoshop UXP APIs](https://developer.adobe.com/photoshop/)
- [Document class](https://developer.adobe.com/photoshop/uxp/ps_reference/classes/document/)
- [Layer class](https://developer.adobe.com/photoshop/uxp/ps_reference/classes/layer/)
- [Selection class](https://developer.adobe.com/photoshop/uxp/ps_reference/classes/selection/)
- [TextItem class](https://developer.adobe.com/photoshop/uxp/2022/ps_reference/classes/textitem/)
- [Channel class](https://developer.adobe.com/photoshop/uxp/2022/ps_reference/classes/channel/)
- [`batchPlay`](https://developer.adobe.com/photoshop/uxp/ps_reference/media/batchplay/)
- [`executeAsModal`](https://developer.adobe.com/photoshop/uxp/2022/ps_reference/media/executeasmodal/)
