#!/usr/bin/env python3
"""Build and audit the Issue #70 monspeak review inventory.

The inventory is derived from production ``textdb-phase0-dump`` artifacts of
the ``speak`` TextDB family scoped to ``database/monspeak.txt`` (SpeakDB
source index 0) and from exact Git source snapshots.  It freezes the 731
English identities (3429 variants) and 733 Chinese identities (3407
variants), the exact 213-key asymmetric list (derived from the baseline
dumps, never copied from prose), the two ZH-only keys (``_jory_rare_`` and
``default 'j'``), the seven shout-family keys whose ZH monspeak definitions
are shadowed by zh/shout.txt in the effective localized merge, the
random-site/Lua-site counts, the complete token classification and a
per-language reachability proof from the consumed production root keys.

``@to_foe@``/``@at_foe@`` (and their ``@to_foe/<alt>@``/``@at_foe/<alt>@``
alternative forms, I70-R4-CR-009A) are EN-only display tokens:
mon-util.cc's ``do_mon_str_replacements()`` deletes the leading-space
compound on the player-foe branch, splices it as `` to @foe@``/`` at @foe@``
on the monster-foe branch, or expands the alternative literally (e.g.
``around``), so the localizable core is the ``@foe@`` reference and
Chinese must not mirror the compounds mechanically.  The paired EN/ZH
token comparison (candidate pair loop and the ledger proposals bound to a
candidate) therefore exempts exactly those two tokens and their
slash-alternative forms: EN keeps its baseline bytes (counts/positions
stay validated by the EN byte binding), while ZH may mirror the
compounds, render the localizable ``@foe@`` structure, or restructure the
sentence -- the compounds are never ZH-required tokens, ``@foe@`` stays
bidirectionally required and every other token stays exactly aligned.

Consumer model (frozen at the baseline OID): ``mon-speak.cc::mons_speaks``
queries ``<prefix> <base> <suffix>`` keys through ``getSpeakString`` with the
``"default "`` fallback chain; the base keys are the English monster DB
names (``mons->name(DESC_DBNAME)`` / ``mons->base_name(DESC_DBNAME)`` /
``mons_type_name(mons_genus(mons->type), DESC_DBNAME)``), ``player ghost``,
``pandemonium lord``, the glyph keys ``'x'``/``'cap-x'`` built from
``mons_base_char`` and the ``get_mon_shape_str`` shape keys; the suffixes
are ``triumphant``/``banished``/``killed``/``permanently killed``/``timeout``
built by ``_get_speak_string``; the prefix space is derived from the
exact-Git mon-speak.cc literals, the ``_god_name_en`` table, the
``branches[]`` abbrevnames and the ``_skill_english_name`` table.  In
addition, fixed consumer literals and dynamic monster-name suffixes are
derived from the exact-Git call sites of mon-death.cc (Dowan/Duvessa twin
death keys and the ``twin_*`` speech prefixes), attitude-change.cc
(``beogh_converted_orc_*``, Gozag bribe), mon-abil.cc
(``nobody_recollection <key>``), god-companions.cc / god-abil.cc / monster.cc
(apostle, orc priest, Maurice, marionette), transform.cc (``<name> riddle``),
mon-cast.cc (``<name> blink_other``/``blink_other_close``/``charge`` and
``branch summon cast prefix``), spl-goditem.cc (holy pacification),
player-reacts.cc (``recite_closure``), mon-util.cc (``_laughs_``),
spl-summoning.cc (``_monster_greeting(imp, "_friendly_imp_greeting")
`` call-imp greeting) and the vault ``dbname:``/``name:`` tags of
dat/des (``deformed humanoid``, ``zin angel``, ``goblin sharper``).
Every non-root identity must be reached by the ``@token@`` closure from
the roots (recursive-internal-fragment); keys with no live producer path
and no inbound reference are frozen legacy-orphaned identities (6 EN
keys), and AXED_MON names are a legacy-axed-monster class that is empty
at the baseline.

The Chinese side adds two baseline facts that the review phase must
adjudicate: 191 empty variants and 14 split Lua fragments (ZH Lua blocks
contain blank lines, so the production weighted-entry parser splits them
into separate variants; the ``{{``/``}}`` pieces are unbalanced in isolation
and can never execute).  The seven override keys keep their raw
zh/monspeak.txt bodies as the review identities while the effective
localized dump carries the zh/shout.txt winners; the override evidence is
recorded per card and the per-language variant totals freeze the raw-body
identity model (3429 EN / 3407 ZH).

The strict JSONL review ledger (one metadata record plus 733 cards) is the
issue #70 audit trail.  ``--scaffold-output`` generates the initial empty
ledger (exclusive create at ``docs/monspeak-review-results.md`` through the
decorlines hardened write transaction, which fails closed when a ledger
already exists); the later zh-translator phase fills the 733 cards, and
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
import itertools
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, deque
from pathlib import Path
from typing import Any

import yaml

import decorlines_inventory as decorlines
import monflee_inventory as shared
import wpnnoise_inventory as hardened
import shout_inventory as shout


SCHEMA_VERSION = 1
SOURCE_BASENAME = "monspeak.txt"
STRICT_BEGIN = "<!-- BEGIN STRICT MONSPEAK REVIEW EVIDENCE v1 -->"
STRICT_END = "<!-- END STRICT MONSPEAK REVIEW EVIDENCE v1 -->"
RESULTS_PATH = Path(__file__).resolve().parents[2] / "docs/monspeak-review-results.md"

# Frozen Issue #70 baseline shape (verified against the production dumps at
# the baseline OID; the asymmetric key list itself is derived from the
# baseline dumps below and only its count/order is frozen here).
EXPECTED_EN_IDENTITY_COUNT = 731
EXPECTED_ZH_IDENTITY_COUNT = 733
# One ledger card per EN identity plus one per ZH-only key.
EXPECTED_IDENTITY_COUNT = 733
EXPECTED_EN_VARIANT_COUNT = 3429
EXPECTED_ZH_VARIANT_COUNT = 3407
EXPECTED_EN_RANDOM_SITES = 47
EXPECTED_ZH_RANDOM_SITES = 38
EXPECTED_EN_LUA_SITES = 18
EXPECTED_ZH_LUA_SITES = 5
# Malformed Lua sites of the baseline dumps (CR-002): the baseline OID is
# clean in both languages; the ``{{{`` stray-brace defect was introduced into
# the review worktree file later and is CR-001's translator fix.  The
# candidate role fails closed on any remaining malformed site (including a
# reintroduced ``{{{``), and the baseline freeze keeps the fact visible.
EXPECTED_ZH_MALFORMED_LUA_SITES: list[list[int | str]] = []
# Frozen candidate-role variant totals: the candidate EN is byte-bound to the
# baseline EN (3429) and the aligned ZH is the 3429 shared EN-aligned variants
# plus the two single-variant ZH-only keys (3431).  Never derived from the
# editable review ledger (CR-003).
EXPECTED_CANDIDATE_EN_VARIANT_COUNT = EXPECTED_EN_VARIANT_COUNT
EXPECTED_CANDIDATE_ZH_VARIANT_COUNT = 3431
EXPECTED_EN_EMPTY_VARIANTS = 0
EXPECTED_ZH_EMPTY_VARIANTS = 191
EXPECTED_EN_DISTINCT_TOKENS = 326
EXPECTED_EN_INFILE_TOKENS = 294
EXPECTED_EN_EXTERNAL_TOKENS = 32
EXPECTED_ZH_DISTINCT_TOKENS = 299
EXPECTED_ZH_INFILE_TOKENS = 270
EXPECTED_ZH_EXTERNAL_TOKENS = 29
EXPECTED_ROOT_COUNT = 460
EXPECTED_FRAGMENT_COUNT = 265
# The ZH side adds the ``default 'j'`` glyph default root and keeps the
# same key space minus the inlined fragments, so its counts differ.
EXPECTED_ZH_ROOT_COUNT = 461
EXPECTED_ZH_FRAGMENT_COUNT = 242
EXPECTED_EN_ORPHAN_COUNT = 6
EXPECTED_ZH_ORPHAN_COUNT = 30

# The two ZH-only monspeak keys (EN has no counterpart); their disposition
# is explicitly deferred to the translation phase.
ZH_ONLY_KEYS = frozenset({"_jory_rare_", "default 'j'"})

# The seven shout-family keys whose zh/monspeak.txt definitions are shadowed
# by the later zh/shout.txt load in the effective localized SpeakDB merge
# (sorted scan: monspeak.txt loads before shout.txt).  Their review
# identities keep the raw zh/monspeak.txt bodies; the effective localized
# dump carries the zh/shout.txt winners.  The EN manifest has no overrides.
CROSS_DB_OVERRIDE_KEYS = frozenset({
    "'&'", "iron imp", "moth of wrath", "player ghost",
    "polyphemus", "shadow imp", "white imp",
})

# The production consumer of every cross-DB override key (CR-015).  The
# override provenance (zh/shout.txt shadowing the zh/monspeak.txt body in
# the effective localized merge) stays in ``evidence_locations`` only;
# the card consumer evidence must name the real lookup path: the ``'&'``
# glyph key is consumed by the mon-speak.cc glyph fallback
# (``glyph_consumer``), while the named monsters and ``player ghost`` go
# through the normal exact-key monspeak lookup (``monspeak_consumer``).
CROSS_DB_OVERRIDE_CONSUMERS = {
    "'&'": "glyph_consumer",
    "iron imp": "monspeak_consumer",
    "moth of wrath": "monspeak_consumer",
    "player ghost": "monspeak_consumer",
    "polyphemus": "monspeak_consumer",
    "shadow imp": "monspeak_consumer",
    "white imp": "monspeak_consumer",
}

# Keys with no live production consumer path and no inbound @token@
# reference at the baseline: legacy-orphaned identities exempt from the
# reachability proof (six stale/typo'd keys; the imp-greeting chain became
# reachable in I70-R5-CR-014 through the spl-summoning.cc call-imp
# greeting).  Derived from the exact-Git consumer proof and required to
# equal this set.
EXPECTED_EN_ORPHANS = frozenset({
    "default '8'",
    "jivya frederick triumphant",
    "no god donald",
    "nobody triumph",
    "roxanne blink_other_closer",
    "silent jory killed",
})

# Additional ZH-side orphans: fragments whose EN references were inlined
# into the ZH bodies, so the ZH closure never reaches them.  The ZH orphan
# set must equal EXPECTED_EN_ORPHANS | ZH_EXTRA_ORPHANS.
EXPECTED_ZH_EXTRA_ORPHANS = frozenset({
    "_begs_",
    "_boris_medium_",
    "_boris_return_common_",
    "_boris_return_rare_",
    "_crazy_yiuf_wordlist1_",
    "_crazy_yiuf_wordlist2_",
    "_fleeing_silenced_common_",
    "_fleeing_silenced_rare_",
    "_friendly_confused_common_",
    "_friendly_confused_medium_",
    "_friendly_confused_rare_",
    "_friendly_family_",
    "_friendly_fleeing_common_",
    "_friendly_fleeing_rare_",
    "_friendly_humanoid_common_",
    "_friendly_humanoid_medium_",
    "_friendly_humanoid_rare_",
    "_friendly_silenced_common_",
    "_friendly_silenced_rare_",
    "_maurice_medium_",
    "_norris_verb_",
    "_roxanne_medium_",
    "_silenced_humanoid_common_",
    "_silenced_humanoid_rare_",
})

# The exact 213 asymmetric monspeak keys (EN count, ZH count); derived from
# the baseline dumps and required to equal this dict verbatim.
EXPECTED_ASYM: dict[str, list[int]] = {
    "_asterion_common_": [13, 6],
    "_asterion_rare_": [7, 3],
    "_bai_suzhen_rare_": [6, 4],
    "_begs_": [4, 6],
    "_blorkula_colour_": [2, 4],
    "_blorkula_common_": [12, 7],
    "_blorkula_rare_": [9, 4],
    "_boris_common_": [2, 4],
    "_boris_rare_": [7, 4],
    "_boris_return_rare_": [4, 5],
    "_confused_humanoid_common_": [9, 10],
    "_crazy_yiuf_sentence_": [3, 15],
    "_crazy_yiuf_speech_verbs_": [7, 8],
    "_dissolution_rare_": [5, 7],
    "_dissolution_speech_": [6, 7],
    "_eustachio_common_": [8, 5],
    "_fleeing_humanoid_common_": [13, 6],
    "_fleeing_humanoid_rare_": [12, 7],
    "_form_": [3, 4],
    "_frances_common_": [10, 5],
    "_frances_rare_": [8, 3],
    "_frederick_common_": [9, 5],
    "_frederick_rare_": [9, 6],
    "_friendly_fleeing_common_": [5, 6],
    "_friendly_imp_": [2, 3],
    "_friendly_imp_greeting": [5, 6],
    "_frog_food_": [12, 15],
    "_generic_donald_": [34, 30],
    "_grum_common_": [9, 5],
    "_harold_ret_hobby_": [6, 7],
    "_harold_ret_house_": [5, 4],
    "_harold_ret_place_": [5, 4],
    "_high_priest_": [3, 5],
    "_holy_being_": [5, 11],
    "_hostile_imp_rare_": [5, 11],
    "_hostile_orc_beogh_believer_speech_": [2, 3],
    "_hostile_orc_beogh_unbeliever_speech_": [2, 3],
    "_important_subject_": [15, 16],
    "_jeremiah_rare_": [13, 5],
    "_jory_common_": [7, 3],
    "_josephina_rare_": [7, 4],
    "_killer_klown_common_": [10, 9],
    "_laughs_": [3, 4],
    "_loudly_or_repeatedly_": [3, 5],
    "_mara_common_": [9, 7],
    "_mara_rare_": [8, 4],
    "_margery_common_": [8, 11],
    "_maurice_common_": [4, 6],
    "_maurice_rare_": [3, 1],
    "_mercenary_guard_": [3, 5],
    "_mutters_": [3, 4],
    "_norris_common_": [14, 6],
    "_norris_rare_": [13, 4],
    "_pikel_rare_": [20, 5],
    "_player_ghost_common_": [13, 7],
    "_player_ghost_medium_": [16, 6],
    "_prince_ribbit_common_": [4, 5],
    "_recite_subject_": [18, 20],
    "_roxanne_common_": [5, 4],
    "_roxanne_rare_": [6, 3],
    "_rupert_rare_": [7, 8],
    "_saint roka generic_": [7, 8],
    "_sigmund_rare_": [6, 7],
    "_snorg_common_": [5, 8],
    "_snorg_rare_": [2, 3],
    "_sojobo_rare_": [4, 5],
    "_sonja_common_": [6, 5],
    "_sonja_rare_": [5, 3],
    "_spectator_speech_": [9, 13],
    "_suck_up_adj2_": [4, 15],
    "_urug_common_": [20, 8],
    "_urug_rare_": [5, 4],
    "_weeping_skull_rare_": [4, 6],
    "_wiglaf_nondwarf_": [2, 3],
    "_wizard_": [3, 6],
    "abyss donald": [10, 7],
    "alderking": [4, 5],
    "amaemon": [2, 3],
    "arcanist": [3, 6],
    "ashenzari donald": [7, 4],
    "beogh donald": [14, 7],
    "beogh frederick": [2, 4],
    "boris": [3, 2],
    "boris killed": [2, 3],
    "boris triumphant": [3, 2],
    "cassandra": [10, 11],
    "cheibriados donald": [8, 4],
    "chuck": [2, 3],
    "cognitogaunt": [11, 13],
    "crypt donald": [32, 12],
    "crystal guardian": [2, 3],
    "death cob": [2, 4],
    "default confused humanoid": [3, 5],
    "default fleeing humanoid": [2, 3],
    "default fleeing silenced humanoid": [2, 1],
    "default friendly confused humanoid": [3, 2],
    "default friendly fleeing humanoid": [2, 1],
    "default friendly humanoid": [4, 2],
    "default friendly silenced humanoid": [2, 1],
    "default hostile confused donald": [13, 8],
    "default silenced humanoid": [3, 1],
    "default stupid friendly humanoid": [1, 2],
    "deformed humanoid": [30, 34],
    "dissolution": [2, 3],
    "dithmenos donald": [8, 9],
    "donald banished": [2, 4],
    "donald killed": [2, 4],
    "duvessa_dowan_dies_bytwin": [2, 3],
    "duvessa_dowan_dies_invisible": [3, 1],
    "elf donald": [8, 9],
    "elyvilon donald": [7, 8],
    "erolcha banished": [2, 1],
    "eustachio triumphant": [2, 3],
    "fedhas donald": [7, 4],
    "frederick triumphant": [6, 1],
    "friendly '5'": [2, 4],
    "friendly donald": [2, 3],
    "friendly good god 'cap-a'": [2, 4],
    "friendly hound": [9, 11],
    "friendly orc": [2, 3],
    "friendly protean progenitor": [2, 3],
    "friendly related beogh orc": [4, 8],
    "friendly related orc": [2, 3],
    "friendly shoals hound": [4, 12],
    "goblin sharper": [16, 24],
    "good god '&'": [4, 8],
    "gozag donald": [9, 10],
    "gozag permabribe": [1, 4],
    "grunn": [2, 3],
    "hepliaklqana donald": [8, 9],
    "holy_being_pacification_humanoid": [3, 4],
    "ignacio": [2, 3],
    "ignis donald": [11, 4],
    "ilsuiw": [2, 3],
    "jiyva donald": [10, 11],
    "jorgrun": [2, 3],
    "jory": [1, 2],
    "kikubaaqudgha donald": [14, 5],
    "kobold blastminer": [3, 4],
    "lodul": [2, 3],
    "lugonu donald": [7, 8],
    "makhleb donald": [14, 4],
    "mara riddle": [1, 3],
    "margery": [2, 3],
    "maurice": [3, 2],
    "maurice confused nonstealing": [5, 7],
    "murray": [2, 3],
    "nekomata": [4, 25],
    "nemelex xobeh donald": [10, 11],
    "nergalle": [7, 6],
    "neutral good god 'cap-a'": [2, 3],
    "no god donald": [7, 4],
    "nobody": [7, 5],
    "obsidian bat": [2, 3],
    "occultist": [3, 6],
    "okawaru donald": [10, 11],
    "okawaru frederick": [2, 4],
    "orb donald": [10, 11],
    "orc": [2, 4],
    "orc donald": [15, 12],
    "pakellas donald": [6, 7],
    "parghit": [2, 3],
    "pargi": [2, 3],
    "player ghost": [3, 5],
    "polyphemus": [2, 3],
    "polyphemus killed": [2, 4],
    "protean progenitor": [5, 6],
    "qazlal donald": [9, 10],
    "raven": [2, 4],
    "related beogh blorkula the orcula": [2, 3],
    "related beogh orc": [3, 6],
    "related beogh orc high priest": [3, 5],
    "related beogh orc sorcerer": [3, 5],
    "related beogh saint roka": [4, 7],
    "related beogh urug": [2, 3],
    "related saint roka": [2, 3],
    "related unbeliever orc": [3, 6],
    "related vashnia": [3, 5],
    "related wiglaf": [2, 3],
    "roxanne": [3, 2],
    "roxanne blink_other_closer": [5, 2],
    "ru donald": [9, 10],
    "rupert": [2, 3],
    "saint roka": [3, 4],
    "shoals donald": [20, 14],
    "sif muna donald": [13, 5],
    "sigmund triumphant": [1, 4],
    "silenced player ghost": [3, 5],
    "snake donald": [21, 11],
    "sojobo": [3, 5],
    "sonja triumphant": [3, 4],
    "spectator": [2, 3],
    "sprozz": [1, 7],
    "sprozz triumphant": [1, 7],
    "temple donald": [9, 11],
    "the shining one donald": [9, 10],
    "tormentor": [2, 4],
    "trog donald": [11, 4],
    "uskayaw donald": [8, 9],
    "vashnia": [3, 5],
    "vaults donald": [10, 11],
    "vehumet donald": [9, 10],
    "weeping skull": [3, 6],
    "wiglaf": [3, 4],
    "wu jian donald": [7, 8],
    "xak'krixis": [8, 14],
    "xom donald": [13, 5],
    "xtahua": [2, 3],
    "yredelemnul donald": [2, 3],
    "zenata": [2, 3],
    "zin angel": [9, 11],
    "zin donald": [11, 5],
    "zot donald": [21, 11],
}

# The 14 ZH variants whose Lua blocks were split by blank lines: the
# production weighted-entry parser separates variants on blank lines, so the
# ``{{``/``}}`` pieces are unbalanced in isolation and can never execute.
# EN has none.  Derived from the baseline dumps and required to equal this
# list (key, variant ordinal).
EXPECTED_SPLIT_LUA_FRAGMENTS = [
    ["friendly shoals hound", 3],
    ["friendly shoals hound", 9],
    ["nekomata", 0],
    ["nekomata", 6],
    ["nekomata", 7],
    ["nekomata", 15],
    ["nekomata", 16],
    ["nekomata", 22],
    ["sprozz", 0],
    ["sprozz", 6],
    ["sprozz triumphant", 0],
    ["sprozz triumphant", 6],
    ["xak'krixis", 6],
    ["xak'krixis", 11],
]

# The monspeak suffixes appended by mon-speak.cc::_get_speak_string.
SPEAK_SUFFIXES = ("triumphant", "banished", "killed",
                  "permanently killed", "timeout")

# The mon-speak.cc prefix literals (plus "default" for the fallback chain).
# God names, branch abbrevnames and skill names are derived from the
# exact-Git tables and must cover the file keys.
STATIC_PREFIXES = frozenset({
    "neutral", "friendly", "hostile", "fleeing", "silenced", "confused",
    "related", "stationary", "stupid", "beogh", "unbeliever", "good god",
    "orb", "bfb", "default",
})

# Tokens replaced after TextDB expansion by
# mon-util.cc::do_mon_str_replacements.  Everything else in every variant
# must be an in-family key (recursive @token@) or one of the five
# cross-family SpeakDB keys below, or the run fails closed.
POSTPROCESS_TOKENS = frozenset({
    "at_foe", "at_foe/around", "foe", "foe,", "foe_genus", "foe_god",
    "foe_name", "foe_possessive", "hands", "my_god", "objective",
    "player_genus", "player_genus_plural", "player_name", "player_only",
    "possessive", "possessive_god", "random_god_chaotic", "random_god_evil",
    "random_god_good", "reflexive", "says", "subjective", "surface",
    "the_monster", "the_monster_possessive", "to_foe",
})

# EN-only display tokens: mon-util.cc::do_mon_str_replacements() deletes the
# leading-space ``@to_foe@``/``@at_foe@`` phrase entirely on the player-foe
# branch and splices it as `` to @foe@``/`` at @foe@`` on the monster-foe
# branch, so the compounds are English display syntax, not ZH-required
# tokens: mechanically mirroring them in Chinese yields a dangling
# preposition / missing object on the player side and a mixed-language
# "to <name>" on the monster side.  The correct ZH structure is the
# localizable ``@foe@`` (player "you" / monster name) or a sentence
# rewrite.  The paired EN/ZH comparison exempts exactly these two tokens
# and their ``@to_foe/<alt>@``/``@at_foe/<alt>@`` alternative forms (see
# ``_foe_protocol_equal``): EN keeps its exact baseline bytes (counts and
# positions stay validated by the EN source/dump byte binding), while ZH
# may carry the mirror tokens, render the ``@foe@`` structure, or omit
# them.  I70-R4-CR-009A: the alternative form ``@at_foe/around@`` expands
# to the literal English alternative ("around") on the player-foe branch
# and to " at @foe@" on the monster-foe branch, so it is equally English
# display syntax and must be covered by the same data-side exception;
# the ZH data drops/replaces it instead of leaking English.  ``@foe@``
# itself stays bidirectionally required and every other token stays
# exactly aligned; the exception is narrow -- only these two exact
# lowercase tokens plus their slash-alternative forms (``@Foe@`` and any
# case variant are separate tokens and remain strictly required).
EN_ONLY_DISPLAY_TOKENS = frozenset({"@to_foe@", "@at_foe@"})

_EN_ONLY_DISPLAY_TOKEN_RE = re.compile(r"^@(?:to|at)_foe(?:/[^@]*)?@$")


def _is_en_only_display_token(token: str) -> bool:
    """True for ``@to_foe@``/``@at_foe@`` and their ``/<alt>`` forms."""
    return bool(_EN_ONLY_DISPLAY_TOKEN_RE.match(token))
# Baseline ZH runtime-token counts of the EN-only display tokens.  Frozen
# historical facts from the baseline dumps; the review never requires the
# candidate to reproduce them -- that is the point of the exception.  The
# baseline EN counts (295 x @to_foe@ / 222 x @at_foe@) are not frozen here
# because the EN side is byte-bound to the baseline.
EXPECTED_ZH_BASELINE_EN_ONLY_COUNTS = {"@to_foe@": 52, "@at_foe@": 12}

# Tokens resolved through SpeakDB lookups in other SpeakDB source files
# (insult.txt demon/imp taunts, colourname.txt colours, monname.txt orc
# names).  They are cross-family references, not monspeak identities.
CROSS_FAMILY_TOKENS = frozenset({
    "demon_taunt", "imp_taunt", "misc_colour", "orc name", "rainbow_colour",
})

# Fixed consumer literal roots and dynamic monster-name suffix roots derived
# from the exact-Git call sites; patterns are matched against the scoped key
# space (see _special_consumer_roots).
_TWIN_KEY_RE = re.compile(
    r"^(dowan|duvessa)_(dowan|duvessa)_dies(_(invisible|distance))?"
    r"(_bytwin)?$"
)
_TWIN_PREFIX_RE = re.compile(
    r"^twin_(ikilled|banished|died|slimified) (dowan|duvessa)$"
)
_BEOGH_CONVERT_RE = re.compile(
    r"^beogh_converted_orc_(reaction_battle|reaction_sight|resurrection|"
    r"speech_battle|speech_sight|speech_vengeance)(_follower)?$"
)
_RECOLLECTION_RE = re.compile(
    r"^nobody_recollection (fire|cold|poison|undead|fear|soldiers|"
    r"rockslide|electricity|xxx|demons|vermin)$"
)

FIXED_CONSUMER_LITERALS = frozenset({
    "gozag bribe", "gozag permabribe", "beogh apostle challenge",
    "orc_apostle_yield", "orc_apostle_dismissed", "orc_apostle_unbanished",
    "orc_priest_preaching", "orc_priest_apostate",
    "maurice confused nonstealing", "maurice nonstealing",
    "branch summon cast prefix", "holy_being_pacification",
    "holy_being_pacification_humanoid", "holy_being_pacification_speech",
    "recite_closure", "_laughs_", "goblin sharper",
    "_friendly_imp_greeting",
})

# Dynamic monster-name suffix roots (<name> + literal) from the exact-Git
# call sites.
NAME_SUFFIX_CONSUMERS = ("marionette", "blink_other", "blink_other_close",
                         "riddle", "charge", "gozag bribe", "gozag permabribe")

# Vault-driven keys: dbname: tags (mapdef.cc props[DBNAME_KEY]) and the
# name: + n_suf tag of the Nemelex goblin vault ("goblin sharper").
VAULT_DBNAME_KEYS = frozenset({"deformed humanoid", "zin angel"})
VAULT_NAME_KEYS = frozenset({"goblin sharper"})

# SpeakDB monspeak.txt load index (first SpeakDB source).
MONSPEAK_SPEAKDB_INDEX = 0

# Fixed exact-Git producer sources (tracked C++ files; the monster YAML and
# vault .des inputs are enumerated from the same OID tree).
PRODUCER_GIT_FILES = [
    "crawl-ref/source/mon-speak.cc",
    "crawl-ref/source/mon-util.cc",
    "crawl-ref/source/mon-death.cc",
    "crawl-ref/source/attitude-change.cc",
    "crawl-ref/source/mon-abil.cc",
    "crawl-ref/source/god-companions.cc",
    "crawl-ref/source/god-abil.cc",
    "crawl-ref/source/monster.cc",
    "crawl-ref/source/transform.cc",
    "crawl-ref/source/mon-cast.cc",
    "crawl-ref/source/mon-behv.cc",
    "crawl-ref/source/spl-goditem.cc",
    "crawl-ref/source/spl-summoning.cc",
    "crawl-ref/source/player-reacts.cc",
    "crawl-ref/source/mapdef.cc",
    "crawl-ref/source/religion.cc",
    "crawl-ref/source/skills.cc",
    "crawl-ref/source/branch-data.h",
]

# Anchor producer names that must survive the exact-Git derivation.
_MONSTER_ANCHORS = ("jory", "donald", "dowan", "duvessa", "orb spider",
                    "player ghost", "hell lord", "nobody")

InventoryError = hardened.InventoryError
_require = hardened._require
_sha256 = hardened._sha256
_canonical_json = hardened._canonical_json

_GLYPH_KEY_RE = re.compile(r"^'(cap-)?[^']'$")
_SHAPE_NAMES_RE = re.compile(r'shape_names\[\]\s*=\s*\{(.*?)\};', re.DOTALL)
_DBNAME_TAG_RE = re.compile(r'dbname:([A-Za-z0-9_]+)')
_MONSPEAK_SOURCE_RE = re.compile(r'TextDB\s*\(\s*"speak"\s*,\s*"database/"',
                                 re.DOTALL)


def _require_regular_monspeak_git_sources(
    ref: str, directory: str, label: str,
) -> None:
    """Bind the monspeak derivation inputs to regular blobs at the exact OID.

    Besides database.cc and every TextDB source, the root-key derivation
    reads the consumer C++ sources, the monster YAML inputs, the generated
    branch-data.h table and the vault .des files from the
    same commit tree; this pre-flight proves every one of those tree
    entries is a regular file so no unsupported Git object type can be
    parsed with semantics different from the production checkout."""
    manifest = (
        shared._english_source_manifest(ref, label)
        if directory == "database/"
        else shared._localized_source_manifest(ref, label)
    )
    des_paths = _git_des_files(ref, label)
    hardened._require_regular_git_blobs(
        ref,
        ["crawl-ref/source/database.cc"]
        + [f"crawl-ref/source/dat/{name}" for name in manifest]
        + [f"crawl-ref/source/dat/{name}"
           for name in shared._english_source_manifest(ref, label)]
        + ["crawl-ref/source/dat/database/zh/monspeak.txt"]
        + PRODUCER_GIT_FILES
        + shout._git_tree_yamls(ref, "crawl-ref/source/dat/mons", label)
        + des_paths,
        label,
    )


def _git_des_files(oid: str, label: str) -> list[str]:
    """Committed ``*.des`` vault inputs at the exact OID (recursive).

    The map parser reads vault files directly from the data directory, so
    every ``*.des`` blob of the tree participates in the ``dbname:``/``name:``
    tag derivation; only blob entries count and a directory named ``*.des``
    would make the production open fail, so it fails closed here instead."""
    listing = shared._git_output(
        ["ls-tree", "-r", oid, "--", "crawl-ref/source/dat/des/"],
        f"{label} vault tree",
    )
    paths: list[str] = []
    for line in listing.splitlines():
        meta, name = line.split(b"\t", 1)
        kind = meta.split(b" ")[1]
        if name.endswith(b".des"):
            _require(
                kind == b"blob",
                f"{label} vault tree has a non-file *.des entry "
                f"{name.decode('utf-8')!r} that production could not read",
            )
            paths.append(name.decode("utf-8"))
    _require(bool(paths), f"{label} vault tree contains no .des inputs")
    return paths


def _vault_dbnames(oid: str, label: str) -> set[str]:
    """Lowercased ``dbname:`` tag values of every committed vault file.

    mapdef.cc stores ``dbname:<snake_case>`` as props[DBNAME_KEY] with
    underscores replaced by spaces; mon-speak.cc queries that value
    verbatim, so the derived keys are the lowercased tag values."""
    values: set[str] = set()
    for git_path in _git_des_files(oid, label):
        source = shared._decode_utf8(
            shared._git_blob_at_oid(oid, git_path, f"{label} {git_path}"),
            label,
        )
        values.update(
            match.group(1).replace("_", " ").lower()
            for match in _DBNAME_TAG_RE.finditer(source)
        )
    _require(VAULT_DBNAME_KEYS <= values,
             f"{label} vault dbname derivation lost "
             f"{sorted(VAULT_DBNAME_KEYS - values)!r}")
    return values


def _monster_producers(oid: str, label: str) -> list[str]:
    """English DB names of every monster (dat/mons/*.yaml name fields).

    These are the ``mons->name(DESC_DBNAME)`` /
    ``mons->base_name(DESC_DBNAME)`` / ``mons_type_name(genus, DESC_DBNAME)``
    values mon-speak.cc queries; the mname path additionally produces
    vault ``name:``-derived custom names (goblin sharper)."""
    names = shout._yaml_name_fields(oid, "crawl-ref/source/dat/mons", label)
    for anchor in _MONSTER_ANCHORS:
        _require(anchor in names,
                 f"{label} monster derivation lost {anchor!r}")
    return names


def _base_chars(oid: str, label: str) -> set[str]:
    """Base glyph characters of every committed monster YAML input.

    mon-gen.py generates mon-data.h from the dat/mons/*.yaml ``glyph``
    fields (parse_glyph/parse_glyph_char), and mon-speak.cc builds the
    glyph fallback key ``'x'``/``'cap-X'`` from ``mons_base_char``; the DB
    lookup lowercases the query, so the derived key space is ``'<char>'``
    plus ``'cap-<char>'`` for upper case base chars."""
    chars: set[str] = set()
    for git_path in shout._git_tree_yamls(oid, "crawl-ref/source/dat/mons",
                                          label):
        source = shared._decode_utf8(
            shared._git_blob_at_oid(oid, git_path, f"{label} {git_path}"),
            label,
        )
        try:
            data = yaml.safe_load(source)
        except yaml.YAMLError as exc:
            raise InventoryError(
                f"{label} {git_path} is not valid YAML: {exc}"
            ) from exc
        _require(isinstance(data, dict) and isinstance(data.get("glyph"), dict),
                 f"{label} {git_path} needs a glyph mapping")
        char = data["glyph"].get("char")
        _require(isinstance(char, str) and len(char) == 1,
                 f"{label} {git_path} needs a single-char glyph")
        chars.add(char)
    _require(len(chars) >= 40,
             f"{label} glyph char derivation lost entries")
    return chars


def _glyph_bases(chars: set[str]) -> set[str]:
    return ({f"'{char}'" for char in chars}
            | {f"'cap-{char.lower()}'" for char in chars
               if char.isupper()})


def _shape_keys(oid: str, label: str) -> set[str]:
    """The get_mon_shape_str shape-name table of the exact-Git mon-util.cc."""
    source = shared._decode_utf8(
        shared._git_blob_at_oid(oid, "crawl-ref/source/mon-util.cc", label),
        label,
    )
    match = _SHAPE_NAMES_RE.search(source)
    _require(match is not None,
             f"{label} cannot find the shape_names table in mon-util.cc")
    shapes = set(match.group(0) and re.findall(r'"([^"]+)"', match.group(1)))
    _require(len(shapes) == 24,
             f"{label} shape table must contain 24 shape names")
    return shapes


def _god_prefixes(oid: str, label: str) -> list[str]:
    """Lowercased _god_name_en values of the exact-Git religion.cc switch."""
    source = shared._decode_utf8(
        shared._git_blob_at_oid(oid, "crawl-ref/source/religion.cc", label),
        label,
    )
    names = [match.lower() for match in re.findall(
        r'case GOD_\w+:\s*return "([^"]+)";', source)]
    _require(len(names) >= 25,
             f"{label} _god_name_en derivation lost entries")
    return names


def _branch_prefixes(oid: str, label: str) -> list[str]:
    """Lowercased branches[] abbrevnames of the exact-Git branch-data.h."""
    source = shared._decode_utf8(
        shared._git_blob_at_oid(oid, "crawl-ref/source/branch-data.h", label),
        label,
    )
    abbrevs = [match[2].lower() for match in re.findall(
        r'\{ BRANCH_\w+,[^}]*?"([^"]*)",\s*"([^"]*)",\s*"([^"]*)"',
        source)]
    _require(len(abbrevs) >= 30,
             f"{label} branch abbrevname derivation lost entries")
    return sorted(set(abbrevs))


def _skill_prefixes(oid: str, label: str) -> list[str]:
    """Lowercased _skill_english_name values of the exact-Git skills.cc.

    mon-speak.cc prefixes player-ghost queries with the ghost's best skill
    (skill_name_en), so every skill name is a possible prefix."""
    source = shared._decode_utf8(
        shared._git_blob_at_oid(oid, "crawl-ref/source/skills.cc", label),
        label,
    )
    match = re.search(
        r'_skill_english_name\(skill_type sk\)\s*\{(.*?)\n\}',
        source, re.DOTALL,
    )
    _require(match is not None,
             f"{label} cannot find _skill_english_name in skills.cc")
    names = [name.lower() for name in re.findall(
        r'case SK_\w+:\s*return "([^"]+)";', match.group(1))]
    _require(len(names) >= 25,
             f"{label} skill name derivation lost entries")
    return names


def _axed_monster_names(oid: str, label: str) -> list[str]:
    """DB names of AXED_MON entries in the exact-Git mon-gen header."""
    source = shared._decode_utf8(
        shared._git_blob_at_oid(
            oid, "crawl-ref/source/util/mon-gen/header.txt", label),
        label,
    )
    names = re.findall(r'AXED_MON\(\s*MONS_\w+\s*,\s*"([^"]+)"\s*\)',
                       source)
    _require(bool(names), f"{label} header.txt has no AXED_MON entries")
    return sorted(names)


def _monspeak_static_prefixes(oid: str, label: str) -> list[str]:
    """The mon-speak.cc literal prefixes pushed into the prefix list
    (emplace_back/push_back literals and the stationary/stupid
    insert-at-begin literals), plus the ``default`` fallback prefix.

    The derived set must equal the frozen STATIC_PREFIXES, so a changed or
    removed prefix literal fails closed instead of silently reclassifying
    the root space."""
    source = shared._decode_utf8(
        shared._git_blob_at_oid(oid, "crawl-ref/source/mon-speak.cc", label),
        label,
    )
    literals = set(re.findall(
        r'prefixes\.(?:emplace_back|push_back)\(\s*"([^"]+)"\s*\)',
        source))
    literals |= set(re.findall(
        r'prefixes\.insert\(prefixes\.begin\(\),\s*"([^"]+)"\s*\)',
        source))
    literals.add("default")
    literals = {literal.lower() for literal in literals}
    _require(
        literals == STATIC_PREFIXES,
        f"{label} mon-speak.cc static prefix derivation differs: "
        f"{sorted(literals ^ STATIC_PREFIXES)!r}",
    )
    return sorted(literals)


def _derivable_root_facts(
    oid: str, label: str, role: str = "candidate",
) -> dict[str, Any]:
    """Every base key the monspeak consumers can query directly, derived
    from the exact-Git producers.

    The base space is the union of the monster DB names, player ghost,
    pandemonium lord, the glyph keys built from the YAML glyph chars, the
    24 shape keys and the vault ``dbname:`` values; the prefix space is the
    union of the mon-speak.cc literals, god names, branch abbrevnames and
    skill names; the suffixes are the five _get_speak_string literals.  The
    production identity shapes are bound first (the genus fallback must use
    the canonical English accessor in the candidate role, exactly like the
    ShoutDB fix), so a localized producer fails the whole derivation before
    any key is classified."""
    _genus_identity_shape(oid, label, role)
    return {
        "static_prefixes": _monspeak_static_prefixes(oid, label),
        "monsters": _monster_producers(oid, label),
        "glyph_chars": sorted(_base_chars(oid, label)),
        "shapes": sorted(_shape_keys(oid, label)),
        "gods": _god_prefixes(oid, label),
        "branches": _branch_prefixes(oid, label),
        "skills": _skill_prefixes(oid, label),
        "axed": _axed_monster_names(oid, label),
        "vault_dbnames": sorted(_vault_dbnames(oid, label)),
    }


def _genus_identity_shape(oid: str, label: str, role: str) -> None:
    """Bind the mon-speak.cc genus fallback lookup identity to the English
    accessor.

    ``mons_type_name(mons_genus(mons->type), DESC_DBNAME)`` localizes under
    ZH, turning the genus key into a Chinese string that can never match the
    English monspeak keys, silently falling back to glyph/shape speech.

    ``role`` decides how strict the check is: ``candidate`` requires the
    fixed canonical-English call and rejects the localized call outright;
    ``baseline`` (which predates the fix) additionally accepts the
    documented historical localized call and records it as evidence."""
    source = shared._decode_utf8(
        shared._git_blob_at_oid(oid, "crawl-ref/source/mon-speak.cc", label),
        label,
    )
    fixed = re.search(
        r'_get_speak_string\(prefixes,\s*'
        r'mons_type_name_en\(mons_genus\(mons->type\),\s*DESC_DBNAME\),',
        source,
    )
    historical = re.search(
        r'_get_speak_string\(prefixes,\s*'
        r'mons_type_name\(mons_genus\(mons->type\),\s*DESC_DBNAME\),',
        source,
    )
    if role == "baseline":
        _require(
            fixed is not None or historical is not None,
            f"{label} mons_speaks() genus branch must use either "
            f"mons_type_name_en(mons_genus(...), DESC_DBNAME) or the "
            f"documented pre-fix mons_type_name(mons_genus(...), "
            f"DESC_DBNAME)",
        )
        return
    _require(
        fixed is not None,
        f"{label} mons_speaks() genus branch must use "
        f"mons_type_name_en(mons_genus(mons->type), DESC_DBNAME)",
    )
    _require(
        historical is None,
        f"{label} mons_speaks() genus branch must not use the localized "
        f"mons_type_name(mons_genus(...), DESC_DBNAME)",
    )


def _vault_name_anchor(oid: str, label: str) -> str:
    """The vault ``name:sharper`` MONS line that produces ``goblin
    sharper`` (mapdef.cc name tag + n_suf appended to the goblin base
    name; mon-speak.cc queries the custom DB name)."""
    git_path = "crawl-ref/source/dat/des/altar/overflow.des"
    source = shared._decode_utf8(
        shared._git_blob_at_oid(oid, git_path, label), label)
    pattern = re.compile(r'MONS:\s+generate_awake goblin god:nemelex_xobeh '
                         r'name:sharper n_suf')
    matches = list(pattern.finditer(source))
    _require(len(matches) == 2,
             f"{label} overflow.des must define goblin name:sharper twice")
    first = matches[0]
    _require(
        source.startswith("MONS:    generate_awake goblin "
                          "god:nemelex_xobeh name:sharper n_suf",
                          first.start()),
        f"{label} goblin sharper vault line shape changed",
    )
    return f"{git_path}:{_line_of(first, source)}"


def _line_of(match: re.Match[str], source: str) -> int:
    """1-based line number of a regex match in the exact-Git source."""
    return source.count("\n", 0, match.start()) + 1


def _source_anchor(
    source: str, label: str, name: str,
    pattern: re.Pattern[str], snippet: str,
) -> int:
    """Locate one production anchor in exact Git source and prove it is the
    intended site: the snippet must start at the match position."""
    match = pattern.search(source)
    _require(match is not None,
             f"{label} cannot find {name} in exact Git source")
    _require(source.startswith(snippet, match.start()),
             f"{label} {name} snippet shape changed")
    return _line_of(match, source)


def _producer_consumer_facts(oid: str, label: str) -> dict[str, Any]:
    """Mechanically derive the producer/consumer evidence anchors from the
    exact Git sources and require them to equal the frozen values.

    Every anchor is line-derived and snippet-checked, so a moved or forged
    site cannot satisfy the ledger comparison."""
    database = shared._decode_utf8(
        shared._git_blob_at_oid(oid, "crawl-ref/source/database.cc", label),
        label,
    )
    monspeak = shared._decode_utf8(
        shared._git_blob_at_oid(oid, "crawl-ref/source/mon-speak.cc", label),
        label,
    )
    monutil = shared._decode_utf8(
        shared._git_blob_at_oid(oid, "crawl-ref/source/mon-util.cc", label),
        label,
    )
    loader_match = _MONSPEAK_SOURCE_RE.search(database)
    _require(loader_match is not None,
             f"{label} cannot find the SpeakDB initializer")
    loader_line = _line_of(loader_match, database)
    _require(
        database.startswith('TextDB("speak", "database/"',
                            loader_match.start()),
        f"{label} SpeakDB initializer snippet shape changed",
    )
    manifest = shared._english_source_manifest(oid, label)
    _require(
        manifest[0] == "database/monspeak.txt",
        f"{label} SpeakDB manifest must load monspeak.txt first",
    )

    def anchor(path: str, name: str, pattern: re.Pattern[str],
               snippet: str) -> str:
        source = shared._decode_utf8(
            shared._git_blob_at_oid(oid, path, label), label)
        return f"{path}:{_source_anchor(source, label, name, pattern, snippet)}"

    facts = {
        "loader": f"crawl-ref/source/database.cc:{loader_line}",
        "recursive_expansion": anchor(
            "crawl-ref/source/database.cc",
            "database.cc recursive @token@ expansion",
            re.compile(r'static bool _call_recursive_replacement\('),
            "static bool _call_recursive_replacement("),
        "monspeak_index": MONSPEAK_SPEAKDB_INDEX,
        "monspeak_consumer": anchor(
            "crawl-ref/source/mon-speak.cc",
            "mon-speak.cc exact-key lookup",
            re.compile(r'msg = getSpeakString\(prefix \+ key\);'),
            "msg = getSpeakString(prefix + key);"),
        "default_three": anchor(
            "crawl-ref/source/mon-speak.cc",
            "mon-speak.cc default 3-prefix fallback",
            re.compile(r'msg = getSpeakString\("default " \+ prefix \+ key\);'),
            'msg = getSpeakString("default " + prefix + key);'),
        "default_bare": anchor(
            "crawl-ref/source/mon-speak.cc",
            "mon-speak.cc default bare fallback",
            re.compile(r'msg = getSpeakString\("default " \+ key\);'),
            'msg = getSpeakString("default " + key);'),
        "suffix_triumphant": anchor(
            "crawl-ref/source/mon-speak.cc",
            "mon-speak.cc triumphant suffix",
            re.compile(r'key \+= " triumphant";'),
            'key += " triumphant";'),
        "suffix_banished": anchor(
            "crawl-ref/source/mon-speak.cc",
            "mon-speak.cc banished suffix",
            re.compile(r'key \+= " banished";'),
            'key += " banished";'),
        "suffix_killed": anchor(
            "crawl-ref/source/mon-speak.cc",
            "mon-speak.cc killed suffix",
            re.compile(r'key \+= " killed";'),
            'key += " killed";'),
        "suffix_permanently": anchor(
            "crawl-ref/source/mon-speak.cc",
            "mon-speak.cc permanently suffix",
            re.compile(r'key \+= " permanently";'),
            'key += " permanently";'),
        "suffix_timeout": anchor(
            "crawl-ref/source/mon-speak.cc",
            "mon-speak.cc timeout suffix",
            re.compile(r'key \+= " timeout";'),
            'key += " timeout";'),
        "glyph_consumer": anchor(
            "crawl-ref/source/mon-speak.cc",
            "mon-speak.cc glyph key construction",
            re.compile(r'string key = "\'";'),
            'string key = "\'";'),
        "shape_consumer": anchor(
            "crawl-ref/source/mon-speak.cc",
            "mon-speak.cc shape lookup",
            re.compile(r'_get_speak_string\(prefixes, '
                       r'get_mon_shape_str\(shape\), mons,'),
            "_get_speak_string(prefixes, get_mon_shape_str(shape), mons,"),
        "replacement_consumer": anchor(
            "crawl-ref/source/mon-util.cc",
            "mon-util.cc do_mon_str_replacements definition",
            re.compile(r'string do_mon_str_replacements\('),
            "string do_mon_str_replacements("),
        "laughs": anchor(
            "crawl-ref/source/mon-util.cc",
            "mon-util.cc _laughs_ query",
            re.compile(r'getSpeakString\("_laughs_"\)'),
            'getSpeakString("_laughs_")'),
        "twin_death": anchor(
            "crawl-ref/source/mon-death.cc",
            "mon-death.cc twin death key construction",
            re.compile(r'string key = mons->name\(DESC_THE, true\) \+ "_"'),
            'string key = mons->name(DESC_THE, true) + "_"'),
        "beogh_convert": anchor(
            "crawl-ref/source/attitude-change.cc",
            "attitude-change.cc beogh_converted_orc query",
            re.compile(r'getSpeakString\("beogh_converted_orc_" \+ key\)'),
            'getSpeakString("beogh_converted_orc_" + key)'),
        "gozag_bribe": anchor(
            "crawl-ref/source/attitude-change.cc",
            "attitude-change.cc Gozag bribe query",
            re.compile(r'getSpeakString\(traitor->name\(DESC_DBNAME, true\)'),
            "getSpeakString(traitor->name(DESC_DBNAME, true)"),
        "recollection": anchor(
            "crawl-ref/source/mon-abil.cc",
            "mon-abil.cc nobody recollection query",
            re.compile(r'getSpeakString\("nobody_recollection " \+ '
                       r'recollection\.key\)'),
            'getSpeakString("nobody_recollection " + recollection.key)'),
        "apostle_challenge": anchor(
            "crawl-ref/source/god-companions.cc",
            "god-companions.cc Beogh apostle challenge",
            re.compile(r'getSpeakString\("Beogh apostle challenge"\)'),
            'getSpeakString("Beogh apostle challenge")'),
        "apostle_yield": anchor(
            "crawl-ref/source/god-companions.cc",
            "god-companions.cc orc_apostle_yield",
            re.compile(r'getSpeakString\("orc_apostle_yield"\)'),
            'getSpeakString("orc_apostle_yield")'),
        "apostle_dismissed": anchor(
            "crawl-ref/source/god-companions.cc",
            "god-companions.cc orc_apostle_dismissed",
            re.compile(r'getSpeakString\("orc_apostle_dismissed"\)'),
            'getSpeakString("orc_apostle_dismissed")'),
        "apostle_unbanished": anchor(
            "crawl-ref/source/god-companions.cc",
            "god-companions.cc orc_apostle_unbanished",
            re.compile(r'getSpeakString\("orc_apostle_unbanished"\)'),
            'getSpeakString("orc_apostle_unbanished")'),
        "marionette": anchor(
            "crawl-ref/source/god-abil.cc",
            "god-abil.cc marionette query",
            re.compile(r'getSpeakString\(target\.name\(DESC_DBNAME\) \+ '
                       r'" marionette"\)'),
            'getSpeakString(target.name(DESC_DBNAME) + " marionette")'),
        "friendly_bfb": anchor(
            "crawl-ref/source/god-abil.cc",
            "god-abil.cc friendly bfb orc",
            re.compile(r'getSpeakString\("friendly bfb orc"\)'),
            'getSpeakString("friendly bfb orc")'),
        "maurice_confused": anchor(
            "crawl-ref/source/monster.cc",
            "monster.cc Maurice confused nonstealing",
            re.compile(r'getSpeakString\("Maurice confused nonstealing"\)'),
            'getSpeakString("Maurice confused nonstealing")'),
        "maurice_nonstealing": anchor(
            "crawl-ref/source/monster.cc",
            "monster.cc Maurice nonstealing",
            re.compile(r'getSpeakString\("Maurice nonstealing"\)'),
            'getSpeakString("Maurice nonstealing")'),
        "riddle": anchor(
            "crawl-ref/source/transform.cc",
            "transform.cc riddle query",
            re.compile(r'getSpeakString\(best_mon->name\(DESC_DBNAME\) \+ '
                       r'" riddle"\)'),
            'getSpeakString(best_mon->name(DESC_DBNAME) + " riddle")'),
        "blink_other": anchor(
            "crawl-ref/source/mon-cast.cc",
            "mon-cast.cc blink_other query",
            re.compile(r'getSpeakString\(mons->name\(DESC_DBNAME\) \+ '
                       r'" blink_other"\)'),
            'getSpeakString(mons->name(DESC_DBNAME) + " blink_other")'),
        "blink_other_close": anchor(
            "crawl-ref/source/mon-cast.cc",
            "mon-cast.cc blink_other_close query",
            re.compile(r'getSpeakString\(mons->name\(DESC_DBNAME\)\s*\+'
                       r'\s*" blink_other_close"\)'),
            'getSpeakString(mons->name(DESC_DBNAME)',
        ),
        "charge": anchor(
            "crawl-ref/source/mon-cast.cc",
            "mon-cast.cc charge query",
            re.compile(r'make_stringf\("%s charge",'),
            'make_stringf("%s charge",',
        ),
        "branch_summon": anchor(
            "crawl-ref/source/mon-cast.cc",
            "mon-cast.cc branch summon cast prefix",
            re.compile(r'getSpeakString\("branch summon cast prefix"\)'),
            'getSpeakString("branch summon cast prefix")'),
        "orc_priest_preaching": anchor(
            "crawl-ref/source/mon-behv.cc",
            "mon-behv.cc orc_priest_preaching",
            re.compile(r'getSpeakString\("orc_priest_preaching"\)'),
            'getSpeakString("orc_priest_preaching")'),
        "orc_priest_apostate": anchor(
            "crawl-ref/source/god-abil.cc",
            "god-abil.cc orc_priest_apostate",
            re.compile(r'getSpeakString\("orc_priest_apostate"\)'),
            'getSpeakString("orc_priest_apostate")'),
        "holy_pacification": anchor(
            "crawl-ref/source/spl-goditem.cc",
            "spl-goditem.cc holy pacification key",
            re.compile(r'string full_key = "holy_being_pacification";'),
            'string full_key = "holy_being_pacification";'),
        "recite_closure": anchor(
            "crawl-ref/source/player-reacts.cc",
            "player-reacts.cc recite_closure",
            re.compile(r'getSpeakString\("recite_closure"\)'),
            'getSpeakString("recite_closure")'),
        "imp_greeting_helper": anchor(
            "crawl-ref/source/spl-summoning.cc",
            "spl-summoning.cc _monster_greeting helper",
            re.compile(r'static void _monster_greeting\('),
            "static void _monster_greeting("),
        "imp_greeting_query": anchor(
            "crawl-ref/source/spl-summoning.cc",
            "spl-summoning.cc helper getSpeakString query",
            re.compile(r'string msg = getSpeakString\(key\);'),
            "string msg = getSpeakString(key);"),
        "imp_greeting_sink": anchor(
            "crawl-ref/source/spl-summoning.cc",
            "spl-summoning.cc helper mons_speaks_msg sink",
            re.compile(r'mons_speaks_msg\(mons, msg, MSGCH_TALK, '
                       r'silenced\(mons->pos\(\)\)\);'),
            "mons_speaks_msg(mons, msg, MSGCH_TALK, "
            "silenced(mons->pos()));"),
        "imp_greeting": anchor(
            "crawl-ref/source/spl-summoning.cc",
            "spl-summoning.cc call-imp greeting",
            re.compile(r'_monster_greeting\(imp, "_friendly_imp_greeting"\);'),
            '_monster_greeting(imp, "_friendly_imp_greeting");'),
        "vault_dbname": anchor(
            "crawl-ref/source/mapdef.cc",
            "mapdef.cc dbname tag parsing",
            re.compile(r'string dbname = strip_tag_prefix\(mon_str, '
                       r'"dbname:"\);'),
            'string dbname = strip_tag_prefix(mon_str, "dbname:");'),
        "vault_name": _vault_name_anchor(oid, label),
    }
    _require(
        facts == FROZEN_PRODUCER_CONSUMER,
        f"{label} producer/consumer anchors drifted from the frozen "
        f"facts: {facts!r}",
    )
    return facts


def _monspeak_definition_lines(
    oid: str, git_path: str, label: str,
) -> dict[str, int]:
    """Source line of the winning definition of every canonical key of one
    monspeak source file, via the production parse layer.

    The EN file legally defines ``_laughs_`` twice; the winner is the
    second definition (DBM_REPLACE), so its line is the winning one."""
    source = shared._decode_utf8(
        shared._git_blob_at_oid(oid, git_path, label), label)
    try:
        definitions = shared.parse_db_keys(source, git_path)
    except SystemExit as exc:
        raise InventoryError(f"{label} TextDB parse failed: {exc}") from exc
    lines: dict[str, int] = {}
    for definition in definitions:
        canonical = shared.lowercase_string(definition.raw_key)
        lines[canonical] = definition.key_line
    return lines


def _override_shout_lines(oid: str, label: str) -> dict[str, int]:
    """Source lines of the seven override keys inside zh/shout.txt.

    The zh/shout.txt definitions shadow the zh/monspeak.txt bodies in the
    effective localized SpeakDB merge; the card evidence records the
    shadowing site."""
    git_path = "crawl-ref/source/dat/database/zh/shout.txt"
    source = shared._decode_utf8(
        shared._git_blob_at_oid(oid, git_path, label), label)
    try:
        definitions = shared.parse_db_keys(source, git_path)
    except SystemExit as exc:
        raise InventoryError(f"{label} zh/shout.txt parse failed: {exc}"
                             ) from exc
    lines = {shared.lowercase_string(d.raw_key): d.key_line
             for d in definitions}
    _require(
        CROSS_DB_OVERRIDE_KEYS <= set(lines),
        f"{label} zh/shout.txt misses override definitions: "
        f"{sorted(CROSS_DB_OVERRIDE_KEYS - set(lines))!r}",
    )
    return {key: lines[key] for key in sorted(CROSS_DB_OVERRIDE_KEYS)}


def _derive_scoped_monspeak_dump(
    oid: str, directory: str, label: str,
) -> dict[str, Any]:
    """Derive the monspeak-scoped dump entries from the exact Git baseline
    using the SpeakDB input sequence (or the localized directory scan)."""
    return hardened.shared._derive_scoped_dump(
        oid, directory, label, source_basename=SOURCE_BASENAME
    )


def _require_scoped_derivation(
    supplied: dict[str, Any], derived: dict[str, Any], label: str,
) -> None:
    """Bind every monspeak-touching entry of the dump to exact Git: the
    same sources and the same scoped history/raw_body/variants."""
    hardened.shared._require_scoped_derivation(
        supplied, derived, label, source_basename=SOURCE_BASENAME
    )


def _raw_monspeak_body(
    oid: str, directory: str, label: str,
) -> dict[str, dict[str, Any]]:
    """Raw per-key bodies of the monspeak source file at the exact OID.

    Used for the seven override keys whose effective dump bodies come from
    zh/shout.txt: their review identities keep the raw monspeak bodies, so
    the variant facts are re-parsed from this source layer."""
    source_name = f"{directory}{SOURCE_BASENAME}"
    git_path = f"crawl-ref/source/dat/{source_name}"
    source = shared._decode_utf8(
        shared._git_blob_at_oid(oid, git_path, label), label)
    try:
        definitions = shared.parse_db_keys(source, git_path)
    except SystemExit as exc:
        raise InventoryError(f"{label} {git_path} parse failed: {exc}"
                             ) from exc
    bodies: dict[str, dict[str, Any]] = {}
    for definition in definitions:
        canonical = shared.lowercase_string(definition.raw_key)
        variants, parse_error = shared._parse_weighted_entry(
            definition.value,
            {"source_name": source_name,
             "load_index": MONSPEAK_SPEAKDB_INDEX,
             "definition_ordinal": len(bodies)},
            canonical,
        )
        bodies[canonical] = {
            "raw_body": definition.value,
            "variants": variants,
            "parse_error": parse_error,
            "body_empty": definition.value == "",
            "key_line": definition.key_line,
        }
    return bodies


def _identity_rows(
    artifact: dict[str, Any], raw: bytes, directory: str, label: str,
    oid: str,
) -> list[dict[str, Any]]:
    """Identity rows of one language: every dump entry whose source history
    touches monspeak.txt.

    Rows whose effective provenance is monspeak.txt keep the dump entry
    verbatim; the seven override rows (effective from zh/shout.txt) keep
    the raw monspeak body re-parsed from the exact-Git source, so the
    review identities always describe the monspeak translation.  The
    override set must equal CROSS_DB_OVERRIDE_KEYS in ZH and be empty in
    EN; the per-language identity and variant totals are frozen."""
    expected_source = f"{directory}{SOURCE_BASENAME}"
    touching = [
        entry for entry in artifact["entries"]
        if any(item["source_name"] == expected_source
               for item in entry["source_history"])
    ]
    raw_bodies = _raw_monspeak_body(oid, directory, label)
    rows: list[dict[str, Any]] = []
    overridden: set[str] = set()
    for entry in sorted(touching, key=lambda item: item["canonical_key"]):
        key = entry["canonical_key"]
        if entry["effective_provenance"]["source_name"] == expected_source:
            _require(
                entry["parse_error"] is None and not entry["body_empty"],
                f"{label} identity {key!r} has a parse error or empty body",
            )
            row = dict(entry)
            row["override"] = False
            row["definition_line"] = None
        else:
            body = raw_bodies[key]
            _require(
                body["parse_error"] is None and not body["body_empty"],
                f"{label} override identity {key!r} raw monspeak body "
                f"has a parse error or empty body",
            )
            row = {
                "canonical_key": key,
                "raw_body": body["raw_body"],
                "variants": body["variants"],
                "parse_error": body["parse_error"],
                "body_empty": body["body_empty"],
                "source_history": entry["source_history"],
                "effective_provenance": entry["effective_provenance"],
                "override": True,
                "definition_line": body["key_line"],
            }
            overridden.add(key)
        rows.append(row)
    expected_override = (
        frozenset() if directory == "database/"
        else CROSS_DB_OVERRIDE_KEYS
    )
    _require(
        overridden == expected_override,
        f"{label} overridden monspeak keys differ: "
        f"{sorted(overridden ^ expected_override)!r}",
    )
    expected_count = (EXPECTED_EN_IDENTITY_COUNT
                      if directory == "database/"
                      else EXPECTED_ZH_IDENTITY_COUNT)
    _require(len(rows) == expected_count,
             f"{label} monspeak identity count mismatch: {len(rows)}")
    keys = [row["canonical_key"] for row in rows]
    _require(len(set(keys)) == len(keys), f"{label} duplicate identity key")
    return rows


def _variant(raw: dict[str, Any],
              lua_protocol: dict[str, Any] | None = None) -> dict[str, Any]:
    text = raw["raw_pattern"]
    variant = {
        "variant_ordinal": raw["locator"]["variant_ordinal"],
        "weight": raw["weight"],
        "text": text,
        "empty": text == "",
        "runtime_tokens": hardened._runtime_tokens(text),
        "random_site_counts": _monspeak_random_site_counts(text),
        "lua_site_count": _monspeak_lua_site_count(text),
        "split_lua": text.count("{{") != text.count("}}"),
    }
    # Candidate-role facts only: they participate in the candidate protocol
    # gate but must not change the frozen baseline ledger shape (the
    # baseline inventory_sha256 is contract-frozen in the ledger metadata).
    if lua_protocol is not None:
        variant["lua_skeletons"] = lua_protocol["skeletons"]
        variant["lua_comparison_literals"] = (
            lua_protocol["comparison_literals"])
        variant["lua_malformed"] = lua_protocol["malformed"]
        # CR-023: the per-site/per-return runtime line channel topology
        # (branch count, per-branch line count and per-line channel).  A
        # malformed block cannot bind a topology; the candidate gate
        # rejects malformed sites later in _dataset anyway, so the empty
        # placeholder never reaches the EN/ZH comparison.
        variant["lua_return_topology"] = (
            _lua_return_topology(text)
            if not lua_protocol["malformed"] else [])
    return variant


def _monspeak_random_site_counts(pattern: str) -> list[int]:
    """Ordered per-site alternative counts of ``[a|b]`` random substrings.

    Production executes embedded Lua at selection time
    (``_execute_embedded_lua``) and only later picks random substrings, so
    ``[`` inside ``{{ }}`` Lua spans is Lua syntax, not a random site.
    Monspeak has no ``[[ ]]`` description substitution outside Lua (frozen
    fact), but the split-Lua ZH fragments carry ``[[ ]]`` long-bracket
    lines; both span kinds are skipped.  An unbalanced span (a split Lua
    fragment) stops the scan: the fragment is recorded as a fact and
    contributes no random site."""
    counts: list[int] = []
    position = 0
    while position < len(pattern):
        lua = pattern.find("{{", position)
        long_bracket = pattern.find("[[", position)
        opening = pattern.find("[", position)
        next_span = min(
            (value for value in (lua, long_bracket) if value >= 0),
            default=-1,
        )
        if next_span >= 0 and (opening < 0 or next_span <= opening):
            closer = "}}" if next_span == lua else "]]"
            end = pattern.find(closer, next_span + 2)
            if end < 0:
                return counts
            position = end + 2
            continue
        if opening < 0:
            break
        closing = pattern.find("]", opening + 1)
        _require(closing >= 0,
                 f"unbalanced random substring marker at offset {opening}")
        nested = pattern.find("[", opening + 1, closing)
        _require(nested < 0,
                 f"nested random substring marker at offset {nested}")
        alternatives = pattern[opening + 1:closing].split("|")
        _require(len(alternatives) >= 2,
                 f"random substring at offset {opening} has no choice")
        counts.append(len(alternatives))
        position = closing + 1
    return counts


def _lua_sites_strict(pattern: str) -> list[dict[str, Any]]:
    """Exact non-overlapping ``{{...}}`` site boundaries of one variant
    (CR-006).

    ``hardened._lua_sites`` validates the ``{{``/``}}`` substring counts,
    but a stray third brace outside the extraction boundary (``}}}`)
    balances those counts while leaving a bare ``}`` behind the site; the
    exact boundary invariant requires every ``{``/``}`` character of the
    pattern to belong to one of the extracted sites."""
    sites = hardened._lua_sites(pattern)
    _require(
        pattern.count("{") == 2 * len(sites)
        and pattern.count("}") == 2 * len(sites),
        f"stray brace outside a {{...}} Lua site boundary in "
        f"pattern {pattern!r}",
    )
    return sites


def _monspeak_lua_site_count(pattern: str) -> int:
    """Lua-site count of one variant.

    A split-Lua fragment (unbalanced ``{{``/``}}`` in isolation) is a
    partial site and counts zero; the fragment itself is recorded in the
    split_lua fact list."""
    if pattern.count("{{") != pattern.count("}}"):
        return 0
    return len(_lua_sites_strict(pattern))


# Marker replacing every translatable ``return <string literal>``
# expression in a Lua block skeleton (CR-002).  All other block bytes stay
# exact.
_LUA_RETURN_MARKER = "__RETURN_DISPLAY__"

# The only non-literal return expressions allowed as translatable display
# text (CR-006): the EN consumer calls the raw Lua helpers and the ZH side
# wraps the same calls in crawl.t_().  Every other return expression
# (arbitrary function calls, arithmetic, booleans) is not display text: it
# stays byte-exact in the skeleton and fails closed.
_LUA_RETURN_DISPLAY_MAPPINGS = frozenset({
    "you.race()",
    "you.genus()",
    "crawl.t_(you.race())",
    "crawl.t_(you.genus())",
})

# CR-006A: the whitelist preserves the exact mapping identity instead of
# folding all four forms into one skeleton marker.  Each declared mapping
# stays byte-exact in the skeleton (``return you.race()`` vs
# ``return crawl.t_(you.race())``), and the paired EN/ZH comparison maps
# every form to its underlying Lua helper so the localizable
# ``crawl.t_()`` wrapper of the same helper is the same display identity,
# while a swapped underlying call (``you.genus()`` for ``you.race()``,
# with or without the wrapper) can never pass.
_LUA_RETURN_UNDERLYING_CALL = {
    "you.race()": "you.race()",
    "you.genus()": "you.genus()",
    "crawl.t_(you.race())": "you.race()",
    "crawl.t_(you.genus())": "you.genus()",
}


def _lua_string_spans(block: str) -> list[tuple[int, int]]:
    """Exact spans of Lua string literals of one block: double-quoted,
    single-quoted (both with backslash escapes) and ``[[ ]]`` long
    brackets.  Fails closed on an unbalanced literal, which would make the
    block non-executable."""
    spans: list[tuple[int, int]] = []
    index = 0
    length = len(block)
    while index < length:
        if block.startswith("[[", index):
            end = block.find("]]", index + 2)
            if end < 0:
                raise InventoryError(
                    f"unbalanced [[ long string in Lua block {block!r}")
            spans.append((index, end + 2))
            index = end + 2
        elif block[index] in "\"'":
            quote = block[index]
            cursor = index + 1
            while cursor < length:
                if block[cursor] == "\\":
                    cursor += 2
                    continue
                if block[cursor] == quote:
                    break
                cursor += 1
            if cursor >= length:
                raise InventoryError(
                    f"unbalanced {quote} string in Lua block {block!r}")
            spans.append((index, cursor + 1))
            index = cursor + 1
        else:
            index += 1
    return spans


def _line_start_offsets(lines: list[str]) -> list[int]:
    """Absolute block offsets of every line start (``\n``-separated)."""
    offsets = [0]
    for line in lines[:-1]:
        offsets.append(offsets[-1] + len(line) + 1)
    return offsets


def _lua_block_protocol(block: str) -> dict[str, Any]:
    """Complete Lua protocol of one ``{{...}}`` block (CR-002).

    ``skeleton`` keeps every non-translatable byte exact: operators,
    control-flow keywords, function calls, comparison literals ("Mummy",
    "Zin", spell names) and whitespace; translatable string-literal
    ``return <display>`` expressions normalize to a fixed marker and the
    declared display mappings keep their exact mapping bytes (CR-006A),
    so EN and ZH skeletons must match byte-for-byte (up to the localizable
    raw-helper/crawl.t_() pairing) while translated display strings may
    differ.  ``comparison_literals`` additionally extracts the
    ``== "..."`` / ``~= "..."`` identity literals as a dedicated fact that
    must stay English.  ``return_strings`` records the display expressions
    (the only translatable part).  ``error`` is set when the block fails
    the structural validity check (stray braces, unbalanced strings,
    unexpected statements, assignment, forbidden control flow) or when a
    return expression is not a string literal / declared display mapping
    (CR-006)."""
    spans = _lua_string_spans(block)
    masked_parts: list[str] = []
    cursor = 0
    comparison_literals: list[str] = []
    for start, end in spans:
        code_before = block[cursor:start]
        if re.search(r"(?:==|~=)\s*$", code_before):
            literal = block[start:end]
            if literal.startswith("[["):
                comparison_literals.append(literal[2:-2])
            else:
                comparison_literals.append(literal[1:-1])
        masked_parts.append(code_before)
        masked_parts.append("\u00a7" + "\n" * block.count("\n", start, end))
        cursor = end
    masked_parts.append(block[cursor:])
    masked = "".join(masked_parts)

    skeleton_lines: list[str] = []
    return_strings: list[str] = []
    unsupported_returns: list[str] = []
    # Masking preserves the line structure (literal contents are replaced by
    # a marker plus their own newlines), so masked and original lines align
    # one-to-one; the masked line decides whether this is a return statement
    # so text inside a multi-line [[ ]] string can never fake one.  Single
    # string literals (``return "..."``/``'...'``/``[[...]]``) are
    # translatable display text and normalize to the marker; the declared
    # display mappings (CR-006) are translatable display expressions too but
    # keep their exact mapping identity byte-for-byte in the skeleton
    # (CR-006A), so EN ``you.race()`` and ZH ``crawl.t_(you.race())`` stay
    # distinguishable from a swapped underlying call.  Any other return
    # expression (arbitrary function call, arithmetic, boolean, ...) is
    # protocol-bound: it stays byte-exact in the skeleton and the block
    # fails closed.
    original_lines = block.split("\n")
    masked_lines = masked.split("\n")
    line_offsets = _line_start_offsets(original_lines)
    index = 0
    while index < len(original_lines):
        original_line = original_lines[index]
        masked_line = masked_lines[index]
        if re.fullmatch(r"return\b.*", masked_line.strip()):
            stripped = original_line.strip()
            original_tail = stripped[len("return"):].strip()
            masked_tail = masked_line.strip()[len("return"):].strip()
            if masked_tail == "\u00a7":
                # The whole return tail is one string literal (possibly a
                # multi-line [[ ]] long string).  The marker column in the
                # masked line is the literal's exact start offset, so the
                # span decides how many continuation lines belong to it and
                # trailing blank lines outside the literal never join the
                # expression.
                literal_start = line_offsets[index] \
                    + masked_line.index("\u00a7")
                literal_span = next(
                    ((start, end) for start, end in spans
                     if start == literal_start),
                    None,
                )
                if literal_span is None:
                    unsupported_returns.append(original_tail)
                    skeleton_lines.append(original_line)
                    index += 1
                    continue
                end_line = block[:literal_span[1]].count("\n")
                expression_lines = [original_tail]
                expression_lines.extend(
                    original_lines[index + 1:end_line + 1])
                return_strings.append("\n".join(expression_lines).strip())
                skeleton_lines.append("return " + _LUA_RETURN_MARKER)
                index = end_line + 1
                continue
            if masked_tail in _LUA_RETURN_DISPLAY_MAPPINGS:
                return_strings.append(original_tail)
                # CR-006A: the exact mapping stays in the skeleton (raw
                # helper vs crawl.t_() wrapper), so the paired EN/ZH
                # comparison can pin the underlying call identity.
                skeleton_lines.append(stripped)
                index += 1
                continue
            unsupported_returns.append(original_tail)
            skeleton_lines.append(original_line)
            index += 1
            continue
        skeleton_lines.append(original_line)
        index += 1

    error = _lua_structure_error(masked)
    if error is None and unsupported_returns:
        error = (
            f"unsupported return expression {unsupported_returns[0]!r}: "
            "only string literals and the declared display mappings "
            "(you.race()/you.genus() and their crawl.t_() forms) may be "
            "treated as translatable display text"
        )
    return {
        "skeleton": "\n".join(skeleton_lines),
        "comparison_literals": sorted(set(comparison_literals)),
        "return_strings": return_strings,
        "error": error,
    }


def _lua_structure_error(masked: str) -> str | None:
    """Structural Lua validity verdict of one block (None == valid).

    Runs on the string-masked code so quoted text can never fake a
    statement: stray braces (the ``{{{`` defect), assignment, forbidden
    control flow, unexpected statements and if/then/end imbalance all
    fail closed.  The candidate gate additionally requires ``luac -p``
    (see ``_lua_syntax_check``)."""
    if "{" in masked or "}" in masked:
        return "stray brace inside Lua site boundary"
    if re.search(r"(?<![=<>~!])=(?!=)", masked):
        return "assignment in Lua block"
    for keyword in ("while", "for", "function", "repeat", "until",
                    "do", "local", "goto"):
        if re.search(rf"\b{keyword}\b", masked):
            return f"forbidden Lua control {keyword!r}"
    if_count = len(re.findall(r"^\s*if\b", masked, re.MULTILINE))
    elseif_count = len(re.findall(r"^\s*elseif\b", masked, re.MULTILINE))
    then_count = len(re.findall(r"\bthen\b", masked))
    end_count = len(re.findall(r"^\s*end\s*$", masked, re.MULTILINE))
    # One ``end`` closes a whole if/elseif/else chain; every ``if`` and
    # every ``elseif`` carries its own ``then``.
    if not (if_count == end_count
            and then_count == if_count + elseif_count):
        return (f"unbalanced Lua if/then/end "
                f"(if {if_count}/elseif {elseif_count}/then "
                f"{then_count}/end {end_count})")
    for line in masked.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if re.fullmatch(r"(?:if|elseif)\b.*\bthen", stripped):
            continue
        if stripped in ("else", "end"):
            continue
        if re.fullmatch(r"return\b.*", stripped):
            continue
        return f"unexpected Lua statement {stripped!r}"
    return None


# The exact ``{{...}}`` site regex of the production pattern layer (also
# used by the scan_i18n.py checker); ``_lua_sites_strict`` validates the
# exact boundaries, this regex only enumerates sites for the runtime
# branch expansion (CR-023).
_LUA_SITE_RE = re.compile(r"\{\{.*?\}\}", re.DOTALL)

# CR-023 Lua-escape table: the escapes the embedded Lua 5.4.8
# interpreter performs on quoted string literals (contrib/lua
# lobject.c luaO_str2num / luaO_hexavalue handling).  Everything else
# fails closed: the runtime text would be ambiguous and the topology
# gate must never guess (the candidate luac -p gate already rejects
# invalid escapes, so only valid escapes can reach this point).
_LUA_ESCAPES = {
    "a": "\a", "b": "\b", "f": "\f", "n": "\n", "r": "\r",
    "t": "\t", "v": "\v", "\\": "\\", "'": "'", '"': '"',
}


# The channel names accepted by strip_channel_prefix's fallback
# str_to_channel() lookup (initfile.cc message_channel_names),
# normalized to the lowercase underscore form.  This mirrors the
# production resolver exactly (message.cc:1463); the scan_i18n.py
# checker imports this classifier so both gates share one identity.
_MONSPEAK_CHANNEL_NAMES = frozenset({
    "plain", "friend_action", "prompt", "god", "duration", "danger",
    "warning", "recovery", "sound", "talk", "talk_visual",
    "intrinsic_gain", "mutation", "monster_spell", "monster_enchant",
    "friend_spell", "friend_enchant", "monster_damage",
    "monster_target", "banishment", "equipment", "floor", "multiturn",
    "examine", "examine_filter", "diagnostic", "error", "tutorial",
    "orb", "timed_portal", "hell_effect", "monster_warning",
    "dgl_message", "decor_flavour", "monster_timeout",
})


def _monspeak_line_channel(line: str) -> str:
    """The msg_channel_type identity one line resolves to through
    resolve_mon_speech_line_channel (mon-speak.cc) /
    strip_channel_prefix (message.cc:1463), with the mons_speaks_msg
    default MSGCH_TALK fallback.  Returns the channel_to_str name for
    equality; only identity is needed (CR-023)."""
    pos = line.find(":")
    if pos < 0:
        return "talk"
    param = line[:pos]
    if param == "WARN" or param == "VISUAL WARN":
        return "warning"
    if param == "SOUND":
        return "sound"
    if param == "VISUAL":
        return "talk_visual"
    if param == "SPELL" or param == "VISUAL SPELL":
        return "monster_spell"
    if param == "ENCHANT" or param == "VISUAL ENCHANT":
        return "monster_enchant"
    normalized = param.replace(" ", "_").lower()
    if normalized == "visual":
        return "talk_visual"
    if normalized == "spell":
        return "monster_spell"
    if normalized in _MONSPEAK_CHANNEL_NAMES:
        return normalized
    return "talk"


def _lua_unescape_literal(body: str) -> str:
    """Runtime value of the body of one quoted Lua string literal: the
    escape processing the embedded Lua 5.4.8 interpreter performs
    (``\\n`` newline, ``\\t`` tab, ``\\r`` CR, ``\\\\`` backslash,
    ``\\'``/``\\\"`` quotes, the ``\\a``/``\\b``/``\\f``/``\\v`` control
    escapes, ``\\xHH`` hex, ``\\ddd`` decimal and ``\\z`` whitespace
    skip).  Any other escape fails closed: the runtime text would be
    ambiguous and the return topology gate must never guess (CR-023)."""
    result: list[str] = []
    index = 0
    length = len(body)
    while index < length:
        char = body[index]
        if char != "\\":
            result.append(char)
            index += 1
            continue
        index += 1
        if index >= length:
            raise InventoryError(
                f"trailing backslash in Lua string literal {body!r}")
        esc = body[index]
        if esc in _LUA_ESCAPES:
            result.append(_LUA_ESCAPES[esc])
            index += 1
            continue
        if esc == "x":
            hex_digits = body[index + 1:index + 3]
            if len(hex_digits) != 2 or not re.fullmatch(
                r"[0-9a-fA-F]{2}", hex_digits
            ):
                raise InventoryError(
                    f"malformed \\x escape in Lua string literal "
                    f"{body!r}")
            result.append(chr(int(hex_digits, 16)))
            index += 3
            continue
        if esc.isdigit():
            match = re.match(r"[0-9]{1,3}", body[index:index + 3])
            value = int(match.group(0))
            if value > 255:
                raise InventoryError(
                    f"decimal escape out of range in Lua string literal "
                    f"{body!r}")
            result.append(chr(value))
            index += match.end()
            continue
        if esc == "z":
            index += 1
            while index < length and body[index] in " \t\n\r\f\v":
                index += 1
            continue
        raise InventoryError(
            f"unsupported Lua escape \\{esc} in string literal {body!r}")
    return "".join(result)


def _lua_literal_value(expression: str) -> str | None:
    """The runtime string value of one literal return expression, or
    None when the expression is not a plain literal (the declared
    display mappings like ``you.race()`` have no statically known
    runtime text)."""
    expression = expression.strip()
    if expression.startswith("[["):
        _require(expression.endswith("]]"),
                 f"unbalanced [[ long string literal {expression!r}")
        return expression[2:-2]
    if len(expression) >= 2 and expression[0] in "\"'" \
            and expression[-1] == expression[0]:
        return _lua_unescape_literal(expression[1:-1])
    return None


def _lua_return_branch_texts(block: str) -> list[str]:
    """Runtime texts of the literal return branches of one ``{{...}}``
    block, in source order (CR-023).

    Reuses ``_lua_block_protocol``'s strict return extraction (CR-002):
    every ``return <string literal>`` display expression is one branch
    and its literal is evaluated to the runtime text the Lua interpreter
    would splice into the message (escape processing included); the
    declared display mappings (``you.race()``/``you.genus()`` and their
    ``crawl.t_()`` forms) have no statically known runtime text and keep
    the colon-free ``{{LUA}}`` placeholder, exactly like the pre-CR-023
    checker neutralization.  Raises ``InventoryError`` on a structurally
    invalid block or an unsupported literal escape: the runtime
    topology must never be guessed."""
    protocol = _lua_block_protocol(block)
    _require(protocol["error"] is None,
             f"Lua block has no bindable return topology: "
             f"{protocol['error']}")
    texts: list[str] = []
    for expression in protocol["return_strings"]:
        value = _lua_literal_value(expression)
        texts.append(value if value is not None else "{{LUA}}")
    return texts


def _runtime_lines_of(message: str) -> list[str]:
    """The production sink line split of one resolved message:
    mons_speaks_msg splits with ``split_string("\\n", msg)``
    (trim_segments=true, accept_empty_segments=false), so every segment
    is trimmed of ASCII whitespace and empty segments never become
    lines."""
    return [segment.strip(" \t\n\r") for segment in message.split("\n")
            if segment.strip(" \t\n\r")]


def _lua_return_branch_lines(pattern: str) -> list[list[str]]:
    """Per-branch runtime line layouts of one monspeak variant pattern
    (CR-023).

    Production order: ``getSpeakString`` evaluates every ``{{...}}`` Lua
    block before the sink and splices the returned string into the
    message; ``mons_speaks_msg`` then splits by ``\\n`` and resolves
    each line's channel.  Every literal return branch of every block is
    therefore a possible runtime message; this helper expands each block
    per return branch (strict extraction from ``_lua_block_protocol``)
    and returns one line layout per branch combination (cross product
    over the blocks, in source order).  Blocks without literal returns
    keep the ``{{LUA}}`` placeholder so their surrounding layout
    survives without a Lua interpreter.  A pattern without Lua blocks
    has exactly one branch: its own lines.  Raises ``InventoryError``
    when any block's return topology cannot be bound."""
    segments: list[list[str]] = []
    position = 0
    for site in _LUA_SITE_RE.finditer(pattern):
        segments.append([pattern[position:site.start()]])
        segments.append(_lua_return_branch_texts(site.group(0)[2:-2]))
        position = site.end()
    segments.append([pattern[position:]])
    branches: list[list[str]] = []
    for combination in itertools.product(*segments):
        branches.append(_runtime_lines_of("".join(combination)))
    return branches


def _lua_return_topology(pattern: str) -> list[list[list[str]]]:
    """Per-site per-branch per-line channel identity of the literal
    return branches of one variant (CR-023).

    Site order follows the ``{{...}}`` sites of the pattern; every site
    maps to one entry per return branch (source order), and each branch
    maps to the channel identity of every runtime line its returned
    string produces under the production sink split.  The declared
    display mappings contribute one ``{{LUA}}`` placeholder branch so
    branch counts stay aligned with the skeleton.  The EN/ZH comparison
    in ``_pair_candidate`` requires these channel topologies to be
    identical: branch count, per-branch line count and per-line channel
    are all encoded in this shape."""
    topology: list[list[list[str]]] = []
    for site in _LUA_SITE_RE.finditer(pattern):
        branches = _lua_return_branch_texts(site.group(0)[2:-2])
        topology.append([
            [_monspeak_line_channel(line)
             for line in _runtime_lines_of(text)]
            for text in branches
        ])
    return topology


# Vendored Lua compiler artifact (CR-006B): the candidate
# executable-syntax gate must use the same Lua the game embeds
# (contrib/lua 5.4.8), never an arbitrary PATH luac -- a 5.1 compiler
# accepts escapes like ``"\\q"`` that 5.4 rejects, so relying on it
# would silently pass non-executable candidate blocks.
_VENDORED_LUAC = (
    Path(__file__).resolve().parents[2]
    / "crawl-ref/source/contrib/lua/src/luac"
)
# The exact embedded contrib/lua version the vendored compiler must report
# (CR-012): a stale build of another Lua release must fail the gate instead
# of validating candidate blocks with different escape semantics.
_VENDORED_LUA_VERSION = "5.4.8"


def _lua_syntax_check(blocks: list[str]) -> dict[str, str]:
    """Executable-syntax gate: every candidate Lua block must pass
    ``luac -p`` (one file per block so a trailing ``return`` can never be
    followed by another chunk).  The vendored contrib/lua 5.4.8 compiler
    artifact is used (CR-006B) and the gate fails closed (CR-012): a
    missing or non-executable vendored compiler, or one whose ``-v``
    output does not report the embedded 5.4.8 version, raises
    ``InventoryError`` instead of falling back to structural validation
    -- an arbitrary PATH luac is never consulted, because a 5.1 compiler
    accepts ``"\\q"`` that 5.4 rejects, so relying on it would silently
    pass non-executable candidate blocks.  Returns the explicit compiler
    fact (``compiler``/``path``/``version``) that the candidate dataset
    records as evidence."""
    if not (_VENDORED_LUAC.is_file()
            and os.access(_VENDORED_LUAC, os.X_OK)):
        raise InventoryError(
            f"vendored contrib/lua {_VENDORED_LUA_VERSION} luac not built "
            f"at {_VENDORED_LUAC}: the candidate Lua executable-syntax "
            "gate fails closed (structural validation alone is not "
            "sufficient, CR-012)")
    version_run = subprocess.run(
        [str(_VENDORED_LUAC), "-v"], capture_output=True, text=True)
    version = (version_run.stdout.strip()
               or version_run.stderr.strip()
               or "")
    if not re.search(rf"\b{re.escape(_VENDORED_LUA_VERSION)}\b", version):
        raise InventoryError(
            f"vendored luac version mismatch: {version!r} does not report "
            f"the embedded contrib/lua {_VENDORED_LUA_VERSION} compiler "
            "(CR-012)")
    for block in blocks:
        with tempfile.NamedTemporaryFile("w", suffix=".lua",
                                         encoding="utf-8") as handle:
            handle.write(block + "\n")
            handle.flush()
            result = subprocess.run(
                [str(_VENDORED_LUAC), "-p", handle.name],
                capture_output=True, text=True)
            if result.returncode != 0:
                raise InventoryError(
                    f"Lua block fails luac -p: {result.stderr.strip()}")
    return {
        "compiler": "vendored",
        "path": str(_VENDORED_LUAC),
        "version": version,
    }


def _lua_protocol(pattern: str, syntax_check: bool = False) -> dict[str, Any]:
    """Complete Lua protocol facts of one variant (CR-002): the exact
    ``{{...}}`` site boundaries, the per-site skeletons, the byte-exact
    comparison literals, the translatable return display strings and the
    structural error list.

    A split-Lua fragment (unbalanced braces in isolation) can never
    execute and contributes no protocol; it is recorded by the split_lua
    fact instead.  With ``syntax_check`` (candidate role) every block must
    be structurally valid and compile under the vendored contrib/lua
    5.4.8 luac (CR-006B); the gate fails closed (CR-012) when the
    vendored compiler is missing, not executable or does not report the
    embedded 5.4.8 version, and records the compiler fact in
    ``lua_syntax_check``."""
    if pattern.count("{{") != pattern.count("}}"):
        return {"site_count": 0, "skeletons": [],
                "comparison_literals": [], "return_strings": [],
                "malformed": [], "lua_syntax_check": None}
    sites = _lua_sites_strict(pattern)
    blocks = hardened._lua_blocks(pattern)
    protocols: list[dict[str, Any]] = []
    for block in blocks:
        try:
            protocols.append(_lua_block_protocol(block))
        except InventoryError as exc:
            protocols.append({"skeleton": block,
                              "comparison_literals": [],
                              "return_strings": [], "error": str(exc)})
    malformed = [protocol["error"]
                 for protocol in protocols if protocol["error"] is not None]
    syntax_fact = None
    if syntax_check and not malformed and blocks:
        syntax_fact = _lua_syntax_check(blocks)
    return {
        "site_count": len(sites),
        "skeletons": [protocol["skeleton"] for protocol in protocols],
        "comparison_literals": sorted({
            literal
            for protocol in protocols
            for literal in protocol["comparison_literals"]
        }),
        "return_strings": [
            expression
            for protocol in protocols
            for expression in protocol["return_strings"]
        ],
        "malformed": malformed,
        "lua_syntax_check": syntax_fact,
    }


def _is_root_key(
    key: str, bases: set[str], prefixes: set[str],
    suffixes: tuple[str, ...],
) -> bool:
    """A key is a direct production root when a prefix sequence from the
    derived prefix space (each prefix used at most once, depth <= 4)
    followed by a base key (optionally with one speak suffix) materializes
    it.  ``default`` is a prefix so the fallback keys are covered."""
    tokens = key.split(" ")
    count = len(tokens)
    prefix_list = sorted(prefixes, key=len, reverse=True)

    def base_suffix(remainder: str) -> bool:
        if remainder in bases:
            return True
        for suffix in suffixes:
            if remainder.endswith(" " + suffix) \
                    and remainder[:-(len(suffix) + 1)] in bases:
                return True
        return False

    def check(index: int, used: frozenset[str]) -> bool:
        if base_suffix(" ".join(tokens[index:])):
            return True
        if index >= count or len(used) >= 4:
            return False
        for prefix in prefix_list:
            if prefix in used:
                continue
            width = len(prefix.split(" "))
            if index + width <= count \
                    and " ".join(tokens[index:index + width]) == prefix \
                    and check(index + width, used | {prefix}):
                return True
        return False

    return check(0, frozenset())


def _special_consumer_roots(keys: set[str], monsters: list[str]) -> set[str]:
    """The fixed-literal and dynamic-name consumer roots present in the key
    space, derived from the exact-Git call sites (regex patterns + name
    suffix materializations)."""
    roots: set[str] = set()
    for key in keys:
        if _TWIN_KEY_RE.match(key) or _TWIN_PREFIX_RE.match(key):
            roots.add(key)
        elif _BEOGH_CONVERT_RE.match(key):
            roots.add(key)
        elif _RECOLLECTION_RE.match(key):
            roots.add(key)
    roots |= FIXED_CONSUMER_LITERALS & keys
    monster_set = set(monsters)
    for name in monster_set:
        roots.update(
            f"{name} {suffix}" for suffix in NAME_SUFFIX_CONSUMERS
            if f"{name} {suffix}" in keys
        )
    return roots


def _token_graph(
    rows: list[dict[str, Any]], keys: set[str],
) -> tuple[dict[str, set[str]], list[dict[str, Any]]]:
    """Directed @token@ edge graph over the identity rows (in-family tokens
    only) plus every token site with its canonical token for later
    classification."""
    edges: dict[str, set[str]] = {key: set() for key in keys}
    sites: list[dict[str, Any]] = []
    for row in rows:
        source = row["canonical_key"]
        for variant in row["variants"]:
            ordinal = variant["locator"]["variant_ordinal"]
            for token in hardened._runtime_tokens(
                variant["raw_pattern"]
            ):
                canonical = token[1:-1].lower()
                sites.append({
                    "key": source,
                    "variant_ordinal": ordinal,
                    "token": token,
                    "canonical_token": canonical,
                })
                if canonical in keys:
                    edges[source].add(canonical)
    return edges, sites


def _reachability(
    edges: dict[str, set[str]], seeds: set[str],
) -> tuple[set[str], dict[str, list[str]]]:
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
    return reached, witnesses


def _classify_tokens(
    rows: list[dict[str, Any]], keys: set[str],
) -> dict[str, Any]:
    """Every token of every variant must be an in-family key (recursive
    edge), a post-processing token of do_mon_str_replacements, or one of
    the five cross-family SpeakDB keys; anything else fails closed."""
    edges, sites = _token_graph(rows, keys)
    recursive: dict[str, list[dict[str, Any]]] = {key: [] for key in keys}
    postprocess_sites: list[dict[str, Any]] = []
    cross_family_sites: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    for site in sites:
        canonical = site["canonical_token"]
        if canonical in keys:
            recursive[canonical].append(site)
        elif canonical in POSTPROCESS_TOKENS:
            postprocess_sites.append(site)
        elif canonical in CROSS_FAMILY_TOKENS:
            cross_family_sites.append(site)
        else:
            unresolved.append(site)
    return {
        "edges": {key: sorted(value) for key, value in sorted(edges.items())},
        "references": {
            key: sorted(value,
                        key=lambda item: (item["key"],
                                          item["variant_ordinal"],
                                          item["token"]))
            for key, value in sorted(recursive.items())
        },
        "postprocess_sites": sorted(
            postprocess_sites,
            key=lambda item: (item["key"], item["variant_ordinal"],
                              item["token"])),
        "cross_family_sites": sorted(
            cross_family_sites,
            key=lambda item: (item["key"], item["variant_ordinal"],
                              item["token"])),
        "unresolved": sorted(
            unresolved,
            key=lambda item: (item["key"], item["variant_ordinal"],
                              item["token"])),
        "distinct_token_count": len({
            site["canonical_token"] for site in sites
        }),
        "infile_token_count": len({
            site["canonical_token"] for site in sites
            if site["canonical_token"] in keys
        }),
        "external_token_count": len({
            site["canonical_token"] for site in sites
            if site["canonical_token"] not in keys
        }),
    }


def _classify_keys(
    rows: list[dict[str, Any]], derivable: dict[str, Any], label: str,
    expected_root_count: int, expected_fragment_count: int, role: str,
) -> dict[str, Any]:
    """Per-language classification: direct roots (prefix materializations +
    special consumers), recursive fragments (token closure), legacy-axed
    (AXED_MON names; empty at baseline) and legacy orphans (unreachable).
    The closure proof requires every non-root, non-orphan identity to be
    reached from the roots, and the frozen orphan/legacy sets must match
    exactly."""
    keys = {row["canonical_key"] for row in rows}
    monsters = set(derivable["monsters"])
    chars = set(derivable["glyph_chars"])
    bases = (monsters | {"player ghost", "pandemonium lord"}
             | set(derivable["shapes"]) | _glyph_bases(chars)
             | set(derivable["vault_dbnames"]))
    prefixes = (set(derivable["static_prefixes"])
                | set(derivable["gods"]) | set(derivable["branches"])
                | set(derivable["skills"]))
    roots = {
        key for key in keys
        if _is_root_key(key, bases, prefixes, SPEAK_SUFFIXES)
    }
    roots |= _special_consumer_roots(keys, derivable["monsters"])

    edges, _sites = _token_graph(rows, keys)
    reached, witnesses = _reachability(edges, roots)
    orphans = keys - reached
    fragments = reached - roots
    non_underscore = sorted(
        key for key in fragments
        if not (key.startswith("_") and key.endswith("_")))
    axed = set(derivable["axed"]) & keys
    _require(
        not axed,
        f"{label} AXED_MON name became a monspeak key: {sorted(axed)!r}",
    )
    if role == "baseline":
        _require(
            len(roots) == expected_root_count,
            f"{label} derived root key count mismatch: {len(roots)}",
        )
        _require(
            len(fragments) == expected_fragment_count,
            f"{label} recursive fragment count mismatch: "
            f"{len(fragments)}",
        )
        _require(
            all(key.startswith("_") and key.endswith("_")
                for key in fragments),
            f"{label} non-underscore recursive fragment: "
            f"{non_underscore}",
        )
    return {
        "keys": keys,
        "roots": roots,
        "fragments": fragments,
        "orphans": orphans,
        "witnesses": witnesses,
        "bases": bases,
        "prefixes": prefixes,
        "axed": axed,
    }


def _dataset(
    artifact: dict[str, Any], raw: bytes, directory: str, label: str,
    role: str, derivable: dict[str, Any], oid: str,
    expected_variant_count: int | None = None,
) -> dict[str, Any]:
    rows = _identity_rows(artifact, raw, directory, label, oid)
    keys = {row["canonical_key"] for row in rows}
    expected_root_count, expected_fragment_count = {
        "database/": (EXPECTED_ROOT_COUNT, EXPECTED_FRAGMENT_COUNT),
        "database/zh/": (EXPECTED_ZH_ROOT_COUNT,
                         EXPECTED_ZH_FRAGMENT_COUNT),
    }[directory]
    classified = _classify_keys(rows, derivable, label,
                                expected_root_count,
                                expected_fragment_count, role)
    expected_orphans = (
        EXPECTED_EN_ORPHANS
        if directory == "database/"
        else EXPECTED_EN_ORPHANS | EXPECTED_ZH_EXTRA_ORPHANS
    )
    if role == "baseline":
        _require(
            classified["orphans"] == expected_orphans,
            f"{label} orphan set differs: "
            f"{sorted(classified['orphans'] ^ expected_orphans)!r}",
        )
        expected_orphan_count = (EXPECTED_EN_ORPHAN_COUNT
                                 if directory == "database/"
                                 else EXPECTED_ZH_ORPHAN_COUNT)
        _require(len(classified["orphans"]) == expected_orphan_count,
                 f"{label} orphan count mismatch: "
                 f"{len(classified['orphans'])}")
    else:
        # The review may only shrink the orphan set (restoring inlined
        # fragment references); the ZH-only keys are exempt because the
        # aligned candidate legitimately orphans them (their EN bodies do
        # not reference the ZH-only fragments).
        exempt = ZH_ONLY_KEYS if directory == "database/zh/" else frozenset()
        _require(
            classified["orphans"] - exempt <= expected_orphans,
            f"{label} candidate introduced orphan keys outside the "
            f"baseline set: "
            f"{sorted((classified['orphans'] - exempt) - expected_orphans)!r}",
        )
    token_facts = _classify_tokens(rows, keys)
    if role == "baseline":
        expected_tokens = {
            "database/": (EXPECTED_EN_DISTINCT_TOKENS,
                          EXPECTED_EN_INFILE_TOKENS,
                          EXPECTED_EN_EXTERNAL_TOKENS),
            "database/zh/": (EXPECTED_ZH_DISTINCT_TOKENS,
                             EXPECTED_ZH_INFILE_TOKENS,
                             EXPECTED_ZH_EXTERNAL_TOKENS),
        }[directory]
        _require(
            (token_facts["distinct_token_count"],
             token_facts["infile_token_count"],
             token_facts["external_token_count"]) == expected_tokens,
            f"{label} token classification counts differ: "
            f"{token_facts['distinct_token_count']}/"
            f"{token_facts['infile_token_count']}/"
            f"{token_facts['external_token_count']}",
        )
    _require(not token_facts["unresolved"],
             f"{label} contains unresolved token: "
             f"{token_facts['unresolved'][:3]!r}")

    entries = []
    split_lua: list[list[int | str]] = []
    malformed_lua: list[list[int | str]] = []
    empty_variants = 0
    total_variants = 0
    random_sites = 0
    lua_sites = 0
    # Candidate-role Lua compiler facts (CR-006B/CR-012): every variant
    # that reached the executable-syntax gate records the same vendored
    # 5.4.8 compiler fact; a missing compiler or a version mismatch fails
    # the candidate audit closed instead of falling back to structural
    # validation.
    lua_syntax_facts: list[dict[str, Any]] = []
    # Baseline-historical counts of the EN-only display tokens (frozen
    # fact, asserted for ZH only; the candidate may legitimately differ).
    en_only_display_counts: Counter = Counter()
    for row in sorted(rows, key=lambda item: item["canonical_key"]):
        key = row["canonical_key"]
        variants = []
        for raw_variant in row["variants"]:
            protocol = _lua_protocol(raw_variant["raw_pattern"],
                                     syntax_check=role == "candidate")
            if protocol["lua_syntax_check"] is not None:
                lua_syntax_facts.append(protocol["lua_syntax_check"])
            if role == "candidate":
                variants.append(_variant(raw_variant, protocol))
            else:
                variants.append(_variant(raw_variant))
            if protocol["malformed"]:
                malformed_lua.append(
                    [key, raw_variant["locator"]["variant_ordinal"]])
        total_variants += len(variants)
        for variant in variants:
            en_only_display_counts.update(
                token for token in variant["runtime_tokens"]
                if token in EN_ONLY_DISPLAY_TOKENS)
            random_sites += len(variant["random_site_counts"])
            lua_sites += variant["lua_site_count"]
            if variant["split_lua"]:
                split_lua.append([key, variant["variant_ordinal"]])
            if variant["empty"]:
                empty_variants += 1
        entries.append({
            "key": key,
            "source_line": (row["definition_line"]
                            if row["override"]
                            else _monspeak_source_line(artifact, directory,
                                                       row, label)),
            "override": row["override"],
            "variants": variants,
        })
    expected_variant = (EXPECTED_EN_VARIANT_COUNT
                        if directory == "database/"
                        else EXPECTED_ZH_VARIANT_COUNT)
    if role == "baseline":
        _require(total_variants == expected_variant,
                 f"{label} baseline variant count mismatch: "
                 f"{total_variants}")
        expected_split_lua = ([] if directory == "database/"
                              else EXPECTED_SPLIT_LUA_FRAGMENTS)
        _require(
            split_lua == expected_split_lua,
            f"{label} split Lua fragments differ: {split_lua!r}",
        )
        expected_empty = (EXPECTED_EN_EMPTY_VARIANTS
                          if directory == "database/"
                          else EXPECTED_ZH_EMPTY_VARIANTS)
        _require(empty_variants == expected_empty,
                 f"{label} empty variant count mismatch: {empty_variants}")
        expected_random = (EXPECTED_EN_RANDOM_SITES
                           if directory == "database/"
                           else EXPECTED_ZH_RANDOM_SITES)
        _require(random_sites == expected_random,
                 f"{label} baseline random-site count mismatch: "
                 f"{random_sites}")
        expected_lua = (EXPECTED_EN_LUA_SITES
                        if directory == "database/"
                        else EXPECTED_ZH_LUA_SITES)
        _require(lua_sites == expected_lua,
                 f"{label} baseline Lua-site count mismatch: {lua_sites}")
        expected_malformed_lua = ([] if directory == "database/"
                                  else EXPECTED_ZH_MALFORMED_LUA_SITES)
        _require(
            malformed_lua == expected_malformed_lua,
            f"{label} malformed Lua sites differ: {malformed_lua!r}",
        )
        if directory == "database/zh/":
            _require(
                dict(en_only_display_counts)
                == EXPECTED_ZH_BASELINE_EN_ONLY_COUNTS,
                f"{label} baseline ZH EN-only display token counts "
                f"differ: {dict(en_only_display_counts)!r}",
            )
    else:
        _require(expected_variant_count is not None,
                 f"{label} candidate audit requires the approved variant "
                 f"total")
        _require(total_variants == expected_variant_count,
                 f"{label} candidate variant count differs from the "
                 f"approved total: {total_variants}")
        _require(
            not malformed_lua,
            f"{label} candidate has malformed Lua sites "
            f"(stray braces / non-executable blocks): {malformed_lua!r}",
        )
        # CR-007: the candidate protocol invariants are enforced on the
        # complete EN/ZH dataset, not only on the shared keys the pair
        # loop covers: the two ZH-only keys (`_jory_rare_`, `default 'j'`)
        # must also be free of empty variants and split-Lua fragments, and
        # the aligned candidate must reproduce the frozen EN random/Lua
        # site totals exactly.
        _require(empty_variants == 0,
                 f"{label} candidate has empty variants: {empty_variants}")
        _require(not split_lua,
                 f"{label} candidate has split Lua fragments: "
                 f"{split_lua!r}")
        _require(random_sites == EXPECTED_EN_RANDOM_SITES,
                 f"{label} candidate random-site count differs from the "
                 f"frozen EN total: {random_sites}")
        _require(lua_sites == EXPECTED_EN_LUA_SITES,
                 f"{label} candidate Lua-site count differs from the "
                 f"frozen EN total: {lua_sites}")
        # CR-006B/CR-012: every Lua-bearing variant records the same
        # vendored 5.4.8 compiler fact; the gate fails closed when the
        # vendored compiler is missing or its version mismatches, so the
        # fact is recorded as candidate evidence only after the exact
        # compiler proved itself.
        _require(lua_syntax_facts and all(
            fact == lua_syntax_facts[0] for fact in lua_syntax_facts),
            f"{label} candidate Lua syntax-check facts differ")

    source_snapshot = next(
        source for source in artifact["sources"]
        if source["source_name"] == f"{directory}{SOURCE_BASENAME}"
    )
    syntax_fact = (lua_syntax_facts[0] if lua_syntax_facts else None)
    dataset = {
        "artifact_sha256": _sha256(raw),
        "source_name": f"{directory}{SOURCE_BASENAME}",
        "source_sha256": _sha256(
            source_snapshot["normalized_utf8"].encode("utf-8")),
        "entries": entries,
        "token_facts": token_facts,
        "reachability": {
            "reachable": sorted(classified["keys"] - classified["orphans"]),
            "witnesses": classified["witnesses"],
        },
        "variant_count": total_variants,
        "random_site_count": random_sites,
        "lua_site_count": lua_sites,
        "empty_variant_count": empty_variants,
        "split_lua_fragments": split_lua,
        "identity_count": len(entries),
        "root_key_count": len(classified["roots"]),
        "fragment_key_count": len(classified["fragments"]),
        "orphan_key_count": len(classified["orphans"]),
        "root_keys": sorted(classified["roots"]),
        "fragment_keys": sorted(classified["fragments"]),
        "orphan_keys": sorted(classified["orphans"]),
        "legacy_axed_keys": sorted(classified["axed"]),
        "producer_facts": {
            "static_prefix_count": len(derivable["static_prefixes"]),
            "monster_producer_count": len(derivable["monsters"]),
            "glyph_char_count": len(derivable["glyph_chars"]),
            "shape_key_count": len(derivable["shapes"]),
            "god_prefix_count": len(derivable["gods"]),
            "branch_prefix_count": len(derivable["branches"]),
            "skill_prefix_count": len(derivable["skills"]),
            "axed_monster_count": len(derivable["axed"]),
            "vault_dbname_count": len(derivable["vault_dbnames"]),
        },
    }
    # Candidate-role compiler evidence (CR-006B); the baseline inventory
    # shape stays byte-stable without the key.
    if role == "candidate":
        dataset["lua_syntax_check"] = syntax_fact
    return dataset


def _monspeak_source_line(
    artifact: dict[str, Any], directory: str,
    row: dict[str, Any], label: str,
) -> int:
    """Source line of the winning monspeak definition of one row.

    The production parse layer defines the canonical keys; ``_laughs_`` is
    the only EN key defined twice, so the winning line is the second
    definition (DBM_REPLACE)."""
    source_name = f"{directory}{SOURCE_BASENAME}"
    snapshot = next(
        source for source in artifact["sources"]
        if source["source_name"] == source_name
    )
    lines = _definition_lines(snapshot["normalized_utf8"],
                              f"{label} {source_name}")
    return lines[row["canonical_key"]]


def _definition_lines(source: str, label: str) -> dict[str, int]:
    try:
        definitions = shared.parse_db_keys(source, label)
    except SystemExit as exc:
        raise InventoryError(f"{label} TextDB parse failed: {exc}") from exc
    lines: dict[str, int] = {}
    for definition in definitions:
        canonical = shared.lowercase_string(definition.raw_key)
        lines[canonical] = definition.key_line
    return lines


def _hashed_dataset(dataset: dict[str, Any]) -> dict[str, Any]:
    """The byte-stable inventory view of one dataset (classification sets
    are evidence, not inventory facts; the hashed core stays byte-identical
    while the classification itself is production-derived)."""
    return {key: value for key, value in dataset.items()
            if key not in {"entries", "root_keys", "fragment_keys",
                           "orphan_keys", "legacy_axed_keys",
                           "producer_facts"}}


def _read_glossary(path: Path, ref: str | None) -> bytes:
    if ref is None:
        return hardened._read_artifact_bytes(path, "glossary")
    return hardened._candidate_regular_blob(
        ref, hardened._repo_relative_git_path(path, "glossary"), "glossary"
    )


def _load_dataset(
    ref: str, path: Path, directory: str, label: str, role: str,
    expected_variant_count: int | None = None,
) -> dict[str, Any]:
    shared._validate_oid(ref, label)
    _require_regular_monspeak_git_sources(ref, directory, label)
    artifact, raw = hardened._load_dump_safe(
        path, label, directory, expected_database="speak"
    )
    derived = _derive_scoped_monspeak_dump(ref, directory, label)
    _require_scoped_derivation(artifact, derived, label)
    derivable = _derivable_root_facts(ref, label, role=role)
    return _dataset(artifact, raw, directory, label, role, derivable, ref,
                    expected_variant_count=expected_variant_count)


def _lifecycle_for(key: str, dataset: dict[str, Any]) -> str:
    if key in dataset["root_keys"]:
        return "direct-production-root"
    if key in dataset["fragment_keys"]:
        return "recursive-internal-fragment"
    if key in dataset["legacy_axed_keys"]:
        return "legacy-axed-monster"
    if key in dataset["orphan_keys"]:
        return "legacy-orphaned"
    return "zh-only"


def _card_consumer_anchor(
    key: str, lifecycle: str, facts: dict[str, Any],
) -> tuple[tuple[str, ...], ...]:
    """The producer/consumer anchor names for one card per lifecycle."""
    if lifecycle == "recursive-internal-fragment":
        return (("recursive_expansion",),)
    if lifecycle in ("legacy-orphaned", "legacy-axed-monster", "zh-only"):
        return ()
    if key == "_friendly_imp_greeting":
        # CR-017: the card binds the complete call-imp data flow -- the
        # spl-summoning.cc call site plus the _monster_greeting helper's
        # declaration, its exact getSpeakString(key) query and the
        # mons_speaks_msg display sink -- so removing or reshaping any
        # step fails the frozen anchor proof closed.
        return (("imp_greeting", "imp_greeting_helper",
                 "imp_greeting_query", "imp_greeting_sink"),)
    # CR-015: the seven cross-DB override keys keep their zh/shout.txt
    # override provenance in evidence_locations only; the card consumer
    # evidence names the real production lookup path per key (the glyph
    # fallback for ''&'', the exact-key monspeak lookup for the named
    # monsters and player ghost) instead of the vault dbname parser.
    if key in CROSS_DB_OVERRIDE_CONSUMERS:
        return ((CROSS_DB_OVERRIDE_CONSUMERS[key],),)
    if key in VAULT_DBNAME_KEYS:
        return (("vault_dbname",),)
    if key in VAULT_NAME_KEYS:
        return (("vault_name",),)
    if key == "_laughs_":
        return (("laughs",),)
    if key == "branch summon cast prefix":
        return (("branch_summon",),)
    if key == "recite_closure":
        return (("recite_closure",),)
    if key.startswith("holy_being_pacification"):
        return (("holy_pacification",),)
    if key == "orc_priest_preaching":
        return (("orc_priest_preaching",),)
    if key == "orc_priest_apostate":
        return (("orc_priest_apostate",),)
    if key in ("gozag bribe", "gozag permabribe"):
        return (("gozag_bribe",),)
    if key == "friendly bfb orc":
        return (("friendly_bfb",),)
    if key == "maurice confused nonstealing":
        return (("maurice_confused",),)
    if key == "maurice nonstealing":
        return (("maurice_nonstealing",),)
    if key in ("beogh apostle challenge", "orc_apostle_yield",
               "orc_apostle_dismissed", "orc_apostle_unbanished"):
        return (("apostle_challenge" if key == "beogh apostle challenge"
                 else f"apostle_{key.split('_', 2)[2]}",),)
    if key.startswith("nobody_recollection "):
        return (("recollection",),)
    if key.startswith("beogh_converted_orc_"):
        return (("beogh_convert",),)
    if _TWIN_KEY_RE.match(key) or _TWIN_PREFIX_RE.match(key):
        return (("twin_death",),)
    if key.endswith(" marionette"):
        return (("marionette",),)
    if key.endswith(" riddle"):
        return (("riddle",),)
    if key.endswith(" blink_other_close"):
        return (("blink_other_close",),)
    if key.endswith(" blink_other"):
        return (("blink_other",),)
    if key.endswith(" charge"):
        return (("charge",),)
    if key.startswith("default "):
        return (("default_three", "default_bare"),)
    if _GLYPH_KEY_RE.match(key):
        return (("glyph_consumer",),)
    if key in facts["shape_keys"]:
        return (("shape_consumer",),)
    for suffix in sorted(SPEAK_SUFFIXES, key=len, reverse=True):
        if key.endswith(" " + suffix):
            name = ("permanently" if suffix == "permanently killed"
                    else suffix.replace(" ", "_"))
            return ((f"suffix_{name}",),)
    return (("monspeak_consumer",),)


def _card_facts(inventory: dict[str, Any]) -> dict[str, Any]:
    """The card-factory evidence view: the frozen producer/consumer
    anchors plus the shape-key set and the localized override lines."""
    facts = dict(inventory["scope"]["producer_consumer"])
    facts["shape_keys"] = set(inventory["scope"]["shape_keys"])
    facts["override_shout_lines"] = dict(
        inventory["scope"]["override_shout_lines"])
    return facts


def _card_producer_consumer(
    entry: dict[str, Any], facts: dict[str, Any],
) -> dict[str, Any]:
    """The applicable producer/consumer evidence for one card: the loader
    plus the lifecycle-specific consumer anchors."""
    anchors = _card_consumer_anchor(entry["key"], entry["lifecycle"], facts)
    result = {"loader": facts["loader"]}
    for anchor_names in anchors:
        for name in anchor_names:
            result[name] = facts[name]
    return result


def _evidence_locations(
    entry: dict[str, Any], facts: dict[str, Any],
) -> list[str]:
    """Mechanically derived per-card evidence locations: the EN/ZH
    definition sites (ZH-only cards have no EN site) plus every recursive
    reference site from the frozen baseline token classification, extended
    with the localized override source for the seven shadowed keys."""
    sites: list[str] = []
    if entry["english_source_line"] is not None:
        sites.append(
            f"crawl-ref/source/dat/database/{SOURCE_BASENAME}:"
            f"{entry['english_source_line']}")
    sites.append(
        f"crawl-ref/source/dat/database/zh/{SOURCE_BASENAME}:"
        f"{entry['chinese_source_line']}")
    sites.extend(
        f"recursive-ref:{site['key']}:{site['variant_ordinal']}"
        for site in entry["english_referencing_sites"]
    )
    sites.extend(
        f"recursive-ref-zh:{site['key']}:{site['variant_ordinal']}"
        for site in entry["chinese_referencing_sites"]
    )
    if entry["key"] in CROSS_DB_OVERRIDE_KEYS:
        sites.append(
            f"localized-override:database/zh/shout.txt:"
            f"{facts['override_shout_lines'][entry['key']]}")
    return sites


def build_inventory(
    baseline_ref: str, english_path: Path, localized_path: Path,
    glossary_path: Path, glossary_ref: str | None = None,
) -> dict[str, Any]:
    en = _load_dataset(baseline_ref, english_path, "database/",
                       "baseline EN", "baseline")
    zh = _load_dataset(baseline_ref, localized_path, "database/zh/",
                       "baseline ZH", "baseline")
    entries, asymmetry = _pair_entries(en, zh)
    producer_consumer = _producer_consumer_facts(
        baseline_ref, "baseline producer/consumer")
    facts = {
        **producer_consumer,
        "shape_keys": _shape_keys(baseline_ref, "baseline shapes"),
        "override_shout_lines": _override_shout_lines(
            baseline_ref, "baseline override lines"),
    }
    scope = {
        "source_basename": SOURCE_BASENAME,
        "expected_identity_counts": {
            "english": EXPECTED_EN_IDENTITY_COUNT,
            "chinese": EXPECTED_ZH_IDENTITY_COUNT,
            "total": EXPECTED_IDENTITY_COUNT,
        },
        "zh_only_keys": sorted(ZH_ONLY_KEYS),
        "override_keys": sorted(CROSS_DB_OVERRIDE_KEYS),
        "root_key_count": en["root_key_count"],
        "fragment_key_count": en["fragment_key_count"],
        "orphan_key_count": {
            "english": en["orphan_key_count"],
            "chinese": zh["orphan_key_count"],
        },
        "legacy_axed_keys": en["legacy_axed_keys"],
        "root_keys": sorted({entry["key"] for entry in entries
                             if entry["lifecycle"]
                             == "direct-production-root"}),
        "fragment_keys": en["fragment_keys"],
        "orphan_keys": {
            "english": en["orphan_keys"],
            "chinese": zh["orphan_keys"],
        },
        "static_prefixes": sorted(STATIC_PREFIXES),
        "speak_suffixes": list(SPEAK_SUFFIXES),
        "shape_keys": sorted(facts["shape_keys"]),
        "override_shout_lines": dict(facts["override_shout_lines"]),
        "producer_facts": en["producer_facts"],
        "postprocess_tokens": sorted(POSTPROCESS_TOKENS),
        "cross_family_tokens": sorted(CROSS_FAMILY_TOKENS),
        "baseline_variant_counts": {
            "english": en["variant_count"],
            "chinese": zh["variant_count"],
        },
        "baseline_random_sites": {
            "english": en["random_site_count"],
            "chinese": zh["random_site_count"],
        },
        "baseline_lua_sites": {
            "english": en["lua_site_count"],
            "chinese": zh["lua_site_count"],
        },
        "baseline_empty_variants": {
            "english": en["empty_variant_count"],
            "chinese": zh["empty_variant_count"],
        },
        "split_lua_fragments": zh["split_lua_fragments"],
        "baseline_asymmetry": {
            key: asymmetry[key] for key in sorted(asymmetry)
        },
        "provenance": {
            "speakdb": {"monspeak.txt": MONSPEAK_SPEAKDB_INDEX},
        },
        "producer_consumer": producer_consumer,
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


def _pair_entries(
    en: dict[str, Any], zh: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, list[int]]]:
    """Pair every EN identity with its ZH counterpart; the two ZH-only keys
    become single-sided cards.  The 213 asymmetric facts must match the
    frozen list exactly."""
    en_by_key = {entry["key"]: entry for entry in en["entries"]}
    zh_by_key = {entry["key"]: entry for entry in zh["entries"]}
    _require(set(en_by_key) - set(zh_by_key) == frozenset(),
             "EN-only monspeak keys appeared")
    _require(set(zh_by_key) - set(en_by_key) == ZH_ONLY_KEYS,
             f"ZH-only monspeak keys differ: "
             f"{sorted((set(zh_by_key) - set(en_by_key)) ^ ZH_ONLY_KEYS)!r}")
    entries: list[dict[str, Any]] = []
    asymmetry: dict[str, list[int]] = {}
    for key in sorted(en_by_key):
        en_entry, zh_entry = en_by_key[key], zh_by_key[key]
        counts = [len(en_entry["variants"]), len(zh_entry["variants"])]
        if counts[0] != counts[1]:
            asymmetry[key] = counts
        lifecycle = _lifecycle_for(key, en)
        entries.append({
            "identity": f"monspeak:{key}",
            "key": key,
            "lifecycle": lifecycle,
            "dependency_group": _group_for(key, lifecycle),
            "english_source_line": en_entry["source_line"],
            "chinese_source_line": zh_entry["source_line"],
            "english_variants": en_entry["variants"],
            "chinese_variants": zh_entry["variants"],
            "english_referencing_sites": en["token_facts"]["references"][key],
            "chinese_referencing_sites": zh["token_facts"]["references"][key],
        })
    for key in sorted(ZH_ONLY_KEYS):
        zh_entry = zh_by_key[key]
        entries.append({
            "identity": f"monspeak:{key}",
            "key": key,
            "lifecycle": "zh-only",
            "dependency_group": "ZH-only 键（EN 无对应，裁决待翻译阶段）",
            "english_source_line": None,
            "chinese_source_line": zh_entry["source_line"],
            "english_variants": [],
            "chinese_variants": zh_entry["variants"],
            "english_referencing_sites": [],
            "chinese_referencing_sites":
                zh["token_facts"]["references"].get(key, []),
        })
    _require(
        len(asymmetry) == len(EXPECTED_ASYM) and asymmetry == EXPECTED_ASYM,
        f"baseline asymmetric key facts changed: {asymmetry!r}",
    )
    _require(len(entries) == EXPECTED_IDENTITY_COUNT,
             f"ledger identity count mismatch: {len(entries)}")
    return entries, asymmetry


def _group_for(key: str, lifecycle: str) -> str:
    if lifecycle == "zh-only":
        return "ZH-only 键（EN 无对应，裁决待翻译阶段）"
    if lifecycle == "legacy-orphaned":
        return "遗留孤儿键（无消费路径，裁决待翻译阶段）"
    if lifecycle == "legacy-axed-monster":
        return "遗留怪物名键（AXED_MON）"
    if lifecycle == "recursive-internal-fragment":
        return "递归内部碎片（@token@ 闭包）"
    if _TWIN_KEY_RE.match(key) or _TWIN_PREFIX_RE.match(key):
        return "Dowan/Duvessa 双胞胎死亡键（mon-death.cc）"
    if key.startswith("beogh_converted_orc_"):
        return "Beogh 转化兽人键（attitude-change.cc）"
    if key.startswith("nobody_recollection "):
        return "Nobody 记忆键（mon-abil.cc）"
    if key in ("gozag bribe", "gozag permabribe"):
        return "Gozag 贿赂键（attitude-change.cc）"
    if key.startswith("orc_apostle_") or key == "beogh apostle challenge":
        return "Beogh 使徒键（god-companions.cc）"
    if key in ("orc_priest_preaching", "orc_priest_apostate"):
        return "兽人祭司键（mon-behv.cc / god-abil.cc）"
    if key in ("maurice nonstealing", "maurice confused nonstealing"):
        return "Maurice 偷窃键（monster.cc）"
    if key.endswith(" marionette"):
        return "傀儡控制键（god-abil.cc）"
    if key.endswith(" riddle"):
        return "斯芬克斯谜语键（transform.cc）"
    if key.endswith(" blink_other") or key.endswith(" blink_other_close"):
        return "瞬移他人键（mon-cast.cc）"
    if key.endswith(" charge"):
        return "充能键（mon-cast.cc）"
    if key == "branch summon cast prefix":
        return "召唤前缀键（mon-cast.cc）"
    if key.startswith("holy_being_pacification"):
        return "圣化安抚键（spl-goditem.cc）"
    if key == "recite_closure":
        return "诵经键（player-reacts.cc）"
    if key == "_laughs_":
        return "笑声碎片键（mon-util.cc 直查）"
    if key == "_friendly_imp_greeting":
        return "召唤小恶魔问候键（spl-summoning.cc）"
    if key in VAULT_DBNAME_KEYS or key in VAULT_NAME_KEYS:
        return "地牢 dbname:/name: 标签键（mapdef.cc）"
    if key.startswith("default "):
        return "默认回退键（default <prefix> <key> 链）"
    if _GLYPH_KEY_RE.match(key):
        return "字形回退键（mons_base_char）"
    for suffix in SPEAK_SUFFIXES:
        if key.endswith(" " + suffix):
            return f"后缀键（<base> {suffix}）"
    return "怪物/前缀直查键（mon-speak.cc）"


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
        _require(isinstance(variant["text"], str),
                 f"{context} ordinal {ordinal} text mismatch")
        _monspeak_random_site_counts(variant["text"])
        _monspeak_lua_site_count(variant["text"])


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
        "en_variant_count": EXPECTED_EN_VARIANT_COUNT,
        "english_production_dump_sha256":
            inventory["dumps"]["english"]["artifact_sha256"],
        "glossary_sha256": inventory["glossary"]["sha256"],
        "identity_count": EXPECTED_IDENTITY_COUNT,
        "inventory_sha256": inventory["inventory_sha256"],
        "terminal_conclusion_counts": dict(sorted(Counter(conclusions).items())),
        "zh_variant_count": EXPECTED_ZH_VARIANT_COUNT,
    }


def validate_results(
    path: Path, inventory: dict[str, Any],
    candidate: dict[str, Any] | None = None,
    records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    records = records if records is not None else _strict_block(path)
    _require(len(records) == EXPECTED_IDENTITY_COUNT + 1,
             "review results require one metadata record and 733 cards")
    metadata, cards = records[0], records[1:]
    _require(set(metadata) == METADATA_FIELDS, "review metadata fields mismatch")
    _require(metadata == _expected_metadata(inventory, cards),
             "review metadata mismatch")
    by_identity = {entry["identity"]: entry for entry in inventory["entries"]}
    _require(len({card.get("identity") for card in cards}) == len(cards),
             "duplicate review identity")
    _require([card.get("identity") for card in cards] == sorted(by_identity),
             "review cards must cover every identity in deterministic order")
    proposals: dict[str, dict[str, list[dict[str, Any]]]] = {}
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
        # The EN source is frozen for this review: proposals may only
        # change the ZH side, never the EN identities (CR-003).
        _require(card["proposed_english_variants"] == current_en,
                 f"review card {identity} proposed EN must equal the "
                 f"baseline EN variants")
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
                 == _evidence_locations(entry, _card_facts(inventory)),
                 f"review card {identity} evidence locations mismatch")
        _require(isinstance(card["rejected_alternatives"], list)
                 and card["rejected_alternatives"],
                 f"review card {identity} requires rejected alternatives")
        _require(isinstance(card["producer_consumer"], dict)
                 and card["producer_consumer"],
                 f"review card {identity} requires producer/consumer evidence")
        _require(card["producer_consumer"]
                 == _card_producer_consumer(entry, _card_facts(inventory)),
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
        # Ledger proposal validation uses the same rule as the candidate
        # protocol gate: every proposal must equal the audited candidate
        # verbatim (below), and the candidate passed the EN-only display
        # token exception of _pair_candidate's _foe_protocol_equal, so the
        # proposed ZH token multisets are validated by the same normalized
        # comparison transitively.
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


def _foe_family_counts(
    tokens: list[str],
) -> tuple[Counter, int, int]:
    """Split one runtime-token list into the strict other-token multiset,
    the bare ``@foe@`` count and the EN-only display compound count.

    Only the exact lowercase tokens participate: ``@Foe@``/``@foe,@`` and
    friends are ordinary strictly-aligned tokens, while the alternative
    forms ``@to_foe/<alt>@``/``@at_foe/<alt>@`` (e.g. ``at_foe/around``)
    are EN-only display compounds (I70-R4-CR-009A) exactly like their
    exact ``@to_foe@``/``@at_foe@`` counterparts."""
    other: Counter = Counter()
    foe = 0
    compounds = 0
    for token in tokens:
        if _is_en_only_display_token(token):
            compounds += 1
        elif token == "@foe@":
            foe += 1
        else:
            other[token] += 1
    return other, foe, compounds


def _foe_protocol_equal(
    en_tokens: list[str], zh_tokens: list[str],
) -> bool:
    """Paired EN/ZH token alignment under the EN-only display-token
    exception.

    ``do_mon_str_replacements()`` expands ``@to_foe@``/``@at_foe@`` and
    their ``/<alt>`` forms into `` to @foe@``/`` at @foe@`` (monster-foe
    branch), deletes the leading-space compound (player-foe branch) or
    expands the alternative literally (e.g. ``around``) -- so the
    localizable core of either compound is the ``@foe@`` reference and
    the alternative forms are equally EN-only display syntax
    (I70-R4-CR-009A).  The comparison therefore keeps every non-foe-family
    token exactly equal and applies two bidirectional ``@foe@`` bounds to
    the foe family:

    - ``zh_foe >= en_foe``: every bare ``@foe@`` of the EN variant must be
      preserved as a bare ``@foe@`` in ZH (a compound cannot replace it,
      because the player-foe branch deletes compounds entirely);
    - ``zh_foe + zh_compounds <= en_foe + en_compounds``: ZH may convert
      EN compounds into bare ``@foe@`` or drop them, but may never invent
      a foe reference that EN does not have.

    Together these accept the aligned mirror structure, the localizable
    ``@foe@`` structure and sentence rewrites that omit the addressee,
    while rejecting drift of every other token and invented ``@foe@``
    references.  EN keeps its exact baseline bytes: the EN counts and
    positions are validated by the EN source/dump byte binding, not by
    this comparison."""
    en_other, en_foe, en_compounds = _foe_family_counts(en_tokens)
    zh_other, zh_foe, zh_compounds = _foe_family_counts(zh_tokens)
    return (
        en_other == zh_other
        and zh_foe >= en_foe
        and zh_foe + zh_compounds <= en_foe + en_compounds
    )


def _lua_skeletons_equal(
    en_skeletons: list[str], zh_skeletons: list[str],
) -> bool:
    """Byte equality of one variant's EN/ZH Lua skeletons under the
    display-mapping equivalence (CR-006A).

    String-literal returns normalize to the fixed marker; the declared
    display mappings stay byte-exact in the skeleton.  The paired
    comparison treats the raw Lua helper and its localizable
    ``crawl.t_()`` wrapper as the same display mapping (same underlying
    call), so EN ``you.race()`` correctly pairs with ZH
    ``crawl.t_(you.race())``.  A swapped underlying call (``you.genus()``
    for ``you.race()``, with or without the wrapper), an added/removed
    wrapper around a different call, and every other byte drift
    (operators, comparison literals, whitespace inside the expression)
    fail the comparison."""
    if len(en_skeletons) != len(zh_skeletons):
        return False
    for en_line, zh_line in zip(en_skeletons, zh_skeletons):
        if en_line == zh_line:
            continue
        en_call = _LUA_RETURN_UNDERLYING_CALL.get(
            en_line.strip()[len("return "):])
        zh_call = _LUA_RETURN_UNDERLYING_CALL.get(
            zh_line.strip()[len("return "):])
        if en_call is not None and en_call == zh_call:
            continue
        return False
    return True


def _pair_candidate(en: dict[str, Any], zh: dict[str, Any]) -> list[dict[str, Any]]:
    en_by_key = {entry["key"]: entry for entry in en["entries"]}
    zh_by_key = {entry["key"]: entry for entry in zh["entries"]}
    _require(en_by_key.keys() == zh_by_key.keys() - ZH_ONLY_KEYS,
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
                _foe_protocol_equal(en_variant["runtime_tokens"],
                                    zh_variant["runtime_tokens"]),
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
            _require(
                en_variant["split_lua"] == zh_variant["split_lua"],
                f"candidate split-Lua topology differs at {key!r} ordinal "
                f"{ordinal}",
            )
            _require(
                en_variant["lua_comparison_literals"]
                == zh_variant["lua_comparison_literals"],
                f"candidate Lua comparison literals differ at {key!r} "
                f"ordinal {ordinal} (identity literals like \"Mummy\"/"
                f"\"Zin\" must stay English)",
            )
            _require(
                _lua_skeletons_equal(en_variant["lua_skeletons"],
                                     zh_variant["lua_skeletons"]),
                f"candidate Lua control skeleton/operators differ at "
                f"{key!r} ordinal {ordinal}",
            )
            # CR-023: the Lua return channel topology (per-site branch
            # count, per-branch runtime line layout and per-line channel
            # identity) must be identical: a return whose VISUAL prefix
            # changed, a return branch deleted or a per-branch line shift
            # inside a Lua block fails here even though the masked
            # skeletons stay byte-identical.
            _require(
                en_variant["lua_return_topology"]
                == zh_variant["lua_return_topology"],
                f"candidate Lua return channel topology differs at "
                f"{key!r} ordinal {ordinal}",
            )
        entries.append({
            "identity": f"monspeak:{key}",
            "key": key,
            "english_variants": en_entry["variants"],
            "chinese_variants": zh_entry["variants"],
        })
    for key in sorted(ZH_ONLY_KEYS):
        _require(key in zh_by_key,
                 f"candidate dropped the ZH-only key {key!r}")
        entries.append({
            "identity": f"monspeak:{key}",
            "key": key,
            "english_variants": [],
            "chinese_variants": zh_by_key[key]["variants"],
        })
    return entries


def _proposal_variant_totals(records: list[dict[str, Any]]) -> dict[str, int]:
    """Per-side proposed variant totals of the review ledger (evidence
    only).  The candidate gate freezes 3429/3431 and never derives its
    expectation from these editable proposals (CR-003)."""
    totals = {"english": 0, "chinese": 0}
    for card in records[1:]:
        totals["english"] += len(card["proposed_english_variants"])
        totals["chinese"] += len(card["proposed_chinese_variants"])
    return totals


def add_candidate(
    inventory: dict[str, Any], baseline_ref: str, candidate_ref: str,
    english_path: Path, localized_path: Path,
) -> dict[str, Any]:
    hardened.shared._require_candidate_commit(
        baseline_ref, candidate_ref, exact_clean_checkout=True
    )
    # Frozen candidate totals (CR-003): the candidate EN is byte-bound to
    # the baseline EN (3429) and the aligned ZH is the 3429 shared
    # EN-aligned variants plus the two single-variant ZH-only keys (3431).
    # They are never derived from the editable review ledger.
    expected_variant_counts = {
        "english": EXPECTED_CANDIDATE_EN_VARIANT_COUNT,
        "chinese": EXPECTED_CANDIDATE_ZH_VARIANT_COUNT,
    }
    en = _load_dataset(
        candidate_ref, english_path, "database/",
        "candidate EN", "candidate",
        expected_variant_count=expected_variant_counts["english"],
    )
    zh = _load_dataset(
        candidate_ref, localized_path, "database/zh/",
        "candidate ZH", "candidate",
        expected_variant_count=expected_variant_counts["chinese"],
    )
    _require(
        _producer_consumer_facts(candidate_ref, "candidate producer/consumer")
        == inventory["scope"]["producer_consumer"],
        "candidate producer/consumer anchors differ from the baseline facts",
    )
    _require(not en["token_facts"]["unresolved"],
             "candidate EN contains unresolved token")
    _require(not zh["token_facts"]["unresolved"],
             "candidate ZH contains unresolved token")
    # The candidate EN source snapshot and the complete EN entries/variants
    # are hard-bound to the baseline EN bytes: any EN edit (even one that
    # keeps the variant totals) fails the candidate audit (CR-003).
    _require(
        en["source_sha256"]
        == inventory["dumps"]["english"]["source_sha256"],
        "candidate EN source snapshot must equal the baseline EN source",
    )
    _require(
        en["artifact_sha256"]
        == inventory["dumps"]["english"]["artifact_sha256"],
        "candidate EN dump must equal the baseline EN dump",
    )
    ledger_en_by_key = {
        entry["key"]: _variant_review_shape(entry["english_variants"])
        for entry in inventory["entries"]
    }
    candidate_en_by_key = {entry["key"]: entry
                           for entry in en["entries"]}
    for key in sorted(candidate_en_by_key):
        _require(
            _variant_review_shape(candidate_en_by_key[key]["variants"])
            == ledger_en_by_key[key],
            f"candidate EN drift at {key!r}: the complete EN variants "
            f"must equal the baseline EN variants",
        )
    _require(
        set(en["orphan_keys"]) <= set(
            inventory["scope"]["orphan_keys"]["english"])
        and (set(zh["orphan_keys"]) - ZH_ONLY_KEYS) <= set(
            inventory["scope"]["orphan_keys"]["chinese"]),
        "candidate orphan classification must not grow beyond the "
        "baseline set",
    )
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
    """One empty ledger card bound to the frozen baseline facts."""
    current_en = _variant_review_shape(entry["english_variants"])
    current_zh = _variant_review_shape(entry["chinese_variants"])
    lifecycle = entry["lifecycle"]
    if lifecycle == "direct-production-root":
        display_context = (
            "mon-speak.cc / 固定消费点直接查询的根键（前缀+基键+后缀与 "
            "default 回退链）；展开后经 do_mon_str_replacements 处理，以"
            "声音/视觉频道显示。"
        )
    elif lifecycle == "recursive-internal-fragment":
        display_context = (
            "仅由根键闭包经 @token@ 递归展开的内部碎片；不能脱离调用点"
            "独立解释。"
        )
    elif lifecycle == "legacy-axed-monster":
        display_context = (
            "AXED_MON 遗留键：当前没有怪物类型产生该 DB 名，运行时不可达；"
            "仅作为历史遗留翻译保留在账本中。"
        )
    elif lifecycle == "legacy-orphaned":
        display_context = (
            "遗留孤儿键：无消费路径（拼写/过时/孤立碎片），运行时不可达；"
            "保留或删除的裁决待翻译阶段。"
        )
    else:
        display_context = (
            "ZH-only 键：EN 无对应 key，仅存在于 zh/monspeak.txt；保留或"
            "删除的裁决待翻译阶段。"
        )
    return {
        "identity": entry["identity"],
        "key": entry["key"],
        "lifecycle": lifecycle,
        "dependency_group": entry["dependency_group"],
        "display_context": display_context,
        "producer_consumer": _card_producer_consumer(
            entry, _card_facts(inventory)),
        "evidence_locations": _evidence_locations(
            entry, _card_facts(inventory)),
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
    component is a symlink, exactly like the shout scaffold; the whole
    create-verify-write-publish lifecycle, including rollback of any
    partial write, is owned by the shared decorlines hardened write
    transaction."""
    cards = [_skeleton_card(inventory, entry)
             for entry in inventory["entries"]]
    cards.sort(key=lambda card: card["identity"])
    records = [_expected_metadata(inventory, cards), *cards]
    text = (
        "# Monspeak 全量审核结果（Issue #70）\n\n"
        "本文件的严格 JSONL 块是 733 个 frozen identity 的完整审核账本。"
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

# Frozen consumer/producer evidence anchors for the SpeakDB loader, the
# mon-speak.cc lookup chain, the fixed/dynamic consumer call sites and the
# vault dbname tag parser.  The values are the exact-Git anchor lines at
# the baseline OID; _producer_consumer_facts re-derives every anchor from
# the exact Git sources with snippet checks and must reproduce this object
# verbatim, so a moved initializer/call site fails closed instead of
# silently re-anchoring the ledger evidence.
FROZEN_PRODUCER_CONSUMER = {
    "loader": "crawl-ref/source/database.cc:120",
    "recursive_expansion": "crawl-ref/source/database.cc:1364",
    "monspeak_index": 0,
    "monspeak_consumer": "crawl-ref/source/mon-speak.cc:89",
    "default_three": "crawl-ref/source/mon-speak.cc:233",
    "default_bare": "crawl-ref/source/mon-speak.cc:271",
    "suffix_triumphant": "crawl-ref/source/mon-speak.cc:284",
    "suffix_banished": "crawl-ref/source/mon-speak.cc:286",
    "suffix_killed": "crawl-ref/source/mon-speak.cc:297",
    "suffix_permanently": "crawl-ref/source/mon-speak.cc:295",
    "suffix_timeout": "crawl-ref/source/mon-speak.cc:300",
    "glyph_consumer": "crawl-ref/source/mon-speak.cc:729",
    "shape_consumer": "crawl-ref/source/mon-speak.cc:755",
    "replacement_consumer": "crawl-ref/source/mon-util.cc:4348",
    "laughs": "crawl-ref/source/mon-util.cc:984",
    "twin_death": "crawl-ref/source/mon-death.cc:4222",
    "beogh_convert": "crawl-ref/source/attitude-change.cc:163",
    "gozag_bribe": "crawl-ref/source/attitude-change.cc:342",
    "recollection": "crawl-ref/source/mon-abil.cc:1484",
    "apostle_challenge": "crawl-ref/source/god-companions.cc:489",
    "apostle_yield": "crawl-ref/source/god-companions.cc:609",
    "apostle_dismissed": "crawl-ref/source/god-companions.cc:820",
    "apostle_unbanished": "crawl-ref/source/god-companions.cc:1059",
    "marionette": "crawl-ref/source/god-abil.cc:3202",
    "friendly_bfb": "crawl-ref/source/god-abil.cc:2635",
    "maurice_confused": "crawl-ref/source/monster.cc:6258",
    "maurice_nonstealing": "crawl-ref/source/monster.cc:6329",
    "riddle": "crawl-ref/source/transform.cc:2554",
    "blink_other": "crawl-ref/source/mon-cast.cc:8183",
    "blink_other_close": "crawl-ref/source/mon-cast.cc:8195",
    "charge": "crawl-ref/source/mon-cast.cc:6790",
    "branch_summon": "crawl-ref/source/mon-cast.cc:6558",
    "orc_priest_preaching": "crawl-ref/source/mon-behv.cc:1404",
    "orc_priest_apostate": "crawl-ref/source/god-abil.cc:2507",
    "holy_pacification": "crawl-ref/source/spl-goditem.cc:58",
    "recite_closure": "crawl-ref/source/player-reacts.cc:651",
    "imp_greeting_helper": "crawl-ref/source/spl-summoning.cc:81",
    "imp_greeting_query": "crawl-ref/source/spl-summoning.cc:83",
    "imp_greeting_sink": "crawl-ref/source/spl-summoning.cc:86",
    "imp_greeting": "crawl-ref/source/spl-summoning.cc:1108",
    "vault_dbname": "crawl-ref/source/mapdef.cc:4113",
    "vault_name": "crawl-ref/source/dat/des/altar/overflow.des:2590",
}


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InventoryError as exc:
        print(f"monspeak_inventory.py: {exc}", file=sys.stderr)
        raise SystemExit(2)
