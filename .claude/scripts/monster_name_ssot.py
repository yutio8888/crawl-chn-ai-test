#!/usr/bin/env python3
"""Enforce source.txt as the SSOT for unique monster Chinese names.

Checks three kinds of cross-file consistency:
1. Every unique monster YAML `name:` must have a source.txt translation.
2. `dat/database/zh/montitle.txt` title text must include the source.txt name.
3. If the EN description/quote explicitly mentions the monster's English name,
   the ZH counterpart must explicitly mention the source.txt Chinese name.
"""

from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n_shared import parse_source_txt


@dataclass(frozen=True)
class UniqueMonster:
    en_name: str
    yaml_file: str


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _load_unique_monsters(source_dir: str) -> list[UniqueMonster]:
    mons_dir = os.path.join(source_dir, "dat", "mons")
    uniques: list[UniqueMonster] = []
    for fn in sorted(os.listdir(mons_dir)):
        if not fn.endswith(".yaml"):
            continue
        path = os.path.join(mons_dir, fn)
        content = _read(path)
        name_match = re.search(r'^name:\s*"(.+)"\s*$', content, re.MULTILINE)
        if not name_match:
            continue
        flags_match = re.search(r"^flags:\s*\[(.+)\]\s*$", content, re.MULTILINE)
        flags = {
            part.strip()
            for part in flags_match.group(1).split(",")
        } if flags_match else set()
        if "unique" in flags:
            uniques.append(UniqueMonster(name_match.group(1), path))
    return uniques


def _rel(path: str) -> str:
    return os.path.relpath(path, os.getcwd())


def _check_title(entries: dict[str, str], monster: UniqueMonster,
                 zh_name: str, findings: list[str]) -> None:
    title_key = f"{monster.en_name} title".lower()
    zh_title = entries.get(title_key, "").strip()
    if zh_title and zh_name not in zh_title:
        findings.append(
            f"montitle mismatch: {_rel(os.path.join('crawl-ref/source/dat/database/zh/montitle.txt'))}: "
            f"'{monster.en_name} title' uses '{zh_title}', expected to contain SSOT name '{zh_name}'"
        )


def _check_body(kind: str, en_entries: dict[str, str], zh_entries: dict[str, str],
                monster: UniqueMonster, zh_name: str, findings: list[str]) -> None:
    en_body = en_entries.get(monster.en_name.lower(), "")
    zh_body = zh_entries.get(monster.en_name.lower(), "")
    if not en_body or not zh_body:
        return

    if monster.en_name in en_body and zh_name not in zh_body:
        findings.append(
            f"{kind} mismatch: key '{monster.en_name}' explicitly names the monster in EN, "
            f"but ZH text does not contain SSOT name '{zh_name}'"
        )


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] != "--source-txt":
        print("Usage: monster_name_ssot.py --source-txt <source.txt>", file=sys.stderr)
        return 2

    source_txt = os.path.abspath(sys.argv[2])
    source_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(source_txt)))
    )

    src_entries = parse_source_txt(source_txt)
    uniques = _load_unique_monsters(source_dir)

    zh_montitle = parse_source_txt(os.path.join(source_dir, "dat", "database", "zh", "montitle.txt"))
    en_monsters = parse_source_txt(os.path.join(source_dir, "dat", "descript", "monsters.txt"))
    zh_monsters = parse_source_txt(os.path.join(source_dir, "dat", "descript", "zh", "monsters.txt"))
    en_quotes = parse_source_txt(os.path.join(source_dir, "dat", "descript", "quotes.txt"))
    zh_quotes = parse_source_txt(os.path.join(source_dir, "dat", "descript", "zh", "quotes.txt"))

    findings: list[str] = []

    for monster in uniques:
        zh_name = src_entries.get(monster.en_name.lower(), "").strip()
        if not zh_name:
            findings.append(
                f"missing source.txt translation: {monster.en_name} "
                f"({_rel(monster.yaml_file)})"
            )
            continue

        _check_title(zh_montitle, monster, zh_name, findings)
        _check_body("monsters.txt", en_monsters, zh_monsters, monster, zh_name, findings)
        _check_body("quotes.txt", en_quotes, zh_quotes, monster, zh_name, findings)

    if findings:
        print("=== MONSTER NAME SSOT VIOLATIONS ===")
        for item in findings:
            print(f"- {item}")
        print(f"-> {len(findings)} violation(s)")
        return 1

    print(f"OK: {len(uniques)} unique monsters follow source.txt SSOT.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
