#!/usr/bin/env python3
"""Build the production world-text review inventory.

The inventory is intentionally derived from the active C++ enums/tables and a
single sorted walk of production .des files.  It is a read-only audit: known
translation gaps are violations, not reasons to omit rows.
"""

import argparse
from collections import Counter
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from i18n_shared import (  # noqa: E402
    AuditInputError,
    AuditRootError,
    AuditSnapshot,
    audit_snapshot_invocation,
    get_audit_snapshot,
    resolve_audit_root,
)

try:
    ROOT = resolve_audit_root(SCRIPT_ROOT)
except AuditRootError as error:
    print(f"ERROR: invalid audit root: {error}", file=sys.stderr)
    raise SystemExit(2)

SRC = ROOT / "crawl-ref/source"

from audit_god_inventory import ordered_initializer_rows  # noqa: E402
from audit_item_name_inventory import (  # noqa: E402
    active_source,
    function_body,
    resolve_commit,
    sha,
    source_entries,
    source_files,
    tag_major_version,
)
from i18n_extract import _lua_tokens, cpp_unescape  # noqa: E402
from i18n_shared import (  # noqa: E402
    i18n_escape_key,
    load_review_input,
    lowercase_string,
    parse_entries_physical,
    review_input_metadata,
    runtime_normalize_value,
)


BRANCH_ENUM = SRC / "branch-type.h"
BRANCH_DATA = SRC / "branch-data.h"
BRANCH_CC = SRC / "branch.cc"
FEATURE_ENUM = SRC / "dungeon-feature-type.h"
FEATURE_DATA = SRC / "feature-data.h"
EN_BRANCHES = SRC / "dat/descript/branches.txt"
ZH_BRANCHES = SRC / "dat/descript/zh/branches.txt"
EN_FEATURES = SRC / "dat/descript/features.txt"
ZH_FEATURES = SRC / "dat/descript/zh/features.txt"
DES_ROOT = SRC / "dat/des"
ZH_SOURCE_DIR = SRC / "dat/i18n/zh"
GLOSSARY = ROOT / "docs/glossary.md"
TRUSTED_CONTROL_INPUTS = (
    SCRIPT_DIR / "audit_god_inventory.py",
    SCRIPT_DIR / "audit_item_name_inventory.py",
    SCRIPT_DIR / "i18n_extract.py",
    SCRIPT_DIR / "i18n_shared.py",
)

DIRECT_SINKS = {"mpr", "formatted_mpr", "yesno", "take_note", "god_speaks"}
FINITE_TITLE_PRODUCERS = {
    "trove_milestone": {
        "sink_kind": "trove_milestone_title",
        "consumer": "trove_milestone:crawl.mpr",
    },
    "wizlab_milestone": {
        "sink_kind": "wizlab_milestone_title",
        "consumer": "wizlab_milestone:crawl.mpr",
    },
}
TIMED_FIELDS = {
    "initmsg", "finalmsg", "range_msg_fmt", "ranges", "messages", "verb",
    "noisemaker", "disappear", "entity", "desc",
}
INTERNAL_FEATURES = {
    "DNGN_UNSEEN": "internal_sentinel",
    "DNGN_EXPLORE_HORIZON": "internal_overlay",
    "DNGN_TRAVEL_TRAIL": "internal_overlay",
    "DNGN_DECORATIVE_FLOOR": "dummy_redefinition",
}
DISPLAY_ASSIGNMENTS = TIMED_FIELDS | {"toll_desc"}
PROTOCOL_ASSIGNMENTS = {
    "NAME", "TAGS", "KFEAT", "MARKER", "replica_name", "feature",
    "vaultname",
}
CRAWL_API_CLASSIFICATIONS = {
    "included_player_display": {
        "formatted_mpr", "god_speaks", "mpr", "take_note", "yesno",
    },
    "display_translation_helper": {
        "grammar", "t_",
    },
    "persistent_protocol": {
        "mark_game_won", "mark_milestone",
    },
    "diagnostic": {
        "dpr",
    },
    "ui_control": {
        "more", "redraw_view", "tutorial_msg",
    },
    "gameplay_state_or_lookup": {
        "game_started", "make_name", "set_max_runes", "split_bytes",
    },
    "randomness": {
        "coinflip", "div_rand_round", "one_chance_in", "random2",
        "random2avg", "random_range", "random_real", "rng_wrap", "roll_dice",
        "x_chance_in_y",
    },
}
CONSTRUCTOR_CLASSIFICATIONS = {
    "timed_msg": "included_display_marker",
    "timed_marker": "included_display_marker",
    "portal_desc": "included_display_marker",
    "trove_marker": "included_display_marker",
    "tutorial_msg": "excluded_lookup_protocol_owned",
    "tutorial_hint": "excluded_lookup_protocol_owned",
    "get_marker": "excluded_lookup_protocol_owned",
    "lua_marker": "excluded_lookup_protocol_owned",
    "props_marker": "excluded_lookup_protocol_owned",
}
REVIEW_COLUMNS = [
    "identity",
    # Existing evidence-card fields retained for compatibility.
    "producer_consumer",
    "trigger_context",
    "persistence_protocol",
    "en",
    "zh",
    "mechanics_tokens",
    # Plan-required independently reviewable fields.
    "lifecycle",
    "display_context",
    "producer",
    "consumers_users",
    "mechanics_behavior",
    "target_scope_conditions_exceptions_consequences",
    "trigger_timing",
    "persistence_serialization",
    "late_translation_sink",
    "format_entity_markup_structure_tokens",
    "glossary_decision_authority",
    "shared_dependency_group",
    "evidence_locations",
    "proposed_translation",
    "adopted_translation",
    "rejected_alternatives",
    "confidence",
    "deferred_follow_up",
    "re_entry_conditions",
    "conclusion",
]
REVIEW_DECISION_FIELDS = {
    "proposed_translation",
    "adopted_translation",
    "rejected_alternatives",
    "confidence",
    "deferred_follow_up",
    "re_entry_conditions",
}
PENDING_REVIEW = "pending review"
TERMINAL_CONCLUSION_KINDS = (
    "adjust",
    "defer implementation",
    "defer terminology",
    "keep",
    "retranslate",
)
TERMINAL_CONCLUSION_PATTERNS = (
    ("adjust", re.compile(r"^(?:adjust|调整)\b", re.I)),
    (
        "defer implementation",
        re.compile(r"^(?:defer implementation|暂缓实现)\b", re.I),
    ),
    (
        "defer terminology",
        re.compile(r"^(?:defer terminology|暂缓术语)\b", re.I),
    ),
    ("keep", re.compile(r"^(?:keep|保留)\b", re.I)),
    ("retranslate", re.compile(r"^(?:retranslate|重译)\b", re.I)),
)
VISIBLE_TERMINAL_SUMMARY_HEADING = "最终结论与实现证据"
REVIEW_ARTIFACT_BEGIN = "<!-- BEGIN WORLD REVIEW ARTIFACT v1 -->"
REVIEW_ARTIFACT_END = "<!-- END WORLD REVIEW ARTIFACT v1 -->"
REVIEW_EVIDENCE_BEGIN = "<!-- BEGIN WORLD INVENTORY EVIDENCE -->"
REVIEW_EVIDENCE_END = "<!-- END WORLD INVENTORY EVIDENCE -->"
REVIEW_STRUCTURE_MARKERS = (
    REVIEW_ARTIFACT_BEGIN,
    REVIEW_ARTIFACT_END,
    REVIEW_EVIDENCE_BEGIN,
    REVIEW_EVIDENCE_END,
)
WORLD_INVENTORY_HISTORY = (
    (
        "最初发现清单：781 个 identity，Inventory-SHA256 "
        "`05dcadd34933fae5b5f62d892e3dbd29acbe5fdf0bac9647d6303809c911d96b`。"
    ),
    (
        "翻译资产落地后的旧成员清单：781 个 identity，Inventory-SHA256 "
        "`100cadf8d9c6fd0b970a0816dbef44b4cb2f2580a05dfa5aefc2a793a444b4af`。"
    ),
    (
        "显示槽纠错后的 761 成员清单：Inventory-SHA256 "
        "`7a56e520767dce0a1d57a3af82a4fd14705f2c3b304e8b218865fea33892b2be`；"
        "同一成员集合在 scanner 生产事实加固后重冻结为 "
        "`940e4b0d41ee1b6a3dc4f3ebcfd677950d75c1e391544dc644acb52e140e4dac`。"
    ),
    (
        "readiness 候选清单：788 个 identity，Inventory-SHA256 "
        "`34d8c6bbf8cdb440253fe49435ac7d719921ccad72aec91e506456d5e14d937c`。"
    ),
    (
        "完整 composite adoption facts 候选清单：788 个 identity，"
        "Inventory-SHA256 "
        "`3b49625119479dddeaa9aee96790bf2cc056e834fb781bca21b0daf774cd15d8`；"
        "该候选因错误采用首个分隔符前的非生产 TextDB prefix 语义而被 "
        "code review 拒绝。"
    ),
    (
        "绑定生产 TextDB prefix 语义的上一清单：788 个 identity，"
        "Inventory-SHA256 "
        "`98bf113173ab65ba614b960d827553aae31a5bc52c55e993706f686468ab1cb4`；"
        "40 branch + 211 feature + 14 portal_family + 523 des_display。"
    ),
    (
        "本地化笔记快照落地后的最终清单：789 个 identity，Inventory-SHA256 "
        "`fae158ab3d86729924978f2124d79c05ea3f598d93d6e925171b911cdeb3d335`；"
        "40 branch + 211 feature + 14 portal_family + 524 des_display。"
    ),
    (
        "生命周期：781 current + 4 compatibility_unfinished + "
        "1 dummy_redefinition + 2 internal_overlay + 1 internal_sentinel。"
    ),
    (
        "最终 inventory 的 17 类 violations 均为 0；前述清单只作为 "
        "superseded 审计历史，不计入最终覆盖数。"
    ),
)
WORLD_INITMSG_OLD_ONLY = (
    (
        "des_display:crawl-ref/source/dat/des/portals/bailey.des:"
        "function:bailey_portal:initmsg:3",
        "des_display:crawl-ref/source/dat/des/portals/bailey.des:"
        "function:bailey_portal:initmsg:2",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/bazaar.des:"
        "function:bazaar_portal:initmsg:3",
        "des_display:crawl-ref/source/dat/des/portals/bazaar.des:"
        "function:bazaar_portal:initmsg:1",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/bazaar.des:"
        "function:bazaar_portal:initmsg:4",
        "des_display:crawl-ref/source/dat/des/portals/bazaar.des:"
        "function:bazaar_portal:initmsg:1",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/desolation.des:"
        "function:desolation_portal:initmsg:3",
        "des_display:crawl-ref/source/dat/des/portals/desolation.des:"
        "function:desolation_portal:initmsg:2",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/gauntlet.des:"
        "function:gauntlet_portal:initmsg:3",
        "des_display:crawl-ref/source/dat/des/portals/gauntlet.des:"
        "function:gauntlet_portal:initmsg:2",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/icecave.des:"
        "function:ice_cave_portal:initmsg:3",
        "des_display:crawl-ref/source/dat/des/portals/icecave.des:"
        "function:ice_cave_portal:initmsg:2",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/necropolis.des:"
        "function:necropolis_portal_entry:initmsg:3",
        "des_display:crawl-ref/source/dat/des/portals/necropolis.des:"
        "function:necropolis_portal_entry:initmsg:2",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/ossuary.des:"
        "function:ossuary_portal:initmsg:3",
        "des_display:crawl-ref/source/dat/des/portals/ossuary.des:"
        "function:ossuary_portal:initmsg:2",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/sewer.des:"
        "function:sewer_portal:initmsg:3",
        "des_display:crawl-ref/source/dat/des/portals/sewer.des:"
        "function:sewer_portal:initmsg:2",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/volcano.des:"
        "function:volcano_portal:initmsg:3",
        "des_display:crawl-ref/source/dat/des/portals/volcano.des:"
        "function:volcano_portal:initmsg:2",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "function:wizlab_portal:initmsg:3",
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "function:wizlab_portal:initmsg:1",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "function:wizlab_portal:initmsg:4",
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "function:wizlab_portal:initmsg:1",
    ),
)
WORLD_DIAGNOSTIC_OLD_ONLY = (
    (
        "des_display:crawl-ref/source/dat/des/arrival/twisted.des:"
        "NAME:dpeg_arrival_water_fire:crawl.mpr:1",
        "map-generation coordinate diagnostic",
    ),
    (
        "des_display:crawl-ref/source/dat/des/builder/"
        "layout_geoelf_castle.des:NAME:layout_geoelf_castle:crawl.mpr:1",
        "map-generation diagnostic output",
    ),
    (
        "des_display:crawl-ref/source/dat/des/builder/"
        "layout_geoelf_castle.des:NAME:layout_geoelf_castle:crawl.mpr:2",
        "map-generation diagnostic output",
    ),
    (
        "des_display:crawl-ref/source/dat/des/builder/"
        "layout_geoelf_castle.des:NAME:layout_geoelf_castle:crawl.mpr:3",
        "map-generation diagnostic output",
    ),
    (
        "des_display:crawl-ref/source/dat/des/builder/"
        "layout_geoelf_castle.des:NAME:layout_geoelf_castle:crawl.mpr:4",
        "map-generation diagnostic output",
    ),
    (
        "des_display:crawl-ref/source/dat/des/builder/"
        "layout_geoelf_castle.des:NAME:layout_geoelf_castle:crawl.mpr:5",
        "map-generation diagnostic output",
    ),
    (
        "des_display:crawl-ref/source/dat/des/builder/"
        "layout_geoelf_castle.des:NAME:layout_geoelf_castle:crawl.mpr:6",
        "map-generation diagnostic output",
    ),
    (
        "des_display:crawl-ref/source/dat/des/variable/compat.des:"
        "function:get_replica:crawl.mpr:3",
        "replica coordinate diagnostic output",
    ),
)
WORLD_READINESS_ADDITIONS = (
    (
        "des_display:crawl-ref/source/dat/des/portals/trove.des:"
        "NAME:index_due_trove_eringya:trove_milestone_title:1",
        "Eringya's Secret Bog",
        "埃林吉亚的秘密毒沼",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/trove.des:"
        "NAME:nicolae_index_trove_orange_crystal:trove_milestone_title:1",
        "an orange crystal hatchery",
        "橙晶孵化场",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/trove.des:"
        "NAME:nicolae_trove_octopus_king:trove_milestone_title:1",
        "The Octopus King's Forgotten Garden",
        "章鱼王的遗忘花园",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/trove.des:"
        "NAME:pf_index_trove_rutra:trove_milestone_title:1",
        "Rutra's Hidden Sanctum",
        "鲁特拉的隐秘圣所",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/trove.des:"
        "NAME:regret_index_trove_dread_knight:trove_milestone_title:1",
        "The Dread Knight's Derelict Chapel",
        "恐惧骑士的废弃礼拜堂",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/trove.des:"
        "NAME:regret_index_trove_erebora:trove_milestone_title:1",
        "The Lost Hoard of Erebora",
        "埃雷博拉失落的宝藏",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/trove.des:"
        "NAME:regret_index_trove_justicar:trove_milestone_title:1",
        "The First Justicar's Armoury",
        "初代执法官的军械库",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/trove.des:"
        "NAME:regret_index_trove_leda:trove_milestone_title:1",
        "Leda's Sunken Stockpile",
        "勒达的沉没储藏室",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/trove.des:"
        "NAME:regret_index_trove_nameless_infernalists:"
        "trove_milestone_title:1",
        "The Name-Rending Infernalists' Reservoir",
        "裂名炼狱术士的秘库",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/trove.des:"
        "NAME:regret_index_trove_ozocubu:trove_milestone_title:1",
        "Ozocubu's Refrigerator",
        "奥佐库布的冷藏库",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/trove.des:"
        "NAME:regret_index_trove_rift:trove_milestone_title:1",
        "a devouring Rift",
        "吞噬万物的裂隙",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/trove.des:"
        "NAME:regret_index_trove_storm_queen:trove_milestone_title:1",
        "The Storm Queen's Palace Crash-Site",
        "风暴女王宫殿坠毁地",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "NAME:wizlab_alistair:wizlab_milestone_title:1",
        "Alistair's Party Mansion",
        "阿利斯泰尔的宴会庄园",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "NAME:wizlab_borgnjor:wizlab_milestone_title:1",
        "Borgnjor's Mausoleum",
        "博格尼尔的陵墓",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "NAME:wizlab_cigotuvi:wizlab_milestone_title:1",
        "Cigotuvi's Fleshworks",
        "西格图维的血肉工坊",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "NAME:wizlab_cloud:wizlab_milestone_title:1",
        "The Chambers of the Cloud Mage",
        "云中法师的密室",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "NAME:wizlab_demon:wizlab_milestone_title:1",
        "The Hall of the Hellbinder",
        "地狱缚者的大厅",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "NAME:wizlab_doroklohe:wizlab_milestone_title:1",
        "Doroklohe's Tomb",
        "多洛克洛之墓",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "NAME:wizlab_eringya:wizlab_milestone_title:1",
        "Eringya's Formal Garden",
        "埃林吉亚的规整花园",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "NAME:wizlab_golubria:wizlab_milestone_title:1",
        "The Roulette of Golubria",
        "戈卢布里亚的轮盘赌",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "NAME:wizlab_iskenderun:wizlab_milestone_title:1",
        "Iskenderun's Mystic Tower",
        "伊斯肯德伦的神秘高塔",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "NAME:wizlab_lehudib:wizlab_milestone_title:1",
        "Lehudib's Moon Base",
        "勒胡迪布的月球基地",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "NAME:wizlab_maxwell:wizlab_milestone_title:1",
        "Maxwell's Workshop",
        "麦克斯韦的工坊",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "NAME:wizlab_tukima:wizlab_milestone_title:1",
        "Tukima's Studio",
        "图基玛的工作室",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "NAME:wizlab_wucad:wizlab_milestone_title:1",
        "Wucad Mu's Monastery",
        "吴卡德·穆的修道院",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "NAME:wizlab_yara:wizlab_milestone_title:1",
        "Yara's Duelist Academy",
        "亚拉的决斗学院",
    ),
    (
        "des_display:crawl-ref/source/dat/des/portals/wizlab.des:"
        "NAME:wizlab_zonguldrok:wizlab_milestone_title:1",
        "Zonguldrok's Shrine",
        "宗古德洛克的神殿",
    ),
)
WORLD_IMPLEMENTATION_EVIDENCE = (
    (
        "每个 identity 恰有一张 terminal evidence card；全部生产事实单元由 "
        "scanner 的 `review_expected_fact_cells()` 从当前生产源重新导出，"
        "人工结论不充当 producer/consumer、机制、token 或 sink 事实来源。"
    ),
    (
        "静态与动态显示路径均在最终显示 sink 翻译；Trove/Wizlab 玩家显示 "
        "title 参数使用有限 SourceDB 标题翻译。note 保存语言锁定的完整显示"
        "快照，缺键时整条英文回退；milestone 保持 canonical English。"
    ),
    (
        "readiness 修正覆盖 `sewer drain`、Trove/Wizlab title、portal 名称、"
        "格律翁／万魔殿领主专名及 transporter；English lookup/protocol/"
        "storage key 均未翻译。"
    ),
    "Code profile PASS：`20260726T223908120479000+0800-70564-01dc9911ec99`。",
    (
        "Translation profile PASS："
        "`20260726T224439361358000+0800-73377-01dc9911ec99`。"
    ),
    (
        "DLua prefix 定向测试、protocol negative scanner，以及 portal "
        "EN↔ZH/display-title/storage 定向测试均 PASS。"
    ),
)
WORLD_DEFER_GROUPS = (
    (
        "compatibility_unfinished lifecycle",
        (
            "branch:BRANCH_DWARF",
            "branch:BRANCH_BLADE",
            "branch:BRANCH_FOREST",
            "branch:BRANCH_LABYRINTH",
        ),
    ),
    (
        "dummy_redefinition lifecycle",
        ("feature:DNGN_DECORATIVE_FLOOR",),
    ),
    (
        "internal_overlay lifecycle",
        (
            "feature:DNGN_EXPLORE_HORIZON",
            "feature:DNGN_TRAVEL_TRAIL",
        ),
    ),
    (
        "internal_sentinel lifecycle",
        ("feature:DNGN_UNSEEN",),
    ),
    (
        "other explicitly owned deferral",
        (
            "des_display:crawl-ref/source/dat/des/variable/compat.des:"
            "function:get_replica:crawl.mpr:1",
        ),
    ),
    (
        "protocol-only or non-display feature identity",
        (
            "feature:DNGN_BADLY_SEALED_DOOR",
            "feature:DNGN_EXIT_LABYRINTH",
            "feature:DNGN_ENTER_LABYRINTH",
            "feature:DNGN_ENTER_DWARF",
            "feature:DNGN_ENTER_FOREST",
            "feature:DNGN_ENTER_BLADE",
            "feature:DNGN_EXIT_DWARF",
            "feature:DNGN_EXIT_FOREST",
            "feature:DNGN_EXIT_BLADE",
            "feature:DNGN_ALTAR_PAKELLAS",
            "feature:DNGN_DRY_FOUNTAIN_BLUE",
            "feature:DNGN_DRY_FOUNTAIN_SPARKLING",
            "feature:DNGN_DRY_FOUNTAIN_BLOOD",
        ),
    ),
)


def _lexical_input_path(path, *, allow_external=False):
    """Return the immutable namespace and lexical absolute input path."""
    lexical = Path(os.path.abspath(os.fspath(path)))
    if lexical in TRUSTED_CONTROL_INPUTS:
        return "control", lexical
    try:
        lexical.relative_to(ROOT)
    except ValueError:
        try:
            lexical.relative_to(SCRIPT_ROOT)
        except ValueError as error:
            if allow_external:
                return "external", lexical
            raise AuditInputError(
                f"world inventory input is outside candidate/control roots: {path}"
            ) from error
        return "control", lexical
    return "candidate", lexical


def relative(path):
    namespace, lexical = _lexical_input_path(path, allow_external=True)
    if namespace == "candidate":
        return lexical.relative_to(ROOT).as_posix()
    if namespace == "control":
        return (
            "trusted-control/"
            + lexical.relative_to(SCRIPT_ROOT).as_posix()
        )
    return os.fspath(lexical)


def audit_snapshot():
    return get_audit_snapshot(ROOT)


_CONTROL_SNAPSHOT = None


def control_snapshot():
    global _CONTROL_SNAPSHOT
    if _CONTROL_SNAPSHOT is None:
        configured_root = os.environ.get("ZH_VERIFY_CONTROL_ROOT")
        configured_commit = os.environ.get("ZH_VERIFY_CONTROL_COMMIT")
        if (configured_root is None) != (configured_commit is None):
            raise AuditInputError(
                "ZH_VERIFY_CONTROL_ROOT and ZH_VERIFY_CONTROL_COMMIT "
                "must be provided together"
            )
        if configured_root is None:
            _CONTROL_SNAPSHOT = AuditSnapshot(SCRIPT_ROOT, None)
        else:
            control_root = Path(configured_root)
            if not control_root.is_absolute():
                raise AuditInputError(
                    "ZH_VERIFY_CONTROL_ROOT must be an absolute path"
                )
            try:
                control_root = control_root.resolve(strict=True)
            except OSError as error:
                raise AuditInputError(
                    "ZH_VERIFY_CONTROL_ROOT cannot be resolved"
                ) from error
            if control_root != SCRIPT_ROOT.resolve():
                raise AuditInputError(
                    "ZH_VERIFY_CONTROL_ROOT does not equal the trusted "
                    "auditor checkout"
                )
            _CONTROL_SNAPSHOT = AuditSnapshot(
                control_root, configured_commit
            )
    return _CONTROL_SNAPSHOT


def input_sha256(path):
    namespace, lexical = _lexical_input_path(path)
    if namespace == "control":
        return control_snapshot().sha256(lexical)
    return audit_snapshot().sha256(lexical)


def physical_db(path):
    entries = parse_entries_physical(audit_snapshot().read(
        path, allow_external_unbound=True
    ))
    counts = Counter(entry.canonical_key for entry in entries)
    effective = {}
    raw = {}
    for entry in entries:
        effective[entry.canonical_key] = runtime_normalize_value(entry.value)
        raw[entry.raw_key] = runtime_normalize_value(entry.value)
    return {
        "effective": effective,
        "raw": raw,
        "duplicates": sorted(key for key, count in counts.items() if count > 1),
    }


def _enum_body(path, enum_name, terminator):
    text = active_source(path)
    match = re.search(
        rf"\benum\s+{re.escape(enum_name)}[^{{]*\{{(.*?)"
        rf"\b{re.escape(terminator)}\b",
        text,
        re.S,
    )
    if not match:
        raise RuntimeError(f"{enum_name} ending at {terminator} was not found")
    return re.sub(r"//[^\n]*|/\*.*?\*/", "", match.group(1), flags=re.S)


def enum_identities(path, enum_name, prefix, terminator):
    """Parse concrete enum identities, values, and aliases after TAG pruning."""
    body = _enum_body(path, enum_name, terminator)
    values = {}
    concrete = []
    aliases = []
    next_value = 0
    for part in body.split(","):
        declaration = part.strip()
        if not declaration:
            continue
        match = re.fullmatch(
            rf"({re.escape(prefix)}[A-Z0-9_]+)"
            r"(?:\s*=\s*([A-Z0-9_]+|[-+]?\d+))?",
            declaration,
        )
        if not match:
            raise RuntimeError(f"unsupported enum declaration: {declaration}")
        identity, expression = match.groups()
        alias_of = None
        if expression is None:
            value = next_value
        elif re.fullmatch(r"[-+]?\d+", expression):
            value = int(expression)
        elif expression in values:
            value = values[expression]
            alias_of = expression
        else:
            raise RuntimeError(
                f"unresolved enum expression for {identity}: {expression}"
            )
        values[identity] = value
        next_value = value + 1
        record = {"identity": identity, "value": value}
        if alias_of:
            record["alias_of"] = alias_of
            aliases.append(record)
        else:
            concrete.append(record)
    if not concrete:
        raise RuntimeError(f"no concrete {prefix} identities parsed")
    return concrete, aliases


def _cpp_literals(text):
    return [
        cpp_unescape(raw)
        for raw in re.findall(r'"((?:[^"\\]|\\.)*)"', text)
    ]


def _split_cpp_fields(row):
    fields = []
    start = 1 if row.lstrip().startswith("{") else 0
    text = row.lstrip()
    depth = 0
    state = "code"
    field_start = start
    for index in range(start, len(text)):
        char = text[index]
        if state == "code":
            if char == '"':
                state = "string"
            elif char == "'":
                state = "char"
            elif char in "({[":
                depth += 1
            elif char in ")}]":
                depth -= 1
            elif char == "," and depth == 0:
                fields.append(text[field_start:index].strip())
                field_start = index + 1
        elif char == "\\":
            state = "escape"
        elif (state == "string" and char == '"') or (
                state == "char" and char == "'"):
            state = "code"
        elif state == "escape":
            state = "string"
    tail = text[field_start:].strip().rstrip("}").strip()
    if tail:
        fields.append(tail)
    return fields


def branch_rows():
    enum_rows, aliases = enum_identities(
        BRANCH_ENUM, "branch_type", "BRANCH_", "NUM_BRANCHES"
    )
    initializers = ordered_initializer_rows(
        active_source(BRANCH_DATA), r"\bbranches\s*\[\s*NUM_BRANCHES\s*\]"
    )
    data = []
    for raw in initializers:
        fields = _split_cpp_fields(raw)
        identity_match = re.match(r"\{\s*(BRANCH_[A-Z0-9_]+)\s*,", raw)
        literals = _cpp_literals(raw)
        if not identity_match or len(literals) < 3:
            raise RuntimeError(f"unparsed branch initializer: {raw[:100]}")
        entry_match = re.search(
            r'"(?:[^"\\]|\\.)*"\s*,\s*"(?:[^"\\]|\\.)*"\s*,\s*'
            r'"(?:[^"\\]|\\.)*"\s*,\s*'
            r'((?:"(?:[^"\\]|\\.)*"\s*)+|nullptr)\s*,',
            raw,
            re.S,
        )
        entry_message = None
        if entry_match and entry_match.group(1).strip() != "nullptr":
            entry_message = "".join(_cpp_literals(entry_match.group(1)))
        data.append({
            "identity": identity_match.group(1),
            "shortname": literals[0],
            "longname": literals[1],
            "abbrevname": literals[2],
            "entry_message": entry_message,
            "mechanics": {
                "parent": fields[1],
                "mindepth": fields[2],
                "maxdepth": fields[3],
                "numlevels": fields[4],
                "absdepth": fields[5],
                "flags": fields[6],
                "entry_feature": fields[7],
                "exit_feature": fields[8],
                "escape_feature": fields[9],
                "runes": fields[17],
                "noise": fields[18],
                "descent_parents": fields[20],
            },
            "raw_producer": raw,
        })

    unfinished_body = function_body(active_source(BRANCH_CC),
                                    "branch_is_unfinished")
    unfinished = set(re.findall(r"\bBRANCH_[A-Z0-9_]+\b", unfinished_body))
    source = source_entries(ZH_SOURCE_DIR)
    en_desc = physical_db(EN_BRANCHES)
    zh_desc = physical_db(ZH_BRANCHES)
    rows = []
    for item in data:
        identity = item["identity"]
        keys = [
            ("shortname", item["shortname"]),
            ("longname", item["longname"]),
            ("entry_message", item["entry_message"]),
        ]
        display = []
        for field, key in keys:
            if key:
                display.append({
                    "field": field,
                    "en": key,
                    "zh": source.get(lowercase_string(i18n_escape_key(key))),
                    "source_exact": (
                        lowercase_string(i18n_escape_key(key)) in source
                    ),
                })
        desc_key = item["shortname"]
        rows.append({
            "identity": f"branch:{identity}",
            "category": "branch",
            "enum_identity": identity,
            "lifecycle": (
                "compatibility_unfinished" if identity in unfinished else "current"
            ),
            **{key: item[key] for key in (
                "shortname", "longname", "abbrevname", "entry_message"
            )},
            "display_strings": display,
            "lookup_identity": {
                "abbrevname": item["abbrevname"],
                "translation_owner": False,
            },
            "shortname_paths": {
                "english_lookup_textdb_key": item["shortname"],
                "display_sink": "branch display consumers translate with T_",
                "required_consumer_refs": [
                    "branch.cc:branch_by_shortname",
                    "describe.cc/lookup-help.cc display sinks",
                ],
            },
            "mechanics": item["mechanics"],
            "raw_producer": item["raw_producer"],
            "english_description": en_desc["raw"].get(desc_key),
            "chinese_description": zh_desc["raw"].get(desc_key),
            "evidence": {
                "enum": relative(BRANCH_ENUM),
                "initializer": relative(BRANCH_DATA),
                "lifecycle_producer": relative(BRANCH_CC),
            },
        })
    proof = {
        "enum_order": [row["identity"] for row in enum_rows],
        "data_order": [row["identity"] for row in data],
        "aliases": aliases,
        "unfinished_from_producer": sorted(unfinished),
    }
    return rows, proof, en_desc, zh_desc


def feature_rows():
    enum_rows, aliases = enum_identities(
        FEATURE_ENUM, "dungeon_feature_type", "DNGN_", "NUM_FEATURES"
    )
    text = active_source(FEATURE_DATA)
    parsed = []
    # Concrete brace rows and macro invocations share the same first three
    # semantic arguments. Macro definitions use the token `enum`, so they
    # cannot satisfy this production-identity pattern.
    pattern = re.compile(
        r"\b(DNGN_[A-Z0-9_]+)\s*,\s*"
        r'"((?:[^"\\]|\\.)*)"\s*,\s*"((?:[^"\\]|\\.)*)"',
        re.S,
    )
    for match in pattern.finditer(text):
        identity, name, vaultname = match.groups()
        parsed.append((match.start(), {
            "identity": identity,
            "name": cpp_unescape(name),
            "vaultname": cpp_unescape(vaultname),
        }))
    for match in re.finditer(
        r"\bSTONE_STAIRS_(DOWN|UP)\s*\(\s*([A-Z]+)\s*,\s*([a-z]+)\s*\)",
        text,
    ):
        direction, numeral, vault_numeral = match.groups()
        parsed.append((match.start(), {
            "identity": f"DNGN_STONE_STAIRS_{direction}_{numeral}",
            "name": f"stone staircase leading {direction.lower()}",
            "vaultname": f"stone_stairs_{direction.lower()}_{vault_numeral}",
        }))
    data = [row for _offset, row in sorted(parsed)]
    macro_behavior = {}
    for match in re.finditer(
        r"#define\s+([A-Z_]+)\([^)]*\)\\\n((?:.*\\\n)+.*)",
        text,
    ):
        flags = re.findall(r"\bFFT_[A-Z0-9_| ]+", match.group(2))
        minimap = re.findall(r"\bMF_[A-Z0-9_]+", match.group(2))
        if flags and minimap:
            macro_behavior[match.group(1)] = (
                flags[-1].strip(), minimap[-1]
            )
    for item in data:
        identity = item["identity"]
        stone = re.fullmatch(
            r"DNGN_STONE_STAIRS_(DOWN|UP)_([A-Z]+)", identity
        )
        if stone:
            macro_name = "STONE_STAIRS_" + stone.group(1)
            invocation = re.search(
                rf"(?m)^\s*{macro_name}\(\s*{stone.group(2)}\s*,.*$",
                text,
            )
            item["flags"], item["minimap"] = macro_behavior[macro_name]
            item["raw_producer"] = invocation.group(0).strip()
            continue
        hit = re.search(
            rf"(?m)^.*\b{re.escape(identity)}\b.*(?:\n(?:.*\\\n)*)?", text
        )
        raw = hit.group(0).strip() if hit else identity
        line_start = text.rfind("\n", 0, hit.start()) + 1 if hit else 0
        line_end = text.find("\n", hit.start()) if hit else 0
        producer_line = text[line_start:line_end]
        macro = re.match(r"\s*([A-Z_]+)\s*\(", producer_line)
        behavior = macro_behavior.get(macro.group(1)) if macro else None
        if not behavior:
            tail = text[hit.start():hit.start() + 500] if hit else ""
            flags = re.search(
                r"\(?\s*\b(FFT_[A-Z0-9_| ]+?)\s*\)?\s*,\s*"
                r"(MF_[A-Z0-9_]+)",
                tail,
            )
            behavior = flags.groups() if flags else (None, None)
        item["flags"], item["minimap"] = behavior
        item["raw_producer"] = raw
    source = source_entries(ZH_SOURCE_DIR)
    en_desc = physical_db(EN_FEATURES)
    zh_desc = physical_db(ZH_FEATURES)
    en_desc_keys = {key.lower(): key for key in en_desc["raw"]}
    zh_desc_keys = {key.lower(): key for key in zh_desc["raw"]}

    def description_value(db, keys, feature_name):
        for candidate in (
                feature_name,
                f"A {feature_name}",
                f"An {feature_name}",
                f"The {feature_name}"):
            matched = keys.get(candidate.lower())
            if matched is not None:
                return db["raw"].get(matched)
        return None

    alias_names = {}
    alias_vaultnames = {}
    for item in data:
        alias_names.setdefault(item["name"], []).append(item["identity"])
        alias_vaultnames.setdefault(item["vaultname"], []).append(item["identity"])
    rows = []
    for item in data:
        identity = item["identity"]
        name = item["name"]
        rows.append({
            "identity": f"feature:{identity}",
            "category": "feature",
            "enum_identity": identity,
            "lifecycle": INTERNAL_FEATURES.get(identity, "current"),
            "name": name,
            "vaultname": item["vaultname"],
            "current_chinese_name": source.get(name.lower()) if name else None,
            "english_description": description_value(
                en_desc, en_desc_keys, name
            ),
            "chinese_description": description_value(
                zh_desc, zh_desc_keys, name
            ),
            "name_alias_group": alias_names[name],
            "vaultname_alias_group": alias_vaultnames[item["vaultname"]],
            "protocol_identity": {
                "vaultname": item["vaultname"],
                "translation_owner": False,
                "display_value": item["name"],
                "required_consumer_refs": [
                    "feature.cc:get_feature_def",
                    "mapdef KFEAT/& lookup consumers",
                    "terrain.cc/describe.cc display consumers",
                ],
            },
            "flags": item["flags"],
            "minimap": item["minimap"],
            "raw_producer": item["raw_producer"],
            "behavior_evidence_refs": [
                "feature.cc:_init_feat_index/get_feature_def",
                "terrain.cc feature behaviour",
                "directn.cc/describe.cc observation sinks",
            ],
            "evidence": {
                "enum": relative(FEATURE_ENUM),
                "initializer": relative(FEATURE_DATA),
            },
        })
    proof = {
        "enum_order": [row["identity"] for row in enum_rows],
        "enum_values": {row["identity"]: row["value"] for row in enum_rows},
        "data_order": [row["identity"] for row in data],
        "aliases": aliases,
    }
    return rows, proof, en_desc, zh_desc


def _line_number(text, offset):
    return text.count("\n", 0, offset) + 1


def _anchor_at(text, offset):
    anchor = "file"
    for match in re.finditer(r"(?m)^\s*NAME:\s*(\S.*?)(?:\s*$)", text[:offset]):
        anchor = "NAME:" + re.sub(r"\s+", " ", match.group(1).strip())
    if anchor == "file":
        functions = list(re.finditer(
            r"\bfunction\s+([A-Za-z_][A-Za-z0-9_.:]*)\s*\(", text[:offset]
        ))
        if functions:
            anchor = "function:" + functions[-1].group(1)
    return anchor


def _matching_token(tokens, opening):
    depth = 0
    for index in range(opening, len(tokens)):
        kind = tokens[index][0]
        if kind in {"(", "{", "["}:
            depth += 1
        elif kind in {")", "}", "]"}:
            depth -= 1
            if depth == 0:
                return index
    raise ValueError(f"unclosed Lua expression at offset {tokens[opening][2]}")


def _expression_record(text, tokens, start, end):
    selected = tokens[start:end]
    strings = [token[1] for token in selected if token[0] == "STRING"]
    identifiers = sorted({
        token[1] for token in selected if token[0] == "IDENT"
    })
    expression_end = tokens[end - 1][2] + 1 if selected else 0
    if selected and selected[-1][0] == "STRING":
        quote_start = selected[-1][2]
        if text[quote_start] in {'"', "'"}:
            quote = text[quote_start]
            expression_end = quote_start + 1
            while expression_end < len(text):
                if text[expression_end] == "\\":
                    expression_end += 2
                    continue
                if text[expression_end] == quote:
                    expression_end += 1
                    break
                expression_end += 1
    expression = text[selected[0][2]:expression_end] if selected else ""
    static = None
    meaningful = [token for token in selected if token[0] not in {"(", ")"}]
    if meaningful and all(token[0] in {"STRING", ".", ".."}
                          for token in meaningful):
        static = "".join(strings)
    elif len(meaningful) == 1 and meaningful[0][0] == "STRING":
        static = meaningful[0][1]
    return {
        "expression": expression.strip(),
        "literal_fragments": strings,
        "dynamic_parameters": identifiers,
        "static_english": static,
    }


def _top_level_first_arg(tokens, opening, closing):
    depth = 0
    end = closing
    for index in range(opening + 1, closing):
        kind = tokens[index][0]
        if kind in {"(", "{", "["}:
            depth += 1
        elif kind in {")", "}", "]"}:
            depth -= 1
        elif kind == "," and depth == 0:
            end = index
            break
    return opening + 1, end


def _top_level_args(tokens, opening, closing):
    result = []
    start = opening + 1
    depth = 0
    for index in range(start, closing):
        kind = tokens[index][0]
        if kind in {"(", "{", "["}:
            depth += 1
        elif kind in {")", "}", "]"}:
            depth -= 1
        elif kind == "," and depth == 0:
            result.append((start, index))
            start = index + 1
    result.append((start, closing))
    return result


def _assignment_end(tokens, start, limit):
    depth = 0
    for index in range(start, limit):
        kind = tokens[index][0]
        if kind in {"(", "{", "["}:
            depth += 1
        elif kind in {")", "}", "]"}:
            if depth == 0:
                return index
            depth -= 1
        elif kind == "," and depth == 0:
            return index
    return limit


def _producer_contexts(tokens):
    contexts = []
    names = {"timed_msg", "timed_marker", "portal_desc", "trove_marker"}
    for index, token in enumerate(tokens[:-1]):
        if token[0] != "IDENT" or token[1] not in names:
            continue
        opening = index + 1
        if tokens[opening][0] == "(" and opening + 1 < len(tokens):
            opening += 1
        if tokens[opening][0] != "{":
            continue
        contexts.append({
            "kind": token[1],
            "start": opening,
            "end": _matching_token(tokens, opening),
        })
    return contexts


def _tokensets(value):
    if value is None:
        return {"placeholders": [], "entity_macros": [], "markup": []}
    return {
        "placeholders": sorted(set(re.findall(
            r"%(?:\d+\$)?[-+#0 .'I]*\d*(?:\.\d+)?[a-zA-Z]", value
        ))),
        "entity_macros": sorted(set(
            re.findall(r"\$[A-Za-z]+(?:\{[^}]*\})?|\{[A-Za-z_]+\}", value)
        )),
        "markup": sorted(set(re.findall(r"</?[A-Za-z_]+>", value))),
    }


def _source_lookup(record, source_exact, trim_fallback=False):
    en = record["static_english"]
    lookup = (
        lowercase_string(i18n_escape_key(en)) if en is not None else None
    )
    zh = source_exact.get(lookup) if lookup is not None else None
    matched_key = lookup if zh is not None else None
    if zh is None and trim_fallback and en is not None:
        trimmed = en.rstrip()
        if trimmed != en:
            trimmed_key = lowercase_string(i18n_escape_key(trimmed))
            zh = source_exact.get(trimmed_key)
            if zh is not None:
                matched_key = trimmed_key
    record["source_lookup_key"] = lookup
    record["source_matched_key"] = matched_key
    record["source_trim_fallback"] = bool(
        matched_key is not None and matched_key != lookup
    )
    record["source_exact_match"] = zh is not None
    record["current_chinese"] = zh
    record["tokens"] = {
        "english": _tokensets(en),
        "chinese": _tokensets(zh),
    }
    record["token_drift"] = (
        record["tokens"]["english"] != record["tokens"]["chinese"]
        if zh is not None else False
    )
    return record


def _des_lua_view(text):
    """Mask non-Lua .des syntax while preserving byte/character offsets."""
    output = []
    in_block = False
    interesting = re.compile(
        r"crawl\.(?:mpr|formatted_mpr|yesno|take_note)|"
        r"set_feature_name|portal_desc|toll_desc|"
        r"trove_milestone|wizlab_milestone"
    )
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        starts_block = re.match(
            r"(?i)(?:[a-z_]\w*\s+)?\{\{(?:\s*$|\s+(?:local|function|if|"
            r"crawl|return)\b)",
            stripped,
        )
        include = in_block or bool(starts_block) or stripped.startswith(":")
        include = include or bool(interesting.search(line))
        if include:
            output.append(line)
        else:
            output.append("".join(
                char if char in "\r\n" else " " for char in line
            ))
        if starts_block:
            in_block = True
        if in_block and "}}" in line:
            in_block = False
    if in_block:
        raise ValueError("unterminated .des lua {{ block")
    return "".join(output)


def scan_des_file(path, source_exact, exclusions=None, feature_desc_exact=None):
    """Extract player-facing slots from one .des using the shared Lua lexer."""
    text = audit_snapshot().text(
        path, allow_external_unbound=True
    )
    tokens = list(_lua_tokens(_des_lua_view(text)))
    candidates = []
    exclusions = exclusions if exclusions is not None else []
    contexts = _producer_contexts(tokens)

    # Direct crawl display sinks.
    for index in range(len(tokens) - 3):
        if not (
            tokens[index][:2] == ("IDENT", "crawl")
            and tokens[index + 1][0] == "."
            and tokens[index + 2][0] == "IDENT"
            and tokens[index + 3][0] == "("
        ):
            continue
        sink = tokens[index + 2][1]
        suspicious = re.search(r"mpr|message|note|yesno|formatted", sink)
        if sink not in DIRECT_SINKS and not suspicious:
            continue
        closing = _matching_token(tokens, index + 3)
        arguments = _top_level_args(tokens, index + 3, closing)
        selected_argument = 1 if sink == "god_speaks" else 0
        if selected_argument >= len(arguments):
            exclusions.append({
                "file": relative(path),
                "line": _line_number(text, tokens[index][2]),
                "sink": f"crawl.{sink}",
                "reason": "malformed display sink arguments",
            })
            continue
        start, end = arguments[selected_argument]
        diagnostic_window = text[max(0, tokens[index][2] - 500):
                                 tokens[index][2] + 200]
        literal_text = " ".join(
            token[1] for token in tokens[start:end] if token[0] == "STRING"
        )
        diagnostic_reason = None
        rel_path = relative(path)
        if "/dat/des/builder/" in rel_path:
            diagnostic_reason = "map-generation diagnostic output"
        elif ("/dat/des/arrival/" in rel_path
              and "replica[1].x" in diagnostic_window):
            diagnostic_reason = "map-generation coordinate diagnostic"
        elif re.search(
            r"(?i)(?:^|[< ])error(?:\s|:)|not a valid|couldn.t find",
            literal_text,
        ):
            diagnostic_reason = "diagnostic/error output"
        elif re.search(r"\b(?:wizmode|dry_run|is_validating|debug)\b",
                       diagnostic_window):
            diagnostic_reason = "wizmode/dry_run/validation output"
        if diagnostic_reason:
            exclusions.append({
                "file": relative(path),
                "line": _line_number(text, tokens[index][2]),
                "sink": f"crawl.{sink}",
                "reason": diagnostic_reason,
            })
            continue
        # A nested crawl.t_(...) is the real SourceDB key.  Keep the outer
        # display call as the slot identity whether translation is direct
        # (crawl.mpr(crawl.t_(...))) or followed by interpolation
        # (crawl.mpr(string.format(crawl.t_(...), value))).
        translations = []
        snapshot_wrappers = []
        for pos in range(start, max(start, end - 3)):
            if (
                tokens[pos][:2] == ("IDENT", "util")
                and tokens[pos + 1][0] == "."
                and tokens[pos + 2][:2]
                    == ("IDENT", "i18n_format_or_english")
                and tokens[pos + 3][0] == "("
            ):
                wrapper_end = _matching_token(tokens, pos + 3)
                if wrapper_end < end:
                    wrapper_args = _top_level_args(
                        tokens, pos + 3, wrapper_end
                    )
                    if wrapper_args:
                        key_start, key_end = wrapper_args[0]
                        snapshot_wrappers.append((
                            pos, wrapper_end, wrapper_args,
                            _expression_record(
                                text, tokens, key_start, key_end
                            ),
                        ))
            if not (
                tokens[pos][:2] == ("IDENT", "crawl")
                and tokens[pos + 1][0] == "."
                and tokens[pos + 2][:2] == ("IDENT", "t_")
                and tokens[pos + 3][0] == "("
            ):
                continue
            translation_end = _matching_token(tokens, pos + 3)
            if translation_end < end:
                inner = _expression_record(
                    text, tokens, pos + 4, translation_end
                )
                translations.append((pos + 4, translation_end, inner))
        static_translations = [
            item for item in translations
            if item[2]["static_english"] is not None
        ]
        selected_translation = (
            static_translations[0] if len(static_translations) == 1
            else translations[0] if len(translations) == 1
            else None
        )
        selected_snapshot = (
            snapshot_wrappers[0] if len(snapshot_wrappers) == 1 else None
        )
        snapshot_covers_argument = False
        if selected_snapshot is not None:
            snapshot_start, snapshot_end, _, record = selected_snapshot
            snapshot_covers_argument = (
                snapshot_start == start and snapshot_end == end - 1
            )
            record["expression"] = text[
                tokens[start][2]:tokens[end - 1][2] + 1
            ].strip()
            record["dynamic_parameters"] = sorted(set(
                record["dynamic_parameters"]
                + [
                    token[1] for token in tokens[start:end]
                    if token[0] == "IDENT"
                    and token[1] not in {
                        "util", "i18n_format_or_english",
                    }
                ]
            ))
            late_consumer = "util.i18n_format_or_english"
        elif selected_translation is not None:
            _, _, record = selected_translation
            record["expression"] = text[
                tokens[start][2]:tokens[end - 1][2] + 1
            ].strip()
            record["dynamic_parameters"] = sorted(set(
                record["dynamic_parameters"]
                + [
                    token[1] for token in tokens[start:end]
                    if token[0] == "IDENT"
                    and token[1] not in {"crawl", "t_", "string", "format"}
                ]
            ))
            late_consumer = "crawl.t_"
        else:
            record = _expression_record(text, tokens, start, end)
            late_consumer = None
            if translations:
                record["unsupported"] = (
                    "no unique static translated template in display expression"
                )
        if selected_snapshot is not None:
            _, _, wrapper_args, _ = selected_snapshot
            translated_dynamic_parameters = sorted({
                token[1]
                for argument_start, argument_end in wrapper_args[1:]
                for token in tokens[argument_start:argument_end]
                if token[0] == "IDENT"
            })
        else:
            translated_dynamic_parameters = sorted({
                token[1]
                for translation_start, translation_end, translation
                in translations
                if translation["static_english"] is None
                for token in tokens[translation_start:translation_end]
                if token[0] == "IDENT"
            })
        display_title_parameters = sorted({
            parameter for parameter in record["dynamic_parameters"]
            if re.search(r"(?:^|_)(?:desc|name|title)$", parameter)
        })
        untranslated_display_title_parameters = sorted(
            set(display_title_parameters) - set(translated_dynamic_parameters)
        )
        record.update({
            "sink_kind": f"crawl.{sink}",
            "channel": "note" if sink == "take_note" else "message",
            "trigger": "direct_call",
            "persistence": sink == "take_note",
            "late_translation_consumer": late_consumer,
            "offset": tokens[index][2],
            "line": _line_number(text, tokens[index][2]),
            "translated_dynamic_parameters": translated_dynamic_parameters,
            "display_title_parameters": display_title_parameters,
            "untranslated_display_title_parameters": (
                untranslated_display_title_parameters
            ),
        })
        if sink not in DIRECT_SINKS:
            record["unsupported"] = f"unknown display-like crawl sink: {sink}"
        elif sink == "take_note":
            record["persistence_snapshot"] = {
                "classification": "localized_display_snapshot",
                "language_semantics": (
                    "stored in the creation language; no retroactive "
                    "retranslation"
                ),
            }
            if (
                selected_snapshot is not None
                and not snapshot_covers_argument
            ):
                record["unsupported"] = (
                    "localized note snapshot helper must cover the complete "
                    "note expression"
                )
            elif untranslated_display_title_parameters:
                record["protocol_boundary_issue"] = (
                    "persistent note display title lacks translation before "
                    "storage: "
                    + ", ".join(untranslated_display_title_parameters)
                )
            elif (
                selected_snapshot is not None
                and record["static_english"] is None
            ):
                record["unsupported"] = (
                    "localized note snapshot format key must be a static "
                    "English literal"
                )
            elif record["static_english"] is None and late_consumer is None:
                record["unsupported"] = (
                    "dynamic persistent display snapshot expression"
                )
        elif untranslated_display_title_parameters:
            record["protocol_boundary_issue"] = (
                "dynamic display title parameter lacks late translation: "
                + ", ".join(untranslated_display_title_parameters)
            )
        elif record["static_english"] is None and late_consumer is None:
            record["unsupported"] = "dynamic direct display expression"
        candidates.append(_source_lookup(record, source_exact))

    # Finite runtime title producers. Their literal callsite arguments are
    # distinct display values consumed through crawl.t_(..._desc) by the
    # milestone display helper; inventory them independently of the shared
    # format-template row.
    for index in range(len(tokens) - 1):
        token = tokens[index]
        if (token[0] != "IDENT"
                or token[1] not in FINITE_TITLE_PRODUCERS
                or tokens[index + 1][0] != "("):
            continue
        closing = _matching_token(tokens, index + 1)
        arguments = _top_level_args(tokens, index + 1, closing)
        if len(arguments) < 2:
            continue
        start, end = arguments[1]
        record = _expression_record(text, tokens, start, end)
        if record["static_english"] is None:
            continue
        producer = FINITE_TITLE_PRODUCERS[token[1]]
        record.update({
            "sink_kind": producer["sink_kind"],
            "channel": "message_title",
            "trigger": "vault_epilogue",
            "persistence": False,
            "late_translation_consumer": "crawl.t_",
            "finite_title_producer": token[1],
            "finite_title_consumer": producer["consumer"],
            "offset": token[2],
            "line": _line_number(text, token[2]),
        })
        candidates.append(_source_lookup(record, source_exact))

    # Production display-producing fields.  Each literal is an independent
    # stable slot; table-valued fields therefore retain every alternative.
    for index, token in enumerate(tokens):
        if token[0] != "IDENT":
            continue
        name = token[1]
        if name in DISPLAY_ASSIGNMENTS and index + 1 < len(tokens):
            if tokens[index + 1][0] not in {"=", "{"}:
                continue
            context = next(
                (item for item in contexts
                 if item["start"] < index < item["end"]),
                None,
            )
            allowed = (
                context is not None
                and (
                    (name == "desc"
                     and context["kind"] in {"portal_desc", "timed_marker"})
                    or (name == "toll_desc"
                        and context["kind"] in {"portal_desc", "trove_marker"})
                    or (name in TIMED_FIELDS - {"desc"}
                        and context["kind"] in {"timed_msg", "timed_marker"})
                )
            )
            if not allowed:
                continue
            value_start = index + 2 if tokens[index + 1][0] == "=" else index + 1
            if value_start >= len(tokens):
                continue
            value_end = _assignment_end(tokens, value_start, context["end"])
            is_table = tokens[value_start][0] == "{"
            if is_table and name == "initmsg":
                table_end = _matching_token(tokens, value_start)
                literal_ranges = _top_level_args(
                    tokens, value_start, table_end
                )
            elif is_table:
                literal_ranges = [
                    (pos, pos + 1) for pos in range(value_start, value_end)
                    if tokens[pos][0] == "STRING"
                ]
            else:
                literal_ranges = [(value_start, value_end)]
            if not any(tokens[pos][0] == "STRING"
                       for pos in range(value_start, value_end)):
                candidates.append({
                    "sink_kind": name,
                    "channel": "message",
                    "trigger": "producer_field",
                    "persistence": name in {"toll_desc", "desc"},
                    "late_translation_consumer": (
                        "lm_trove:crawl.t_" if name == "toll_desc"
                        else "lm_tmsg/lm_timed"
                    ),
                    "expression": text[tokens[value_start][2]:
                                       tokens[value_end - 1][2] + 1].strip(),
                    "literal_fragments": [],
                    "dynamic_parameters": sorted({
                        t[1] for t in tokens[value_start:value_end]
                        if t[0] == "IDENT"
                    }),
                    "static_english": None,
                    "source_exact_match": False,
                    "current_chinese": None,
                    "tokens": {"english": _tokensets(None),
                               "chinese": _tokensets(None)},
                    "token_drift": False,
                    "offset": token[2],
                    "line": _line_number(text, token[2]),
                    "unsupported": "dynamic producer field",
                })
            for literal_start, literal_end in literal_ranges:
                record = _expression_record(
                    text, tokens, literal_start, literal_end
                )
                record.update({
                    "sink_kind": name,
                    "channel": "message",
                    "trigger": "producer_field",
                    "persistence": name in {"toll_desc", "desc"},
                    "late_translation_consumer": (
                        "lm_trove:crawl.t_" if name == "toll_desc"
                        else "lm_tmsg/lm_timed"
                    ),
                    "offset": token[2],
                    "line": _line_number(text, token[2]),
                })
                lookup_db = (
                    feature_desc_exact
                    if (name == "desc" and context["kind"] == "portal_desc"
                        and feature_desc_exact is not None)
                    else source_exact
                )
                candidates.append(_source_lookup(
                    record,
                    lookup_db,
                    trim_fallback=name in {
                        "initmsg", "finalmsg", "range_msg_fmt", "ranges",
                        "messages", "verb", "noisemaker", "entity",
                    },
                ))

    # Feature renames: only the second argument is display; first is protocol.
    for index, token in enumerate(tokens):
        if token[:2] != ("IDENT", "set_feature_name"):
            continue
        opening = index + 1
        if opening >= len(tokens) or tokens[opening][0] != "(":
            continue
        closing = _matching_token(tokens, opening)
        depth = 0
        comma = None
        for pos in range(opening + 1, closing):
            if tokens[pos][0] in {"(", "{", "["}:
                depth += 1
            elif tokens[pos][0] in {")", "}", "]"}:
                depth -= 1
            elif tokens[pos][0] == "," and depth == 0:
                comma = pos
                break
        if comma is None:
            continue
        record = _expression_record(text, tokens, comma + 1, closing)
        record.update({
            "sink_kind": "feature_rename",
            "channel": "feature_description",
            "trigger": "feature_observation",
            "persistence": True,
            "late_translation_consumer": "feature description display",
            "offset": token[2],
            "line": _line_number(text, token[2]),
        })
        candidates.append(_source_lookup(record, source_exact))

    rel = relative(path)
    ordinals = Counter()
    rows = []
    for candidate in sorted(candidates, key=lambda row: (
            row["offset"], row["sink_kind"], row.get("static_english") or "")):
        anchor = _anchor_at(text, candidate["offset"])
        key = (anchor, candidate["sink_kind"])
        ordinals[key] += 1
        candidate["identity"] = (
            f"des_display:{rel}:{anchor}:{candidate['sink_kind']}:"
            f"{ordinals[key]}"
        )
        candidate["category"] = "des_display"
        candidate["lifecycle"] = "current"
        candidate["evidence"] = {"file": rel, "line": candidate.pop("line")}
        candidate.pop("offset")
        rows.append(candidate)
    return rows


def des_producer_universe(files):
    """Enumerate and classify every production crawl call/marker constructor."""
    calls = {}
    constructors = {}
    crawl_classification = {}
    for classification, methods in CRAWL_API_CLASSIFICATIONS.items():
        for method in methods:
            if method in crawl_classification:
                raise ValueError(
                    f"crawl.{method} appears in multiple producer classes"
                )
            crawl_classification[method] = classification
    for path in files:
        text = audit_snapshot().text(
            path, allow_external_unbound=True
        )
        tokens = list(_lua_tokens(_des_lua_view(text)))
        for index in range(len(tokens) - 3):
            name = None
            collection = None
            if (tokens[index][:2] == ("IDENT", "crawl")
                    and tokens[index + 1][0] == "."
                    and tokens[index + 2][0] == "IDENT"
                    and tokens[index + 3][0] == "("):
                name = "crawl." + tokens[index + 2][1]
                collection = calls
            elif (tokens[index][0] == "IDENT"
                    and re.search(r"(?:_msg|_hint|_marker|_desc)$",
                                  tokens[index][1])
                    and tokens[index + 1][0] in {"(", "{"}):
                name = tokens[index][1]
                collection = constructors
            if collection is None:
                continue
            record = collection.setdefault(
                name, {"count": 0, "evidence": []}
            )
            record["count"] += 1
            if len(record["evidence"]) < 3:
                record["evidence"].append({
                    "file": relative(path),
                    "line": _line_number(text, tokens[index][2]),
                })
    classified = []
    unknown = []
    for name, evidence in sorted(calls.items()):
        method = name.split(".", 1)[1]
        classification = crawl_classification.get(method, "unknown")
        if classification == "unknown":
            unknown.append(name)
        classified.append(
            {"producer": name, "classification": classification, **evidence}
        )
    for required in {"tutorial_msg", "tutorial_hint"}:
        constructors.setdefault(required, {"count": 0, "evidence": []})
    for name, evidence in sorted(constructors.items()):
        classification = CONSTRUCTOR_CLASSIFICATIONS.get(name, "unknown")
        if classification == "unknown":
            unknown.append(name)
        classified.append(
            {"producer": name, "classification": classification, **evidence}
        )
    return classified, unknown


def des_rows():
    snapshot = audit_snapshot()
    files = list(snapshot.glob(DES_ROOT, "*.des", recursive=True))
    source_exact = {}
    for path in source_files(ZH_SOURCE_DIR):
        for entry in parse_entries_physical(snapshot.read(path)):
            source_exact[entry.canonical_key] = runtime_normalize_value(
                entry.value
            )
    feature_desc_exact = physical_db(ZH_FEATURES)["effective"]
    rows = []
    excluded = []
    excluded_slots = []
    for path in files:
        rel = relative(path)
        if path.name == "test.des" or "test" in path.parts:
            excluded.append({"file": rel, "reason": "test fixture"})
            continue
        try:
            file_rows = scan_des_file(
                path, source_exact, excluded_slots, feature_desc_exact
            )
        except ValueError as error:
            raise ValueError(f"{rel}: {error}") from error
        rows.extend(file_rows)
        if not file_rows:
            excluded.append({
                "file": rel,
                "reason": "no supported player-display producer",
            })
    portal_files = list(snapshot.glob(DES_ROOT / "portals", "*.des"))
    family_rows = []
    child_counts = Counter(
        Path(row["evidence"]["file"]).stem
        for row in rows
        if "/dat/des/portals/" in row["evidence"]["file"]
    )
    for path in portal_files:
        family_rows.append({
            "identity": f"portal_family:{path.stem}",
            "category": "portal_family",
            "lifecycle": "current",
            "file": relative(path),
            "display_slot_count": child_counts[path.stem],
            "evidence": {"file": relative(path)},
        })
    universe, unknown = des_producer_universe(files)
    return (family_rows + rows, files, excluded, excluded_slots,
            universe, unknown)


def inventory_violations(rows, branch_proof, feature_proof,
                         branch_dbs, feature_dbs, unknown_producers=None):
    identities = [row["identity"] for row in rows]
    branches = [row for row in rows if row["category"] == "branch"]
    features = [row for row in rows if row["category"] == "feature"]
    enum_branch = branch_proof["enum_order"]
    data_branch = branch_proof["data_order"]
    enum_feature = feature_proof["enum_order"]
    data_feature = feature_proof["data_order"]
    display = [row for row in rows if row["category"] == "des_display"]
    return {
        "duplicate_identities": sorted(
            identity for identity, count in Counter(identities).items()
            if count > 1
        ),
        "branch_enum_data_set_drift": {
            "enum_only": sorted(set(enum_branch) - set(data_branch)),
            "data_only": sorted(set(data_branch) - set(enum_branch)),
        } if set(enum_branch) != set(data_branch) else {},
        "branch_enum_data_order_drift": (
            {"enum": enum_branch, "data": data_branch}
            if enum_branch != data_branch else {}
        ),
        "feature_enum_data_set_drift": {
            "enum_only": sorted(set(enum_feature) - set(data_feature)),
            "data_only": sorted(set(data_feature) - set(enum_feature)),
        } if set(enum_feature) != set(data_feature) else {},
        "feature_duplicate_data_identities": sorted(
            identity for identity, count in Counter(data_feature).items()
            if count > 1
        ),
        "missing_display_translations": sorted(
            f"{row['identity']}:{item['field']}" for row in branches
            if row["lifecycle"] == "current"
            for item in row["display_strings"] if not item["zh"]
        ) + sorted(
            row["identity"] for row in features
            if row["lifecycle"] == "current" and row["name"]
            and not row["current_chinese_name"]
        ),
        "missing_descriptions": sorted(
            row["identity"] for row in branches + features
            if row["lifecycle"] == "current"
            and row.get("english_description") is not None
            and not row.get("chinese_description")
        ),
        "unexpected_zh_branch_description_keys": sorted(
            set(branch_dbs[1]["raw"]) - set(branch_dbs[0]["raw"])
        ),
        "unexpected_zh_feature_description_keys": sorted(
            set(feature_dbs[1]["raw"]) - set(feature_dbs[0]["raw"])
        ),
        "duplicate_textdb_keys": {
            name: db["duplicates"]
            for name, db in {
                "en_branches": branch_dbs[0],
                "zh_branches": branch_dbs[1],
                "en_features": feature_dbs[0],
                "zh_features": feature_dbs[1],
            }.items() if db["duplicates"]
        },
        "missing_exact_source_keys": sorted(
            row["identity"] for row in display
            if row.get("static_english") and not row["source_exact_match"]
            and not row.get("protocol_deferral")
        ),
        "unresolved_or_unsupported_display_slots": sorted(
            row["identity"] for row in display
            if row.get("unsupported")
        ),
        "placeholder_macro_markup_drift": sorted(
            row["identity"] for row in display if row.get("token_drift")
        ),
        "protocol_display_boundary_issues": sorted(
            row["identity"] for row in display
            if (row["sink_kind"] in PROTOCOL_ASSIGNMENTS
                or row.get("protocol_boundary_issue"))
        ),
        "unknown_des_producers": sorted(unknown_producers or []),
        "missing_branch_mechanics": sorted(
            row["identity"] for row in branches
            if not row.get("mechanics") or not row.get("raw_producer")
        ),
        "missing_feature_behavior_evidence": sorted(
            row["identity"] for row in features
            if not row.get("flags") or not row.get("minimap")
            or not row.get("raw_producer")
            or not row.get("behavior_evidence_refs")
        ),
    }


def _review_safe(value):
    value = str(value if value is not None and value != "" else "(none)")
    # Markdown table parsing strips cell-edge whitespace. Normalize the
    # production-derived expectation to that representable boundary only;
    # inventory identities and SourceDB lookup values remain untouched.
    return re.sub(r"\s+", " ", value).strip().replace("|", "/")


def _row_current_chinese(row):
    return (
        row.get("current_chinese")
        or row.get("current_chinese_name")
        or next((
            item.get("zh") for item in row.get("display_strings", [])
            if item.get("zh")
        ), None)
        or row.get("chinese_description")
    )


def review_expected_composite_adoption(row, adopted_values=None):
    """Build the complete branch/feature adoption object bound to review."""
    if row["category"] == "branch":
        displays = {
            item["field"]: item.get("zh")
            for item in row.get("display_strings", [])
        }
        expected_values = {
            "description": row.get("chinese_description"),
            "entry_message": displays.get("entry_message"),
            "longname": displays.get("longname"),
            "shortname": displays.get("shortname"),
        }
        english_values = {
            "description": row.get("english_description"),
            "entry_message": row.get("entry_message"),
            "longname": row.get("longname"),
            "shortname": row.get("shortname"),
        }
    elif row["category"] == "feature":
        expected_values = {
            "description": row.get("chinese_description"),
            "name": row.get("current_chinese_name"),
            "vaultname": (
                "preserve canonical English: " + row["vaultname"]
                if row.get("vaultname") else None
            ),
        }
        english_values = {
            "description": row.get("english_description"),
            "name": row.get("name"),
            "vaultname": row.get("vaultname"),
        }
    else:
        return None

    values = expected_values if adopted_values is None else adopted_values
    return {
        "category": row["category"],
        "values": values,
        "tokens": {
            field: {
                "english": _tokensets(english_values.get(field) or ""),
                "adopted": _tokensets(values.get(field) or ""),
            }
            for field in expected_values
        },
    }


def _submitted_composite_adoption(row, cell):
    """Canonicalize the adopted/current object carried by a decision cell."""
    try:
        decision = json.loads(cell)
    except (TypeError, json.JSONDecodeError):
        return {"invalid_json": cell}
    if not isinstance(decision, dict):
        return {"invalid_structure": decision}
    if "adopt" in decision:
        adopted = decision["adopt"]
    elif "current" in decision:
        # Keep/defer cards preserve the production value rather than proposing
        # a replacement, so their current object is the adopted object.
        adopted = decision["current"]
    elif set(decision) == set(
            review_expected_composite_adoption(row)["values"]):
        # Some terminal adjustment cards carry the complete adopted object
        # directly, without historical/current wrapper metadata.
        adopted = decision
    else:
        return {"missing_adopt_or_current": decision}
    if not isinstance(adopted, dict):
        return {"invalid_adopted_object": adopted}
    return review_expected_composite_adoption(row, adopted)


def review_expected_fact_cells(payload, row):
    """Return production-derived evidence cells shared by writer and validator."""
    evidence = row.get("evidence", {})
    producer = evidence.get("file") or evidence.get("initializer") or (
        row.get("file") or row["category"]
    )
    consumers = (
        row.get("behavior_evidence_refs")
        or row.get("protocol_identity", {}).get("required_consumer_refs")
        or row.get("shortname_paths", {}).get("required_consumer_refs")
        or [row.get("finite_title_consumer")
            or row.get("late_translation_consumer")
            or "inventory parent"]
    )
    english = (
        row.get("static_english") or row.get("name")
        or row.get("shortname") or row.get("file")
    )
    chinese = _row_current_chinese(row)
    if row["category"] == "feature":
        mechanics = {
            "flags": row.get("flags"),
            "minimap": row.get("minimap"),
            "raw_producer": row.get("raw_producer"),
            "behavior_evidence_refs": row.get("behavior_evidence_refs"),
        }
    elif row["category"] == "branch":
        mechanics = {
            "mechanics": row.get("mechanics"),
            "raw_producer": row.get("raw_producer"),
        }
    elif row["category"] == "portal_family":
        mechanics = {
            "display_slot_count": row.get("display_slot_count"),
            "file": row.get("file"),
        }
    else:
        mechanics = {
            "sink_kind": row.get("sink_kind"),
            "tokens": row.get("tokens"),
            "dynamic_parameters": row.get("dynamic_parameters"),
            "translated_dynamic_parameters": row.get(
                "translated_dynamic_parameters"
            ),
        }
        if row.get("persistence_snapshot"):
            mechanics["persistence_snapshot"] = row["persistence_snapshot"]
    protocol = bool(
        row.get("protocol_identity") or row.get("lookup_identity")
        or row.get("protocol_deferral")
    )
    tokens = row.get("tokens") or {
        "format": "not applicable",
        "entity_macro": "not applicable",
        "markup": "not applicable",
        "structure": row["category"],
    }
    dependencies = (
        row.get("name_alias_group")
        or row.get("vaultname_alias_group")
        or [row.get("finite_title_producer") or row["category"]]
    )
    authority = {
        "glossary_sha256": payload.get("glossary_sha256", "not supplied"),
        "decisions_sha256": payload.get("input_sha256", {}).get(
            "docs/decisions.md", "not supplied"
        ),
    }
    target_scope = {
        "category": row["category"],
        "identity": row["identity"],
        "lifecycle": row["lifecycle"],
        "conditions": row.get("trigger") or row["lifecycle"],
        "exceptions": row.get("protocol_deferral") or "none",
        "consequences": row.get("channel") or row["category"],
    }
    facts = {
        "producer_consumer": _review_safe(
            f"{producer}; {', '.join(consumers)}"
        ),
        "trigger_context": _review_safe(
            f"{row.get('trigger', row['category'])}; "
            f"{row.get('channel', row['lifecycle'])}"
        ),
        "persistence_protocol": _review_safe(
            f"persistent={row.get('persistence', False)}; "
            f"protocol={protocol}"
        ),
        "en": _review_safe(english),
        "zh": _review_safe(chinese if chinese else "(missing)"),
        "mechanics_tokens": _review_safe(json.dumps(
            mechanics, ensure_ascii=False, sort_keys=True
        )),
        "lifecycle": _review_safe(row["lifecycle"]),
        "display_context": _review_safe(
            row.get("channel") or row.get("category")
        ),
        "producer": _review_safe(producer),
        "consumers_users": _review_safe(", ".join(consumers)),
        "mechanics_behavior": _review_safe(json.dumps(
            mechanics, ensure_ascii=False, sort_keys=True
        )),
        "target_scope_conditions_exceptions_consequences": _review_safe(
            json.dumps(target_scope, ensure_ascii=False, sort_keys=True)
        ),
        "trigger_timing": _review_safe(
            row.get("trigger") or "inventory parent lifecycle"
        ),
        "persistence_serialization": _review_safe(
            f"persistent={row.get('persistence', False)}; "
            f"serialization_protocol={protocol}"
        ),
        "late_translation_sink": _review_safe(
            row.get("late_translation_consumer") or "not applicable"
        ),
        "format_entity_markup_structure_tokens": _review_safe(json.dumps(
            tokens, ensure_ascii=False, sort_keys=True
        )),
        "glossary_decision_authority": _review_safe(json.dumps(
            authority, ensure_ascii=False, sort_keys=True
        )),
        "shared_dependency_group": _review_safe(json.dumps(
            dependencies, ensure_ascii=False, sort_keys=True
        )),
        "evidence_locations": _review_safe(json.dumps(
            evidence, ensure_ascii=False, sort_keys=True
        )),
    }
    return facts, (_review_safe(chinese) if chinese else None)


def terminal_conclusion_kind(value):
    stripped = value.strip()
    for kind, pattern in TERMINAL_CONCLUSION_PATTERNS:
        if pattern.match(stripped):
            return kind
    return None


def visible_terminal_summary_coverage(text, conclusion_counts):
    """Bind the visible terminal summary to the evidence-card conclusions."""
    heading_pattern = re.compile(
        rf"(?m)^##\s+{re.escape(VISIBLE_TERMINAL_SUMMARY_HEADING)}\s*$"
    )
    headings = list(heading_pattern.finditer(text))
    result = {
        "heading_count": len(headings),
        "summary_counts": {},
        "evidence_conclusion_counts": {
            kind: conclusion_counts.get(kind, 0)
            for kind in TERMINAL_CONCLUSION_KINDS
        },
        "duplicate_summary_categories": [],
        "missing_summary_categories": list(TERMINAL_CONCLUSION_KINDS),
        "unexpected_summary_categories": [],
        "malformed_summary_lines": [],
        "summary_total": None,
        "evidence_conclusion_total": sum(conclusion_counts.values()),
        "counts_match": False,
    }
    if len(headings) != 1:
        return result

    section_start = headings[0].end()
    next_heading = re.search(r"(?m)^##(?:\s|$)", text[section_start:])
    section_end = (
        section_start + next_heading.start()
        if next_heading else len(text)
    )
    section_lines = text[section_start:section_end].splitlines()
    while section_lines and not section_lines[0].strip():
        section_lines.pop(0)
    summary_lines = []
    for line in section_lines:
        if not line.strip():
            break
        summary_lines.append(line)

    line_pattern = re.compile(
        r"^- `([^`]+)`：(0|[1-9][0-9]*)$"
    )
    parsed = []
    malformed = []
    unexpected = []
    for line in summary_lines:
        match = line_pattern.fullmatch(line)
        if not match:
            malformed.append(line)
            continue
        category, count = match.groups()
        if category not in TERMINAL_CONCLUSION_KINDS:
            unexpected.append(category)
            continue
        parsed.append((category, int(count)))

    category_counts = Counter(category for category, _ in parsed)
    duplicates = sorted(
        category for category, count in category_counts.items()
        if count > 1
    )
    summary_counts = {
        category: count for category, count in parsed
        if category_counts[category] == 1
    }
    missing = [
        category for category in TERMINAL_CONCLUSION_KINDS
        if category not in summary_counts
    ]
    expected = result["evidence_conclusion_counts"]
    result.update({
        "summary_counts": summary_counts,
        "duplicate_summary_categories": duplicates,
        "missing_summary_categories": missing,
        "unexpected_summary_categories": sorted(unexpected),
        "malformed_summary_lines": malformed,
        "summary_total": (
            sum(summary_counts.values()) if not missing else None
        ),
        "counts_match": (
            len(summary_lines) == len(TERMINAL_CONCLUSION_KINDS)
            and not duplicates
            and not missing
            and not unexpected
            and not malformed
            and summary_counts == expected
            and sum(summary_counts.values()) == sum(expected.values())
        ),
    })
    return result


def _review_table_rows(text):
    """Parse one exact-column evidence table without interpreting decisions."""
    table_lines = [
        line for line in text.splitlines()
        if line.lstrip().startswith("|")
    ]
    header = []
    if table_lines:
        header = [
            cell.strip().lower()
            for cell in table_lines[0].strip().strip("|").split("|")
        ]
    rows = []
    if header == REVIEW_COLUMNS:
        for line in table_lines[2:]:
            cells = [
                cell.strip() for cell in line.strip().strip("|").split("|")
            ]
            if len(cells) == len(REVIEW_COLUMNS):
                card = dict(zip(REVIEW_COLUMNS, cells))
                rows.append((card["identity"].strip("`"), card))
    return header, rows


def review_structure_marker_counts(text):
    return {
        marker: text.count(marker)
        for marker in REVIEW_STRUCTURE_MARKERS
    }


def review_structure_markers_exact(text):
    return all(
        count == 1
        for count in review_structure_marker_counts(text).values()
    )


def review_decisions_from_text(text):
    marker_counts = review_structure_marker_counts(text)
    marker_shape = tuple(
        marker_counts[marker] for marker in REVIEW_STRUCTURE_MARKERS
    )
    if marker_shape == (0, 0, 0, 0):
        return {}
    if marker_shape not in (
            (0, 0, 1, 1),
            (1, 1, 1, 1)):
        raise ValueError(
            "world review structural markers are partial or duplicated"
        )
    managed_match = re.search(
        re.escape(REVIEW_EVIDENCE_BEGIN) + r"(.*?)"
        + re.escape(REVIEW_EVIDENCE_END),
        text,
        re.S,
    )
    review_text = managed_match.group(1) if managed_match else text
    _header, rows = _review_table_rows(review_text)
    return {
        identity: {
            **{
                field: card[field]
                for field in REVIEW_DECISION_FIELDS
            },
            "conclusion": card["conclusion"],
        }
        for identity, card in rows
    }


def _pending_world_decision():
    return {
        "proposed_translation": PENDING_REVIEW,
        "adopted_translation": PENDING_REVIEW,
        "rejected_alternatives": PENDING_REVIEW,
        "confidence": PENDING_REVIEW,
        "deferred_follow_up": PENDING_REVIEW,
        "re_entry_conditions": PENDING_REVIEW,
        "conclusion": "insufficient evidence",
    }


def review_artifact_summary(payload, decisions):
    conclusion_counts = Counter(
        kind for kind in (
            terminal_conclusion_kind(decision.get("conclusion", ""))
            for decision in decisions.values()
        )
        if kind is not None
    )
    violations = payload.get("violations", {})
    return {
        "category_counts": payload.get("category_counts", {}),
        "glossary_sha256": payload.get("glossary_sha256", "not supplied"),
        "inventory_sha256": payload["inventory_sha256"],
        "lifecycle_counts": payload.get("lifecycle_counts", {}),
        "terminal_conclusion_counts": {
            kind: conclusion_counts.get(kind, 0)
            for kind in TERMINAL_CONCLUSION_KINDS
        },
        "violations": violations,
        "violations_zero": not any(violations.values()),
    }


def world_history_lines():
    """Render the frozen superseded-boundary and membership evidence."""
    lines = [
        "## Inventory 审计历史与最终边界",
        "",
        *(f"- {entry}" for entry in WORLD_INVENTORY_HISTORY),
        "",
        "## Identity migration 机械证明",
        "",
        (
            "旧 516 个 DES identity 纠正为 496 个；old-only 20、new-only 0。"
            "其中 12 个是相邻 `initmsg` 片段合并／重编号，8 个是地图生成"
            "诊断输出。显示 wrapper 的独立前后集合均为 504，双向差集均为 0。"
        ),
        "",
        "### 12 个 initmsg old-only identity 与存活 identity",
        "",
        *(
            f"- `{old}` → `{survivor}`"
            for old, survivor in WORLD_INITMSG_OLD_ONLY
        ),
        "",
        "### 8 个诊断排除 identity",
        "",
        *(
            f"- `{identity}` — {reason}"
            for identity, reason in WORLD_DIAGNOSTIC_OLD_ONLY
        ),
        "",
        (
            "上述 20 项完整解释了 old-only 集合；new-only 为空。合并后的"
            "存活卡记录完整 English runtime key、当前中文、late sink、"
            "所有旧片段证据及被拒方案。"
        ),
        "",
        "## 761→788 readiness membership migration",
        "",
        (
            "成员迁移为 761→788，新增 27、移除 0。新增项严格限于生产代码"
            "实际消费的 Trove/Wizlab 有限标题；该历史阶段的 note/milestone "
            "持久化载荷仍保持 canonical English，后续笔记快照语义见下节。"
        ),
        "",
        *(
            f"- `{identity}` — `{english}` → `{chinese}`"
            for identity, english, chinese in WORLD_READINESS_ADDITIONS
        ),
        "",
        "## 788→789 本地化笔记身份迁移",
        "",
        (
            "Ashenzari 的单分支与双分支笔记使用两个不同的完整运行时模板，"
            "因此原有一个拼接式 identity 被两个可独立验证的模板 identity "
            "取代；old-only 0、new-only 1。其余 8 个 `crawl.take_note` "
            "identity 成员保持不变。9 个笔记 identity 均保存创建时语言的"
            "完整显示快照；模板或任一字符串参数缺键时整条回退英文，"
            "milestone 与其他协议值保持 canonical English。"
        ),
        "",
    ]
    return lines


def implementation_and_defer_history_lines(
    payload, decisions, allow_test_fixture_subset=False
):
    """Bind the visible retained-defer history to terminal evidence cards."""
    inventory_ids = {row["identity"] for row in payload["rows"]}
    expected_deferred = {
        identity
        for _heading, identities in WORLD_DEFER_GROUPS
        for identity in identities
    }
    missing_inventory_defer_ids = sorted(expected_deferred - inventory_ids)
    if missing_inventory_defer_ids and not allow_test_fixture_subset:
        raise ValueError(
            "world inventory is missing frozen defer-history identities: "
            + ", ".join(missing_inventory_defer_ids)
        )
    use_frozen_defer_history = not missing_inventory_defer_ids
    if use_frozen_defer_history:
        actual_deferred = {
            identity for identity, decision in decisions.items()
            if terminal_conclusion_kind(decision.get("conclusion", ""))
            in {"defer implementation", "defer terminology"}
        }
        if actual_deferred != expected_deferred:
            missing = sorted(expected_deferred - actual_deferred)
            unexpected = sorted(actual_deferred - expected_deferred)
            raise ValueError(
                "world defer history differs from terminal decisions: "
                f"missing={missing}, unexpected={unexpected}"
            )

    lines = [
        *(f"- {evidence}" for evidence in WORLD_IMPLEMENTATION_EVIDENCE),
        "",
        "## 仍保留的 defer（按权威边界分组）",
        "",
    ]
    if use_frozen_defer_history:
        for heading, identities in WORLD_DEFER_GROUPS:
            lines.extend([
                f"### {heading}（{len(identities)}）",
                "",
                *(f"- `{identity}`" for identity in identities),
                "",
            ])
    else:
        lines.extend([
            "该测试或迁移子集不覆盖冻结的 789-member defer 边界；"
            "完整生产 artifact 必须恢复全部分组。",
            "",
        ])
    return lines


def render_review_results(
    payload, decisions, allow_test_fixture_subset=False
):
    rows = sorted(payload["rows"], key=lambda row: row["identity"])
    canonical_decisions = {
        row["identity"]: decisions.get(
            row["identity"], _pending_world_decision()
        )
        for row in rows
    }
    summary = json.dumps(
        review_artifact_summary(payload, canonical_decisions),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    counts = Counter(
        kind for kind in (
            terminal_conclusion_kind(
                canonical_decisions[row["identity"]]["conclusion"]
            )
            for row in rows
        )
        if kind is not None
    )
    lines = [
        "# World translation review",
        "",
        REVIEW_ARTIFACT_BEGIN,
        summary,
        REVIEW_ARTIFACT_END,
        "",
        *world_history_lines(),
        f"## {VISIBLE_TERMINAL_SUMMARY_HEADING}",
        "",
        *(
            f"- `{kind}`：{counts.get(kind, 0)}"
            for kind in TERMINAL_CONCLUSION_KINDS
        ),
        "",
        *implementation_and_defer_history_lines(
            payload,
            canonical_decisions,
            allow_test_fixture_subset=allow_test_fixture_subset,
        ),
        REVIEW_EVIDENCE_BEGIN,
        f"Inventory-SHA256: {payload['inventory_sha256']}",
        "",
        "| " + " | ".join(REVIEW_COLUMNS) + " |",
        "|" + "|".join("---" for _ in REVIEW_COLUMNS) + "|",
    ]
    for row in rows:
        facts, _expected_adopted = review_expected_fact_cells(payload, row)
        decision = canonical_decisions[row["identity"]]
        card = {
            "identity": f"`{row['identity']}`",
            **facts,
            **decision,
        }
        lines.append("| " + " | ".join(
            card[column] for column in REVIEW_COLUMNS
        ) + " |")
    lines.extend([
        REVIEW_EVIDENCE_END,
        "",
    ])
    rendered = "\n".join(lines)
    if not review_structure_markers_exact(rendered):
        raise ValueError(
            "world review content contains a reserved structural marker"
        )
    return rendered


def _review_recorded_authority(cards):
    """Parse the ledger-recorded glossary/decisions digests from one row.

    The ``glossary_decision_authority`` cell records the review's input
    snapshot digests.  Every row in a canonical ledger records the same pair;
    return None when no row carries the cell (legacy or empty fixtures), and
    raise when recorded values are not canonical 64-hex strings.
    """
    for identity in sorted(cards):
        card = cards[identity]
        raw = card.get("glossary_decision_authority")
        if raw is None or raw in {"(none)", "", "-", "—"}:
            continue
        try:
            parsed = json.loads(raw)
        except (TypeError, json.JSONDecodeError):
            return None
        if not isinstance(parsed, dict):
            return None
        glossary = parsed.get("glossary_sha256")
        decisions = parsed.get("decisions_sha256")

        def _valid_digest(value):
            # ``not supplied`` is the fixture/placeholder spelling when the
            # current payload has no real digest for that slot; a real value
            # must be canonical 64-hex.
            if value is None or value == "not supplied":
                return True
            return isinstance(value, str) and bool(
                re.fullmatch(r"[0-9a-f]{64}", value)
            )

        if glossary is None and decisions is None:
            return None
        if not (_valid_digest(glossary) and _valid_digest(decisions)):
            raise RuntimeError(
                "world review glossary_decision_authority digest is malformed"
            )
        return {
            "glossary_sha256": (
                glossary if isinstance(glossary, str)
                and re.fullmatch(r"[0-9a-f]{64}", glossary) else None
            ),
            "decisions_sha256": (
                decisions if isinstance(decisions, str)
                and re.fullmatch(r"[0-9a-f]{64}", decisions) else None
            ),
        }
    return None


def _review_payload_with_authority(payload, recorded):
    """Return a payload copy whose authority digests are the recorded ones."""
    overlaid = {
        **payload,
        "glossary_sha256": (
            recorded["glossary_sha256"]
            if recorded["glossary_sha256"] is not None
            else payload.get("glossary_sha256")
        ),
    }
    input_sha256 = dict(payload.get("input_sha256", {}))
    if recorded["decisions_sha256"] is not None:
        input_sha256["docs/decisions.md"] = recorded["decisions_sha256"]
    overlaid["input_sha256"] = input_sha256
    return overlaid


def review_coverage(
    payload, review_input, allow_test_fixture_subset=False
):
    """Prove exactly one terminal conclusion per frozen inventory identity."""
    text = review_input.text
    marker_counts = review_structure_marker_counts(text)
    structure_markers_exact = all(
        count == 1 for count in marker_counts.values()
    )
    managed_match = re.search(
        re.escape(REVIEW_EVIDENCE_BEGIN) + r"(.*?)"
        + re.escape(REVIEW_EVIDENCE_END),
        text,
        re.S,
    )
    review_text = managed_match.group(1) if managed_match else text
    known = {row["identity"] for row in payload["rows"]}
    digest_match = re.search(
        r"(?mi)^\s*Inventory-SHA256:\s*`?([0-9a-f]{64})`?\s*$",
        review_text,
    )
    required_columns = REVIEW_COLUMNS
    header, parsed_rows = _review_table_rows(review_text)
    rows = []
    missing_fields = {}
    for identity, card in parsed_rows:
        if identity in known or identity.startswith(
                ("branch:", "feature:", "portal_family:", "des_display:")):
            rows.append((identity, card))
            empty = [
                field for field in required_columns[1:]
                if not card[field] or card[field] in {"-", "—"}
            ]
            if empty:
                missing_fields[identity] = empty
    identities = [identity for identity, _ in rows]
    actual = set(identities)
    cards = {identity: card for identity, card in rows}
    inventory_rows = {row["identity"]: row for row in payload["rows"]}

    # Slice A: the glossary/decisions digests inside each row's
    # ``glossary_decision_authority`` cell are provenance records from the
    # review's input snapshot.  Compare the ledger against those recorded
    # values (overlay), not against the current tree digests, so an unrelated
    # glossary or decisions.md edit cannot poison coverage.  The recorded
    # cells must still parse as canonical 64-hex JSON.
    original_payload = payload
    recorded_authority = _review_recorded_authority(cards)
    if recorded_authority is not None:
        payload = _review_payload_with_authority(payload, recorded_authority)
    current_glossary_digest = original_payload.get("glossary_sha256")
    current_decisions_digest = original_payload.get(
        "input_sha256", {}
    ).get("docs/decisions.md")
    recorded_glossary_digest = (
        recorded_authority["glossary_sha256"]
        if recorded_authority is not None else None
    )
    recorded_decisions_digest = (
        recorded_authority["decisions_sha256"]
        if recorded_authority is not None else None
    )
    if (
        recorded_glossary_digest is not None
        and current_glossary_digest is not None
        and recorded_glossary_digest != current_glossary_digest
    ):
        print(
            "notice: world review ledger records glossary_sha256 "
            f"{recorded_glossary_digest} != current "
            f"{current_glossary_digest}; verify whether a related "
            "terminology review is needed",
            file=sys.stderr,
        )
    if (
        recorded_decisions_digest is not None
        and current_decisions_digest is not None
        and recorded_decisions_digest != current_decisions_digest
    ):
        print(
            "notice: world review ledger records decisions_sha256 "
            f"{recorded_decisions_digest} != current "
            f"{current_decisions_digest}; verify whether a related "
            "decisions review is needed",
            file=sys.stderr,
        )

    fact_mismatches = {}
    adopted_translation_mismatches = {}
    composite_adoption_mismatches = {}
    for identity, card in cards.items():
        row = inventory_rows.get(identity)
        if row is None:
            continue
        expected_facts, expected_adopted = review_expected_fact_cells(
            payload, row
        )
        mismatched = sorted(
            field for field, expected in expected_facts.items()
            if card.get(field) != expected
        )
        if mismatched:
            fact_mismatches[identity] = mismatched
        if (expected_adopted is not None
                and card.get("adopted_translation") != expected_adopted):
            adopted_translation_mismatches[identity] = {
                "expected": expected_adopted,
                "actual": card.get("adopted_translation"),
            }
        expected_composite = review_expected_composite_adoption(row)
        if expected_composite is not None:
            actual_composite = _submitted_composite_adoption(
                row, card.get("proposed_translation")
            )
            if actual_composite != expected_composite:
                composite_adoption_mismatches[identity] = {
                    "decision_field": "proposed_translation",
                    "expected": expected_composite,
                    "actual": actual_composite,
                }
    conclusions = {
        identity: card["conclusion"] for identity, card in rows
    }
    invalid = sorted(
        identity for identity, conclusion in conclusions.items()
        if terminal_conclusion_kind(conclusion) is None
    )
    conclusion_counts = Counter(
        kind for kind in (
            terminal_conclusion_kind(card["conclusion"])
            for _, card in rows
        )
        if kind is not None
    )
    visible_summary = visible_terminal_summary_coverage(
        text, conclusion_counts
    )
    pending_pattern = re.compile(
        r"^(?:pending(?: review| evidence review)?|insufficient evidence|"
        r"not reviewed|tbd|unknown)$",
        re.I,
    )
    pending_required_fields = {
        identity: sorted(
            field for field in required_columns[1:]
            if pending_pattern.match(card[field].strip())
        )
        for identity, card in cards.items()
        if terminal_conclusion_kind(card["conclusion"]) is not None
        and any(
            pending_pattern.match(card[field].strip())
            for field in required_columns[1:]
        )
    }
    invalid_decision_fields = {
        identity: sorted(
            field for field in REVIEW_DECISION_FIELDS
            if pending_pattern.match(card[field].strip())
        )
        for identity, card in cards.items()
        if terminal_conclusion_kind(card["conclusion"]) is not None
        and any(
            pending_pattern.match(card[field].strip())
            for field in REVIEW_DECISION_FIELDS
        )
    }
    confidence_pattern = re.compile(
        r"^(?:high|medium|low|高|中|低)(?:$|[\s:：])", re.I
    )
    invalid_confidence = sorted(
        identity for identity, card in cards.items()
        if terminal_conclusion_kind(card["conclusion"]) is not None
        and not confidence_pattern.match(card["confidence"].strip())
    )
    decisions = {
        identity: {
            **{
                field: card[field]
                for field in REVIEW_DECISION_FIELDS
            },
            "conclusion": card["conclusion"],
        }
        for identity, card in rows
    }
    try:
        expected_artifact = render_review_results(
            payload,
            decisions,
            allow_test_fixture_subset=allow_test_fixture_subset,
        )
    except ValueError:
        expected_artifact = None
    artifact_exact = (
        structure_markers_exact
        and expected_artifact is not None
        and review_input.text == expected_artifact
    )
    return {
        **review_input_metadata(review_input),
        "review_results": review_input.logical_path,
        "review_results_sha256": review_input.sha256,
        "inventory_sha256_binding": (
            digest_match.group(1) if digest_match else None
        ),
        "inventory_digest_matches": bool(
            digest_match
            and digest_match.group(1) == payload["inventory_sha256"]
        ),
        "glossary_digest_matches": (
            recorded_glossary_digest == current_glossary_digest
            if recorded_glossary_digest is not None
            and current_glossary_digest is not None else True
        ),
        "decisions_digest_matches": (
            recorded_decisions_digest == current_decisions_digest
            if recorded_decisions_digest is not None
            and current_decisions_digest is not None else True
        ),
        "required_columns": required_columns,
        "header_matches": header == required_columns,
        "evidence_card_count": len(identities),
        "duplicate_evidence_cards": sorted(
            identity for identity, count in Counter(identities).items()
            if count > 1
        ),
        "missing_evidence_cards": sorted(known - actual),
        "unexpected_evidence_cards": sorted(actual - known),
        "invalid_terminal_conclusions": invalid,
        "missing_required_fields": missing_fields,
        "pending_required_fields": pending_required_fields,
        "invalid_decision_fields": invalid_decision_fields,
        "invalid_confidence": invalid_confidence,
        "visible_terminal_summary": visible_summary,
        "fact_mismatches": fact_mismatches,
        "adopted_translation_mismatches": (
            adopted_translation_mismatches
        ),
        "composite_adoption_mismatches": composite_adoption_mismatches,
        "structure_marker_counts": marker_counts,
        "structure_markers_exact": structure_markers_exact,
        "artifact_exact": artifact_exact,
        "coverage_equal": (
            len(identities) == len(known)
            and actual == known
            and not invalid
            and not missing_fields
            and not pending_required_fields
            and not invalid_decision_fields
            and not invalid_confidence
            and visible_summary["counts_match"]
            and not fact_mismatches
            and not adopted_translation_mismatches
            and not composite_adoption_mismatches
            and header == required_columns
            and bool(digest_match)
            and digest_match.group(1) == payload["inventory_sha256"]
            and structure_markers_exact
            and artifact_exact
        ),
    }


def complete_review_results(
    payload, path, allow_test_fixture_subset=False
):
    """Rewrite the complete artifact, preserving only reviewer decisions."""
    try:
        old = audit_snapshot().text(
            path, allow_external_unbound=True
        )
    except AuditInputError:
        if audit_snapshot().bound:
            raise
        old = ""
    decisions = review_decisions_from_text(old)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_review_results(
            payload,
            decisions,
            allow_test_fixture_subset=allow_test_fixture_subset,
        ),
        encoding="utf-8",
    )


@audit_snapshot_invocation(ROOT)
def build_inventory():
    snapshot = audit_snapshot()
    branches, branch_proof, en_branches, zh_branches = branch_rows()
    features, feature_proof, en_features, zh_features = feature_rows()
    (des, des_files, excluded_files, excluded_slots,
     producer_universe, unknown_producers) = des_rows()
    rows = branches + features + des
    inputs = [
        BRANCH_ENUM, BRANCH_DATA, BRANCH_CC, FEATURE_ENUM, FEATURE_DATA,
        EN_BRANCHES, ZH_BRANCHES, EN_FEATURES, ZH_FEATURES, GLOSSARY,
        SRC / "tag-version.h",
        SRC / "branch.h", SRC / "feature.h", SRC / "feature.cc",
        SRC / "directn.cc", SRC / "terrain.cc", SRC / "describe.cc",
        SRC / "lookup-help.cc", SRC / "stairs.cc", SRC / "database.cc",
        SRC / "dat/dlua/lm_tmsg.lua", SRC / "dat/dlua/lm_timed.lua",
        SRC / "dat/dlua/lm_pdesc.lua", SRC / "dat/dlua/lm_trove.lua",
        *TRUSTED_CONTROL_INPUTS,
        ROOT / "docs/decisions.md",
        *source_files(ZH_SOURCE_DIR), *des_files,
    ]
    input_hashes = {
        relative(path): input_sha256(path)
        for path in sorted(set(inputs), key=relative)
    }
    control_metadata = control_snapshot().metadata()
    expected_control_inputs = sorted(
        path.relative_to(SCRIPT_ROOT).as_posix()
        for path in TRUSTED_CONTROL_INPUTS
    )
    observed_control_inputs = [
        item["path"]
        for item in control_metadata["input_manifest"]["inputs"]
    ]
    if observed_control_inputs != expected_control_inputs:
        raise AuditInputError(
            "trusted-control input manifest is incomplete or unexpected: "
            f"{observed_control_inputs!r} != {expected_control_inputs!r}"
        )
    violations = inventory_violations(
        rows, branch_proof, feature_proof,
        (en_branches, zh_branches), (en_features, zh_features),
        unknown_producers,
    )
    category_counts = Counter(row["category"] for row in rows)
    lifecycle_counts = Counter(row["lifecycle"] for row in rows)
    payload = {
        "schema": "dcss-world-review-inventory-v1",
        "baseline": snapshot.audit_commit or resolve_commit("HEAD"),
        "tag_major_version": tag_major_version(),
        "glossary_sha256": sha(GLOSSARY),
        "input_sha256": input_hashes,
        "control_snapshot": control_metadata,
        "scope": {
            "included": [
                "active branch enum and branches[] display producers",
                "active feature enum and feat_defs[] display producers",
                "all sorted dat/des/portals/*.des families including zero-slot families",
                "single sorted production dat/des/**/*.des display-producer walk",
                "direct crawl display sinks, timed portal fields, trove toll_desc, "
                "portal desc and feature renames",
            ],
            "excluded": [
                "comments and dead/commented calls",
                "test files and directories",
                "diagnostic, error, assert, wizmode and dry_run output",
                "milestone and xlog protocol payloads",
                ".des NAME/TAGS/KFEAT/MARKER and feature/schema/lookup/"
                "comparison/serialization identity keys",
                "vaultname and branch abbrevname protocol identities",
            ],
            "excluded_files": excluded_files,
            "excluded_slots": excluded_slots,
            "non_owner_universe": [
                "dat/des/tutorial", "dat/des/sprint", "dat/des/altar"
            ],
            "producer_universe": producer_universe,
        },
        "proof": {"branches": branch_proof, "features": feature_proof},
        "category_counts": dict(sorted(category_counts.items())),
        "lifecycle_counts": dict(sorted(lifecycle_counts.items())),
        "rows": rows,
        "audit_snapshot": snapshot.metadata(),
        "violations": violations,
    }
    encoded = json.dumps(
        rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    payload["inventory_sha256"] = hashlib.sha256(encoded).hexdigest()
    return payload


def has_violations(payload):
    return any(payload["violations"].values())


@audit_snapshot_invocation(ROOT)
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
            review_input = load_review_input(
                ROOT,
                args.review_results,
                snapshot=audit_snapshot(),
            )
            payload["review_input"] = review_input_metadata(review_input)
            payload["review_coverage"] = review_coverage(
                payload, review_input
            )
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError,
            json.JSONDecodeError) as error:
        print(f"ERROR: world inventory could not be built: {error}",
              file=sys.stderr)
        return 2
    payload["audit_snapshot"] = audit_snapshot().metadata()
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    summary = {
        key: payload[key] for key in (
            "baseline", "glossary_sha256", "inventory_sha256",
            "category_counts", "lifecycle_counts",
        )
    }
    summary["violation_counts"] = {
        key: len(value) if hasattr(value, "__len__") else int(bool(value))
        for key, value in payload["violations"].items()
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stderr)
    coverage_failed = (
        "review_coverage" in payload
        and not payload["review_coverage"]["coverage_equal"]
    )
    return 1 if has_violations(payload) or coverage_failed else 0


if __name__ == "__main__":
    sys.exit(main())
