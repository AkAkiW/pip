import os
import tempfile
import unittest

from src.errors import RepositoryError
from src.testrepo import load_test_repository

FIXTURE = os.path.join(
    os.path.dirname(__file__), "fixtures", "repo.txt"
)


class LoadTestRepositoryTest(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)

    def _write(self, text: str) -> str:
        path = os.path.join(self._dir.name, "repo.txt")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return path

    def test_fixture_graph(self) -> None:
        get = load_test_repository(FIXTURE)
        self.assertEqual(get("A"), ["B", "C"])
        self.assertEqual(get("E"), ["B"])
        self.assertEqual(get("H"), [])

    def test_unknown_package_has_no_dependencies(self) -> None:
        get = load_test_repository(FIXTURE)
        self.assertEqual(get("Z"), [])

    def test_extra_whitespace_is_allowed(self) -> None:
        get = load_test_repository(self._write("A:   B   C\n"))
        self.assertEqual(get("A"), ["B", "C"])

    def test_blank_lines_are_skipped(self) -> None:
        get = load_test_repository(self._write("\nA: B\n\n"))
        self.assertEqual(get("A"), ["B"])

    def test_line_without_colon_is_rejected(self) -> None:
        path = self._write("A B\n")
        with self.assertRaises(RepositoryError):
            load_test_repository(path)

    def test_lowercase_name_is_rejected(self) -> None:
        path = self._write("a: B\n")
        with self.assertRaises(RepositoryError) as ctx:
            load_test_repository(path)
        self.assertIn("line 1", str(ctx.exception))

    def test_lowercase_dependency_is_rejected(self) -> None:
        path = self._write("A: b\n")
        with self.assertRaises(RepositoryError):
            load_test_repository(path)

    def test_error_mentions_line_number(self) -> None:
        path = self._write("A: B\nbroken line\n")
        with self.assertRaises(RepositoryError) as ctx:
            load_test_repository(path)
        self.assertIn("line 2", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
