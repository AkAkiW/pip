import argparse
import sys
from typing import Dict, List

from src.config import Config, ConfigError, load_config
from src.errors import RepositoryError
from src.graph import build_dependency_graph
from src.pypi import pypi_source
from src.testrepo import load_test_repository


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2
    source = _make_source(config)
    try:
        graph = build_dependency_graph(
            source, config.package, config.filter
        )
    except RepositoryError as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 1
    _print_graph(graph)
    return 0


def _make_source(config: Config):
    if config.test_mode:
        return load_test_repository(config.repository)
    return pypi_source(config.repository, config.package, config.version)


def _print_graph(graph: Dict[str, List[str]]) -> None:
    for name in sorted(graph):
        deps = " ".join(graph[name])
        if deps:
            print(f"{name}: {deps}")
        else:
            print(f"{name}:")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="depgraph",
        description="pip dependency graph visualizer",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="path to the JSON configuration file",
    )
    return parser


if __name__ == "__main__":
    sys.exit(main())
