import heapq
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


def load_order(graph: Dict[str, List[str]]) -> List[str]:
    indegree = {name: len(deps) for name, deps in graph.items()}
    dependents = _dependents(graph)
    ready = [name for name, deps in graph.items() if not deps]
    heapq.heapify(ready)
    order = []
    while ready:
        name = heapq.heappop(ready)
        order.append(name)
        for dependent in dependents.get(name, []):
            indegree[dependent] -= 1
            if not indegree[dependent]:
                heapq.heappush(ready, dependent)
    remaining = sorted(set(graph) - set(order))
    return order + remaining


def _dependents(graph: Dict[str, List[str]]) -> Dict[str, List[str]]:
    result = {name: [] for name in graph}
    for name, deps in graph.items():
        for dep in deps:
            result[dep].append(name)
    return result
