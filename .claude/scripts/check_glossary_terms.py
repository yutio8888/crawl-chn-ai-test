#!/usr/bin/env python3
"""Validate exact translation keys against the generated OmegaT glossary."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import re
import subprocess

from i18n_shared import AuditRootError, resolve_audit_root


SCRIPT_ROOT = Path(__file__).resolve().parents[2]
try:
    ROOT = resolve_audit_root(SCRIPT_ROOT)
except AuditRootError as error:
    raise SystemExit(f"ERROR: invalid audit root: {error}") from error
DEFAULT_GLOSSARY = ROOT / "docs/glossary.utf8"
DEFAULT_PATHS = (
    ROOT / "crawl-ref/source/dat/i18n/zh/source.txt",
)


def load_terms(path: Path) -> dict[str, set[str]]:
    terms: dict[str, set[str]] = defaultdict(set)
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        columns = line.split("\t")
        if len(columns) != 3 or not columns[0] or not columns[1]:
            raise ValueError(f"invalid OmegaT row at {path}:{lineno}")
        targets = [part.strip() for part in re.split(r"\s+/\s+", columns[1]) if part.strip()]
        for target in targets:
            # Parenthetical labels describe context and are not literal output.
            target = re.sub(r"（[^）]+）$", "", target).strip()
            if target:
                terms[columns[0]].add(target)
    if not terms:
        raise ValueError(f"no terms found in {path}")
    return dict(terms)


def split_blocks_text(text: str) -> list[tuple[int, str, str]]:
    records: list[tuple[int, str, str]] = []
    block: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if line == "%%%%":
            if block:
                nonempty = [(line_no, value) for line_no, value in block if value.strip()]
                if len(nonempty) >= 2:
                    records.append((nonempty[0][0], nonempty[0][1], "\n".join(value for _, value in nonempty[1:])))
            block = []
        else:
            block.append((lineno, line))
    if block:
        nonempty = [(line_no, value) for line_no, value in block if value.strip()]
        if len(nonempty) >= 2:
            records.append((nonempty[0][0], nonempty[0][1], "\n".join(value for _, value in nonempty[1:])))
    return records


def split_blocks(path: Path) -> list[tuple[int, str, str]]:
    return split_blocks_text(path.read_text(encoding="utf-8", errors="replace"))


def iter_text_files(paths: list[Path]):
    seen: set[Path] = set()
    for path in paths:
        if path.is_file():
            candidates = [path]
        elif path.is_dir():
            candidates = sorted(path.rglob("*.txt"))
        else:
            raise ValueError(f"translation path does not exist: {path}")
        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                yield candidate


def _record_map(records: list[tuple[int, str, str]]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for _lineno, source, target in records:
        result[source].append(target)
    return dict(result)


def changed_records(path: Path, base: str) -> list[tuple[int, str, str]]:
    current = split_blocks(path)
    try:
        relative = path.resolve().relative_to(ROOT.resolve())
    except ValueError as error:
        raise ValueError(f"path is outside repository: {path}") from error
    result = subprocess.run(
        ["git", "show", f"{base}:{relative.as_posix()}"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode == 0:
        previous = _record_map(split_blocks_text(result.stdout))
    else:
        previous = {}
    current_map = _record_map(current)
    changed_keys = {source for source, targets in current_map.items() if previous.get(source) != targets}
    return [record for record in current if record[1] in changed_keys]


def validate(
    terms: dict[str, set[str]],
    paths: list[Path],
    *,
    base: str | None = None,
) -> tuple[int, int]:
    checked = 0
    failures = 0
    for path in iter_text_files(paths):
        records = changed_records(path, base) if base else split_blocks(path)
        for lineno, source, target in records:
            allowed = terms.get(source)
            if not allowed:
                continue
            checked += 1
            normalized_target = target.strip()
            if normalized_target in allowed:
                continue
            expected = " / ".join(sorted(allowed))
            print(f"FAIL: {path}:{lineno}: {source!r} uses {target!r}; expected exactly one of: {expected}")
            failures += 1
    return checked, failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glossary", type=Path, default=DEFAULT_GLOSSARY)
    parser.add_argument("--paths", type=Path, nargs="*", default=list(DEFAULT_PATHS))
    parser.add_argument("--base", default="HEAD", help="only check entries changed since this Git revision")
    parser.add_argument("--all", action="store_true", help="audit all exact keys, including historical entries")
    args = parser.parse_args()
    try:
        terms = load_terms(args.glossary)
        checked, failures = validate(terms, args.paths, base=None if args.all else args.base)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if failures:
        print(f"FAIL: {failures} canonical terminology violation(s) in {checked} exact-key entries")
        return 1
    print(f"OK: {checked} exact-key entries match the current glossary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
