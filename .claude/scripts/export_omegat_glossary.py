#!/usr/bin/env python3
"""Export the canonical Markdown glossary to an OmegaT UTF-8 TSV glossary.

OmegaT glossary rows are: source<TAB>target<TAB>comment.  Only explicit
terminology domains are exported; prose, naming patterns, rules, and culture
guidance remain human-facing documentation in glossary.md.
"""

import argparse
import difflib
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE = ROOT / "docs/glossary.md"
DEFAULT_OUTPUT = ROOT / "docs/glossary.utf8"
EXPORT_DOMAINS = {
    "gods", "magic", "core", "combat", "items", "dialogue", "shouts",
    "species", "skills", "status", "backgrounds", "abilities", "mutations",
    "monsters", "unique-monsters", "monster-titles",
    "spells",
}


def clean_cell(value: str) -> str:
    return value.strip().strip("`").strip()


def split_variants(value: str):
    return [part.strip() for part in re.split(r"\s+/\s+", value) if part.strip()]


def split_markdown_row(line: str):
    r"""Split on unescaped Markdown pipes and decode ``\|`` literals."""
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
    return [clean_cell(value) for value in cells]


def parse_tables(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    domain = None
    rows = []
    index = 0
    while index < len(lines):
        marker = re.match(r"^<!--\s*domain:([\w-]+)\s*-->$", lines[index].strip())
        if marker:
            domain = marker.group(1)
            index += 1
            continue
        if not lines[index].lstrip().startswith("|"):
            index += 1
            continue
        table = []
        while index < len(lines) and lines[index].lstrip().startswith("|"):
            table.append(lines[index])
            index += 1
        if domain not in EXPORT_DOMAINS or len(table) < 2:
            continue

        parsed = []
        for line in table:
            parsed.append(split_markdown_row(line))
        if len(parsed[1]) < 2 or all(set(value) <= {"-"} for value in parsed[1]):
            header = parsed[0]
            data = parsed[2:]
        else:
            header = parsed[0]
            data = parsed[1:]
        if len(header) < 2:
            continue

        # Normalize human-facing table-header variants in the exported comment.
        # OmegaT always receives the same semantic pair, regardless of whether
        # the Markdown table says "EN/ZH" or "English/中文".
        source_header = "EN"
        target_header = "ZH"
        for row in data:
            if len(row) < 2:
                raise ValueError(f"malformed glossary row in {path}: {row!r}")
            source = row[0]
            target = row[1]
            if not source or not target or set(source) <= {"-"}:
                continue
            if source.lower() in {"en", "english", "en key", "词根", "模式", "场景", "角色"}:
                continue
            comment_parts = [f"domain={domain}", f"source={source_header}/{target_header}"]
            for column_index, value in enumerate(row[2:], start=2):
                if value and value != "—":
                    label = header[column_index] if column_index < len(header) else f"column{column_index + 1}"
                    comment_parts.append(f"{label}={value}")

            source_variants = split_variants(source)
            target_variants = split_variants(target)
            if len(source_variants) > 1 and len(target_variants) == len(source_variants):
                pairs = zip(source_variants, target_variants)
            else:
                pairs = ((variant, target) for variant in source_variants)
            for source_term, target_term in pairs:
                rows.append((source_term, target_term, "; ".join(comment_parts)))
    return rows


def merge_rows(rows):
    merged = {}
    for source, target, comment in rows:
        if "\t" in source or "\t" in target or "\n" in comment:
            raise ValueError(f"tab/newline in glossary term: {source!r}")
        target_map = merged.setdefault(source, {})
        if target in target_map:
            old_comment = target_map[target]
            if comment not in old_comment.split(" | "):
                target_map[target] = old_comment + " | " + comment
        else:
            target_map[target] = comment
    output = []
    for source in sorted(merged, key=str.casefold):
        for target in sorted(merged[source], key=str.casefold):
            output.append(f"{source}\t{target}\t{merged[source][target]}")
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="check output without writing it")
    args = parser.parse_args()

    expected = "\n".join(merge_rows(parse_tables(args.source))) + "\n"
    actual = args.output.read_text(encoding="utf-8") if args.output.exists() else ""
    if args.check:
        if actual == expected:
            print(f"OK: {args.output} matches {args.source}")
            return 0
        print(f"FAIL: {args.output} is stale; regenerate from {args.source}")
        for line in difflib.unified_diff(actual.splitlines(), expected.splitlines(), fromfile=str(args.output), tofile="generated"):
            print(line)
        return 1

    args.output.write_text(expected, encoding="utf-8", newline="\n")
    print(f"OK: wrote {len(expected.splitlines())} OmegaT terms to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
