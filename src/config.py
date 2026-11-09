import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict
from urllib.parse import urlparse

VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-_+!]*$")
REQUIRED_KEYS = ("package", "repository", "version")
OPTIONAL_DEFAULTS = {"test_mode": False, "ascii_tree": False, "filter": ""}
KNOWN_KEYS = REQUIRED_KEYS + tuple(OPTIONAL_DEFAULTS)


class ConfigError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    package: str
    repository: str
    version: str
    test_mode: bool
    ascii_tree: bool
    filter: str


def load_config(path: str) -> Config:
    raw = _read_json(path)
    _check_unknown_keys(raw)
    _check_required_keys(raw)
    test_mode = _validate_bool(raw, "test_mode")
    return Config(
        package=_validate_package(raw["package"]),
        repository=_validate_repository(raw["repository"], test_mode),
        version=_validate_version(raw["version"]),
        test_mode=test_mode,
        ascii_tree=_validate_bool(raw, "ascii_tree"),
        filter=_validate_filter(raw),
    )


def _read_json(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path):
        raise ConfigError("config file not found: " + path)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError("config root must be a JSON object")
    return data


def _check_unknown_keys(raw: Dict[str, Any]) -> None:
    unknown = sorted(set(raw) - set(KNOWN_KEYS))
    if unknown:
        raise ConfigError("unknown config keys: " + ", ".join(unknown))


def _check_required_keys(raw: Dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_KEYS if key not in raw]
    if missing:
        raise ConfigError("missing config keys: " + ", ".join(missing))


def _validate_package(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("'package' must be a non-empty string")
    return value.strip()


def _validate_repository(value: Any, test_mode: bool) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("'repository' must be a non-empty string")
    value = value.strip()
    if test_mode:
        if not os.path.isfile(value):
            raise ConfigError("test repository file not found: " + value)
    else:
        _validate_url(value)
    return value


def _validate_url(value: str) -> None:
    parsed = urlparse(value)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ConfigError("'repository' must be an http(s) URL or enable "
                          "test_mode with a file path")


def _validate_version(value: Any) -> str:
    if not isinstance(value, str) or not VERSION_PATTERN.match(value):
        raise ConfigError("'version' must be a valid version string, got: "
                          + repr(value))
    return value


def _validate_bool(raw: Dict[str, Any], key: str) -> bool:
    value = raw.get(key, OPTIONAL_DEFAULTS[key])
    if type(value) is not bool:
        raise ConfigError(f"'{key}' must be true or false")
    return value


def _validate_filter(raw: Dict[str, Any]) -> str:
    value = raw.get("filter", OPTIONAL_DEFAULTS["filter"])
    if not isinstance(value, str):
        raise ConfigError("'filter' must be a string")
    return value
