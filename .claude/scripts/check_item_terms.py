#!/usr/bin/env python3
"""Check item terminology using docs/glossary.md as the canonical SSOT.

Current terms are read from the ``domain:items`` table in glossary.md.
Historical rejected names are read from concrete Type-B naming revisions in
decisions.md; decisions remains history, not a second current-term registry.
"""

import argparse
from pathlib import Path
import re
import sys

from i18n_shared import AuditRootError, resolve_audit_root


SCRIPT_ROOT = Path(__file__).resolve().parents[2]
try:
    ROOT = resolve_audit_root(SCRIPT_ROOT)
except AuditRootError as error:
    print(f"ERROR: invalid audit root: {error}", file=sys.stderr)
    raise SystemExit(2)
SOURCE = ROOT / "crawl-ref/source/dat/i18n/zh/source.txt"
DEFAULT_GLOSSARY = ROOT / "docs/glossary.md"
DEFAULT_DECISIONS = ROOT / "docs/decisions.md"
DEFAULT_OMEGAT = ROOT / "docs/glossary.utf8"
ZH_DIRS = [
    ROOT / "crawl-ref/source/dat/i18n/zh",
    ROOT / "crawl-ref/source/dat/descript/zh",
    ROOT / "crawl-ref/source/dat/database/zh",
]

def parse_source(path: Path):
    entries = {}
    blocks = path.read_text(encoding="utf-8").split("%%%%")
    for block in blocks:
        lines = block.strip("\n").splitlines()
        if len(lines) == 2:
            entries[lines[0]] = lines[1]
    return entries


def split_markdown_row(line: str):
    r"""Split a Markdown table row on unescaped pipes.

    Markdown requires a literal pipe inside a cell to be written as ``\|``.
    Decode that escape here so context-qualified glossary keys match the
    production ``context|key`` form.
    """
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        raise ValueError(f"malformed Markdown table row: {line!r}")

    cells = []
    cell = []
    escaped = False
    for char in stripped[1:-1]:
        if escaped:
            if char == "|":
                cell.append("|")
            else:
                cell.extend(("\\", char))
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(cell).strip())
            cell = []
        else:
            cell.append(char)
    if escaped:
        cell.append("\\")
    cells.append("".join(cell).strip())
    if any(value.count("`") % 2 for value in cells):
        raise ValueError(
            f"unescaped pipe or unmatched code span in Markdown row: {line!r}"
        )
    return cells


def parse_item_glossary(path: Path):
    """Read EN→ZH pairs from the item-name-terms table in glossary.md."""
    content = path.read_text(encoding="utf-8")
    marker = "<!-- item-name-terms -->"
    if marker not in content:
        raise ValueError(f"missing {marker!r} in {path}")
    section = content.split(marker, 1)[1]
    section = section.split("<!-- domain:", 1)[0]

    terms = {}
    for line in section.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        columns = split_markdown_row(line)
        if len(columns) != 3:
            raise ValueError(
                f"malformed item glossary row in {path}: {line!r}"
            )
        en, zh, _comment = columns
        if set(en.strip()) <= {"-"}:
            continue
        if en.strip().lower() == "en":
            continue
        # Qualifiers document scope but are not part of the source.txt key.
        en = re.sub(r"\s+\([^)]*\)$", "", en.strip()).strip("`")
        if en in terms:
            raise ValueError(f"duplicate item term {en!r} in {path}")
        terms[en] = zh.strip()

    if not terms:
        raise ValueError(f"no item terms found in {path}")
    return terms


def parse_omegat(path: Path):
    """Read an OmegaT glossary: UTF-8 TSV source, target, comment."""
    terms = {}
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line or line.startswith("#"):
            continue
        columns = line.split("\t")
        if len(columns) != 3 or not columns[0] or not columns[1]:
            raise ValueError(f"invalid OmegaT glossary row at {path}:{lineno}")
        terms.setdefault(columns[0], set()).add(columns[1])
    if not terms:
        raise ValueError(f"no OmegaT terms found in {path}")
    return terms


def parse_rejected_from_decisions(path: Path):
    """Extract old Chinese names from concrete D-B naming revisions.

    The current translation remains in glossary.md. This parser only consumes
    the historical ``old → **new**`` evidence needed to prevent regressions.
    """
    content = path.read_text(encoding="utf-8")
    rejected = set()
    for block in re.split(r"\n(?=### D-B-)", content):
        for line in block.splitlines():
            match = re.search(r"：(.+?)\s*→\s*\*\*[^*]+\*\*", line)
            if not match:
                continue
            old_part = match.group(1).split("；", 1)[0]
            old_part = re.sub(r"`[^`]+`\s*\（[^）]*\）", "", old_part)
            for old in re.split(r"\s*/\s*|、", old_part):
                old = old.strip(" `（）()")
                if old and not re.search(r"[A-Za-z]", old):
                    rejected.add(old)
    if not rejected:
        raise ValueError(f"no rejected item terms found in {path}")
    return rejected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--glossary", type=Path, default=DEFAULT_GLOSSARY)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--omegat", type=Path, default=DEFAULT_OMEGAT)
    args = parser.parse_args()

    failures = 0
    entries = parse_source(SOURCE)
    expected = parse_item_glossary(args.glossary)
    omegat = parse_omegat(args.omegat)
    rejected = parse_rejected_from_decisions(args.decisions)
    for key, wanted in expected.items():
        if wanted not in omegat.get(key, set()):
            print(f"FAIL: {args.omegat} lacks item term {key!r} → {wanted!r}")
            failures += 1

    print("=== Canonical item-term check ===")
    print(f"  Source: {args.glossary}")
    for key, wanted in expected.items():
        actual = entries.get(key)
        if actual != wanted:
            print(f"  FAIL: {key!r}: expected {wanted!r}, found {actual!r}")
            failures += 1
        else:
            print(f"  OK: {key} → {wanted}")

    for directory in ZH_DIRS:
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.txt")):
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                for old in rejected:
                    if old in line:
                        print(f"  FAIL: rejected term {old!r} at {path.relative_to(ROOT)}:{lineno}")
                        failures += 1

    if failures:
        print(f"FAILED: {failures} item-term issue(s)")
        return 1
    print(f"OK: {len(expected)} glossary item terms and rejected-name scan passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
