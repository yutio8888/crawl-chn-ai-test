#!/usr/bin/env python3
"""Reject machine-specific repository references in maintained project files."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]

ROOT_DOCUMENTS = (
    ".dcss-paths.conf.example",
    "AGENTS.md",
    "CODEX.md",
    "README.md",
)

SCOPED_GLOBS = (
    ".agents/**/*.md",
    ".claude/ORCHESTRATION_STATE.md",
    ".claude/scripts/*.py",
    ".claude/scripts/*.sh",
    ".claude/scripts/lib/*.sh",
    ".codex/**/*.md",
    ".codex/**/*.toml",
    ".pi/**/*.md",
    ".pi/**/*.json",
    ".pi/**/*.mjs",
    ".pi/**/*.ts",
    "docs/**/*.md",
    "crawl-ref/source/util/build-console.sh",
    "crawl-ref/source/util/build-tiles.sh",
    "crawl-ref/source/util/build-android.sh",
    "crawl-ref/source/util/edit_vault",
)

# This checker and its tests necessarily contain the literals they detect.
EXCLUDED = {
    ".claude/scripts/check_path_portability.py",
}
ALLOW_MARKER = "path-portability: allow"


@dataclass(frozen=True)
class Rule:
    name: str
    pattern: re.Pattern[str]


RULES = (
    Rule("user-home absolute path", re.compile(r"/(?:home|Users)/[^/\s`\"']+/")),
    Rule("WSL drive mount", re.compile(r"/mnt/[A-Za-z]/")),
    Rule("Windows drive path", re.compile(r"(?<![A-Za-z0-9])(?:[A-Za-z]:[\\/])")),
    Rule(
        "home-relative project layout",
        re.compile(r"(?:~|\$HOME|\$\{HOME\})/(?:projects|crawl|outputs)/"),
    ),
)


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    rule: str
    text: str


def discover_paths(root: Path) -> list[Path]:
    listed = subprocess.run(
        [
            "git", "-C", str(root), "ls-files", "--cached", "--others",
            "--exclude-standard", "-z",
        ],
        capture_output=True,
        check=False,
    )
    visible = None
    if listed.returncode == 0:
        visible = {
            item.decode("utf-8", errors="surrogateescape")
            for item in listed.stdout.split(b"\0") if item
        }

    paths = {root / name for name in ROOT_DOCUMENTS}
    for pattern in SCOPED_GLOBS:
        paths.update(root.glob(pattern))
    return sorted(
        path for path in paths
        if path.is_file()
        and (relative := path.relative_to(root).as_posix()) not in EXCLUDED
        and (visible is None or relative in visible)
    )


def find_violations(root: Path, paths: list[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if ALLOW_MARKER in line:
                continue
            for rule in RULES:
                if rule.pattern.search(line):
                    violations.append(
                        Violation(path.relative_to(root), number, rule.name, line.strip())
                    )
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument(
        "--path",
        action="append",
        default=[],
        help="Root-relative file to scan; repeat to override normal discovery.",
    )
    args = parser.parse_args()

    root = args.root.resolve()
    paths = [root / value for value in args.path] if args.path else discover_paths(root)
    missing = [path for path in paths if not path.is_file()]
    if missing:
        for path in missing:
            print(f"ERROR: path does not exist: {path}", file=sys.stderr)
        return 2

    violations = find_violations(root, paths)
    if violations:
        print("Path portability violations:", file=sys.stderr)
        for item in violations:
            print(
                f"  {item.path.as_posix()}:{item.line}: {item.rule}: {item.text}",
                file=sys.stderr,
            )
        return 1

    print(f"Path portability check passed ({len(paths)} files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
