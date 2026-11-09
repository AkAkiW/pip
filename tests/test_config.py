import json
import os
import tempfile
import unittest

from src.config import ConfigError, load_config


class LoadConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)

    def _write(self, data: object) -> str:
        path = os.path.join(self._dir.name, "config.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
        return path

    def _valid(self) -> dict:
        return {
            "package": "requests",
            "repository": "https://pypi.org/pypi",
            "version": "2.32.0",
        }

    def test_valid_config_with_defaults(self) -> None:
        config = load_config(self._write(self._valid()))
        self.assertEqual(config.package, "requests")
        self.assertFalse(config.test_mode)
        self.assertFalse(config.ascii_tree)
        self.assertEqual(config.filter, "")

    def test_missing_file(self) -> None:
        path = os.path.join(self._dir.name, "nope.json")
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_invalid_json(self) -> None:
        path = os.path.join(self._dir.name, "bad.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("{ not json")
        with self.assertRaises(ConfigError):
            load_config(path)

    def test_root_not_object(self) -> None:
        with self.assertRaises(ConfigError):
            load_config(self._write([1, 2]))

    def test_unknown_key(self) -> None:
        data = self._valid()
        data["packege"] = "x"
        with self.assertRaises(ConfigError):
            load_config(self._write(data))

    def test_missing_required_key(self) -> None:
        data = self._valid()
        del data["version"]
        with self.assertRaises(ConfigError):
            load_config(self._write(data))

    def test_empty_package(self) -> None:
        data = self._valid()
        data["package"] = "  "
        with self.assertRaises(ConfigError):
            load_config(self._write(data))

    def test_package_wrong_type(self) -> None:
        data = self._valid()
        data["package"] = 5
        with self.assertRaises(ConfigError):
            load_config(self._write(data))

    def test_bad_url_without_test_mode(self) -> None:
        data = self._valid()
        data["repository"] = "ftp://example.com"
        with self.assertRaises(ConfigError):
            load_config(self._write(data))

    def test_test_mode_requires_existing_file(self) -> None:
        data = self._valid()
        data["test_mode"] = True
        data["repository"] = "missing.txt"
        with self.assertRaises(ConfigError):
            load_config(self._write(data))

    def test_test_mode_accepts_existing_file(self) -> None:
        repo = os.path.join(self._dir.name, "repo.txt")
        with open(repo, "w", encoding="utf-8") as handle:
            handle.write("A: B\n")
        data = self._valid()
        data["test_mode"] = True
        data["repository"] = repo
        config = load_config(self._write(data))
        self.assertTrue(config.test_mode)
        self.assertEqual(config.repository, repo)

    def test_invalid_version(self) -> None:
        data = self._valid()
        data["version"] = "??"
        with self.assertRaises(ConfigError):
            load_config(self._write(data))

    def test_bool_field_wrong_type(self) -> None:
        data = self._valid()
        data["ascii_tree"] = "yes"
        with self.assertRaises(ConfigError):
            load_config(self._write(data))

    def test_filter_wrong_type(self) -> None:
        data = self._valid()
        data["filter"] = 3
        with self.assertRaises(ConfigError):
            load_config(self._write(data))

    def test_explicit_values(self) -> None:
        data = self._valid()
        data.update({"ascii_tree": True, "filter": "test"})
        config = load_config(self._write(data))
        self.assertTrue(config.ascii_tree)
        self.assertEqual(config.filter, "test")


if __name__ == "__main__":
    unittest.main()
