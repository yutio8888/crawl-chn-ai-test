#!/usr/bin/env python3
"""Enforce source.txt as the SSOT for monster Chinese names.

The inventory is every YAML definition under dat/mons. Definitions which use
the same normalized English name are variants of one monster and are checked
once. Unique monsters additionally retain their montitle check; descriptions
and quotations are checked for every normalized monster name.
"""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "crawl-ref" / "source"
MONSTER_ENUMS = SRC / "monster-type.h"
MONSTER_DATA_DIR = SRC / "dat" / "mons"
ZH_SOURCE = SRC / "dat" / "i18n" / "zh" / "source.txt"
EN_MONSTER_DESCRIPTIONS = SRC / "dat" / "descript" / "monsters.txt"
ZH_MONSTER_DESCRIPTIONS = SRC / "dat" / "descript" / "zh" / "monsters.txt"
ZH_MONSTER_TITLES = SRC / "dat" / "database" / "zh" / "montitle.txt"
GLOSSARY = ROOT / "docs" / "glossary.md"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_item_name_inventory import active_source  # noqa: E402


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
    enum_identity: str
    yaml_file: str
    is_unique: bool
    flags: tuple[str, ...]
    fields: Mapping[str, str]


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


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _relative(path: str | Path) -> str:
    resolved = Path(path).resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(resolved)


def _read(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="strict") as stream:
            return stream.read()
    except (OSError, UnicodeError) as exc:
        raise AuditInputError(f"cannot read required input '{path}': {exc}") from exc


def _parse_textdb_content(
    path: str,
    content: str,
    *,
    trim_keys: bool = True,
) -> dict[str, str]:
    """Parse TextDB content with database.cc `_parse_text_db` semantics."""
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


def _parse_required_textdb(path: str, *, trim_keys: bool = True) -> dict[str, str]:
    """Parse one required TextDB with database.cc `_parse_text_db` semantics."""
    return _parse_textdb_content(path, _read(path), trim_keys=trim_keys)


def _parse_yaml_top_level(path: str, content: str) -> dict[str, str]:
    """Return deterministic raw values for the mon-gen YAML subset.

    The production generator owns YAML decoding. The audit only needs complete
    top-level evidence and therefore preserves each field as normalized source
    text instead of implementing a second semantic YAML parser.
    """
    fields: dict[str, str] = {}
    current = None
    value_lines: list[str] = []

    def flush() -> None:
        nonlocal current, value_lines
        if current is not None:
            if current in fields:
                raise AuditInputError(
                    f"monster YAML has duplicate top-level field {current!r}: '{path}'"
                )
            fields[current] = "\n".join(value_lines).strip()
        current = None
        value_lines = []

    for line in content.splitlines():
        if not line or line.startswith("#"):
            if current is not None and line:
                value_lines.append(line)
            continue
        match = re.match(r"^([a-z][a-z0-9_]*):(?:\s*(.*))?$", line)
        if match:
            flush()
            current = match.group(1)
            value_lines = [match.group(2) or ""]
        elif current is not None and (line.startswith(" ") or line.startswith("\t")):
            value_lines.append(line)
        else:
            raise AuditInputError(
                f"unsupported top-level monster YAML syntax in '{path}': {line!r}"
            )
    flush()
    if not fields:
        raise AuditInputError(f"monster YAML contains no fields: '{path}'")
    return fields


def _quoted_scalar(fields: Mapping[str, str], key: str, path: str) -> str | None:
    raw = fields.get(key)
    if raw is None:
        return None
    match = re.fullmatch(r'"([^"\n]+)"', raw.strip())
    if not match:
        raise AuditInputError(
            f"monster YAML {key} must be one non-empty quoted string: '{path}'"
        )
    return match.group(1)


def _enum_scalar(fields: Mapping[str, str], key: str, path: str) -> str | None:
    raw = fields.get(key)
    if raw is None:
        return None
    value = raw.strip()
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", value):
        raise AuditInputError(
            f"monster YAML {key} must be an enum token: '{path}'"
        )
    return value.lower()


def _flag_values(fields: Mapping[str, str], path: str) -> tuple[str, ...]:
    raw = fields.get("flags", "[]").strip()
    match = re.fullmatch(r"\[(.*?)\]", raw)
    if not match:
        raise AuditInputError(
            f"monster YAML flags must be a bracketed list: '{path}'"
        )
    flags = tuple(sorted(
        part.strip() for part in match.group(1).split(",") if part.strip()
    ))
    if any(not re.fullmatch(r"[a-z][a-z0-9_]*", flag) for flag in flags):
        raise AuditInputError(f"monster YAML has an invalid flag: '{path}'")
    return flags


def _default_enum(name: str) -> str:
    """Match util/mon-gen.py's default enum derivation exactly."""
    return "MONS_" + name.upper().replace(" ", "_")


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
        fields = _parse_yaml_top_level(path, content)
        name = _quoted_scalar(fields, "name", path)
        if name is None:
            raise AuditInputError(
                f"monster YAML must contain exactly one top-level name field: '{path}'"
            )
        enum_token = _enum_scalar(fields, "enum", path)
        enum_identity = (
            f"MONS_{enum_token.upper()}" if enum_token else _default_enum(name)
        )
        if not re.fullmatch(r"MONS_[A-Z0-9_]+", enum_identity):
            raise AuditInputError(
                f"monster YAML name requires an explicit valid enum: '{path}'"
            )
        flags = _flag_values(fields, path)
        definitions.append(MonsterDefinition(
            en_name=name,
            enum_identity=enum_identity,
            yaml_file=path,
            is_unique="unique" in flags,
            flags=flags,
            fields=fields,
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


def _active_monster_enum_identities(path: Path = MONSTER_ENUMS) -> list[str]:
    """Return concrete save-compatible identities before NUM_MONSTERS."""
    text = active_source(path)
    text = text.split("NUM_MONSTERS", 1)[0]
    identities = []
    for match in re.finditer(
        r"^\s*(MONS_[A-Z0-9_]+)\s*(?:=\s*([^,]+))?\s*,",
        text,
        re.MULTILINE,
    ):
        identity, assignment = match.groups()
        # MONS_0 aliases MONS_PROGRAM_BUG and is not a separate identity.
        if assignment and re.search(r"\bMONS_[A-Z0-9_]+\b", assignment):
            continue
        identities.append(identity)
    if not identities:
        raise AuditInputError(
            f"active monster enum inventory is empty: '{path}'"
        )
    duplicates = sorted(
        identity for identity, count in Counter(identities).items()
        if count > 1
    )
    if duplicates:
        raise AuditInputError(
            f"active monster enum inventory contains duplicates: {duplicates!r}"
        )
    return identities


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


def _textdb_duplicate_keys(path: Path, *, trim_keys: bool = True) -> list[str]:
    content = _read(str(path))
    keys = []
    awaiting_key = False
    for line in content.splitlines():
        if line.startswith("#"):
            continue
        if line.startswith("%%%%"):
            awaiting_key = True
            continue
        if awaiting_key:
            key = (line.strip() if trim_keys else line).casefold()
            if key:
                keys.append(key)
                awaiting_key = False
    return sorted(
        key for key, count in Counter(keys).items() if count > 1
    )


def _field_enum(fields: Mapping[str, str], key: str,
                default: str) -> str:
    value = fields.get(key, default).strip()
    return f"MONS_{value.upper()}"


def _exposure(definition: MonsterDefinition) -> str:
    if (
        "cant_spawn" in definition.flags
        or definition.enum_identity.startswith(("MONS_SENSED", "MONS_TEST_"))
        or definition.enum_identity == "MONS_PROGRAM_BUG"
    ):
        return "internal_or_special"
    if definition.is_unique:
        return "unique"
    return "ordinary"


def _core_facts(fields: Mapping[str, str]) -> dict[str, str | None]:
    keys = (
        "hd", "hp_10x", "ac", "ev", "will", "will_per_hd", "speed",
        "energy", "holiness", "flags", "resists", "attacks", "spells",
        "shout", "intelligence", "uses", "size", "shape", "god",
        "has_corpse",
    )
    return {key: fields.get(key) for key in keys}


def _inventory_rows(
    definitions: list[MonsterDefinition],
    enum_identities: list[str],
    source_entries: Mapping[str, str],
    en_descriptions: Mapping[str, str],
    zh_descriptions: Mapping[str, str],
    zh_titles: Mapping[str, str],
) -> list[dict[str, object]]:
    definitions_by_enum = {
        definition.enum_identity: definition for definition in definitions
    }
    rows: list[dict[str, object]] = []
    for identity in enum_identities:
        definition = definitions_by_enum.get(identity)
        if definition is None:
            rows.append({
                "identity": f"monster:{identity}",
                "enum_identity": identity,
                "lifecycle": "compatibility_enum",
                "exposure": "not_applicable",
                "english_source_name": None,
                "current_chinese_name": None,
                "genus_identity": None,
                "species_identity": None,
                "unique": False,
                "metadata_and_display_context": (
                    "save-compatible monster_type identity without a current "
                    "dat/mons definition; no current mon-data display consumer"
                ),
                "producer_consumer": {
                    "producer": _relative(MONSTER_ENUMS),
                    "consumer": "save compatibility / enum identity only",
                },
                "core_facts": None,
                "english_description": None,
                "chinese_description": None,
                "chinese_title": None,
                "source_file": _relative(MONSTER_ENUMS),
                "production_data": None,
            })
            continue

        key = _normalize(definition.en_name)
        fields = definition.fields
        rows.append({
            "identity": f"monster:{identity}",
            "enum_identity": identity,
            "lifecycle": "current_definition",
            "exposure": _exposure(definition),
            "english_source_name": definition.en_name,
            "current_chinese_name": source_entries.get(key, "").strip() or None,
            "genus_identity": _field_enum(
                fields, "genus",
                fields.get("species", identity.removeprefix("MONS_").lower()),
            ),
            "species_identity": _field_enum(
                fields, "species",
                identity.removeprefix("MONS_").lower(),
            ),
            "unique": definition.is_unique,
            "metadata_and_display_context": (
                "dat/mons -> generated mon-data.h -> mons_class_name / "
                "mons_type_name -> monster_info::common_name; SourceDB "
                "translation is applied only for display"
            ),
            "producer_consumer": {
                "definition": _relative(definition.yaml_file),
                "generator": "crawl-ref/source/util/mon-gen.py",
                "name_consumer": "crawl-ref/source/mon-util.cc:3063",
                "display_consumer": "crawl-ref/source/mon-info.cc:1216",
                "description_consumer": "crawl-ref/source/describe.cc:6944",
            },
            "core_facts": _core_facts(fields),
            "english_description": en_descriptions.get(key),
            "chinese_description": zh_descriptions.get(key),
            "chinese_title": (
                zh_titles.get(f"{key} title") if definition.is_unique else None
            ),
            "source_file": _relative(definition.yaml_file),
            "production_data": dict(fields),
        })
    return rows


def _inventory_violations(
    definitions: list[MonsterDefinition],
    enum_identities: list[str],
    rows: list[dict[str, object]],
    ssot_findings: tuple[str, ...],
) -> dict[str, object]:
    definition_identities = [
        definition.enum_identity for definition in definitions
    ]
    enum_set = set(enum_identities)
    row_identities = [str(row["identity"]) for row in rows]
    return {
        "duplicate_definition_identities": sorted(
            identity for identity, count in Counter(definition_identities).items()
            if count > 1
        ),
        "definition_identities_absent_from_enum": sorted(
            set(definition_identities) - enum_set
        ),
        "duplicate_inventory_identities": sorted(
            identity for identity, count in Counter(row_identities).items()
            if count > 1
        ),
        "missing_current_chinese_names": sorted(
            str(row["identity"]) for row in rows
            if row["lifecycle"] == "current_definition"
            and not row["current_chinese_name"]
        ),
        "ssot_findings": list(ssot_findings),
        "duplicate_description_keys": {
            "english": _textdb_duplicate_keys(EN_MONSTER_DESCRIPTIONS),
            "chinese": _textdb_duplicate_keys(ZH_MONSTER_DESCRIPTIONS),
        },
    }


def build_inventory(
    source_dir: Path = SRC,
    source_txt: Path = ZH_SOURCE,
) -> dict[str, object]:
    definitions = _load_monster_definitions(str(source_dir))
    enum_identities = _active_monster_enum_identities(
        source_dir / "monster-type.h"
    )
    source_entries = _parse_required_textdb(
        str(source_txt), trim_keys=False
    )
    en_descriptions = _parse_required_textdb(
        str(source_dir / "dat/descript/monsters.txt")
    )
    zh_descriptions = _parse_required_textdb(
        str(source_dir / "dat/descript/zh/monsters.txt")
    )
    zh_titles = _parse_required_textdb(
        str(source_dir / "dat/database/zh/montitle.txt")
    )
    ssot = audit_repository(str(source_dir), str(source_txt))
    rows = _inventory_rows(
        definitions,
        enum_identities,
        source_entries,
        en_descriptions,
        zh_descriptions,
        zh_titles,
    )
    violations = _inventory_violations(
        definitions, enum_identities, rows, ssot.findings
    )
    input_paths = [
        source_dir / "monster-type.h",
        source_dir / "util/mon-gen.py",
        source_dir / "dat/mons/README.md",
        *sorted((source_dir / "dat/mons").glob("*.yaml")),
        source_txt,
        source_dir / "dat/database/zh/montitle.txt",
        source_dir / "dat/descript/monsters.txt",
        source_dir / "dat/descript/zh/monsters.txt",
        source_dir / "dat/descript/quotes.txt",
        source_dir / "dat/descript/zh/quotes.txt",
        GLOSSARY,
    ]
    encoded_rows = json.dumps(
        rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    payload: dict[str, object] = {
        "schema": "dcss-monster-review-inventory-v1",
        "baseline": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "glossary_sha256": _sha(GLOSSARY),
        "input_sha256": {
            _relative(path): _sha(path) for path in input_paths
        },
        "inventory_sha256": hashlib.sha256(encoded_rows).hexdigest(),
        "scope": {
            "included": [
                "all concrete monster_type identities before NUM_MONSTERS",
                "all current dat/mons definitions and generated mon-data facts",
                "current and compatibility enum lifecycle",
                "ordinary, unique, internal and special exposure categories",
                "source.txt display names, unique titles and monster descriptions",
                "genus/species relationships, stats, attacks, resists, spells and behaviour fields",
            ],
            "excluded": [
                "post-NUM_MONSTERS sentinels and random-selection pseudo-values",
                "balance changes, AI changes and spawn-table changes",
                "independent spell-name conclusions",
                "generic monspeak dialogue not tied to entity naming",
                "Wiki-derived identity counts",
            ],
        },
        "count": len(rows),
        "definition_count": len(definitions),
        "compatibility_count": sum(
            row["lifecycle"] == "compatibility_enum" for row in rows
        ),
        "lifecycle_counts": {
            lifecycle: sum(row["lifecycle"] == lifecycle for row in rows)
            for lifecycle in sorted({str(row["lifecycle"]) for row in rows})
        },
        "exposure_counts": {
            exposure: sum(row["exposure"] == exposure for row in rows)
            for exposure in sorted({str(row["exposure"]) for row in rows})
        },
        **violations,
        "rows": rows,
    }
    return payload


TERMINAL_CONCLUSIONS = {
    "keep",
    "adjust",
    "retranslate",
    "defer terminology",
    "defer implementation",
}


def _resolve_commit(ref: str) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
            cwd=ROOT,
            text=True,
        ).strip()
    except subprocess.CalledProcessError as error:
        raise AuditInputError(
            f"review baseline does not name a commit: {ref!r}"
        ) from error


def review_coverage(
    payload: Mapping[str, object],
    path: Path,
    baseline_ref: str,
) -> dict[str, object]:
    """Prove one evidence-card row and terminal conclusion per identity."""
    text = path.read_text(encoding="utf-8")
    baseline_oid = _resolve_commit(baseline_ref)
    baseline_matches = re.findall(
        rf"^- 基线：`{re.escape(baseline_oid)}`$",
        text,
        re.MULTILINE,
    )
    expected_text = render_review_results(payload, baseline_oid)
    matches = re.findall(
        r"^\|\s*`(monster:MONS_[A-Z0-9_]+)`\s*\|.*?"
        r"\|\s*([^|\n]+?)\s*\|\s*$",
        text,
        re.MULTILINE,
    )
    identities = [identity for identity, _conclusion in matches]
    conclusions = {
        identity: conclusion.strip() for identity, conclusion in matches
    }
    expected = {str(row["identity"]) for row in payload["rows"]}
    actual = set(identities)
    invalid = sorted(
        identity for identity, conclusion in conclusions.items()
        if conclusion.split(":", 1)[0].strip() not in TERMINAL_CONCLUSIONS
    )
    result = {
        "review_results": _relative(path),
        "review_results_sha256": _sha(path),
        "artifact_exact": text == expected_text,
        "baseline_header_count": len(baseline_matches),
        "evidence_card_count": len(identities),
        "duplicate_evidence_cards": sorted(
            identity for identity, count in Counter(identities).items()
            if count > 1
        ),
        "missing_evidence_cards": sorted(expected - actual),
        "unexpected_evidence_cards": sorted(actual - expected),
        "invalid_terminal_conclusions": invalid,
        "conclusion_counts": {
            conclusion: sum(
                value.split(":", 1)[0].strip() == conclusion
                for value in conclusions.values()
            )
            for conclusion in sorted(TERMINAL_CONCLUSIONS)
        },
    }
    result["coverage_equal"] = (
        len(identities) == len(expected)
        and actual == expected
        and not result["duplicate_evidence_cards"]
        and not invalid
        and result["artifact_exact"]
    )
    return result


def _git_text(ref: str, path: Path) -> str:
    relative = _relative(path)
    try:
        return subprocess.check_output(
            ["git", "show", f"{ref}:{relative}"],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="strict",
        )
    except subprocess.CalledProcessError as error:
        raise AuditInputError(
            f"cannot read baseline input {relative!r} at {ref!r}"
        ) from error


def render_review_results(
    payload: Mapping[str, object],
    baseline_ref: str,
) -> str:
    """Render one evidence-backed terminal conclusion per frozen identity."""
    baseline_ref = _resolve_commit(baseline_ref)
    baseline_names = _parse_textdb_content(
        f"{baseline_ref}:{_relative(ZH_SOURCE)}",
        _git_text(baseline_ref, ZH_SOURCE),
        trim_keys=False,
    )
    current_names = _parse_required_textdb(
        str(ZH_SOURCE), trim_keys=False
    )
    baseline_descriptions = _parse_textdb_content(
        f"{baseline_ref}:{_relative(ZH_MONSTER_DESCRIPTIONS)}",
        _git_text(baseline_ref, ZH_MONSTER_DESCRIPTIONS),
    )
    current_descriptions = _parse_required_textdb(
        str(ZH_MONSTER_DESCRIPTIONS)
    )

    lines = [
        "# Issue #24 怪物翻译全量复审结果",
        "",
        f"- 基线：`{baseline_ref}`",
        f"- 术语表 SHA-256：`{payload['glossary_sha256']}`",
        f"- 清单 SHA-256：`{payload['inventory_sha256']}`",
        f"- 身份总数：{payload['count']}（现行 {payload['definition_count']}；"
        f"兼容枚举 {payload['compatibility_count']}）",
        "- 证据规则：每行绑定 enum 身份、生命周期、暴露类型、现行中英名称、"
        "genus/species、生产数据文件及描述存在性；完整原始字段由同一清单"
        "命令生成的 JSON 提供。",
        "- 终态规则：兼容枚举没有现行 `dat/mons` 定义或显示消费者，"
        "统一记为 `defer implementation`；现行项逐项对照后，未改动者为 "
        "`keep`，名称改动为 `adjust`，描述改动为 `retranslate`。",
        "- 重建命令："
        "`python3 .claude/scripts/monster_name_ssot.py "
        "--inventory-output /tmp/monster-inventory.json "
        "--review-results docs/monster-review-results.md "
        f"--baseline-ref {baseline_ref}`。",
        "",
        "| 身份 | 证据卡 | 终态结论 |",
        "|---|---|---|",
    ]
    for row in payload["rows"]:
        identity = str(row["identity"])
        if row["lifecycle"] == "compatibility_enum":
            evidence = (
                "compatibility_enum; exposure=N/A; current consumer=none; "
                f"source={row['source_file']}"
            )
            conclusion = (
                "defer implementation: restore only with a current definition "
                "and display consumer"
            )
        else:
            key = _normalize(str(row["english_source_name"]))
            name_changed = baseline_names.get(key) != current_names.get(key)
            description_changed = (
                baseline_descriptions.get(key) != current_descriptions.get(key)
            )
            evidence = (
                f"current; exposure={row['exposure']}; "
                f"name={row['english_source_name']}→{row['current_chinese_name']}; "
                f"genus={row['genus_identity']}; species={row['species_identity']}; "
                f"data={row['source_file']}; "
                f"desc={'EN/ZH' if row['english_description'] and row['chinese_description'] else 'N/A'}"
            )
            if description_changed:
                conclusion = (
                    "retranslate: name and description corrected"
                    if name_changed else
                    "retranslate: description corrected"
                )
            elif name_changed:
                conclusion = "adjust: display name corrected"
            else:
                conclusion = "keep"
        lines.append(f"| `{identity}` | {evidence} | {conclusion} |")

    return "\n".join(lines) + "\n"


def write_review_results(
    payload: Mapping[str, object],
    output: Path,
    baseline_ref: str,
) -> None:
    """Write the deterministic per-identity review ledger."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_review_results(payload, baseline_ref),
        encoding="utf-8",
    )


def inventory_has_violations(payload: Mapping[str, object]) -> bool:
    keys = (
        "duplicate_definition_identities",
        "definition_identities_absent_from_enum",
        "duplicate_inventory_identities",
        "missing_current_chinese_names",
        "ssot_findings",
    )
    duplicate_descriptions = payload["duplicate_description_keys"]
    return (
        any(payload[key] for key in keys)
        or any(duplicate_descriptions.values())
    )


def _run_ssot(source_txt: str) -> int:
    source_txt = os.path.abspath(source_txt)
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--source-txt",
        help="run the blocking monster-name SSOT check",
    )
    mode.add_argument(
        "--inventory-output",
        type=Path,
        help="write the deterministic Issue #24 JSON inventory",
    )
    parser.add_argument(
        "--review-results",
        type=Path,
        help="prove exact evidence-card and terminal-conclusion coverage",
    )
    parser.add_argument(
        "--write-review-results",
        type=Path,
        help="write the Issue #24 per-identity review ledger",
    )
    parser.add_argument(
        "--baseline-ref",
        help="git ref used to classify review-result changes",
    )
    args = parser.parse_args(argv)
    if args.source_txt:
        if args.review_results or args.write_review_results or args.baseline_ref:
            parser.error("review options require --inventory-output")
        return _run_ssot(args.source_txt)
    needs_baseline = bool(args.write_review_results or args.review_results)
    if needs_baseline != bool(args.baseline_ref):
        parser.error(
            "--baseline-ref is required by, and only valid with, review options"
        )

    try:
        payload = build_inventory()
        if args.write_review_results:
            write_review_results(
                payload, args.write_review_results, args.baseline_ref
            )
        if args.review_results:
            payload["review_coverage"] = review_coverage(
                payload, args.review_results, args.baseline_ref
            )
    except (
        AuditInputError,
        OSError,
        RuntimeError,
        subprocess.SubprocessError,
        ValueError,
    ) as error:
        print(f"ERROR: monster inventory could not be built: {error}",
              file=sys.stderr)
        return 2

    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    args.inventory_output.parent.mkdir(parents=True, exist_ok=True)
    args.inventory_output.write_text(encoded, encoding="utf-8")
    summary_keys = (
        "baseline",
        "glossary_sha256",
        "inventory_sha256",
        "count",
        "definition_count",
        "compatibility_count",
        "lifecycle_counts",
        "exposure_counts",
        "duplicate_definition_identities",
        "definition_identities_absent_from_enum",
        "duplicate_inventory_identities",
        "missing_current_chinese_names",
        "ssot_findings",
        "duplicate_description_keys",
    )
    summary = {key: payload[key] for key in summary_keys}
    if "review_coverage" in payload:
        summary["review_coverage"] = payload["review_coverage"]
    print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
    coverage_failed = (
        "review_coverage" in payload
        and not payload["review_coverage"]["coverage_equal"]
    )
    return 1 if inventory_has_violations(payload) or coverage_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
