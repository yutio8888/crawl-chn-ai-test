#!/usr/bin/env python3
"""Validate exact keys and explicitly rejected forms against the OmegaT glossary."""

from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
import re
import subprocess

from i18n_shared import AuditRootError, parse_entries, resolve_audit_root


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
            # A matching trailing qualifier in the English identity is part
            # of the name (e.g. Dragon Vein (Fire)), not a context annotation.
            if not re.search(r"(?:\([^()]+\)|（[^（）]+）)$", columns[0]):
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



def load_rejections(path: Path) -> dict[str, set[str]]:
    """Read only explicit reject= markers, never prose such as '弃用数值名'."""
    rules: dict[str, set[str]] = defaultdict(set)
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        source, _target, comment = line.split("\t")
        for marker in re.finditer(r"(?:^|[;；])\s*reject=([^;；]*)", comment):
            rejected = [part.strip() for part in marker[1].split("／")]
            if not all(rejected):
                raise ValueError(f"empty reject= form for {source!r} in {path}")
            rules[source.casefold()].update(rejected)
    return dict(rules)


def validate_rejections(
    rules: dict[str, set[str]], data_root: Path,
) -> tuple[int, int]:
    """Scan the whole current catalog and paired English/ZH prose bodies.

    Lookup keys identify prose entries; they are never English body evidence.
    Unpaired legacy keys have no English body and are outside this check.
    """
    if not rules:
        return 0, 0
    patterns = [(term, re.compile(r"(?<!\w)" + r"\s+".join(
        re.escape(word) for word in term.split()) + r"(?!\w)", re.IGNORECASE), rejected)
        for term, rejected in sorted(rules.items())]
    checked = failures = 0

    def check(path: Path, lineno: int, key: str, english: str, chinese: str):
        nonlocal checked, failures
        for term, pattern, rejected in patterns:
            if not pattern.search(english):
                continue
            checked += 1
            for form in sorted(rejected):
                if form in chinese:
                    match_line = lineno + chinese[:chinese.index(form)].count("\n")
                    print(f"FAIL: {path}:{match_line}: {key!r}: deprecated {form!r} "
                          f"for English term {term!r}")
                    failures += 1

    catalog = data_root / "i18n/zh/source.txt"
    if not catalog.is_file():
        raise ValueError(f"missing rejection-scan catalog: {catalog}")
    for entry in parse_entries(catalog, lowercase_keys=False):
        check(catalog, entry.key_line + 1, entry.key, entry.key, entry.value)
    for family in ("descript", "database"):
        zh_dir = data_root / family / "zh"
        if not zh_dir.is_dir():
            raise ValueError(f"missing rejection-scan directory: {zh_dir}")
        for path in sorted(zh_dir.glob("*.txt")):
            english_path = path.parent.parent / path.name
            if not english_path.is_file():
                raise ValueError(f"missing English partner: {english_path}")
            english = {entry.key: entry.value for entry in parse_entries(english_path)}
            for entry in parse_entries(path):
                body = english.get(entry.key)
                if body is not None:
                    check(path, entry.key_line + 1, entry.key, body, entry.value)
    return checked, failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glossary", type=Path, default=DEFAULT_GLOSSARY)
    parser.add_argument("--paths", type=Path, nargs="*", default=list(DEFAULT_PATHS))
    parser.add_argument("--base", default="HEAD", help="only check entries changed since this Git revision")
    parser.add_argument("--all", action="store_true", help="audit all exact keys, including historical entries")
    parser.add_argument("--data-root", type=Path, default=ROOT / "crawl-ref/source/dat",
                        help="full data tree for deprecated-form scans (independent of --base/--paths)")
    args = parser.parse_args()
    try:
        terms = load_terms(args.glossary)
        checked, failures = validate(terms, args.paths, base=None if args.all else args.base)
        rejected_checked, rejected_failures = validate_rejections(
            load_rejections(args.glossary), args.data_root)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if failures:
        print(f"FAIL: {failures} canonical terminology violation(s) in {checked} exact-key entries")
    else:
        print(f"OK: {checked} exact-key entries match the current glossary")
    if rejected_failures:
        print(f"FAIL: {rejected_failures} deprecated-form violation(s) in "
              f"{rejected_checked} term-matched entries")
    else:
        print(f"OK: {rejected_checked} term-matched entries contain no explicit rejected forms")
    return int(bool(failures or rejected_failures))


if __name__ == "__main__":
    raise SystemExit(main())
