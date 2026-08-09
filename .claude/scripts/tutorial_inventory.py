#!/usr/bin/env python3
"""Deterministic production inventory for Issue #46 tutorial TextDB review.

The inventory is anchored to an exact Git commit.  Identities come from the
static producers used by the five tutorial vaults plus the two global C++/Lua
messages, independently of either the English or Chinese TextDB key set.
"""

from __future__ import annotations

import argparse
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
    generate_name_table,
    git_show_blob,
    merge_desc_sequence,
    parse_command_enum,
    parse_db_keys,
    resolve_commit,
    write_inventory_output,
)
from i18n_shared import (  # noqa: E402
    AuditInput,
    load_review_input,
    review_input_metadata,
)


TUTORIAL_EN = "crawl-ref/source/dat/descript/tutorial.txt"
TUTORIAL_ZH = "crawl-ref/source/dat/descript/zh/tutorial.txt"
TUTORIAL_LUA = "crawl-ref/source/dat/dlua/tutorial.lua"
TUTORIAL_CC = "crawl-ref/source/tutorial.cc"
HINTS_CC = "crawl-ref/source/hints.cc"
L_CRAWL_CC = "crawl-ref/source/l-crawl.cc"
COMMAND_TYPE_H = "crawl-ref/source/command-type.h"
GLOSSARY_MD = "docs/glossary.md"
LESSONS = tuple(
    f"crawl-ref/source/dat/des/tutorial/lesson{number}.des"
    for number in range(1, 6)
)

STRICT_REVIEW_BEGIN = "<!-- BEGIN STRICT TUTORIAL REVIEW EVIDENCE v1 -->"
STRICT_REVIEW_END = "<!-- END STRICT TUTORIAL REVIEW EVIDENCE v1 -->"
TERMINAL_CONCLUSIONS = {
    "keep",
    "adjust",
    "retranslate",
    "defer terminology",
    "defer implementation",
}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
STRICT_CARD_FIELDS = {
    "actual_behavior",
    "confidence",
    "consumer",
    "current_chinese",
    "current_english",
    "dependency_group",
    "display_context",
    "evidence_locations",
    "fact_sha256",
    "glossary_authority",
    "identity",
    "lifecycle",
    "producer",
    "production_facts",
    "proposed_translation",
    "reentry_trigger",
    "rejected_alternatives",
    "reviewer_rationale",
    "terminal_conclusion",
}

_LITERAL_LESSON_CALL_RE = re.compile(
    r"\btutorial([1-5])\.msg\(\s*\"([a-z0-9_]+)\"\s*\)"
)
_ANY_LESSON_CALL_RE = re.compile(r"\btutorial([1-5])\.msg\s*\(")
_DIRECT_CALL_RE = re.compile(
    r"\bcrawl\.tutorial_msg\(\s*\"([^\"\n]+)\""
)
_ANY_DIRECT_CALL_RE = re.compile(r"\bcrawl\.tutorial_msg\s*\(")
_CC_CALL_RE = re.compile(r"\btutorial_msg\(\s*\"([^\"\n]+)\"")
_COMMAND_RE = re.compile(r"\$cmd\[([A-Z][A-Z0-9_]*)\]")
_ANY_COMMAND_START_RE = re.compile(r"\$cmd\[")
_TAG_RE = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9_]*)>")
_TAG_LIKE_RE = re.compile(r"<[^>\n]*>")


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _assert_exact_wrapper(text: str, lesson: int, path: str) -> None:
    wrapper = re.compile(
        rf"function\s+tutorial{lesson}\.msg\(text\)\s*"
        rf"return\s+tutorial_msg\(\"tutorial{lesson} \"\s*\.\.\s*text\)\s*"
        rf"end"
    )
    if len(wrapper.findall(text)) != 1:
        raise RuntimeError(f"{path}: tutorial{lesson}.msg wrapper changed")


def extract_producers(blobs: dict[str, bytes]) -> tuple[list[str], dict[str, list[str]]]:
    """Extract every static production key and all of its source locations."""
    locations: dict[str, list[str]] = {}

    def add(key: str, path: str, text: str, offset: int) -> None:
        if not re.fullmatch(r"tutorial(?:[1-5] [a-z0-9_]+| (?:intro|death))", key):
            raise RuntimeError(f"{path}:{_line_number(text, offset)}: invalid tutorial key {key!r}")
        locations.setdefault(key, []).append(f"{path}:{_line_number(text, offset)}")

    for lesson, path in enumerate(LESSONS, start=1):
        text = blobs[path].decode("utf-8", errors="strict")
        _assert_exact_wrapper(text, lesson, path)
        literal_calls = list(_LITERAL_LESSON_CALL_RE.finditer(text))
        any_calls = list(_ANY_LESSON_CALL_RE.finditer(text))
        # The function definition itself is the sole non-call occurrence.
        if len(literal_calls) + 1 != len(any_calls):
            raise RuntimeError(f"{path}: non-literal or malformed tutorial{lesson}.msg call")
        for match in literal_calls:
            if int(match.group(1)) != lesson:
                raise RuntimeError(f"{path}:{_line_number(text, match.start())}: cross-lesson producer")
            add(f"tutorial{lesson} {match.group(2)}", path, text, match.start())

        direct_calls = list(_DIRECT_CALL_RE.finditer(text))
        any_direct = list(_ANY_DIRECT_CALL_RE.finditer(text))
        if len(direct_calls) != len(any_direct):
            raise RuntimeError(f"{path}: non-literal or malformed crawl.tutorial_msg call")
        for match in direct_calls:
            key = match.group(1)
            if not key.startswith(f"tutorial{lesson} "):
                raise RuntimeError(f"{path}:{_line_number(text, match.start())}: cross-lesson direct key")
            add(key, path, text, match.start())

    lua_text = blobs[TUTORIAL_LUA].decode("utf-8", errors="strict")
    lua_literals = list(_DIRECT_CALL_RE.finditer(lua_text))
    for match in lua_literals:
        add(match.group(1), TUTORIAL_LUA, lua_text, match.start())
    # The one dynamic call is the documented forwarding consumer for a key
    # already produced by lesson wrappers; no other dynamic producer is safe.
    dynamic = re.findall(r"crawl\.tutorial_msg\(\s*([^\"\s][^,)]*)", lua_text)
    if [value.strip() for value in dynamic] != ["data.text"]:
        raise RuntimeError(f"{TUTORIAL_LUA}: tutorial forwarding shape changed")

    cc_text = blobs[TUTORIAL_CC].decode("utf-8", errors="strict")
    cc_calls = list(_CC_CALL_RE.finditer(cc_text))
    if len(cc_calls) != 1:
        raise RuntimeError(f"{TUTORIAL_CC}: expected one literal tutorial_msg producer")
    add(cc_calls[0].group(1), TUTORIAL_CC, cc_text, cc_calls[0].start())

    ordered = sorted(locations, key=lambda key: (
        0 if key == "tutorial intro" else
        6 if key == "tutorial death" else int(key[len("tutorial")]),
        key,
    ))
    return ordered, {key: locations[key] for key in ordered}


def _token_facts(value: str, command_names: set[str]) -> dict[str, object]:
    commands = [match.group(1) for match in _COMMAND_RE.finditer(value)]
    malformed_commands = []
    if len(commands) != len(_ANY_COMMAND_START_RE.findall(value)):
        malformed_commands.append("unterminated or malformed $cmd token")
    unknown_commands = sorted(set(commands) - command_names)

    tag_tokens = [match.group(0) for match in _TAG_RE.finditer(value)]
    tag_like = _TAG_LIKE_RE.findall(value)
    normalized_tag_like = [
        token[token.rfind("</"):] if token.startswith("<<") and "</" in token else token
        for token in tag_like
    ]
    unknown_tag_syntax = sorted(set(normalized_tag_like) - set(tag_tokens))
    stack: list[str] = []
    tag_errors: list[str] = []
    for match in _TAG_RE.finditer(value):
        closing, name = match.groups()
        if not closing:
            stack.append(name)
        elif not stack or stack[-1] != name:
            tag_errors.append(f"unexpected </{name}>")
        else:
            stack.pop()
    tag_errors.extend(f"unclosed <{name}>" for name in reversed(stack))

    return {
        "commands": commands,
        "command_counts": dict(sorted(Counter(commands).items())),
        "malformed_commands": malformed_commands,
        "unknown_commands": unknown_commands,
        "tag_counts": dict(sorted(Counter(tag_tokens).items())),
        "tag_errors": tag_errors,
        "unknown_tag_syntax": unknown_tag_syntax,
        "nowrap_count": sum(1 for line in value.splitlines() if line == ":nowrap"),
    }


def _dependency_group(key: str) -> str:
    if key in {"tutorial intro", "tutorial death"} or key.endswith((" start", " exit", " tutorial_end")):
        return "entry, summary, and exit"
    suffix = key.split(" ", 1)[1]
    if any(word in suffix for word in ("move", "stairs", "map", "explor", "travel", "door", "water", "newlevel", "exclusion")):
        return "movement and exploration"
    if any(word in suffix for word in ("melee", "battle", "throw", "firing", "boomerang", "monster", "berserk")):
        return "combat and targeting"
    if any(word in suffix for word in ("spell", "magic", "meph", "cloud", "allies", "memorise")):
        return "magic and allies"
    if any(word in suffix for word in ("religion", "altar", "piety", "exhaustion", "dungeon_overview")):
        return "religion and progression"
    return "items, inventory, and shops"


def verify_consumers(blobs: dict[str, bytes]) -> None:
    """Bind the inventory to the production lookup and substitution chain."""
    required = {
        HINTS_CC: (
            "string text = getHintString(key);",
            "_replace_static_tags(text);",
            "text = untag_tiles_console(text);",
            'while ((p = text.find("$cmd[")) != string::npos)',
            "command_type cmd = name_to_command(command);",
            "command = command_to_string(cmd);",
        ),
        L_CRAWL_CC: (
            "static int crawl_tutorial_msg(lua_State *ls)",
            "tutorial_msg(key, lua_isboolean(ls, 2) && lua_toboolean(ls, 2));",
            '{ "tutorial_msg",       crawl_tutorial_msg },',
        ),
        TUTORIAL_LUA: (
            "crawl.tutorial_msg(data.text, data.exit)",
            "return function_at_spot('tutorial_messenger_db', data, true)",
        ),
    }
    for path, fragments in required.items():
        text = blobs[path].decode("utf-8", errors="strict")
        missing = [fragment for fragment in fragments if text.count(fragment) < 1]
        if missing:
            raise RuntimeError(f"{path}: tutorial consumer shape changed: {missing}")


def _fact_sha(row: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(
        row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def build_payload(baseline: str) -> dict[str, object]:
    paths = [
        TUTORIAL_EN, TUTORIAL_ZH, TUTORIAL_LUA, TUTORIAL_CC,
        HINTS_CC, L_CRAWL_CC, COMMAND_TYPE_H, GLOSSARY_MD, *LESSONS,
    ]
    blobs = {path: git_show_blob(baseline, path) for path in paths}
    return build_payload_from_blobs(baseline, blobs)


def build_payload_from_blobs(
    baseline: str, blobs: dict[str, bytes]
) -> dict[str, object]:
    """Build an inventory from an already frozen blob map (test seam)."""
    paths = [
        TUTORIAL_EN, TUTORIAL_ZH, TUTORIAL_LUA, TUTORIAL_CC,
        HINTS_CC, L_CRAWL_CC, COMMAND_TYPE_H, GLOSSARY_MD, *LESSONS,
    ]
    if set(blobs) != set(paths):
        missing = sorted(set(paths) - set(blobs))
        extra = sorted(set(blobs) - set(paths))
        raise RuntimeError(f"tutorial input manifest mismatch: missing={missing} extra={extra}")
    verify_consumers(blobs)
    producer_keys, producer_locations = extract_producers(blobs)

    en_entries = parse_db_keys(blobs[TUTORIAL_EN].decode("utf-8"), TUTORIAL_EN)
    zh_entries = parse_db_keys(blobs[TUTORIAL_ZH].decode("utf-8"), TUTORIAL_ZH)
    en_effective, en_overrides = merge_desc_sequence(en_entries)
    zh_effective, zh_overrides = merge_desc_sequence(zh_entries)
    en_keys = set(en_effective)
    zh_keys = set(zh_effective)
    producer_set = set(producer_keys)
    if len(producer_keys) != len(producer_set):
        raise RuntimeError("producer inventory contains duplicate identities")
    if en_overrides or zh_overrides:
        raise RuntimeError(f"tutorial TextDB overrides are forbidden: EN={en_overrides} ZH={zh_overrides}")

    command_enum = parse_command_enum(blobs[COMMAND_TYPE_H].decode("utf-8"))
    command_names = set(generate_name_table(command_enum).values())

    inventory = []
    for key in producer_keys:
        en = en_effective.get(key)
        zh = zh_effective.get(key)
        english = _desc_display(en.value) if en else None
        chinese = _desc_display(zh.value) if zh else None
        en_tokens = _token_facts(english or "", command_names)
        zh_tokens = _token_facts(chinese or "", command_names)
        token_failures = (
            en_tokens["malformed_commands"], zh_tokens["malformed_commands"],
            en_tokens["unknown_commands"], zh_tokens["unknown_commands"],
            en_tokens["unknown_tag_syntax"], zh_tokens["unknown_tag_syntax"],
        )
        if any(token_failures):
            raise RuntimeError(
                f"{key}: malformed or unknown tutorial token: {token_failures}"
            )
        mechanical = {
            "identity": f"tutorial:{key}",
            "key": key,
            "lifecycle": "current",
            "producer_locations": producer_locations[key],
            "english": english,
            "chinese": chinese,
            "english_key_line": en.key_line if en else None,
            "chinese_key_line": zh.key_line if zh else None,
            "english_tokens": en_tokens,
            "chinese_tokens": zh_tokens,
            "token_multiset_equal": {
                "commands": en_tokens["command_counts"] == zh_tokens["command_counts"],
                "tags": en_tokens["tag_counts"] == zh_tokens["tag_counts"],
                "nowrap": en_tokens["nowrap_count"] == zh_tokens["nowrap_count"],
            },
            "dependency_group": _dependency_group(key),
        }
        mechanical["fact_sha256"] = _fact_sha(mechanical)
        inventory.append(mechanical)

    payload: dict[str, object] = {
        "baseline": baseline,
        "glossary_sha256": hashlib.sha256(blobs[GLOSSARY_MD]).hexdigest(),
        "inputs": {
            path: {"sha256": hashlib.sha256(blobs[path]).hexdigest()}
            for path in paths
        },
        "producer_keys": producer_keys,
        "tutorial_en_keys": sorted(en_keys),
        "tutorial_zh_keys": sorted(zh_keys),
        "producer_minus_en": sorted(producer_set - en_keys),
        "en_minus_producer": sorted(en_keys - producer_set),
        "producer_minus_zh": sorted(producer_set - zh_keys),
        "zh_minus_producer": sorted(zh_keys - producer_set),
        "inventory": inventory,
    }
    payload["inventory_sha256"] = hashlib.sha256(json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    return payload


def _load_json(line: str, label: str) -> object:
    def reject_constant(value: str) -> object:
        raise ValueError(f"non-finite JSON value {value}")
    try:
        return json.loads(line, parse_constant=reject_constant)
    except (json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(f"invalid {label} JSON") from error


def load_git_review_input(commit: str, supplied: Path) -> AuditInput:
    """Load the review ledger from the exact candidate Git tree."""
    root = ROOT.resolve()
    if supplied.is_absolute():
        try:
            relative = supplied.resolve().relative_to(root)
        except (OSError, ValueError) as error:
            raise RuntimeError("review results path is outside the repository") from error
    else:
        relative = supplied
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise RuntimeError("review results path is not normalized")
    logical = relative.as_posix()
    data = git_show_blob(commit, logical)
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
        sha256=hashlib.sha256(data).hexdigest(),
    )


def parse_review(review_input: AuditInput) -> tuple[dict[str, object], list[dict[str, object]]]:
    text = review_input.text
    if text.count(STRICT_REVIEW_BEGIN) != 1 or text.count(STRICT_REVIEW_END) != 1:
        raise RuntimeError("strict tutorial review block is missing or duplicated")
    block = text.split(STRICT_REVIEW_BEGIN, 1)[1].split(STRICT_REVIEW_END, 1)[0]
    if not block.startswith("\n") or not block.endswith("\n"):
        raise RuntimeError("strict tutorial review framing is invalid")
    lines = block[1:-1].splitlines()
    if len(lines) < 4 or lines[1] != "```jsonl" or lines[-1] != "```":
        raise RuntimeError("strict tutorial review structure is invalid")
    metadata = _load_json(lines[0], "tutorial review metadata")
    expected_meta = {"baseline", "glossary_sha256", "identity_count", "inventory_sha256"}
    if not isinstance(metadata, dict) or set(metadata) != expected_meta:
        raise RuntimeError("strict tutorial review metadata fields are invalid")
    if lines[0] != json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")):
        raise RuntimeError("strict tutorial review metadata is not canonical JSON")
    cards = []
    for line in lines[2:-1]:
        card = _load_json(line, "tutorial review card")
        if not isinstance(card, dict) or set(card) != STRICT_CARD_FIELDS:
            raise RuntimeError("strict tutorial review card fields are invalid")
        if line != json.dumps(card, ensure_ascii=False, sort_keys=True, separators=(",", ":")):
            raise RuntimeError("strict tutorial review card is not canonical JSON")
        cards.append(card)
    return metadata, cards


def _mechanical_fields(row: dict[str, object]) -> dict[str, object]:
    return {
        "identity": row["identity"],
        "lifecycle": row["lifecycle"],
        "current_english": row["english"],
        "current_chinese": row["chinese"],
        "dependency_group": row["dependency_group"],
        "production_facts": row,
        "fact_sha256": row["fact_sha256"],
    }


def review_coverage(payload: dict[str, object], review_input: AuditInput) -> dict[str, object]:
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
                if json.dumps(card[field], ensure_ascii=False, sort_keys=True) != json.dumps(value, ensure_ascii=False, sort_keys=True):
                    mismatches.append(f"{identity}:{field}")
        conclusion = card["terminal_conclusion"]
        proposal = card["proposed_translation"]
        if conclusion not in TERMINAL_CONCLUSIONS:
            invalid.append(f"{identity}:terminal_conclusion")
        if conclusion in {"adjust", "retranslate"} and (not isinstance(proposal, str) or not proposal.strip() or proposal == card["current_chinese"]):
            invalid.append(f"{identity}:proposed_translation")
        if conclusion in {"keep", "defer terminology", "defer implementation"} and proposal is not None:
            invalid.append(f"{identity}:unexpected_proposal")
        for field in ("actual_behavior", "consumer", "display_context", "glossary_authority", "producer", "reviewer_rationale", "reentry_trigger"):
            if not isinstance(card[field], str) or not card[field].strip():
                invalid.append(f"{identity}:{field}")
        if card["confidence"] not in CONFIDENCE_LEVELS:
            invalid.append(f"{identity}:confidence")
        if not isinstance(card["evidence_locations"], list) or not card["evidence_locations"]:
            invalid.append(f"{identity}:evidence_locations")
        if not isinstance(card["rejected_alternatives"], list):
            invalid.append(f"{identity}:rejected_alternatives")

    binding = {
        "baseline": metadata.get("baseline") == payload["baseline"],
        "glossary_sha256": metadata.get("glossary_sha256") == payload["glossary_sha256"],
        "identity_count": metadata.get("identity_count") == len(inventory),
        "inventory_sha256": metadata.get("inventory_sha256") == payload["inventory_sha256"],
    }
    duplicates = sorted(key for key, count in Counter(review_ids).items() if count > 1)
    coverage_equal = (
        all(binding.values())
        and review_ids == inventory_ids
        and not duplicates
        and not mismatches
        and not invalid
    )
    return {
        **review_input_metadata(review_input),
        "evidence_card_count": len(cards),
        "terminal_conclusion_counts": dict(sorted(Counter(card["terminal_conclusion"] for card in cards).items())),
        "binding_matches": binding,
        "duplicate_evidence_cards": duplicates,
        "inventory_minus_review": sorted(set(inventory_ids) - set(review_ids)),
        "review_minus_inventory": sorted(set(review_ids) - set(inventory_ids)),
        "canonical_card_order": review_ids == inventory_ids,
        "mismatched_mechanical_fields": sorted(mismatches),
        "invalid_cards": sorted(invalid),
        "coverage_equal": coverage_equal,
    }


def candidate_agreement(
    payload: dict[str, object], review_input: AuditInput, candidate: str
) -> dict[str, object]:
    """Prove the exact candidate ZH values implement the confirmed ledger."""
    _metadata, cards = parse_review(review_input)
    candidate_entries, overrides = merge_desc_sequence(parse_db_keys(
        git_show_blob(candidate, TUTORIAL_ZH).decode("utf-8"), TUTORIAL_ZH
    ))
    if overrides:
        raise RuntimeError(f"candidate tutorial TextDB overrides are forbidden: {overrides}")
    inventory = payload["inventory"]
    assert isinstance(inventory, list)
    card_by_id = {card["identity"]: card for card in cards}
    mismatches = []
    for row in inventory:
        identity = row["identity"]
        card = card_by_id.get(identity)
        if card is None:
            mismatches.append(f"{identity}:missing_card")
            continue
        conclusion = card["terminal_conclusion"]
        expected = (
            card["proposed_translation"]
            if conclusion in {"adjust", "retranslate"}
            else card["current_chinese"]
        )
        entry = candidate_entries.get(row["key"])
        actual = _desc_display(entry.value) if entry else None
        if actual != expected:
            mismatches.append(identity)
    candidate_keys = set(candidate_entries)
    expected_keys = {row["key"] for row in inventory}
    return {
        "candidate": candidate,
        "candidate_minus_inventory": sorted(candidate_keys - expected_keys),
        "inventory_minus_candidate": sorted(expected_keys - candidate_keys),
        "translation_mismatches": sorted(mismatches),
        "candidate_agrees": (
            candidate_keys == expected_keys and not mismatches
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-ref", default="HEAD")
    parser.add_argument(
        "--candidate-ref",
        help="optional exact candidate commit whose ZH tutorial values must "
             "match each confirmed keep/adjust/retranslate decision",
    )
    parser.add_argument("--inventory-output", default="/tmp/tutorial-inventory.json")
    parser.add_argument("--review-results", type=Path)
    args = parser.parse_args()
    try:
        payload = build_payload(resolve_commit(args.baseline_ref))
        candidate = resolve_commit(args.candidate_ref) if args.candidate_ref else None
        if args.review_results:
            review_input = (
                load_git_review_input(candidate, args.review_results)
                if candidate else load_review_input(ROOT, args.review_results)
            )
            payload["review_input"] = review_input_metadata(review_input)
            payload["review_coverage"] = review_coverage(payload, review_input)
            if candidate:
                payload["candidate_agreement"] = candidate_agreement(
                    payload, review_input, candidate
                )
        elif args.candidate_ref:
            raise RuntimeError("--candidate-ref requires --review-results")
        out = write_inventory_output(
            args.inventory_output,
            json.dumps(payload, ensure_ascii=False, indent=1),
        )
    except (OSError, RuntimeError, UnicodeError, ValueError) as error:
        print(f"ERROR: tutorial inventory failed: {error}", file=sys.stderr)
        return 2

    inventory = payload["inventory"]
    assert isinstance(inventory, list)
    print(f"tutorial inventory sha256: {payload['inventory_sha256']}")
    print(f"producer identities: {len(payload['producer_keys'])}")
    print(f"EN/ZH identities: {len(payload['tutorial_en_keys'])}/{len(payload['tutorial_zh_keys'])}")
    print(f"producer/EN differences: {payload['producer_minus_en']} / {payload['en_minus_producer']}")
    print(f"producer/ZH differences: {payload['producer_minus_zh']} / {payload['zh_minus_producer']}")
    structural = [row["identity"] for row in inventory if (
        row["english_tokens"]["tag_errors"]
        or row["chinese_tokens"]["tag_errors"]
        or not all(row["token_multiset_equal"].values())
    )]
    print(f"structural review candidates: {structural}")
    if "review_coverage" in payload:
        print("review coverage: " + json.dumps(payload["review_coverage"], ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    if "candidate_agreement" in payload:
        print("candidate agreement: " + json.dumps(payload["candidate_agreement"], ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    print(f"wrote {out}")
    if any((payload["producer_minus_en"], payload["en_minus_producer"], payload["producer_minus_zh"], payload["zh_minus_producer"])):
        return 1
    if "review_coverage" in payload and not payload["review_coverage"]["coverage_equal"]:
        return 1
    if "candidate_agreement" in payload and not payload["candidate_agreement"]["candidate_agrees"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
