import pathlib
import unittest

from scripts.replay_fixtures import run_fixture


ROOT = pathlib.Path(__file__).resolve().parents[2]


class ReplayFixtureTests(unittest.TestCase):
    def test_all_replay_fixtures(self):
        fixture_dir = ROOT / "python" / "tests" / "fixtures" / "replay"
        names = [run_fixture(path)["name"] for path in sorted(fixture_dir.glob("*.json"))]
        self.assertIn("photoshop-active-layers", names)
        self.assertIn("illustrator-text-export", names)

    def test_photoshop_active_layers_replay(self):
        result = run_fixture(ROOT / "python" / "tests" / "fixtures" / "replay" / "photoshop_active_layers.json")
        self.assertEqual(result["stdout"], ["Background", "Grade"])
        self.assertEqual(
            [(call["namespace"], call["method"], call["args"]) for call in result["calls"]],
            [("document", "getActive", []), ("document", "getActiveLayers", [7])],
        )


if __name__ == "__main__":
    unittest.main()
