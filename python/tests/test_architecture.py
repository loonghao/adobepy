import unittest

from scripts.check_architecture import check_architecture, runtime_invoke_pairs_from_source


class ArchitectureTests(unittest.TestCase):
    def test_architecture_boundaries_hold(self):
        messages = check_architecture()
        self.assertIn("facade aliases: every camelCase member has a snake_case sibling", messages)
        self.assertTrue(any("runtime invoke pairs declared in IR" in message for message in messages))

    def test_runtime_invoke_pair_extraction_includes_literal_helpers(self):
        source = """
class SelectionProxy:
    def select_all(self):
        return self._invoke("selectAll")

    def _invoke(self, method):
        return self._session.invoke("selection", method)

class App:
    def version(self):
        return self._session.invoke("app", "getVersion")
"""
        self.assertEqual(
            runtime_invoke_pairs_from_source(source, "sample.py"),
            {("selection", "selectAll"), ("app", "getVersion")},
        )


if __name__ == "__main__":
    unittest.main()
