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
from i18n_shared import (  # noqa: E402
    AuditRootError,
    load_review_input,
    resolve_audit_root,
    review_input_metadata,
)

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
}
CHARACTER_REVIEW_BASE = "76c815b2ac79d11a8066597ad04d127a1636e153"
STRICT_REVIEW_BEGIN = "<!-- BEGIN STRICT REVIEW EVIDENCE v2 -->"
STRICT_REVIEW_END = "<!-- END STRICT REVIEW EVIDENCE v2 -->"
REVIEW_ARTIFACT_BEGIN = "<!-- BEGIN CHARACTER REVIEW ARTIFACT v2 -->"
REVIEW_ARTIFACT_END = "<!-- END CHARACTER REVIEW ARTIFACT v2 -->"
STRICT_CARD_FIELDS = {
    "current_chinese",
    "current_english",
    "fact_sha256",
    "identity",
    "lifecycle",
    "production_facts",
    "reviewer_rationale",
    "terminal_conclusion",
}
REVIEW_DECISION_FIELDS = {
    "reviewer_rationale", "terminal_conclusion",
}
REVIEW_CATEGORY_HEADINGS = (
    ("attribute", "属性证据卡"),
    ("skill", "技能证据卡"),
    ("ability", "非神祇能力证据卡"),
    ("mutation", "变异证据卡"),
    ("duration", "时长状态证据卡"),
    ("status", "附加状态证据卡"),
    ("monster_status", "怪物状态证据卡"),
)

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
            fragment = body[match.start():end].strip()
            if (
                "Intentional fallthrough" in fragment
                and index + 1 < len(matches)
                and matches[index + 1].group(1).startswith("DUR_")
            ):
                fallthrough_end = (
                    matches[index + 2].start()
                    if index + 2 < len(matches) else len(body)
                )
                fallthrough = body[
                    matches[index + 1].start():fallthrough_end
                ].strip()
                if not re.search(r"\bbreak\s*;", fallthrough):
                    raise RuntimeError(
                        "intentional status fallthrough has no bounded break: "
                        f"{match.group(1)}"
                    )
                fragment += "\n" + fallthrough
            result[match.group(1)] = fragment
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


def duration_status_fragments():
    """Return literal status facts loaded by _fill_inf_from_ddef."""
    result = {}
    rows = ordered_initializer_rows(
        active_source(DURATION_DATA),
        r"\bstatic\s+const\s+duration_def\s+duration_data\s*\[\]",
    )
    for raw in rows:
        fields = initializer_fields(raw)
        match = re.search(r"\b(DUR_[A-Z0-9_]+)\b", fields[0])
        if not match or len(fields) < 6:
            raise RuntimeError(
                f"unparsed duration facts for status producer: {raw[:100]}"
            )
        strings = [cpp_strings(field) for field in fields[2:6]]
        if any(len(values) != 1 for values in strings):
            raise RuntimeError(
                f"unparsed duration display facts: {match.group(1)}"
            )
        light, short, _name, long_text = [values[0] for values in strings]
        assignments = []
        if light:
            assignments.extend((
                f'inf.db_key = "{light}";',
                f'inf.light_text = C_("status", "{light}");',
            ))
        if short:
            assignments.extend((
                f'inf.short_db_key = "{short}";',
                f'inf.short_text = C_("status", "{short}");',
            ))
        if long_text:
            assignments.append(f'inf.long_text = T_("{long_text}");')
        result[match.group(1)] = "\n".join(assignments)
    return result


def normalize_producer_fragment(fragment):
    return re.sub(r"\s+", " ", _strip_cpp_comments(fragment)).strip()


def status_producer_proof(
    declared, fragments, source, duration_fragments=None
):
    """Prove enum/producer conservation and resolve bounded helper calls."""
    declared_set = set(declared)
    producer_set = set(fragments)
    duration_fragments = duration_fragments or {}
    resolved = {}
    unresolved = []
    for identity in sorted(producer_set & declared_set):
        fragment = fragments[identity]
        describe_calls = re.findall(
            r"\b(_describe_[a-z0-9_]+)\s*\(\s*inf\s*\)\s*;",
            fragment,
        )
        describe_mentions = set(re.findall(
            r"\b(_describe_[a-z0-9_]+)\b", fragment
        ))
        fill_calls = re.findall(
            r"\b_fill_inf_from_ddef\s*\(\s*(DUR_[A-Z0-9_]+)\s*,"
            r"\s*inf\s*\)\s*;",
            fragment,
        )
        fill_mentions = re.findall(r"\b_fill_inf_from_ddef\b", fragment)
        inf_call_names = set(re.findall(
            r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\([^()]*\binf\b[^()]*\)"
            r"\s*;",
            fragment,
        ))
        known_calls = set(describe_calls)
        if fill_calls:
            known_calls.add("_fill_inf_from_ddef")
        if (
            describe_mentions != set(describe_calls)
            or len(describe_calls) > 1
            or len(fill_mentions) != len(fill_calls)
            or len(fill_calls) > 1
            or inf_call_names != known_calls
        ):
            unresolved.append(identity)
            resolved[identity] = fragment
            continue
        resolved_fragment = fragment
        if describe_calls:
            try:
                helper = exact_function_body(
                    _strip_cpp_comments(source),
                    rf"\b(?:static\s+)?void\s+{re.escape(describe_calls[0])}",
                )
            except RuntimeError:
                unresolved.append(identity)
                resolved[identity] = fragment
                continue
            if re.search(r"\b_describe_[a-z0-9_]+\s*\(", helper):
                unresolved.append(identity)
                resolved[identity] = fragment
                continue
            resolved_fragment += "\n" + helper
        if fill_calls:
            duration_fragment = duration_fragments.get(fill_calls[0])
            if not duration_fragment:
                unresolved.append(identity)
                resolved[identity] = fragment
                continue
            try:
                helper = exact_function_body(
                    _strip_cpp_comments(source),
                    r"\bstatic\s+bool\s+_fill_inf_from_ddef",
                )
            except RuntimeError:
                unresolved.append(identity)
                resolved[identity] = fragment
                continue
            resolved_fragment += "\n" + helper + "\n" + duration_fragment
        resolved[identity] = resolved_fragment
        if (
            not status_db_keys(resolved_fragment)
            and not status_display_literals(resolved_fragment)
        ):
            unresolved.append(identity)
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
    proof = status_producer_proof(
        declared, fragments, source, duration_status_fragments()
    )
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
            "producer_fragment": (
                normalize_producer_fragment(fragment)
                if producer_present else None
            ),
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


def _split_legacy_decision(value):
    state, separator, rationale = value.strip().partition("：")
    if not separator:
        state, separator, rationale = value.strip().partition(":")
    mapping = {
        "保留": "keep",
        "修订": "adjust",
        "重译": "retranslate",
        "暂缓术语": "defer terminology",
        "暂缓实现": "defer implementation",
    }
    return {
        "terminal_conclusion": mapping.get(state.strip(), state.strip()),
        "reviewer_rationale": rationale.strip() if separator else "",
    }


def legacy_review_decisions(text):
    matches = re.findall(
        r"^\|\s*`((?:mutation|duration|status|ability|skill|attribute|"
        r"monster_status):[^`]+)`\s*\|.*?\|\s*([^|\n]+?)\s*\|\s*$",
        text,
        re.MULTILINE,
    )
    duplicates = sorted(
        identity for identity, count in Counter(
            identity for identity, _value in matches
        ).items()
        if count > 1
    )
    if duplicates:
        raise RuntimeError(
            "duplicate legacy reviewer decisions: " + ", ".join(duplicates)
        )
    return {
        identity: _split_legacy_decision(value)
        for identity, value in matches
    }


def legacy_review_conclusions(text):
    """Compatibility view for callers that only need the terminal state."""
    return {
        identity: decision["terminal_conclusion"]
        for identity, decision in legacy_review_decisions(text).items()
    }


def fact_sha256(row):
    encoded = json.dumps(
        row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _canonical_json_key(key):
    if isinstance(key, str):
        return key
    if key is None:
        return "null"
    if key is True:
        return "true"
    if key is False:
        return "false"
    if isinstance(key, (int, float)):
        return str(key)
    raise RuntimeError(f"unsupported JSON object key: {key!r}")


def canonical_json_value(value, path="$"):
    """Normalize object keys exactly once and reject lossy JSON collisions."""
    if isinstance(value, dict):
        normalized = {}
        for key, child_value in value.items():
            key_text = _canonical_json_key(key)
            if key_text in normalized:
                raise RuntimeError(
                    f"colliding JSON object keys at {path}: {key_text!r}"
                )
            normalized[key_text] = canonical_json_value(
                child_value, f"{path}.{key_text}"
            )
        return normalized
    if isinstance(value, list):
        return [
            canonical_json_value(item, f"{path}[{index}]")
            for index, item in enumerate(value)
        ]
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise RuntimeError(f"unsupported JSON value at {path}: {value!r}")


def language_snapshot(row, language):
    """Return every language-labelled field without truncating nested values."""
    snapshot = {}

    def collect(value, path):
        if isinstance(value, dict):
            for key in sorted(value, key=_canonical_json_key):
                key_text = _canonical_json_key(key)
                child = f"{path}.{key_text}" if path else key_text
                if language in key_text.lower():
                    snapshot[child] = canonical_json_value(
                        value[key], f"$.{child}"
                    )
                if isinstance(value[key], (dict, list)):
                    collect(value[key], child)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, (dict, list)):
                    collect(item, f"{path}[{index}]")

    collect(row, "")
    return snapshot


def _validated_decisions(payload, decisions):
    expected = {row["identity"] for row in payload["rows"]}
    actual = set(decisions)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        details = []
        if missing:
            details.append("missing explicit reviewer decisions: " + ", ".join(missing))
        if unexpected:
            details.append(
                "unexpected reviewer decisions: " + ", ".join(unexpected)
            )
        raise RuntimeError("; ".join(details))
    validated = {}
    for identity in sorted(expected):
        decision = decisions[identity]
        if not isinstance(decision, dict) or set(decision) != REVIEW_DECISION_FIELDS:
            raise RuntimeError(
                f"reviewer decision fields are invalid for {identity}"
            )
        conclusion = decision["terminal_conclusion"]
        rationale = decision["reviewer_rationale"]
        if conclusion not in TERMINAL_CONCLUSIONS:
            raise RuntimeError(
                f"non-terminal reviewer conclusion for {identity}: {conclusion!r}"
            )
        if not isinstance(rationale, str) or not rationale.strip():
            raise RuntimeError(f"empty reviewer rationale for {identity}")
        validated[identity] = {
            "terminal_conclusion": conclusion,
            "reviewer_rationale": rationale.strip(),
        }
    return validated


def review_cards(payload, decisions):
    decisions = _validated_decisions(payload, decisions)
    cards = []
    for row in sorted(payload["rows"], key=lambda item: item["identity"]):
        decision = decisions[row["identity"]]
        cards.append({
            "current_chinese": language_snapshot(row, "chinese"),
            "current_english": language_snapshot(row, "english"),
            "fact_sha256": fact_sha256(row),
            "identity": row["identity"],
            "lifecycle": row.get("lifecycle"),
            "production_facts": canonical_json_value(row),
            **decision,
        })
    return cards


def parse_strict_review_evidence(review_input):
    return _parse_strict_review_text(review_input.text)


def _parse_strict_review_text(text):
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


def review_coverage(payload, review_input):
    metadata, cards = parse_strict_review_evidence(review_input)
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
        and (
            card["fact_sha256"] != fact_sha256(
                expected_by_id[card["identity"]]
            )
            or card["production_facts"]
            != canonical_json_value(expected_by_id[card["identity"]])
            or card["lifecycle"]
            != expected_by_id[card["identity"]].get("lifecycle")
            or card["current_english"]
            != language_snapshot(expected_by_id[card["identity"]], "english")
            or card["current_chinese"]
            != language_snapshot(expected_by_id[card["identity"]], "chinese")
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
    empty_rationales = sorted(
        card["identity"] for card in cards
        if not isinstance(card["reviewer_rationale"], str)
        or not card["reviewer_rationale"].strip()
    )
    decisions = {
        card["identity"]: {
            "terminal_conclusion": card["terminal_conclusion"],
            "reviewer_rationale": card["reviewer_rationale"],
        }
        for card in cards
    }
    try:
        expected_artifact = render_review_results(payload, decisions)
    except RuntimeError:
        expected_artifact = None
    artifact_exact = review_input.text == expected_artifact
    return {
        **review_input_metadata(review_input),
        "review_results": review_input.logical_path,
        "review_results_sha256": review_input.sha256,
        "evidence_card_count": len(identities),
        "binding_matches": bindings,
        "duplicate_evidence_cards": duplicate,
        "missing_evidence_cards": missing,
        "unexpected_evidence_cards": unexpected,
        "canonical_card_order": order_matches,
        "mismatched_fact_sha256": mismatched_facts,
        "invalid_terminal_conclusions": invalid,
        "empty_reviewer_rationales": empty_rationales,
        "artifact_exact": artifact_exact,
        "coverage_equal": (
            all(bindings.values())
            and len(identities) == len(expected_ids)
            and not duplicate
            and not missing
            and not unexpected
            and order_matches
            and not mismatched_facts
            and not invalid
            and not empty_rationales
            and artifact_exact
        ),
    }


def strict_review_block(payload, cards):
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
    for card in cards:
        lines.append(json.dumps(
            card, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ))
    lines.extend(["```", STRICT_REVIEW_END])
    return "\n".join(lines)


def review_artifact_summary(payload):
    return {
        "category_counts": payload.get("category_counts", {}),
        "glossary_sha256": payload["glossary_sha256"],
        "identity_count": payload["count"],
        "lifecycle_counts": payload.get("lifecycle_counts", {}),
        "violations": payload.get("violations", {}),
        "violations_zero": (
            not has_violations(payload) if "violations" in payload else True
        ),
    }


def render_review_results(payload, decisions):
    cards = review_cards(payload, decisions)
    summary = json.dumps(
        review_artifact_summary(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    visible_sections = "\n".join(
        generated_evidence_section(cards, category, heading)
        for category, heading in REVIEW_CATEGORY_HEADINGS
    )
    return (
        "# Character mechanics translation review\n\n"
        f"{REVIEW_ARTIFACT_BEGIN}\n"
        f"{summary}\n"
        f"{REVIEW_ARTIFACT_END}\n\n"
        "## Human-visible complete evidence\n\n"
        "Every visible row below is rendered from the same complete card as "
        "the strict JSONL evidence. Values are losslessly JSON-encoded; "
        "Markdown delimiter pipes use HTML entities, and values are never "
        "truncated.\n\n"
        f"{visible_sections}\n"
        f"{strict_review_block(payload, cards)}\n"
    )


def _strict_review_decisions(cards):
    identities = [card["identity"] for card in cards]
    duplicates = sorted(
        identity for identity, count in Counter(identities).items()
        if count > 1
    )
    if duplicates:
        raise RuntimeError(
            "duplicate strict review evidence-card identities: "
            + ", ".join(duplicates)
        )
    return {
        card["identity"]: {
            field: card[field] for field in REVIEW_DECISION_FIELDS
        }
        for card in cards
    }


def write_strict_review_evidence(payload, path):
    text = path.read_text(encoding="utf-8")
    if STRICT_REVIEW_BEGIN in text or STRICT_REVIEW_END in text:
        _metadata, cards = _parse_strict_review_text(text)
        decisions = _strict_review_decisions(cards)
    else:
        decisions = legacy_review_decisions(text)
    rendered = render_review_results(payload, decisions)
    path.write_text(rendered, encoding="utf-8")


def table_json(value):
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).replace("|", "&#124;")


def generated_evidence_section(cards, category, heading):
    rows = [
        card for card in cards
        if card["production_facts"]["category"] == category
    ]
    lines = [
        f"## {heading}（{len(rows)}）",
        "",
        "| 身份 | 生命周期 | 完整当前英文 | 完整当前中文 | 完整生产事实 | "
        "终态结论 | Reviewer rationale |",
        "|---|---|---|---|---|---|---|",
    ]
    for card in rows:
        lines.append(
            f"| `{card['identity']}` | {table_json(card['lifecycle'])} | "
            f"{table_json(card['current_english'])} | "
            f"{table_json(card['current_chinese'])} | "
            f"{table_json(card['production_facts'])} | "
            f"`{card['terminal_conclusion']}` | "
            f"{table_json(card['reviewer_rationale'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def complete_review_results(payload, path):
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
            review_input = load_review_input(ROOT, args.review_results)
            payload["review_input"] = review_input_metadata(review_input)
            payload["review_coverage"] = review_coverage(
                payload, review_input
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
