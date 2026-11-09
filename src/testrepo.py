import re
from typing import Callable, Dict, List

from src.errors import RepositoryError

LINE_PATTERN = re.compile(r"^([A-Z]+)\s*:\s*(.*)$")
NAME_PATTERN = re.compile(r"^[A-Z]+$")


def load_test_repository(path: str) -> Callable[[str], List[str]]:
    table = _parse_file(path)

    def get_dependencies(package: str) -> List[str]:
        return table.get(package, [])

    return get_dependencies


def _parse_file(path: str) -> Dict[str, List[str]]:
    table = {}
    with open(path, "r", encoding="utf-8") as handle:
        for number, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            _add_line(table, line, number, path)
    return table


def _add_line(table: Dict[str, List[str]], line: str, number: int,
              path: str) -> None:
    match = LINE_PATTERN.match(line)
    if match is None:
        raise RepositoryError(f"invalid line {number} in {path}: {line}")
    _validate_names([match.group(1)] + match.group(2).split(), number, path)
    table[match.group(1)] = match.group(2).split()


def _validate_names(names: List[str], number: int, path: str) -> None:
    for name in names:
        if NAME_PATTERN.match(name) is None:
            message = (
                f"invalid package name '{name}' on line {number} in {path}"
            )
            raise RepositoryError(message)
