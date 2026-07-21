#!/usr/bin/env python3
"""Enforce source.txt as the SSOT for monster Chinese names.

The inventory is every YAML definition under dat/mons. Definitions which use
the same normalized English name are variants of one monster and are checked
once. Unique monsters additionally retain their montitle check; descriptions
and quotations are checked for every normalized monster name.
"""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass
from typing import Mapping


# These quotation entries deliberately use a literary, historical, religious,
# or ordinary-language rendering instead of the in-game monster display name.
# The audit below rejects an exception when its key disappears, either TextDB
# side disappears, the English quote stops naming it, or the Chinese quote is
# changed to contain the SSOT name. This keeps the list narrow and non-stale.
QUOTE_NAME_EXCEPTIONS: dict[str, str] = {
    "Executioner": "The Mikado quotation names the office of Lord High Executioner.",
    "basilisk": "The quotation uses the mythological serpent/cockatrice tradition.",
    "bush": "The Biblical burning bush is a specific scriptural image.",
    "cacodemon": "The word is a character's proper name in the cited play.",
    "cherub": "The Biblical quotation uses the established religious name 基路伯.",
    "daeva": "The quotation uses the Avestan religious term rather than a game monster.",
    "ettin": "Red Ettin is the proper name of a figure in the cited ballad.",
    "goblin": "The Tolkien quotation uses its established 哥布林 rendering.",
    "golden eye": "The words are an ordinary phrase describing a golden eye.",
    "harpy": "Harpyiai is a classical proper name in the cited work.",
    "hobgoblin": "The word is used figuratively, not as the game monster.",
    "jackal": "The natural-history quotation uses the established animal name 胡狼.",
    "kraken": "The Norse creature is referred to by its established proper name 克拉肯.",
    "lindwurm": "The quotation preserves the Germanic creature's proper name.",
    "necromancer": "The occurrence is only in a cited song title.",
    "reaper": "The quotation personifies Death as the Grim Reaper.",
    "salamander": "The natural-history quotation uses the historical 沙罗曼达 rendering.",
    "seraph": "The Biblical quotation uses the established religious name 撒拉弗.",
    "toadstool": "Fly-bane denotes fly agaric specifically, not a generic poisonous mushroom.",
    "wight": "The archaic word means a person in this quotation.",
    "wraith": "The poetic occurrence means an apparition or phantom.",
}


# A key is the complete set of *different normalized English names* which are
# intentionally assigned one Chinese name. Empty today: identical English
# names used by multiple YAML variants are deduplicated before this check.
REVERSE_DUP_EXCEPTIONS: dict[frozenset[str], str] = {}


# Complete word forms used by the literary quotations but not produced by the
# regular English plural rules below.
EN_NAME_IRREGULAR_FORMS: dict[str, tuple[str, ...]] = {
    "harpy": ("Harpyiai",),
    "seraph": ("seraphim", "seraphims"),
}


class AuditInputError(ValueError):
    """A required production input cannot be completely evaluated."""


@dataclass(frozen=True)
class MonsterDefinition:
    en_name: str
    yaml_file: str
    is_unique: bool


@dataclass(frozen=True)
class Monster:
    en_name: str
    yaml_files: tuple[str, ...]
    is_unique: bool


@dataclass(frozen=True)
class AuditResult:
    definition_count: int
    monster_count: int
    unique_count: int
    findings: tuple[str, ...]


def _read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="strict") as stream:
            return stream.read()
    except (OSError, UnicodeError) as exc:
        raise AuditInputError(f"cannot read required input '{path}': {exc}") from exc


def _parse_required_textdb(path: str, *, trim_keys: bool = True) -> dict[str, str]:
    """Parse one required TextDB with database.cc `_parse_text_db` semantics."""
    content = _read(path)
    if "\0" in content:
        raise AuditInputError(f"required TextDB contains an embedded NUL: '{path}'")
    if content.startswith("\ufeff"):
        content = content[1:]

    entries: dict[str, str] = {}
    key = ""
    value = ""
    in_entry = False

    def flush() -> None:
        nonlocal key, value
        if key:
            # database.cc removes leading newlines, retains the final newline,
            # and replaces an earlier definition of the same lowercased key.
            entries[key] = value.lstrip("\n")
        key = ""
        value = ""

    lines = content.split("\n")
    if not content.endswith("\n"):
        # UTF8FileLineInput performs one final empty read before reporting EOF.
        lines.append("")
    for line in lines:
        # Production comments and separators are recognized only at column 0.
        if line.startswith("#"):
            continue
        if line.startswith("%%%%"):
            flush()
            in_entry = True
            continue
        if not in_entry:
            continue
        if not key:
            key = (line.strip() if trim_keys else line).lower()
        else:
            value += line.rstrip() + "\n"
    flush()

    if not entries:
        raise AuditInputError(f"required TextDB contains no entries: '{path}'")
    return entries


def _load_monster_definitions(source_dir: str) -> list[MonsterDefinition]:
    mons_dir = os.path.join(source_dir, "dat", "mons")
    try:
        filenames = sorted(
            name for name in os.listdir(mons_dir) if name.endswith(".yaml")
        )
    except OSError as exc:
        raise AuditInputError(
            f"cannot enumerate monster YAML directory '{mons_dir}': {exc}"
        ) from exc
    if not filenames:
        raise AuditInputError(f"monster YAML inventory is empty: '{mons_dir}'")

    definitions: list[MonsterDefinition] = []
    for filename in filenames:
        path = os.path.join(mons_dir, filename)
        content = _read(path)
        name_lines = re.findall(r"^name:\s*(.*?)\s*$", content, re.MULTILINE)
        if len(name_lines) != 1:
            raise AuditInputError(
                f"monster YAML must contain exactly one top-level name field: "
                f"'{path}' has {len(name_lines)}"
            )
        name_match = re.fullmatch(r'"([^"\n]+)"', name_lines[0])
        if not name_match:
            raise AuditInputError(
                f"monster YAML name must be one non-empty quoted string: '{path}'"
            )

        flags_lines = re.findall(r"^flags:\s*(.*?)\s*$", content, re.MULTILINE)
        if len(flags_lines) > 1:
            raise AuditInputError(
                f"monster YAML has multiple top-level flags fields: '{path}'"
            )
        if flags_lines:
            flags_match = re.fullmatch(r"\[(.*?)\]", flags_lines[0])
            if not flags_match:
                raise AuditInputError(
                    f"monster YAML flags must be a bracketed list: '{path}'"
                )
            flags = {
                part.strip()
                for part in flags_match.group(1).split(",")
                if part.strip()
            }
        else:
            flags = set()
        definitions.append(MonsterDefinition(
            en_name=name_match.group(1),
            yaml_file=path,
            is_unique="unique" in flags,
        ))
    return definitions


def _normalize(name: str) -> str:
    return name.casefold()


def _canonicalize(definitions: list[MonsterDefinition]) -> dict[str, Monster]:
    grouped: dict[str, list[MonsterDefinition]] = defaultdict(list)
    for definition in definitions:
        grouped[_normalize(definition.en_name)].append(definition)
    return {
        key: Monster(
            en_name=group[0].en_name,
            yaml_files=tuple(item.yaml_file for item in group),
            is_unique=any(item.is_unique for item in group),
        )
        for key, group in sorted(grouped.items())
    }


def _rel(path: str) -> str:
    return os.path.relpath(path, os.getcwd())


def _contains(text: str, name: str) -> bool:
    return name.casefold() in text.casefold()


def _contains_en_name(text: str, name: str) -> bool:
    """Match a complete English name, not a substring of a longer word."""
    normalized = name.casefold()
    forms = {name}
    if (normalized.endswith("y") and len(name) > 1
            and normalized[-2] not in "aeiou"):
        forms.add(f"{name[:-1]}ies")
    elif normalized.endswith(("s", "x", "z", "ch", "sh")):
        forms.add(f"{name}es")
    else:
        forms.add(f"{name}s")
    forms.update(EN_NAME_IRREGULAR_FORMS.get(normalized, ()))
    alternatives = "|".join(
        re.escape(form) for form in sorted(forms, key=len, reverse=True)
    )
    pattern = rf"(?<![A-Za-z0-9])(?:{alternatives})(?![A-Za-z0-9])"
    return re.search(pattern, text, flags=re.IGNORECASE | re.ASCII) is not None


def _check_title(entries: Mapping[str, str], monster: Monster,
                 zh_name: str, findings: list[str]) -> None:
    title_key = f"{monster.en_name} title".casefold()
    zh_title = entries.get(title_key, "").strip()
    if zh_title and not _contains(zh_title, zh_name):
        findings.append(
            "montitle mismatch: "
            f"key '{monster.en_name} title' uses '{zh_title}', "
            f"expected to contain SSOT name '{zh_name}'"
        )


def _body_mismatch(en_entries: Mapping[str, str],
                   zh_entries: Mapping[str, str], monster: Monster,
                   zh_name: str) -> bool:
    key = _normalize(monster.en_name)
    en_body = en_entries.get(key, "")
    if not en_body or not _contains_en_name(en_body, monster.en_name):
        return False
    zh_body = zh_entries.get(key, "")
    return not zh_body or not _contains(zh_body, zh_name)


def _check_body(kind: str, en_entries: Mapping[str, str],
                zh_entries: Mapping[str, str], monster: Monster,
                zh_name: str, findings: list[str]) -> None:
    if _body_mismatch(en_entries, zh_entries, monster, zh_name):
        findings.append(
            f"{kind} mismatch: key '{monster.en_name}' explicitly names the "
            f"monster in EN, but ZH text does not contain SSOT name '{zh_name}'"
        )


def _normalize_reverse_exceptions(
    exceptions: Mapping[frozenset[str], str],
    findings: list[str],
) -> dict[frozenset[str], str]:
    normalized: dict[frozenset[str], str] = {}
    for raw_group, reason in exceptions.items():
        group = frozenset(_normalize(name) for name in raw_group)
        if len(group) < 2:
            findings.append(
                f"invalid reverse-duplicate exception {sorted(raw_group)!r}: "
                "must name at least two different English monsters"
            )
        if not reason.strip():
            findings.append(
                f"invalid reverse-duplicate exception {sorted(raw_group)!r}: "
                "reason is empty"
            )
        if group in normalized:
            findings.append(
                f"duplicate reverse-duplicate exception after normalization: {sorted(group)!r}"
            )
        normalized[group] = reason
    return normalized


def _check_reverse_duplicates(
    monsters: Mapping[str, Monster],
    zh_names: Mapping[str, str],
    exceptions: Mapping[frozenset[str], str],
    findings: list[str],
) -> None:
    normalized_exceptions = _normalize_reverse_exceptions(exceptions, findings)
    reverse: dict[str, set[str]] = defaultdict(set)
    for key, zh_name in zh_names.items():
        if zh_name:
            reverse[zh_name.casefold()].add(key)

    actual_groups = {frozenset(group) for group in reverse.values() if len(group) > 1}
    for group in sorted(actual_groups, key=lambda item: sorted(item)):
        if group not in normalized_exceptions:
            display_names = [monsters[key].en_name for key in sorted(group)]
            zh_name = zh_names[next(iter(group))]
            findings.append(
                f"reverse duplicate: SSOT name '{zh_name}' maps different English "
                f"monsters {display_names!r}"
            )

    for group in normalized_exceptions:
        missing = sorted(group - monsters.keys())
        if missing:
            findings.append(
                f"stale reverse-duplicate exception {sorted(group)!r}: "
                f"monster inventory is missing {missing!r}"
            )
            continue
        if group not in actual_groups:
            actual = sorted(
                reverse.get(zh_names[next(iter(group))].casefold(), set())
            )
            findings.append(
                f"stale reverse-duplicate exception {sorted(group)!r}: "
                f"actual complete group is {actual!r}"
            )


def _normalize_quote_exceptions(
    exceptions: Mapping[str, str], findings: list[str]
) -> dict[str, tuple[str, str]]:
    normalized: dict[str, tuple[str, str]] = {}
    for raw_key, reason in exceptions.items():
        key = _normalize(raw_key)
        if not reason.strip():
            findings.append(
                f"invalid quotes.txt exception '{raw_key}': reason is empty"
            )
        if key in normalized:
            findings.append(
                f"duplicate quotes.txt exception after normalization: '{raw_key}'"
            )
        normalized[key] = (raw_key, reason)
    return normalized


def _check_quote_exceptions(
    exceptions: Mapping[str, tuple[str, str]],
    monsters: Mapping[str, Monster],
    zh_names: Mapping[str, str],
    en_quotes: Mapping[str, str],
    zh_quotes: Mapping[str, str],
    findings: list[str],
) -> set[str]:
    valid: set[str] = set()
    for key, (raw_key, reason) in exceptions.items():
        if not reason.strip():
            continue
        monster = monsters.get(key)
        if monster is None:
            findings.append(
                f"stale quotes.txt exception '{raw_key}': key is absent from monster inventory"
            )
            continue
        if key not in en_quotes or key not in zh_quotes:
            missing = []
            if key not in en_quotes:
                missing.append("EN quotes.txt")
            if key not in zh_quotes:
                missing.append("ZH quotes.txt")
            findings.append(
                f"stale quotes.txt exception '{raw_key}': missing {' and '.join(missing)} entry"
            )
            continue
        zh_name = zh_names.get(key, "")
        if not zh_name:
            # The primary missing-translation finding is sufficient and the
            # exception cannot be proven necessary without an SSOT value.
            findings.append(
                f"invalid quotes.txt exception '{raw_key}': SSOT translation is missing"
            )
            continue
        if not _contains_en_name(en_quotes[key], monster.en_name):
            findings.append(
                f"stale quotes.txt exception '{raw_key}': EN quote no longer explicitly names it"
            )
            continue
        if _contains(zh_quotes[key], zh_name):
            findings.append(
                f"stale quotes.txt exception '{raw_key}': ZH quote now contains "
                f"SSOT name '{zh_name}'"
            )
            continue
        valid.add(key)
    return valid


def audit_repository(
    source_dir: str,
    source_txt: str,
    *,
    quote_exceptions: Mapping[str, str] = QUOTE_NAME_EXCEPTIONS,
    reverse_dup_exceptions: Mapping[frozenset[str], str] = REVERSE_DUP_EXCEPTIONS,
) -> AuditResult:
    definitions = _load_monster_definitions(source_dir)
    monsters = _canonicalize(definitions)

    # SourceDB is the sole production TextDB which disables key trimming.
    src_entries = _parse_required_textdb(source_txt, trim_keys=False)
    zh_montitle = _parse_required_textdb(
        os.path.join(source_dir, "dat", "database", "zh", "montitle.txt")
    )
    en_monsters = _parse_required_textdb(
        os.path.join(source_dir, "dat", "descript", "monsters.txt")
    )
    zh_monsters = _parse_required_textdb(
        os.path.join(source_dir, "dat", "descript", "zh", "monsters.txt")
    )
    en_quotes = _parse_required_textdb(
        os.path.join(source_dir, "dat", "descript", "quotes.txt")
    )
    zh_quotes = _parse_required_textdb(
        os.path.join(source_dir, "dat", "descript", "zh", "quotes.txt")
    )

    findings: list[str] = []
    zh_names: dict[str, str] = {}
    for key, monster in monsters.items():
        zh_name = src_entries.get(key, "").strip()
        zh_names[key] = zh_name
        if not zh_name:
            findings.append(
                f"missing source.txt translation: {monster.en_name} "
                f"({', '.join(_rel(path) for path in monster.yaml_files)})"
            )

    _check_reverse_duplicates(
        monsters, zh_names, reverse_dup_exceptions, findings
    )
    normalized_quote_exceptions = _normalize_quote_exceptions(
        quote_exceptions, findings
    )
    valid_quote_exceptions = _check_quote_exceptions(
        normalized_quote_exceptions, monsters, zh_names,
        en_quotes, zh_quotes, findings,
    )

    for key, monster in monsters.items():
        zh_name = zh_names[key]
        if not zh_name:
            continue
        if monster.is_unique:
            _check_title(zh_montitle, monster, zh_name, findings)
        _check_body(
            "monsters.txt", en_monsters, zh_monsters,
            monster, zh_name, findings,
        )
        if key not in valid_quote_exceptions:
            _check_body(
                "quotes.txt", en_quotes, zh_quotes,
                monster, zh_name, findings,
            )

    return AuditResult(
        definition_count=len(definitions),
        monster_count=len(monsters),
        unique_count=sum(monster.is_unique for monster in monsters.values()),
        findings=tuple(findings),
    )


def main() -> int:
    if len(sys.argv) != 3 or sys.argv[1] != "--source-txt":
        print("Usage: monster_name_ssot.py --source-txt <source.txt>", file=sys.stderr)
        return 2

    source_txt = os.path.abspath(sys.argv[2])
    source_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(source_txt)))
    )
    try:
        result = audit_repository(source_dir, source_txt)
    except AuditInputError as exc:
        print("=== MONSTER NAME SSOT INPUT ERROR ===")
        print(f"- {exc}")
        return 1

    if result.findings:
        print("=== MONSTER NAME SSOT VIOLATIONS ===")
        for item in result.findings:
            print(f"- {item}")
        print(f"-> {len(result.findings)} violation(s)")
        return 1

    print(
        f"OK: {result.definition_count} YAML definitions / "
        f"{result.monster_count} normalized monster names "
        "follow source.txt SSOT."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
