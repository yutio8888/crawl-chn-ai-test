#!/usr/bin/env python3
"""
zh_runtime_check.py — JSONL v1 issue protocol parser & baseline manager.

Issue 66, Task A: JSONL issue protocol, parser & mutation fixtures.

Usage:
  # Generate a new baseline (first run)
  python3 .claude/scripts/zh_runtime_check.py \\
      --catch2-stderr /tmp/catch2-zh.log \\
      --catch2-stdout /tmp/catch2-zh.stdout \\
      --output-baseline baseline.json

  # Compare against existing baseline (monitoring / CI)
  python3 .claude/scripts/zh_runtime_check.py \\
      --catch2-stderr /tmp/catch2-zh.log \\
      --catch2-stdout /tmp/catch2-zh.stdout \\
      --baseline baseline.json

  # Help system catch2 aggregation
  python3 .claude/scripts/zh_runtime_check.py --mode help \\
      --catch2-stderr /tmp/catch2-zh-help.log \\
      --catch2-stdout /tmp/catch2-zh-help.stdout \\
      --baseline baseline.json

  # Migrate baseline protocol metadata (add catch2_protocol field)
  python3 .claude/scripts/zh_runtime_check.py \\
      --migrate-baseline-protocol baseline.json --suite zh_translation|zh_help

  # Verify baseline protocol metadata
  python3 .claude/scripts/zh_runtime_check.py \\
      --check-baseline-protocol baseline.json

Exit codes:
  0 = valid, no regression, or successful (temp) baseline write
  1 = valid protocol with regression or coverage failure
  2 = CLI / input / baseline usage errors
  3 = JSONL schema / identity / ordering / conservation errors
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple

# ============================================================================
# Constants
# ============================================================================

SCHEMA_VERSION = 1

ZH_TRANSLATION_ENUMERATORS = [
    "gods", "god_abilities", "spells", "monsters", "features", "clouds",
    "mutations", "fixed_artefacts", "skill_name", "species_backgrounds",
    "durations", "godspeak", "tutorial_hints_commands", "weapon_brands",
    "armour_egos", "item_base_names",
]

ZH_HELP_ENUMERATORS = ["passive_status_textdb"]

VALID_SUITES = {"zh_translation", "zh_help"}
VALID_KINDS = {
    "UNTRANSLATED", "MIXED_CN_EN", "FORMAT_BROKEN", "GARBLED_UTF8",
    "EMPTY_DB", "WHITESPACE_ANOMALY", "INVISIBLE_CHAR", "PUNCT_STYLE",
    "EMBEDDED_LUA_ERROR",
}

# Exact RC-bot coverage contract. Counts alone are insufficient: every case
# must appear exactly once, in shard order, with its defining semantic tokens.
BOT_CASE_MANIFESTS = {
    "all": [
        "probe:ui", "item:chaos_demon_whip", "item:running_boots",
        "god:Trog", "phase:ui:done", "probe:spells", "phase:spells:done",
        "probe:issue68", "protocol:cloud:noxious", "protocol:cloud:freezing",
        "protocol:cloud:foul", "protocol:trap:permanent",
        "phase:issue68:done", "probe:issue48",
        "path1:unid_appearance_msg", "path3:enchantress_msg",
        "phase:issue48:done",
    ],
    "issue68-l2": [
        "setup", "lua_identity", "display_assets", "arrival_vault",
        "trove_quantity",
        "trove_plus", "trove_rune", "trove_horn", "trove_ego",
        "trove_jewellery", "trove_demon_weapon",
        "trove_demon_alternative", "portal_late_translation",
        "portal_distance_late_translation", "portal_close_grammar",
        "sewer_late_translation", "portal_milestone_boundary",
        "item_trigger_identity",
        "status_boundary", "monster_boundary", "zot_boundary", "level_up",
        "godspeak_trog", "godspeak_xom", "end",
    ],
}

BOT_REQUIRED_CONTENT = {
    "probe:ui": ("lang=zh", "你攻击"),
    "item:chaos_demon_whip": ("恶魔之鞭",),
    "item:running_boots": ("蜘蛛之靴",),
    "god:Trog": ("特洛格欢迎你",),
    "probe:issue68": ("lang=zh",),
    "protocol:cloud:noxious": ("noxious fumes",),
    "protocol:cloud:freezing": ("freezing vapour",),
    "protocol:cloud:foul": ("foul pestilence",),
    "protocol:trap:permanent": ("permanent teleport", "hook=permanent teleport"),
    "setup": ("language=zh", "你攻击"),
    "lua_identity": ("Minotaur", "Fighter", "minotaur"),
    "display_assets": ("牛头人", "战士", "特洛格", "蜘蛛网"),
    "arrival_vault": ("heliophobic_arrival_battle_scene placed",),
    "trove_quantity": ("scroll", "acquirement", "2 获取卷轴"),
    "trove_plus": ("armour", "golden dragon scales", "+4 金龙鳞甲"),
    "trove_rune": ("rune of Zot", "slimy rune of Zot", "黏液 佐特符文"),
    "trove_horn": ("horn of Geryon", "格律翁之角"),
    "trove_ego": ("weapon", "war axe", "flaming", "+2 烈焰之战斧"),
    "trove_jewellery": ("jewellery", "ring of protection", "+3 防护戒指"),
    "trove_demon_weapon": ("demon whip", "恶魔武器"),
    "trove_demon_alternative": ("demon blade",),
    "item_trigger_identity": ("scroll of blinking", "legacy_zh="),
    "portal_late_translation": ("You hear coins being counted.",
                                "你听到了数钱的声音。"),
    "portal_distance_late_translation": ("You hear the brisk tolling",
                                         "distant bell"),
    "portal_close_grammar": ("an alarm",),
    "sewer_late_translation": ("sewer drain",),
    "portal_milestone_boundary": (
        "The Name-Rending Infernalists' Reservoir",
        "The Chambers of the Cloud Mage",
        "fallback:",
        "Issue 28 missing portal title",
    ),
    "status_boundary": ("immotile=true", "mighty=true"),
    "monster_boundary": ("orc priest",),
    "zot_boundary": ("orb of fire", "orb of winter", "orb of entropy",
                     "佐特领域"),
    "level_up": ("你已达到20级",),
    "godspeak_trog": ("Trog bestows a gift",),
    "godspeak_xom": ("Xom thinks this is hilarious",),
    "end": ("ok",),
    "probe:spells": ("lang=zh", "你攻击"),
    "probe:issue48": ("lang=zh",),
    "path1:unid_appearance_msg": ("歌唱之剑",),
    "path3:enchantress_msg": ("妖术女王",),
}

HELP_BOT_EXPECTED_IDS = [
    "help:probe:ok",
    "help:guide:quickstart:ok", "help:guide:manual:ok",
    "help:guide:macros:ok", "help:guide:options:ok",
    "help:god:ok", "help:branch:ok", "help:cloud:ok", "help:card:ok",
    "help:skill:ok", "help:passive:ok", "help:status:ok",
    "help:status:bat:ok", "help:monster:ok", "help:spell:ok",
    "help:ability:ok", "help:feature:ok", "help:item:ok",
    "help:mutation:ok", "help:bane:ok", "help:spell_school:ok",
    "help:text:spell:ok", "help:text:ability:ok",
    "help:text:mutation:ok", "help:text:feature:ok",
    "help:text:bane:ok", "help:text:monster:ok", "help:text:item:ok",
    "help:phase:done",
]

# Canonical JSON encoding: UTF-8, sort_keys=True, separators=(",",":"), ensure_ascii=False
_CANONICAL_JSON_KWARGS = {
    "sort_keys": True,
    "separators": (",", ":"),
    "ensure_ascii": False,
}


# ============================================================================
# Protocol Helpers
# ============================================================================

def _canonical_json(obj: dict) -> str:
    """Canonical JSON encoding: sort_keys, compact separators, no ASCII escaping."""
    return json.dumps(obj, **_CANONICAL_JSON_KWARGS)


def _protocol_error(msg: str) -> None:
    """Print a protocol-level error and exit 3."""
    print(f"PROTOCOL ERROR: {msg}", file=sys.stderr)
    sys.exit(3)


def _usage_error(msg: str) -> None:
    """Print a usage-level error and exit 2."""
    print(f"USAGE ERROR: {msg}", file=sys.stderr)
    sys.exit(2)


def _manifest_sha256(suite: str, enumerators: List[str]) -> str:
    """Compute manifest_sha256: canonical JSON of object minus manifest_sha256 field."""
    obj = {
        "schema": "dcss-zh-catch2-jsonl",
        "schema_version": SCHEMA_VERSION,
        "suite": suite,
        "enumerators": enumerators,
    }
    h = hashlib.sha256(_canonical_json(obj).encode("utf-8"))
    return h.hexdigest()


def _make_catch2_protocol(suite: str, enumerators: List[str]) -> dict:
    """Build catch2_protocol metadata block."""
    manifest_sha256 = _manifest_sha256(suite, enumerators)
    return {
        "schema": "dcss-zh-catch2-jsonl",
        "schema_version": SCHEMA_VERSION,
        "suite": suite,
        "enumerators": list(enumerators),
        "manifest_sha256": manifest_sha256,
    }


# ============================================================================
# JSONL Parser
# ============================================================================

# Pattern for the JSONL prefix
JSONL_PREFIX_RE = re.compile(r"^ZH_ISSUE_JSON:\s*")


class JsonlIssue:
    """Parsed and validated issue record from JSONL protocol."""
    def __init__(self, raw: dict):
        self.schema_version = raw["schema_version"]
        self.suite: str = raw["suite"]
        self.enumerator: str = raw["enumerator"]
        self.sequence: int = raw["sequence"]
        self.kind: str = raw["kind"]
        self.source: str = raw["source"]
        self.key: str = raw["key"]
        self.sample: str = raw["sample"]
        self.sample_bytes_hex: str = raw["sample_bytes_hex"]

    @property
    def transport_id(self) -> tuple:
        """Transport identity: (suite, enumerator, sequence)."""
        return (self.suite, self.enumerator, self.sequence)

    @property
    def semantic_id(self) -> tuple:
        """Semantic identity: (suite, enumerator, kind, source, key, sample_bytes_hex)."""
        return (self.suite, self.enumerator, self.kind,
                self.source, self.key, self.sample_bytes_hex)


class JsonlSummary:
    """Parsed and validated summary record from JSONL protocol."""
    def __init__(self, raw: dict):
        self.schema_version = raw["schema_version"]
        self.suite: str = raw["suite"]
        self.enumerator: str = raw["enumerator"]
        self.issue_count: int = raw["issue_count"]


def _validate_jsonl_line(line_data: dict) -> None:
    """Validate a single JSONL record against the protocol schema.

    Raises SystemExit(3) on any violation.
    """
    # --- Common required fields ---
    sv = line_data.get("schema_version")
    if sv != 1:
        _protocol_error(f"schema_version must be 1, got {sv!r}")
    if not isinstance(sv, int) or isinstance(sv, bool):
        _protocol_error(f"schema_version must be integer, got {type(sv).__name__}")

    rt = line_data.get("record_type")
    if rt not in ("issue", "summary"):
        _protocol_error(f"unknown record_type: {rt!r}")

    suite = line_data.get("suite")
    if suite not in VALID_SUITES:
        _protocol_error(f"unknown suite: {suite!r}")

    enumerator = line_data.get("enumerator")

    # --- Record-type specific ---
    if rt == "issue":
        if enumerator not in ZH_TRANSLATION_ENUMERATORS + ZH_HELP_ENUMERATORS:
            _protocol_error(f"unknown enumerator for issue record: {enumerator!r}")

        seq = line_data.get("sequence")
        if not isinstance(seq, int) or isinstance(seq, bool):
            _protocol_error(f"sequence must be integer, got {type(seq).__name__} {seq!r}")
        if seq < 0:
            _protocol_error(f"negative sequence: {seq}")

        kind = line_data.get("kind")
        if kind not in VALID_KINDS:
            _protocol_error(f"unknown kind: {kind!r}")

        for field in ("source", "key", "sample", "sample_bytes_hex"):
            if field not in line_data:
                _protocol_error(f"missing field '{field}' in issue record")
            if not isinstance(line_data[field], str):
                _protocol_error(f"field '{field}' must be string, got {type(line_data[field]).__name__}")

        hex_val = line_data["sample_bytes_hex"]
        if len(hex_val) % 2 != 0:
            _protocol_error(f"sample_bytes_hex has odd length: {len(hex_val)}")
        if len(hex_val) > 240:
            _protocol_error(f"sample_bytes_hex too long: {len(hex_val)} (max 240)")
        if not re.fullmatch(r"[0-9a-f]*", hex_val):
            _protocol_error(f"sample_bytes_hex contains non-lowercase-hex chars")

        # Verify hex decodes to match sample (errors=replace)
        try:
            decoded = bytes.fromhex(hex_val).decode("utf-8", errors="replace")
        except ValueError:
            _protocol_error(f"sample_bytes_hex is not valid hex")

        if len(hex_val) > 0:
            sample = line_data.get("sample", "")
            # Compare first min(len(sample), len(decoded)) characters
            max_compare = min(len(sample), len(decoded))
            # The decoded text should match sample for the raw-byte prefixes
            # Allow truncation (hex could be decoding up to 120 raw bytes,
            # sample is already truncated)
            if max_compare > 0 and decoded[:max_compare] != sample[:max_compare]:
                _protocol_error(
                    f"sample_bytes_hex decoded to {decoded[:60]!r} "
                    f"but sample is {sample[:60]!r}"
                )

        # No extra fields
        allowed_issue = {"schema_version", "record_type", "suite", "enumerator",
                         "sequence", "kind", "source", "key", "sample", "sample_bytes_hex"}
        extra = set(line_data.keys()) - allowed_issue
        if extra:
            _protocol_error(f"extra fields in issue record: {extra}")

    elif rt == "summary":
        if enumerator not in ZH_TRANSLATION_ENUMERATORS + ZH_HELP_ENUMERATORS:
            _protocol_error(f"unknown enumerator for summary record: {enumerator!r}")

        ic = line_data.get("issue_count")
        if not isinstance(ic, int) or isinstance(ic, bool):
            _protocol_error(f"issue_count must be integer, got {type(ic).__name__} {ic!r}")
        if ic < 0:
            _protocol_error(f"negative issue_count: {ic}")

        allowed_summary = {"schema_version", "record_type", "suite",
                           "enumerator", "issue_count"}
        extra = set(line_data.keys()) - allowed_summary
        if extra:
            _protocol_error(f"extra fields in summary record: {extra}")


def _validate_conservation(issues: List[JsonlIssue],
                           summaries: List[JsonlSummary],
                           suite: str,
                           expected_enumerators: List[str]) -> None:
    """Validate transport identity, ordering, and conservation rules.

    Raises SystemExit(3) on any violation.
    """
    # Group issues by enumerator
    by_enum: Dict[str, List[JsonlIssue]] = defaultdict(list)
    for iss in issues:
        if iss.suite != suite:
            _protocol_error(f"suite mismatch in issue: {iss.suite} != {suite}")
        by_enum[iss.enumerator].append(iss)

    # Group summaries by enumerator
    summary_map: Dict[str, JsonlSummary] = {}
    for s in summaries:
        if s.suite != suite:
            _protocol_error(f"suite mismatch in summary: {s.suite} != {suite}")
        if s.enumerator in summary_map:
            _protocol_error(f"duplicate summary for enumerator: {s.enumerator}")
        summary_map[s.enumerator] = s

    # Check each expected enumerator
    for enum_name in expected_enumerators:
        enum_issues = by_enum.get(enum_name, [])
        enum_summary = summary_map.get(enum_name)

        if enum_summary is None:
            _protocol_error(f"missing summary for enumerator: {enum_name}")

        # Sequence: contiguous 0..N-1, unique, in order
        seen_seq = set()
        for iss in enum_issues:
            if iss.sequence in seen_seq:
                _protocol_error(f"duplicate sequence {iss.sequence} for {enum_name}")
            seen_seq.add(iss.sequence)
        expected_seq = set(range(len(enum_issues)))
        if seen_seq != expected_seq:
            missing = expected_seq - seen_seq
            extra = seen_seq - expected_seq
            msg = []
            if missing:
                msg.append(f"missing sequences {sorted(missing)}")
            if extra:
                msg.append(f"extra sequences {sorted(extra)}")
            _protocol_error(f"sequence violation for {enum_name}: {'; '.join(msg)}")

        # Per-enumerator count
        if enum_summary.issue_count != len(enum_issues):
            _protocol_error(
                f"issue_count mismatch for {enum_name}: "
                f"summary says {enum_summary.issue_count}, "
                f"parsed {len(enum_issues)}"
            )

    # Check no unexpected enumerators
    for enum_name in by_enum:
        if enum_name not in expected_enumerators:
            _protocol_error(f"unexpected enumerator {enum_name!r} "
                            f"(not in {suite} manifest)")

    for enum_name in summary_map:
        if enum_name not in expected_enumerators:
            _protocol_error(f"unexpected summary enumerator {enum_name!r} "
                            f"(not in {suite} manifest)")

    # Global count
    total_parsed = len(issues)
    total_summarized = sum(s.issue_count for s in summaries)
    if total_parsed != total_summarized:
        _protocol_error(
            f"global count mismatch: parsed {total_parsed}, "
            f"summarized {total_summarized}"
        )


def parse_jsonl_protocol(stderr_path: str, stdout_path: str,
                         suite: Optional[str] = None) -> Tuple[List[JsonlIssue], List[JsonlSummary]]:
    """Parse JSONL protocol from Catch2 stderr and stdout.

    Raises SystemExit(3) on protocol errors.
    Returns (issues, summaries) sorted by transport order.
    """
    # Read stderr
    if not stderr_path or not os.path.exists(stderr_path):
        _protocol_error(f"stderr file not found: {stderr_path}")

    with open(stderr_path, "r", encoding="utf-8", errors="replace") as f:
        stderr_text = f.read()

    # Check for old protocol
    old_protocol_found = False
    issues = []
    summaries = []
    jsonl_count = 0

    for line_num, line in enumerate(stderr_text.splitlines(), 1):
        line_stripped = line.strip()

        # Skip non-protocol lines
        if not line_stripped.startswith("ZH_ISSUE"):
            continue

        if line_stripped.startswith("ZH_ISSUE:"):
            # Old protocol - error
            _protocol_error(
                f"stderr line {line_num}: old ZH_ISSUE: protocol detected "
                f"(must use ZH_ISSUE_JSON: after migration)"
            )

        if line_stripped.startswith("ZH_ISSUE_JSON:"):
            json_str = JSONL_PREFIX_RE.sub("", line_stripped)
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError as e:
                _protocol_error(
                    f"stderr line {line_num}: invalid JSON: {e}\n"
                    f"  content: {json_str[:200]}"
                )

            # Validate schema
            _validate_jsonl_line(data)

            if data["record_type"] == "issue":
                issues.append(JsonlIssue(data))
            else:
                summaries.append(JsonlSummary(data))
            jsonl_count += 1

    # Read stdout — must NOT contain ZH_ISSUE_JSON:
    if stdout_path and os.path.exists(stdout_path):
        with open(stdout_path, "r", encoding="utf-8", errors="replace") as f:
            for line_num, line in enumerate(f, 1):
                if "ZH_ISSUE_JSON:" in line:
                    _protocol_error(
                        f"stdout line {line_num}: ZH_ISSUE_JSON: found "
                        f"(protocol records must go to stderr only)"
                    )

    if jsonl_count == 0:
        _protocol_error("no ZH_ISSUE_JSON: records found in stderr")

    # Determine suite from records if not specified
    if suite is None:
        suites_in_use = set(iss.suite for iss in issues) | set(s.suite for s in summaries)
        if len(suites_in_use) == 1:
            suite = suites_in_use.pop()
        elif len(suites_in_use) > 1:
            _protocol_error(f"multiple suites found: {suites_in_use} (must be uniform)")
        else:
            _protocol_error("no records to determine suite")

    # Validate identity, ordering, conservation
    expected_enums = (
        ZH_TRANSLATION_ENUMERATORS if suite == "zh_translation"
        else ZH_HELP_ENUMERATORS
    )
    _validate_conservation(issues, summaries, suite, expected_enums)

    return issues, summaries


# ============================================================================
# Baseline management
# ============================================================================

def _check_catch2_protocol_in_baseline(baseline: dict, suite: str,
                                       enumerators: List[str]) -> None:
    """Check that the baseline has the correct catch2_protocol metadata.

    Exits 2 on mismatch or missing fields. Exits 0 on success.
    """
    proto = baseline.get("catch2_protocol")
    if proto is None:
        print(f"ERROR: baseline missing 'catch2_protocol' field; "
              f"run --migrate-baseline-protocol first",
              file=sys.stderr)
        sys.exit(2)

    expected = _make_catch2_protocol(suite, enumerators)
    errors = []

    if proto.get("schema") != expected["schema"]:
        errors.append(f"schema: {proto.get('schema')!r} != {expected['schema']!r}")
    if proto.get("schema_version") != expected["schema_version"]:
        errors.append(
            f"schema_version: {proto.get('schema_version')!r} != "
            f"{expected['schema_version']!r}"
        )
    if proto.get("suite") != expected["suite"]:
        errors.append(f"suite: {proto.get('suite')!r} != {expected['suite']!r}")
    if proto.get("enumerators") != expected["enumerators"]:
        errors.append(
            f"enumerators: {proto.get('enumerators')!r} != "
            f"{expected['enumerators']!r}"
        )
    if proto.get("manifest_sha256") != expected["manifest_sha256"]:
        errors.append(
            f"manifest_sha256: {proto.get('manifest_sha256')!r} != "
            f"{expected['manifest_sha256']!r}"
        )

    if errors:
        print("ERROR: catch2_protocol metadata mismatch:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(2)


def migrate_baseline_protocol(path: str, suite: str) -> int:
    """Add catch2_protocol metadata to a baseline file.

    Exits 2 if:
        - file not found or unreadable
        - file has legacy Catch2 issues that would be lost by migration
        - file already has correct metadata (idempotent: return 0, no change)

    Exits 0 on successful migration.
    """
    if suite not in VALID_SUITES:
        print(f"ERROR: unknown suite {suite!r}", file=sys.stderr)
        return 2

    if not os.path.exists(path):
        print(f"ERROR: baseline file not found: {path}", file=sys.stderr)
        return 2

    with open(path, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    enumerators = (
        ZH_TRANSLATION_ENUMERATORS if suite == "zh_translation"
        else ZH_HELP_ENUMERATORS
    )

    # Check if already has correct protocol metadata
    existing = baseline.get("catch2_protocol")
    expected = _make_catch2_protocol(suite, enumerators)

    if existing == expected:
        # Already correct — idempotent
        return 0

    # Check for legacy Catch2 issues
    layer = baseline.get("layer1_catch2", {})
    total_issues = layer.get("total_issues", 0)
    all_issues = baseline.get("all_issues", [])
    c2_issues = [i for i in all_issues if i.get("layer") == "catch2"]
    if total_issues > 0 or c2_issues:
        print(f"ERROR: baseline has {total_issues} Catch2 issue(s); "
              f"metadata-only migration refused. "
              f"Use manual rebuild instead.",
              file=sys.stderr)
        return 2

    # Help baseline check
    if suite == "zh_help":
        help_layer = baseline.get("layer_help", {})
        help_c2_issues = help_layer.get("catch2_issues", 0)
        if help_c2_issues > 0:
            print(f"ERROR: help baseline has {help_c2_issues} Catch2 issue(s); "
                  f"metadata-only migration refused.",
                  file=sys.stderr)
            return 2

    if existing is not None and existing != expected:
        print(f"ERROR: existing catch2_protocol metadata does not match "
              f"expected suite={suite}; manual reconciliation required.",
              file=sys.stderr)
        return 2

    # Add metadata
    baseline["catch2_protocol"] = expected

    with open(path, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2, ensure_ascii=False, default=str)

    print(f"Migrated: {path}")
    return 0


def check_baseline_protocol(path: str) -> int:
    """Verify a baseline file has correct catch2_protocol metadata.

    Exits 2 on any problem. Exits 0 on success.
    """
    if not os.path.exists(path):
        print(f"ERROR: baseline file not found: {path}", file=sys.stderr)
        return 2

    with open(path, "r", encoding="utf-8") as f:
        baseline = json.load(f)

    proto = baseline.get("catch2_protocol")
    if proto is None:
        print(f"ERROR: {path} missing catch2_protocol field", file=sys.stderr)
        return 2

    schema = proto.get("schema")
    sv = proto.get("schema_version")
    suite = proto.get("suite")
    enumerators = proto.get("enumerators", [])
    manifest_sha256 = proto.get("manifest_sha256")

    if schema != "dcss-zh-catch2-jsonl":
        print(f"ERROR: unknown schema {schema!r}", file=sys.stderr)
        return 2
    if sv != SCHEMA_VERSION:
        print(f"ERROR: unknown schema_version {sv}", file=sys.stderr)
        return 2
    if suite not in VALID_SUITES:
        print(f"ERROR: unknown suite {suite!r}", file=sys.stderr)
        return 2

    expected_enums = (
        ZH_TRANSLATION_ENUMERATORS if suite == "zh_translation"
        else ZH_HELP_ENUMERATORS
    )
    if enumerators != expected_enums:
        print(f"ERROR: enumerators mismatch", file=sys.stderr)
        return 2

    expected_sha = _manifest_sha256(suite, enumerators)
    if manifest_sha256 != expected_sha:
        print(f"ERROR: manifest_sha256 mismatch: "
              f"{manifest_sha256!r} != {expected_sha!r}",
              file=sys.stderr)
        return 2

    return 0


# ============================================================================
# Baseline building and comparison
# ============================================================================

def build_catch2_baseline(issues: List[JsonlIssue],
                          summaries: List[JsonlSummary]) -> dict:
    """Build a catch2-only baseline from parsed JSONL protocol data."""
    by_kind = Counter(iss.kind for iss in issues)
    by_enumerator = defaultdict(int)
    for iss in issues:
        by_enumerator[iss.enumerator] += 1

    baseline = {
        "layer1_catch2": {
            "total_issues": len(issues),
            "by_kind": dict(by_kind),
            "by_enumerator": dict(by_enumerator),
        },
        "all_issues": [
            {
                "enumerator": iss.enumerator,
                "kind": iss.kind,
                "kind_name": iss.kind,
                "source": iss.source,
                "key": iss.key,
                "sample": iss.sample,
                "sample_bytes_hex": iss.sample_bytes_hex,
                "sequence": iss.sequence,
                "layer": "catch2",
            }
            for iss in issues
        ],
        "grand_total": len(issues),
    }
    return baseline


def build_help_baseline_from_jsonl(issues: List[JsonlIssue],
                                   summaries: List[JsonlSummary]) -> dict:
    """Build a help-mode baseline section from parsed JSONL protocol data."""
    by_kind = Counter(iss.kind for iss in issues)
    by_enumerator = defaultdict(int)
    for iss in issues:
        by_enumerator[iss.enumerator] += 1

    help_section = {
        "catch2_issues": len(issues),
        "catch2_by_kind": dict(by_kind),
        "catch2_issue_records": [
            {
                "enumerator": iss.enumerator,
                "kind": iss.kind,
                "kind_name": iss.kind,
                "sequence": iss.sequence,
                "source": iss.source,
                "key": iss.key,
                "sample": iss.sample,
            }
            for iss in issues
        ],
    }
    return {"layer_help": help_section}


def compare_issue_sets(previous_issues: List[dict],
                       current_issues: List[dict]) -> int:
    """Count regressions (new issues) between two issue lists.

    Uses signature-based comparison: (enumerator, kind, source, key, sample_bytes_hex).
    Returns count of CURRENT - PREVIOUS (positive = regression).
    """
    def sig(iss: dict) -> tuple:
        return (
            iss.get("enumerator", iss.get("layer", "")),
            iss.get("kind", ""),
            iss.get("source", ""),
            iss.get("key", ""),
            iss.get("sample_bytes_hex", iss.get("sample", "")),
        )

    prev_counts = Counter(sig(i) for i in previous_issues)
    curr_counts = Counter(sig(i) for i in current_issues)
    delta = curr_counts - prev_counts
    return sum(delta.values())


def compare_baselines_simple(previous: dict, current: dict) -> dict:
    """Simple comparison between two baselines.

    Returns a report dict with regression count.
    """
    prev_issues = previous.get("all_issues", [])
    curr_issues = current.get("all_issues", [])
    regression_count = compare_issue_sets(prev_issues, curr_issues)

    return {
        "prev_total": len(prev_issues),
        "curr_total": len(curr_issues),
        "delta": len(curr_issues) - len(prev_issues),
        "regressions": regression_count,
    }


# ============================================================================
# Generic mode (default)
# ============================================================================

def _mode_generic(args) -> int:
    """Generic mode: parse JSONL protocol from Catch2 and compare/write baseline.

    Requires --catch2-stderr and --catch2-stdout as a pair.
    """
    if not args.catch2_stderr or not args.catch2_stdout:
        _usage_error("generic mode requires both --catch2-stderr and --catch2-stdout")

    suite = "zh_translation"
    issues, summaries = parse_jsonl_protocol(
        args.catch2_stderr, args.catch2_stdout, suite
    )

    # Verify suite completeness
    enum_set = set(s.enumerator for s in summaries)
    expected_set = set(ZH_TRANSLATION_ENUMERATORS)
    missing = expected_set - enum_set
    if missing:
        _protocol_error(
            f"incomplete zh_translation suite: missing enumerators {sorted(missing)}"
        )

    current = build_catch2_baseline(issues, summaries)

    if args.output_baseline:
        # Add protocol metadata
        proto = _make_catch2_protocol(suite, ZH_TRANSLATION_ENUMERATORS)
        current["catch2_protocol"] = proto

        with open(args.output_baseline, "w", encoding="utf-8") as f:
            json.dump(current, f, indent=2, ensure_ascii=False, default=str)
        print(f"Baseline written: {args.output_baseline}")
        print(f"  Enumerators: {len(summaries)}")
        print(f"  Total issues: {current.get('grand_total', 0)}")
        return 0

    if args.baseline:
        if not os.path.exists(args.baseline):
            print(f"ERROR: baseline file not found: {args.baseline}",
                  file=sys.stderr)
            return 2

        with open(args.baseline, "r", encoding="utf-8") as f:
            previous = json.load(f)

        # Check baseline protocol metadata
        _check_catch2_protocol_in_baseline(
            previous, suite, ZH_TRANSLATION_ENUMERATORS
        )

        report = compare_baselines_simple(previous, current)

        print(f"Regression report:")
        print(f"  Previous total: {report['prev_total']}")
        print(f"  Current total:  {report['curr_total']}")
        print(f"  Delta:          {report['delta']:+d}")
        print(f"  Regressions:    {report['regressions']}")

        if report["regressions"] > 0:
            return 1
        return 0

    # No baseline — just summary
    print(f"Summary (no comparison baseline):")
    print(f"  Enumerators: {len(summaries)}")
    print(f"  Total issues: {len(issues)}")
    for s in sorted(summaries, key=lambda x: x.enumerator):
        print(f"  {s.enumerator}: {s.issue_count} issues")
    return 0


# ============================================================================
# Help mode
# ============================================================================

def _mode_help(args) -> int:
    """Help-system aggregation mode."""
    if not args.catch2_stderr or not args.catch2_stdout:
        _usage_error("help mode requires both --catch2-stderr and --catch2-stdout")

    suite = "zh_help"
    issues, summaries = parse_jsonl_protocol(
        args.catch2_stderr, args.catch2_stdout, suite
    )

    # Verify suite completeness
    enum_set = set(s.enumerator for s in summaries)
    expected_set = set(ZH_HELP_ENUMERATORS)
    missing = expected_set - enum_set
    if missing:
        _protocol_error(
            f"incomplete zh_help suite: missing enumerators {sorted(missing)}"
        )

    current = build_help_baseline_from_jsonl(issues, summaries)

    if args.bot_stderr:
        records = _parse_bot_frame_records(args.bot_stderr)
        observed = [record["case_id"] for record in records]
        if observed != HELP_BOT_EXPECTED_IDS:
            _protocol_error(
                "help bot manifest mismatch: expected "
                f"{HELP_BOT_EXPECTED_IDS}, got {observed}"
            )

    if args.output_baseline:
        proto = _make_catch2_protocol(suite, ZH_HELP_ENUMERATORS)

        # Merge with existing baseline if it exists
        merged = {}
        if os.path.exists(args.output_baseline):
            try:
                with open(args.output_baseline, "r") as f:
                    merged = json.load(f)
            except (ValueError, OSError):
                merged = {}

        merged["catch2_protocol"] = proto
        merged["layer_help"] = current["layer_help"]

        with open(args.output_baseline, "w", encoding="utf-8") as f:
            json.dump(merged, f, indent=2, ensure_ascii=False, default=str)
        print(f"Help baseline written: {args.output_baseline}")
        print(f"  Catch2 issues: {len(issues)}")
        return 0

    if args.baseline:
        if not os.path.exists(args.baseline):
            print(f"ERROR: baseline file not found: {args.baseline}",
                  file=sys.stderr)
            return 2

        with open(args.baseline, "r", encoding="utf-8") as f:
            previous = json.load(f)

        _check_catch2_protocol_in_baseline(
            previous, suite, ZH_HELP_ENUMERATORS
        )

        prev_issues = previous.get("layer_help", {}).get("catch2_issue_records", [])
        curr_issues = current["layer_help"].get("catch2_issue_records", [])
        regression_count = compare_issue_sets(prev_issues, curr_issues)

        print(f"Help regression report:")
        print(f"  Previous issues: {len(prev_issues)}")
        print(f"  Current issues:  {len(curr_issues)}")
        print(f"  Regressions:     {regression_count}")

        if regression_count > 0:
            return 1
        return 0

    # No baseline — just summary
    print(f"Help summary (no comparison baseline):")
    print(f"  Total issues: {len(issues)}")
    for s in sorted(summaries, key=lambda x: x.enumerator):
        print(f"  {s.enumerator}: {s.issue_count} issues")
    return 0


# ============================================================================
# Deprecated old-format parsers (kept for backward compat in existing tests)
# ============================================================================

def parse_catch2_stderr(path: str) -> Tuple[Dict[str, int], List[dict]]:
    """DEPRECATED: Parse old ZH_ISSUE lines from catch2 stderr.

    Kept for backward compat with test_zh_runtime_check.sh.
    """
    by_kind = defaultdict(int)
    issues = []
    if not path or not os.path.exists(path):
        return by_kind, issues
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.match(r'ZH_ISSUE:\s*(\d+)\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*(.*)', line)
            if m:
                kind = int(m.group(1))
                source = m.group(2).strip()
                key = m.group(3).strip()
                sample = m.group(4).strip()
                KIND_NAMES_OLD = {
                    0: "UNTRANSLATED", 1: "MIXED_CN_EN", 2: "FORMAT_BROKEN",
                    3: "GARBLED_UTF8", 4: "EMPTY_DB", 5: "WHITESPACE_ANOMALY",
                    6: "INVISIBLE_CHAR", 7: "PUNCT_STYLE",
                    8: "EMBEDDED_LUA_ERROR",
                }
                by_kind[KIND_NAMES_OLD.get(kind, str(kind))] += 1
                issues.append({
                    "kind": kind, "kind_name": KIND_NAMES_OLD.get(kind, "?"),
                    "source": source, "key": key, "sample": sample[:120],
                    "layer": "catch2",
                })
    return by_kind, issues


def parse_catch2_stdout(path: str) -> Dict[str, int]:
    """DEPRECATED: Parse 'zh enumerator summary: <name> -> N issues' from stdout."""
    summaries = {}
    if not path or not os.path.exists(path):
        return summaries
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.match(r'.*zh enumerator summary:\s*(.+?)\s*->\s*(\d+)\s+issues', line)
            if m:
                summaries[m.group(1).strip()] = int(m.group(2))
    return summaries


def _parse_bot_frame_records(path: str) -> List[dict]:
    """Read FRAME_MARKER records from the combined RC-bot transcript."""
    if not path or not os.path.isfile(path):
        _usage_error(f"bot stderr file not found: {path!r}")
    records = []
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        for lineno, line in enumerate(f, 1):
            match = re.search(
                r"FRAME_MARKER:\s*(.+?)\s*\| ?(.*?)(?:\r?\n)?$", line
            )
            if match:
                records.append({
                    "case_id": match.group(1).strip(),
                    "content": match.group(2),
                    "line": lineno,
                })
    return records


def _mode_bot(args) -> int:
    """Validate the exact RC-bot case manifest, ordering, and semantics."""
    if not args.bot_stderr:
        _usage_error("--mode bot requires --bot-stderr")
    if not args.bot_manifest:
        _usage_error("--mode bot requires --bot-manifest")

    expected = BOT_CASE_MANIFESTS[args.bot_manifest]
    records = _parse_bot_frame_records(args.bot_stderr)
    observed = [record["case_id"] for record in records]
    counts = Counter(observed)
    missing = [case_id for case_id in expected if counts[case_id] == 0]
    duplicates = sorted(
        case_id for case_id, count in counts.items() if count > 1
    )
    unexpected = [case_id for case_id in observed if case_id not in expected]
    in_manifest = [case_id for case_id in observed if case_id in expected]
    out_of_order = in_manifest != expected

    unique_content = {
        record["case_id"]: record["content"]
        for record in records
        if counts[record["case_id"]] == 1
    }
    semantic_failures = []
    for case_id in expected:
        absent = [
            token for token in BOT_REQUIRED_CONTENT.get(case_id, ())
            if token not in unique_content.get(case_id, "")
        ]
        if absent:
            semantic_failures.append({
                "case_id": case_id,
                "missing_tokens": absent,
            })

    print(f"Bot manifest: {args.bot_manifest}")
    print(f"Bot coverage: {len(observed)} / {len(expected)} markers")
    print(f"Missing: {missing}")
    print(f"Duplicates: {duplicates}")
    print(f"Unexpected: {unexpected}")
    print(f"Out of order: {out_of_order}")
    print(f"Semantic failures: {semantic_failures}")
    return 1 if (missing or duplicates or unexpected or out_of_order
                 or semantic_failures) else 0


# ============================================================================
# Main CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="zh-runtime check — JSONL v1 issue protocol parser & baseline manager"
    )

    # Input/output
    parser.add_argument("--catch2-stderr",
                        help="stderr from catch2-tests [zh-translation] or [zh-help]")
    parser.add_argument("--catch2-stdout",
                        help="stdout from catch2-tests [zh-translation] or [zh-help]")
    parser.add_argument("--baseline",
                        help="previous baseline JSON to compare against")
    parser.add_argument("--output-baseline",
                        help="write new baseline to this path")

    # Mode selection
    parser.add_argument("--mode", choices=("generic", "help", "bot"), default=None,
                        help="aggregation mode: generic (Catch2 JSONL, default when "
                             "catch2-stderr given), help (help-system status), "
                             "or bot (exact RC manifest)")

    # Protocol management
    parser.add_argument("--migrate-baseline-protocol",
                        help="add catch2_protocol metadata to a baseline file")
    parser.add_argument("--check-baseline-protocol",
                        help="verify catch2_protocol metadata in a baseline file")
    parser.add_argument("--suite", choices=("zh_translation", "zh_help"),
                        help="suite for baseline protocol migration")

    # Layer inputs. Lua remains accepted for compatibility; bot inputs are
    # active only in the explicit bot mode.
    parser.add_argument("--lua-stderr", help=argparse.SUPPRESS)
    parser.add_argument("--bot-stderr", help="combined RC-bot transcript")
    parser.add_argument("--json", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--bot-manifest", choices=tuple(BOT_CASE_MANIFESTS),
                        help="exact RC-bot manifest to require")

    args = parser.parse_args()

    # --- Protocol management commands ---
    if args.migrate_baseline_protocol:
        if not args.suite:
            _usage_error("--migrate-baseline-protocol requires --suite")
        return migrate_baseline_protocol(args.migrate_baseline_protocol, args.suite)

    if args.check_baseline_protocol:
        return check_baseline_protocol(args.check_baseline_protocol)

    # --- Mode selection ---
    mode = args.mode
    if mode is None:
        if args.catch2_stderr and args.catch2_stdout:
            mode = "generic"
        else:
            mode = "generic"  # default, may fail if args missing

    # --- Catch2-only modes ---
    if mode == "generic":
        return _mode_generic(args)

    if mode == "help":
        return _mode_help(args)

    if mode == "bot":
        return _mode_bot(args)

    # Fallback (should not reach)
    _usage_error("unrecognized mode or missing arguments")
    return 2


if __name__ == "__main__":
    sys.exit(main())
