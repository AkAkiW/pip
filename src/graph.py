from typing import Callable, Dict, List, Set

from src.errors import RepositoryError

DependencySource = Callable[[str], List[str]]


def build_dependency_graph(source: DependencySource, root: str,
                           exclude: str = "") -> Dict[str, List[str]]:
    graph = {}
    _bfs_step(source, [root], exclude, graph, set())
    return graph


def _bfs_step(source: DependencySource, queue: List[str], exclude: str,
              graph: Dict[str, List[str]], visited: Set[str]) -> None:
    if not queue:
        return
    node = queue.pop(0)
    if node in visited:
        _bfs_step(source, queue, exclude, graph, visited)
        return
    visited.add(node)
    try:
        found = source(node)
    except RepositoryError as exc:
        message = f"failed to get dependencies of '{node}': {exc}"
        raise RepositoryError(message) from exc
    deps = _filtered(found, exclude)
    graph[node] = deps
    for dep in deps:
        if dep not in visited and dep not in queue:
            queue.append(dep)
    _bfs_step(source, queue, exclude, graph, visited)


def _filtered(names: List[str], exclude: str) -> List[str]:
    kept = {name for name in names if not _is_excluded(name, exclude)}
    return sorted(kept)


def _is_excluded(name: str, exclude: str) -> bool:
    return bool(exclude) and exclude in name
