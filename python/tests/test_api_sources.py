import pathlib
import unittest

from scripts.validate_api_sources import DEFAULT_IR_DIR, DEFAULT_REGISTRY, validate_registry


class ApiSourceTests(unittest.TestCase):
    def test_api_source_registry_matches_ir_hosts(self):
        messages = validate_registry(DEFAULT_REGISTRY, DEFAULT_IR_DIR)
        self.assertEqual(
            {message.split(":", 1)[0] for message in messages},
            {"after-effects", "illustrator", "indesign", "photoshop", "premiere"},
        )
        self.assertTrue(pathlib.Path(DEFAULT_REGISTRY).exists())


if __name__ == "__main__":
    unittest.main()
