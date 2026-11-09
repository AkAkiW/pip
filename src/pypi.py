import json
import operator
import platform
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

HTTP_TIMEOUT = 15
USER_AGENT = "pip-dependency-graph/0.1"
NAME_PATTERN = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
MARKER_CLAUSE = re.compile(
    r"^(python_version|python_full_version)\s*"
    r"(==|!=|<=|>=|<|>)\s*[\"']([^\"']+)[\"']$"
)
VERSION_PART = re.compile(r"\d+")
COMPARE = {
    "==": operator.eq,
    "!=": operator.ne,
    "<": operator.lt,
    "<=": operator.le,
    ">": operator.gt,
    ">=": operator.ge,
}


class RepositoryError(Exception):
    pass


def fetch_direct_dependencies(
    repository: str, package: str, version: str
) -> List[str]:
    url = build_metadata_url(repository, package, version)
    data = _http_get_json(url)
    info = data.get("info")
    if not isinstance(info, dict):
        raise RepositoryError("unexpected metadata format: " + url)
    requires = info.get("requires_dist")
    if requires is None:
        return []
    if not isinstance(requires, list):
        raise RepositoryError("unexpected requires_dist format: " + url)
    return _parse_requires_dist(requires)


def build_metadata_url(repository: str, package: str, version: str) -> str:
    base = repository.rstrip("/")
    return f"{base}/{quote(package, safe='')}/{quote(version, safe='')}/json"


def _http_get_json(url: str) -> Dict[str, Any]:
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as resp:
            payload = resp.read()
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise RepositoryError("package or version not found: " + url)
        raise RepositoryError(f"repository returned HTTP {exc.code}: {url}")
    except urllib.error.URLError as exc:
        raise RepositoryError("cannot reach repository: " + str(exc.reason))
    try:
        data = json.loads(payload.decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        message = "repository returned invalid JSON: " + url
        raise RepositoryError(message) from exc
    if not isinstance(data, dict):
        raise RepositoryError("unexpected metadata format: " + url)
    return data


def _parse_requires_dist(entries: List[Any]) -> List[str]:
    names = set()
    for entry in entries:
        if not isinstance(entry, str):
            continue
        name = _parse_requirement_line(entry)
        if name is not None:
            names.add(name)
    return sorted(names)


def _parse_requirement_line(line: str) -> Optional[str]:
    requirement, marker = _split_marker(line)
    if marker is not None and not _is_marker_active(marker):
        return None
    match = NAME_PATTERN.match(requirement)
    if match is None:
        return None
    return _normalize_name(match.group(1))


def _split_marker(line: str) -> Tuple[str, Optional[str]]:
    parts = line.split(";", 1)
    if len(parts) == 1:
        return line, None
    return parts[0].strip(), parts[1].strip()


def _is_marker_active(marker: str) -> bool:
    for clause in marker.split(" and "):
        if _eval_clause(clause.strip()) is False:
            return False
    return True


def _eval_clause(clause: str) -> Optional[bool]:
    if "extra" in clause:
        return False
    match = MARKER_CLAUSE.match(clause)
    if match is None:
        return None
    current = _current_version(match.group(1))
    wanted = _version_tuple(match.group(3))
    return COMPARE[match.group(2)](current, wanted)


def _current_version(variable: str) -> Tuple[int, ...]:
    full = _version_tuple(platform.python_version())
    if variable == "python_version":
        return full[:2]
    return full


def _version_tuple(text: str) -> Tuple[int, ...]:
    parts = VERSION_PART.findall(text)
    if not parts:
        return (0,)
    return tuple(int(part) for part in parts)


def _normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()
