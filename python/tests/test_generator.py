import pathlib
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO

from generators.ir_to_python import (
    HostIr,
    IrValidationError,
    capabilities_from_ir,
    expand_paths,
    load_ir,
    main,
    pascal_case,
    render_pyi,
    snake_case,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]


class GeneratorTests(unittest.TestCase):
    def test_repository_ir(self):
        contracts = [load_ir(path) for path in sorted((ROOT / "generators" / "ir").glob("*.json"))]
        self.assertEqual({contract.host for contract in contracts}, {"after-effects", "illustrator", "photoshop", "indesign", "premiere"})
        photoshop = next(contract for contract in contracts if contract.host == "photoshop")
        caps = capabilities_from_ir(photoshop)
        self.assertIn("layer", caps["namespaces"])
        self.assertEqual(caps["methods"]["action"], ["batchPlay"])
        after_effects = next(contract for contract in contracts if contract.host == "after-effects")
        self.assertIn("evalExtendScript", capabilities_from_ir(after_effects)["methods"]["raw"])
        self.assertIn("DocumentProxy", {proxy.name for proxy in photoshop.proxies})

    def test_render_and_write_cli(self):
        contract = load_ir(ROOT / "generators" / "ir" / "photoshop-mvp.json")
        stub = render_pyi(contract)
        self.assertIn("class Photoshop(PhotoshopSession):", stub)
        self.assertIn("def activeDocument(self) -> DocumentProxy | None: ...", stub)
        self.assertIn("def documents(self) -> list[DocumentProxy]: ...", stub)
        self.assertIn("class DocumentProxy:", stub)
        self.assertIn("def batchPlay(self, descriptors: list[dict[str, Any]]", stub)
        self.assertIn("def batch_play(self, descriptors: list[dict[str, Any]]", stub)

        output = StringIO()
        with redirect_stdout(output):
            self.assertEqual(main(["validate", str(ROOT / "generators" / "ir" / "premiere-mvp.json")]), 0)
        self.assertIn("valid premiere 0.1.0", output.getvalue())
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(main(["pyi", str(ROOT / "generators" / "ir" / "premiere-mvp.json"), "--out-dir", tmp]), 0)
            self.assertTrue((pathlib.Path(tmp) / "premiere" / "session.pyi").exists())

    def test_validation_errors_and_names(self):
        with self.assertRaisesRegex(IrValidationError, "at least one namespace"):
            HostIr.from_mapping({"host": "photoshop", "version": "0.1.0", "namespaces": []})
        with self.assertRaisesRegex(IrValidationError, "invalid host"):
            HostIr.from_mapping({"host": "class", "version": "0.1.0", "namespaces": [{"name": "app"}]})
        with self.assertRaisesRegex(IrValidationError, "requiresModalWhenMutating"):
            HostIr.from_mapping({"host": "photoshop", "version": "0.1.0", "namespaces": [{"name": "action", "methods": [{"name": "x", "requiresModalWhenMutating": True}]}]})
        with self.assertRaisesRegex(IrValidationError, "source must be namespace.method"):
            HostIr.from_mapping({"host": "photoshop", "version": "0.1.0", "namespaces": [{"name": "app", "methods": [{"name": "x"}], "properties": [{"name": "p", "type": "Document", "source": "x"}]}]})
        with self.assertRaisesRegex(IrValidationError, "does not reference"):
            HostIr.from_mapping({"host": "photoshop", "version": "0.1.0", "namespaces": [{"name": "app", "properties": [{"name": "p", "type": "Document", "source": "app.x"}]}]})
        with self.assertRaisesRegex(IrValidationError, "invalid proxy name"):
            HostIr.from_mapping({"host": "photoshop", "version": "0.1.0", "namespaces": [{"name": "app"}], "proxies": [{"name": "not-valid"}]})
        with self.assertRaisesRegex(IrValidationError, "duplicate photoshop: proxy DocumentProxy"):
            HostIr.from_mapping({"host": "photoshop", "version": "0.1.0", "namespaces": [{"name": "app"}], "proxies": [{"name": "DocumentProxy"}, {"name": "DocumentProxy"}]})
        self.assertEqual(snake_case("batchPlay"), "batch_play")
        self.assertEqual(snake_case("after-effects"), "after_effects")
        self.assertEqual(pascal_case("indesign"), "InDesign")
        self.assertEqual(pascal_case("after-effects"), "AfterEffects")
        self.assertIn(ROOT / "generators" / "ir" / "photoshop-mvp.json", expand_paths([str(ROOT / "generators" / "ir" / "photoshop-*.json")]))
        with self.assertRaisesRegex(SystemExit, "no IR files matched"):
            main(["validate", str(ROOT / "missing-*.json")])


if __name__ == "__main__":
    unittest.main()
