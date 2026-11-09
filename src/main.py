import argparse
import sys

from src.config import Config, ConfigError, load_config


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print("error: " + str(exc), file=sys.stderr)
        return 2
    _print_config(config)
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


def _print_config(config: Config) -> None:
    values = {
        "package": config.package,
        "repository": config.repository,
        "test_mode": _json_bool(config.test_mode),
        "version": config.version,
        "ascii_tree": _json_bool(config.ascii_tree),
        "filter": config.filter,
    }
    for key, value in values.items():
        print(f"{key}={value}")


def _json_bool(value: bool) -> str:
    return "true" if value else "false"


if __name__ == "__main__":
    sys.exit(main())
