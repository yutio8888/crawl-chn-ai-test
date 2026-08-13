#!/usr/bin/env python3
"""Build and audit the Issue #60 wpnnoise inventory from production dumps.

The supplied ``textdb-phase0-dump`` artifacts (EN and ZH) remain the artifacts
under review.  This narrow entry reuses ``monflee_inventory`` for exact-Git
source discovery, TextDB parsing, weighted-variant derivation, artifact
validation, hashing, candidate binding, and safe output.  Only wpnnoise's
consumer-specific invariants and strict review schema live here.

The baseline inventory stays frozen at the pre-landing shape (731 EN / 720 ZH,
including the six asymmetric keys and every one-sided ordinal fact).  The
strict review card schema v2 adds ``reviewed_actions``: per-card action records
bound to baseline source locators and exact proposed/removed text that
represent reviewed one-sided structural changes (EN-only missing variants
approved for addition, the ZH-only orphan approved for removal, positional
kazoo realignment).  The candidate gate walks baseline and candidate ZH
variants with those actions (add ordinals are candidate positions, remove
ordinals are baseline positions) and proves: English is byte-identical to the
baseline; every candidate ZH variant is either an approved add matching the
baseline EN variant's protocol, or the reviewed proposal (or a kept shifted
variant under an in-range add placeholder) with the mapped baseline ZH
protocol (weight/control/ordered tokens/random sites/complete Lua blocks)
unchanged; any unreviewed key/weight/control/token/Lua/random-site drift or
one-sided change fails closed.  Matched slots are compared only against the
mapped baseline ZH variant -- there is no generic same-ordinal EN envelope --
except for exactly one approved, card-local ``protocol_transition`` record
bound to key+ordinal, the exact baseline protocol, the exact
candidate/proposed text and the exact new protocol.  Every proposed
translation is also derived back to protocol facts during card validation,
so a candidate and its review ledger cannot jointly reroute a channel or
change token/Lua/random-site expansion.

Reachability is proven, not assumed: the directed recursive-token graph is
built independently for EN and ZH and traversed from every ROOT_KEYS member;
the complete non-root closure must equal the fragment set (disconnected
cycles and self-loops fail closed) and every fragment gets a deterministic
root-to-fragment witness recorded in the inventory evidence/digest.

Mutable artifacts (production dumps, review results, glossary) are read
through the repository audited snapshot helper: one no-follow descriptor, a
regular-file requirement, and opened-inode identity verification, never a
reopened pathname.  In the candidate flow the review ledger and glossary are
read directly from the exact candidate commit tree as regular-file blobs, and
the exact-clean candidate boundary is proven before any candidate data is
consumed.

Production boundary (frozen at the Issue #60 baseline):

- EN source: ``crawl-ref/source/dat/database/wpnnoise.txt``
- ZH source: ``crawl-ref/source/dat/database/zh/wpnnoise.txt``
- Loader: ``TextDB("speak", "database/", ...)`` in database.cc; wpnnoise.txt is
  the fourth SpeakDB source.  Other SpeakDB files only participate in load
  order, collision and effective-provenance proof; their translations are not
  owned here.
- Consumers: ``shout.cc::noisy_equipment``/``item_noise`` (noisy randarts and
  unrands), ``art-func.h`` Singing Sword tiers, shield of the gong, Majin-Bo
  and Zonguldrok wrappers, fungal fisticloak thoughts, and the eel-hand
  flavour messages in ``player-reacts.cc``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import deque
from pathlib import Path
from typing import Any

import i18n_shared as audit_inputs
import monflee_inventory as shared
from audit_monspell_phase0 import ArtifactError, validate_artifact
from command_inventory import parse_db_keys


# The inventory schema is unchanged: the baseline inventory digest must stay
# immutable.  Only the strict review evidence schema moved to v2.
SCHEMA_VERSION = 1
SOURCE_BASENAME = "wpnnoise.txt"
STRICT_BEGIN = "<!-- BEGIN STRICT WPNNOISE REVIEW EVIDENCE v2 -->"
STRICT_END = "<!-- END STRICT WPNNOISE REVIEW EVIDENCE v2 -->"

# shout.cc item_noise routes these leading "X:" prefixes to channels; any
# other leading "X:" stays literal text, so an unrecognized control fails
# closed here instead of silently displaying a raw prefix.
ALLOWED_CONTROLS = {
    None, "DANGER", "ENCHANT", "PLAIN", "SOUND", "SPELL", "TALK", "VISUAL",
    "WARN",
}

# Frozen Issue #60 baseline shape (verified against the production dumps).
EXPECTED_IDENTITY_COUNT = 65
EXPECTED_EN_VARIANT_COUNT = 731
EXPECTED_ZH_VARIANT_COUNT = 720
EXPECTED_EN_RANDOM_SITES = 84
EXPECTED_ZH_RANDOM_SITES = 83
EXPECTED_EN_LUA_SITES = 2
EXPECTED_ZH_LUA_SITES = 3
EXPECTED_EN_VISUAL_PREFIXES = 6
EXPECTED_ZH_VISUAL_PREFIXES = 6
EXPECTED_EN_SOUND_PREFIXES = 1
EXPECTED_ZH_SOUND_PREFIXES = 1
EXPECTED_STATIC_ONLY_COUNT = 0

# Lua comparison strings are protocol identities (you.god() == "No God") and
# must never be translated.  The union across both languages must equal this
# frozen set exactly.
LUA_COMPARISON_STRINGS = ("No God",)

# Direct production roots with current callers.  Reachability for every other
# key is proven by the recursive token closure, never assumed.
ROOT_KEYS = (
    "shield of the gong",
    "frozen axe \"frostbite\"",
    "trishula \"condemnation\"",
    "noisy weapon",
    "singing sword silenced",
    "singing sword no_tension",
    "singing sword low_tension",
    "singing sword high_tension",
    "singing sword scream",
    "majin-bo greeting",
    "majin-bo cast",
    "majin-bo cast weak",
    "zonguldrok greeting",
    "zonguldrok reprise",
    "zonguldrok farewell",
    "zonguldrok hat good",
    "zonguldrok hat okay",
    "zonguldrok hat bad",
    "zonguldrok hat crown of dyrovepreva",
    "zonguldrok hat crown of vainglory",
    "zonguldrok hat hat of pondering",
    "zonguldrok hat hat of the alchemist",
    "zonguldrok hat hat of the bear spirit",
    "zonguldrok hat hood of the assassin",
    "zonguldrok hat mask of the dragon",
    "fungus thoughts",
    "eel hand actions",
    "eel hand solo actions",
)

# Per-key EN/ZH variant counts frozen at the baseline.  One-sided variants
# (EN-only or ZH-only ordinals) are baseline facts: the review covers every ZH
# variant production can emit, and EN-only ordinals stay EN-side facts.
ASYMMETRIC_VARIANT_KEYS = {
    "_instrumental_noises_": (13, 12),
    "_real_song_no_tension_": (21, 19),
    "_scream_": (71, 70),
    "_speaking_high_tension_": (32, 33),
    "fungus thoughts": (14, 7),
    "weapon_noise": (39, 38),
}

# Review dependency groups order the audit so shared roots are reviewed
# together.  Fragments shared between families (weapon_noises,
# _instrumental_noises_, _weapon_chatter_) follow their primary family.
DEPENDENCY_GROUP = {
    "shield of the gong": "锣盾：声音频道与固定响度",
    "frozen axe \"frostbite\"": "噪音神器武器：寒冷环境拟声",
    "trishula \"condemnation\"": "噪音神器武器：审判呼号",
    "noisy weapon": "噪音武器：随机聊天与拟声族",
    "_weapon_chatter_": "噪音武器：随机聊天与拟声族",
    "_rare_chatter_": "噪音武器：随机聊天与拟声族",
    "weapon_noises": "噪音武器：随机聊天与拟声族",
    "_instrumental_noises_": "噪音武器：随机聊天与拟声族",
    "weapon_noise": "噪音武器：随机聊天与拟声族",
    "singing sword silenced": "唱歌剑：静默/张力层级",
    "singing sword no_tension": "唱歌剑：静默/张力层级",
    "singing sword low_tension": "唱歌剑：静默/张力层级",
    "singing sword high_tension": "唱歌剑：静默/张力层级",
    "singing sword scream": "唱歌剑：静默/张力层级",
    "_weapon_noises_low-high_tension_": "唱歌剑：张力碎片",
    "_singing_no_tension_": "唱歌剑：张力碎片",
    "_singing_no-low_tension_": "唱歌剑：张力碎片",
    "_speaking_no_tension_": "唱歌剑：张力碎片",
    "_common_speaking_no_tension_": "唱歌剑：张力碎片",
    "_rare_speaking_no_tension_": "唱歌剑：张力碎片",
    "_speaking_low_tension_": "唱歌剑：张力碎片",
    "_speaking_low-high_tension_": "唱歌剑：张力碎片",
    "_speaking_high_tension_": "唱歌剑：张力碎片",
    "_godless_sorter_": "唱歌剑：张力碎片",
    "_scream_": "唱歌剑：张力碎片",
    "_real_song_no_tension_": "唱歌剑：张力碎片",
    "_real_song_low_tension_": "唱歌剑：张力碎片",
    "_real_song_low-high_tension_": "唱歌剑：张力碎片",
    "_real_song_high_tension_": "唱歌剑：张力碎片",
    "_screams_": "唱歌剑：张力碎片",
    "_screams_how_": "唱歌剑：张力碎片",
    "_loudly_": "唱歌剑：张力碎片",
    "_beastly_adjective_": "唱歌剑：张力碎片",
    "_beast_": "唱歌剑：张力碎片",
    "_strikes_up_what_": "唱歌剑：张力碎片",
    "_kind_of_scales_": "唱歌剑：张力碎片",
    "_rhyme_word_": "唱歌剑：张力碎片",
    "_song_theme_": "唱歌剑：张力碎片",
    "_musical_topic_": "唱歌剑：张力碎片",
    "_exasperated_": "唱歌剑：张力碎片",
    "_crimson_": "唱歌剑：张力碎片",
    "_miscreants_": "唱歌剑：张力碎片",
    "_pets_": "唱歌剑：张力碎片",
    "_corpses_": "唱歌剑：张力碎片",
    "_body_part_": "唱歌剑：张力碎片",
    "_glorious_": "唱歌剑：张力碎片",
    "majin-bo greeting": "马金魔杖：低语包装",
    "majin-bo cast": "马金魔杖：低语包装",
    "majin-bo cast weak": "马金魔杖：低语包装",
    "zonguldrok greeting": "宗古德洛克：低语包装",
    "zonguldrok reprise": "宗古德洛克：低语包装",
    "zonguldrok farewell": "宗古德洛克：低语包装",
    "zonguldrok hat good": "宗古德洛克：帽子评论",
    "zonguldrok hat okay": "宗古德洛克：帽子评论",
    "zonguldrok hat bad": "宗古德洛克：帽子评论",
    "zonguldrok hat crown of dyrovepreva": "宗古德洛克：帽子评论",
    "zonguldrok hat crown of vainglory": "宗古德洛克：帽子评论",
    "zonguldrok hat hat of pondering": "宗古德洛克：帽子评论",
    "zonguldrok hat hat of the alchemist": "宗古德洛克：帽子评论",
    "zonguldrok hat hat of the bear spirit": "宗古德洛克：帽子评论",
    "zonguldrok hat hood of the assassin": "宗古德洛克：帽子评论",
    "zonguldrok hat mask of the dragon": "宗古德洛克：帽子评论",
    "fungus thoughts": "菌皮斗篷：思想絮语",
    "eel hand actions": "电鳗之手：风味消息",
    "eel hand solo actions": "电鳗之手：风味消息",
}

# Frozen per-route runtime evidence.  Fragments (RECURSIVE) reach production
# only through SpeakDB recursive token expansion; the referencing sites are
# computed per identity and frozen into the entry.
FROZEN_CONSUMER = {
    "NOISY_EQUIPMENT": {
        "localized_lookup_and_recursion": "crawl-ref/source/database.cc:2307",
        "en_name_lookup": "crawl-ref/source/shout.cc:386",
        "channel_routing_and_expansion": "crawl-ref/source/shout.cc:304",
        "noise_trigger": "crawl-ref/source/melee-attack.cc:2011",
    },
    "SINGING_SWORD": {
        "localized_lookup_and_recursion": "crawl-ref/source/database.cc:2307",
        "tier_selection": "crawl-ref/source/art-func.h:355",
        "channel_routing_and_expansion": "crawl-ref/source/shout.cc:304",
    },
    "GONG": {
        "localized_lookup": "crawl-ref/source/database.cc:2307",
        "direct_display": "crawl-ref/source/art-func.h:481",
        "sound_sink": "crawl-ref/source/art-func.h:484",
        "loudness": "crawl-ref/source/art-func.h:486",
    },
    "WHISPER": {
        "localized_lookup": "crawl-ref/source/database.cc:2307",
        "whisper_wrap": "crawl-ref/source/art-func.h:1208",
        "cast_wrap": "crawl-ref/source/spl-cast.cc:851",
        "zonguldrok_wrap": "crawl-ref/source/art-func.h:1871",
        "hat_wrap": "crawl-ref/source/player-equip.cc:2218",
    },
    "FUNGUS": {
        "localized_lookup": "crawl-ref/source/database.cc:2307",
        "equip_display": "crawl-ref/source/art-func.h:1894",
        "world_reacts_display": "crawl-ref/source/art-func.h:1913",
    },
    "EEL": {
        "localized_lookup": "crawl-ref/source/database.cc:2307",
        "solo_lookup": "crawl-ref/source/player-reacts.cc:1280",
        "action_lookup": "crawl-ref/source/player-reacts.cc:1282",
        "head_skin_replacement": "crawl-ref/source/player-reacts.cc:1286",
        "talk_sink": "crawl-ref/source/player-reacts.cc:1291",
    },
    "RECURSIVE": {
        "localized_lookup": "crawl-ref/source/database.cc:2307",
        "recursive_expansion": "crawl-ref/source/database.cc:1497",
        "marker_replacement": "crawl-ref/source/database.cc:1386",
        "lua_execution": "crawl-ref/source/database.cc:526",
    },
}

FROZEN_ACTUAL_BEHAVIOR = {
    "NOISY_EQUIPMENT": (
        "melee-attack 在玩家以带 ARTP_NOISE 属性的神器武器攻击时调用 noisy_equipment："
        "非随机神器以 ScopedLangEn 取得稳定英文限定名查询；空结果回退 noisy weapon，"
        "选中正文恰为 NONE 时显式抑制。随后进入 item_noise：按前缀路由频道"
        "（SOUND/PLAIN/TALK/VISUAL/DANGER/WARN/SPELL/ENCHANT，未知前缀保留为字面文本），"
        "替换 @The_weapon@/@the_weapon@/@Your_weapon@/@your_weapon@/@weapon@、"
        "@player_name@、@player_god@、@player_genus@/@a_player_genus@/"
        "@player_genus_plural@，展开 [a|b] 随机子串与 @CAPS@…@NOCAPS@，按频道 mprf；"
        "非 TALK_VISUAL 频道调用 noisy(20)。"
    ),
    "SINGING_SWORD": (
        "art-func 按沉默与 tension 选择 silenced/no_tension/low_tension/high_tension/"
        "SCREAM key，以 loudness {0,0,20,30,40} 进入 item_noise；tier 同时决定 "
        "sonic-wave 行为，但本批只审核显示消息。item_noise 的路由、token、随机子串与 "
        "@CAPS@ 展开同 NOISY_EQUIPMENT。"
    ),
    "GONG": (
        "带盾击触发时以稳定英文 key 查询 shield of the gong；空结果回退 "
        "\"You hear a strange loud sound.\"；不做 token/随机/控制前缀处理，"
        "直接以 MSGCH_SOUND 显示并 noisy(40)。"
    ),
    "WHISPER": (
        "装备/施法触发时以 A voice whispers, \"…\"（T_ 包装）包裹 SpeakDB 选中正文，"
        "经 MSGCH_TALK 显示；不做 token/随机/控制前缀处理。zonguldrok hat 系列 key 由 "
        "_zonguldrok_comment_on_hat 按 artefact/brand/普通以及神器英文名派生。"
    ),
    "FUNGUS": (
        "装备时经 _equip_mpr 显示，world_reacts 以 MSGCH_TALK 显示；"
        "不做 token/随机/控制前缀处理。"
    ),
    "EEL": (
        "无邻近敌人时由 _do_eel_flavour_msg 选择 solo/actions key，替换 @head@（无形态时 "
        "为 form）与 @skin@（species::skin_name），直接以 MSGCH_TALK 显示；"
        "不执行 maybe_pick_random_substring，因此 [a|b] 括号保持字面文本。"
    ),
    "RECURSIVE": (
        "由 getSpeakString 经 _getRandomisedStr 的递归 token 展开（@key@ 查找 SpeakDB "
        "canonical key，未命中保持原样），随后 _execute_embedded_lua 执行 {{ }} 代码块；"
        "Lua 比较字符串（如 \"No God\"）为协议身份，不得翻译。"
    ),
}

FROZEN_DISPLAY_CONTEXT = {
    "NOISY_EQUIPMENT": "玩家持握噪音神器武器攻击时经 item_noise 产生的玩家可见消息；"
                       "频道由控制前缀决定（默认 MSGCH_TALK）。",
    "SINGING_SWORD": "唱歌剑按静默/张力层级产生的玩家可见消息；频道由控制前缀决定。",
    "GONG": "玩家敲击锣盾时以 MSGCH_SOUND 频道显示的固定响度消息。",
    "WHISPER": "装备/施法/换帽时以低语包装经 MSGCH_TALK 显示的玩家可见消息。",
    "FUNGUS": "菌皮斗篷装备或世界反应时以 MSGCH_TALK 显示的玩家可见消息。",
    "EEL": "无邻近敌人时电鳗之手风味消息，替换 @head@/@skin@ 后以 MSGCH_TALK 显示。",
    "RECURSIVE": "仅作为 SpeakDB 递归 token 展开的内部 fragment，不直接作为生产根查询。",
}

FROZEN_PRODUCERS = {
    "NOISY_EQUIPMENT": [
        {"location": "crawl-ref/source/melee-attack.cc:2011",
         "mode": "player melee hit with ARTP_NOISE artefact weapon"},
        {"location": "crawl-ref/source/shout.cc:386",
         "mode": "stable English qualname lookup, NONE suppression, "
                 "noisy weapon fallback"},
    ],
    "SINGING_SWORD": [
        {"location": "crawl-ref/source/art-func.h:355",
         "mode": "silence/tension tier 0..4 selecting singing sword keys"},
    ],
    "GONG": [
        {"location": "crawl-ref/source/art-func.h:479",
         "mode": "shield of the gong melee strike"},
    ],
    "WHISPER": [
        {"location": "crawl-ref/source/art-func.h:1207",
         "mode": "Majin-Bo equip greeting"},
        {"location": "crawl-ref/source/spl-cast.cc:848",
         "mode": "Majin-Bo cast by spell difficulty (weak <= level 4)"},
        {"location": "crawl-ref/source/art-func.h:1866",
         "mode": "Skull of Zonguldrok equip greeting/reprise"},
        {"location": "crawl-ref/source/art-func.h:1882",
         "mode": "Skull of Zonguldrok unequip farewell"},
        {"location": "crawl-ref/source/player-equip.cc:2198",
         "mode": "Zonguldrok hat comment by artefact/brand/unrand name"},
    ],
    "FUNGUS": [
        {"location": "crawl-ref/source/art-func.h:1893",
         "mode": "fungal fisticloak equip"},
        {"location": "crawl-ref/source/art-func.h:1911",
         "mode": "fungal fisticloak world_reacts flavour"},
    ],
    "EEL": [
        {"location": "crawl-ref/source/player-reacts.cc:1279",
         "mode": "eel hands transformation flavour (arm_count 1 solo)"},
    ],
    "RECURSIVE": [
        {"location": "crawl-ref/source/database.cc:1386",
         "mode": "recursive @key@ replacement over the selected pattern"},
    ],
}

REENTRY_TRIGGER = (
    "英文或中文 TextDB source、production key/variant/weight/control/token/Lua/"
    "随机子串拓扑、database.cc 加载顺序与递归、shout.cc/art-func.h/player-equip.cc/"
    "player-reacts.cc 消费者语义、docs/glossary.md 权威发生变化时重新审阅。"
)

TERMINAL_CONCLUSIONS = {"keep", "adjust", "retranslate",
                        "defer terminology", "defer implementation"}
DEFER_CONCLUSIONS = {"defer terminology", "defer implementation"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}

METADATA_FIELDS = {
    "baseline", "chinese_production_dump_sha256", "en_lua_site_count",
    "en_random_site_count", "en_variant_count", "english_production_dump_sha256",
    "glossary_sha256", "identity_count", "inventory_sha256",
    "terminal_conclusion_counts", "zh_lua_site_count", "zh_random_site_count",
    "zh_variant_count",
}
CARD_FIELDS = {
    "actual_behavior", "confidence", "consumer", "current_chinese",
    "current_english", "deferral_owner", "deferral_reason",
    "dependency_group", "display_context", "evidence_locations",
    "glossary_authority", "identity", "key", "lifecycle", "producers",
    "production_facts", "proposed_translation", "reentry_trigger",
    "rejected_alternatives", "reviewed_actions", "reviewer_rationale",
    "terminal_conclusion", "variant_reviews",
}
# Reviewed one-sided action: kind "add" binds an EN-only missing variant
# (baseline EN ordinal, approved Chinese text, protocol copied from the EN
# variant); kind "remove" binds a ZH-only orphan (baseline ZH ordinal, exact
# current text being removed).  Add ordinals are candidate (final) positions;
# remove ordinals are baseline positions.  Kind "protocol_transition" is the
# narrow card-local exception for the single approved matched-slot protocol
# move: it binds a baseline ordinal, the exact baseline protocol, the exact
# candidate/proposed text and the exact new protocol.
ACTION_FIELDS = {"kind", "variant_ordinal", "text", "rationale"}
TRANSITION_ACTION_FIELDS = {
    "kind", "variant_ordinal", "baseline_protocol", "text",
    "new_protocol", "rationale",
}
# Text-derived protocol fields whose complete tuple must equal the mapped
# baseline ZH variant at every matched slot.  Weight is bound separately
# because it is variant metadata, not text-derived.  Lua is bound as the
# complete ordered block bodies (operators, statements, literals,
# multiplicity, order), never as site counts or comparison strings alone,
# so ``==`` -> ``~=`` or block reorder/dedup changes the protocol tuple.
PROTOCOL_FIELDS = ("control_prefix", "runtime_tokens",
                   "random_site_counts", "lua_blocks")
# Weight plus every text-derived protocol field, compared as one ordered
# tuple for matched slots and protocol_transition records.
TRANSITION_PROTOCOL_FIELDS = {
    "weight", "control_prefix", "runtime_tokens", "random_site_counts",
    "lua_blocks",
}
TRANSITION_PROTOCOL_ORDER = ("weight", "control_prefix", "runtime_tokens",
                             "random_site_counts", "lua_blocks")
# The single matched-slot protocol transition approved for the Issue #60
# landing (explicit acceptance criterion): _singing_no_tension_ baseline
# ordinal 5 restores the EN empty random option, changing the ordered
# per-site alternative shape [2,2] -> [3,2].  The enumeration binds
# key+ordinal, the exact candidate/proposed text and the exact new
# random-site shape; every other protocol_transition record is rejected even
# when it is internally consistent.
APPROVED_PROTOCOL_TRANSITIONS = {
    ("_singing_no_tension_", 5): {
        "text": "@The_weapon@[几乎|很明显|][奏出了|没奏出]音乐会音高。",
        "new_random_site_counts": [3, 2],
    },
}
PRODUCTION_FACT_FIELDS = {
    "caller_tokens", "chinese_definition_ordinal", "chinese_source_line",
    "control_prefixes", "en_only_variant_ordinals", "english_definition_ordinal",
    "english_source", "english_source_line", "en_variant_count", "lifecycle",
    "localized_source", "lua_comparison_strings", "lua_site_counts",
    "pairing_protocol_differences", "parse_error", "random_site_counts",
    "recursive_tokens", "referencing_sites", "runtime_tokens",
    "source_history_length", "weights", "zh_only_variant_ordinals",
    "zh_variant_count",
}
VARIANT_FIELDS = {
    "control_prefix", "current_chinese", "english", "lua_comparison_strings",
    "lua_site_count", "proposed_translation", "random_site_counts", "rationale",
    "runtime_tokens", "terminal_conclusion", "variant_ordinal", "weight",
}
DEFERRAL_FIELDS = {"deferral_owner", "deferral_reason", "reentry_trigger"}


InventoryError = shared.InventoryError
_require = shared._require
_sha256 = shared._sha256
_canonical_json = shared._canonical_json
_is_int = shared._is_int
_nonempty_string = shared._nonempty_string
_require_exact_fields = shared._require_exact_fields
_runtime_tokens = shared._runtime_tokens

_LUA_RE = re.compile(r"\{\{(.*?)\}\}", re.DOTALL)
_LUA_COMPARE_RE = re.compile(r'(?:==|~=)\s*"([^"]*)"')


def _random_site_counts(pattern: str) -> list[int]:
    """Ordered per-site alternative counts with fail-closed bracket checks."""
    counts: list[int] = []
    position = 0
    while position < len(pattern):
        opening = pattern.find("[", position)
        stray_closing = pattern.find("]", position)
        if stray_closing >= 0 and (opening < 0 or stray_closing < opening):
            raise InventoryError(
                f"unbalanced random substring marker at offset {stray_closing}"
            )
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
    trailing = pattern.find("]", position)
    _require(trailing < 0,
             f"unbalanced random substring marker at offset {trailing}")
    return counts


def _lua_sites(pattern: str) -> list[dict[str, Any]]:
    sites = [{"start": match.start(), "end": match.end()}
             for match in _LUA_RE.finditer(pattern)]
    _require(pattern.count("{{") == len(sites),
             f"unbalanced Lua site in pattern {pattern!r}")
    _require(pattern.count("}}") == len(sites),
             f"unbalanced Lua close in pattern {pattern!r}")
    return sites


def _lua_comparison_strings(pattern: str) -> list[str]:
    strings: set[str] = set()
    for match in _LUA_RE.finditer(pattern):
        strings.update(_LUA_COMPARE_RE.findall(match.group(1)))
    return sorted(strings)


def _lua_blocks(pattern: str) -> list[str]:
    """Ordered complete Lua block bodies (exact ``{{ }}`` inner text).

    The ordered list binds operators, statements, literals, multiplicity and
    order byte-exactly, so ``==`` -> ``~=``, block reorder or block
    duplication change the fingerprint even when site counts and comparison
    strings stay identical.
    """
    return [match.group(1) for match in _LUA_RE.finditer(pattern)]


# ── audited input reads ────────────────────────────────────────────────
#
# Mutable external artifacts (production dumps, review results, glossary)
# are read through the repository audited snapshot helper: every parent
# component is lstat-checked, the target must be a regular file (never a
# symlink/FIFO/device), it is opened with O_NOFOLLOW, the opened inode must
# equal the inspected inode, and the complete content is read from that one
# descriptor (never a reopened pathname), so a concurrent swap cannot
# substitute different bytes.  Exact-Git inputs additionally require a
# regular-file tree mode in the bound commit.


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _read_artifact_bytes(path: Path, label: str) -> bytes:
    """Read one mutable artifact through a checked no-follow descriptor.

    A fresh development-mode snapshot is used per read so no pathname is
    ever re-read from a cache: every read is independently bound to the
    inode it inspected.
    """
    snapshot = audit_inputs.AuditSnapshot(_repository_root(), None)
    try:
        return snapshot.read(path, allow_external_unbound=True).bytes
    except audit_inputs.AuditInputError as exc:
        raise InventoryError(f"cannot read {label} {path}: {exc}") from exc


def _load_dump_safe(
    path: Path, label: str, expected_directory: str,
    expected_database: str = "speak",
) -> tuple[dict[str, Any], bytes]:
    """Parse a production dump whose bytes were read through one checked
    no-follow descriptor with inode identity verification.

    ``expected_database`` defaults to ``'speak'``: the hardened speak-family
    callers (graffiti, wpnnoise and the monspell CLI path) reject a misc
    dump, and only the misc-family decorlines caller passes ``'misc'``
    explicitly, so a speak dump can never be consumed on a misc path (or
    vice versa)."""
    raw = _read_artifact_bytes(path, f"{label} production dump")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise InventoryError(
            f"cannot parse {label} production dump {path}: {exc}") from exc
    try:
        validate_artifact(
            value, f"{label} production dump",
            expected_database=expected_database,
        )
    except ArtifactError as exc:
        raise InventoryError(str(exc)) from exc
    _require(
        value["source_directory"] == expected_directory,
        f"{label} source_directory must be exactly {expected_directory!r}",
    )
    return value, raw


def _candidate_regular_blob(ref: str, git_path: str, label: str) -> bytes:
    """Read one candidate-tree input bound to the exact candidate commit.

    The tree entry must be a regular-file blob (100644/100755); symlink,
    gitlink, subtree and device entries are rejected before any content is
    consumed, so the bytes always carry checkout-identical semantics.
    """
    try:
        mode, data = audit_inputs.read_regular_git_blob(
            _repository_root(), ref, git_path, with_mode=True
        )
    except audit_inputs.AuditInputError as exc:
        raise InventoryError(
            f"cannot read {label} {git_path}@{ref[:12]} from exact Git: {exc}",
        ) from exc
    _require(
        mode in ("100644", "100755"),
        f"{label} {git_path}@{ref[:12]} is not a regular blob",
    )
    return data


def _repo_relative_git_path(path: Path, label: str) -> str:
    """Map a CLI path to a lexical repository-relative Git path."""
    repository = _repository_root()
    supplied = path if path.is_absolute() else repository / path
    try:
        relative = supplied.relative_to(repository)
    except ValueError as exc:
        raise InventoryError(
            f"{label} must be inside the repository when a candidate is "
            f"bound: {path}",
        ) from exc
    git_path = relative.as_posix()
    _require(
        all(part not in {"", ".", ".."} for part in git_path.split("/")),
        f"{label} has an unsafe repository path {path!r}",
    )
    return git_path


def _require_regular_git_blobs(
    ref: str, git_paths: list[str], label: str,
) -> None:
    """Every exact-Git input must be a regular-file blob in the commit tree."""
    for git_path in git_paths:
        try:
            mode, _data = audit_inputs.read_regular_git_blob(
                _repository_root(), ref, git_path, with_mode=True
            )
        except audit_inputs.AuditInputError as exc:
            raise InventoryError(
                f"{label} exact-Git input {git_path}@{ref[:12]} is not a "
                f"regular blob: {exc}",
            ) from exc
        _require(
            mode in ("100644", "100755"),
            f"{label} exact-Git input {git_path}@{ref[:12]} has unsupported "
            f"mode {mode!r}",
        )


def _require_regular_git_sources(
    ref: str, directory: str, label: str,
) -> None:
    """Bind the SpeakDB derivation inputs to regular blobs at the exact OID.

    The shared derivation reads database.cc and every SpeakDB source from
    exact Git; this pre-flight proves each one of those tree entries is a
    regular file so an unsupported English Git object type can never be
    parsed with semantics different from the production checkout.
    """
    if directory == "database/":
        manifest = shared._english_source_manifest(ref, label)
    else:
        manifest = shared._localized_source_manifest(ref, label)
    _require_regular_git_blobs(
        ref,
        ["crawl-ref/source/database.cc"]
        + [f"crawl-ref/source/dat/{name}" for name in manifest],
        label,
    )


def _definition_lines(source: str, label: str) -> dict[str, int]:
    try:
        definitions = parse_db_keys(source, SOURCE_BASENAME)
    except SystemExit as exc:
        raise InventoryError(f"{label} TextDB parse failed: {exc}") from exc
    lines: dict[str, int] = {}
    for definition in definitions:
        canonical = shared.lowercase_string(definition.raw_key)
        _require(canonical not in lines,
                 f"{label} duplicate raw key {canonical!r} in wpnnoise.txt")
        lines[canonical] = definition.key_line
    return lines


def _dump_binding(
    artifact: dict[str, Any], raw: bytes, label: str, role: str = "baseline",
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    _require(role in ("baseline", "candidate"),
             f"{label} unknown dump binding role {role!r}")
    directory = artifact["source_directory"]
    expected_source = f"{directory}{SOURCE_BASENAME}"
    matching_sources = [
        source for source in artifact["sources"]
        if source["source_name"] == expected_source
    ]
    _require(len(matching_sources) == 1,
             f"{label} dump must contain exactly one {expected_source!r}")
    source_snapshot = matching_sources[0]["normalized_utf8"]
    touching = [
        entry for entry in artifact["entries"]
        if any(item["source_name"] == expected_source
               for item in entry["source_history"])
    ]
    for entry in touching:
        key = entry["canonical_key"]
        _require(entry["parse_error"] is None,
                 f"{label} key {key!r} has parse error")
        _require(not entry["body_empty"],
                 f"{label} key {key!r} has an empty body")
        _require(len(entry["source_history"]) == 1,
                 f"{label} key {key!r} is overridden")
        provenance = entry["effective_provenance"]
        _require(
            provenance["source_name"] == expected_source,
            f"{label} key {key!r} is not effective from {expected_source}",
        )

    actual_keys = {entry["canonical_key"] for entry in touching}
    _require(actual_keys == set(ROOT_KEYS) | {
        key for key in DEPENDENCY_GROUP if key not in ROOT_KEYS
    }, f"{label} wpnnoise key set mismatch")
    ordinals = sorted(
        entry["effective_provenance"]["definition_ordinal"]
        for entry in touching
    )
    _require(ordinals == list(range(len(ordinals))),
             f"{label} wpnnoise definition ordinals are not contiguous from zero")

    definition_lines = _definition_lines(source_snapshot, label)
    rows: list[dict[str, Any]] = []
    for entry in sorted(touching, key=lambda item: item["canonical_key"]):
        variants = []
        for expected_ordinal, variant in enumerate(entry["variants"]):
            locator = variant["locator"]
            _require(locator["variant_ordinal"] == expected_ordinal,
                     f"{label} ordinal gap for {entry['canonical_key']!r}")
            pattern = variant["raw_pattern"]
            prefix = shared._control_prefix(pattern)
            _require(prefix in ALLOWED_CONTROLS,
                     f"{label} unrecognized control prefix {prefix!r}")
            lua_sites = _lua_sites(pattern)
            comparisons = _lua_comparison_strings(pattern)
            _require(
                set(comparisons) <= set(LUA_COMPARISON_STRINGS),
                f"{label} unknown Lua comparison string {comparisons!r}",
            )
            variants.append({
                "locator": {"key": entry["canonical_key"],
                            "variant_ordinal": expected_ordinal},
                "weight": variant["weight"],
                "control_prefix": prefix,
                "runtime_tokens": _runtime_tokens(pattern),
                "random_site_counts": _random_site_counts(pattern),
                "lua_site_count": len(lua_sites),
                "lua_comparison_strings": comparisons,
                "raw_pattern": pattern,
            })
        key = entry["canonical_key"]
        _require(key in definition_lines,
                 f"{label} cannot bind a source line for {key!r}")
        rows.append({
            "key": key,
            "effective_provenance": entry["effective_provenance"],
            "definition_ordinal":
                entry["effective_provenance"]["definition_ordinal"],
            "source_line": definition_lines[key],
            "source_history_length": len(entry["source_history"]),
            "variants": variants,
        })

    is_english = directory == "database/"
    _require(len(rows) == EXPECTED_IDENTITY_COUNT,
             f"{label} wpnnoise identity count mismatch")
    if is_english or role == "baseline":
        _require(
            sum(len(row["variants"]) for row in rows)
            == (EXPECTED_EN_VARIANT_COUNT if is_english
                else EXPECTED_ZH_VARIANT_COUNT),
            f"{label} wpnnoise variant count mismatch",
        )
        _require(
            sum(len(variant["random_site_counts"])
                for row in rows for variant in row["variants"])
            == (EXPECTED_EN_RANDOM_SITES if is_english
                else EXPECTED_ZH_RANDOM_SITES),
            f"{label} wpnnoise random-site count mismatch",
        )
        _require(
            sum(variant["lua_site_count"]
                for row in rows for variant in row["variants"])
            == (EXPECTED_EN_LUA_SITES if is_english else EXPECTED_ZH_LUA_SITES),
            f"{label} wpnnoise Lua site count mismatch",
        )
        _require(
            sum(variant["control_prefix"] == "VISUAL"
                for row in rows for variant in row["variants"])
            == (EXPECTED_EN_VISUAL_PREFIXES if is_english
                else EXPECTED_ZH_VISUAL_PREFIXES),
            f"{label} wpnnoise VISUAL control count mismatch",
        )
        _require(
            sum(variant["control_prefix"] == "SOUND"
                for row in rows for variant in row["variants"])
            == (EXPECTED_EN_SOUND_PREFIXES if is_english
                else EXPECTED_ZH_SOUND_PREFIXES),
            f"{label} wpnnoise SOUND control count mismatch",
        )
    # A candidate-role ZH dump is exempt from the frozen baseline totals: the
    # reviewed-action gate proves every candidate variant position (count,
    # weight, control, tokens, random sites, Lua) against the baseline or the
    # EN source, so the aggregates are covered per position instead.
    # Candidate EN keeps every frozen total because English is immutable.
    binding = {
        "artifact_sha256": _sha256(raw),
        "database_name": artifact["database_name"],
        "source_directory": directory,
        "source_snapshots": [
            {
                "source_name": source["source_name"],
                "load_index": source["load_index"],
                "normalized_utf8_sha256": _sha256(
                    source["normalized_utf8"].encode("utf-8")
                ),
            }
            for source in artifact["sources"]
        ],
        "effective_wpnnoise_source": expected_source,
    }
    return binding, rows


def _pair_entries(
    en_rows: list[dict[str, Any]], zh_rows: list[dict[str, Any]], label: str,
    role: str = "baseline",
) -> list[dict[str, Any]]:
    _require(role in ("baseline", "candidate"),
             f"{label} unknown pairing role {role!r}")
    en_by_key = {row["key"]: row for row in en_rows}
    zh_by_key = {row["key"]: row for row in zh_rows}
    _require(en_by_key.keys() == zh_by_key.keys(), f"{label} EN/ZH key sets differ")
    entries = []
    for key in sorted(en_by_key):
        en = en_by_key[key]
        zh = zh_by_key[key]
        en_count = len(en["variants"])
        zh_count = len(zh["variants"])
        if role == "candidate":
            # The approved one-sided actions restore full EN coverage: every
            # candidate key must have equal EN/ZH counts.  Any remaining
            # asymmetry is an unreviewed one-sided change and fails closed.
            _require(en_count == zh_count,
                     f"{label} variant count differs for {key!r}: EN "
                     f"{en_count} vs ZH {zh_count} (unreviewed one-sided "
                     f"change)")
        elif en_count != zh_count:
            frozen = ASYMMETRIC_VARIANT_KEYS.get(key)
            _require(
                frozen == (en_count, zh_count),
                f"{label} variant count differs for {key!r}: EN {en_count} "
                f"vs ZH {zh_count} (expected frozen {frozen!r})",
            )
        else:
            _require(key not in ASYMMETRIC_VARIANT_KEYS,
                     f"{label} frozen asymmetric key {key!r} has equal counts")
        # ZH variants are the complete review list (variant_ordinal is the ZH
        # file ordinal).  Paired ordinals carry the ordinal-paired EN pattern;
        # ZH-only ordinals carry english=None.  EN-only ordinals are recorded
        # as facts and have no review slot.
        variants = []
        for ordinal, zh_variant in enumerate(zh["variants"]):
            en_variant = en["variants"][ordinal] if ordinal < en_count else None
            differences = []
            if en_variant is not None:
                for field, en_value, zh_value in (
                    ("weight", en_variant["weight"], zh_variant["weight"]),
                    ("control", en_variant["control_prefix"],
                     zh_variant["control_prefix"]),
                    ("tokens", en_variant["runtime_tokens"],
                     zh_variant["runtime_tokens"]),
                    ("random_sites", en_variant["random_site_counts"],
                     zh_variant["random_site_counts"]),
                    ("lua", en_variant["lua_site_count"],
                     zh_variant["lua_site_count"]),
                ):
                    if en_value != zh_value:
                        differences.append(field)
            variants.append({
                "locator": {"key": key, "variant_ordinal": ordinal},
                "weight": zh_variant["weight"],
                "control_prefix": zh_variant["control_prefix"],
                "runtime_tokens": zh_variant["runtime_tokens"],
                "random_site_counts": zh_variant["random_site_counts"],
                "lua_site_count": zh_variant["lua_site_count"],
                "lua_comparison_strings": zh_variant["lua_comparison_strings"],
                "lua_blocks": _lua_blocks(zh_variant["raw_pattern"]),
                "english": en_variant["raw_pattern"]
                if en_variant is not None else None,
                "chinese": zh_variant["raw_pattern"],
                "pairing_protocol_differences": differences,
            })
        en_only = [ordinal for ordinal in range(zh_count, en_count)]
        zh_only = [ordinal for ordinal in range(en_count, zh_count)]
        entries.append({
            "identity": f"wpnnoise:{key}",
            "key": key,
            "route": _route_for(key),
            "lifecycle": _lifecycle_for(key),
            "english_variants": [{
                "locator": variant["locator"],
                "weight": variant["weight"],
                "control_prefix": variant["control_prefix"],
                "runtime_tokens": variant["runtime_tokens"],
                "random_site_counts": variant["random_site_counts"],
                "lua_site_count": variant["lua_site_count"],
                "lua_comparison_strings": variant["lua_comparison_strings"],
                "lua_blocks": _lua_blocks(variant["raw_pattern"]),
                "raw_pattern": variant["raw_pattern"],
            } for variant in en["variants"]],
            "english_source_line": en["source_line"],
            "chinese_source_line": zh["source_line"],
            "english_definition_ordinal": en["definition_ordinal"],
            "chinese_definition_ordinal": zh["definition_ordinal"],
            "source_history_length": {
                "english": en["source_history_length"],
                "chinese": zh["source_history_length"],
            },
            "english_provenance": en["effective_provenance"],
            "chinese_provenance": zh["effective_provenance"],
            "en_variant_count": en_count,
            "zh_variant_count": zh_count,
            "en_only_variant_ordinals": en_only,
            "zh_only_variant_ordinals": zh_only,
            "variants": variants,
        })
    return entries


def _route_for(key: str) -> str:
    if key in ROOT_KEYS:
        if key.startswith("singing sword"):
            return "SINGING_SWORD"
        if key in {"frozen axe \"frostbite\"", "trishula \"condemnation\"",
                   "noisy weapon"}:
            return "NOISY_EQUIPMENT"
        if key == "shield of the gong":
            return "GONG"
        if key.startswith(("majin-bo", "zonguldrok")):
            return "WHISPER"
        if key == "fungus thoughts":
            return "FUNGUS"
        if key.startswith("eel hand"):
            return "EEL"
        raise InventoryError(f"root key {key!r} has no frozen route")
    return "RECURSIVE"


def _lifecycle_for(key: str) -> str:
    if key in ROOT_KEYS:
        return "direct-production-root"
    return "recursive-internal-fragment"


def _referencing_sites(
    rows: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    sites: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        for variant in row["variants"]:
            for token in variant["runtime_tokens"]:
                canonical = token[1:-1].lower()
                sites.setdefault(canonical, []).append({
                    "key": row["key"],
                    "variant_ordinal": variant["locator"]["variant_ordinal"],
                })
    for key in sites:
        sites[key].sort(key=lambda item: (item["key"], item["variant_ordinal"]))
    return sites


def _language_edges(
    rows: list[dict[str, Any]], key_set: set[str],
) -> dict[str, list[str]]:
    """Directed recursive-token graph of one language.

    An edge ``K -> T`` exists when any variant of key ``K`` contains the
    runtime token ``@T@`` with ``T`` in the SpeakDB key set.  Caller tokens
    (@player_name@, @CAPS@, @head@, ...) are replaced by consumers, never by
    the DB, so they never participate in the recursive closure.
    """
    edges: dict[str, list[str]] = {}
    for row in rows:
        destinations = {
            token[1:-1].lower()
            for variant in row["variants"]
            for token in variant["runtime_tokens"]
            if token[1:-1].lower() in key_set
        }
        edges[row["key"]] = sorted(destinations)
    return edges


def _reachability_proof(
    rows: list[dict[str, Any]], key_set: set[str], roots: set[str],
    fragments: set[str],
) -> dict[str, Any]:
    """Traverse the directed recursive-token graph from every ROOT_KEYS member.

    The traversal is independent per language and deterministic: BFS from the
    roots in ROOT_KEYS order with sorted adjacency.  The complete non-root
    closure must equal the fragment set, so disconnected cycles and
    self-loops (whose members are unreachable from any root) fail closed, and
    no root key may be a token destination.  Every fragment gets the first
    discovered root-to-fragment path as a deterministic witness.
    """
    edges = _language_edges(rows, key_set)
    destinations = {
        target for targets in edges.values() for target in targets
    }
    unexpected_roots = sorted(destinations & roots)
    _require(
        not unexpected_roots,
        f"wpnnoise recursive token graph references root keys "
        f"{unexpected_roots!r}",
    )
    reached = set(roots)
    witnesses: dict[str, list[str]] = {}
    queue: deque[tuple[str, tuple[str, ...]]] = deque(
        (root, (root,)) for root in ROOT_KEYS
    )
    while queue:
        key, path = queue.popleft()
        for target in edges.get(key, ()):
            if target in reached:
                continue
            reached.add(target)
            new_path = path + (target,)
            if target in fragments:
                witnesses[target] = list(new_path)
            queue.append((target, new_path))
    missing = sorted(fragments - (reached - roots))
    _require(
        not missing,
        f"wpnnoise recursive closure leaves fragments unreachable from "
        f"ROOT_KEYS: {missing!r}",
    )
    _require(
        reached - roots == fragments,
        "wpnnoise non-root closure does not equal the fragment set",
    )
    _require(
        len(witnesses) == len(fragments),
        "wpnnoise root-to-fragment witness coverage mismatch",
    )
    return {
        "edges": edges,
        "non_root_closure": sorted(reached - roots),
        "witnesses": {key: witnesses[key] for key in sorted(witnesses)},
    }


def _expected_referencing_sites(
    entry: dict[str, Any], en_references: dict[str, Any],
    zh_references: dict[str, Any],
) -> dict[str, list[dict[str, Any]]] | None:
    if entry["lifecycle"] != "recursive-internal-fragment":
        return None
    return {
        "english": en_references.get(entry["key"], []),
        "chinese": zh_references.get(entry["key"], []),
    }


def _expected_evidence_locations(entry: dict[str, Any]) -> list[str]:
    en_source = (
        f"crawl-ref/source/dat/database/wpnnoise.txt:"
        f"{entry['english_source_line']}"
    )
    zh_source = (
        f"crawl-ref/source/dat/database/zh/wpnnoise.txt:"
        f"{entry['chinese_source_line']}"
    )
    route = entry["route"]
    if route == "RECURSIVE":
        referencing = entry["referencing_sites"]
        refs = sorted({
            f"recursive-ref:{item['key']}:{item['variant_ordinal']}"
            for items in referencing.values()
            for item in items
        })
        return [
            en_source, zh_source,
            "crawl-ref/source/database.cc:2307",
            "crawl-ref/source/database.cc:1497",
            "crawl-ref/source/database.cc:1386",
            *refs,
        ]
    return [en_source, zh_source, *sorted(FROZEN_CONSUMER[route].values())]


def _frozen_route_evidence(entry: dict[str, Any]) -> dict[str, Any]:
    route = entry["route"]
    return {
        "actual_behavior": FROZEN_ACTUAL_BEHAVIOR[route],
        "display_context": FROZEN_DISPLAY_CONTEXT[route],
        "consumer": FROZEN_CONSUMER[route],
        "producers": FROZEN_PRODUCERS[route],
    }


def _expected_production_facts(
    inventory: dict[str, Any], entry: dict[str, Any],
) -> dict[str, Any]:
    variants = entry["variants"]
    en_variants = entry["english_variants"]
    tokens_used = {
        token for variant in variants for token in variant["runtime_tokens"]
    }
    tokens_used |= {
        token for variant in en_variants for token in variant["runtime_tokens"]
    }
    key_set = {row["key"] for row in inventory["entries"]}
    recursive_tokens = sorted(
        token for token in tokens_used
        if token[1:-1].lower() in key_set
    )
    caller_tokens = sorted(
        token for token in tokens_used
        if token[1:-1].lower() not in key_set
    )
    comparisons = sorted({
        comparison
        for variant in variants
        for comparison in variant["lua_comparison_strings"]
    } | {
        comparison
        for variant in en_variants
        for comparison in variant["lua_comparison_strings"]
    })
    return {
        "caller_tokens": caller_tokens,
        "chinese_definition_ordinal": entry["chinese_definition_ordinal"],
        "chinese_source_line": entry["chinese_source_line"],
        "control_prefixes": {
            "english": [variant["control_prefix"]
                        for variant in en_variants],
            "chinese": [variant["control_prefix"] for variant in variants],
        },
        "en_only_variant_ordinals": entry["en_only_variant_ordinals"],
        "english_definition_ordinal": entry["english_definition_ordinal"],
        "english_source":
            inventory["dumps"]["english"]["effective_wpnnoise_source"],
        "english_source_line": entry["english_source_line"],
        "en_variant_count": entry["en_variant_count"],
        "lifecycle": entry["lifecycle"],
        "localized_source":
            inventory["dumps"]["localized"]["effective_wpnnoise_source"],
        "lua_comparison_strings": comparisons,
        "lua_site_counts": {
            "english": [variant["lua_site_count"]
                        for variant in en_variants],
            "chinese": [variant["lua_site_count"] for variant in variants],
        },
        "pairing_protocol_differences": [
            variant["pairing_protocol_differences"] for variant in variants
        ],
        "parse_error": None,
        "random_site_counts": {
            "english": [variant["random_site_counts"]
                        for variant in en_variants],
            "chinese": [variant["random_site_counts"] for variant in variants],
        },
        "recursive_tokens": recursive_tokens,
        "referencing_sites": entry["referencing_sites"],
        "runtime_tokens": {
            "english": [variant["runtime_tokens"] for variant in en_variants],
            "chinese": [variant["runtime_tokens"] for variant in variants],
        },
        "source_history_length": entry["source_history_length"],
        "weights": {
            "english": [variant["weight"] for variant in en_variants],
            "chinese": [variant["weight"] for variant in variants],
        },
        "zh_only_variant_ordinals": entry["zh_only_variant_ordinals"],
        "zh_variant_count": entry["zh_variant_count"],
    }


def build_inventory(
    baseline_ref: str, english_path: Path, localized_path: Path,
    glossary_path: Path, glossary_ref: str | None = None,
) -> dict[str, Any]:
    shared._validate_oid(baseline_ref, "baseline")
    _require_regular_git_sources(baseline_ref, "database/", "baseline EN")
    _require_regular_git_sources(
        baseline_ref, "database/zh/", "baseline ZH")
    en_dump, en_raw = _load_dump_safe(english_path, "baseline EN", "database/")
    zh_dump, zh_raw = _load_dump_safe(
        localized_path, "baseline ZH", "database/zh/"
    )
    shared._require_scoped_derivation(
        en_dump, shared._derive_scoped_dump(
            baseline_ref, "database/", "baseline EN",
            source_basename=SOURCE_BASENAME,
        ), "baseline EN", source_basename=SOURCE_BASENAME,
    )
    shared._require_scoped_derivation(
        zh_dump, shared._derive_scoped_dump(
            baseline_ref, "database/zh/", "baseline ZH",
            source_basename=SOURCE_BASENAME,
        ), "baseline ZH", source_basename=SOURCE_BASENAME,
    )
    en_binding, en_rows = _dump_binding(en_dump, en_raw, "baseline EN")
    zh_binding, zh_rows = _dump_binding(zh_dump, zh_raw, "baseline ZH")
    en_references = _referencing_sites(en_rows)
    zh_references = _referencing_sites(zh_rows)

    entries = []
    for entry in _pair_entries(en_rows, zh_rows, "baseline"):
        entry["referencing_sites"] = _expected_referencing_sites(
            entry, en_references, zh_references
        )
        entry["dependency_group"] = DEPENDENCY_GROUP[entry["key"]]
        entry["evidence_locations"] = _expected_evidence_locations(entry)
        entries.append(entry)

    # Reachability proof, independent per language: the directed recursive
    # token graph is traversed from every ROOT_KEYS member; the complete
    # non-root closure must equal the fragment set (disconnected cycles and
    # self-loops fail closed), and every fragment gets a deterministic
    # root-to-fragment witness recorded in the inventory evidence/digest.
    # Nothing is assumed reachable; unproven keys fail closed.
    key_set = {entry["key"] for entry in entries}
    fragments = {
        entry["key"] for entry in entries
        if entry["lifecycle"] == "recursive-internal-fragment"
    }
    roots = set(ROOT_KEYS)
    _require(len(fragments | roots) == EXPECTED_IDENTITY_COUNT,
             "wpnnoise identity/lifecycle coverage mismatch")
    reachability = {
        "english": _reachability_proof(en_rows, key_set, roots, fragments),
        "chinese": _reachability_proof(zh_rows, key_set, roots, fragments),
    }

    comparisons = sorted({
        comparison
        for entry in entries
        for variant in entry["variants"]
        for comparison in variant["lua_comparison_strings"]
    } | {
        comparison
        for entry in entries
        for variant in entry["english_variants"]
        for comparison in variant["lua_comparison_strings"]
    })
    _require(comparisons == sorted(LUA_COMPARISON_STRINGS),
             f"wpnnoise Lua comparison string set mismatch: {comparisons!r}")

    # The glossary is a mutable worktree artifact in the baseline-only flow
    # (checked no-follow descriptor); in the candidate flow it is read
    # directly from the exact candidate commit tree as a regular-file blob,
    # so a transient worktree substitution cannot rebind its SHA-256.
    if glossary_ref is not None:
        glossary_sha256 = _sha256(_candidate_regular_blob(
            glossary_ref,
            _repo_relative_git_path(glossary_path, "glossary"),
            "glossary",
        ))
    else:
        glossary_sha256 = _sha256(
            _read_artifact_bytes(glossary_path, "glossary"))
    scope = {
        "source_basename": SOURCE_BASENAME,
        "expected_identity_count": EXPECTED_IDENTITY_COUNT,
        "expected_en_variant_count": EXPECTED_EN_VARIANT_COUNT,
        "expected_zh_variant_count": EXPECTED_ZH_VARIANT_COUNT,
        "expected_en_random_sites": EXPECTED_EN_RANDOM_SITES,
        "expected_zh_random_sites": EXPECTED_ZH_RANDOM_SITES,
        "expected_en_lua_sites": EXPECTED_EN_LUA_SITES,
        "expected_zh_lua_sites": EXPECTED_ZH_LUA_SITES,
        "lua_comparison_strings": list(LUA_COMPARISON_STRINGS),
        "root_keys": list(ROOT_KEYS),
        "asymmetric_variant_keys": {
            key: list(counts) for key, counts in sorted(ASYMMETRIC_VARIANT_KEYS.items())
        },
    }
    core = {
        "schema_version": SCHEMA_VERSION,
        "baseline_ref": baseline_ref,
        "scope": scope,
        "scope_sha256": _sha256(_canonical_json(scope)),
        "glossary": {"path": "docs/glossary.md", "sha256": glossary_sha256},
        "dumps": {"english": en_binding, "localized": zh_binding},
        "entries": entries,
        "reachability": reachability,
    }
    return {**core, "inventory_sha256": _sha256(_canonical_json(core))}


def _strict_block(path: Path) -> list[dict[str, Any]]:
    return shared._strict_block(path, STRICT_BEGIN, STRICT_END)


def _strict_block_from_text(text: str, path: Path) -> list[dict[str, Any]]:
    """Parse the fenced strict evidence block from already-read text."""
    _require(text.count(STRICT_BEGIN) == 1,
             "review results require exactly one strict begin marker")
    _require(text.count(STRICT_END) == 1,
             "review results require exactly one strict end marker")
    begin = text.index(STRICT_BEGIN) + len(STRICT_BEGIN)
    end = text.index(STRICT_END, begin)
    body = text[begin:end].strip()
    match = re.fullmatch(r"```jsonl\s*\n(.*?)\n```", body, re.DOTALL)
    _require(match is not None,
             "strict review evidence must be one fenced jsonl block")
    lines = [line for line in match.group(1).splitlines() if line.strip()]
    records = []
    for line_number, line in enumerate(lines, 1):
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InventoryError(
                f"invalid review JSONL line {line_number}: {exc}") from exc
        _require(isinstance(value, dict),
                 f"review JSONL line {line_number} must be an object")
        records.append(value)
    return records


def _strict_block_safe(path: Path) -> list[dict[str, Any]]:
    """Read review results through one checked no-follow descriptor."""
    raw = _read_artifact_bytes(path, "review results")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InventoryError(
            f"cannot decode review results {path}: {exc}") from exc
    return _strict_block_from_text(text, path)


def _validate_deferral(record: dict[str, Any], context: str) -> None:
    conclusion = record.get("terminal_conclusion")
    if conclusion in DEFER_CONCLUSIONS:
        for field in ("deferral_owner", "deferral_reason", "reentry_trigger"):
            _require(_nonempty_string(record.get(field)),
                     f"{context} deferred conclusion requires {field}")
    else:
        for field in ("deferral_owner", "deferral_reason"):
            _require(record.get(field) is None,
                     f"{context} non-deferred conclusion forbids {field}")


def _aggregate(conclusions: list[str]) -> str:
    if "retranslate" in conclusions:
        return "retranslate"
    if "adjust" in conclusions:
        return "adjust"
    for conclusion in DEFER_CONCLUSIONS:
        if conclusion in conclusions:
            return conclusion
    return "keep"


def _derived_action_fact(text: str, field: str) -> Any:
    """Derive one protocol fact from an approved action's text."""
    if field == "control_prefix":
        return shared._control_prefix(text)
    if field == "runtime_tokens":
        return _runtime_tokens(text)
    if field == "random_site_counts":
        return _random_site_counts(text)
    if field == "lua_site_count":
        return len(_lua_sites(text))
    if field == "lua_comparison_strings":
        return _lua_comparison_strings(text)
    if field == "lua_blocks":
        return _lua_blocks(text)
    raise InventoryError(f"unknown action fact field {field!r}")


def _first_protocol_drift(
    candidate_facts: dict[str, Any], baseline_facts: dict[str, Any],
) -> str | None:
    """First text-derived protocol field differing from the mapped baseline.

    Matched slots compare ONLY against the mapped baseline ZH variant (or an
    approved protocol_transition's exact new protocol); there is no generic
    same-ordinal EN envelope, so a shifted variant can never inherit the EN
    protocol of an unrelated ordinal after add/remove remapping.
    """
    for field in PROTOCOL_FIELDS:
        if candidate_facts[field] != baseline_facts[field]:
            return field
    return None


def _transition_actions(
    actions: list[dict[str, Any]],
) -> dict[int, dict[str, Any]]:
    return {action["variant_ordinal"]: action for action in actions
            if action["kind"] == "protocol_transition"}


def _validate_actions(
    actions: Any, entry: dict[str, Any], proposed: list[str] | None,
    context: str,
) -> None:
    """Strict schema for reviewed one-sided actions bound to the baseline.

    Add actions bind an EN-only missing variant by its baseline EN ordinal and
    require the approved text to reproduce the EN variant's protocol.  An add
    ordinal inside the baseline ZH count must borrow the proposal slot
    (placeholder convention, used by the positional kazoo realignment).
    Remove actions bind a ZH-only orphan by its baseline ZH ordinal and the
    exact current text being removed.  Protocol_transition actions bind the
    single approved matched-slot protocol move: baseline ordinal, exact
    baseline protocol, exact candidate/proposed text and exact new protocol;
    every other transition is rejected even when internally consistent.
    """
    _require(isinstance(actions, list),
             f"{context} reviewed_actions must be a list")
    en_variants = entry["english_variants"]
    zh_variants = entry["variants"]
    seen: set[tuple[str, int]] = set()
    for action in actions:
        _require(isinstance(action, dict),
                 f"{context} reviewed action must be an object")
        kind = action.get("kind")
        _require(kind in ("add", "remove", "protocol_transition"),
                 f"{context} reviewed action kind mismatch")
        _require_exact_fields(
            action,
            TRANSITION_ACTION_FIELDS if kind == "protocol_transition"
            else ACTION_FIELDS,
            f"{context} reviewed action",
        )
        ordinal = action["variant_ordinal"]
        _require(_is_int(ordinal) and ordinal >= 0,
                 f"{context} reviewed action ordinal mismatch")
        _require(_nonempty_string(action["text"]),
                 f"{context} reviewed action requires text")
        _require(_nonempty_string(action["rationale"]),
                 f"{context} reviewed action requires a rationale")
        _require((kind, ordinal) not in seen,
                 f"{context} duplicate reviewed action {kind} {ordinal}")
        seen.add((kind, ordinal))
        if kind == "protocol_transition":
            _validate_protocol_transition(action, entry, actions, context)
        elif kind == "add":
            _require(
                ordinal < len(en_variants),
                f"{context} add action ordinal {ordinal} exceeds EN variants",
            )
            en_variant = en_variants[ordinal]
            for field in ("control_prefix", "runtime_tokens",
                          "random_site_counts", "lua_blocks"):
                _require(
                    _derived_action_fact(action["text"], field)
                    == en_variant[field],
                    f"{context} add action {ordinal} {field} does not match "
                    f"the EN variant",
                )
            if ordinal < len(zh_variants) and proposed is not None:
                _require(
                    proposed[ordinal] == action["text"],
                    f"{context} in-range add ordinal {ordinal} must borrow "
                    f"the proposal slot (placeholder)",
                )
        else:
            _require(
                ordinal < len(zh_variants),
                f"{context} remove action ordinal {ordinal} exceeds ZH "
                f"variants",
            )
            _require(
                action["text"] == zh_variants[ordinal]["chinese"],
                f"{context} remove action text does not match the baseline "
                f"ZH variant",
            )


def _validate_protocol_transition(
    action: dict[str, Any], entry: dict[str, Any],
    actions: list[dict[str, Any]], context: str,
) -> None:
    """Bind one approved matched-slot protocol transition exactly.

    The record must name an approved (key, ordinal), reproduce the exact
    approved candidate/proposed text, reproduce the exact baseline protocol
    of that baseline ZH variant, and carry a new protocol derived from the
    approved text with weight unchanged.  A card-local transition ordinal
    must not collide with an add/remove action of the same card.
    """
    ordinal = action["variant_ordinal"]
    zh_variants = entry["variants"]
    _require(
        ordinal < len(zh_variants),
        f"{context} protocol_transition ordinal {ordinal} exceeds ZH "
        f"variants",
    )
    colliding = sorted({
        f"{other['kind']}@{other['variant_ordinal']}"
        for other in actions
        if other is not action and other["kind"] in ("add", "remove")
        and other["variant_ordinal"] == ordinal
    })
    _require(
        not colliding,
        f"{context} protocol_transition ordinal {ordinal} collides with "
        f"{colliding!r}",
    )
    approved = APPROVED_PROTOCOL_TRANSITIONS.get((entry["key"], ordinal))
    _require(
        approved is not None,
        f"{context} protocol_transition at {entry['key']!r} ordinal "
        f"{ordinal} is not an approved protocol transition",
    )
    _require(
        action["text"] == approved["text"],
        f"{context} protocol_transition text must equal the approved text",
    )
    baseline = zh_variants[ordinal]
    baseline_protocol = action["baseline_protocol"]
    _require(isinstance(baseline_protocol, dict),
             f"{context} protocol_transition baseline_protocol must be an "
             f"object")
    _require_exact_fields(
        baseline_protocol, TRANSITION_PROTOCOL_FIELDS,
        f"{context} protocol_transition baseline_protocol",
    )
    expected_baseline = {
        "weight": baseline["weight"],
        "control_prefix": baseline["control_prefix"],
        "runtime_tokens": baseline["runtime_tokens"],
        "random_site_counts": baseline["random_site_counts"],
        "lua_blocks": baseline["lua_blocks"],
    }
    _require(
        baseline_protocol == expected_baseline,
        f"{context} protocol_transition baseline_protocol does not match "
        f"the baseline ZH variant",
    )
    new_protocol = action["new_protocol"]
    _require(isinstance(new_protocol, dict),
             f"{context} protocol_transition new_protocol must be an object")
    _require_exact_fields(
        new_protocol, TRANSITION_PROTOCOL_FIELDS,
        f"{context} protocol_transition new_protocol",
    )
    _require(
        new_protocol["weight"] == baseline["weight"],
        f"{context} protocol_transition must not change weight",
    )
    for field in PROTOCOL_FIELDS:
        _require(
            new_protocol[field] == _derived_action_fact(action["text"], field),
            f"{context} protocol_transition new_protocol {field} does not "
            f"match the approved text",
        )
    _require(
        new_protocol["random_site_counts"]
        == approved["new_random_site_counts"],
        f"{context} protocol_transition random-site shape does not match "
        f"the approved transition",
    )


def _action_slots(
    baseline_count: int, actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Map baseline ordinals to candidate ordinals through reviewed actions.

    Add ordinals are candidate (final) positions and remove ordinals are
    baseline positions.  The walk consumes both lists without assuming any
    other ordinal pairing, so approved insert/removal shifts never mask drift
    in the remaining variants.
    """
    adds = sorted((a for a in actions if a["kind"] == "add"),
                  key=lambda a: a["variant_ordinal"])
    removes = {a["variant_ordinal"] for a in actions if a["kind"] == "remove"}
    add_by_ord = {a["variant_ordinal"]: a for a in adds}
    expected = baseline_count + len(adds) - len(removes)
    _require(expected >= 0,
             "reviewed actions exceed the baseline variant count")
    slots: list[dict[str, Any]] = []
    baseline_index = 0
    candidate_index = 0
    while baseline_index < baseline_count or candidate_index < expected:
        if candidate_index in add_by_ord:
            slots.append({
                "kind": "add",
                "variant_ordinal": candidate_index,
                "candidate_ordinal": candidate_index,
                "action": add_by_ord[candidate_index],
            })
            candidate_index += 1
        elif baseline_index in removes:
            baseline_index += 1
        else:
            _require(baseline_index < baseline_count
                     and candidate_index < expected,
                     "reviewed actions are inconsistent")
            slots.append({
                "kind": "match",
                "variant_ordinal": baseline_index,
                "candidate_ordinal": candidate_index,
            })
            baseline_index += 1
            candidate_index += 1
    _require(baseline_index == baseline_count
             and candidate_index == expected,
             "reviewed actions are inconsistent")
    return slots


def _expected_candidate_texts(
    entry: dict[str, Any], actions: list[dict[str, Any]],
    proposed: list[str],
) -> list[str]:
    """Expected candidate ZH texts per candidate ordinal."""
    zh_variants = entry["variants"]
    add_ordinals = {a["variant_ordinal"] for a in actions
                    if a["kind"] == "add"}
    expected: list[str] = []
    for slot in _action_slots(len(zh_variants), actions):
        if slot["kind"] == "add":
            expected.append(slot["action"]["text"])
        elif slot["variant_ordinal"] in add_ordinals:
            # In-range add placeholder: the shifted baseline variant is kept.
            expected.append(zh_variants[slot["variant_ordinal"]]["chinese"])
        else:
            expected.append(proposed[slot["variant_ordinal"]])
    return expected


def _review_bindings_from_block(
    records: list[dict[str, Any]],
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, list[str]]]:
    """Extract per-key reviewed actions and proposals from the strict block.

    Shape validation runs here so the candidate gate fails closed before it
    consumes any malformed review data; the full card semantics (including
    action-vs-entry binding) are validated by ``_validate_card``.
    """
    _require(len(records) == EXPECTED_IDENTITY_COUNT + 1,
             "review evidence metadata/card coverage mismatch")
    actions_by_key: dict[str, list[dict[str, Any]]] = {}
    proposals_by_key: dict[str, list[str]] = {}
    for record in records[1:]:
        _require(isinstance(record, dict), "review card must be an object")
        identity = record.get("identity")
        key = record.get("key")
        _require(isinstance(identity, str) and isinstance(key, str),
                 "review card identity/key mismatch")
        actions = record.get("reviewed_actions")
        _require(actions is not None,
                 f"{identity} review card requires reviewed_actions")
        _require(isinstance(actions, list),
                 f"{identity} reviewed_actions must be a list")
        seen: set[tuple[str, int]] = set()
        for action in actions:
            _require(isinstance(action, dict),
                     f"{identity} reviewed action must be an object")
            kind = action.get("kind")
            _require(kind in ("add", "remove", "protocol_transition"),
                     f"{identity} reviewed action kind mismatch")
            _require_exact_fields(
                action,
                TRANSITION_ACTION_FIELDS
                if kind == "protocol_transition" else ACTION_FIELDS,
                f"{identity} reviewed action",
            )
            ordinal = action["variant_ordinal"]
            _require(_is_int(ordinal) and ordinal >= 0,
                     f"{identity} reviewed action ordinal mismatch")
            _require(_nonempty_string(action["text"]),
                     f"{identity} reviewed action requires text")
            _require(_nonempty_string(action["rationale"]),
                     f"{identity} reviewed action requires a rationale")
            _require((kind, ordinal) not in seen,
                     f"{identity} duplicate reviewed action")
            seen.add((kind, ordinal))
        proposed = record.get("proposed_translation")
        _require(
            isinstance(proposed, list)
            and all(isinstance(item, str) for item in proposed),
            f"{identity} proposed_translation must be a string list",
        )
        actions_by_key[key] = actions
        proposals_by_key[key] = proposed
    return actions_by_key, proposals_by_key


def _validate_card(
    card: dict[str, Any], inventory: dict[str, Any], entry: dict[str, Any],
    candidate: dict[str, Any] | None,
) -> None:
    identity = entry["identity"]
    _require_exact_fields(card, CARD_FIELDS, identity)
    _require(card["identity"] == identity, f"{identity} identity mismatch")
    _require(card["key"] == entry["key"], f"{identity} key mismatch")
    _require(card["lifecycle"] == entry["lifecycle"],
             f"{identity} lifecycle mismatch")
    _require(card["dependency_group"] == entry["dependency_group"],
             f"{identity} dependency_group mismatch")
    _require(card["glossary_authority"] == (
        f"{inventory['glossary']['path']}@{inventory['glossary']['sha256']}"
    ), f"{identity} glossary_authority mismatch")
    frozen = _frozen_route_evidence(entry)
    _require(card["actual_behavior"] == frozen["actual_behavior"],
             f"{identity} actual_behavior mismatch")
    _require(card["display_context"] == frozen["display_context"],
             f"{identity} display_context mismatch")
    _require(card["consumer"] == frozen["consumer"],
             f"{identity} consumer mismatch")
    _require(card["producers"] == frozen["producers"],
             f"{identity} producers mismatch")
    _require(card["evidence_locations"] == entry["evidence_locations"],
             f"{identity} evidence_locations mismatch")
    _require(card["confidence"] in CONFIDENCE_LEVELS,
             f"{identity} confidence mismatch")
    _require(_nonempty_string(card["reentry_trigger"]),
             f"{identity} requires a nonempty reentry_trigger")
    alternatives = card["rejected_alternatives"]
    _require(
        isinstance(alternatives, list) and bool(alternatives)
        and all(_nonempty_string(alternative) for alternative in alternatives),
        f"{identity} rejected_alternatives must be a nonempty string array",
    )
    _require(_nonempty_string(card["reviewer_rationale"]),
             f"{identity} requires a nonempty reviewer_rationale")
    _validate_deferral(card, identity)

    conclusion = card["terminal_conclusion"]
    _require(conclusion in TERMINAL_CONCLUSIONS,
             f"{identity} has nonterminal conclusion {conclusion!r}")
    facts = card["production_facts"]
    _require(isinstance(facts, dict), f"{identity} production_facts must be an object")
    _require_exact_fields(facts, PRODUCTION_FACT_FIELDS,
                          f"{identity} production_facts")
    _require(facts == _expected_production_facts(inventory, entry),
             f"{identity} production_facts mismatch")

    current_english = [
        variant["raw_pattern"] for variant in entry["english_variants"]
    ]
    current_chinese = [variant["chinese"] for variant in entry["variants"]]
    _require(card["current_english"] == current_english,
             f"{identity} current_english mismatch")
    _require(card["current_chinese"] == current_chinese,
             f"{identity} current_chinese mismatch")

    proposed = card["proposed_translation"]
    _require(
        isinstance(proposed, list)
        and len(proposed) == len(entry["variants"])
        and all(isinstance(item, str) for item in proposed),
        f"{identity} proposed_translation coverage mismatch",
    )
    actions = card["reviewed_actions"]
    _validate_actions(actions, entry, proposed, identity)
    transitions = _transition_actions(actions)
    # In-range add ordinals borrow the proposal slot (placeholder): the
    # proposal there is the approved add text whose protocol is bound to the
    # baseline EN variant by _validate_actions, never to the shifted
    # baseline ZH variant.
    in_range_add_ordinals = {
        action["variant_ordinal"] for action in actions
        if action["kind"] == "add"
        and action["variant_ordinal"] < len(entry["variants"])
    }
    reviews = card["variant_reviews"]
    _require(
        isinstance(reviews, list) and len(reviews) == len(entry["variants"]),
        f"{identity} variant_reviews coverage mismatch",
    )
    variant_conclusions: list[str] = []
    for variant, review, proposal in zip(entry["variants"], reviews, proposed):
        ordinal = variant["locator"]["variant_ordinal"]
        context = f"{identity} variant {ordinal}"
        _require(isinstance(review, dict), f"{context} review must be an object")
        review_conclusion = review.get("terminal_conclusion")
        expected_fields = (
            VARIANT_FIELDS | DEFERRAL_FIELDS
            if review_conclusion in DEFER_CONCLUSIONS
            else VARIANT_FIELDS
        )
        _require_exact_fields(review, expected_fields, context)
        _require(review_conclusion in TERMINAL_CONCLUSIONS,
                 f"{context} has nonterminal conclusion {review_conclusion!r}")
        _require(_is_int(review["variant_ordinal"])
                 and review["variant_ordinal"] == ordinal,
                 f"{context} variant_ordinal mismatch")
        for field, expected in (
            ("weight", variant["weight"]),
            ("control_prefix", variant["control_prefix"]),
            ("runtime_tokens", variant["runtime_tokens"]),
            ("random_site_counts", variant["random_site_counts"]),
            ("lua_site_count", variant["lua_site_count"]),
            ("lua_comparison_strings", variant["lua_comparison_strings"]),
            ("english", variant["english"]),
            ("current_chinese", variant["chinese"]),
            ("proposed_translation", proposal),
        ):
            _require(review.get(field) == expected, f"{context} {field} mismatch")
        _require(_nonempty_string(review["rationale"]),
                 f"{context} requires a rationale")
        # Every proposed translation must keep the mapped baseline ZH
        # protocol: the complete protocol tuple (control prefix, ordered
        # runtime tokens with multiplicity, per-site random alternative
        # shape, complete ordered Lua blocks) must equal the baseline ZH
        # variant at that ordinal, or the exact new protocol of the approved
        # card-local protocol_transition.  Weight is variant metadata, not
        # text-derived, so it is bound by the candidate gate only.  There is
        # no generic same-ordinal EN envelope: a candidate and its review
        # ledger jointly agreeing on any other protocol fails closed here,
        # before any candidate is consumed.
        if ordinal not in in_range_add_ordinals:
            transition = transitions.get(ordinal)
            proposal_facts = {
                field: _derived_action_fact(proposal, field)
                for field in PROTOCOL_FIELDS
            }
            if transition is not None:
                expected_facts = {
                    field: transition["new_protocol"][field]
                    for field in PROTOCOL_FIELDS
                }
                envelope = "approved protocol transition"
            else:
                expected_facts = {
                    field: variant[field] for field in PROTOCOL_FIELDS
                }
                envelope = "baseline ZH protocol"
            drift = _first_protocol_drift(proposal_facts, expected_facts)
            _require(
                drift is None,
                f"{context} proposed text {drift} does not match the "
                f"{envelope}",
            )
            if transition is not None:
                _require(
                    proposal == transition["text"],
                    f"{context} protocol_transition proposal must equal "
                    f"the approved text",
                )
        if review_conclusion == "keep":
            _require(proposal == variant["chinese"],
                     f"{context} keep must preserve current Chinese")
        elif review_conclusion in {"adjust", "retranslate"}:
            _require(proposal != variant["chinese"],
                     f"{context} {review_conclusion} must change current Chinese")
        else:
            _validate_deferral(review, context)
            _require(proposal == variant["chinese"],
                     f"{context} deferred conclusion must preserve current Chinese")
        variant_conclusions.append(review_conclusion)

    _require(conclusion == _aggregate(variant_conclusions),
             f"{identity} conclusion aggregation mismatch")
    if conclusion == "keep":
        _require(proposed == current_chinese,
                 f"{identity} keep must preserve current Chinese")
    elif conclusion in {"adjust", "retranslate"}:
        _require(proposed != current_chinese,
                 f"{identity} {conclusion} must change current Chinese")
    else:
        _require(proposed == current_chinese,
                 f"{identity} deferred conclusion must preserve current Chinese")

    if candidate is not None:
        candidate_zh = [variant["chinese"] for variant in candidate["variants"]]
        expected_texts = _expected_candidate_texts(entry, actions, proposed)
        _require(expected_texts == candidate_zh,
                 f"{identity} proposal/action list does not match candidate "
                 f"ZH dump")


def validate_results(
    path: Path, inventory: dict[str, Any],
    candidate_entries: list[dict[str, Any]] | None,
    records: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    if records is None:
        records = _strict_block(path)
    _require(len(records) == EXPECTED_IDENTITY_COUNT + 1,
             "review evidence metadata/card coverage mismatch")
    metadata, cards = records[0], records[1:]
    _require_exact_fields(metadata, METADATA_FIELDS, "review metadata")
    _require(metadata["baseline"] == inventory["baseline_ref"],
             "review metadata baseline mismatch")
    _require(metadata["glossary_sha256"] == inventory["glossary"]["sha256"],
             "review metadata glossary_sha256 mismatch")
    _require(metadata["inventory_sha256"] == inventory["inventory_sha256"],
             "review metadata inventory_sha256 mismatch")
    _require(_is_int(metadata["identity_count"])
             and metadata["identity_count"] == EXPECTED_IDENTITY_COUNT,
             "review metadata identity_count mismatch")
    _require(metadata["english_production_dump_sha256"]
             == inventory["dumps"]["english"]["artifact_sha256"],
             "review metadata english_production_dump_sha256 mismatch")
    _require(metadata["chinese_production_dump_sha256"]
             == inventory["dumps"]["localized"]["artifact_sha256"],
             "review metadata chinese_production_dump_sha256 mismatch")
    _require(metadata["en_variant_count"] == EXPECTED_EN_VARIANT_COUNT
             and metadata["zh_variant_count"] == EXPECTED_ZH_VARIANT_COUNT,
             "review metadata variant counts mismatch")
    _require(metadata["en_random_site_count"] == EXPECTED_EN_RANDOM_SITES
             and metadata["zh_random_site_count"] == EXPECTED_ZH_RANDOM_SITES,
             "review metadata random-site counts mismatch")
    _require(metadata["en_lua_site_count"] == EXPECTED_EN_LUA_SITES
             and metadata["zh_lua_site_count"] == EXPECTED_ZH_LUA_SITES,
             "review metadata Lua site counts mismatch")

    expected_entries = {entry["identity"]: entry for entry in inventory["entries"]}
    seen: dict[str, dict[str, Any]] = {}
    for card in cards:
        _require(isinstance(card, dict), "review card must be an object")
        identity = card.get("identity")
        _require(isinstance(identity, str),
                 "review card identity must be a string")
        _require(identity not in seen, f"duplicate review card {identity!r}")
        seen[identity] = card
    _require(seen.keys() == expected_entries.keys(),
             f"review card identity set mismatch: expected "
             f"{sorted(expected_entries)!r}, got {sorted(seen)!r}")
    _require([card["identity"] for card in cards]
             == [entry["identity"] for entry in inventory["entries"]],
             "review card identity order mismatch")

    candidate_by_identity = (
        {entry["identity"]: entry for entry in candidate_entries}
        if candidate_entries is not None else {}
    )
    counts: dict[str, int] = {}
    for entry in inventory["entries"]:
        card = seen[entry["identity"]]
        _validate_card(card, inventory, entry,
                       candidate_by_identity.get(entry["identity"]))
        conclusion = card["terminal_conclusion"]
        counts[conclusion] = counts.get(conclusion, 0) + 1
    expected_counts = {
        conclusion: count for conclusion, count in sorted(counts.items())
    }
    _require(
        metadata["terminal_conclusion_counts"] == expected_counts,
        f"review metadata terminal_conclusion_counts mismatch: "
        f"{metadata['terminal_conclusion_counts']!r} != {expected_counts!r}",
    )
    return {"metadata": metadata, "cards": cards}


def _zh_protocol_shape(
    ref: str, dump_path: Path | None, label: str, role: str = "baseline",
) -> dict[tuple[str, int], dict[str, Any]]:
    """Project the per-ZH-variant protocol facts from a production dump.

    The baseline shape is re-derived from exact Git (the baseline dump paths
    are not supplied to the candidate gate), while the candidate shape comes
    from the supplied candidate dump; both are validated by the same dump
    binding so the comparison cannot see different parsers.
    """
    if dump_path is not None:
        zh_dump, zh_raw = _load_dump_safe(
            dump_path, f"{label} ZH", "database/zh/"
        )
        derived = shared._derive_scoped_dump(
            ref, "database/zh/", f"{label} ZH",
            source_basename=SOURCE_BASENAME,
        )
        shared._require_scoped_derivation(
            zh_dump, derived, f"{label} ZH", source_basename=SOURCE_BASENAME
        )
        _zh_binding, zh_rows = _dump_binding(
            zh_dump, zh_raw, f"{label} ZH", role=role)
    else:
        derived = shared._derive_scoped_dump(
            ref, "database/zh/", f"{label} ZH",
            source_basename=SOURCE_BASENAME,
        )
        artifact = {
            **derived, "schema_version": 1, "database_name": "speak",
            "source_directory": "database/zh/",
        }
        _zh_binding, zh_rows = _dump_binding(
            artifact, b"", f"{label} ZH", role=role)
    return {
        (row["key"], variant["locator"]["variant_ordinal"]): {
            "chinese": variant["raw_pattern"],
            "weight": variant["weight"],
            "control_prefix": variant["control_prefix"],
            "runtime_tokens": variant["runtime_tokens"],
            "random_site_counts": variant["random_site_counts"],
            "lua_site_count": variant["lua_site_count"],
            "lua_comparison_strings": variant["lua_comparison_strings"],
            "lua_blocks": _lua_blocks(variant["raw_pattern"]),
        }
        for row in zh_rows
        for variant in row["variants"]
    }


def add_candidate(
    inventory: dict[str, Any], candidate_ref: str, english_path: Path,
    localized_path: Path, review_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Bind the candidate to the approved review and prove its differences.

    The candidate gate proves, at the exact-Git level: (1) the candidate
    English side is byte-identical to the baseline; (2) the candidate ZH side
    differs from the baseline only by the reviewed actions (approved
    additions bound to baseline EN locators, the approved orphan removal and
    the single approved protocol_transition) and the reviewed proposal
    texts, with every matched variant's full protocol (weight, control
    prefix, ordered runtime tokens with multiplicity, random-site per-site
    alternative shape, complete ordered Lua blocks) equal to the mapped
    baseline ZH variant (or to the approved transition's exact new protocol)
    and every added variant's full protocol equal to the EN source.  Any
    unreviewed key/weight/control/token/Lua/random-site drift, extra
    insertion, deletion, or reorder fails closed.  The exact-clean candidate
    boundary is proven before any candidate data is consumed, and every
    candidate-tree input is read as a regular-file blob.
    """
    _require(review_records is not None,
             "candidate validation requires review evidence records")
    actions_by_key, proposals_by_key = _review_bindings_from_block(
        review_records
    )
    entry_by_key = {entry["key"]: entry for entry in inventory["entries"]}
    _require(
        set(actions_by_key) <= set(entry_by_key),
        f"reviewed action keys outside the inventory: "
        f"{sorted(set(actions_by_key) - set(entry_by_key))!r}",
    )
    for key, actions in actions_by_key.items():
        entry = entry_by_key[key]
        _validate_actions(actions, entry, None, entry["identity"])
        _require(
            len(proposals_by_key[key]) == len(entry["variants"]),
            f"{entry['identity']} proposed_translation coverage mismatch",
        )

    shared._require_candidate_commit(
        inventory["baseline_ref"], candidate_ref, exact_clean_checkout=True
    )
    _require_regular_git_sources(
        candidate_ref, "database/", "candidate EN")
    _require_regular_git_sources(
        candidate_ref, "database/zh/", "candidate ZH")
    en_dump, en_raw = _load_dump_safe(
        english_path, "candidate EN", "database/")
    zh_dump, zh_raw = _load_dump_safe(
        localized_path, "candidate ZH", "database/zh/"
    )
    candidate_en_derived = shared._derive_scoped_dump(
        candidate_ref, "database/", "candidate EN",
        source_basename=SOURCE_BASENAME,
    )
    shared._require_scoped_derivation(
        en_dump, candidate_en_derived, "candidate EN",
        source_basename=SOURCE_BASENAME,
    )
    shared._require_scoped_derivation(
        zh_dump, shared._derive_scoped_dump(
            candidate_ref, "database/zh/", "candidate ZH",
            source_basename=SOURCE_BASENAME,
        ), "candidate ZH", source_basename=SOURCE_BASENAME,
    )
    _en_binding, en_rows = _dump_binding(
        en_dump, en_raw, "candidate EN", role="candidate"
    )
    _zh_binding, zh_rows = _dump_binding(
        zh_dump, zh_raw, "candidate ZH", role="candidate"
    )
    entries = _pair_entries(en_rows, zh_rows, "candidate", role="candidate")

    # EN no-drift proof without ZH projection: the candidate EN side must
    # equal the baseline EN side at the exact-Git level (source snapshots and
    # complete derived variant lists, EN-only ordinals included).
    baseline_en_derived = shared._derive_scoped_dump(
        inventory["baseline_ref"], "database/", "baseline EN",
        source_basename=SOURCE_BASENAME,
    )
    _require(
        baseline_en_derived["sources"] == candidate_en_derived["sources"],
        "candidate English source drift (wpnnoise.txt snapshot differs "
        "from baseline)",
    )
    _require(
        baseline_en_derived["entries"] == candidate_en_derived["entries"],
        "candidate English drift (EN variant list differs from baseline)",
    )

    # Reviewed-action ZH gate: every candidate ZH variant must be an approved
    # add (text + full protocol equal to the baseline EN variant at the EN
    # locator) or a matched baseline variant (weight and every text-derived
    # protocol field equal to the mapped baseline ZH variant, or to the exact
    # new protocol of the approved card-local protocol_transition; text equal
    # to the reviewed proposal, or the kept shifted variant under an in-range
    # add placeholder).  The walk uses the action ordinals explicitly, so
    # approved insert/removal shifts never mask drift elsewhere.
    baseline_zh_shape = _zh_protocol_shape(
        inventory["baseline_ref"], None, "baseline"
    )
    candidate_zh_shape = _zh_protocol_shape(
        candidate_ref, localized_path, "candidate", role="candidate"
    )
    _require(
        {key for key, _ordinal in candidate_zh_shape}
        == {key for key, _ordinal in baseline_zh_shape},
        "candidate ZH key set drift",
    )

    def _group_by_key(
        shape: dict[tuple[str, int], dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        by_key: dict[str, list[dict[str, Any]]] = {}
        for (key, _ordinal), facts in shape.items():
            by_key.setdefault(key, []).append(facts)
        return by_key

    baseline_zh = _group_by_key(baseline_zh_shape)
    candidate_zh = _group_by_key(candidate_zh_shape)
    en_facts: dict[tuple[str, int], dict[str, Any]] = {}
    for entry in inventory["entries"]:
        for variant in entry["english_variants"]:
            en_facts[(entry["key"],
                      variant["locator"]["variant_ordinal"])] = variant
    for key, baseline_variants in baseline_zh.items():
        actions = actions_by_key.get(key, [])
        entry = entry_by_key[key]
        transitions = _transition_actions(actions)
        slots = _action_slots(len(baseline_variants), actions)
        candidate_variants = candidate_zh[key]
        _require(
            len(slots) == len(candidate_variants),
            f"candidate ZH variant count drift at key {key!r}: expected "
            f"{len(slots)} variants, got {len(candidate_variants)}",
        )
        expected_texts = _expected_candidate_texts(
            entry, actions, proposals_by_key[key]
        )
        for slot in slots:
            candidate_facts = candidate_variants[slot["candidate_ordinal"]]
            if slot["kind"] == "add":
                en_variant = en_facts[(key, slot["action"]["variant_ordinal"])]
                for field in ("weight", "control_prefix", "runtime_tokens",
                              "random_site_counts", "lua_blocks"):
                    _require(
                        candidate_facts[field] == en_variant[field],
                        f"candidate ZH protocol drift at {key!r} add "
                        f"ordinal {slot['action']['variant_ordinal']}: "
                        f"{field}",
                    )
            else:
                baseline_facts = baseline_variants[
                    slot["variant_ordinal"]
                ]
                # Matched slots preserve only the mapped baseline ZH
                # protocol (weight, control prefix, ordered runtime tokens
                # with multiplicity, per-site random alternative shape,
                # complete ordered Lua blocks), or the exact new protocol of
                # the approved card-local protocol_transition.  There is no
                # generic same-ordinal EN envelope, so a shifted variant can
                # never inherit the EN protocol of an unrelated ordinal.
                transition = transitions.get(slot["variant_ordinal"])
                expected_facts = (
                    transition["new_protocol"] if transition is not None
                    else baseline_facts
                )
                for field in TRANSITION_PROTOCOL_ORDER:
                    _require(
                        candidate_facts[field] == expected_facts[field],
                        f"candidate ZH protocol drift at {key!r} ordinal "
                        f"{slot['variant_ordinal']}: {field}",
                    )
            _require(
                candidate_facts["chinese"]
                == expected_texts[slot["candidate_ordinal"]],
                f"candidate ZH text drift at {key!r} ordinal "
                f"{slot['variant_ordinal']}",
            )

    candidate = {
        "candidate_ref": candidate_ref,
        "entries": [{
            "identity": entry["identity"],
            "variants": [
                {"locator": variant["locator"], "chinese": variant["chinese"]}
                for variant in entry["variants"]
            ],
        } for entry in entries],
    }
    candidate["candidate_sha256"] = _sha256(_canonical_json(candidate))
    inventory["candidate"] = candidate
    return candidate["entries"]


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
    parser.add_argument(
        "--glossary", type=Path,
        default=Path(__file__).resolve().parents[2] / "docs/glossary.md",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    candidate_values = (
        args.candidate_ref, args.candidate_english_dump, args.candidate_localized_dump
    )
    if any(value is not None for value in candidate_values):
        _require(all(value is not None for value in candidate_values),
                 "candidate ref and both candidate dumps must be supplied together")
        _require(args.review_results is not None,
                 "candidate validation requires --review-results")
    # The exact-clean candidate boundary is proven before any candidate data
    # is consumed, and the review ledger is read directly from the exact
    # candidate commit tree as a regular-file blob, so a transient worktree
    # substitution can never rebind the emitted candidate evidence.
    records = None
    if args.review_results is not None and args.candidate_ref is not None:
        shared._require_candidate_commit(
            args.baseline_ref, args.candidate_ref, exact_clean_checkout=True
        )
        ledger_bytes = _candidate_regular_blob(
            args.candidate_ref,
            _repo_relative_git_path(args.review_results, "review results"),
            "review results",
        )
        try:
            ledger_text = ledger_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InventoryError(
                "cannot decode review results from the candidate tree"
            ) from exc
        records = _strict_block_from_text(ledger_text, args.review_results)
    inventory = build_inventory(
        args.baseline_ref, args.english_dump, args.localized_dump,
        args.glossary,
        glossary_ref=args.candidate_ref if args.candidate_ref else None,
    )
    if args.review_results is not None and records is None:
        records = _strict_block_safe(args.review_results)
    candidate_entries = None
    if args.candidate_ref is not None:
        candidate_entries = add_candidate(
            inventory, args.candidate_ref,
            args.candidate_english_dump, args.candidate_localized_dump,
            records,
        )
    if args.review_results is not None:
        inventory["review_evidence"] = validate_results(
            args.review_results, inventory, candidate_entries, records=records
        )
    shared._safe_output(args.inventory_output, inventory)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InventoryError as exc:
        print(f"wpnnoise_inventory.py: {exc}", file=sys.stderr)
        raise SystemExit(2)
