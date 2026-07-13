#!/usr/bin/env python3
"""Convert DCSS source.txt entries to bilingual XLIFF 1.2."""
from __future__ import annotations
import argparse
import hashlib
import html
from pathlib import Path
import sys

# These prefixes are TextDB key namespaces, not part of the user-visible
# English text. Other pipes in source strings are real UI separators.
IDENTIFIER_PREFIXES = frozenset(
    {
        "status",
        "rune_name",
        "hand",
        "flag long",
        "flag short",
        "topbar status",
        "verb",
        "element",
        "title article",
        "attributive",
        "monster info",
        "ctx",
        "monster equip",
        "beam hit player",
        "beam hit monster",
        "weapon-category",
        "ability cost",
        "skill_mode",
    }
)


def strip_identifier_prefix(value: str) -> tuple[str, str]:
    prefix, separator, visible = value.partition("|")
    if separator and prefix in IDENTIFIER_PREFIXES:
        return visible, prefix
    return value, ""


def is_contextual_entry(lines: list[str]) -> bool:
    """Recognize the project's context/source/target three-line form.

    A plain three-line block can also be a multiline target. Markup, printf
    tokens, or a literal newline token in the first two lines identify that
    case as ordinary TextDB data rather than context metadata.
    """
    if len(lines) != 3 or not all(line.strip() for line in lines):
        return False
    return not any(token in lines[0] or token in lines[1] for token in ("<", ">", "%", "\\n"))


def parse_block(block: str, number: int):
    lines = [line.rstrip("\r") for line in block.splitlines()]
    # Match the project's TextDB parser: comments before the first content
    # line are metadata, while comments after the key are value text.
    while lines and (not lines[0].strip() or lines[0].startswith("#")):
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    if not lines:
        return None
    # Contextual entries are context / source / target; ordinary entries are
    # source / target, sometimes separated by a blank physical line.
    if is_contextual_entry(lines):
        source, prefix = strip_identifier_prefix(_unescape_key(lines[1]))
        return lines[0], source, "\n".join(lines[2:]), prefix
    if not lines[0]:
        raise ValueError(f"entry {number}: empty source key")
    source, prefix = strip_identifier_prefix(_unescape_key(lines[0]))
    return "", source, "\n".join(lines[1:]) if len(lines) > 1 else "", prefix


def _unescape_key(value: str) -> str:
    """Decode source.txt's leading ``\\#`` key escape."""
    return value[1:] if value.startswith("\\#") else value


def entries(path: Path):
    block: list[str] = []
    number = 1
    for line in path.read_text(encoding="utf-8").splitlines():
        # Only a separator line delimits TextDB records. Inline "%%%%" is a
        # literal format token and must remain part of the source text.
        if line.strip() == "%%%%":
            item = parse_block("\n".join(block), number)
            if item:
                yield item
            number += 1
            block = []
        else:
            block.append(line)
    item = parse_block("\n".join(block), number)
    if item:
        yield item


def esc(value: str) -> str:
    return html.escape(value, quote=False)


def esc_attr(value: str) -> str:
    return html.escape(value, quote=True)


def build_xliff(input_path: Path, source_locale: str, target_locale: str) -> str:
    rows = []
    seen = {}
    for number, (context, source, target, prefix) in enumerate(entries(input_path), 1):
        digest = hashlib.sha1(source.encode("utf-8")).hexdigest()[:12]
        seen[digest] = seen.get(digest, 0) + 1
        suffix = f"-{seen[digest]}" if seen[digest] > 1 else ""
        ident = f"u{digest}{suffix}"
        note = f"source.txt entry {number}"
        if context:
            note += f"; context={context}"
        if prefix:
            note += f"; key-prefix={prefix}"
        rows.append(
            f'    <trans-unit id="{ident}" resname="{esc_attr(source)}">\n'
            f"      <source>{esc(source)}</source>\n"
            f"      <target>{esc(target)}</target>\n"
            f"      <note>{esc(note)}</note>\n"
            "    </trans-unit>"
        )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<xliff version="1.2" xmlns="urn:oasis:names:tc:xliff:document:1.2">\n'
        f'  <file source-language="{esc(source_locale)}" '
        f'target-language="{esc(target_locale)}" datatype="x-crawl" original="source.txt">\n'
        "    <body>\n" + "\n".join(rows) + "\n"
        "    </body>\n  </file>\n</xliff>\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--source-locale", default="en")
    parser.add_argument("--target-locale", default="zh")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_xliff(args.input, args.source_locale, args.target_locale), encoding="utf-8")
    print(f"Wrote XLIFF: {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
