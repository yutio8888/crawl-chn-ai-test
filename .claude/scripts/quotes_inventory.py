#!/usr/bin/env python3
"""Build and audit the complete Issue #72 quotes TextDB inventory.

The inventory is read-only and bound to exact Git blobs.  It mirrors the
production DescriptionDB parser, records the comment-only ``####`` section
headings separately from TextDB identities, follows ``<target>`` aliases with
the same lowercase key semantics as ``_query_database``, and binds the
producer/load/consumer chain used by ``getQuoteString``.

The strict JSONL ledger is deliberately a review artifact, not terminology
authority.  Candidate mode proves that every English block is unchanged and
every Chinese block equals its card's accepted proposal (or its frozen value
for keep/defer decisions).
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from command_inventory import (  # noqa: E402
    _desc_display,
    merge_desc_sequence,
    parse_db_keys,
    resolve_commit,
    write_inventory_output,
)
from i18n_shared import (  # noqa: E402
    AuditInput,
    AuditInputError,
    load_review_input,
    lowercase_string,
    read_regular_git_blob,
    review_input_metadata,
)


QUOTES_EN = "crawl-ref/source/dat/descript/quotes.txt"
QUOTES_ZH = "crawl-ref/source/dat/descript/zh/quotes.txt"
DATABASE_CC = "crawl-ref/source/database.cc"
DATABASE_H = "crawl-ref/source/database.h"
LOOKUP_HELP_CC = "crawl-ref/source/lookup-help.cc"
DESCRIBE_CC = "crawl-ref/source/describe.cc"
MUTATION_CC = "crawl-ref/source/mutation.cc"
ABILITY_CC = "crawl-ref/source/ability.cc"
MONSTER_SSOT = ".claude/scripts/monster_name_ssot.py"
ZH_SOURCE = "crawl-ref/source/dat/i18n/zh/source.txt"
GLOSSARY_MD = "docs/glossary.md"
DECISIONS_MD = "docs/decisions.md"

INPUT_PATHS = (
    QUOTES_EN,
    QUOTES_ZH,
    DATABASE_CC,
    DATABASE_H,
    LOOKUP_HELP_CC,
    DESCRIBE_CC,
    MUTATION_CC,
    ABILITY_CC,
    MONSTER_SSOT,
    ZH_SOURCE,
    GLOSSARY_MD,
    DECISIONS_MD,
)

STRICT_REVIEW_BEGIN = "<!-- BEGIN STRICT QUOTES REVIEW EVIDENCE v1 -->"
STRICT_REVIEW_END = "<!-- END STRICT QUOTES REVIEW EVIDENCE v1 -->"
TERMINAL_CONCLUSIONS = {
    "keep",
    "adjust",
    "retranslate",
    "defer terminology",
    "defer implementation",
}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
STRICT_CARD_FIELDS = {
    "alias_target",
    "confidence",
    "current_chinese",
    "current_english",
    "decision_authority",
    "deferral_owner",
    "deferral_reason",
    "dependency_group",
    "display_context",
    "evidence_locations",
    "fact_sha256",
    "glossary_authority",
    "identity",
    "key",
    "lifecycle",
    "literary_exception_reason",
    "producer_consumer",
    "proposed_translation",
    "reentry_trigger",
    "rejected_alternatives",
    "resolved_key",
    "reviewer_rationale",
    "section",
    "suggestions",
    "terminal_conclusion",
}

_SECTION_BORDER_RE = re.compile(r"^#{8,}$")
_SECTION_TITLE_RE = re.compile(r"^#\s+([^#].*?)\s*$")
_ALIAS_RE = re.compile(r"<([^<>\n]+)>")


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _sha(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return hashlib.sha256(value).hexdigest()


def _single_fragment(text: str, fragment: str, path: str) -> str:
    count = text.count(fragment)
    if count != 1:
        raise RuntimeError(
            f"{path}: expected exactly one provenance fragment {fragment!r}, "
            f"found {count}"
        )
    line = text[:text.index(fragment)].count("\n") + 1
    return f"{path}:{line}"


def _verify_provenance(blobs: dict[str, bytes]) -> dict[str, object]:
    required = {
        DATABASE_CC: (
            'TextDB("quotes", "descript/",',
            '{ "quotes.txt"    // quotes for items and monsters',
            "static TextDB& QuotesDB      = AllDBs[6];",
            "string getQuoteString(const string &key)",
            "return unwrap_desc(_query_database(QuotesDB, key, true, true));",
            "// <foo> is an alias to key foo",
        ),
        DATABASE_H: ("string getQuoteString(const string &key);",),
        LOOKUP_HELP_CC: ("inf.quote = getQuoteString(key);",),
        MUTATION_CC: ("const string quote = getQuoteString(key);",),
        ABILITY_CC: (
            'const string quote = getQuoteString(name + " ability");',
        ),
        DESCRIBE_CC: (
            "inf.body << long_desc;\n\n    if (include_extra)",
            "// And quotes {due}\n    inf.quote = getQuoteString(db_name);",
            "quote = getQuoteString(get_unrand_name_en(item));",
            "quote = getQuoteString(item.name(DESC_DBNAME, true, false, false));",
            'getQuoteString(string(spell_english_name(spell)) + " spell")',
            "quote2 = getQuoteString(symbol_suffix);",
        ),
    }
    anchors: dict[str, str] = {}
    for path, fragments in required.items():
        text = blobs[path].decode("utf-8", errors="strict")
        for fragment in fragments:
            anchors[f"{path}@{fragment}"] = _single_fragment(text, fragment, path)
    return {
        "loader": "TextDB quotes loads descript/quotes.txt; locale overlay loads descript/zh/quotes.txt",
        "lookup": "getQuoteString -> lowercase canonical key -> localized DB -> EN fallback -> <target> alias -> substitutions/Lua -> unwrap_desc",
        "display_consumers": [
            LOOKUP_HELP_CC,
            DESCRIBE_CC,
            MUTATION_CC,
            ABILITY_CC,
        ],
        "anchors": anchors,
    }


def _section_markers(text: str, path: str) -> list[tuple[int, str]]:
    lines = text.split("\n")
    result: list[tuple[int, str]] = []
    for index in range(len(lines) - 4):
        title = _SECTION_TITLE_RE.fullmatch(lines[index + 2])
        if (
            _SECTION_BORDER_RE.fullmatch(lines[index])
            and lines[index + 1] == "#"
            and title
            and lines[index + 3] == "#"
            and _SECTION_BORDER_RE.fullmatch(lines[index + 4])
        ):
            result.append((index + 5, title.group(1)))
    if not result:
        raise RuntimeError(f"{path}: no #### section headings found")
    if len({name for _, name in result}) != len(result):
        raise RuntimeError(f"{path}: duplicate #### section heading")
    return result


def _entry_sections(text: str, entries: list[object], path: str) -> dict[str, str]:
    markers = _section_markers(text, path)
    result: dict[str, str] = {}
    marker_index = 0
    section: str | None = None
    for entry in entries:
        while marker_index < len(markers) and markers[marker_index][0] < entry.key_line:
            section = markers[marker_index][1]
            marker_index += 1
        if section is None:
            raise RuntimeError(f"{path}:{entry.key_line}: entry precedes first section")
        result[lowercase_string(entry.raw_key)] = section
    return result


def _literal_mapping(source: str, variable: str) -> dict[str, str]:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.AnnAssign):
            continue
        if isinstance(node.target, ast.Name) and node.target.id == variable:
            value = ast.literal_eval(node.value)
            if not isinstance(value, dict) or not all(
                isinstance(key, str) and isinstance(reason, str)
                for key, reason in value.items()
            ):
                break
            return {lowercase_string(key): reason for key, reason in value.items()}
    raise RuntimeError(f"{MONSTER_SSOT}: cannot parse {variable}")


def _alias_target(value: str) -> str | None:
    match = _ALIAS_RE.fullmatch(value)
    return lowercase_string(match.group(1)) if match else None


def _resolve_aliases(entries: dict[str, object]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for key in entries:
        current = key
        seen: list[str] = []
        while True:
            if current in seen:
                raise RuntimeError(f"quotes alias cycle: {' -> '.join(seen + [current])}")
            seen.append(current)
            entry = entries.get(current)
            if entry is None:
                raise RuntimeError(f"quotes alias target is missing: {' -> '.join(seen)}")
            target = _alias_target(_desc_display(entry.value))
            if target is None:
                resolved[key] = current
                break
            current = target
    return resolved


def _attribution_lines(value: str) -> list[dict[str, object]]:
    result = []
    for number, line in enumerate(value.split("\n"), start=1):
        stripped = line.strip()
        if stripped.startswith(("-", "—")) or stripped.lower().startswith(
            ("trans.", "translation ")
        ):
            result.append({"body_line": number, "text": line})
    return result


def _fact_sha(row: dict[str, object]) -> str:
    return _sha(_canonical_json(row))


def _regular_blob(commit: str, path: str) -> bytes:
    try:
        mode, data = read_regular_git_blob(ROOT, commit, path, with_mode=True)
    except AuditInputError as error:
        raise RuntimeError(
            f"cannot read exact-Git input {path}@{commit[:12]}: {error}"
        ) from error
    if mode not in {"100644", "100755"}:
        raise RuntimeError(
            f"exact-Git input {path}@{commit[:12]} is not a regular blob: {mode}"
        )
    return data


def _load_blobs(commit: str) -> dict[str, bytes]:
    return {path: _regular_blob(commit, path) for path in INPUT_PATHS}


def _load_git_review_input(commit: str, supplied: Path) -> AuditInput:
    path = supplied if supplied.is_absolute() else ROOT / supplied
    try:
        relative = path.relative_to(ROOT)
    except ValueError as error:
        raise RuntimeError("review results path is outside the repository") from error
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise RuntimeError("review results path is not normalized")
    logical = relative.as_posix()
    data = _regular_blob(commit, logical)
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise RuntimeError("review results are not strict UTF-8") from error
    return AuditInput(
        audit_commit=commit,
        logical_path=logical,
        relative_path=logical,
        bytes=data,
        text=text,
        sha256=_sha(data),
    )


def build_payload(baseline: str) -> dict[str, object]:
    blobs = _load_blobs(baseline)
    texts = {
        path: data.decode("utf-8", errors="strict") for path, data in blobs.items()
    }
    provenance = _verify_provenance(blobs)

    en_physical = parse_db_keys(texts[QUOTES_EN], QUOTES_EN)
    zh_physical = parse_db_keys(texts[QUOTES_ZH], QUOTES_ZH)
    en_effective, en_overrides = merge_desc_sequence(en_physical)
    zh_effective, zh_overrides = merge_desc_sequence(zh_physical)
    if en_overrides or zh_overrides:
        raise RuntimeError(
            f"quotes TextDB overrides are forbidden: EN={en_overrides}, ZH={zh_overrides}"
        )

    en_order = [lowercase_string(entry.raw_key) for entry in en_physical]
    zh_order = [lowercase_string(entry.raw_key) for entry in zh_physical]
    if len(set(en_order)) != len(en_order) or len(set(zh_order)) != len(zh_order):
        raise RuntimeError("quotes physical identity uniqueness failed")

    en_sections = _entry_sections(texts[QUOTES_EN], en_physical, QUOTES_EN)
    zh_sections = _entry_sections(texts[QUOTES_ZH], zh_physical, QUOTES_ZH)
    aliases = _resolve_aliases(en_effective)
    zh_aliases = _resolve_aliases(zh_effective)
    exceptions = _literal_mapping(texts[MONSTER_SSOT], "QUOTE_NAME_EXCEPTIONS")

    inventory = []
    for key in en_order:
        en = en_effective[key]
        zh = zh_effective.get(key)
        english = _desc_display(en.value)
        chinese = _desc_display(zh.value) if zh else None
        en_alias = _alias_target(english)
        zh_alias = _alias_target(chinese) if isinstance(chinese, str) else None
        mechanical: dict[str, object] = {
            "identity": f"quotes:{key}",
            "key": key,
            "raw_key": en.raw_key,
            "lifecycle": "alias" if en_alias is not None else "direct-quote",
            "section": en_sections[key],
            "english": english,
            "chinese": chinese,
            "english_key_line": en.key_line,
            "chinese_key_line": zh.key_line if zh else None,
            "english_body_line_count": len(english.split("\n")),
            "chinese_body_line_count": (
                len(chinese.split("\n")) if isinstance(chinese, str) else None
            ),
            "english_attribution_lines": _attribution_lines(english),
            "chinese_attribution_lines": (
                _attribution_lines(chinese) if isinstance(chinese, str) else []
            ),
            "alias_target": en_alias,
            "chinese_alias_target": zh_alias,
            "resolved_key": aliases[key],
            "chinese_resolved_key": zh_aliases.get(key),
            "dependency_group": (
                f"alias->{en_alias}" if en_alias is not None else en_sections[key]
            ),
            "literary_exception_reason": exceptions.get(key),
        }
        mechanical["fact_sha256"] = _fact_sha(mechanical)
        inventory.append(mechanical)

    payload: dict[str, object] = {
        "schema": "quotes-inventory-v1",
        "baseline": baseline,
        "glossary_sha256": _sha(blobs[GLOSSARY_MD]),
        "inputs": {
            path: {"sha256": _sha(blobs[path])} for path in INPUT_PATHS
        },
        "provenance": provenance,
        "section_headings": [name for _, name in _section_markers(texts[QUOTES_EN], QUOTES_EN)],
        "english_keys": en_order,
        "chinese_keys": zh_order,
        "english_minus_chinese": sorted(set(en_order) - set(zh_order)),
        "chinese_minus_english": sorted(set(zh_order) - set(en_order)),
        "canonical_order_equal": en_order == zh_order,
        "section_assignments_equal": en_sections == zh_sections,
        "alias_graph_equal": aliases == zh_aliases,
        "identity_count": len(inventory),
        "direct_quote_count": sum(row["lifecycle"] == "direct-quote" for row in inventory),
        "alias_count": sum(row["lifecycle"] == "alias" for row in inventory),
        "inventory": inventory,
    }
    payload["inventory_sha256"] = _sha(_canonical_json(payload))
    return payload


def _load_json(line: str, label: str) -> object:
    def reject_constant(value: str) -> object:
        raise ValueError(f"non-finite JSON value {value}")

    try:
        return json.loads(line, parse_constant=reject_constant)
    except (json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(f"invalid {label} JSON") from error


def parse_review(
    review_input: AuditInput,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    text = review_input.text
    if text.count(STRICT_REVIEW_BEGIN) != 1 or text.count(STRICT_REVIEW_END) != 1:
        raise RuntimeError("strict quotes review block is missing or duplicated")
    block = text.split(STRICT_REVIEW_BEGIN, 1)[1].split(STRICT_REVIEW_END, 1)[0]
    if not block.startswith("\n") or not block.endswith("\n"):
        raise RuntimeError("strict quotes review framing is invalid")
    lines = block[1:-1].splitlines()
    if len(lines) < 4 or lines[1] != "```jsonl" or lines[-1] != "```":
        raise RuntimeError("strict quotes review structure is invalid")
    metadata = _load_json(lines[0], "quotes review metadata")
    expected_meta = {
        "alias_count",
        "baseline",
        "direct_quote_count",
        "glossary_sha256",
        "identity_count",
        "inventory_sha256",
    }
    if not isinstance(metadata, dict) or set(metadata) != expected_meta:
        raise RuntimeError("strict quotes review metadata fields are invalid")
    if lines[0] != _canonical_json(metadata):
        raise RuntimeError("strict quotes review metadata is not canonical JSON")

    cards = []
    for line in lines[2:-1]:
        card = _load_json(line, "quotes review card")
        if not isinstance(card, dict) or set(card) != STRICT_CARD_FIELDS:
            raise RuntimeError("strict quotes review card fields are invalid")
        if line != _canonical_json(card):
            raise RuntimeError("strict quotes review card is not canonical JSON")
        cards.append(card)
    return metadata, cards


def _mechanical_fields(row: dict[str, object]) -> dict[str, object]:
    return {
        "alias_target": row["alias_target"],
        "current_chinese": row["chinese"],
        "current_english": row["english"],
        "dependency_group": row["dependency_group"],
        "fact_sha256": row["fact_sha256"],
        "identity": row["identity"],
        "key": row["key"],
        "lifecycle": row["lifecycle"],
        "literary_exception_reason": row["literary_exception_reason"],
        "resolved_key": row["resolved_key"],
        "section": row["section"],
    }


def review_coverage(
    payload: dict[str, object], review_input: AuditInput
) -> dict[str, object]:
    metadata, cards = parse_review(review_input)
    inventory = payload["inventory"]
    assert isinstance(inventory, list)
    expected = {row["identity"]: row for row in inventory}
    inventory_ids = [row["identity"] for row in inventory]
    review_ids = [card["identity"] for card in cards]
    mismatches = []
    invalid = []
    for card in cards:
        identity = card["identity"]
        if identity in expected:
            for field, value in _mechanical_fields(expected[identity]).items():
                if _canonical_json(card[field]) != _canonical_json(value):
                    mismatches.append(f"{identity}:{field}")

        conclusion = card["terminal_conclusion"]
        proposal = card["proposed_translation"]
        if conclusion not in TERMINAL_CONCLUSIONS:
            invalid.append(f"{identity}:terminal_conclusion")
        if conclusion in {"adjust", "retranslate"}:
            if (
                not isinstance(proposal, str)
                or not proposal.strip()
                or proposal == card["current_chinese"]
            ):
                invalid.append(f"{identity}:proposed_translation")
        elif proposal is not None:
            invalid.append(f"{identity}:unexpected_proposal")

        for field in (
            "decision_authority",
            "display_context",
            "glossary_authority",
            "producer_consumer",
            "reviewer_rationale",
            "reentry_trigger",
        ):
            if not isinstance(card[field], str) or not card[field].strip():
                invalid.append(f"{identity}:{field}")
        for field in ("evidence_locations", "rejected_alternatives", "suggestions"):
            if not isinstance(card[field], list):
                invalid.append(f"{identity}:{field}")
        if not card["evidence_locations"]:
            invalid.append(f"{identity}:evidence_locations")
        if card["confidence"] not in CONFIDENCE_LEVELS:
            invalid.append(f"{identity}:confidence")

        deferred = conclusion in {"defer terminology", "defer implementation"}
        for field in ("deferral_reason", "deferral_owner"):
            value = card[field]
            if deferred and (not isinstance(value, str) or not value.strip()):
                invalid.append(f"{identity}:{field}")
            if not deferred and value is not None:
                invalid.append(f"{identity}:unexpected_{field}")

    binding = {
        "alias_count": metadata.get("alias_count") == payload["alias_count"],
        "baseline": metadata.get("baseline") == payload["baseline"],
        "direct_quote_count": metadata.get("direct_quote_count")
        == payload["direct_quote_count"],
        "glossary_sha256": metadata.get("glossary_sha256")
        == payload["glossary_sha256"],
        "identity_count": metadata.get("identity_count") == len(inventory),
        "inventory_sha256": metadata.get("inventory_sha256")
        == payload["inventory_sha256"],
    }
    duplicates = sorted(
        identity for identity, count in Counter(review_ids).items() if count > 1
    )
    coverage_equal = (
        all(binding.values())
        and review_ids == inventory_ids
        and not duplicates
        and not mismatches
        and not invalid
    )
    return {
        **review_input_metadata(review_input),
        "binding_matches": binding,
        "canonical_card_order": review_ids == inventory_ids,
        "coverage_equal": coverage_equal,
        "duplicate_evidence_cards": duplicates,
        "evidence_card_count": len(cards),
        "inventory_minus_review": sorted(set(inventory_ids) - set(review_ids)),
        "invalid_cards": sorted(invalid),
        "mismatched_mechanical_fields": sorted(mismatches),
        "review_minus_inventory": sorted(set(review_ids) - set(inventory_ids)),
        "terminal_conclusion_counts": dict(
            sorted(Counter(card["terminal_conclusion"] for card in cards).items())
        ),
    }


def candidate_agreement(
    payload: dict[str, object], review_input: AuditInput, candidate: str
) -> dict[str, object]:
    _metadata, cards = parse_review(review_input)
    candidate_payload = build_payload(candidate)
    inventory = payload["inventory"]
    candidate_inventory = candidate_payload["inventory"]
    assert isinstance(inventory, list) and isinstance(candidate_inventory, list)
    candidate_by_id = {row["identity"]: row for row in candidate_inventory}
    card_by_id = {card["identity"]: card for card in cards}
    mismatches = []
    english_drift = []
    structural_drift = []
    for row in inventory:
        identity = row["identity"]
        card = card_by_id.get(identity)
        actual = candidate_by_id.get(identity)
        if card is None or actual is None:
            mismatches.append(f"{identity}:missing")
            continue
        if actual["english"] != row["english"]:
            english_drift.append(identity)
        for field in (
            "key",
            "raw_key",
            "lifecycle",
            "section",
            "alias_target",
            "resolved_key",
        ):
            if actual[field] != row[field]:
                structural_drift.append(f"{identity}:{field}")
        expected_zh = (
            card["proposed_translation"]
            if card["terminal_conclusion"] in {"adjust", "retranslate"}
            else card["current_chinese"]
        )
        if actual["chinese"] != expected_zh:
            mismatches.append(identity)

    baseline_ids = [row["identity"] for row in inventory]
    candidate_ids = [row["identity"] for row in candidate_inventory]
    protected_input_drift = _protected_input_drift(payload, candidate_payload)
    return {
        "candidate": candidate,
        "candidate_agrees": (
            baseline_ids == candidate_ids
            and not mismatches
            and not english_drift
            and not structural_drift
            and not protected_input_drift
        ),
        "candidate_inventory_sha256": candidate_payload["inventory_sha256"],
        "candidate_minus_baseline": sorted(set(candidate_ids) - set(baseline_ids)),
        "baseline_minus_candidate": sorted(set(baseline_ids) - set(candidate_ids)),
        "canonical_order_equal": baseline_ids == candidate_ids,
        "english_drift": sorted(english_drift),
        "protected_input_drift": protected_input_drift,
        "structural_drift": sorted(structural_drift),
        "translation_mismatches": sorted(mismatches),
    }


def _protected_input_drift(
    baseline_payload: dict[str, object], candidate_payload: dict[str, object]
) -> list[str]:
    baseline_inputs = baseline_payload["inputs"]
    candidate_inputs = candidate_payload["inputs"]
    assert isinstance(baseline_inputs, dict) and isinstance(candidate_inputs, dict)
    return [
        path
        for path in INPUT_PATHS
        if path != QUOTES_ZH
        and _canonical_json(baseline_inputs.get(path))
        != _canonical_json(candidate_inputs.get(path))
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-ref", default="HEAD")
    parser.add_argument("--candidate-ref")
    parser.add_argument("--review-results", type=Path)
    parser.add_argument("--inventory-output", default="/tmp/quotes-inventory.json")
    args = parser.parse_args()
    try:
        baseline = resolve_commit(args.baseline_ref)
        payload = build_payload(baseline)
        candidate = resolve_commit(args.candidate_ref) if args.candidate_ref else None
        if args.review_results:
            review_input = (
                _load_git_review_input(candidate, args.review_results)
                if candidate
                else load_review_input(ROOT, args.review_results)
            )
            payload["review_input"] = review_input_metadata(review_input)
            payload["review_coverage"] = review_coverage(payload, review_input)
            if candidate:
                payload["candidate_agreement"] = candidate_agreement(
                    payload, review_input, candidate
                )
        elif candidate:
            raise RuntimeError("--candidate-ref requires --review-results")
        out = write_inventory_output(
            args.inventory_output,
            json.dumps(payload, ensure_ascii=False, indent=1),
        )
    except (OSError, RuntimeError, UnicodeError, ValueError) as error:
        print(f"ERROR: quotes inventory failed: {error}", file=sys.stderr)
        return 2

    print(f"quotes inventory sha256: {payload['inventory_sha256']}")
    print(
        "identities/direct/aliases: "
        f"{payload['identity_count']}/{payload['direct_quote_count']}/{payload['alias_count']}"
    )
    print(
        "EN/ZH differences: "
        f"{payload['english_minus_chinese']} / {payload['chinese_minus_english']}"
    )
    print(f"canonical order equal: {payload['canonical_order_equal']}")
    print(f"section assignments equal: {payload['section_assignments_equal']}")
    print(f"alias graph equal: {payload['alias_graph_equal']}")
    if "review_coverage" in payload:
        print("review coverage: " + _canonical_json(payload["review_coverage"]))
    if "candidate_agreement" in payload:
        print("candidate agreement: " + _canonical_json(payload["candidate_agreement"]))
    print(f"wrote {out}")

    structural_ok = (
        not payload["english_minus_chinese"]
        and not payload["chinese_minus_english"]
        and payload["canonical_order_equal"]
        and payload["section_assignments_equal"]
        and payload["alias_graph_equal"]
    )
    if not structural_ok:
        return 1
    if "review_coverage" in payload and not payload["review_coverage"]["coverage_equal"]:
        return 1
    if "candidate_agreement" in payload and not payload["candidate_agreement"]["candidate_agrees"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
