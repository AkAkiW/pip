import argparse
import sys

from src.config import ConfigError, load_config
from src.pypi import RepositoryError, fetch_direct_dependencies


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2
    if config.test_mode:
        print("error: test mode is not implemented yet", file=sys.stderr)
        return 2
    try:
        dependencies = fetch_direct_dependencies(
            config.repository, config.package, config.version
        )
    except RepositoryError as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 1
    for name in dependencies:
        print(name)
    return 0


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
