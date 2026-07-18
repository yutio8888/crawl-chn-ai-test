#!/usr/bin/env python3
"""Require bundled default option files to be BOM-free, strict UTF-8."""

from __future__ import annotations

import argparse
from pathlib import Path


UTF8_BOM = b"\xef\xbb\xbf"


def check_defaults(defaults_dir: Path) -> list[str]:
    issues: list[str] = []
    if not defaults_dir.is_dir():
        return [f"missing defaults directory: {defaults_dir}"]

    files = sorted(defaults_dir.glob("*.txt"))
    if not files:
        return [f"no default option files found in: {defaults_dir}"]

    for path in files:
        data = path.read_bytes()
        if data.startswith(UTF8_BOM):
            issues.append(f"{path}: UTF-8 BOM is not allowed")
            continue
        try:
            data.decode("utf-8", errors="strict")
        except UnicodeDecodeError as error:
            issues.append(
                f"{path}: invalid UTF-8 at byte {error.start}: {error.reason}"
            )
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--defaults-dir",
        type=Path,
        default=Path("crawl-ref/source/dat/defaults"),
        help="directory containing bundled default option .txt files",
    )
    args = parser.parse_args()

    issues = check_defaults(args.defaults_dir)
    if issues:
        for issue in issues:
            print(f"ERROR: {issue}")
        return 1

    print(f"Default option encoding: PASS ({args.defaults_dir})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
