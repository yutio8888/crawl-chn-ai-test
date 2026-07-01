#!/usr/bin/env python3
"""Migrate hardcoded Chinese spell titles in spl-data.h to T_() calls.

Steps:
1. Extract (enum, current_zh_title) from current spl-data.h
2. Extract (enum, en_title) from 0.34.1 spl-data.h
3. Replace each Chinese title with T_("<en_title>") in-place
4. Generate source.txt entries: en_title → zh_title

Usage:
    python3 .claude/scripts/migrate_spell_titles.py
"""

import re
import subprocess
import sys
from pathlib import Path

SPL_DATA = Path("crawl-ref/source/spl-data.h")
SOURCE_TXT = Path("crawl-ref/source/dat/i18n/zh/source.txt")


def get_en_titles():
    """Parse 0.34.1 tag spl-data.h for English spell titles."""
    result = subprocess.run(
        ["git", "show", "0.34.1:crawl-ref/source/spl-data.h"],
        capture_output=True, text=True, check=True
    )
    pattern = re.compile(r'SPELL_(\w+),\s*"((?:[^"\\]|\\.)*)"')
    en_map = {}
    for match in pattern.finditer(result.stdout):
        enum = match.group(1)
        title = match.group(2)
        en_map[enum] = title
    return en_map


def get_zh_titles():
    """Parse current spl-data.h for Chinese spell titles."""
    content = SPL_DATA.read_text(encoding="utf-8")
    pattern = re.compile(r'SPELL_(\w+),\s*"((?:[^"\\]|\\.)*)"')
    zh_map = {}
    for match in pattern.finditer(content):
        enum = match.group(1)
        title = match.group(2)
        zh_map[enum] = title
    return zh_map


def rebuild_spl_data(en_map, zh_map):
    """Replace Chinese titles with T_() calls in spl-data.h."""
    content = SPL_DATA.read_text(encoding="utf-8")

    def replace_title(match):
        enum = match.group(1)
        zh_title = match.group(2)
        en_title = en_map.get(enum)
        if en_title is None:
            print(f"WARNING: No English title for SPELL_{enum}, skipping")
            return match.group(0)
        # Escape backslashes and double quotes for C++ string
        escaped = en_title.replace("\\", "\\\\").replace('"', '\\"')
        return f'SPELL_{enum}, T_("{escaped}")'

    pattern = re.compile(r'SPELL_(\w+),\s*"((?:[^"\\]|\\.)*)"')
    new_content = pattern.sub(replace_title, content)
    SPL_DATA.write_text(new_content, encoding="utf-8")
    return new_content


def generate_source_entries(en_map, zh_map):
    """Generate new source.txt entries for spell titles."""
    existing = set()
    if SOURCE_TXT.exists():
        content = SOURCE_TXT.read_text(encoding="utf-8")
        for m in re.finditer(r'^(?!#)([^\n]+)\n[^\n]+', content, re.MULTILINE):
            existing.add(m.group(1))

    entries = []
    for enum, zh in zh_map.items():
        en = en_map.get(enum)
        if en is None or en in existing:
            continue
        entries.append(f"{en}\n{zh}\n%%%%")

    if entries:
        with open(SOURCE_TXT, "a", encoding="utf-8") as f:
            f.write("\n" + "\n".join(entries) + "\n")
        print(f"Added {len(entries)} entries to source.txt")
    else:
        print("No new entries needed for source.txt")


def main():
    print("Parsing 0.34.1 English titles...")
    en_map = get_en_titles()
    print(f"  Found {len(en_map)} spell entries")

    print("Parsing current Chinese titles...")
    zh_map = get_zh_titles()
    print(f"  Found {len(zh_map)} spell entries")

    # Check mismatches
    en_only = set(en_map) - set(zh_map)
    zh_only = set(zh_map) - set(en_map)
    if en_only:
        print(f"WARNING: {len(en_only)} spells in 0.34.1 but not current: {en_only}")
    if zh_only:
        print(f"WARNING: {len(zh_only)} spells in current but not 0.34.1: {zh_only}")

    # Verify English titles are ASCII (no Chinese chars slipped in)
    non_ascii = 0
    for enum, title in en_map.items():
        if any(ord(c) > 127 for c in title):
            print(f"WARNING: Non-ASCII in EN title SPELL_{enum}: {title!r}")
            non_ascii += 1
    if non_ascii:
        print(f"  {non_ascii} titles have non-ASCII characters")

    print("Rebuilding spl-data.h with T_() calls...")
    rebuild_spl_data(en_map, zh_map)

    print("Generating source.txt entries...")
    generate_source_entries(en_map, zh_map)

    print("Done!")


if __name__ == "__main__":
    main()
