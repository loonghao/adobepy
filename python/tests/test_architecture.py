import unittest

from scripts.check_architecture import check_architecture


class ArchitectureTests(unittest.TestCase):
    def test_architecture_boundaries_hold(self):
        messages = check_architecture()
        self.assertIn("facade aliases: every camelCase member has a snake_case sibling", messages)


if __name__ == "__main__":
    unittest.main()
