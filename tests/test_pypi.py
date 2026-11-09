import json
import unittest
import urllib.error
from unittest import mock

from src.pypi import (
    RepositoryError,
    _http_get_json,
    _parse_requirement_line,
    build_metadata_url,
    fetch_direct_dependencies,
)

REQUESTS_METADATA = {
    "info": {
        "requires_dist": [
            "charset-normalizer (<4, >=2)",
            "idna (<4, >=2.5)",
            "urllib3 (<3, >=1.21.1)",
            "certifi (>=2017.4.17)",
            "PySocks !=1.5.7, >=1.5.6; extra == 'socks'",
            "chardet (<6, >=3.0.2); extra == 'use_chardet_on_py3'",
        ]
    }
}


class FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self) -> bytes:
        return self._payload


class BuildUrlTest(unittest.TestCase):
    def test_joins_repository_package_version(self) -> None:
        url = build_metadata_url("https://pypi.org/pypi", "requests", "2.32.0")
        self.assertEqual(url, "https://pypi.org/pypi/requests/2.32.0/json")

    def test_strips_trailing_slash(self) -> None:
        url = build_metadata_url("https://pypi.org/pypi/", "a", "1.0")
        self.assertEqual(url, "https://pypi.org/pypi/a/1.0/json")

    def test_escapes_special_characters(self) -> None:
        url = build_metadata_url("https://pypi.org/pypi", "a b", "1.0/2")
        self.assertEqual(url, "https://pypi.org/pypi/a%20b/1.0%2F2/json")


class ParseRequirementLineTest(unittest.TestCase):
    def test_simple_requirement(self) -> None:
        self.assertEqual(
            _parse_requirement_line("charset-normalizer (<4, >=2)"),
            "charset-normalizer",
        )

    def test_name_normalization(self) -> None:
        self.assertEqual(_parse_requirement_line("Zope.Interface (>=4)"),
                         "zope-interface")

    def test_extra_marker_is_skipped(self) -> None:
        line = "PySocks >=1.5.6; extra == 'socks'"
        self.assertIsNone(_parse_requirement_line(line))

    def test_python_version_marker_true(self) -> None:
        line = 'foo; python_version >= "2.0"'
        self.assertEqual(_parse_requirement_line(line), "foo")

    def test_python_version_marker_false(self) -> None:
        line = 'foo; python_version < "2.0"'
        self.assertIsNone(_parse_requirement_line(line))

    def test_python_version_marker_single_quotes(self) -> None:
        line = "foo; python_version >= '2.0'"
        self.assertEqual(_parse_requirement_line(line), "foo")

    def test_python_version_marker_single_quotes_false(self) -> None:
        line = "foo; python_version < '2.0'"
        self.assertIsNone(_parse_requirement_line(line))

    def test_unknown_marker_keeps_requirement(self) -> None:
        line = "bar; platform_system == 'Windows'"
        self.assertEqual(_parse_requirement_line(line), "bar")

    def test_or_marker_keeps_requirement(self) -> None:
        line = 'baz; python_version < "2.0" or python_version >= "3.0"'
        self.assertEqual(_parse_requirement_line(line), "baz")


class FetchDirectDependenciesTest(unittest.TestCase):
    def test_requests_dependencies(self) -> None:
        with mock.patch("src.pypi._http_get_json") as get:
            get.return_value = REQUESTS_METADATA
            result = fetch_direct_dependencies(
                "https://pypi.org/pypi", "requests", "2.32.0"
            )
        self.assertEqual(
            result, ["certifi", "charset-normalizer", "idna", "urllib3"]
        )
        get.assert_called_once_with(
            "https://pypi.org/pypi/requests/2.32.0/json"
        )

    def test_missing_requires_dist(self) -> None:
        with mock.patch("src.pypi._http_get_json") as get:
            get.return_value = {"info": {}}
            result = fetch_direct_dependencies(
                "https://pypi.org/pypi", "stdlib-helper", "1.0"
            )
        self.assertEqual(result, [])

    def test_info_not_dict(self) -> None:
        with mock.patch("src.pypi._http_get_json") as get:
            get.return_value = {"info": "broken"}
            with self.assertRaises(RepositoryError):
                fetch_direct_dependencies("r", "p", "1")

    def test_requires_dist_not_list(self) -> None:
        with mock.patch("src.pypi._http_get_json") as get:
            get.return_value = {"info": {"requires_dist": "broken"}}
            with self.assertRaises(RepositoryError):
                fetch_direct_dependencies("r", "p", "1")


class HttpGetJsonTest(unittest.TestCase):
    def test_successful_decode(self) -> None:
        payload = json.dumps({"ok": True}).encode("utf-8")
        with mock.patch("src.pypi.urllib.request.urlopen") as open_:
            open_.return_value = FakeResponse(payload)
            data = _http_get_json("https://example.test/json")
        self.assertEqual(data, {"ok": True})

    def test_not_found(self) -> None:
        error = urllib.error.HTTPError(
            "u", 404, "Not Found", hdrs=None, fp=None
        )
        with mock.patch("src.pypi.urllib.request.urlopen") as open_:
            open_.side_effect = error
            with self.assertRaises(RepositoryError):
                _http_get_json("https://example.test/missing")

    def test_invalid_json(self) -> None:
        with mock.patch("src.pypi.urllib.request.urlopen") as open_:
            open_.return_value = FakeResponse(b"not json")
            with self.assertRaises(RepositoryError):
                _http_get_json("https://example.test/bad")

    def test_root_not_object(self) -> None:
        payload = json.dumps([1, 2]).encode("utf-8")
        with mock.patch("src.pypi.urllib.request.urlopen") as open_:
            open_.return_value = FakeResponse(payload)
            with self.assertRaises(RepositoryError):
                _http_get_json("https://example.test/list")


if __name__ == "__main__":
    unittest.main()
