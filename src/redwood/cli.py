import argparse
import os
import sys
import time

from redwood.humanize import human_size
from redwood.scanner import scan


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="redwood", description="Show disk usage as a treemap with a navigable folder list."
    )
    parser.add_argument("path", nargs="?", default=".", help="folder to scan (default: .)")
    parser.add_argument(
        "-x", "--one-file-system", action="store_true", help="don't cross filesystem boundaries"
    )
    parser.add_argument(
        "--apparent-size", action="store_true", help="use file sizes instead of disk usage"
    )
    parser.add_argument("--no-color", action="store_true", help="draw with characters only")
    return parser.parse_args(argv)


class _Progress:
    def __init__(self):
        self.last = 0.0

    def __call__(self, count: int, path: str) -> None:
        now = time.monotonic()
        if now - self.last < 0.1:
            return
        self.last = now
        width = os.get_terminal_size(sys.stderr.fileno()).columns if sys.stderr.isatty() else 80
        line = f"Scanning: {count} items  {path}"
        sys.stderr.write("\r" + line[: width - 1].ljust(width - 1))
        sys.stderr.flush()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if not os.path.isdir(args.path):
        sys.exit(f"redwood: not a directory: {args.path}")

    progress = _Progress() if sys.stderr.isatty() else None
    try:
        root = scan(args.path, args.one_file_system, args.apparent_size, progress)
    except KeyboardInterrupt:
        sys.exit(130)
    except OSError as e:
        sys.exit(f"redwood: {e}")
    if progress:
        sys.stderr.write("\r\033[K")

    if not sys.stdout.isatty():
        print(f"{human_size(root.size)}\t{root.path}")
        return

    from redwood.ui import run

    try:
        run(root, color=not args.no_color)
    except KeyboardInterrupt:
        pass
