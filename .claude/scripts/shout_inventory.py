#!/usr/bin/env python3
"""Build and audit the Issue #69 shout/insult review inventory.

The inventory is derived from production ``textdb-phase0-dump`` artifacts of
the ``shout`` TextDB family (database.cc ``TextDB("shout", "database/",
{"shout.txt", "insult.txt"})``) and exact Git source snapshots.  It freezes
the 91 shout.txt identities per language (119/119 weighted variants), the 33
insult.txt identities (557/532 weighted variants), the exact 8-key
asymmetric list (derived from the baseline dumps, never copied from prose),
the zero random-site/Lua-site counts, the complete token classification and
a reachability proof from the consumed production root keys.

Consumer model (frozen): ``shout.cc::monster_shout`` queries ``_shout_key``
(``mons_type_name(DESC_DBNAME)`` monster DB names, ``pandemonium lord``, and
``transform.cc`` queries ``Sphinx riddle success``/``failure``/
``failure acknowledged``.  The suffix variants, monster keys, ghost keys,
glyph keys and sphinx roots are direct query roots; every other identity
must be reachable: the four ``_riddle_*`` fragments, the shared ``imp``
fragment and the twenty demon-taunt/imp-taunt/insult-chain keys through
the ShoutDB ``@token@`` walk from the roots, and the twelve
``insult <species>`` keys plus ``small_food`` only through the
post-processing path ``mon-util.cc::_get_species_insult``
(``@species_insult_*@``) which resolves them through SpeakDB - insult.txt
is double-loaded by SpeakDB (index 4) and ShoutDB (index 1), so the
double-load provenance is checked per DB and the SpeakDB effective
entries must match the ShoutDB dump verbatim.  The root set is not
``everything minus a hand list``: default keys are parsed from the
exact-Git ``default_msg_keys`` map, sphinx roots from the exact-Git
``transform.cc`` literals, the glyph shape from the exact-Git
``shout.cc`` expressions, monster names from ``dat/mons/*.yaml``, job
names from ``dat/jobs/*.yaml`` and the legacy ``giant slug`` key from the
exact-Git ``AXED_MON`` table (mon-gen/header.txt).

The ``#### Player sphinx riddle lines`` comment title block is a
production-parser artifact: comment lines starting with ``#`` are skipped,
but the title line itself is not, so it becomes a zero-body key that can
never be selected.  Both the parse layer (``parse_db_keys`` over the exact
sources) and the derived layer (the production dump) must produce the same
93/92 shout.txt raw key sets and the same single empty artifact; the title
never becomes an identity.  ``__buggy`` is the only in-file sentinel key
(``__DEFAULT``/``__NEXT``/``__NONE`` are runtime-only fallback values and
must never be ShoutDB keys).

The strict JSONL review ledger (one metadata record plus 124 cards) is the
issue #69 audit trail.  ``--scaffold-output`` generates the initial empty
ledger (exclusive create at ``docs/shout-review-results.md`` through the
decorlines hardened write transaction, which fails closed when a ledger
already exists); the later zh-translator phase fills the 124 cards, and
``--candidate-ref`` plus the candidate parameters bind every proposal to an
exact-clean candidate commit whose dumps match the ledger proposals
verbatim.

Mutable artifacts (production dumps, review results, glossary) are read
through the hardened audited snapshot helpers (no-follow descriptor, regular
file, opened-inode identity).  In the candidate flow the review ledger and
glossary are read directly from the exact candidate commit tree as
regular-file blobs, and the exact-clean candidate boundary is proven before
any candidate data is consumed.  Generated evidence (``--inventory-output``)
may only be written to /tmp; the only repository write is the explicitly
scoped ledger scaffold.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, deque
from pathlib import Path
from typing import Any

import yaml

import decorlines_inventory as decorlines
import monflee_inventory as shared
import wpnnoise_inventory as hardened


SCHEMA_VERSION = 1
SOURCE_BASENAMES = ("shout.txt", "insult.txt")
STRICT_BEGIN = "<!-- BEGIN STRICT SHOUT REVIEW EVIDENCE v1 -->"
STRICT_END = "<!-- END STRICT SHOUT REVIEW EVIDENCE v1 -->"
RESULTS_PATH = Path(__file__).resolve().parents[2] / "docs/shout-review-results.md"

# Frozen Issue #69 baseline shape (verified against the production dumps at
# the baseline OID; the asymmetric key list itself is derived from the
# baseline dumps below and only its count/order is frozen here).
EXPECTED_SHOUT_IDENTITY_COUNT = 91
EXPECTED_INSULT_IDENTITY_COUNT = 33
EXPECTED_IDENTITY_COUNT = EXPECTED_SHOUT_IDENTITY_COUNT + EXPECTED_INSULT_IDENTITY_COUNT
# Identity-level variant counts exclude the __buggy sentinel variant; the
# dump-level totals (119/119 for shout.txt) are frozen separately.
EXPECTED_SHOUT_EN_VARIANTS = 118
EXPECTED_SHOUT_ZH_VARIANTS = 118
EXPECTED_INSULT_EN_VARIANTS = 557
EXPECTED_INSULT_ZH_VARIANTS = 532
EXPECTED_DUMP_SHOUT_EN_VARIANTS = 119
EXPECTED_DUMP_SHOUT_ZH_VARIANTS = 119
EXPECTED_EN_RANDOM_SITES = 0
EXPECTED_ZH_RANDOM_SITES = 0
EXPECTED_EN_LUA_SITES = 0
EXPECTED_ZH_LUA_SITES = 0
# The __buggy sentinel keeps exactly one variant per language.
EXPECTED_SENTINEL_VARIANTS = {"english": 1, "chinese": 1}

# The exact 8 asymmetric insult.txt keys (EN count, ZH count).  shout.txt is
# symmetric (119/119).
EXPECTED_ASYMMETRY: dict[str, list[int]] = {
    "give_up": [30, 29],
    "insult general adj1": [78, 72],
    "insult general adj2": [70, 65],
    "insult general noun": [103, 84],
    "insult mummy adj2": [18, 17],
    "insult mummy noun": [15, 14],
    "insult vampire adj2": [11, 12],
    "run_away": [27, 34],
}

# The 26 default_msg_keys entries of shout.cc::monster_shout; parsed from
# the exact-Git map and required to equal this frozen tuple.
DEFAULT_MSG_KEYS = (
    "__SHOUT", "__BARK", "__HOWL", "__TWO_SHOUTS", "__ROAR", "__SCREAM",
    "__BELLOW", "__BLEAT", "__TRUMPET", "__SCREECH", "__BUZZ", "__MOAN",
    "__GURGLE", "__CROAK", "__GROWL", "__HISS", "__SKITTER",
    "__FAINT_SKITTER", "__DEMON_TAUNT", "__CHERUB", "__SQUEAL",
    "__LOUD_ROAR", "__RUSTLE", "__SQUEAK", "__CAW", "__LAUGH",
)

# transform.cc getShoutString("Sphinx riddle ...") literals.
SPHINX_RIDDLE_KEYS = frozenset({
    "sphinx riddle success",
    "sphinx riddle failure",
    "sphinx riddle failure acknowledged",
})

# Glyph fallback keys present in shout.txt; the consumer builds "'x'" /
# "'cap-X'" from the base char, bound to the exact-Git shout.cc shape.
EXPECTED_GLYPH_KEYS = frozenset({"'&'", "'cap-g'", "'cap-j'"})

# The only in-file sentinel key: monster_shout falls back to the
# lookup(default_msg_keys, s_type, "__BUGGY") value.  __DEFAULT/__NEXT/
# __NONE are runtime-only fallback values and must never be ShoutDB keys.
# Runtime sentinel values live in the same canonical key space as
# scoped_keys (lowercase_string), so the intersection in _classify_keys
# and _dataset is effective instead of vacuous.
SENTINEL_KEYS = frozenset({"__buggy"})
RUNTIME_SENTINEL_VALUES = frozenset({"__default", "__next", "__none"})

# The "#### Player sphinx riddle lines" title block artifact: the title
# line is parsed as a zero-body key by the production parser (comment lines
# starting with '#' are skipped, the title itself is not).  It must never
# become an identity.
TITLE_BLOCK_ARTIFACTS = frozenset({"player sphinx riddle lines"})

# ShoutDB recursion fragments: reachable only through @token@ recursion.
# The four _riddle_* keys are driven by the sphinx riddle roots; "imp"
# (there is no MONS_IMP monster type at the baseline) is the shared imp
# shout driven by the iron/shadow/white imp monster roots.
FRAGMENT_KEYS = frozenset({
    "_riddle_adj_",
    "_riddle_fail_acknowledged_",
    "_riddle_fail_general_",
    "_riddle_prefix_",
    "imp",
})

# shout.txt keys whose monster type is AXED_MON at the exact commit
# (mon-gen/header.txt): no live monster producer builds the DB name and no
# @token@ references it, so it can never be queried at runtime.  It stays a
# review identity but is exempt from the reachability proof by definition.
# Derived from the exact-Git AXED_MON table and required to equal this set.
EXPECTED_LEGACY_KEYS = frozenset({"giant slug"})

# insult.txt keys reachable only through the mon-util.cc::_get_species_insult
# post-processing path (@species_insult_*@ -> SpeakDB lookups of
# "insult <species>/general <type>").  The general adj1/adj2/noun keys are
# NOT in this set: they are also referenced in-family (@insult general adjN@
# from insult_adjective1/2 and insult_noun), so they are ShoutDB-recursion
# keys.  small_food is SpeakDB-only (referenced only by "insult spriggan
# noun", which is itself SpeakDB-only).  Their SpeakDB effective entries
# must match the ShoutDB dump verbatim (double-load parity).
SPEAKDB_POSTPROCESS_KEYS = frozenset({
    "insult dwarf adj2",
    "insult elf adj1",
    "insult felid adj1",
    "insult felid adj2",
    "insult felid noun",
    "insult minotaur noun",
    "insult mummy adj2",
    "insult mummy noun",
    "insult spriggan noun",
    "insult tengu adj2",
    "insult undead adj2",
    "insult vampire adj2",
    "small_food",
})

# Tokens replaced after TextDB expansion by mon-util.cc::do_mon_str_replacements
# (and _get_species_insult).  Everything else in every variant must be an
# in-family key (ShoutDB recursion) or the run fails closed.
POSTPROCESS_TOKENS = frozenset({
    "the_monster",
    "the_monster_possessive",
    "possessive",
    "says",
    "subjective",
    "species_insult_adj1",
    "species_insult_adj2",
    "species_insult_noun",
})

# Closure seeds: the 26 default_msg_keys + 3 sphinx riddle roots + 3 glyph
# roots.  From these seeds the ShoutDB @token@ walk reaches the riddle
# fragments and the demon-taunt insult chain (frozen below); the imp chain
# (imp/imp_taunt/run_or_give_up) is driven by the iron/shadow/white imp
# monster roots, and the full closure proof starts from every direct root.
CLOSURE_SEEDS = (
    tuple(key.lower() for key in DEFAULT_MSG_KEYS)
    + tuple(sorted(SPHINX_RIDDLE_KEYS))
    + tuple(sorted(EXPECTED_GLYPH_KEYS))
)

# Non-root keys the 32 seeds alone cannot reach: the "imp" fragment and its
# insult chain (imp_taunt/run_or_give_up) are driven by the monster roots.
# The species keys "insult general adj1/adj2/noun" ARE seed-reachable
# (insult_adjective1/2 -> @insult general adjN@); "insult undead adj2" is
# SpeakDB-only (its only in-family references come from the SpeakDB-only
# mummy/vampire adj2 keys).
MONSTER_DRIVEN_NON_ROOTS = frozenset({"imp", "imp_taunt", "run_or_give_up"})

# Fixed exact-Git producer sources (tracked C++ files; the monster and job
# YAML inputs are enumerated from the same OID tree).
PRODUCER_GIT_FILES = [
    "crawl-ref/source/shout.cc",         # default_msg_keys + glyph shape
    "crawl-ref/source/transform.cc",     # Sphinx riddle getShoutString calls
    "crawl-ref/source/database.cc",      # TextDB initializers
    "crawl-ref/source/mon-util.cc",      # _get_species_insult / do_mon_str_replacements
    "crawl-ref/source/util/mon-gen/header.txt",  # AXED_MON legacy names
]

# Anchor producer names that must survive the exact-Git derivation.
# "giant slug" is deliberately absent: it is an AXED_MON legacy name
# (bound by _axed_monster_names/EXPECTED_LEGACY_KEYS), not a live YAML.
_MONSTER_ANCHORS = ("moth of wrath", "iron imp", "polyphemus",
                    "player ghost")
_JOB_ANCHORS = ("fighter", "monk", "wanderer", "fire elementalist",
                "chaos knight")

# The localized directory scan loads every zh/*.txt file into each DB;
# zh/monspeak.txt legally defines seven shout-family keys whose shout.txt
# definitions win (sorted scan loads monspeak before shout).  The EN
# ShoutDB manifest (shout.txt/insult.txt only) has no overrides.
EXPECTED_OVERRIDDEN_KEYS: dict[str, frozenset[str]] = {
    "english": frozenset(),
    "chinese": frozenset({
        "'&'", "iron imp", "moth of wrath", "player ghost",
        "polyphemus", "shadow imp", "white imp",
    }),
}

InventoryError = hardened.InventoryError
_require = hardened._require
_sha256 = hardened._sha256
_canonical_json = hardened._canonical_json

_SHOUT_DB_RE = re.compile(
    r'\bTextDB\s*\(\s*"shout"\s*,\s*"database/"\s*,\s*\{(.*?)\}\s*\)',
    re.DOTALL,
)
_GLYPH_KEY_RE = re.compile(r"^'(cap-)?[^']'$")
_DEFAULT_MSG_MAP_RE = re.compile(
    r"default_msg_keys\s*=\s*\{(.*?)\n\};", re.DOTALL
)
_MSG_MAP_ENTRY_RE = re.compile(r"\{\s*S_\w+\s*,\s*\"([^\"]*)\"\s*\}")
_GETSHOUT_CALL_RE = re.compile(r'getShoutString\(([^;]*)\)', re.DOTALL)


def _shoutdb_source_manifest(oid: str, label: str) -> list[str]:
    """Parameterized copy of the hardened manifest reader, targeting the
    ``TextDB("shout", "database/", ...)`` initializer.  The two source
    literals and their order are bound to exact Git."""
    database = shared._decode_utf8(
        shared._git_blob_at_oid(oid, "crawl-ref/source/database.cc", label),
        label,
    )
    matches = list(_SHOUT_DB_RE.finditer(database))
    _require(
        len(matches) == 1,
        f"{label} database.cc must have one literal ShoutDB initializer",
    )
    body = matches[0].group(1)
    files: list[str] = []
    position = 0
    expect_value = True
    while True:
        while position < len(body):
            if body[position] in " \t\r\n\f\v":
                position += 1
            elif body.startswith("//", position):
                newline = body.find("\n", position + 2)
                position = len(body) if newline < 0 else newline + 1
            else:
                break
        if position == len(body):
            break
        if expect_value:
            _require(body[position] == '"',
                     f"{label} ShoutDB initializer is not a literal list")
            end = body.find('"', position + 1)
            _require(end >= 0 and "\\" not in body[position + 1:end],
                     f"{label} ShoutDB source literal is malformed")
            filename = body[position + 1:end]
            _require(bool(re.fullmatch(r"[A-Za-z0-9_]+\.txt", filename)),
                     f"{label} has unsafe ShoutDB source {filename!r}")
            _require(filename not in files,
                     f"{label} has duplicate ShoutDB source {filename!r}")
            files.append(filename)
            position = end + 1
            expect_value = False
        else:
            _require(body[position] == ',',
                     f"{label} ShoutDB source literals must be comma separated")
            position += 1
            expect_value = True
    _require(
        files == ["shout.txt", "insult.txt"],
        f"{label} ShoutDB source manifest must be exactly "
        f"shout.txt, insult.txt, got {files!r}",
    )
    return [f"database/{filename}" for filename in files]


def _speakdb_insult_provenance(oid: str, label: str) -> int:
    """SpeakDB also loads insult.txt (as the fifth SpeakDB source).  The
    two loads are independent provenance: SpeakDB index 4, ShoutDB index 1,
    with different effective load orders.  Recorded separately and checked
    per DB."""
    manifest = shared._english_source_manifest(oid, label)
    _require(
        "database/insult.txt" in manifest,
        f"{label} SpeakDB manifest must load insult.txt",
    )
    index = manifest.index("database/insult.txt")
    _require(
        index == 4,
        f"{label} SpeakDB insult.txt index must be 4, got {index}",
    )
    return index


def _derive_scoped_shout_dump(
    oid: str, directory: str, label: str,
) -> dict[str, Any]:
    """Derive the shout-family-scoped dump (shout.txt + insult.txt entries)
    from the exact Git baseline using the ShoutDB input sequence (or the
    localized directory scan for ZH)."""
    manifest = (
        _shoutdb_source_manifest(oid, label)
        if directory == "database/"
        else hardened.shared._localized_source_manifest(oid, label)
    )
    sources = [
        {
            "source_name": source_name,
            "load_index": load_index,
            "normalized_utf8": hardened.shared._source_snapshot_at_oid(
                oid, source_name, f"{label} {source_name}"
            ),
        }
        for load_index, source_name in enumerate(manifest)
    ]
    entries: list[dict[str, Any]] = []
    for basename in SOURCE_BASENAMES:
        scoped = hardened.shared._derive_scoped_from_sources(
            sources, directory, label, source_basename=basename
        )
        entries.extend(scoped["entries"])
    return {"sources": sources, "entries": entries}


def _require_scoped_derivation(
    supplied: dict[str, Any], derived: dict[str, Any], label: str,
) -> None:
    """Bind every shout-family entry of the dump to exact Git, per source
    file: the same sources and, for each of shout.txt/insult.txt, the same
    scoped history/raw_body/variants."""
    _require(
        supplied["sources"] == derived["sources"],
        f"{label} source manifest/order/snapshots do not match exact Git inputs",
    )
    for basename in SOURCE_BASENAMES:
        scoped_source = f"{supplied['source_directory']}{basename}"
        touching = [
            entry for entry in supplied["entries"]
            if any(item["source_name"] == scoped_source
                   for item in entry["source_history"])
        ]
        derived_scoped = [
            entry for entry in derived["entries"]
            if any(item["source_name"] == scoped_source
                   for item in entry["source_history"])
        ]
        _require(
            touching == derived_scoped,
            f"{label} {basename} scoped history/raw_body/variants do not "
            f"match exact Git derivation",
        )


def _normalize_load_index(entry: dict[str, Any], old: int, new: int) -> dict[str, Any]:
    """Deep-copy one dump entry with every provenance load_index remapped
    (used for the cross-DB parity comparison)."""
    def remap(provenance: dict[str, Any]) -> dict[str, Any]:
        return {
            "source_name": provenance["source_name"],
            "load_index": new if provenance["load_index"] == old
                          else provenance["load_index"],
            "definition_ordinal": provenance["definition_ordinal"],
        }

    result = dict(entry)
    result["effective_provenance"] = remap(entry["effective_provenance"])
    result["source_history"] = [remap(item)
                                for item in entry["source_history"]]
    variants = []
    for variant in entry["variants"]:
        variant_copy = dict(variant)
        variant_copy["provenance"] = remap(variant["provenance"])
        variants.append(variant_copy)
    result["variants"] = variants
    return result


def _require_speakdb_insult_parity(
    supplied: dict[str, Any], oid: str, label: str,
) -> None:
    """The double-load provenance proof: insult.txt is loaded by both
    SpeakDB (index 4) and ShoutDB (index 1).  Derive the SpeakDB-scoped
    insult entries from the exact-Git SpeakDB manifest and require every
    one to match the ShoutDB dump entry verbatim after the load_index
    remap (SpeakDB 4 -> ShoutDB 1).  A SpeakDB collision in a later source
    file, a removed/emptied/forged key or a load-order change fails closed
    instead of silently changing the species-insult path."""
    speak_index = _speakdb_insult_provenance(oid, label)
    derived = hardened.shared._derive_scoped_dump(
        oid, supplied["source_directory"], label,
        source_basename="insult.txt",
    )
    derived_by_key = {
        entry["canonical_key"]: entry for entry in derived["entries"]
    }
    supplied_by_key = {
        entry["canonical_key"]: entry for entry in supplied["entries"]
        if any(item["source_name"]
               == f"{supplied['source_directory']}insult.txt"
               for item in entry["source_history"])
    }
    _require(
        set(derived_by_key) == set(supplied_by_key),
        f"{label} SpeakDB insult key set differs from the ShoutDB dump: "
        f"{sorted(set(derived_by_key) ^ set(supplied_by_key))!r}",
    )
    for key in sorted(derived_by_key):
        expected = _normalize_load_index(derived_by_key[key], speak_index, 1)
        _require(
            supplied_by_key[key] == expected,
            f"{label} SpeakDB insult key {key!r} does not match the "
            f"ShoutDB dump verbatim (double-load parity)",
        )


def _require_regular_shout_git_sources(
    ref: str, directory: str, label: str,
) -> None:
    """Bind the ShoutDB derivation inputs to regular blobs at the exact OID.

    Besides database.cc and every TextDB source, the root-key derivation
    reads the consumer C++ sources and the monster/job YAML inputs from the
    same commit tree; this pre-flight proves every one of those tree
    entries is a regular file so no unsupported Git object type can be
    parsed with semantics different from the production checkout."""
    if directory == "database/":
        manifest = _shoutdb_source_manifest(ref, label)
    else:
        manifest = hardened.shared._localized_source_manifest(ref, label)
    hardened._require_regular_git_blobs(
        ref,
        ["crawl-ref/source/database.cc"]
        + [f"crawl-ref/source/dat/{name}" for name in manifest]
        + PRODUCER_GIT_FILES
        + _git_tree_yamls(ref, "crawl-ref/source/dat/mons", label)
        + _git_tree_yamls(ref, "crawl-ref/source/dat/jobs", label),
        label,
    )


def _git_tree_yamls(oid: str, directory: str, label: str) -> list[str]:
    """List the committed top-level ``*.yaml`` inputs of one data directory
    at the exact OID.

    Mirrors mon-gen.py/job-gen.py exactly: both iterate
    ``sorted(os.listdir(datadir))`` and open every ``*.yaml`` name directly,
    never descending into nested directories, so a recursive ``ls-tree -r``
    would overcount YAML files living in subdirectories that production
    never reads.  The non-recursive listing still emits tree entries for
    subdirectories; only blob entries named ``*.yaml`` count, and a
    directory named ``*.yaml`` would make the production open fail, so it
    fails closed here instead."""
    listing = hardened.shared._git_output(
        ["ls-tree", oid, "--", f"{directory}/"],
        f"{label} {directory}",
    )
    paths: list[str] = []
    for line in listing.splitlines():
        meta, name = line.split(b"\t", 1)
        kind = meta.split(b" ")[1]
        if name.endswith(b".yaml"):
            _require(
                kind == b"blob",
                f"{label} {directory} has a non-file *.yaml entry "
                f"{name.decode('utf-8')!r} that production could not read",
            )
            paths.append(name.decode("utf-8"))
    _require(bool(paths), f"{label} {directory} contains no YAML inputs")
    return paths


def _yaml_name_fields(oid: str, directory: str, label: str) -> list[str]:
    """Lowercased ``name`` fields of every committed YAML input in one data
    directory.  mon-data.h/job-data.h store the YAML ``name`` verbatim; the
    TextDB lookup lowercases the query key (database.cc::_getWeightedSelection),
    so the shout.txt file keys are the lowercased producer names."""
    names: list[str] = []
    for git_path in _git_tree_yamls(oid, directory, label):
        source = hardened.shared._decode_utf8(
            hardened.shared._git_blob_at_oid(
                oid, git_path, f"{label} {git_path}"
            ),
            label,
        )
        try:
            data = yaml.safe_load(source)
        except yaml.YAMLError as exc:
            raise InventoryError(
                f"{label} {git_path} is not valid YAML: {exc}"
            ) from exc
        _require(isinstance(data, dict),
                 f"{label} {git_path} must be a YAML mapping")
        name = data.get("name")
        _require(isinstance(name, str) and len(name) >= 2,
                 f"{label} {git_path} needs a valid name field")
        names.append(name.lower())
    _require(bool(names), f"{label} {directory} derived no producer names")
    return sorted(names)


def _monster_producers(oid: str, label: str) -> list[str]:
    """English DB names of every monster (dat/mons/*.yaml name fields);
    these are the ``mons_type_name(mc, DESC_DBNAME)`` prefixes shout.cc
    queries through _shout_key."""
    names = _yaml_name_fields(oid, "crawl-ref/source/dat/mons", label)
    for anchor in _MONSTER_ANCHORS:
        _require(anchor in names,
                 f"{label} monster derivation lost {anchor!r}")
    return names


def _job_producers(oid: str, label: str) -> list[str]:
    """Lowercased job names (dat/jobs/*.yaml name fields); the player-ghost
    shout keys are ``<job> player ghost`` built by shout.cc::_shout_key."""
    names = _yaml_name_fields(oid, "crawl-ref/source/dat/jobs", label)
    for anchor in _JOB_ANCHORS:
        _require(anchor in names,
                 f"{label} job derivation lost {anchor!r}")
    return names


def _shoutcc_default_keys(oid: str, label: str) -> list[str]:
    """Parse the exact-Git default_msg_keys map of shout.cc and require it
    to equal the frozen 26 keys in declaration order."""
    source = hardened.shared._decode_utf8(
        hardened.shared._git_blob_at_oid(
            oid, "crawl-ref/source/shout.cc", label
        ),
        label,
    )
    match = _DEFAULT_MSG_MAP_RE.search(source)
    _require(match is not None,
             f"{label} cannot find default_msg_keys map in shout.cc")
    # The map starts with the S_SILENT -> "" entry; the 26 non-empty
    # values are the default shout lookup keys.
    keys = [found.group(1)
            for found in _MSG_MAP_ENTRY_RE.finditer(match.group(1))
            if found.group(1)]
    _require(
        tuple(keys) == DEFAULT_MSG_KEYS,
        f"{label} default_msg_keys differ from the frozen 26 keys: {keys!r}",
    )
    return keys


def _transformcc_sphinx_roots(oid: str, label: str) -> list[str]:
    """Parse the exact-Git getShoutString literals of transform.cc and
    require exactly the three Sphinx riddle roots."""
    source = hardened.shared._decode_utf8(
        hardened.shared._git_blob_at_oid(
            oid, "crawl-ref/source/transform.cc", label
        ),
        label,
    )
    calls: list[str] = []
    for found in _GETSHOUT_CALL_RE.finditer(source):
        calls.extend(literal.group(1)
                     for literal in re.finditer(r'"([^"]*)"', found.group(1)))
    _require(
        sorted(literal.lower() for literal in calls)
        == sorted(SPHINX_RIDDLE_KEYS),
        f"{label} transform.cc getShoutString literals differ from the "
        f"frozen Sphinx riddle roots: {sorted(calls)!r}",
    )
    # The failure branch must be the ternary with the monster-specific
    # SpeakDB line gate (mon_msg.empty() -> failure, else acknowledged).
    _require(
        re.search(
            r'getShoutString\(mon_msg\.empty\(\)\s*\?\s*"Sphinx riddle '
            r'failure"\s*:\s*"Sphinx riddle failure acknowledged"\)',
            source, re.DOTALL,
        ) is not None,
        f"{label} transform.cc Sphinx riddle failure ternary shape changed",
    )
    return sorted(calls)


def _glyph_consumer_shape(oid: str, label: str) -> None:
    """Bind the glyph fallback keys to the exact-Git shout.cc construction
    (glyph_key = "'" + [cap-] + base char + "'")."""
    source = hardened.shared._decode_utf8(
        hardened.shared._git_blob_at_oid(
            oid, "crawl-ref/source/shout.cc", label
        ),
        label,
    )
    _require(
        re.search(r'string glyph_key\s*=\s*"\'";', source) is not None,
        f"{label} shout.cc glyph key must start with an apostrophe literal",
    )
    _require(
        re.search(
            r'if \(isaupper\(mchar\)\)\s*\n\s*glyph_key\s*\+=\s*"cap-";',
            source,
        ) is not None,
        f"{label} shout.cc glyph key must add the cap- prefix for upper "
        f"case base chars",
    )
    _require(
        re.search(r'glyph_key\s*\+=\s*mchar;', source) is not None
        and re.search(r'glyph_key\s*\+=\s*"\'";', source) is not None,
        f"{label} shout.cc glyph key must append the base char and closing "
        f"apostrophe",
    )
    _require(
        re.search(r'getShoutString\(glyph_key,\s*suffix\)', source)
        is not None,
        f"{label} shout.cc must query the glyph key with the seen/unseen "
        f"suffix",
    )


def _line_of(match: re.Match[str], source: str) -> int:
    """1-based line number of a regex match in the exact-Git source."""
    return source.count("\n", 0, match.start()) + 1


def _source_anchor(
    source: str, label: str, name: str,
    pattern: re.Pattern[str], snippet: str,
) -> int:
    """Locate one production anchor in exact Git source and prove it is the
    intended site: the snippet must start at the match position (no other
    occurrence with the same shape can substitute for the anchored fact)."""
    match = pattern.search(source)
    _require(match is not None,
             f"{label} cannot find {name} in exact Git source")
    _require(source.startswith(snippet, match.start()),
             f"{label} {name} snippet shape changed")
    return _line_of(match, source)


def _producer_consumer_facts(oid: str, label: str) -> dict[str, str]:
    """Mechanically derive the five producer/consumer evidence anchors from
    the exact Git sources and require them to equal the frozen values:

    - loader: the ``TextDB("shout", "database/", ...)`` initializer line
      in database.cc (the ShoutDB producer);
    - shout_consumer: the first ``getShoutString(key, suffix)`` lookup of
      shout.cc::monster_shout (the _shout_key query);
    - riddle_consumer: the transform.cc Sphinx riddle call site;
    - insult_postprocessing: the mon-util.cc::_get_species_insult
      definition;
    - speakdb_double_load: the ``"insult.txt"`` literal inside the
      database.cc ``TextDB("speak", ...)`` initializer (SpeakDB index 4).

    Every anchor is line-derived and snippet-checked, so a moved or forged
    site cannot satisfy the ledger comparison."""
    database = hardened.shared._decode_utf8(
        hardened.shared._git_blob_at_oid(
            oid, "crawl-ref/source/database.cc", label),
        label,
    )
    shout = hardened.shared._decode_utf8(
        hardened.shared._git_blob_at_oid(
            oid, "crawl-ref/source/shout.cc", label),
        label,
    )
    transform = hardened.shared._decode_utf8(
        hardened.shared._git_blob_at_oid(
            oid, "crawl-ref/source/transform.cc", label),
        label,
    )
    monutil = hardened.shared._decode_utf8(
        hardened.shared._git_blob_at_oid(
            oid, "crawl-ref/source/mon-util.cc", label),
        label,
    )
    loader_match = re.search(
        r'TextDB\s*\(\s*"shout"\s*,\s*"database/"', database)
    _require(loader_match is not None,
             f"{label} cannot find the ShoutDB initializer")
    loader_line = _line_of(loader_match, database)
    _require(
        database.startswith('TextDB("shout", "database/",',
                            loader_match.start()),
        f"{label} ShoutDB initializer snippet shape changed",
    )
    _require(
        _shoutdb_source_manifest(oid, label)[:1] == ["database/shout.txt"],
        f"{label} ShoutDB initializer must load shout.txt first",
    )
    shout_consumer = _source_anchor(
        shout, label, "shout.cc::monster_shout getShoutString lookup",
        re.compile(r'getShoutString\(key,\s*suffix\)'),
        "getShoutString(key, suffix)",
    )
    riddle_consumer = _source_anchor(
        transform, label, "transform.cc Sphinx riddle call",
        re.compile(r'getShoutString\("Sphinx riddle success"\)'),
        'getShoutString("Sphinx riddle success")',
    )
    insult_postprocessing = _source_anchor(
        monutil, label, "mon-util.cc _get_species_insult definition",
        re.compile(r'static\s+string\s+_get_species_insult\s*\('),
        "static string _get_species_insult(",
    )
    speakdb = re.search(r'TextDB\s*\(\s*"speak"\s*,\s*"database/"',
                        database)
    _require(speakdb is not None,
             f"{label} cannot find the SpeakDB initializer")
    _require(
        database.startswith('TextDB("speak", "database/",',
                            speakdb.start()),
        f"{label} SpeakDB initializer snippet shape changed",
    )
    tail = database[speakdb.end():]
    following = re.search(r'TextDB\s*\(', tail)
    block_end = speakdb.end() + following.start() if following \
        else len(database)
    block = database[speakdb.start():block_end]
    insult_literal = re.search(r'"insult\.txt"', block)
    _require(insult_literal is not None,
             f"{label} SpeakDB initializer must load insult.txt")
    insult_abs = speakdb.start() + insult_literal.start()
    speakdb_double_load = database.count("\n", 0, insult_abs) + 1
    facts = {
        "loader": f"crawl-ref/source/database.cc:{loader_line}",
        "shout_consumer": f"crawl-ref/source/shout.cc:{shout_consumer}",
        "riddle_consumer":
            f"crawl-ref/source/transform.cc:{riddle_consumer}",
        "insult_postprocessing":
            f"crawl-ref/source/mon-util.cc:{insult_postprocessing}",
        "speakdb_double_load":
            f"crawl-ref/source/database.cc:{speakdb_double_load}",
    }
    _require(
        facts == FROZEN_PRODUCER_CONSUMER,
        f"{label} producer/consumer anchors drifted from the frozen "
        f"facts: {facts!r}",
    )
    return facts


def _card_producer_consumer(
    entry: dict[str, Any], facts: dict[str, str],
) -> dict[str, str]:
    """The applicable producer/consumer evidence for one card, per
    lifecycle: sphinx-driven keys cite the transform.cc riddle consumer,
    monster_shout-driven keys cite the shout.cc lookup, SpeakDB-only keys
    cite the species-insult post-processing path, and the legacy AXED_MON
    key has no runtime consumer (only the ShoutDB loader fact applies).
    Every card keeps the ShoutDB loader producer fact."""
    lifecycle = entry["lifecycle"]
    if lifecycle == "direct-production-root":
        anchors = (("riddle_consumer",)
                   if entry["key"] in SPHINX_RIDDLE_KEYS
                   else ("shout_consumer",))
    elif lifecycle == "recursive-shoutdb-fragment":
        anchors = (("riddle_consumer",)
                   if entry["key"] in FRAGMENT_KEYS - {"imp"}
                   else ("shout_consumer",))
    elif lifecycle == "legacy-axed-monster":
        anchors = ()
    elif lifecycle == "recursive-shoutdb-insult":
        anchors = ("shout_consumer", "speakdb_double_load")
    else:  # speakdb-postprocessing-insult
        anchors = ("insult_postprocessing", "speakdb_double_load")
    return {"loader": facts["loader"],
            **{anchor: facts[anchor] for anchor in anchors}}


def _axed_monster_names(oid: str, label: str) -> list[str]:
    """DB names of AXED_MON entries in the exact-Git mon-gen header.

    Axed monsters keep their DB names in the generated mon-data.h header
    (``AXED_MON(MONS_X, "name")``) but have no live monster type, so no
    ``mons_type_name(DESC_DBNAME)`` call can produce them; a shout.txt key
    that matches an axed name is a legacy identity with no producer."""
    source = hardened.shared._decode_utf8(
        hardened.shared._git_blob_at_oid(
            oid, "crawl-ref/source/util/mon-gen/header.txt", label
        ),
        label,
    )
    names = re.findall(r'AXED_MON\(\s*MONS_\w+\s*,\s*"([^"]+)"\s*\)',
                       source)
    _require(bool(names), f"{label} header.txt has no AXED_MON entries")
    _require(all(bool(name) for name in names),
             f"{label} has an empty AXED_MON name")
    return sorted(names)


def _derivable_root_facts(
    oid: str, label: str,
) -> dict[str, Any]:
    """Every shout.txt key the production consumer can query directly,
    derived from the exact-Git producers.

    The default-region keys are the suffix materializations of the 26
    default_msg_keys (``key + " seen"/" unseen"`` then bare ``key``,
    mirroring database.cc::_getWeightedSelection) that exist in the file;
    ghost keys are ``<job> player ghost`` for every job YAML name plus the
    ``player ghost`` monster DB name; monster keys are the mons YAML names
    in the file; glyph keys match the consumer's ``'x'``/``'cap-X'`` shape;
    the sphinx roots are the transform.cc literals."""
    default_keys = _shoutcc_default_keys(oid, label)
    _transformcc_sphinx_roots(oid, label)
    _glyph_consumer_shape(oid, label)
    monsters = _monster_producers(oid, label)
    jobs = _job_producers(oid, label)
    axed = _axed_monster_names(oid, label)
    return {
        "default_keys": default_keys,
        "monsters": monsters,
        "jobs": jobs,
        "axed": axed,
    }


def _definition_lines(source: str, label: str) -> dict[str, int]:
    """Source line of the first definition of every canonical key of one
    source file, via the production parse layer."""
    try:
        definitions = hardened.shared.parse_db_keys(source, label)
    except SystemExit as exc:
        raise InventoryError(f"{label} TextDB parse failed: {exc}") from exc
    lines: dict[str, int] = {}
    for definition in definitions:
        canonical = hardened.shared.lowercase_string(definition.raw_key)
        _require(canonical not in lines,
                 f"{label} duplicate raw key {canonical!r}")
        lines[canonical] = definition.key_line
    return lines


def _read_glossary(path: Path, ref: str | None) -> bytes:
    if ref is None:
        return hardened._read_artifact_bytes(path, "glossary")
    return hardened._candidate_regular_blob(
        ref, hardened._repo_relative_git_path(path, "glossary"), "glossary"
    )


def _source_rows(
    artifact: dict[str, Any], directory: str, label: str,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Identity rows of one language: every dump entry whose source history
    touches shout.txt or insult.txt, excluding the sentinel key and the
    title-block artifact (empty bodies can never be selected)."""
    rows: list[dict[str, Any]] = []
    per_file: dict[str, int] = {}
    for entry in artifact["entries"]:
        touching = [
            basename for basename in SOURCE_BASENAMES
            if any(item["source_name"] == f"{directory}{basename}"
                   for item in entry["source_history"])
        ]
        if not touching:
            continue
        _require(
            len(touching) == 1,
            f"{label} key {entry['canonical_key']!r} touches both "
            f"shout.txt and insult.txt",
        )
        basename = touching[0]
        if entry["canonical_key"] in TITLE_BLOCK_ARTIFACTS:
            _require(
                entry["body_empty"] and entry["variants"] == []
                and entry["parse_error"] == "BUG, EMPTY ENTRY",
                f"{label} title-block artifact {entry['canonical_key']!r} "
                f"must be a zero-body entry",
            )
            continue
        if entry["canonical_key"] in SENTINEL_KEYS:
            _require(
                not entry["body_empty"],
                f"{label} sentinel key {entry['canonical_key']!r} must have "
                f"a body",
            )
            continue
        _require(
            not entry["body_empty"] and entry["parse_error"] is None,
            f"{label} identity {entry['canonical_key']!r} has a parse "
            f"error or empty body",
        )
        _require(
            entry["effective_provenance"]["source_name"]
            == f"{directory}{basename}",
            f"{label} key {entry['canonical_key']!r} is not effective from "
            f"{basename}",
        )
        rows.append(entry)
        per_file[basename] = per_file.get(basename, 0) + 1
    _require(
        len(rows) == EXPECTED_IDENTITY_COUNT,
        f"{label} shout-family identity count mismatch: {len(rows)}",
    )
    _require(
        per_file == {
            "shout.txt": EXPECTED_SHOUT_IDENTITY_COUNT,
            "insult.txt": EXPECTED_INSULT_IDENTITY_COUNT,
        },
        f"{label} per-file identity counts differ: {per_file!r}",
    )
    keys = [row["canonical_key"] for row in rows]
    _require(len(set(keys)) == len(keys), f"{label} duplicate identity key")
    # The localized directory scan loads every zh/*.txt file into each DB;
    # monspeak.txt legally defines seven shout-family keys too, so the
    # effective shout.txt definitions carry zh/monspeak.txt in their source
    # history (DBM_REPLACE keeps the shout.txt definition, which loads
    # later in the sorted scan).  The per-language override facts are
    # frozen; the EN manifest (shout.txt/insult.txt only) has none.
    overridden = {
        row["canonical_key"] for row in rows
        if len(row["source_history"]) > 1
    }
    expected_overridden = (
        EXPECTED_OVERRIDDEN_KEYS["english"]
        if directory == "database/"
        else EXPECTED_OVERRIDDEN_KEYS["chinese"]
    )
    _require(
        overridden == expected_overridden,
        f"{label} overridden shout-family keys differ: "
        f"{sorted(overridden)!r}",
    )
    for row in rows:
        if len(row["source_history"]) > 1:
            basename = next(
                basename for basename in SOURCE_BASENAMES
                if any(item["source_name"] == f"{directory}{basename}"
                       for item in row["source_history"])
            )
            extra = {
                item["source_name"] for item in row["source_history"]
            } - {f"{directory}{basename}"}
            _require(
                extra == {f"{directory}monspeak.txt"},
                f"{label} key {row['canonical_key']!r} has unexpected "
                f"override sources {sorted(extra)!r}",
            )
    return sorted(rows, key=lambda entry: entry["canonical_key"]), per_file


def _variant(raw: dict[str, Any]) -> dict[str, Any]:
    text = raw["raw_pattern"]
    return {
        "variant_ordinal": raw["locator"]["variant_ordinal"],
        "weight": raw["weight"],
        "text": text,
        "runtime_tokens": hardened._runtime_tokens(text),
        "random_site_counts": hardened._random_site_counts(text),
        "lua_site_count": len(hardened._lua_sites(text)),
    }


def _classify_tokens(
    rows: list[dict[str, Any]], all_effective_keys: set[str],
) -> dict[str, Any]:
    key_set = {row["canonical_key"].lower() for row in rows}
    recursive: dict[str, list[dict[str, Any]]] = {key: [] for key in key_set}
    fragment_sites: list[dict[str, Any]] = []
    postprocess_sites: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    edges: dict[str, set[str]] = {key: set() for key in key_set}
    for row in rows:
        source = row["canonical_key"].lower()
        for raw in row["variants"]:
            ordinal = raw["locator"]["variant_ordinal"]
            for token in hardened._runtime_tokens(raw["raw_pattern"]):
                canonical = token[1:-1].lower()
                site = {"key": source, "variant_ordinal": ordinal,
                        "token": token}
                if canonical in key_set:
                    edges[source].add(canonical)
                    recursive[canonical].append(site)
                    if canonical in FRAGMENT_KEYS:
                        fragment_sites.append(site)
                elif canonical in POSTPROCESS_TOKENS:
                    postprocess_sites.append(site)
                else:
                    unresolved.append(site)
    _require(
        {site["token"][1:-1].lower() for site in fragment_sites}
        == FRAGMENT_KEYS,
        "frozen fragment token set differs from the four riddle fragments",
    )
    return {
        "edges": {key: sorted(value) for key, value in sorted(edges.items())},
        "references": {
            key: sorted(value,
                        key=lambda item: (item["key"], item["variant_ordinal"],
                                          item["token"]))
            for key, value in sorted(recursive.items())
        },
        "fragment_sites": sorted(
            fragment_sites,
            key=lambda item: (item["key"], item["variant_ordinal"], item["token"]),
        ),
        "postprocess_sites": sorted(
            postprocess_sites,
            key=lambda item: (item["key"], item["variant_ordinal"], item["token"]),
        ),
        "unresolved": sorted(
            unresolved,
            key=lambda item: (item["key"], item["variant_ordinal"], item["token"]),
        ),
    }


def _reachability(
    edges: dict[str, list[str]], seeds: tuple[str, ...],
) -> dict[str, Any]:
    reached = set(seeds)
    queue: deque[tuple[str, tuple[str, ...]]] = deque(
        (key, (key,)) for key in sorted(seeds)
    )
    witnesses: dict[str, list[str]] = {}
    while queue:
        source, path = queue.popleft()
        for target in sorted(edges.get(source, ())):
            if target in reached:
                continue
            reached.add(target)
            next_path = (*path, target)
            witnesses[target] = list(next_path)
            queue.append((target, next_path))
    return {
        "reachable": sorted(reached),
        "witnesses": {key: witnesses[key] for key in sorted(witnesses)},
    }


def _classify_keys(
    scoped_keys: set[str], shout_rows: list[dict[str, Any]],
    insult_rows: list[dict[str, Any]], derivable: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    """Every identity key must be exactly one of:

    - a direct production root (default-region keys including the suffix
      materializations, ghost keys, monster keys, glyph keys, sphinx roots),
    - a recursive fragment (the four _riddle_* keys),
    - a ShoutDB-recursion insult key (reached by the @token@ walk),
    - a SpeakDB-post-processing insult key (the 16 species keys),
    - or the sentinel/artifact keys already excluded from the identity set.

    The default-region set is derived from the 26 exact-Git default keys
    and the production suffix mechanism; ghost/monster roots from the
    exact-Git YAML producers; glyph roots from the file keys matching the
    consumer glyph shape; sphinx roots from the exact-Git transform.cc
    literals.  Anything else fails closed."""
    default_keys = [key.lower() for key in derivable["default_keys"]]
    monsters = set(derivable["monsters"])
    jobs = set(derivable["jobs"])
    axed = set(derivable["axed"])

    def present(*candidates: str) -> set[str]:
        return {candidate for candidate in candidates
                if candidate in scoped_keys}

    default_region: set[str] = set()
    for key in default_keys:
        default_region.update(
            present(key, f"{key} seen", f"{key} unseen")
        )
    ghost_keys = present("player ghost")
    ghost_keys.update(
        f"{job} player ghost" for job in jobs
        if f"{job} player ghost" in scoped_keys
    )
    monster_keys = present(*(monsters & scoped_keys))
    monster_keys -= ghost_keys
    glyph_keys = {key for key in scoped_keys if _GLYPH_KEY_RE.match(key)}
    sphinx_keys = present(*(sorted(SPHINX_RIDDLE_KEYS)))
    legacy_keys = present(*(axed & scoped_keys))
    roots = (default_region | ghost_keys | monster_keys
             | glyph_keys | sphinx_keys)

    sentinel_in_file = scoped_keys & SENTINEL_KEYS
    _require(
        sentinel_in_file == SENTINEL_KEYS,
        f"{label} sentinel key set must be exactly {sorted(SENTINEL_KEYS)!r}",
    )
    _require(
        not (scoped_keys & RUNTIME_SENTINEL_VALUES),
        f"{label} runtime sentinel values must never be ShoutDB keys",
    )
    artifacts = scoped_keys & TITLE_BLOCK_ARTIFACTS
    identity_keys = scoped_keys - sentinel_in_file - artifacts
    _require(
        len(identity_keys) == EXPECTED_IDENTITY_COUNT,
        f"{label} identity key count mismatch after sentinel/artifact "
        f"exclusion",
    )

    fragments = identity_keys & FRAGMENT_KEYS
    _require(
        fragments == FRAGMENT_KEYS,
        f"{label} fragment keys differ: {sorted(fragments ^ FRAGMENT_KEYS)!r}",
    )
    _require(
        legacy_keys == EXPECTED_LEGACY_KEYS,
        f"{label} legacy AXED_MON keys differ: {sorted(legacy_keys)!r}",
    )
    insult_keys = {row["canonical_key"].lower() for row in insult_rows}
    shout_recursion_insult = insult_keys - SPEAKDB_POSTPROCESS_KEYS
    _require(
        len(shout_recursion_insult) == 20,
        f"{label} ShoutDB-recursion insult key count mismatch: "
        f"{len(shout_recursion_insult)}",
    )
    speakdb_only = insult_keys & SPEAKDB_POSTPROCESS_KEYS
    _require(
        speakdb_only == SPEAKDB_POSTPROCESS_KEYS,
        f"{label} SpeakDB post-processing insult keys differ: "
        f"{sorted(speakdb_only ^ SPEAKDB_POSTPROCESS_KEYS)!r}",
    )

    classified = (roots | fragments | legacy_keys
                  | shout_recursion_insult | speakdb_only)
    _require(
        classified == identity_keys,
        f"{label} keys are neither derivable production roots nor "
        f"recursive/SpeakDB/legacy non-roots: "
        f"{sorted(identity_keys - classified)!r}; "
        f"derived roots missing from the file: "
        f"{sorted(classified - identity_keys)!r}",
    )
    _require(
        len(roots) == 85,
        f"{label} derived root key count mismatch: {len(roots)}",
    )
    _require(
        glyph_keys == EXPECTED_GLYPH_KEYS,
        f"{label} glyph keys differ: {sorted(glyph_keys)!r}",
    )
    _require(
        sphinx_keys == SPHINX_RIDDLE_KEYS,
        f"{label} sphinx roots differ: {sorted(sphinx_keys)!r}",
    )
    _require(
        len(ghost_keys) == 21,
        f"{label} ghost key count mismatch: {len(ghost_keys)}",
    )
    _require(
        len(monster_keys) == 7,
        f"{label} live monster key count mismatch: {len(monster_keys)}",
    )
    for key in sorted(roots):
        _require(
            key in scoped_keys,
            f"{label} derived root {key!r} is not a shout.txt key",
        )
    return {
        "roots": roots,
        "default_region": default_region,
        "ghost_keys": ghost_keys,
        "monster_keys": monster_keys,
        "glyph_keys": glyph_keys,
        "sphinx_keys": sphinx_keys,
        "fragments": fragments,
        "legacy_keys": legacy_keys,
        "shout_recursion_insult": shout_recursion_insult,
        "speakdb_only": speakdb_only,
        "sentinel_in_file": sentinel_in_file,
        "artifacts": artifacts,
    }


def _dataset(
    artifact: dict[str, Any], raw: bytes, directory: str, label: str,
    role: str, derivable: dict[str, Any],
    sentinel_baseline: dict[str, Any] | None = None,
    expected_dump_variants: dict[str, int] | None = None,
) -> dict[str, Any]:
    # Sentinel integrity is role-independent: _source_rows deliberately
    # removes the __buggy sentinel from the identity rows and the 124-card
    # review ledger never covers it, so the candidate audit must verify the
    # sentinel entry directly against the dump.  The baseline derivation is
    # the only authority for its content: no reviewed commit may change it.
    sentinel_entries = [
        entry for entry in artifact["entries"]
        if entry["canonical_key"] in SENTINEL_KEYS
    ]
    _require(
        len(sentinel_entries) == 1,
        f"{label} dump must contain exactly one sentinel entry",
    )
    sentinel_entry = sentinel_entries[0]
    _require(
        not sentinel_entry["body_empty"]
        and sentinel_entry["parse_error"] is None,
        f"{label} sentinel entry must have a valid body",
    )
    expected_sentinel = (EXPECTED_SENTINEL_VARIANTS["english"]
                         if directory == "database/"
                         else EXPECTED_SENTINEL_VARIANTS["chinese"])
    _require(
        len(sentinel_entry["variants"]) == expected_sentinel,
        f"{label} sentinel variant count mismatch: "
        f"{len(sentinel_entry['variants'])}",
    )
    if role == "candidate":
        _require(
            sentinel_baseline is not None,
            f"{label} candidate audit requires the baseline sentinel entry",
        )
        _require(
            sentinel_entry["raw_body"] == sentinel_baseline["raw_body"]
            and sentinel_entry["variants"]
            == sentinel_baseline["variants"],
            f"{label} sentinel content differs from the baseline derivation",
        )
    family_sources = {f"{directory}{basename}"
                      for basename in SOURCE_BASENAMES}
    scoped_keys = {
        entry["canonical_key"].lower() for entry in artifact["entries"]
        if any(item["source_name"] in family_sources
               for item in entry["source_history"])
    }
    # Runtime sentinel values are checked in the canonical (lowercase) key
    # space before the identity-count gate: an added __DEFAULT/__NEXT/__NONE
    # key must fail this guard specifically, not be swallowed by the frozen
    # identity count.
    _require(
        not (scoped_keys & RUNTIME_SENTINEL_VALUES),
        f"{label} runtime sentinel values must never be ShoutDB keys",
    )
    rows, per_file = _source_rows(artifact, directory, label)
    shout_rows = [row for row in rows
                  if any(item["source_name"] == f"{directory}shout.txt"
                         for item in row["source_history"])]
    insult_rows = [row for row in rows
                   if any(item["source_name"] == f"{directory}insult.txt"
                          for item in row["source_history"])]
    _require(
        len(shout_rows) + len(insult_rows) == len(rows),
        f"{label} identity rows must be exactly shout.txt or insult.txt",
    )
    classified = _classify_keys(scoped_keys, shout_rows, insult_rows,
                                derivable, label)
    token_facts = _classify_tokens(rows, scoped_keys)
    # Full closure proof: every non-root identity is reachable from the
    # direct root set through the ShoutDB @token@ walk.  The legacy axed
    # key is exempt by definition (no live producer, no inbound reference).
    full_reachability = _reachability(token_facts["edges"],
                                      tuple(sorted(classified["roots"])))
    expected_full_reached = (
        classified["roots"] | FRAGMENT_KEYS
        | classified["shout_recursion_insult"]
    )
    _require(
        set(full_reachability["reachable"]) == expected_full_reached,
        f"{label} full-root closure differs: "
        f"{sorted(set(full_reachability['reachable']) ^ expected_full_reached)!r}",
    )
    _require(
        FRAGMENT_KEYS <= set(full_reachability["reachable"]),
        f"{label} riddle/imp fragments are not reachable from the roots",
    )
    _require(
        classified["shout_recursion_insult"]
        <= set(full_reachability["reachable"]),
        f"{label} demon/imp taunt recursion chain is not reachable "
        f"from the roots",
    )
    _require(
        not (set(full_reachability["reachable"]) & classified["speakdb_only"]),
        f"{label} SpeakDB-only insult keys must not be ShoutDB-reachable",
    )
    _require(
        not (set(full_reachability["reachable"]) & classified["legacy_keys"]),
        f"{label} legacy AXED_MON key must not be ShoutDB-reachable",
    )
    # Seed-driven sub-closure (26 defaults + sphinx + glyph): the riddle
    # fragments and the demon-taunt insult chain; the imp chain is driven
    # by the monster roots and must not be seed-reachable.
    seed_reachability = _reachability(token_facts["edges"], CLOSURE_SEEDS)
    seed_non_roots = (
        set(seed_reachability["reachable"]) - set(CLOSURE_SEEDS)
    )
    expected_seed_non_roots = (
        FRAGMENT_KEYS - MONSTER_DRIVEN_NON_ROOTS
        | classified["shout_recursion_insult"] - MONSTER_DRIVEN_NON_ROOTS
    )
    _require(
        seed_non_roots == expected_seed_non_roots,
        f"{label} seed-driven closure differs: "
        f"{sorted(seed_non_roots ^ expected_seed_non_roots)!r}",
    )
    _require(
        MONSTER_DRIVEN_NON_ROOTS <= (
            FRAGMENT_KEYS | classified["shout_recursion_insult"]
        ),
        f"{label} monster-driven non-roots must be fragments or insult keys",
    )
    reachability = {
        "full": full_reachability,
        "seeds": seed_reachability,
        "seed_non_roots": sorted(seed_non_roots),
        "monster_driven_non_roots": sorted(MONSTER_DRIVEN_NON_ROOTS),
    }

    sources_by_name = {source["source_name"]: source
                       for source in artifact["sources"]}
    entries = []
    for row in rows:
        key = row["canonical_key"]
        basename = row["effective_provenance"]["source_name"]\
            .rsplit("/", 1)[-1]
        _require(
            basename in SOURCE_BASENAMES,
            f"{label} key {key!r} must be effective from the shout family",
        )
        source_snapshot = sources_by_name[
            f"{directory}{basename}"
        ]
        lines = _definition_lines(source_snapshot["normalized_utf8"],
                                  f"{label} {basename}")
        entries.append({
            "key": key,
            "source_basename": basename,
            "definition_ordinal":
                row["effective_provenance"]["definition_ordinal"],
            "source_line": lines[key],
            "source_history_length": len(row["source_history"]),
            "variants": [_variant(variant) for variant in row["variants"]],
        })
    total = sum(len(entry["variants"]) for entry in entries)
    random_sites = sum(
        len(variant["random_site_counts"])
        for entry in entries for variant in entry["variants"]
    )
    lua_sites = sum(
        variant["lua_site_count"]
        for entry in entries for variant in entry["variants"]
    )
    per_file_variants = {
        basename: sum(
            len(entry["variants"]) for entry in entries
            if entry["source_basename"] == basename
        )
        for basename in SOURCE_BASENAMES
    }
    # Dump-level totals include the __buggy sentinel variant (the zero-body
    # title artifact contributes nothing) and are role-aware: the baseline
    # keeps the frozen 119/119 shout.txt and 557/532 insult.txt shape, while
    # the candidate audit requires the approved aligned totals (mechanically
    # derived from the review ledger proposals / the baseline EN facts), so
    # the completed reviewed candidate is not rejected against the stale
    # baseline ZH count.  The one-variant sentinel comparison above stays
    # independent of role.
    dump_variants = {
        basename: sum(
            len(entry["variants"]) for entry in artifact["entries"]
            if any(item["source_name"] == f"{directory}{basename}"
                   for item in entry["source_history"])
        )
        for basename in SOURCE_BASENAMES
    }
    if role == "candidate":
        _require(
            expected_dump_variants is not None,
            f"{label} candidate audit requires the approved dump totals",
        )
        _require(
            set(expected_dump_variants) == {"shout.txt", "insult.txt"},
            f"{label} approved dump totals must cover both source files",
        )
        expected = dict(expected_dump_variants)
    else:
        expected = {
            "shout.txt": (EXPECTED_DUMP_SHOUT_EN_VARIANTS
                          if directory == "database/"
                          else EXPECTED_DUMP_SHOUT_ZH_VARIANTS),
            "insult.txt": (EXPECTED_INSULT_EN_VARIANTS
                           if directory == "database/"
                           else EXPECTED_INSULT_ZH_VARIANTS),
        }
    _require(dump_variants == expected,
             f"{label} dump-level variant totals differ: "
             f"{dump_variants!r}")
    if role == "baseline":
        expected_variants = {
            "shout.txt": (EXPECTED_SHOUT_EN_VARIANTS
                          if directory == "database/"
                          else EXPECTED_SHOUT_ZH_VARIANTS),
            "insult.txt": (EXPECTED_INSULT_EN_VARIANTS
                           if directory == "database/"
                           else EXPECTED_INSULT_ZH_VARIANTS),
        }
        _require(per_file_variants == expected_variants,
                 f"{label} baseline variant count mismatch: "
                 f"{per_file_variants!r}")
        expected_random = (EXPECTED_EN_RANDOM_SITES
                           if directory == "database/"
                           else EXPECTED_ZH_RANDOM_SITES)
        _require(random_sites == expected_random,
                 f"{label} baseline random-site count mismatch")
        expected_lua = (EXPECTED_EN_LUA_SITES
                        if directory == "database/"
                        else EXPECTED_ZH_LUA_SITES)
        _require(lua_sites == expected_lua,
                 f"{label} baseline Lua-site count mismatch")
    source_snapshot = sources_by_name[f"{directory}shout.txt"]
    return {
        "artifact_sha256": _sha256(raw),
        "source_name": f"{directory}shout.txt",
        "source_sha256": _sha256(
            source_snapshot["normalized_utf8"].encode("utf-8")
        ),
        "entries": entries,
        "token_facts": token_facts,
        "reachability": reachability,
        "variant_count": total,
        "per_file_variant_counts": per_file_variants,
        "random_site_count": random_sites,
        "lua_site_count": lua_sites,
        "identity_count": len(entries),
        "per_file_identity_counts": per_file,
        "root_key_count": len(classified["roots"]),
        "root_keys": sorted(classified["roots"]),
        "default_region_keys": sorted(classified["default_region"]),
        "ghost_keys": sorted(classified["ghost_keys"]),
        "monster_keys": sorted(classified["monster_keys"]),
        "glyph_keys": sorted(classified["glyph_keys"]),
        "sphinx_keys": sorted(classified["sphinx_keys"]),
        "fragment_keys": sorted(classified["fragments"]),
        "legacy_keys": sorted(classified["legacy_keys"]),
        "shout_recursion_insult_keys":
            sorted(classified["shout_recursion_insult"]),
        "speakdb_postprocess_keys": sorted(classified["speakdb_only"]),
        "sentinel_keys": sorted(classified["sentinel_in_file"]),
        "title_block_artifacts": sorted(classified["artifacts"]),
        "producer_facts": {
            "default_key_count": len(derivable["default_keys"]),
            "monster_producer_count": len(derivable["monsters"]),
            "job_producer_count": len(derivable["jobs"]),
            "axed_monster_count": len(derivable["axed"]),
        },
    }


def _hashed_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    """The byte-stable inventory view of one dataset.

    The derivation internals (root/key classification and producer facts)
    are classification evidence, not inventory facts: the frozen review
    ledger binds ``inventory_sha256`` to the historical schema, so the
    hashed core must stay byte-identical while the classification itself is
    production-derived."""
    return {key: value for key, value in dataset.items()
            if key not in {"entries", "root_keys", "default_region_keys",
                           "ghost_keys", "monster_keys", "glyph_keys",
                           "sphinx_keys", "fragment_keys", "legacy_keys",
                           "shout_recursion_insult_keys",
                           "speakdb_postprocess_keys", "sentinel_keys",
                           "title_block_artifacts", "producer_facts"}}


def _derived_sentinel_entry(
    oid: str, directory: str, label: str,
) -> dict[str, Any]:
    """The exact-Git derived ``__buggy`` entry of one language directory.

    The review ledger never covers the sentinel, so every reviewed commit
    must keep it byte-identical to the baseline derivation; the candidate
    audit compares the candidate dump entry against this value."""
    derived = _derive_scoped_shout_dump(oid, directory, label)
    sentinel = [
        entry for entry in derived["entries"]
        if entry["canonical_key"] in SENTINEL_KEYS
    ]
    _require(
        len(sentinel) == 1,
        f"{label} derivation must contain exactly one sentinel entry",
    )
    return sentinel[0]


def _load_dataset(
    ref: str, path: Path, directory: str, label: str, role: str,
    sentinel_baseline: dict[str, Any] | None = None,
    expected_dump_variants: dict[str, int] | None = None,
) -> dict[str, Any]:
    hardened.shared._validate_oid(ref, label)
    _require_regular_shout_git_sources(ref, directory, label)
    artifact, raw = hardened._load_dump_safe(
        path, label, directory, expected_database="shout"
    )
    derived = _derive_scoped_shout_dump(ref, directory, label)
    _require_scoped_derivation(artifact, derived, label)
    if directory == "database/":
        _require_speakdb_insult_parity(artifact, ref, label)
    derivable = _derivable_root_facts(ref, label)
    return _dataset(artifact, raw, directory, label, role, derivable,
                    sentinel_baseline=sentinel_baseline,
                    expected_dump_variants=expected_dump_variants)


def _pair_entries(
    en: dict[str, Any], zh: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, list[int]]]:
    en_by_key = {entry["key"]: entry for entry in en["entries"]}
    zh_by_key = {entry["key"]: entry for entry in zh["entries"]}
    _require(en_by_key.keys() == zh_by_key.keys(),
             "shout-family EN/ZH key sets differ")
    entries = []
    asymmetry: dict[str, list[int]] = {}
    for key in sorted(en_by_key):
        en_entry, zh_entry = en_by_key[key], zh_by_key[key]
        counts = (len(en_entry["variants"]), len(zh_entry["variants"]))
        if counts[0] != counts[1]:
            asymmetry[key] = list(counts)
        lifecycle = _lifecycle_for(key, en)
        entries.append({
            "identity": f"{en_entry['source_basename'].split('.')[0]}:{key}",
            "key": key,
            "source_basename": en_entry["source_basename"],
            "lifecycle": lifecycle,
            "dependency_group": _group_for(key, en_entry["source_basename"]),
            "english_definition_ordinal": en_entry["definition_ordinal"],
            "chinese_definition_ordinal": zh_entry["definition_ordinal"],
            "english_source_line": en_entry["source_line"],
            "chinese_source_line": zh_entry["source_line"],
            "english_variants": en_entry["variants"],
            "chinese_variants": zh_entry["variants"],
            "english_referencing_sites": en["token_facts"]["references"][key],
            "chinese_referencing_sites": zh["token_facts"]["references"][key],
        })
    _require(
        len(asymmetry) == len(EXPECTED_ASYMMETRY)
        and asymmetry == EXPECTED_ASYMMETRY,
        f"baseline asymmetric key facts changed: {asymmetry!r}",
    )
    multiset_drift: set[tuple[str, int]] = set()
    for entry in entries:
        key = entry["key"]
        for ordinal, (en_variant, zh_variant) in enumerate(
            zip(entry["english_variants"], entry["chinese_variants"])
        ):
            if (Counter(en_variant["runtime_tokens"])
                    != Counter(zh_variant["runtime_tokens"])):
                multiset_drift.add((key, ordinal))
    _require(
        multiset_drift == EXPECTED_BASELINE_TOKEN_MULTISET_DRIFT,
        "baseline token-multiset drift facts changed",
    )
    return entries, asymmetry


def _group_for(key: str, basename: str) -> str:
    if basename == "insult.txt":
        if key in SPEAKDB_POSTPROCESS_KEYS:
            return "物种羞辱（SpeakDB 后处理路径）"
        return "恶魔/小鬼嘲讽递归链（ShoutDB）"
    if key in FRAGMENT_KEYS:
        if key == "imp":
            return "递归片段（imp 小鬼共享喊叫）"
        return "斯芬克斯谜语递归片段"
    if key in SPHINX_RIDDLE_KEYS:
        return "斯芬克斯谜语根键"
    if key in SENTINEL_KEYS:
        return "哨兵键（__BUGGY 回退）"
    if key in EXPECTED_LEGACY_KEYS:
        return "遗留怪物名喊叫键（AXED_MON）"
    if key in DEFAULT_MSG_KEYS or key.startswith("__"):
        return "默认喊叫键（default_msg_keys 与 seen/unseen 后缀）"
    if key.endswith(" player ghost") or key == "player ghost":
        return "玩家鬼魂喊叫（职业名键）"
    if _GLYPH_KEY_RE.match(key):
        return "字形回退键（glyph）"
    return "怪物名喊叫键（DESC_DBNAME）"


def _lifecycle_for(key: str, dataset: dict[str, Any]) -> str:
    if key in dataset["root_keys"]:
        return "direct-production-root"
    if key in dataset["fragment_keys"]:
        return "recursive-shoutdb-fragment"
    if key in dataset["legacy_keys"]:
        return "legacy-axed-monster"
    if key in dataset["shout_recursion_insult_keys"]:
        return "recursive-shoutdb-insult"
    return "speakdb-postprocessing-insult"


def build_inventory(
    baseline_ref: str, english_path: Path, localized_path: Path,
    glossary_path: Path, glossary_ref: str | None = None,
) -> dict[str, Any]:
    en = _load_dataset(baseline_ref, english_path, "database/",
                       "baseline EN", "baseline")
    zh = _load_dataset(baseline_ref, localized_path, "database/zh/",
                       "baseline ZH", "baseline")
    _require(en["token_facts"]["unresolved"]
             == EXPECTED_BASELINE_UNRESOLVED["english"],
             "baseline EN unresolved-token facts changed")
    _require(zh["token_facts"]["unresolved"]
             == EXPECTED_BASELINE_UNRESOLVED["chinese"],
             "baseline ZH unresolved-token facts changed")
    entries, asymmetry = _pair_entries(en, zh)
    scope = {
        "source_basenames": list(SOURCE_BASENAMES),
        "expected_identity_counts": {
            "shout.txt": EXPECTED_SHOUT_IDENTITY_COUNT,
            "insult.txt": EXPECTED_INSULT_IDENTITY_COUNT,
            "total": EXPECTED_IDENTITY_COUNT,
        },
        "root_key_count": en["root_key_count"],
        "root_keys": sorted({entry["key"] for entry in entries
                             if entry["lifecycle"]
                             == "direct-production-root"}),
        "closure_seeds": sorted(CLOSURE_SEEDS),
        "default_msg_keys": list(DEFAULT_MSG_KEYS),
        "sphinx_riddle_keys": sorted(SPHINX_RIDDLE_KEYS),
        "glyph_keys": sorted(EXPECTED_GLYPH_KEYS),
        "fragment_keys": sorted(FRAGMENT_KEYS),
        "monster_driven_non_roots": sorted(MONSTER_DRIVEN_NON_ROOTS),
        "legacy_keys": en["legacy_keys"],
        "shoutdb_recursion_insult_keys": en["shout_recursion_insult_keys"],
        "speakdb_postprocess_keys": en["speakdb_postprocess_keys"],
        "sentinel_keys": en["sentinel_keys"],
        "runtime_sentinel_values": sorted(RUNTIME_SENTINEL_VALUES),
        "title_block_artifacts": {
            "english": en["title_block_artifacts"],
            "chinese": zh["title_block_artifacts"],
        },
        "overridden_keys": {
            "english": sorted(EXPECTED_OVERRIDDEN_KEYS["english"]),
            "chinese": sorted(EXPECTED_OVERRIDDEN_KEYS["chinese"]),
        },
        "provenance": {
            "shoutdb": {
                "shout.txt": 0,
                "insult.txt": 1,
            },
            "speakdb": {
                "insult.txt": _speakdb_insult_provenance(
                    baseline_ref, "baseline provenance"),
            },
        },
        "producer_consumer": _producer_consumer_facts(
            baseline_ref, "baseline producer/consumer"),
        "postprocess_tokens": sorted(POSTPROCESS_TOKENS),
        "baseline_variant_counts": {
            "english": en["per_file_variant_counts"],
            "chinese": zh["per_file_variant_counts"],
        },
        "baseline_dump_variant_totals": {
            "english": {
                "shout.txt": EXPECTED_DUMP_SHOUT_EN_VARIANTS,
                "insult.txt": EXPECTED_INSULT_EN_VARIANTS,
            },
            "chinese": {
                "shout.txt": EXPECTED_DUMP_SHOUT_ZH_VARIANTS,
                "insult.txt": EXPECTED_INSULT_ZH_VARIANTS,
            },
        },
        "sentinel_key_variant_counts": dict(EXPECTED_SENTINEL_VARIANTS),
        "baseline_asymmetry": {
            key: asymmetry[key] for key in sorted(asymmetry)
        },
        "baseline_token_multiset_drift": [
            [key, ordinal]
            for key, ordinal in sorted(EXPECTED_BASELINE_TOKEN_MULTISET_DRIFT)
        ],
        "baseline_random_sites": {
            "english": en["random_site_count"],
            "chinese": zh["random_site_count"],
        },
        "baseline_lua_sites": {
            "english": en["lua_site_count"],
            "chinese": zh["lua_site_count"],
        },
    }
    core = {
        "schema_version": SCHEMA_VERSION,
        "baseline_ref": baseline_ref,
        "scope": scope,
        "scope_sha256": _sha256(_canonical_json(scope)),
        "glossary": {
            "path": "docs/glossary.md",
            "sha256": _sha256(_read_glossary(glossary_path, glossary_ref)),
        },
        "dumps": {
            "english": _hashed_dataset(en),
            "localized": _hashed_dataset(zh),
        },
        "entries": entries,
    }
    return {**core, "inventory_sha256": _sha256(_canonical_json(core))}


def _strict_block_from_text(text: str) -> list[dict[str, Any]]:
    _require(text.count(STRICT_BEGIN) == 1,
             "review results require exactly one strict begin marker")
    _require(text.count(STRICT_END) == 1,
             "review results require exactly one strict end marker")
    body = text.split(STRICT_BEGIN, 1)[1].split(STRICT_END, 1)[0].strip()
    match = re.fullmatch(r"```jsonl\s*\n(.*?)\n```", body, re.DOTALL)
    _require(match is not None,
             "strict review evidence must be one fenced jsonl block")
    records = []
    for number, line in enumerate(match.group(1).splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InventoryError(
                f"invalid review JSONL line {number}: {exc}") from exc
        _require(isinstance(value, dict),
                 f"review JSONL line {number} must be an object")
        records.append(value)
    return records


def _strict_block(path: Path) -> list[dict[str, Any]]:
    raw = hardened._read_artifact_bytes(path, "review results")
    try:
        return _strict_block_from_text(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise InventoryError("cannot decode review results") from exc


def _variant_review_shape(variants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{"weight": variant["weight"], "text": variant["text"]}
            for variant in variants]


def _validate_variant_list(value: Any, context: str) -> None:
    _require(isinstance(value, list), f"{context} must be a list")
    for ordinal, variant in enumerate(value):
        _require(isinstance(variant, dict) and set(variant) == VARIANT_FIELDS,
                 f"{context} ordinal {ordinal} fields mismatch")
        _require(isinstance(variant["weight"], int)
                 and not isinstance(variant["weight"], bool)
                 and variant["weight"] > 0,
                 f"{context} ordinal {ordinal} weight mismatch")
        _require(isinstance(variant["text"], str) and bool(variant["text"]),
                 f"{context} ordinal {ordinal} text mismatch")
        hardened._random_site_counts(variant["text"])
        hardened._lua_sites(variant["text"])


def _expected_metadata(
    inventory: dict[str, Any], cards: list[dict[str, Any]],
) -> dict[str, Any]:
    conclusions = [
        card["terminal_conclusion"] for card in cards
        if card["terminal_conclusion"] is not None
    ]
    return {
        "baseline": inventory["baseline_ref"],
        "chinese_production_dump_sha256":
            inventory["dumps"]["localized"]["artifact_sha256"],
        "en_variant_count": sum(
            inventory["scope"]["baseline_variant_counts"]["english"].values()
        ),
        "english_production_dump_sha256":
            inventory["dumps"]["english"]["artifact_sha256"],
        "glossary_sha256": inventory["glossary"]["sha256"],
        "identity_count": EXPECTED_IDENTITY_COUNT,
        "inventory_sha256": inventory["inventory_sha256"],
        "terminal_conclusion_counts": dict(sorted(Counter(conclusions).items())),
        "zh_variant_count": sum(
            inventory["scope"]["baseline_variant_counts"]["chinese"].values()
        ),
    }


def _evidence_locations(entry: dict[str, Any]) -> list[str]:
    """Mechanically derived per-card evidence locations: the EN/ZH
    definition sites plus every recursive reference site from the frozen
    baseline token classification.  The scaffold and the strict validation
    share this derivation, so a forged or incomplete evidence list in the
    ledger cannot pass without matching the derived value verbatim."""
    return [
        f"crawl-ref/source/dat/database/{entry['source_basename']}:"
        f"{entry['english_source_line']}",
        f"crawl-ref/source/dat/database/zh/{entry['source_basename']}:"
        f"{entry['chinese_source_line']}",
        *(f"recursive-ref:{site['key']}:{site['variant_ordinal']}"
          for site in entry["english_referencing_sites"]),
        *(f"recursive-ref-zh:{site['key']}:{site['variant_ordinal']}"
          for site in entry["chinese_referencing_sites"]),
    ]


def validate_results(
    path: Path, inventory: dict[str, Any],
    candidate: dict[str, Any] | None = None,
    records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    records = records if records is not None else _strict_block(path)
    _require(len(records) == EXPECTED_IDENTITY_COUNT + 1,
             "review results require one metadata record and 124 cards")
    metadata, cards = records[0], records[1:]
    _require(set(metadata) == METADATA_FIELDS, "review metadata fields mismatch")
    _require(metadata == _expected_metadata(inventory, cards),
             "review metadata mismatch")
    by_identity = {entry["identity"]: entry for entry in inventory["entries"]}
    _require(len({card.get("identity") for card in cards}) == len(cards),
             "duplicate review identity")
    _require([card.get("identity") for card in cards] == sorted(by_identity),
             "review cards must cover every identity in deterministic order")
    proposals: dict[str, dict[str, Any]] = {}
    for card in cards:
        identity = card["identity"]
        entry = by_identity[identity]
        _require(set(card) == CARD_FIELDS, f"review card {identity} fields mismatch")
        _require(card["key"] == entry["key"], f"review card {identity} key mismatch")
        _require(card["lifecycle"] == entry["lifecycle"],
                 f"review card {identity} lifecycle mismatch")
        _require(card["dependency_group"] == entry["dependency_group"],
                 f"review card {identity} group mismatch")
        current_en = _variant_review_shape(entry["english_variants"])
        current_zh = _variant_review_shape(entry["chinese_variants"])
        _require(card["current_english_variants"] == current_en,
                 f"review card {identity} current EN mismatch")
        _require(card["current_chinese_variants"] == current_zh,
                 f"review card {identity} current ZH mismatch")
        _validate_variant_list(card["proposed_english_variants"],
                               f"review card {identity} proposed EN")
        _validate_variant_list(card["proposed_chinese_variants"],
                               f"review card {identity} proposed ZH")
        conclusion = card["terminal_conclusion"]
        _require(conclusion in CONCLUSIONS,
                 f"review card {identity} conclusion mismatch")
        changed = (card["proposed_english_variants"] != current_en
                   or card["proposed_chinese_variants"] != current_zh)
        _require(changed == (conclusion in {"adjust", "retranslate"}),
                 f"review card {identity} conclusion/change mismatch")
        for field in ("rationale", "display_context", "reentry_trigger"):
            _require(isinstance(card[field], str) and bool(card[field].strip()),
                     f"review card {identity} requires {field}")
        _require(card["confidence"] in CONFIDENCE_LEVELS,
                 f"review card {identity} confidence mismatch")
        _require(isinstance(card["evidence_locations"], list)
                 and card["evidence_locations"],
                 f"review card {identity} requires evidence locations")
        _require(card["evidence_locations"]
                 == _evidence_locations(entry),
                 f"review card {identity} evidence locations mismatch")
        _require(isinstance(card["rejected_alternatives"], list)
                 and card["rejected_alternatives"],
                 f"review card {identity} requires rejected alternatives")
        _require(isinstance(card["producer_consumer"], dict)
                 and card["producer_consumer"],
                 f"review card {identity} requires producer/consumer evidence")
        _require(card["producer_consumer"]
                 == _card_producer_consumer(
                     entry, inventory["scope"]["producer_consumer"]),
                 f"review card {identity} producer/consumer evidence mismatch")
        if conclusion in DEFER_CONCLUSIONS:
            _require(isinstance(card["deferral_owner"], str)
                     and card["deferral_owner"].strip(),
                     f"review card {identity} deferred conclusion requires owner")
            _require(isinstance(card["deferral_reason"], str)
                     and card["deferral_reason"].strip(),
                     f"review card {identity} deferred conclusion requires reason")
        else:
            _require(card["deferral_owner"] is None
                     and card["deferral_reason"] is None,
                     f"review card {identity} non-deferred conclusion "
                     f"forbids deferral fields")
        proposals[entry["key"]] = {
            "english": card["proposed_english_variants"],
            "chinese": card["proposed_chinese_variants"],
        }
    if candidate is not None:
        candidate_by_key = {entry["key"]: entry for entry in candidate["entries"]}
        _require(candidate_by_key.keys() == proposals.keys(),
                 "candidate key set differs from review ledger")
        for key in sorted(proposals):
            actual = candidate_by_key[key]
            _require(_variant_review_shape(actual["english_variants"])
                     == proposals[key]["english"],
                     f"candidate EN drift at {key!r}")
            _require(_variant_review_shape(actual["chinese_variants"])
                     == proposals[key]["chinese"],
                     f"candidate ZH drift at {key!r}")
    return {"metadata": metadata, "cards": cards}


def _pair_candidate(en: dict[str, Any], zh: dict[str, Any]) -> list[dict[str, Any]]:
    en_by_key = {entry["key"]: entry for entry in en["entries"]}
    zh_by_key = {entry["key"]: entry for entry in zh["entries"]}
    _require(en_by_key.keys() == zh_by_key.keys(),
             "candidate EN/ZH key sets differ")
    entries = []
    for key in sorted(en_by_key):
        en_entry, zh_entry = en_by_key[key], zh_by_key[key]
        _require(len(en_entry["variants"]) == len(zh_entry["variants"]),
                 f"candidate variant count differs at {key!r}")
        _require([v["weight"] for v in en_entry["variants"]]
                 == [v["weight"] for v in zh_entry["variants"]],
                 f"candidate weight order differs at {key!r}")
        for ordinal, (en_variant, zh_variant) in enumerate(
            zip(en_entry["variants"], zh_entry["variants"])
        ):
            _require(
                Counter(en_variant["runtime_tokens"])
                == Counter(zh_variant["runtime_tokens"]),
                f"candidate recursive/postprocess token multiset differs at "
                f"{key!r} ordinal {ordinal}",
            )
            _require(
                en_variant["random_site_counts"]
                == zh_variant["random_site_counts"],
                f"candidate random-site topology differs at {key!r} ordinal "
                f"{ordinal}",
            )
            _require(
                en_variant["lua_site_count"] == zh_variant["lua_site_count"],
                f"candidate Lua-site count differs at {key!r} ordinal "
                f"{ordinal}",
            )
        entries.append({
            "identity": f"{en_entry['source_basename'].split('.')[0]}:{key}",
            "key": key,
            "english_variants": en_entry["variants"],
            "chinese_variants": zh_entry["variants"],
        })
    return entries


def _proposal_dump_totals(records: list[dict[str, Any]]) -> dict[str, int]:
    """The approved candidate dump totals, mechanically derived from the
    review ledger: per-file proposed ZH variant totals plus the one
    __buggy sentinel variant of shout.txt (the sentinel is outside the
    ledger but part of the production dump totals)."""
    totals = {"shout.txt": 0, "insult.txt": 0}
    for card in records[1:]:
        basename = ("shout.txt" if card["identity"].startswith("shout:")
                    else "insult.txt")
        totals[basename] += len(card["proposed_chinese_variants"])
    totals["shout.txt"] += EXPECTED_SENTINEL_VARIANTS["chinese"]
    return totals


def add_candidate(
    inventory: dict[str, Any], baseline_ref: str, candidate_ref: str,
    english_path: Path, localized_path: Path,
    expected_dump_variants: dict[str, int] | None = None,
) -> dict[str, Any]:
    hardened.shared._require_candidate_commit(
        baseline_ref, candidate_ref, exact_clean_checkout=True
    )
    if expected_dump_variants is None:
        # Mechanical default from the baseline EN facts (the approved
        # aligned shape: this batch keeps every EN key at the baseline
        # count and aligns ZH to it, so the candidate insult total is the
        # baseline EN insult total and shout.txt adds the sentinel).
        en_counts = inventory["dumps"]["english"]["per_file_variant_counts"]
        expected_dump_variants = {
            "shout.txt": (en_counts["shout.txt"]
                           + EXPECTED_SENTINEL_VARIANTS["english"]),
            "insult.txt": en_counts["insult.txt"],
        }
    en = _load_dataset(
        candidate_ref, english_path, "database/",
        "candidate EN", "candidate",
        sentinel_baseline=_derived_sentinel_entry(
            baseline_ref, "database/", "baseline sentinel EN"
        ),
        expected_dump_variants=expected_dump_variants,
    )
    zh = _load_dataset(
        candidate_ref, localized_path, "database/zh/",
        "candidate ZH", "candidate",
        sentinel_baseline=_derived_sentinel_entry(
            baseline_ref, "database/zh/", "baseline sentinel ZH"
        ),
        expected_dump_variants=expected_dump_variants,
    )
    # The reviewed commit must not move the producer/consumer anchors that
    # the ledger evidence is bound to; the candidate anchors are derived
    # and snippet-checked from the exact candidate Git sources.
    _require(
        _producer_consumer_facts(candidate_ref, "candidate producer/consumer")
        == inventory["scope"]["producer_consumer"],
        "candidate producer/consumer anchors differ from the baseline facts",
    )
    _require(not en["token_facts"]["unresolved"],
             "candidate EN contains unresolved token")
    _require(not zh["token_facts"]["unresolved"],
             "candidate ZH contains unresolved token")
    entries = _pair_candidate(en, zh)
    candidate = {
        "candidate_ref": candidate_ref,
        "dumps": {
            "english": _hashed_dataset(en),
            "localized": _hashed_dataset(zh),
        },
        "entries": entries,
    }
    candidate["candidate_sha256"] = _sha256(_canonical_json(candidate))
    inventory["candidate"] = candidate
    return candidate


def _skeleton_card(
    inventory: dict[str, Any], entry: dict[str, Any],
) -> dict[str, Any]:
    """One empty ledger card bound to the frozen baseline facts.

    The zh-translator phase fills proposed_* variants, terminal_conclusion,
    confidence, rationale and reentry_trigger; the schema is shared with the
    final strict review ledger so the completed file validates unchanged."""
    current_en = _variant_review_shape(entry["english_variants"])
    current_zh = _variant_review_shape(entry["chinese_variants"])
    lifecycle = entry["lifecycle"]
    if lifecycle == "direct-production-root":
        display_context = (
            "shout.cc::monster_shout 直接查询的根键（含 seen/unseen 后缀机制"
            "）；展开后经 do_mon_str_replacements 处理，以声音/视觉频道显示。"
        )
    elif lifecycle == "recursive-shoutdb-fragment":
        display_context = (
            "仅由 Sphinx riddle 根键或 imp 怪物根键闭包递归展开的内部片段；"
            "不能脱离调用点独立解释。"
        )
    elif lifecycle == "legacy-axed-monster":
        display_context = (
            "AXED_MON 遗留键：当前没有怪物类型产生该 DB 名，也没有递归"
            "引用，运行时不可达；仅作为历史遗留翻译保留在账本中。"
        )
    elif lifecycle == "recursive-shoutdb-insult":
        display_context = (
            "仅由 __DEMON_TAUNT/imp 默认键闭包递归展开的 ShoutDB 嘲讽片段；"
            "不能脱离调用点独立解释。"
        )
    else:
        display_context = (
            "仅由 mon-util.cc::_get_species_insult 的 @species_insult_*@ "
            "后处理路径经 SpeakDB 查询；ShoutDB 递归不可达。"
        )
    return {
        "identity": entry["identity"],
        "key": entry["key"],
        "lifecycle": lifecycle,
        "dependency_group": entry["dependency_group"],
        "display_context": display_context,
        "producer_consumer": _card_producer_consumer(
            entry, inventory["scope"]["producer_consumer"]),
        "evidence_locations": _evidence_locations(entry),
        "current_english_variants": current_en,
        "current_chinese_variants": current_zh,
        "proposed_english_variants": None,
        "proposed_chinese_variants": None,
        "terminal_conclusion": None,
        "confidence": None,
        "rationale": "",
        "rejected_alternatives": [],
        "reentry_trigger": "",
        "deferral_owner": None,
        "deferral_reason": None,
    }


def scaffold_results(
    path: Path, inventory: dict[str, Any],
) -> list[dict[str, Any]]:
    """Generate the initial empty strict JSONL ledger (exclusive create).

    Fails closed when the ledger already exists and when any pathname
    component is a symlink, exactly like the decorlines scaffold; the whole
    create-verify-write-publish lifecycle, including rollback of any
    partial write, is owned by the shared decorlines hardened write
    transaction."""
    cards = [_skeleton_card(inventory, entry)
             for entry in inventory["entries"]]
    cards.sort(key=lambda card: card["identity"])
    records = [_expected_metadata(inventory, cards), *cards]
    text = (
        "# Shout/Insult 全量审核结果（Issue #69）\n\n"
        "本文件的严格 JSONL 块是 124 个 frozen identity 的完整审核账本。"
        "每张卡绑定基线 EN/ZH 变体；zh-translator 阶段填写提案、结论与"
        "理由后，候选审计只接受逐字等于提案的提交。\n\n"
        f"{STRICT_BEGIN}\n```jsonl\n"
        + "\n".join(json.dumps(record, ensure_ascii=False, sort_keys=True)
                    for record in records)
        + f"\n```\n{STRICT_END}\n"
    )
    resolved = path.resolve(strict=False)
    _require(resolved == RESULTS_PATH.resolve(strict=False),
             f"scaffold output must be {RESULTS_PATH}")
    decorlines._scaffold_write_transaction(path, text)
    return records


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-ref", required=True)
    parser.add_argument("--english-dump", required=True, type=Path)
    parser.add_argument("--localized-dump", required=True, type=Path)
    parser.add_argument("--inventory-output", required=True, type=Path)
    parser.add_argument("--review-results", type=Path)
    parser.add_argument("--candidate-ref")
    parser.add_argument("--candidate-english-dump", type=Path)
    parser.add_argument("--candidate-localized-dump", type=Path)
    parser.add_argument("--scaffold-output", type=Path)
    parser.add_argument(
        "--glossary", type=Path,
        default=Path(__file__).resolve().parents[2] / "docs/glossary.md",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    candidate_values = (args.candidate_ref, args.candidate_english_dump,
                        args.candidate_localized_dump)
    if any(value is not None for value in candidate_values):
        _require(all(value is not None for value in candidate_values),
                 "candidate ref and both candidate dumps must be supplied together")
        _require(args.review_results is not None,
                 "candidate validation requires review results")
    _require(args.scaffold_output is None
             or (args.review_results is None and args.candidate_ref is None),
             "scaffolding cannot be combined with review/candidate validation")
    records = None
    if args.candidate_ref is not None:
        hardened.shared._require_candidate_commit(
            args.baseline_ref, args.candidate_ref, exact_clean_checkout=True
        )
        ledger = hardened._candidate_regular_blob(
            args.candidate_ref,
            hardened._repo_relative_git_path(args.review_results,
                                             "review results"),
            "review results",
        )
        records = _strict_block_from_text(ledger.decode("utf-8"))
    inventory = build_inventory(
        args.baseline_ref, args.english_dump, args.localized_dump,
        args.glossary,
        glossary_ref=args.candidate_ref if args.candidate_ref else None,
    )
    candidate = None
    if args.scaffold_output is not None:
        scaffold_results(args.scaffold_output, inventory)
    if args.candidate_ref is not None:
        candidate = add_candidate(
            inventory, args.baseline_ref, args.candidate_ref,
            args.candidate_english_dump, args.candidate_localized_dump,
            expected_dump_variants=_proposal_dump_totals(records),
        )
    if args.review_results is not None:
        inventory["review_evidence"] = validate_results(
            args.review_results, inventory, candidate, records=records
        )
    hardened.shared._safe_output(args.inventory_output, inventory)
    return 0


CONCLUSIONS = {
    "keep", "adjust", "retranslate", "defer implementation",
    "defer terminology",
}
DEFER_CONCLUSIONS = {"defer implementation", "defer terminology"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
METADATA_FIELDS = {
    "baseline", "chinese_production_dump_sha256", "en_variant_count",
    "english_production_dump_sha256", "glossary_sha256", "identity_count",
    "inventory_sha256", "terminal_conclusion_counts", "zh_variant_count",
}
CARD_FIELDS = {
    "confidence", "current_chinese_variants", "current_english_variants",
    "deferral_owner", "deferral_reason", "dependency_group",
    "display_context", "evidence_locations", "identity", "key", "lifecycle",
    "producer_consumer", "proposed_chinese_variants",
    "proposed_english_variants", "rationale", "reentry_trigger",
    "rejected_alternatives", "terminal_conclusion",
}
VARIANT_FIELDS = {"text", "weight"}

# Frozen consumer/producer evidence anchors for the ShoutDB loader, the
# shout.cc::monster_shout lookup, the transform.cc Sphinx riddle path and
# the mon-util.cc insult path.  The values are the exact-Git anchor lines
# at the baseline OID; _producer_consumer_facts re-derives every anchor
# from the exact Git sources with snippet checks and must reproduce this
# object verbatim, so a moved initializer/call site fails closed instead
# of silently re-anchoring the ledger evidence.
FROZEN_PRODUCER_CONSUMER = {
    "loader": "crawl-ref/source/database.cc:134",
    "shout_consumer": "crawl-ref/source/shout.cc:176",
    "riddle_consumer": "crawl-ref/source/transform.cc:2541",
    "insult_postprocessing": "crawl-ref/source/mon-util.cc:4275",
    "speakdb_double_load": "crawl-ref/source/database.cc:125",
}

# Frozen baseline token-multiset drift (EN vs ZH at the baseline OID): the
# baseline ZH deliberately rewrites 17 variant bodies with a different token
# multiset (recorded in the scope as baseline_token_multiset_drift); there
# are no pure token-order differences, so the strict candidate gate requires
# the review phase to align every drifted multiset.
EXPECTED_BASELINE_TOKEN_MULTISET_DRIFT: set[tuple[str, int]] = {
    ("'cap-g'", 0),
    ("__cherub seen", 0),
    ("__cherub seen", 1),
    ("__cherub seen", 2),
    ("__cherub seen", 3),
    ("__faint_skitter seen", 0),
    ("__rustle seen", 0),
    ("__skitter seen", 0),
    ("ballistomycete spore", 0),
    ("giant slug", 0),
    ("glowing orange brain", 0),
    ("moth of wrath", 0),
    ("player ghost", 0),
    ("insult mummy adj2", 16),
    ("insult spriggan noun", 0),
    ("insult spriggan noun", 16),
    ("insult vampire adj2", 10),
}
EXPECTED_BASELINE_UNRESOLVED: dict[str, list[dict[str, Any]]] = {
    "english": [],
    "chinese": [],
}


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InventoryError as exc:
        print(f"shout_inventory.py: {exc}", file=sys.stderr)
        raise SystemExit(2)
