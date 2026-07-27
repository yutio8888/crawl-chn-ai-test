#!/usr/bin/env python3
"""Freeze the Issue #27 character-mechanics translation inventory.

The inventory is derived from production C++ enums/initializers and TextDB
inputs.  It covers mutations, displayed player durations/statuses,
non-religious abilities, skills/titles, core stats, and monster-status
description slots.  God-specific abilities are recorded as explicit
exclusions because Issue #25 owns their identity conclusions.
"""

import argparse
from collections import Counter
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n_shared import AuditRootError, resolve_audit_root  # noqa: E402

try:
    ROOT = resolve_audit_root(SCRIPT_ROOT)
except AuditRootError as error:
    print(f"ERROR: invalid audit root: {error}", file=sys.stderr)
    raise SystemExit(2)

SRC = ROOT / "crawl-ref/source"
ZH_SOURCE_DIR = SRC / "dat/i18n/zh"

MUTATION_TYPE = SRC / "mutation-type.h"
MUTATION_DATA = SRC / "mutation-data.h"
DURATION_TYPE = SRC / "duration-type.h"
DURATION_DATA = SRC / "duration-data.h"
STATUS_TYPE = SRC / "status.h"
STATUS_CODE = SRC / "status.cc"
ABILITY_TYPE = SRC / "ability-type.h"
ABILITY_CODE = SRC / "ability.cc"
SKILL_TYPE = SRC / "skill-type.h"
SKILL_CODE = SRC / "skills.cc"
STAT_TYPE = SRC / "stat-type.h"
STAT_CODE = SRC / "player-stats.cc"

DESCRIPTION_FILES = {
    "mutation": (
        SRC / "dat/descript/mutations.txt",
        SRC / "dat/descript/zh/mutations.txt",
    ),
    "status": (
        SRC / "dat/descript/status.txt",
        SRC / "dat/descript/zh/status.txt",
    ),
    "monster_status": (
        SRC / "dat/descript/monstatus.txt",
        SRC / "dat/descript/zh/monstatus.txt",
    ),
    "ability": (
        SRC / "dat/descript/ability.txt",
        SRC / "dat/descript/zh/ability.txt",
    ),
    "skill": (
        SRC / "dat/descript/skills.txt",
        SRC / "dat/descript/zh/skills.txt",
    ),
}

from audit_god_inventory import (  # noqa: E402
    _matching_brace,
    _strip_cpp_comments,
    exact_function_body,
    ordered_initializer_rows,
)
from audit_item_name_inventory import (  # noqa: E402
    active_source,
    sha,
    source_entries,
    source_files,
)
from i18n_shared import (  # noqa: E402
    parse_entries_physical,
    runtime_normalize_value,
)


TERMINAL_CONCLUSIONS = {
    "keep",
    "adjust",
    "retranslate",
    "defer terminology",
    "defer implementation",
    "保留",
    "修订",
    "重译",
    "暂缓术语",
    "暂缓实现",
}
CHARACTER_REVIEW_BASE = "76c815b2ac79d11a8066597ad04d127a1636e153"
STRICT_REVIEW_BEGIN = "<!-- BEGIN STRICT REVIEW EVIDENCE v1 -->"
STRICT_REVIEW_END = "<!-- END STRICT REVIEW EVIDENCE v1 -->"
STRICT_CARD_FIELDS = {
    "fact_sha256", "identity", "terminal_conclusion",
}

REVISED_MUTATION_IDENTITIES = {
    "MUT_ACIDIC_BITE",
    "MUT_ANTIMAGIC_BITE",
    "MUT_ANTI_WIZARDRY",
    "MUT_ARTEFACT_ENCHANTING",
    "MUT_BEAK",
    "MUT_CLEVER",
    "MUT_CLUMSY",
    "MUT_CONSTRICTING_TAIL",
    "MUT_COWARDICE",
    "MUT_DISTORTION_FIELD",
    "MUT_DOPEY",
    "MUT_DOUBLE_POTION_HEAL",
    "MUT_DRUNKEN_BRAWLING",
    "MUT_EFFICIENT_MAGIC",
    "MUT_EXPLORE_REGEN",
    "MUT_FANGS",
    "MUT_FEED_OFF_SUFFERING",
    "MUT_FOUL_STENCH",
    "MUT_FRAIL",
    "MUT_FORMLESS",
    "MUT_HIGH_MAGIC",
    "MUT_HEX_ENHANCER",
    "MUT_HORNS",
    "MUT_HP_CASTING",
    "MUT_IGNITE_BLOOD",
    "MUT_INITIALLY_ATTRACTIVE",
    "MUT_INVIOLATE_MAGIC",
    "MUT_IRON_FUSED_SCALES",
    "MUT_LOW_MAGIC",
    "MUT_LUCKY",
    "MUT_MAKHLEB_MARK_CELEBRANT",
    "MUT_MAKHLEB_MARK_EXECUTION",
    "MUT_MANA_LINK",
    "MUT_MANA_REGENERATION",
    "MUT_MANA_SHIELD",
    "MUT_MEEK",
    "MUT_MERTAIL",
    "MUT_MISSING_HAND",
    "MUT_MNEMOPHAGE",
    "MUT_MOLTEN_SCALES",
    "MUT_MP_WANDS",
    "MUT_NO_FORGECRAFT_MAGIC",
    "MUT_NO_AIR_MAGIC",
    "MUT_NO_ARTIFICE",
    "MUT_NO_ARMOUR",
    "MUT_NO_ARMOUR_SKILL",
    "MUT_NO_CONJURATION_MAGIC",
    "MUT_NO_EARTH_MAGIC",
    "MUT_NO_FIRE_MAGIC",
    "MUT_NO_FORMS",
    "MUT_NO_HEXES_MAGIC",
    "MUT_NO_ICE_MAGIC",
    "MUT_NO_JEWELLERY",
    "MUT_NO_REGENERATION",
    "MUT_NO_SUMMONING_MAGIC",
    "MUT_NO_TRANSLOCATION_MAGIC",
    "MUT_POWERED_BY_PAIN",
    "MUT_POOR_CONSTITUTION",
    "MUT_REFLEXIVE_HEADBUTT",
    "MUT_RENOUNCE_SCROLLS",
    "MUT_ROLLPAGE",
    "MUT_RUGGED_BROWN_SCALES",
    "MUT_RUNIC_MAGIC",
    "MUT_SHAGGY_FUR",
    "MUT_SHARP_SCALES",
    "MUT_SLIME_SHROUD",
    "MUT_SPATIAL_ENTANGLEMENT",
    "MUT_SPINY",
    "MUT_STURDY_FRAME",
    "MUT_TELEPORTITIS",
    "MUT_THIN_SKELETAL_STRUCTURE",
    "MUT_TOUGH_SKIN",
    "MUT_TREASURE_SENSE",
    "MUT_WIELD_OFFHAND",
}

REVISED_DURATION_IDENTITIES = {
    "DUR_ACROBAT",
    "DUR_AMBROSIA",
    "DUR_CACOPHONY",
    "DUR_GOZAG_GOLD_AURA",
    "DUR_HEAVENLY_STORM",
    "DUR_OOZE_REGEN",
    "DUR_PARRYING",
    "DUR_PHALANX_BARRIER",
    "DUR_SANGUINE_ARMOUR",
    "DUR_SPWPN_PROTECTION",
    "DUR_TROGS_HAND",
}

REVISED_STATUS_IDENTITIES = {
    "STATUS_CANINE_FAMILIAR_ACTIVE",
    "STATUS_DUEL",
    "STATUS_NO_SCROLL",
    "STATUS_RF_ZERO",
    "STATUS_SERPENTS_LASH",
    "STATUS_SILENCE",
}

REVISED_MONSTER_STATUS_KEYS = {
    "lost in madness monstatus",
    "mute monstatus",
    "stupefied monstatus",
}

STATUS_PRODUCERLESS_EXCEPTIONS = {"STATUS_IN_DEBT"}


def relative(path):
    path = path.resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def cpp_strings(text):
    """Decode ordinary C++ string literals from one initializer fragment."""
    values = []
    for raw in re.findall(r'"((?:[^"\\]|\\.)*)"', text):
        try:
            values.append(json.loads(f'"{raw}"'))
        except json.JSONDecodeError as error:
            raise ValueError(f"unsupported C++ string literal: {raw!r}") from error
    return values


def initializer_fields(row):
    row = row.strip()
    if not row.startswith("{"):
        raise ValueError(f"initializer row does not start with '{{': {row[:60]}")
    return ordered_initializer_rows(
        f"static const int temporary[] = {row};",
        r"\btemporary\s*\[\]",
    )


def concrete_enum_identities(path, prefix):
    identities = []
    for line in active_source(path).splitlines():
        match = re.match(
            rf"^\s*({re.escape(prefix)}[A-Z0-9_]+)"
            r"\s*(?:=\s*([^,]+))?\s*,",
            line,
        )
        if not match:
            continue
        rhs = (match.group(2) or "").strip()
        if rhs and re.fullmatch(
            rf"{re.escape(prefix)}[A-Z0-9_]+", rhs
        ):
            continue
        identities.append(match.group(1))
    if not identities:
        raise RuntimeError(f"no {prefix} identities parsed from {relative(path)}")
    return identities


def description_entries(path):
    entries = parse_entries_physical(str(path))
    counts = Counter(entry.canonical_key for entry in entries)
    effective = {}
    raw_keys = {}
    for entry in entries:
        effective[entry.canonical_key] = runtime_normalize_value(entry.value)
        raw_keys[entry.canonical_key] = entry.raw_key
    return effective, raw_keys, sorted(
        key for key, count in counts.items() if count > 1
    )


def translation(db, english, context=None):
    key = f"{context}|{english}" if context else english
    value = db.get(key.lower())
    resolved_key = key
    if value is None and context:
        value = db.get(english.lower())
        resolved_key = english
    return {
        "english": english,
        "lookup_key": key,
        "resolved_lookup_key": resolved_key if value is not None else None,
        "chinese": value,
        "translation_present": bool(value),
    }


def case_fragments(body, prefix):
    matches = list(re.finditer(
        r"\bcase\s+((?:STATUS_|DUR_)[A-Z0-9_]+)\s*:", body
    ))
    result = {}
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        default = re.search(r"\bdefault\s*:", body[match.end():end])
        if default:
            end = match.end() + default.start()
        if match.group(1).startswith(prefix):
            result[match.group(1)] = body[match.start():end].strip()
    return result


def status_display_literals(fragment):
    display = []
    assignments = re.finditer(
        r"\binf\.(light_text|short_text|long_text)\s*=\s*(.*?);",
        fragment,
        re.DOTALL,
    )
    for assignment in assignments:
        expression = assignment.group(2)
        values = cpp_strings(expression)
        if re.search(r'\bC_\s*\(\s*"status"\s*,', expression):
            values = [value for value in values if value != "status"]
        for value in values:
            if value and value not in display:
                display.append(value)
    return display


def status_db_keys(fragment):
    return sorted(set(re.findall(
        r'\binf\.db_key\s*=\s*"((?:[^"\\]|\\.)*)"', fragment
    )))


def status_producer_proof(declared, fragments, source):
    """Prove enum/producer conservation and resolve one helper call."""
    declared_set = set(declared)
    producer_set = set(fragments)
    resolved = {}
    unresolved = []
    for identity in sorted(producer_set & declared_set):
        fragment = fragments[identity]
        calls = re.findall(
            r"\b(_describe_[a-z0-9_]+)\s*\(\s*inf\s*\)\s*;",
            fragment,
        )
        mentions = set(re.findall(r"\b(_describe_[a-z0-9_]+)\b", fragment))
        if mentions != set(calls) or len(calls) > 1:
            unresolved.append(identity)
            resolved[identity] = fragment
            continue
        if not calls:
            resolved[identity] = fragment
            continue
        try:
            helper = exact_function_body(
                _strip_cpp_comments(source),
                rf"\b(?:static\s+)?void\s+{re.escape(calls[0])}",
            )
        except RuntimeError:
            unresolved.append(identity)
            resolved[identity] = fragment
            continue
        if re.search(r"\b_describe_[a-z0-9_]+\s*\(", helper):
            unresolved.append(identity)
            resolved[identity] = fragment
            continue
        resolved[identity] = fragment + "\n" + helper
    return {
        "resolved_fragments": resolved,
        "missing_status_producers": sorted(
            declared_set - producer_set - STATUS_PRODUCERLESS_EXCEPTIONS
        ),
        "unexpected_status_producers": sorted(producer_set - declared_set),
        "stale_producerless_status_exceptions": sorted(
            exception for exception in STATUS_PRODUCERLESS_EXCEPTIONS
            if exception not in declared_set or exception in producer_set
        ),
        "unresolved_status_helpers": unresolved,
    }


def mutation_rows(db, descriptions):
    en_desc, zh_desc = descriptions
    rows = []
    data_rows = ordered_initializer_rows(
        active_source(MUTATION_DATA),
        r"\bstatic\s+const\s+mutation_def\s+mut_data\s*\[\]",
    )
    for raw in data_rows:
        fields = initializer_fields(raw)
        identity_match = re.search(r"\b(MUT_[A-Z0-9_]+)\b", fields[0])
        strings = cpp_strings(raw)
        if not identity_match or not strings:
            raise RuntimeError(f"unparsed mutation initializer: {raw[:100]}")
        identity = identity_match.group(1)
        number_match = re.match(
            r"\s*\{\s*MUT_[A-Z0-9_]+\s*,\s*(-?\d+)\s*,\s*(\d+)\s*,",
            raw,
            re.S,
        )
        if not number_match:
            raise RuntimeError(f"unparsed mutation weight/levels: {identity}")
        short_desc = strings[0]
        desc_key = f"{short_desc} mutation"
        display_strings = [value for value in strings if value]
        rows.append({
            "identity": f"mutation:{identity}",
            "category": "mutation",
            "lifecycle": (
                "internal"
                if identity == "MUT_REMOVED_MUTATION"
                else "current"
            ),
            "english_source_name": short_desc,
            "current_chinese_name": translation(
                db, short_desc, "mutation"
            )["chinese"],
            "levels": int(number_match.group(2)),
            "weight": int(number_match.group(1)),
            "flags": fields[3].strip(),
            "display_strings": [
                translation(
                    db,
                    value,
                    "mutation" if index == 0 else None,
                )
                for index, value in enumerate(display_strings)
            ],
            "description_key": desc_key,
            "english_description": en_desc.get(desc_key.lower()),
            "chinese_description": zh_desc.get(desc_key.lower()),
            "source_file": relative(MUTATION_DATA),
        })
    return rows


def duration_rows(db):
    rows = []
    data_rows = ordered_initializer_rows(
        active_source(DURATION_DATA),
        r"\bstatic\s+const\s+duration_def\s+duration_data\s*\[\]",
    )
    for raw in data_rows:
        fields = initializer_fields(raw)
        match = re.search(r"\b(DUR_[A-Z0-9_]+)\b", fields[0])
        if not match or len(fields) < 6:
            raise RuntimeError(f"unparsed duration initializer: {raw[:100]}")
        strings = [cpp_strings(field) for field in fields[2:6]]
        if any(len(values) != 1 for values in strings):
            raise RuntimeError(f"unparsed duration display fields: {match.group(1)}")
        light, short, name, long_text = [values[0] for values in strings]
        lifecycle = "current" if any((light, short, long_text)) else "internal"
        display_name = short or light
        display_strings = [
            translation(db, value, "status")
            for value in dict.fromkeys((light, short, long_text))
            if value
        ]
        rows.append({
            "identity": f"duration:{match.group(1)}",
            "category": "duration",
            "lifecycle": lifecycle,
            "english_source_name": display_name or name,
            "current_chinese_name": (
                translation(db, display_name, "status")["chinese"]
                if display_name else None
            ),
            "light": translation(db, light, "status") if light else None,
            "short": translation(db, short, "status") if short else None,
            "internal_name": name or None,
            "long": translation(db, long_text) if long_text else None,
            "display_strings": display_strings,
            "flags": fields[6].strip() if len(fields) > 6 else "",
            "source_file": relative(DURATION_DATA),
        })
    return rows


def status_rows(db, with_proof=False):
    source = active_source(STATUS_CODE)
    body = exact_function_body(
        source,
        r"\bbool\s+fill_status_info",
    )
    fragments = case_fragments(body, "STATUS_")
    declared = concrete_enum_identities(STATUS_TYPE, "STATUS_")
    proof = status_producer_proof(declared, fragments, source)
    rows = []
    for identity in declared:
        fragment = proof["resolved_fragments"].get(identity, "")
        display = [
            translation(db, value, "status")
            for value in status_display_literals(fragment)
        ]
        db_keys = status_db_keys(fragment)
        producer_present = identity in fragments
        rows.append({
            "identity": f"status:{identity}",
            "category": "status",
            "lifecycle": "current" if producer_present else "internal",
            "english_source_name": db_keys[0] if db_keys else identity,
            "current_chinese_name": (
                translation(db, db_keys[0], "status")["chinese"]
                if db_keys else None
            ),
            "db_keys": db_keys,
            "display_strings": display,
            "producer_present": producer_present,
            "source_file": relative(STATUS_CODE),
        })
    if with_proof:
        return rows, {
            key: value for key, value in proof.items()
            if key != "resolved_fragments"
        }
    return rows


def ability_rows(db, descriptions):
    en_desc, zh_desc = descriptions
    rows = ordered_initializer_rows(
        active_source(ABILITY_CODE),
        r"\bstatic\s+vector\s*<\s*ability_def\s*>\s+Ability_List",
    )
    parsed = []
    excluded = []
    religious = False
    for raw in rows:
        fields = initializer_fields(raw)
        match = re.search(r"\b(ABIL_[A-Z0-9_]+)\b", fields[0])
        if not match:
            raise RuntimeError(f"unparsed ability initializer: {raw[:100]}")
        identity = match.group(1)
        if identity == "ABIL_ZIN_RECITE":
            religious = True
        is_excluded = religious or identity.startswith("ABIL_WIZ_")
        if identity == "ABIL_CONVERT_TO_BEOGH":
            religious = False
        strings = cpp_strings(fields[1])
        if not strings:
            raise RuntimeError(f"ability has no literal name: {identity}")
        name = strings[-1]
        if is_excluded:
            excluded.append(identity)
            continue
        desc_key = f"{name} ability"
        parsed.append({
            "identity": f"ability:{identity}",
            "category": "ability",
            "lifecycle": (
                "internal" if identity == "ABIL_NON_ABILITY" else "current"
            ),
            "english_source_name": name,
            "current_chinese_name": translation(db, name)["chinese"],
            "description_key": desc_key,
            "english_description": en_desc.get(desc_key.lower()),
            "chinese_description": zh_desc.get(desc_key.lower()),
            "production_initializer": re.sub(r"\s+", " ", raw).strip(),
            "source_file": relative(ABILITY_CODE),
        })
    return parsed, excluded


def useless_skills():
    body = exact_function_body(
        active_source(SKILL_CODE),
        r"\bbool\s+is_removed_skill",
    )
    return set(re.findall(r"\bcase\s+(SK_[A-Z0-9_]+)\s*:", body))


def skill_rows(db, descriptions):
    en_desc, zh_desc = descriptions
    identities = concrete_enum_identities(SKILL_TYPE, "SK_")
    identities = identities[:identities.index("SK_BLANK_LINE")]
    source = active_source(SKILL_CODE)
    table_rows = ordered_initializer_rows(
        source,
        r"\bstatic\s+const\s+char\s*\*\s*skill_titles"
        r"\s*\[\s*NUM_SKILLS\s*\]\s*\[\s*7\s*\]",
    )
    if len(identities) != len(table_rows):
        raise RuntimeError(
            f"skill enum/table mismatch: {len(identities)} != {len(table_rows)}"
        )
    special_title_sets = {}
    for array_name in ("martial_arts_titles", "claw_and_tooth_titles"):
        match = re.search(
            rf"\bstatic\s+const\s+char\s*\*\s*{array_name}"
            r"\s*\[\s*6\s*\]\s*=\s*\{(.*?)\}\s*;",
            source,
            re.DOTALL,
        )
        if not match:
            raise RuntimeError(f"missing special skill title array: {array_name}")
        strings = cpp_strings(match.group(1))
        if len(strings) != 6 or strings[0] != "Unarmed Combat":
            raise RuntimeError(
                f"unexpected special skill titles: {array_name}: {strings}"
            )
        special_title_sets[array_name] = [
            translation(db, title) for title in strings[1:]
        ]
    obsolete = useless_skills()
    rows = []
    for identity, raw in zip(identities, table_rows):
        strings = cpp_strings(raw)
        if len(strings) != 7:
            raise RuntimeError(f"skill row has {len(strings)} fields: {identity}")
        name, *rest = strings
        titles, abbreviation = rest[:5], rest[5]
        row = {
            "identity": f"skill:{identity}",
            "category": "skill",
            "lifecycle": "compatibility" if identity in obsolete else "current",
            "english_source_name": name,
            "current_chinese_name": translation(db, name)["chinese"],
            "titles": [translation(db, title) for title in titles],
            "abbreviation": abbreviation,
            "description_key": name,
            "english_description": en_desc.get(name.lower()),
            "chinese_description": zh_desc.get(name.lower()),
            "source_file": relative(SKILL_CODE),
        }
        if identity == "SK_UNARMED_COMBAT":
            row["special_title_sets"] = special_title_sets
        rows.append(row)
    return rows


def attribute_rows(db):
    identities = concrete_enum_identities(STAT_TYPE, "STAT_")
    identities = identities[:identities.index("STAT_ALL")]
    table_rows = ordered_initializer_rows(
        active_source(STAT_CODE),
        r"\bstatic\s+const\s+char\s*\*\s*descs"
        r"\s*\[\s*NUM_STATS\s*\]\s*\[\s*NUM_STAT_DESCS\s*\]",
    )
    if len(identities) != len(table_rows):
        raise RuntimeError("stat enum/table mismatch")
    rows = []
    for identity, raw in zip(identities, table_rows):
        strings = cpp_strings(raw)
        if len(strings) != 4:
            raise RuntimeError(f"stat row has {len(strings)} fields: {identity}")
        rows.append({
            "identity": f"attribute:{identity}",
            "category": "attribute",
            "lifecycle": "current",
            "english_source_name": strings[0],
            "current_chinese_name": translation(db, strings[0])["chinese"],
            "display_strings": [translation(db, value) for value in strings],
            "source_file": relative(STAT_CODE),
        })
    return rows


def monster_status_rows(descriptions):
    en_desc, zh_desc = descriptions
    return [{
        "identity": f"monster_status:{key}",
        "category": "monster_status",
        "lifecycle": "current",
        "english_source_name": key,
        "current_chinese_name": key,
        "description_key": key,
        "english_description": value,
        "chinese_description": zh_desc.get(key),
        "source_file": relative(DESCRIPTION_FILES["monster_status"][0]),
    } for key, value in sorted(en_desc.items())]


def description_payload():
    result = {}
    for category, (english, chinese) in DESCRIPTION_FILES.items():
        en, en_raw, en_dup = description_entries(english)
        zh, zh_raw, zh_dup = description_entries(chinese)
        result[category] = {
            "english": en,
            "chinese": zh,
            "english_raw_keys": en_raw,
            "chinese_raw_keys": zh_raw,
            "duplicate_english_keys": en_dup,
            "duplicate_chinese_keys": zh_dup,
            "missing_chinese_keys": sorted(set(en) - set(zh)),
            "unexpected_chinese_keys": sorted(set(zh) - set(en)),
        }
    return result


def inventory_violations(rows, descriptions, status_proof=None):
    identities = [row["identity"] for row in rows]
    missing_names = sorted(
        row["identity"] for row in rows
        if row["category"] in {"mutation", "ability", "skill", "attribute"}
        and row["lifecycle"] == "current"
        and not row.get("current_chinese_name")
    )
    missing_descriptions = sorted(
        row["identity"] for row in rows
        if row["category"] in {"mutation", "ability", "skill", "monster_status"}
        and row["lifecycle"] == "current"
        and (
            not row.get("english_description")
            or not row.get("chinese_description")
        )
    )
    missing_display = sorted(
        f"{row['identity']}:{item['lookup_key']}"
        for row in rows
        if row["category"] in {
            "mutation",
            "duration",
            "status",
            "skill",
            "attribute",
        }
        and row["lifecycle"] == "current"
        for field in ("display_strings", "titles")
        for item in row.get(field, [])
        if item["english"] and not item["translation_present"]
    )
    required_status_facts = {
        "status:STATUS_AIRBORNE": {
            "db_keys": {"Fly"},
            "display": {"Fly", "flying", "You are flying."},
        },
    }
    missing_status_display_facts = []
    rows_by_identity = {row["identity"]: row for row in rows}
    for identity, expected_facts in required_status_facts.items():
        row = rows_by_identity.get(identity)
        if row is None:
            missing_status_display_facts.append(identity)
            continue
        actual_display = {
            item.get("english") for item in row.get("display_strings", [])
        }
        if (
            not expected_facts["db_keys"].issubset(set(row.get("db_keys", [])))
            or not expected_facts["display"].issubset(actual_display)
        ):
            missing_status_display_facts.append(identity)
    return {
        "duplicate_identities": sorted(
            identity for identity, count in Counter(identities).items()
            if count > 1
        ),
        "missing_chinese_names": missing_names,
        "missing_descriptions": missing_descriptions,
        "missing_display_translations": missing_display,
        "missing_status_display_facts": missing_status_display_facts,
        "description_findings": {
            category: {
                key: value
                for key, value in payload.items()
                if key.startswith("duplicate_")
                or key.endswith("_chinese_keys")
            }
            for category, payload in descriptions.items()
        },
        **(status_proof or {
            "missing_status_producers": [],
            "unexpected_status_producers": [],
            "stale_producerless_status_exceptions": [],
            "unresolved_status_helpers": [],
        }),
    }


def has_violations(payload):
    findings = payload["violations"]
    if any(
        findings[key] for key in (
            "duplicate_identities",
            "missing_chinese_names",
            "missing_descriptions",
            "missing_display_translations",
            "missing_status_display_facts",
            "missing_status_producers",
            "unexpected_status_producers",
            "stale_producerless_status_exceptions",
            "unresolved_status_helpers",
        )
    ):
        return True
    return any(
        value
        for category in findings["description_findings"].values()
        for value in category.values()
    )


def build_inventory():
    db = source_entries(ZH_SOURCE_DIR)
    descriptions = description_payload()
    mutation = mutation_rows(
        db,
        (
            descriptions["mutation"]["english"],
            descriptions["mutation"]["chinese"],
        ),
    )
    durations = duration_rows(db)
    statuses, status_proof = status_rows(db, with_proof=True)
    abilities, excluded_abilities = ability_rows(
        db,
        (
            descriptions["ability"]["english"],
            descriptions["ability"]["chinese"],
        ),
    )
    skills = skill_rows(
        db,
        (
            descriptions["skill"]["english"],
            descriptions["skill"]["chinese"],
        ),
    )
    attributes = attribute_rows(db)
    monster_statuses = monster_status_rows((
        descriptions["monster_status"]["english"],
        descriptions["monster_status"]["chinese"],
    ))
    rows = sorted(
        mutation + durations + statuses + abilities + skills
        + attributes + monster_statuses,
        key=lambda row: row["identity"],
    )
    inputs = [
        *source_files(ZH_SOURCE_DIR),
        MUTATION_TYPE,
        MUTATION_DATA,
        DURATION_TYPE,
        DURATION_DATA,
        STATUS_TYPE,
        STATUS_CODE,
        ABILITY_TYPE,
        ABILITY_CODE,
        SKILL_TYPE,
        SKILL_CODE,
        STAT_TYPE,
        STAT_CODE,
        *(path for pair in DESCRIPTION_FILES.values() for path in pair),
        ROOT / "docs/glossary.md",
        ROOT / "docs/decisions.md",
    ]
    payload = {
        "schema": "dcss-character-mechanics-review-inventory-v1",
        "baseline": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "glossary_sha256": sha(ROOT / "docs/glossary.md"),
        "input_sha256": {
            relative(path): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in inputs
        },
        "scope": {
            "included": [
                "mutation definitions and all player-facing mutation strings",
                "duration/status producers used by fill_status_info",
                "non-religious ability definitions and descriptions",
                "current and save-compatibility skills, descriptions and titles",
                "core Strength/Intelligence/Dexterity display forms",
                "English monster-status TextDB slots and their ZH counterparts",
            ],
            "excluded": [
                "god-specific abilities and passives owned by Issue #25",
                "spell/item identity re-review",
                "balance, formulas, probabilities and costs",
                "internal durations without any change to their game behaviour",
                "Wiki-derived identity counts",
            ],
            "excluded_god_ability_identities": excluded_abilities,
        },
        "count": len(rows),
        "category_counts": {
            category: sum(row["category"] == category for row in rows)
            for category in sorted({row["category"] for row in rows})
        },
        "lifecycle_counts": {
            lifecycle: sum(row["lifecycle"] == lifecycle for row in rows)
            for lifecycle in sorted({row["lifecycle"] for row in rows})
        },
        "violations": inventory_violations(rows, descriptions, status_proof),
        "rows": rows,
    }
    encoded = json.dumps(
        rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    payload["inventory_sha256"] = hashlib.sha256(encoded).hexdigest()
    return payload


def legacy_review_conclusions(text):
    matches = re.findall(
        r"^\|\s*`((?:mutation|duration|status|ability|skill|attribute|"
        r"monster_status):[^`]+)`\s*\|.*?\|\s*([^|\n]+?)\s*\|\s*$",
        text,
        re.MULTILINE,
    )
    mapping = {
        "保留": "keep",
        "修订": "adjust",
        "重译": "retranslate",
        "暂缓术语": "defer terminology",
        "暂缓实现": "defer implementation",
    }
    return {
        identity: mapping.get(
            conclusion.strip().split("：", 1)[0].strip(),
            conclusion.strip().split("：", 1)[0].strip(),
        )
        for identity, conclusion in matches
    }


def fact_sha256(row):
    encoded = json.dumps(
        row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def parse_strict_review_evidence(path):
    text = path.read_text(encoding="utf-8")
    if text.count(STRICT_REVIEW_BEGIN) != 1 or text.count(STRICT_REVIEW_END) != 1:
        raise RuntimeError("strict review evidence block is missing or duplicated")
    block = text.split(STRICT_REVIEW_BEGIN, 1)[1].split(
        STRICT_REVIEW_END, 1
    )[0].strip().splitlines()
    if len(block) < 4 or block[1] != "```jsonl" or block[-1] != "```":
        raise RuntimeError("strict review evidence block structure is invalid")
    metadata = json.loads(block[0])
    if not isinstance(metadata, dict) or set(metadata) != {
        "baseline", "glossary_sha256", "identity_count", "inventory_sha256",
    }:
        raise RuntimeError("strict review metadata fields are invalid")
    if block[0] != json.dumps(
        metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ):
        raise RuntimeError("strict review metadata is not canonical JSON")
    cards = []
    for line in block[2:-1]:
        card = json.loads(line)
        if not isinstance(card, dict) or set(card) != STRICT_CARD_FIELDS:
            raise RuntimeError("strict review evidence-card fields are invalid")
        if line != json.dumps(
            card, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ):
            raise RuntimeError("strict review evidence card is not canonical JSON")
        cards.append(card)
    return metadata, cards


def review_coverage(payload, path):
    metadata, cards = parse_strict_review_evidence(path)
    expected_rows = sorted(payload["rows"], key=lambda row: row["identity"])
    expected_ids = [row["identity"] for row in expected_rows]
    identities = [card["identity"] for card in cards]
    expected = set(expected_ids)
    actual = set(identities)
    invalid = sorted(
        card["identity"] for card in cards
        if card["terminal_conclusion"] not in TERMINAL_CONCLUSIONS
    )
    expected_by_id = {row["identity"]: row for row in expected_rows}
    mismatched_facts = sorted(
        card["identity"] for card in cards
        if card["identity"] in expected_by_id
        and card["fact_sha256"] != fact_sha256(
            expected_by_id[card["identity"]]
        )
    )
    bindings = {
        "baseline": metadata["baseline"] == CHARACTER_REVIEW_BASE,
        "glossary_sha256": (
            metadata["glossary_sha256"] == payload["glossary_sha256"]
        ),
        "inventory_sha256": (
            metadata["inventory_sha256"] == payload["inventory_sha256"]
        ),
        "identity_count": metadata["identity_count"] == payload["count"],
    }
    duplicate = sorted(
        identity for identity, count in Counter(identities).items()
        if count > 1
    )
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    order_matches = identities == expected_ids
    return {
        "review_results": relative(path),
        "review_results_sha256": sha(path),
        "evidence_card_count": len(identities),
        "binding_matches": bindings,
        "duplicate_evidence_cards": duplicate,
        "missing_evidence_cards": missing,
        "unexpected_evidence_cards": unexpected,
        "canonical_card_order": order_matches,
        "mismatched_fact_sha256": mismatched_facts,
        "invalid_terminal_conclusions": invalid,
        "coverage_equal": (
            all(bindings.values())
            and len(identities) == len(expected_ids)
            and not duplicate
            and not missing
            and not unexpected
            and order_matches
            and not mismatched_facts
            and not invalid
        ),
    }


def strict_review_block(payload, conclusions):
    metadata = {
        "baseline": CHARACTER_REVIEW_BASE,
        "glossary_sha256": payload["glossary_sha256"],
        "identity_count": payload["count"],
        "inventory_sha256": payload["inventory_sha256"],
    }
    lines = [
        STRICT_REVIEW_BEGIN,
        json.dumps(
            metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ),
        "```jsonl",
    ]
    for row in sorted(payload["rows"], key=lambda item: item["identity"]):
        card = {
            "fact_sha256": fact_sha256(row),
            "identity": row["identity"],
            "terminal_conclusion": conclusions.get(row["identity"], "pending"),
        }
        lines.append(json.dumps(
            card, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ))
    lines.extend(["```", STRICT_REVIEW_END])
    return "\n".join(lines)


def write_strict_review_evidence(payload, path):
    text = path.read_text(encoding="utf-8")
    conclusions = legacy_review_conclusions(text)
    block = strict_review_block(payload, conclusions)
    if STRICT_REVIEW_BEGIN in text:
        prefix, remainder = text.split(STRICT_REVIEW_BEGIN, 1)
        if STRICT_REVIEW_END not in remainder:
            raise RuntimeError("unterminated existing strict review evidence")
        suffix = remainder.split(STRICT_REVIEW_END, 1)[1]
        text = prefix.rstrip() + "\n\n" + block + suffix
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    path.write_text(text, encoding="utf-8")


def table_text(value, limit=72):
    text = re.sub(r"\s+", " ", str(value or "—")).strip()
    text = text.replace("|", "／")
    return text if len(text) <= limit else text[:limit - 1] + "…"


def translated_display(row):
    values = [
        item["chinese"]
        for item in row.get("display_strings", [])
        if item.get("chinese")
    ]
    return "；".join(dict.fromkeys(table_text(value, 40) for value in values))


def generated_evidence_section(payload, category, heading):
    rows = [row for row in payload["rows"] if row["category"] == category]
    lines = [
        f"## {heading}（{len(rows)}）",
        "",
        "| 身份 | 生命周期 | 名称与显示形式 | 生产事实 | 终态结论 |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        identity = row["identity"]
        bare_identity = identity.split(":", 1)[1]
        english = table_text(row.get("english_source_name"), 42)
        chinese = table_text(row.get("current_chinese_name"), 42)
        display = translated_display(row)
        if display and display != chinese:
            name = f"{english} → {chinese}；显示：{display}"
        else:
            name = f"{english} → {chinese}"

        if category == "mutation":
            fact = (
                f"{row['levels']} 级；weight {row['weight']}；"
                f"flags {table_text(row['flags'], 28)}；"
                f"说明：{table_text(row.get('chinese_description'))}"
            )
            conclusion = (
                "修订：校准名称、术语或机制说明"
                if bare_identity in REVISED_MUTATION_IDENTITIES
                else (
                    "保留：内部哨兵身份"
                    if row["lifecycle"] == "internal"
                    else "保留：名称、等级显示与机制说明准确"
                )
            )
        elif category == "duration":
            slots = sum(
                bool(row.get(field)) for field in ("light", "short", "long")
            )
            fact = (
                f"`duration_data` 显示槽 {slots}/3；"
                f"flags {table_text(row['flags'], 30)}；"
                f"内部名 {table_text(row.get('internal_name'), 30)}"
            )
            conclusion = (
                "修订：补齐显示翻译或统一相关说明术语"
                if bare_identity in REVISED_DURATION_IDENTITIES
                else (
                    "保留：无玩家显示槽的内部计时身份"
                    if row["lifecycle"] == "internal"
                    else "保留：显示槽、颜色标记与说明准确"
                )
            )
        elif category == "status":
            keys = "、".join(row.get("db_keys", [])) or "动态/无 TextDB 键"
            fact = (
                f"`fill_status_info` producer="
                f"{str(row['producer_present']).lower()}；"
                f"db_key {table_text(keys, 42)}；"
                f"显示字面量 {len(row.get('display_strings', []))}"
            )
            conclusion = (
                "修订：长文本纳入 status 上下文翻译"
                if bare_identity in REVISED_STATUS_IDENTITIES
                else (
                    "保留：枚举保留、无独立 producer"
                    if row["lifecycle"] == "internal"
                    else "保留：生产条件、显示文本与 TextDB 键准确"
                )
            )
        else:
            fact = (
                "英文/中文 TextDB 一一配对；说明："
                f"{table_text(row.get('chinese_description'))}"
            )
            conclusion = (
                "修订：神名统一为“辛”"
                if bare_identity in REVISED_MONSTER_STATUS_KEYS
                else "保留：状态语义、效果说明与术语准确"
            )
            name = f"{english}；中文说明已配对"

        lines.append(
            f"| `{identity}` | {row['lifecycle']} | {name} | "
            f"{fact} | {conclusion} |"
        )
    lines.append("")
    return "\n".join(lines)


def complete_review_results(payload, path):
    text = path.read_text(encoding="utf-8")
    marker = "\n## 变异证据卡（"
    if marker in text:
        text = text.split(marker, 1)[0].rstrip() + "\n"
    sections = [
        generated_evidence_section(payload, "mutation", "变异证据卡"),
        generated_evidence_section(payload, "duration", "时长状态证据卡"),
        generated_evidence_section(payload, "status", "附加状态证据卡"),
        generated_evidence_section(
            payload, "monster_status", "怪物状态证据卡"
        ),
    ]
    path.write_text(text.rstrip() + "\n\n" + "\n".join(sections), encoding="utf-8")
    write_strict_review_evidence(payload, path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--review-results", type=Path)
    parser.add_argument("--complete-review-results", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = build_inventory()
        if args.complete_review_results:
            complete_review_results(payload, args.complete_review_results)
        if args.review_results:
            payload["review_coverage"] = review_coverage(
                payload, args.review_results
            )
    except (
        AttributeError,
        IndexError,
        KeyError,
        OSError,
        RuntimeError,
        subprocess.SubprocessError,
        ValueError,
    ) as error:
        print(
            f"ERROR: character-mechanics inventory could not be built: {error}",
            file=sys.stderr,
        )
        return 2
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    summary = {
        key: payload[key]
        for key in (
            "baseline",
            "glossary_sha256",
            "inventory_sha256",
            "count",
            "category_counts",
            "lifecycle_counts",
            "violations",
        )
    }
    if "review_coverage" in payload:
        summary["review_coverage"] = payload["review_coverage"]
    print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
    coverage_failed = (
        "review_coverage" in payload
        and not payload["review_coverage"]["coverage_equal"]
    )
    return 1 if has_violations(payload) or coverage_failed else 0


if __name__ == "__main__":
    sys.exit(main())
