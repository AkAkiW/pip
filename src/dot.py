from typing import Dict, List


def to_dot(graph: Dict[str, List[str]]) -> str:
    lines = ["digraph dependencies {", "    rankdir=LR;"]
    for name in sorted(graph):
        lines.append(f'    "{_escape(name)}";')
    for name in sorted(graph):
        for dep in graph[name]:
            lines.append(f'    "{_escape(name)}" -> "{_escape(dep)}";')
    lines.append("}")
    return "\n".join(lines)


def _escape(name: str) -> str:
    return name.replace("\\", "\\\\").replace('"', '\\"')
