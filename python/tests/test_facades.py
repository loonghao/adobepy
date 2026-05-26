import unittest

from adobe.after_effects import AfterEffects
from adobe.indesign import InDesign
from adobe.illustrator import Illustrator
from adobe.photoshop import Photoshop, PhotoshopSession, connect as connect_photoshop
from adobe.premiere import Premiere
from adobe.raw import RawSession


class CapturingClient:
    target = "default"

    def __init__(self):
        self.calls = []
        self.async_calls = []

    def call(self, host, namespace, method, args=None, options=None, target=None):
        self.calls.append({"host": host, "namespace": namespace, "method": method, "args": list(args or []), "options": options or {}})
        if namespace == "app":
            if method == "getDocuments":
                return [{"id": 7, "name": "demo", "path": "C:/demo", "width": 100, "height": 50}]
            return {"photoshop": "26.0", "indesign": "19.5", "premiere": "25.6", "after-effects": "24.4", "illustrator": "28.2"}[host]
        if namespace == "document" and method == "getActive":
            return {"id": 7, "name": "demo", "path": "C:/demo", "width": 100, "height": 50}
        if namespace == "document" and method == "getById":
            return {"id": args[0], "name": "demo", "width": 100, "height": 50}
        if namespace == "document" and method in {"getLayers", "getActiveLayers"}:
            return [{"id": 11, "name": "Layer 1", "kind": "pixel", "opacity": 80, "visible": True}]
        if namespace == "layer":
            if method == "getChildren":
                return [{"id": 12, "name": "Child", "kind": "pixel"}]
            return {"id": 11, "name": "Layer 1"}
        if namespace == "raw" and method == "evalJs":
            return {"source": args[0], "args": list(args[1:])}
        if namespace == "raw" and method == "getPath":
            return {"path": list(args[0]), "depth": args[1]}
        if namespace == "raw" and method == "callPath":
            return {"path": list(args[0]), "args": list(args[1]), "depth": args[2]}
        if namespace == "project":
            return {"name": "cut", "path": "C:/cut", "itemCount": 3}
        return {"ok": True}

    async def call_async(self, host, namespace, method, args=None, options=None, target=None):
        self.async_calls.append({"host": host, "namespace": namespace, "method": method, "args": list(args or []), "options": options or {}})
        return {"method": method}


class FacadeTests(unittest.TestCase):
    def test_photoshop_contract(self):
        client = CapturingClient()
        app = Photoshop(client=client)
        self.assertEqual(app.version, "26.0")
        self.assertEqual(app.documents[0].name, "demo")
        self.assertEqual(app.activeDocument.width, 100)
        self.assertEqual(app.activeDocument.layers[0].opacity, 80)
        self.assertEqual(app.activeDocument.activeLayers[0].name, "Layer 1")
        self.assertEqual(app.activeLayers[0].name, "Layer 1")
        self.assertEqual(app.active_layer.name, "Layer 1")
        self.assertFalse(app.active_layer.hasChildren)
        self.assertEqual(app.active_layer.layers[0].name, "Child")
        self.assertEqual(app.dom.app.activeDocument.get()["path"], ["app", "activeDocument"])
        self.assertEqual(app.dom.app.activeDocument.createLayer({"name": "x"}, modal=True)["path"], ["app", "activeDocument", "createLayer"])
        with app.executeAsModal(commandName="Hide"):
            app.action.batchPlay([{"_obj": "hide"}])
        self.assertEqual(client.calls[-1]["options"]["commandName"], "Hide")
        with app.execute_as_modal(command_name="Tone"):
            app.batch_play([{"_obj": "levels"}])
        self.assertEqual(client.calls[-1]["options"]["commandName"], "Tone")
        app.activeDocument.saveAs("C:/x.psd", commandName="Save")
        app.activeDocument.export("C:/x.png", timeout_ms=3)
        app.activeLayer.hide()
        self.assertTrue(client.calls[-1]["options"]["modal"])
        self.assertIsInstance(connect_photoshop(broker_url="http://x"), Photoshop)

    def test_document_refresh_and_session_modal(self):
        client = CapturingClient()
        session = PhotoshopSession(client)
        doc = session.app.active_document
        self.assertIs(doc.refresh(), doc)
        with session.modal("Batch"):
            session.action.batch_play([{"_obj": "select"}])
        self.assertEqual(client.calls[-1]["options"]["commandName"], "Batch")

    def test_indesign_and_premiere(self):
        self.assertEqual(InDesign(client=CapturingClient()).active_document.name, "demo")
        self.assertEqual(InDesign(client=CapturingClient()).version, "19.5")
        self.assertEqual(Premiere(client=CapturingClient()).activeProject.name, "cut")
        self.assertEqual(Premiere(client=CapturingClient()).project.name, "cut")
        self.assertEqual(Premiere(client=CapturingClient()).version, "25.6")

    def test_legacy_cep_facades(self):
        ae = AfterEffects(client=CapturingClient())
        self.assertEqual(ae.version, "24.4")
        self.assertEqual(ae.activeProject.itemCount, 3)
        self.assertEqual(ae.project.path, "C:/cut")

        illustrator = Illustrator(client=CapturingClient())
        self.assertEqual(illustrator.version, "28.2")
        self.assertEqual(illustrator.activeDocument.name, "demo")
        self.assertEqual(illustrator.active_document.path, "C:/demo")

    def test_raw_session(self):
        client = CapturingClient()
        raw = RawSession("illustrator", client)
        raw.eval_js("1", timeout_ms=1)
        raw.evalJs("1", timeoutMs=2)
        raw.eval_extendscript("1")
        raw.eval_extend_script("1")
        raw.evalExtendScript("1", timeoutMs=3)
        raw.send_sdk_message({"x": 1})
        raw.sendSdkMessage({"x": 2}, timeoutMs=4)
        raw.batch_play([{"_obj": "hide"}])
        raw.batchPlay([{"_obj": "show"}], timeoutMs=5)
        self.assertEqual(client.calls[-1]["method"], "batchPlay")


class AsyncFacadeTests(unittest.IsolatedAsyncioTestCase):
    async def test_async_raw(self):
        client = CapturingClient()
        raw = RawSession("premiere", client)
        self.assertEqual(await raw.eval_js_async("1"), {"method": "evalJs"})
        self.assertEqual(await raw.eval_extendscript_async("1"), {"method": "evalExtendScript"})
        self.assertEqual(await raw.eval_extend_script_async("1"), {"method": "evalExtendScript"})
        self.assertEqual(await raw.send_sdk_message_async({"x": 1}), {"method": "sendSdkMessage"})
        self.assertEqual(await raw.batch_play_async([{"_obj": "hide"}]), {"method": "batchPlay"})


if __name__ == "__main__":
    unittest.main()
