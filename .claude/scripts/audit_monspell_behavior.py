#!/usr/bin/env python3
"""Sound Phase-1 audit of behavior-bearing runtime monspell candidates.

This consumes the production C++ candidate upper-bound artifact, production
SpeakDB dumps, the Phase-0 inventory, and the production overlay manifest. It
deliberately does not parse TextDB source.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import heapq
import itertools
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

from audit_monspell_phase0 import (
    ArtifactError,
    MAX_RECURSION_DEPTH,
    MAX_REPLACEMENTS,
    _reachable_variants,
    load_artifact,
    textdb_marker_sites,
)
from generate_message_overlay import ManifestError, validate_manifest


SCHEMA_VERSION = 1
GESTURE_NEEDLES = ("Gesture", " gesture", "Point", " point", "手势", "指向")
PRE_BEHAVIORS = {
    "GESTURE": GESTURE_NEEDLES,
    "VISUAL_APPLICABILITY": ("VISUAL",),
}
VISUAL_PREFIX = "VISUAL"
SOUND_LIKE_PREFIXES = frozenset({"WARN", "SOUND", "SPELL", "ENCHANT"})
KNOWN_PREFIXES = SOUND_LIKE_PREFIXES | frozenset({
    "VISUAL", "VISUAL WARN", "VISUAL SPELL", "VISUAL ENCHANT",
})
MAX_EDGE = 64
MAX_PRE_EDGE = max(len(needle) for needles in PRE_BEHAVIORS.values()
                   for needle in needles) - 1
MAX_SUMMARIES = 4096
NON_CONTROL_FRAGMENT = "\0"
DYNAMIC_FRAGMENT = "\1"
_DYNAMIC_PREFIX_RE = re.compile(r"(?:@[^@]+@|\[[^]]+\]|\{\{.*?\}\})", re.DOTALL)
_STATIC_CONTROL_RE = re.compile(r"[A-Z][A-Z0-9_ ]*")
SYMBOL_MARKER = "${beam_short_name}"
ALLOWED_ATTEMPTS = frozenset({
    "normal", "unseen", "silent_prefixed", "silent_unprefixed_fallback",
})
CANDIDATE_TOP_LEVEL_KEYS = {
    "schema_version", "domain", "completeness", "valid", "diagnostic",
    "input_domain", "counts", "scenarios", "base_expressions",
    "lookup_expressions",
}
CANDIDATE_COUNT_KEYS = {
    "monster_types", "spells", "monster_tuples", "monster_spell_tuples",
    "scenarios", "base_expressions", "lookup_expressions", "lookup_attempts",
}
CANDIDATE_ANCHOR_KEYS = {
    "schema_version", "domain", "artifact_sha256", "counts",
    "producer_contract",
}
CANDIDATE_INPUT_KEYS = {
    "monster_types", "monster_fragments", "spells", "scenarios",
    "beam_short_name", "lookup_state_machine",
}
CANDIDATE_SCENARIO_KEYS = {
    "id", "category_bits", "humanoid", "at_least_human_intelligence",
    "hoarfrost_finale", "targeted", "visible_beam",
}
CANDIDATE_INPUT_DOMAIN = {
    "monster_types": (
        "integer range [0,NUM_MONSTERS) with "
        "get_monster_data(type) != nullptr"
    ),
    "monster_fragments": (
        "unique canonical-English type/species/genus tuples"
    ),
    "spells": (
        "all is_valid_spell(spell) values in [0,NUM_SPELLS), "
        "deduplicated by spell_english_name"
    ),
    "scenarios": (
        "finite branch cover proven exhaustive over 32 category masks "
        "and all recipe booleans"
    ),
    "beam_short_name": (
        "symbolic ${beam_short_name}; runtime materialization excluded"
    ),
    "lookup_state_machine": (
        "search_message_candidate recorder, then production lowercase "
        "canonicalization, for normal, unseen, silent-prefixed and "
        "silent-unprefixed fallback"
    ),
}
EXPECTED_CANDIDATE_SCENARIOS = (
    {
        "id": "none_humanoid_maximal",
        "category_bits": 0,
        "humanoid": True,
        "at_least_human_intelligence": True,
        "hoarfrost_finale": True,
        "targeted": True,
        "visible_beam": True,
    },
    {
        "id": "wizard_humanoid_maximal",
        "category_bits": 8,
        "humanoid": True,
        "at_least_human_intelligence": True,
        "hoarfrost_finale": True,
        "targeted": True,
        "visible_beam": True,
    },
    {
        "id": "priest_humanoid_maximal",
        "category_bits": 16,
        "humanoid": True,
        "at_least_human_intelligence": True,
        "hoarfrost_finale": True,
        "targeted": True,
        "visible_beam": True,
    },
    {
        "id": "magical_humanoid_maximal",
        "category_bits": 2,
        "humanoid": True,
        "at_least_human_intelligence": True,
        "hoarfrost_finale": True,
        "targeted": True,
        "visible_beam": True,
    },
    {
        "id": "natural_humanoid_maximal",
        "category_bits": 1,
        "humanoid": True,
        "at_least_human_intelligence": True,
        "hoarfrost_finale": True,
        "targeted": True,
        "visible_beam": True,
    },
    {
        "id": "wizard_non_humanoid_maximal",
        "category_bits": 8,
        "humanoid": False,
        "at_least_human_intelligence": True,
        "hoarfrost_finale": True,
        "targeted": True,
        "visible_beam": True,
    },
)
CANDIDATE_PRODUCER_CONTRACT = (
    "production scenario_cover + mon_cast_message_keys::build_key_recipe "
    "+ search_message_candidate recorder"
)


class AuditError(ValueError):
    pass


class Unanalysable(AuditError):
    pass


@dataclass(frozen=True)
class CandidateArtifact:
    schema_version: int
    completeness: str
    counts: dict[str, int]
    lookup_expressions: list[dict[str, Any]]


@dataclass(frozen=True)
class CandidateAnchor:
    artifact_sha256: str
    counts: dict[str, int]


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise AuditError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditError(f"{path} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError as exc:
        raise AuditError(f"cannot hash {path}: {exc}") from exc


def _render(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def _validate_symbol_expression(expression: str, context: str) -> None:
    count = expression.count(SYMBOL_MARKER)
    _require(count <= 1, f"{context} contains duplicate {SYMBOL_MARKER}")
    without_symbol = expression.replace(SYMBOL_MARKER, "")
    _require("${" not in without_symbol and "$" not in without_symbol
             and "{" not in without_symbol and "}" not in without_symbol,
             f"{context} contains an invalid symbolic marker")


def _expected_lookup_records(
    normalized_bases: list[str],
) -> Iterable[tuple[str, tuple[str, ...]]]:
    streams = (
        ((base, ("normal", "silent_unprefixed_fallback"))
         for base in normalized_bases),
        (("silent " + base, ("silent_prefixed",))
         for base in normalized_bases),
        (("unseen " + base, ("unseen",))
         for base in normalized_bases),
    )
    merged = heapq.merge(*streams, key=lambda item: item[0])
    for expression, grouped in itertools.groupby(
            merged, key=lambda item: item[0]):
        attempts = sorted({
            attempt
            for _, item_attempts in grouped
            for attempt in item_attempts
        })
        yield expression, tuple(attempts)


def load_candidate_anchor(path: Path) -> CandidateAnchor:
    anchor = _read_json(path)
    _require(set(anchor) == CANDIDATE_ANCHOR_KEYS,
             "candidate anchor has unknown or missing fields")
    _require(anchor["schema_version"] == 1,
             "candidate anchor schema_version must be 1")
    _require(anchor["domain"] == "monspell_candidate_lookup",
             "candidate anchor domain mismatch")
    digest = anchor["artifact_sha256"]
    _require(isinstance(digest, str)
             and re.fullmatch(r"[0-9a-f]{64}", digest) is not None,
             "candidate anchor artifact_sha256 is invalid")
    counts = anchor["counts"]
    _require(isinstance(counts, dict) and set(counts) == CANDIDATE_COUNT_KEYS
             and all(_is_int(value) and value > 0 for value in counts.values()),
             "candidate anchor counts are invalid")
    _require(anchor["producer_contract"] == CANDIDATE_PRODUCER_CONTRACT,
             "candidate anchor producer_contract mismatch")
    return CandidateAnchor(artifact_sha256=digest, counts=dict(counts))


def load_candidate_artifact(path: Path) -> CandidateArtifact:
    artifact = _read_json(path)
    _require(set(artifact) == CANDIDATE_TOP_LEVEL_KEYS,
             "candidate artifact has unknown or missing top-level fields")
    _require(artifact["schema_version"] == 1,
             "candidate artifact schema_version must be 1")
    _require(artifact["domain"] == "monspell_candidate_lookup",
             "candidate artifact domain mismatch")
    _require(artifact["completeness"] == "closed_world_upper_bound",
             "candidate artifact completeness mismatch")
    _require(artifact["valid"] is True and artifact["diagnostic"] is None,
             "candidate artifact is not valid")

    input_domain = artifact["input_domain"]
    _require(isinstance(input_domain, dict)
             and set(input_domain) == CANDIDATE_INPUT_KEYS,
             "candidate artifact input_domain fields are invalid")
    _require(input_domain == CANDIDATE_INPUT_DOMAIN,
             "candidate artifact input_domain contract mismatch")
    counts = artifact["counts"]
    _require(isinstance(counts, dict) and set(counts) == CANDIDATE_COUNT_KEYS
             and all(_is_int(value) and value >= 0 for value in counts.values()),
             "candidate artifact counts are invalid")
    _require(all(counts[key] > 0 for key in CANDIDATE_COUNT_KEYS),
             "candidate artifact counts must all be positive")
    _require(counts["monster_spell_tuples"]
             == counts["monster_tuples"] * counts["spells"],
             "candidate monster/spell tuple count mismatch")

    scenarios = artifact["scenarios"]
    _require(isinstance(scenarios, list)
             and len(scenarios) == counts["scenarios"],
             "candidate scenario count mismatch")
    for index, scenario in enumerate(scenarios):
        context = f"candidate scenarios[{index}]"
        _require(isinstance(scenario, dict)
                 and set(scenario) == CANDIDATE_SCENARIO_KEYS,
                 f"{context} fields are invalid")
        _require(_is_int(scenario["category_bits"])
                 and scenario["category_bits"] >= 0
                 and all(isinstance(scenario[field], bool)
                         for field in CANDIDATE_SCENARIO_KEYS
                         - {"id", "category_bits"}),
                 f"{context} values are invalid")
    _require(scenarios == list(EXPECTED_CANDIDATE_SCENARIOS),
             "candidate scenarios do not match production scenario_cover()")

    base = artifact["base_expressions"]
    _require(isinstance(base, list) and len(base) == counts["base_expressions"],
             "candidate base expression count mismatch")
    previous_expression: str | None = None
    for index, expression in enumerate(base):
        context = f"candidate base_expressions[{index}]"
        _require(isinstance(expression, str) and expression
                 and expression.isascii(),
                 f"{context} must be non-empty canonical English ASCII")
        _require(previous_expression is None or previous_expression < expression,
                 "candidate base expressions must be strictly sorted and unique")
        _validate_symbol_expression(expression, context)
        previous_expression = expression
    normalized_bases = sorted(expression.lower() for expression in base)
    normalized_bases = [
        expression
        for expression, _ in itertools.groupby(normalized_bases)
    ]

    lookup = artifact["lookup_expressions"]
    _require(isinstance(lookup, list)
             and len(lookup) == counts["lookup_expressions"],
             "candidate lookup expression count mismatch")
    previous_expression = None
    attempt_count = 0
    for index, record in enumerate(lookup):
        context = f"candidate lookup_expressions[{index}]"
        _require(isinstance(record, dict)
                 and set(record) == {"expression", "attempts"},
                 f"{context} fields are invalid")
        expression = record["expression"]
        attempts = record["attempts"]
        _require(isinstance(expression, str) and expression
                 and expression.isascii()
                 and expression == expression.lower(),
                 f"{context}.expression is not production lowercase")
        _require(previous_expression is None or previous_expression < expression,
                 "candidate lookup expressions must be strictly sorted and unique")
        _validate_symbol_expression(expression, f"{context}.expression")
        _require(isinstance(attempts, list) and attempts
                 and all(isinstance(attempt, str)
                         and attempt in ALLOWED_ATTEMPTS for attempt in attempts)
                 and all(left < right
                         for left, right in zip(attempts, attempts[1:])),
                 f"{context}.attempts must be strictly sorted, unique, and known")
        attempt_count += len(attempts)
        previous_expression = expression
    _require(attempt_count == counts["lookup_attempts"],
             "candidate lookup attempt count mismatch")
    expected = _expected_lookup_records(normalized_bases)
    for index, pair in enumerate(itertools.zip_longest(lookup, expected)):
        record, expected_record = pair
        _require(record is not None,
                 "candidate lookup closure is truncated")
        _require(expected_record is not None,
                 "candidate lookup closure contains an extra expression")
        expected_expression, expected_attempts = expected_record
        _require(
            record["expression"] == expected_expression
            and tuple(record["attempts"]) == expected_attempts,
            f"candidate lookup closure mismatch at index {index}",
        )
    return CandidateArtifact(
        schema_version=artifact["schema_version"],
        completeness=artifact["completeness"],
        counts=dict(counts),
        lookup_expressions=lookup,
    )


def _clip_head(text: str) -> str:
    return text[:MAX_EDGE]


def _clip_pre_head(text: str) -> str:
    return text[:MAX_PRE_EDGE]


def _clip_pre_tail(text: str) -> str:
    return text[-MAX_PRE_EDGE:]


def _marker_parts(text: str) -> Iterable[tuple[str, str]]:
    """Yield (kind, value), mirroring runtime left-to-right @ pairing."""
    position = 0
    while True:
        begin = text.find("@", position)
        if begin < 0:
            if position < len(text):
                yield "literal", text[position:]
            return
        end = text.find("@", begin + 1)
        if end < 0:
            yield "literal", text[position:]
            return
        if begin > position:
            yield "literal", text[position:begin]
        yield "marker", text[begin + 1:end]
        position = end + 1


def _random_parts(text: str) -> Iterable[tuple[str, tuple[str, ...]]]:
    """Yield literals and legacy `[a|b]` options in runtime scan order."""
    position = 0
    while True:
        begin = text.find("[", position)
        if begin < 0:
            if position < len(text):
                yield "literal", (text[position:],)
            return
        end = text.find("]", begin + 1)
        if end < 0:
            yield "literal", (text[position:],)
            return
        if begin > position:
            yield "literal", (text[position:begin],)
        yield "choice", tuple(text[begin + 1:end].split("|"))
        position = end + 1


@dataclass(frozen=True)
class PreSummary:
    head: str
    tail: str
    behaviors: frozenset[str]


def _pre_literal(text: str) -> PreSummary:
    found = frozenset(
        behavior for behavior, needles in PRE_BEHAVIORS.items()
        if any(needle in text for needle in needles)
    )
    return PreSummary(_clip_pre_head(text), _clip_pre_tail(text), found)


def _pre_concat(left: PreSummary, right: PreSummary) -> PreSummary:
    boundary = left.tail + right.head
    found = set(left.behaviors | right.behaviors)
    for behavior, needles in PRE_BEHAVIORS.items():
        if any(needle in boundary for needle in needles):
            found.add(behavior)
    return PreSummary(
        _clip_pre_head(left.head + right.head),
        _clip_pre_tail(left.tail + right.tail),
        frozenset(found),
    )


def _line_effect(line: str) -> tuple[frozenset[str], bool]:
    if line == NON_CONTROL_FRAGMENT:
        return frozenset(), False
    if ":" not in line:
        return frozenset(), False
    prefix = line.split(":", 1)[0]
    if prefix == VISUAL_PREFIX:
        return frozenset({"VISUAL_CHANNEL"}), False
    if prefix in SOUND_LIKE_PREFIXES:
        return frozenset({"SOUND_LIKE_CHANNEL"}), False
    if prefix in KNOWN_PREFIXES:
        return frozenset(), False
    dynamic = DYNAMIC_FRAGMENT in prefix or bool(_DYNAMIC_PREFIX_RE.search(prefix)) \
        or "[" in prefix or "]" in prefix or "{{" in prefix or "}}" in prefix
    unknown_static = bool(_STATIC_CONTROL_RE.fullmatch(prefix))
    return frozenset(), dynamic or unknown_static


def _line_fragment(text: str) -> str:
    """Retain only the portion that can still determine a line channel."""
    if text in {NON_CONTROL_FRAGMENT, DYNAMIC_FRAGMENT}:
        return text
    colon = text.find(":")
    dynamic = bool(_DYNAMIC_PREFIX_RE.search(text)) \
        or "[" in text or "]" in text or "{{" in text or "}}" in text
    if dynamic:
        return DYNAMIC_FRAGMENT + (":" if colon >= 0 else "")
    if 0 <= colon < MAX_EDGE:
        return text[:colon + 1]
    if text and not ("A" <= text[0] <= "Z") \
            and text[0] not in "@[{":
        return NON_CONTROL_FRAGMENT
    return _clip_head(text)


def _append_line_fragment(left: str, right: str) -> str:
    if left == NON_CONTROL_FRAGMENT or ":" in left or len(left) >= MAX_EDGE:
        return left
    if left == DYNAMIC_FRAGMENT:
        return DYNAMIC_FRAGMENT + (":" if ":" in right else "")
    return _line_fragment(left + right)


@dataclass(frozen=True)
class PostSummary:
    first: str
    last: str
    multiline: bool
    behaviors: frozenset[str]
    unknown_prefix: bool

    def completed(self) -> "PostSummary":
        behaviors = set(self.behaviors)
        unknown = self.unknown_prefix
        edge_lines = (self.first, self.last) if self.multiline else (self.first,)
        for line in edge_lines:
            effect, bad = _line_effect(line)
            behaviors.update(effect)
            unknown = unknown or bad
        return PostSummary(self.first, self.last, self.multiline,
                           frozenset(behaviors), unknown)


def _post_literal(text: str) -> PostSummary:
    lines = text.split("\n")
    behaviors: set[str] = set()
    unknown = False
    for line in lines[1:-1]:
        effect, bad = _line_effect(line)
        behaviors.update(effect)
        unknown = unknown or bad
    return PostSummary(
        _line_fragment(lines[0]), _line_fragment(lines[-1]), len(lines) > 1,
        frozenset(behaviors), unknown,
    )


def _post_concat(left: PostSummary, right: PostSummary) -> PostSummary:
    behaviors = set(left.behaviors | right.behaviors)
    unknown = left.unknown_prefix or right.unknown_prefix
    boundary = _append_line_fragment(left.last, right.first)
    if left.multiline and right.multiline:
        effect, bad = _line_effect(boundary)
        behaviors.update(effect)
        unknown = unknown or bad
    first = left.first if left.multiline \
        else _append_line_fragment(left.first, right.first)
    last = right.last if right.multiline \
        else _append_line_fragment(left.last, right.last)
    return PostSummary(first, last, left.multiline or right.multiline,
                       frozenset(behaviors), unknown)


def _bounded(values: set[Any], context: str) -> set[Any]:
    if len(values) > MAX_SUMMARIES:
        raise Unanalysable(f"{context}: symbolic state limit exceeded")
    return values


def _product(left: set[Any], right: set[Any], concat, context: str) -> set[Any]:
    return _bounded({concat(a, b) for a in left for b in right}, context)


@dataclass(frozen=True)
class EffectiveEntry:
    key: str
    variants: tuple[dict[str, Any], ...]
    source_language: str
    fallback_to_english: bool
    parse_error: str | None
    had_parsed_variants: bool
    effective_source: str
    effective_nonempty: bool


def _entry_index(artifact: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["canonical_key"]: entry for entry in artifact["entries"]}


def effective_entries(
    en_artifact: dict[str, Any], localized_artifact: dict[str, Any] | None,
    language: str,
) -> dict[str, EffectiveEntry]:
    en = _entry_index(en_artifact)
    localized = _entry_index(localized_artifact) if localized_artifact else {}
    result: dict[str, EffectiveEntry] = {}
    for key in sorted(set(en) | set(localized)):
        local = localized.get(key)
        base = en.get(key)
        chosen = local
        fallback = False
        if chosen is None or chosen.get("body_empty"):
            chosen = base
            fallback = local is not None or language != "en"
        if chosen is None:
            continue
        result[key] = EffectiveEntry(
            key=key,
            variants=tuple(_reachable_variants(chosen)),
            source_language=(language if chosen is local else "en"),
            fallback_to_english=fallback and chosen is base,
            parse_error=chosen.get("parse_error"),
            had_parsed_variants=bool(chosen["variants"]),
            effective_source=chosen["effective_provenance"]["source_name"],
            effective_nonempty=not chosen["body_empty"],
        )
    return result


def _normalized_source(source: str, language: str) -> str:
    localized_prefix = f"database/{language}/"
    if language != "en" and source.startswith(localized_prefix):
        return "database/" + source[len(localized_prefix):]
    return source


def candidate_hits(candidate: CandidateArtifact,
                   entries: dict[str, EffectiveEntry],
                   language: str) -> dict[str, Any]:
    key_index = {
        key: entry for key, entry in entries.items() if entry.effective_nonempty
    }
    sorted_keys = sorted(key_index)
    attempts_by_key: dict[str, set[str]] = {}
    symbol_matches: list[dict[str, object]] = []
    for record in candidate.lookup_expressions:
        expression = record["expression"]
        attempts = record["attempts"]
        if SYMBOL_MARKER not in expression:
            matches = (expression,) if expression in key_index else ()
        else:
            prefix, suffix = expression.split(SYMBOL_MARKER)
            matches = tuple(
                key for key in sorted_keys
                if key.startswith(prefix) and key.endswith(suffix)
                and len(key) >= len(prefix) + len(suffix)
            )
            if matches:
                symbol_matches.append({
                    "expression": expression,
                    "matched_keys": list(matches),
                    "attempts": list(attempts),
                })
        for key in matches:
            attempts_by_key.setdefault(key, set()).update(attempts)

    hits = []
    source_counts: Counter[str] = Counter()
    cross_domain = []
    for key in sorted(attempts_by_key):
        entry = key_index[key]
        source = _normalized_source(entry.effective_source, language)
        source_counts[source] += 1
        hit = {
            "canonical_key": key,
            "source": source,
            "effective_source": entry.effective_source,
            "attempts": sorted(attempts_by_key[key]),
        }
        hits.append(hit)
        if source != "database/monspell.txt":
            cross_domain.append(hit)
    return {
        "hit_count": len(hits),
        "hits": hits,
        "source_counts": dict(sorted(source_counts.items())),
        "cross_domain_hits": cross_domain,
        "symbol_matches": symbol_matches,
        "symbol_match_key_count": len({
            key for record in symbol_matches for key in record["matched_keys"]
        }),
    }


class PredicateAnalyzer:
    def __init__(self, entries: dict[str, EffectiveEntry], language: str):
        self.entries = entries
        self.language = language
        self._pre_cache: dict[tuple[str, int], set[PreSummary]] = {}
        self._post_cache: dict[tuple[str, int], set[PostSummary]] = {}

    def _variant(self, key: str, ordinal: int) -> dict[str, Any]:
        entry = self.entries.get(key)
        if entry is None or entry.parse_error is not None:
            raise Unanalysable(f"{key}: missing or corrupt recursive entry")
        if not entry.variants:
            raise Unanalysable(f"{key}: no selectable variants")
        for variant in entry.variants:
            if variant["locator"]["variant_ordinal"] == ordinal:
                return variant
        raise Unanalysable(f"{key}:{ordinal}: unreachable or missing variant")

    def _ordinals(self, key: str) -> list[int]:
        entry = self.entries.get(key)
        if entry is None or entry.parse_error is not None:
            return []
        if entry.had_parsed_variants and not entry.variants:
            raise Unanalysable(f"{key}: total selectable weight is not positive")
        return [variant["locator"]["variant_ordinal"] for variant in entry.variants]

    @staticmethod
    def _checked_markers(text: str, key: str, ordinal: int) -> list[dict[str, object]]:
        markers, unbalanced = textdb_marker_sites(text)
        if unbalanced is not None:
            raise Unanalysable(
                f"{key}:{ordinal}: unbalanced @ marker at offset {unbalanced}")
        return markers

    @staticmethod
    def _check_lua(text: str, key: str, ordinal: int) -> None:
        if "{{" in text or "}}" in text:
            raise Unanalysable(f"{key}:{ordinal}: embedded Lua")

    def validate_limits(self, key: str, ordinal: int) -> None:
        memo: dict[tuple[str, int], tuple[int, int]] = {}

        def limits(current_key: str, current_ordinal: int,
                   stack: tuple[tuple[str, int], ...]) -> tuple[int, int]:
            locator = (current_key, current_ordinal)
            if locator in stack:
                raise Unanalysable(f"{key}:{ordinal}: recursive cycle")
            if locator in memo:
                return memo[locator]
            variant = self._variant(current_key, current_ordinal)
            text = variant["raw_pattern"]
            self._check_lua(text, current_key, current_ordinal)
            markers = self._checked_markers(text, current_key, current_ordinal)
            depth = 1
            replacements = len(markers)
            for marker in markers:
                child_key = str(marker["canonical_key"])
                child_ordinals = self._ordinals(child_key)
                if not child_ordinals:
                    child = self.entries.get(child_key)
                    if child and child.parse_error is not None:
                        raise Unanalysable(f"{child_key}: corrupt recursive entry")
                    # Production enters `_getRandomisedStr()` for every paired
                    # marker before it can discover that the child key is
                    # missing.  The failed lookup is therefore one recursive
                    # leaf call.  It consumes no additional replacement beyond
                    # the marker already counted in `len(markers)`.
                    depth = max(depth, 2)
                    continue
                child_limits = [
                    limits(child_key, child_ordinal, stack + (locator,))
                    for child_ordinal in child_ordinals
                ]
                depth = max(depth, 1 + max(item[0] for item in child_limits))
                replacements += max(item[1] for item in child_limits)
            memo[locator] = depth, replacements
            return memo[locator]

        depth, replacements = limits(key, ordinal, ())
        if depth > MAX_RECURSION_DEPTH:
            raise Unanalysable(
                f"{key}:{ordinal}: can exceed recursion depth {MAX_RECURSION_DEPTH}")
        if replacements > MAX_REPLACEMENTS:
            raise Unanalysable(
                f"{key}:{ordinal}: can exceed replacement limit {MAX_REPLACEMENTS}")

    def pre_variant(self, key: str, ordinal: int,
                    stack: tuple[tuple[str, int], ...] = ()) -> set[PreSummary]:
        locator = (key, ordinal)
        if locator in stack:
            raise Unanalysable(f"{key}:{ordinal}: recursive cycle")
        if locator in self._pre_cache:
            return self._pre_cache[locator]
        text = self._variant(key, ordinal)["raw_pattern"]
        self._check_lua(text, key, ordinal)
        self._checked_markers(text, key, ordinal)
        result = {_pre_literal("")}
        for kind, value in _marker_parts(text):
            if kind == "literal":
                part = {_pre_literal(value)}
            else:
                child_key = value.lower()
                child = self.entries.get(child_key)
                if child and child.variants and child.parse_error is None:
                    part = set()
                    for child_ordinal in self._ordinals(child_key):
                        part.update(self.pre_variant(
                            child_key, child_ordinal, stack + (locator,)))
                elif child and child.parse_error is not None:
                    raise Unanalysable(f"{child_key}: corrupt recursive entry")
                else:
                    part = {_pre_literal(f"@{value}@")}
            result = _product(result, part, _pre_concat,
                              f"{key}:{ordinal} pre-binding")
        self._pre_cache[locator] = result
        return result

    def post_variant(self, key: str, ordinal: int,
                     stack: tuple[tuple[str, int], ...] = ()) -> set[PostSummary]:
        locator = (key, ordinal)
        if locator in stack:
            raise Unanalysable(f"{key}:{ordinal}: recursive cycle")
        if locator in self._post_cache:
            return self._post_cache[locator]
        text = self._variant(key, ordinal)["raw_pattern"]
        self._check_lua(text, key, ordinal)
        self._checked_markers(text, key, ordinal)
        result = {_post_literal("")}
        for kind, value in _marker_parts(text):
            if kind == "marker":
                child_key = value.lower()
                child = self.entries.get(child_key)
                if child and child.variants and child.parse_error is None:
                    part: set[PostSummary] = set()
                    for child_ordinal in self._ordinals(child_key):
                        part.update(self.post_variant(
                            child_key, child_ordinal, stack + (locator,)))
                elif child and child.parse_error is not None:
                    raise Unanalysable(f"{child_key}: corrupt recursive entry")
                else:
                    part = {_post_literal(f"@{value}@")}
            else:
                part = {_post_literal("")}
                for random_kind, options in _random_parts(value):
                    if random_kind == "choice" and any(
                            "[" in option or "]" in option for option in options):
                        raise Unanalysable(
                            f"{key}:{ordinal}: random replacement can create a new bracket site")
                    choices = (_post_literal(options[0]),) if random_kind == "literal" \
                        else tuple(_post_literal(option) for option in options)
                    part = _product(part, set(choices), _post_concat,
                                    f"{key}:{ordinal} random materialization")
            result = _product(result, part, _post_concat,
                              f"{key}:{ordinal} post-materialization")
        self._post_cache[locator] = result
        return result

    def provenance(self, key: str, ordinal: int) -> list[dict[str, object]]:
        found: set[tuple[str, int]] = set()

        def visit(current_key: str, current_ordinal: int,
                  stack: tuple[tuple[str, int], ...]) -> None:
            locator = (current_key, current_ordinal)
            if locator in stack or locator in found:
                return
            found.add(locator)
            variant = self._variant(current_key, current_ordinal)
            self._checked_markers(variant["raw_pattern"],
                                  current_key, current_ordinal)
            for kind, value in _marker_parts(variant["raw_pattern"]):
                if kind != "marker":
                    continue
                child_key = value.lower()
                child = self.entries.get(child_key)
                if child and child.variants and child.parse_error is None:
                    for child_ordinal in self._ordinals(child_key):
                        visit(child_key, child_ordinal, stack + (locator,))

        visit(key, ordinal, ())
        found.discard((key, ordinal))
        return [
            {"canonical_key": child_key, "variant_ordinal": child_ordinal}
            for child_key, child_ordinal in sorted(found)
        ]


def _catalog_index(manifest: dict[str, Any]) -> dict[tuple[str, int], dict[str, Any]]:
    result = {}
    for entry in manifest["entries"]:
        for variant in entry["variants"]:
            if not variant.get("tombstone"):
                indexed = dict(variant)
                indexed["_entry_mode"] = entry["mode"]
                result[(entry["canonical_key"], variant["variant_ordinal"])] = indexed
    return result


def _catalog_coverage(catalog: dict[tuple[str, int], dict[str, Any]],
                      key: str, ordinal: int, behavior: str) -> dict[str, object]:
    variant = catalog.get((key, ordinal))
    if not variant or variant.get("_entry_mode") == "LEGACY_ONLY":
        return {"covered": False, "stable_id": None}
    lines = list(variant.get("line_metadata", []))
    for case in variant.get("materialization_cases", []):
        lines.extend(case.get("line_metadata", []))
    covered = False
    if behavior == "GESTURE":
        covered = bool(lines) and all(
            line.get("behavior", {}).get("implies_gesture") is True for line in lines)
    elif behavior in {"VISUAL_APPLICABILITY", "VISUAL_CHANNEL"}:
        covered = bool(lines) and all(line.get("sensory") == "VISUAL" for line in lines)
    elif behavior == "SOUND_LIKE_CHANNEL":
        covered = bool(lines) and all(line.get("sensory") == "SOUND" for line in lines)
    return {"covered": covered, "stable_id": variant.get("stable_id")}


def _occurrence(key: str, language: str, ordinal: int,
                provenance: list[dict[str, object]], phase: str,
                behavior: str, catalog: dict[tuple[str, int], dict[str, Any]],
                detail: str | None = None) -> dict[str, object]:
    effects = {
        "GESTURE": "legacy target resolution receives gestured=true",
        "VISUAL_APPLICABILITY": "legacy unseen applicability rejects the candidate",
        "VISUAL_CHANNEL": "legacy output routes the materialized line to MSGCH_TALK_VISUAL",
        "SOUND_LIKE_CHANNEL": "legacy output treats the materialized control prefix as sound-like",
        "UNANALYSABLE": "analysis fails closed; legacy effect is not statically proven",
    }
    result: dict[str, object] = {
        "requested_root": key,
        "language": language,
        "top_locator": {"canonical_key": key, "variant_ordinal": ordinal},
        "recursive_provenance": provenance,
        "phase": phase,
        "behavior": behavior,
        "legacy_effect": effects[behavior],
        "catalog_coverage": _catalog_coverage(catalog, key, ordinal, behavior),
    }
    if detail is not None:
        result["detail"] = detail
    return result


def analyze_language(language: str, roots: list[str],
                     entries: dict[str, EffectiveEntry],
                     catalog: dict[tuple[str, int], dict[str, Any]]) -> dict[str, Any]:
    analyzer = PredicateAnalyzer(entries, language)
    occurrences: list[dict[str, object]] = []
    predicates: dict[str, set[str]] = {key: set() for key in roots}
    source_counts = {"selected_language": 0, "english_fallback": 0, "missing": 0}
    for key in roots:
        entry = entries.get(key)
        if entry is None:
            source_counts["missing"] += 1
            occurrences.append(_occurrence(
                key, language, 0, [], "ANALYSIS", "UNANALYSABLE", catalog,
                "requested root is absent from the effective database"))
            predicates[key].add("UNANALYSABLE")
            continue
        if entry.source_language == language:
            source_counts["selected_language"] += 1
        else:
            source_counts["english_fallback"] += 1
        if entry.parse_error is not None or not entry.variants:
            detail = entry.parse_error or "requested root has no selectable variants"
            occurrences.append(_occurrence(
                key, language, 0, [], "ANALYSIS", "UNANALYSABLE", catalog, detail))
            predicates[key].add("UNANALYSABLE")
            continue
        for variant in entry.variants:
            ordinal = variant["locator"]["variant_ordinal"]
            try:
                analyzer.validate_limits(key, ordinal)
                provenance = analyzer.provenance(key, ordinal)
                pre = analyzer.pre_variant(key, ordinal)
                post = {summary.completed()
                        for summary in analyzer.post_variant(key, ordinal)}
                found_pre = set().union(*(summary.behaviors for summary in pre))
                found_post = set().union(*(summary.behaviors for summary in post))
                if any(summary.unknown_prefix for summary in post):
                    raise Unanalysable(f"{key}:{ordinal}: dynamic or unknown channel prefix")
                for behavior in sorted(found_pre):
                    predicates[key].add(behavior)
                    occurrences.append(_occurrence(
                        key, language, ordinal, provenance, "PRE_BINDING", behavior,
                        catalog))
                for behavior in sorted(found_post):
                    predicates[key].add(behavior)
                    occurrences.append(_occurrence(
                        key, language, ordinal, provenance, "POST_MATERIALIZATION",
                        behavior, catalog))
            except Unanalysable as exc:
                predicates[key].add("UNANALYSABLE")
                occurrences.append(_occurrence(
                    key, language, ordinal, [], "ANALYSIS", "UNANALYSABLE",
                    catalog, str(exc)))
    occurrences.sort(key=lambda item: (
        item["requested_root"], item["top_locator"]["variant_ordinal"],
        item["phase"], item["behavior"],
    ))
    behavior_roots = {
        behavior: sorted(key for key, values in predicates.items() if behavior in values)
        for behavior in (
            "GESTURE", "VISUAL_APPLICABILITY", "VISUAL_CHANNEL",
            "SOUND_LIKE_CHANNEL", "UNANALYSABLE",
        )
    }
    return {
        "effective_source_counts": source_counts,
        "predicate_roots": behavior_roots,
        "behavior_root_union": sorted(
            key for key, values in predicates.items()
            if values - {"UNANALYSABLE"}),
        "occurrences": occurrences,
    }


def build_report(en_path: Path, zh_path: Path, inventory_path: Path,
                 manifest_path: Path, candidate_path: Path,
                 candidate_anchor_path: Path) -> dict[str, Any]:
    try:
        en_artifact = load_artifact(en_path)
        zh_artifact = load_artifact(zh_path)
    except ArtifactError as exc:
        raise AuditError(str(exc)) from exc
    inventory = _read_json(inventory_path)
    manifest_raw = _read_json(manifest_path)
    semantic = inventory.get("semantic_fingerprint")
    if not isinstance(semantic, str) or not semantic:
        raise AuditError("inventory semantic_fingerprint is missing")
    try:
        manifest = validate_manifest(manifest_raw, inventory)
    except ManifestError as exc:
        raise AuditError(str(exc)) from exc
    candidate_anchor = load_candidate_anchor(candidate_anchor_path)
    candidate_sha256 = _sha256(candidate_path)
    _require(candidate_sha256 == candidate_anchor.artifact_sha256,
             "candidate artifact does not match tracked anchor")
    candidate = load_candidate_artifact(candidate_path)
    _require(candidate.counts == candidate_anchor.counts,
             "candidate artifact counts do not match tracked anchor")
    inventory_roots = sorted(
        entry["key"] for entry in inventory.get("entries", [])
        if entry.get("defined_in_monspell") is True
    )
    if not inventory_roots or len(inventory_roots) != len(set(inventory_roots)):
        raise AuditError("inventory monspell root universe is empty or duplicated")
    catalog = _catalog_index(manifest)
    en_effective = effective_entries(en_artifact, None, "en")
    zh_effective = effective_entries(en_artifact, zh_artifact, "zh")
    en_candidate = candidate_hits(candidate, en_effective, "en")
    zh_candidate = candidate_hits(candidate, zh_effective, "zh")
    en_hit_index = {
        item["canonical_key"]: item for item in en_candidate["hits"]
    }
    zh_hit_index = {
        item["canonical_key"]: item for item in zh_candidate["hits"]
    }
    en_hit_keys = set(en_hit_index)
    zh_hit_keys = set(zh_hit_index)
    runtime_roots = sorted(en_hit_keys | zh_hit_keys)
    en_only = sorted(en_hit_keys - zh_hit_keys)
    zh_only = sorted(zh_hit_keys - en_hit_keys)
    presence_mismatches = [
        {
            "requested_root": key,
            "mismatch_kind": "PRESENCE",
            "en_present": key in en_hit_index,
            "zh_present": key in zh_hit_index,
            "en_hit": en_hit_index.get(key),
            "zh_hit": zh_hit_index.get(key),
            "migration_priority": "CANDIDATE_PRESENCE_DIVERGENCE",
        }
        for key in sorted(set(en_only) | set(zh_only))
    ]
    source_mismatches = [
        {
            "canonical_key": key,
            "en_source": en_hit_index[key]["source"],
            "zh_source": zh_hit_index[key]["source"],
            "en_effective_source": en_hit_index[key]["effective_source"],
            "zh_effective_source": zh_hit_index[key]["effective_source"],
        }
        for key in sorted(en_hit_keys & zh_hit_keys)
        if en_hit_index[key]["source"] != zh_hit_index[key]["source"]
    ]
    inventory_root_set = set(inventory_roots)
    inventory_unreachable = sorted(inventory_root_set - set(runtime_roots))
    languages = {
        "en": analyze_language("en", runtime_roots, en_effective, catalog),
        "zh": analyze_language("zh", runtime_roots, zh_effective, catalog),
    }
    mismatches = []
    inconclusive = []
    presence_mismatch_keys = set(en_only) | set(zh_only)
    for key in runtime_roots:
        if key in presence_mismatch_keys:
            continue
        en_unanalysable = key in languages["en"]["predicate_roots"]["UNANALYSABLE"]
        zh_unanalysable = key in languages["zh"]["predicate_roots"]["UNANALYSABLE"]
        en_predicates = sorted(
            behavior for behavior, values in languages["en"]["predicate_roots"].items()
            if key in values and behavior != "UNANALYSABLE")
        zh_predicates = sorted(
            behavior for behavior, values in languages["zh"]["predicate_roots"].items()
            if key in values and behavior != "UNANALYSABLE")
        if en_unanalysable or zh_unanalysable:
            inconclusive.append({
                "requested_root": key,
                "en_analyzable": not en_unanalysable,
                "zh_analyzable": not zh_unanalysable,
                "en_proven_predicates": en_predicates,
                "zh_proven_predicates": zh_predicates,
            })
        elif en_predicates != zh_predicates:
            mismatches.append({
                "requested_root": key,
                "en_predicates": en_predicates,
                "zh_predicates": zh_predicates,
                "migration_priority": "BEHAVIOR_DIVERGENCE",
            })
    occurrences = languages["en"]["occurrences"] + languages["zh"]["occurrences"]
    behavioral = [item for item in occurrences if item["behavior"] != "UNANALYSABLE"]
    covered = sum(1 for item in behavioral if item["catalog_coverage"]["covered"])
    unanalysable = sum(1 for item in occurrences if item["behavior"] == "UNANALYSABLE")
    catalog_complete = covered == len(behavioral)
    parity_proven = not mismatches and not presence_mismatches
    analysis_conclusive = not inconclusive
    blockers = []
    if not catalog_complete:
        blockers.append("legacy behavior metadata coverage is incomplete")
    if not parity_proven:
        blockers.append("EN/ZH behavior parity is not proven")
    if not analysis_conclusive:
        blockers.append("EN/ZH behavior analysis is inconclusive")
    return {
        "schema_version": SCHEMA_VERSION,
        "domain": "monspell",
        "analysis_completeness": "SOUND_CLOSED_WORLD_UPPER_BOUND",
        "inputs": {
            "english_artifact": {"sha256": _sha256(en_path)},
            "localized_artifact": {"language": "zh", "sha256": _sha256(zh_path)},
            "candidate_artifact": {
                "sha256": candidate_sha256,
                "schema_version": candidate.schema_version,
                "completeness": candidate.completeness,
                "counts": candidate.counts,
            },
            "candidate_anchor": {
                "sha256": _sha256(candidate_anchor_path),
                "artifact_sha256": candidate_anchor.artifact_sha256,
            },
            "inventory": {
                "semantic_fingerprint": semantic,
                "sha256": _sha256(inventory_path),
            },
            "overlay_manifest": {"sha256": _sha256(manifest_path)},
        },
        "universe": {
            "requested_root_source": (
                "union of canonical candidate lookup hits in EN and ZH "
                "effective nonempty SpeakDB"
            ),
            "requested_root_count": len(runtime_roots),
            "runtime_roots": runtime_roots,
            "effective_merge_languages": ["en", "zh"],
            "inventory_root_count": len(inventory_roots),
            "inventory_reachable_root_count": (
                len(inventory_root_set & set(runtime_roots))
            ),
            "inventory_unreachable_root_count": len(inventory_unreachable),
            "inventory_unreachable_roots": inventory_unreachable,
            "inventory_roots_contained_in_english_artifact": all(
                key in en_effective for key in inventory_roots),
            "inventory_roots_contained_in_zh_effective_merge": all(
                key in zh_effective for key in inventory_roots),
            "candidate_key_containment_proven": True,
            "runtime_reachability_proven": True,
            "reachability_kind": "SOUND_UPPER_BOUND_NOT_EXACT",
            "containment_proof": (
                "production recipe closed-world upper bound joined against "
                "effective nonempty SpeakDB keys"
            ),
        },
        "candidate_lookup": {
            "en": en_candidate,
            "zh": zh_candidate,
            "language_only_hits": {
                "en_only": [en_hit_index[key] for key in en_only],
                "zh_only": [zh_hit_index[key] for key in zh_only],
            },
            "presence_parity_proven": not presence_mismatches,
            "source_parity_proven": not source_mismatches,
            "source_parity_mismatch": source_mismatches,
        },
        "languages": languages,
        "locale_presence_mismatch": presence_mismatches,
        "locale_behavior_mismatch": mismatches,
        "locale_behavior_inconclusive": inconclusive,
        "coverage": {
            "behavior_occurrences": len(behavioral),
            "catalog_covered_occurrences": covered,
            "catalog_coverage_complete": catalog_complete,
            "unanalysable_occurrences": unanalysable,
            "en_zh_behavior_parity_proven": parity_proven,
            "en_zh_behavior_analysis_conclusive": analysis_conclusive,
        },
        "phase2_ready": not blockers,
        "phase2_blockers": blockers,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--english-artifact", type=Path, required=True)
    parser.add_argument("--localized-artifact", type=Path, required=True)
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--candidate-artifact", type=Path, required=True)
    parser.add_argument("--candidate-anchor", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        rendered = _render(build_report(
            args.english_artifact, args.localized_artifact,
            args.inventory, args.manifest, args.candidate_artifact,
            args.candidate_anchor))
        if args.check:
            actual = args.output.read_text(encoding="utf-8")
            if actual != rendered:
                print("monspell behavior audit error: report drift", file=sys.stderr)
                return 1
        else:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
    except (AuditError, OSError, UnicodeError) as exc:
        print(f"monspell behavior audit error: {exc}", file=sys.stderr)
        return 2
    print("monspell behavior audit: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
