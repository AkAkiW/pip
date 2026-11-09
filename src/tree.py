from typing import Dict, List, Set

CYCLE_SUFFIX = " (cycle)"
DUPLICATE_SUFFIX = " (already listed)"


def render_tree(graph: Dict[str, List[str]], root: str) -> List[str]:
    lines = [root]
    _append_children(graph, root, "", lines, set(), {root})
    return lines


def _append_children(graph: Dict[str, List[str]], node: str, prefix: str,
                     lines: List[str], shown: Set[str],
                     path: Set[str]) -> None:
    children = graph.get(node, [])
    for index, child in enumerate(children):
        last = index == len(children) - 1
        lines.append(_line(prefix, _label(child, shown, path), last))
        if child in shown or child in path:
            continue
        shown.add(child)
        deeper = prefix + ("    " if last else "|   ")
        _append_children(graph, child, deeper, lines, shown,
                         path | {child})


def _label(child: str, shown: Set[str], path: Set[str]) -> str:
    if child in path:
        return child + CYCLE_SUFFIX
    if child in shown:
        return child + DUPLICATE_SUFFIX
    return child


def _line(prefix: str, label: str, last: bool) -> str:
    branch = "`-- " if last else "|-- "
    return prefix + branch + label
