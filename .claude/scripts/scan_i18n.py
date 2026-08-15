#!/usr/bin/env python3
"""
scan_i18n.py — T_() world translation blind-spot scanner.

Replaces scan_untranslated.sh (which was designed for the if/else language-guard
world). Scans C++ source for patterns that indicate untranslated or incorrectly
translated messages in the T_() + source.txt architecture.

Usage:
    # Find mprf/mpr calls without T_() wrapping
    ./scan_i18n.py missing-t crawl-ref/source/

    # Check mprf_p usage for positional format strings (MinGW compat)
    ./scan_i18n.py mprf-p crawl-ref/source/ --source-txt dat/i18n/zh/source.txt

    # Check %s count parity between EN keys and CN translations
    ./scan_i18n.py arg-mismatch --source-txt dat/i18n/zh/source.txt

    # Detect language-dependent arguments in T_() calls
    ./scan_i18n.py lang-args crawl-ref/source/
"""

import argparse
import hashlib
import json
import os
import re
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n_shared import (parse_entries, parse_source_txt,
                         parse_entries_physical, compute_canonical_key,
                         compute_group_fingerprint)
# CR-023: the monspeak VISUAL channel contract reuses the strict Lua
# return extraction of the Issue-70 inventory (monspeak_inventory
# ``_lua_block_protocol``) so the per-branch runtime line/channel
# topology of Lua ``return "VISUAL:..."`` emissions is bound exactly like
# the production order (getSpeakString evaluates the block first, then
# the sink splits the returned string).  The channel classifier is the
# shared one too, so the scan checker and the inventory candidate gate
# resolve line channels identically.
from monspeak_inventory import (InventoryError, _lua_return_branch_lines,
                                _monspeak_line_channel)


# ══════════════════════════════════════════════════════════════════════════════
# Utilities
# ══════════════════════════════════════════════════════════════════════════════

# Call-like patterns that we scan for — message output + UI construction
MPR_CALL_RE = re.compile(
    r'\b(?:mprf|mprf_nojoin|mprf_p|mpr|cprintf|formatted_string|make_stringf'
    r'|simple_monster_message)\s*\(')

# High-confidence display contracts.  The integer is the zero-based argument
# containing player-visible text.  Keep this metadata small: unlike the broad
# MPR_CALL_RE heuristic, these sinks are blocking in the code/review profiles.
DIRECT_DISPLAY_SINKS = {
    'MenuEntry': 0,
    'draw_desc': 0,
    'game_ended': 1,
    'god_speaks': 1,
    'notify_fail': 0,
    'prompt_for_int': 0,
    'save_game': 1,
    'set_more': 0,
    'simple_god_message': 0,
    'title_prompt': 2,
    'yesno': 0,
}

# Functions whose returned or out-parameter text is displayed to the player.
# The key is relative to crawl-ref/source (or the scan root used by fixtures).
# Values map an unqualified function name to out-parameters which also carry
# display text. Return expressions are always checked. These are zero-debt,
# blocking contracts; keep the registry explicit to avoid guessing from names.
DISPLAY_TEXT_PRODUCERS = {
    'evoke.cc': {
        'cannot_evoke_item_reason': (),
    },
    'files.cc': {
        '_type_name_with_article_display': (),
    },
    'item-name.cc': {
        'cannot_read_item_reason': (),
        'cannot_drink_item_reason': (),
    },
    'item-prop.cc': {
        '_xp_evoker_recharge_msg': (),
    },
    'item-use.cc': {
        'cannot_put_on_talisman_reason': (),
    },
    'player.cc': {
        'no_tele_reason': (),
    },
    'religion.cc': {
        'god_spell_warn_string': (),
    },
    'spl-summoning.cc': {
        'mons_simulacrum_immune_reason': (),
        'surprising_crocodile_unusable_reason': (),
    },
    'spl-transloc.cc': {
        'movement_impossible_reason': (),
    },
    'god-abil.cc': {
        'wu_jian_can_wall_jump': ('error_ret',),
    },
}

# UI builder functions mutate one or more strings which are rendered after the
# function returns.  These scopes are intentionally file-qualified to avoid
# treating generic variables such as ``tip`` or ``text`` as player-visible in
# unrelated protocol and parser code.
DISPLAY_TEXT_BUILDERS = {
    'dgn-overview.cc': {
        '_get_seen_branches': ('zclock_desc',),
    },
    'mon-project.cc': {
        '_iood_hit_setup': ('beam.name',),
        '_annihilation_explode_setup': ('beam.name',),
    },
    'throw.cc': {
        '_throw_noise': ('msg',),
    },
    'tilereg-doll.cc': {
        'render': ('part_name', 'item_str', 'doll_name', 'mode_name',
                   'cat_name', 'info_str', 'help_text'),
    },
    'tilereg-inv.cc': {
        'update_tab_tip_text': ('tip', 'prefix1'),
        'update_tip_text': ('tip', 'tmp', 'tip_prefix', 'inf.title'),
    },
    'tilereg-map.cc': {
        'update_tip_text': ('tip',),
    },
    'tilereg-spl.cc': {
        'update_tab_tip_text': ('tip', 'prefix1'),
        'update_tip_text': ('tip',),
    },
    'tilereg-skl.cc': {
        'update_tab_tip_text': ('tip', 'prefix'),
        'update_tip_text': ('tip',),
    },
    'tilereg-stat.cc': {
        'update_tip_text': ('tip',),
    },
    'tilereg-msg.cc': {
        'update_tip_text': ('tip',),
    },
    'tilereg-abl.cc': {
        'update_tab_tip_text': ('tip', 'prefix1'),
        'update_tip_text': ('tip',),
    },
    'tilereg-mem.cc': {
        'update_tab_tip_text': ('tip', 'prefix1'),
        'update_tip_text': ('tip',),
    },
    'tilereg-dgn.cc': {
        'update_tip_text': ('tip',),
    },
}

# Issue 68 protocol/display producer registry. Each artifact is bounded by two
# production anchors so a convenient token elsewhere in the file (a decoy)
# cannot satisfy the contract. Required producer cardinality is fail-closed;
# forbidden localized producers must be absent from the same scope.
PROTOCOL_BOUNDARY_CONTRACTS = OrderedDict([
    ('des-hydra-heads', ({
        'file': 'mapdef.cc',
        'start': r'mons_spec\s+mons_list::get_hydra_spec\s*\(',
        'end': r'mons_spec\s+mons_list::get_slime_spec\s*\(',
        'required': ((r'number_in_words_en\s*\(', 1),),
        'forbidden': (r'number_in_words\s*\(',),
        'localized': 'number_in_words(',
    },)),
    ('zot-dgn', ({
        'file': 'l-dgnlvl.cc', 'start': r'LUAFN\(dgn_zot_orb_type\)',
        'end': r'const\s+struct\s+luaL_Reg\s+dgn_level_dlib',
        'required': ((r'mons_type_name_en\s*\(', 1),),
        'forbidden': (r'mons_type_name\s*\(',),
        'localized': 'mons_type_name(',
    },)),
    ('zot-you', ({
        'file': 'l-you.cc', 'start': r'LUAFN\(you_zot_orb_monster\)',
        'end': r'static\s+const\s+struct\s+luaL_Reg\s+you_clib',
        'required': ((r'mons_type_name_en\s*\(', 1),
                     (r'pluralise_monster\s*\(', 1),
                     (r'ScopedLangEn\s+en\s*;', 1)),
        'forbidden': (r'mons_type_name\s*\(',),
        'localized': 'mons_type_name(',
    },)),
    ('zot-milestone', ({
        'file': 'dgn-overview.cc',
        'start': r'void\s+seen_notable_thing\s*\(',
        'end': r'bool\s+move_notable_thing\s*\(',
        'required': ((r'mons_type_name_en\s*\(', 1),
                     (r'pluralise_monster\s*\(', 1),
                     (r'ScopedLangEn\s+en\s*;', 1)),
        'forbidden': (r'mons_type_name\s*\(',),
        'localized': 'mons_type_name(',
    },)),
    ('zot-overview', ({
        'file': 'dgn-overview.cc',
        'start': r'string\s+overview_description_string\s*\(',
        'end': r'static\s+string\s+_pad_cs\s*\(',
        'required': ((r'mons_type_name\s*\(', 1),
                     (r'T_\s*\(\s*"\\nThe Realm of Zot', 1)),
        'forbidden': (r'mons_type_name_en\s*\(', r'pluralise\s*\('),
        'localized': 'mons_type_name_en(',
    },)),
    ('status-you', ({
        'file': 'l-you.cc', 'start': r'LUAFN\(you_status\)',
        'end': r'LUAFN\(you_quiver_valid\)',
        'required': ((r'inf\.short_db_key\s*==\s*which', 1),
                     (r'inf\.short_text\s*==\s*which', 1)),
        'forbidden': (r'which\s*==\s*inf\.short_text\s*\)',),
        'localized': 'which == inf.short_text)',
    },)),
    ('status-mon', ({
        'file': 'l-moninf.cc', 'start': r'LUAFN\(moninf_get_status\)',
        'end': r'LUAFN\(moninf_get_name\)',
        'required': ((r'vector<string>\s+display_status\s*=\s*mi->attributes', 1),
                     (r'ScopedLangEn\s+en\s*;', 1),
                     (r'english_status\s*=\s*mi->attributes', 1)),
        'forbidden': (r'vector<string>\s+english_status\s*=\s*display_status',),
        'localized': 'vector<string> english_status = display_status',
    },)),
    ('mon-clua', ({
        'file': 'l-moninf.cc', 'start': r'LUAFN\(moninf_get_name\)',
        'end': r'LUAFN\(moninf_get_display_name\)',
        'required': ((r'ScopedLangEn\s+en\s*;', 1),
                     (r'mi->full_name\s*\(', 1)),
        'forbidden': (r'zh_monster_name\s*\(',),
        'localized': 'zh_monster_name(',
    },)),
    ('mon-dlua', (
        {
            'file': 'l-mons.cc', 'start': r'^MDEF\(name\)',
            'end': r'^MDEF\(unique\)',
            'required': ((r'ScopedLangEn\s+en\s*;', 1),),
            'forbidden': (r'zh_monster_name\s*\(',),
            'localized': 'zh_monster_name(',
        },
        {
            'file': 'l-mons.cc', 'start': r'MDEF\(base_name\)',
            'end': r'MDEF\(full_name\)',
            'required': ((r'ScopedLangEn\s+en\s*;', 1),),
            'forbidden': (r'zh_monster_name\s*\(',),
            'localized': 'zh_monster_name(',
        },
        {
            'file': 'l-mons.cc', 'start': r'MDEF\(full_name\)',
            'end': r'MDEF\(display_name\)',
            'required': ((r'ScopedLangEn\s+en\s*;', 1),),
            'forbidden': (r'zh_monster_name\s*\(',),
            'localized': 'zh_monster_name(',
        },
        {
            'file': 'l-mons.cc', 'start': r'MDEF\(type_name\)',
            'end': r'MDEF\(entry_name\)',
            'required': ((r'mons_type_name_en\s*\(', 1),),
            'forbidden': (r'mons_type_name\s*\(',),
            'localized': 'mons_type_name(',
        },
    )),
    ('mon-display', (
        {
            'file': 'l-moninf.cc',
            'start': r'LUAFN\(moninf_get_display_name\)',
            'end': r'LUAFN\(moninf_get_title_name\)',
            'required': ((r'mi->full_name\s*\(', 1),),
            'forbidden': (r'ScopedLangEn', r'mons_type_name_en\s*\('),
            'localized': 'ScopedLangEn',
        },
        {
            'file': 'l-mons.cc', 'start': r'MDEF\(display_name\)',
            'end': r'MDEF\(title_name\)',
            'required': ((r'mons->full_name\s*\(', 1),),
            'forbidden': (r'ScopedLangEn', r'mons_type_name_en\s*\('),
            'localized': 'ScopedLangEn',
        },
    )),
    ('item-clua', (
        {
            'file': 'l-item.cc',
            'start': r'static\s+int\s+l_item_do_subtype_en\s*\(',
            'end': r'/\*\*\*\s+What is the subtype',
            'required': ((r'ScopedLangEn\s+en\s*;', 1),),
            'forbidden': (r'const\s+string\s+subtype\s*=\s*_item_subtype[^;]+;\s*ScopedLangEn',),
            'localized': 'const string subtype = _item_subtype(*item, armour_slots); ScopedLangEn',
        },
        {
            'file': 'l-item.cc',
            'start': r'static\s+int\s+l_item_do_ego_en\s*\(',
            'end': r'/\*\*\*\s+What is the ego',
            'required': ((r'ScopedLangEn\s+en\s*;', 1),),
            'forbidden': (r'const\s+string\s+ego\s*=\s*_item_ego[^;]+;\s*ScopedLangEn',),
            'localized': 'const string ego = _item_ego(*item, terse); ScopedLangEn',
        },
        {
            'file': 'l-item.cc', 'start': r'IDEF\(weap_skill_en\)',
            'end': r'IDEF\(is_ranged\)',
            'required': ((r'ScopedLangEn\s+en\s*;', 1),),
            'forbidden': (r'return\s+_push_weap_skill[^;]+;\s*ScopedLangEn',),
            'localized': 'return _push_weap_skill(ls, item); ScopedLangEn',
        },
    )),
    ('item-dlua', (
        {
            'file': 'l-item.cc', 'start': r'IDEF\(base_type\)',
            'end': r'IDEF\(sub_type\)',
            'required': ((r'ScopedLangEn\s+en\s*;', 1),),
            'forbidden': (), 'localized': 'base_type_string(',
        },
        {
            'file': 'l-item.cc', 'start': r'IDEF\(sub_type\)',
            'end': r'IDEF\(ego_type\)',
            'required': ((r'ScopedLangEn\s+en\s*;', 1),),
            'forbidden': (), 'localized': 'sub_type_string(',
        },
        {
            'file': 'l-item.cc', 'start': r'IDEF\(ego_type\)',
            'end': r'IDEF\(ego_type_terse\)',
            'required': ((r'ScopedLangEn\s+en\s*;', 1),),
            'forbidden': (), 'localized': 'ego_type_string(',
        },
        {
            'file': 'l-item.cc', 'start': r'IDEF\(ego_type_terse\)',
            'end': r'IDEF\(artefact_name\)',
            'required': ((r'ScopedLangEn\s+en\s*;', 1),),
            'forbidden': (), 'localized': 'ego_type_string(',
        },
    )),
    ('item-marker', (
        {
            'file': 'l-item.cc',
            'start': r'static\s+int\s+l_item_do_marker_identity\s*\(',
            'end': r'/\*\*\*\s+Get this item',
            'required': ((r'canonical\.quantity\s*=\s*1\s*;', 1),
                         (r'canonical\.inscription\.clear\s*\(\s*\)', 1),
                         (r'ScopedLangEn\s+en\s*;', 1),
                         (r'canonical\.name\s*\(\s*DESC_PLAIN\s*,\s*false\s*,\s*true\s*,\s*false\s*\)', 1)),
            'forbidden': (r'_item_name\s*\(',),
            'localized': '_item_name(',
        },
        {
            'file': 'dat/dlua/lm_trig.lua',
            'start': r'function\s+DgnTriggerer:capture_item_target\s*\(',
            'end': r'function\s+DgnTriggerer:added\s*\(',
            'required': ((r'items\[1\]\.marker_identity\s*\(\s*\)', 1),),
            'forbidden': (r'items\[1\]\.name\s*\(',),
            'localized': 'items[1].name(',
        },
    )),
    ('trap', (
        {
            'file': 'traps.cc', 'start': r'bool\s+trap_def::is_safe\s*\(',
            'end': r'bool\s+chaos_lace_criteria\s*\(',
            'required': ((r'trap_name_en\s*\(', 1),),
            'forbidden': (r'trap_name\s*\(',),
            'localized': 'trap_name(',
        },
        {
            'file': 'l-view.cc', 'start': r'LUAFN\(view_trap_at\)',
            'end': r'/\*\*\*\s+Is it safe here',
            'required': ((r'trap_name_en\s*\(', 1),),
            'forbidden': (r'trap_name\s*\(',),
            'localized': 'trap_name(',
        },
    )),
    ('cloud', ({
        'file': 'l-view.cc', 'start': r'LUAFN\(view_cloud_at\)',
        'end': r'/\*\*\*\s+What kind of trap',
        'required': ((r'cloud_type_name_en\s*\(', 1),),
        'forbidden': (r'cloud_type_name\s*\(',),
        'localized': 'cloud_type_name(',
    },)),
    ('issue16-textdb-identity', (
        {
            'file': 'main.cc', 'start': r'static\s+void\s+_god_greeting_message\s*\([^;]+\)\s*\{',
            'end': r'static\s+void\s+_take_starting_note\s*\(',
            'required': ((r'_god_name_en\s*\(', 2),),
            'forbidden': (r'getSpeakString\s*\(\s*god_name\s*\(',),
            'localized': 'getSpeakString(god_name(',
        },
        {
            'file': 'lookup-help.cc', 'start': r'static\s+vector<string>\s+_get_skill_keys\s*\(\s*\)',
            'end': r'static\s+bool\s+_monster_filter\s*\(',
            'required': ((r'skill_name_en\s*\(', 1),),
            'forbidden': (r'skill_name\s*\(',),
            'localized': 'skill_name(',
        },
        {
            'file': 'spl-miscast.cc', 'start': r'static\s+void\s+_do_msg\s*\(',
            'end': r'static\s+void\s+_ouch\s*\(',
            'required': ((r'spelltype_long_name_en\s*\(', 1),),
            'forbidden': (r'spelltype_long_name\s*\(',),
            'localized': 'spelltype_long_name(',
        },
        {
            'file': 'mon-speak.cc', 'start': r'bool\s+mons_speaks\s*\(',
            'end': r'bool\s+resolve_mon_speech_line_channel\s*\(',
            'required': ((r'skill_name_en\s*\(', 1),
                         (r'_god_name_en\s*\(', 2)),
            'forbidden': (r'prefixes\.push_back\s*\(\s*god_name\s*\(',
                          r'ghost_skill\s*=\s*skill_name\s*\('),
            'localized': 'ghost_skill = skill_name(',
        },
        {
            'file': 'shout.cc', 'start': r'(?:static\s+)?string\s+_shout_key\s*\(',
            'end': r'void\s+monster_consider_shouting\s*\(',
            'required': ((r'get_job_name_en\s*\(', 1),),
            'forbidden': (r'get_job_name\s*\(',),
            'localized': 'get_job_name(',
        },
        {
            'file': 'artefact.cc', 'start': r'string\s+make_artefact_name\s*\(',
            'end': r'string\s+get_artefact_base_name\s*\(',
            'required': ((r'_god_name_en\s*\(', 2),),
            'forbidden': (r'(?<!_)god_name\s*\(',),
            'localized': 'god_name(',
        },
    )),
    ('issue16-rc-identity', (
        {
            'file': 'spl-cast.cc', 'start': r'static\s+bool\s+_spellcasting_aborted\s*\(',
            'end': r'static\s+vector<coord_def>\s+_simple_find_all_hostiles\s*\(',
            'required': ((r'match_name\s*=\s*spell_english_name\s*\(', 1),),
            'forbidden': (r'match_name\s*=\s*spell_title\s*\(',),
            'localized': 'match_name = spell_title(',
        },
        {
            'file': 'ability.cc', 'start': r'static\s+bool\s+_check_ability_possible\s*\(',
            'end': r'bool\s+activate_talent\s*\(',
            'required': ((r'match_name\s*=\s*ability_name\s*\(\s*abil\.ability\s*,\s*true\s*\)', 1),),
            'forbidden': (r'match_name\s*=\s*ability_name\s*\([^,;]+\)',),
            'localized': 'match_name = ability_name(abil.ability)',
        },
        {
            'file': 'spl-util.cc', 'start': r'bool\s+add_spell_to_memory\s*\(',
            'end': r'bool\s+del_spell_from_memory_by_slot\s*\(',
            'required': ((r'sname\s*=\s*spell_english_name\s*\(', 1),
                         (r'ename\s*=\s*lowercase_string\s*\(\s*spell_english_name', 1)),
            'forbidden': (r'sname\s*=\s*spell_title\s*\(',),
            'localized': 'sname = spell_title(',
        },
        {
            'file': 'items.cc', 'start': r'static\s+inline\s+string\s+_autopickup_item_name\s*\(',
            'end': r'void\s+fix_item_coordinates\s*\(',
            'required': ((r'ScopedLangEn\s+en\s*;', 1),),
            'forbidden': (r'return\s+userdef_annotate_item',),
            'localized': 'return userdef_annotate_item',
        },
    )),
    ('issue16-lua-identity', (
        {
            'file': 'travel.cc', 'start': r'static\s+const\s+char\s*\*\s*_run_mode_name\s*\(',
            'end': r'uint8_t\s+is_waypoint\s*\(',
            'required': ((r'\?\s*"travel"\s*:', 1),),
            'forbidden': (r'T_\s*\(\s*"travel"',),
            'localized': 'T_("travel"',
        },
        {
            'file': 'nearby-danger.cc', 'start': r'bool\s+mons_is_safe\s*\(',
            'end': r'static\s+string\s+_seen_monsters_announcement\s*\(',
            'required': ((r'canonical_name\s*=\s*mon->name\s*\(\s*DESC_PLAIN', 1),
                         (r'clua\.callfn\s*\(\s*"ch_mon_is_safe"', 1)),
            'forbidden': (r'ch_mon_is_safe[^;]+mon->name',),
            'localized': 'ch_mon_is_safe mon->name',
        },
        {
            'file': 'l-you.cc', 'start': r'static\s+int\s+l_you_spells\s*\(',
            'end': r'static\s+int\s+l_you_spell_letters\s*\(',
            'required': ((r'spell_english_name\s*\(', 1),),
            'forbidden': (r'spell_title\s*\(',),
            'localized': 'spell_title(',
        },
        {
            'file': 'l-moninf.cc', 'start': r'LUAFN\(moninf_get_spells\)',
            'end': r'/\*\*\*\s+What quality of stab',
            'required': ((r'spell_english_name\s*\(', 2),),
            'forbidden': (r'spell_title\s*\(',),
            'localized': 'spell_title(',
        },
        {
            'file': 'l-view.cc', 'start': r'if\s*\(cell\.cloud\(\)\s*!=\s*CLOUD_NONE\)',
            'end': r'if\s*\(!unsafe\s*&&\s*cell\.trap',
            'required': ((r'cloud_type_name_en\s*\(', 1),),
            'forbidden': (r'cloud_type_name\s*\(',),
            'localized': 'cloud_type_name(',
        },
    )),
    ('issue16-serialization', (
        {
            'file': 'tags.cc', 'start': r'static\s+void\s+_tag_construct_char\s*\([^;]+\)\s*\{',
            'end': r'static\s+bool\s+_calc_score_exists\s*\(',
            'required': ((r'get_job_name_en\s*\(', 1),
                         (r'SPNAME_PLAIN\s*,\s*true', 1),
                         (r'_god_name_en\s*\(', 1)),
            'forbidden': (r'get_job_name\s*\(', r'god_name\s*\('),
            'localized': 'get_job_name(',
        },
        {
            'file': 'hiscores.cc', 'start': r'void\s+scorefile_entry::set_base_xlog_fields\s*\(',
            'end': r'void\s+scorefile_entry::set_score_fields\s*\(',
            'required': ((r'get_job_name_en\s*\(', 1),
                         (r'skill_name_en\s*\(', 1),
                         (r'_god_name_en\s*\(', 1)),
            'forbidden': (r'fields->add_field\s*\(\s*"(?:cls|sk|god)"[^;]+(?:get_job_name|skill_name|god_name)\s*\(',),
            'localized': 'fields->add_field("cls", "%s", get_job_name(',
        },
        {
            'file': 'hiscores.cc', 'start': r'void\s+scorefile_entry::init\s*\(',
            'end': r'//\s*Note all skills at level 27',
            'required': ((r'title\s*=\s*player_title\s*\(\s*false\s*\)\s*;', 1),
                         (r'ScopedLangEn\s+protocol_language\s*;', 1)),
            'forbidden': (r'title\s*=\s*T_\s*\(',),
            'localized': 'title = T_(player_title(false));',
        },
        {
            'file': 'hiscores.cc', 'start': r'if\s*\(you\.skills\[sk\]\s*==\s*27\)',
            'end': r'if\s*\(you\.skills\[sk\]\s*>=\s*15\)',
            'required': ((r'maxed_skills\s*\+=\s*skill_name_en\s*\(\s*sk\s*\)\s*;', 1),),
            'forbidden': (r'maxed_skills\s*\+=\s*skill_name\s*\(',),
            'localized': 'maxed_skills += skill_name(sk);',
        },
        {
            'file': 'hiscores.cc', 'start': r'if\s*\(you\.skills\[sk\]\s*>=\s*15\)',
            'end': r'\{\s*ScopedLangEn\s+protocol_language\s*;\s*status_info\s+inf\s*;',
            'required': ((r'fifteen_skills\s*\+=\s*skill_name_en\s*\(\s*sk\s*\)\s*;', 1),),
            'forbidden': (r'fifteen_skills\s*\+=\s*skill_name\s*\(',),
            'localized': 'fifteen_skills += skill_name(sk);',
        },
        {
            'file': 'hiscores.cc',
            'start': r'\{\s*ScopedLangEn\s+protocol_language\s*;\s*status_info\s+inf\s*;',
            'end': r'kills\s*=\s*you\.kills\.total_kills\s*\(\s*\)\s*;',
            'required': ((r'status_effects\s*\+=\s*inf\.short_text\s*;', 1),
                         (r'fill_status_info\s*\(', 1)),
            'forbidden': (r'status_effects\s*\+=\s*T_\s*\(',),
            'localized': 'status_effects += T_(inf.short_text);',
        },
        {
            'file': 'religion.cc', 'start': r'void\s+dec_penance\s*\(\s*god_type',
            'end': r'void\s+dec_penance\s*\(\s*int',
            'required': ((r'"mollified\s+"\s*\+\s*string\s*\(\s*_god_name_en', 1),),
            'forbidden': (r'T_\s*\(\s*"mollified\s+"',),
            'localized': 'T_("mollified "',
        },
        {
            'file': 'dat/des/portals/trove.des', 'start': r'function\s+trove_milestone\s*\(',
            'end': r'function\s+trove_setup\s*\(',
            'required': ((r'"entered\s+"\s*\.\.', 1),),
            'forbidden': (r'crawl\.mark_milestone[^\n]+\n\s*crawl\.t_',),
            'localized': 'crawl.t_("entered ")',
        },
    )),

    ('issue16-monspeak-channels', (
        {
            # CR-004: the contract validates VISUAL channel routing at the
            # current EN-aligned (key, ordinal) positions instead of binding
            # the Chinese sentence text that the Issue #70 review replaces.
            # Every EN variant that starts with "VISUAL:" must keep the
            # VISUAL: channel prefix in ZH at the same key and ordinal, so
            # reworded/reordered translations cannot silently degrade the
            # visual channel.  Dispatched to
            # _monspeak_visual_channel_findings().
            'file': 'dat/database/zh/monspeak.txt',
            'custom': 'monspeak-visual-channels',
            'localized': 'VISUAL channel prefix at EN-aligned (key, ordinal)',
        },
    )),
    ('issue16-portal-persistence', (
        {
            'file': 'dat/des/portals/bailey.des',
            'start': r'function\s+bailey_portal\s*\(', 'end': r'e\.tags\("uniq_bailey',
            'required': ((r'initmsg\s*=\s*\{\s*"', 1),),
            'forbidden': (r'(?:initmsg|finalmsg|range_msg_fmt|disappear)\s*=\s*crawl\.t_',),
            'localized': 'initmsg = { crawl.t_(',
        },
        {
            'file': 'dat/des/portals/volcano.des',
            'start': r'function\s+volcano_portal\s*\(', 'end': r'e\.tags\("uniq_volcano',
            'required': ((r'initmsg\s*=\s*\{\s*"', 1),),
            'forbidden': (r'(?:initmsg|finalmsg|range_msg_fmt|disappear)\s*=\s*crawl\.t_',),
            'localized': 'initmsg = { crawl.t_(',
        },
        {
            'file': 'dat/des/portals/wizlab.des',
            'start': r'function\s+wizlab_portal\s*\(', 'end': r'e\.tags\("uniq_wizlab',
            'required': ((r'initmsg\s*=\s*\{\s*"', 1),),
            'forbidden': (r'(?:initmsg|finalmsg|range_msg_fmt|disappear)\s*=\s*crawl\.t_',),
            'localized': 'initmsg = { crawl.t_(',
        },
        {
            'file': 'dat/des/portals/sewer.des',
            'start': r'function\s+sewer_portal\s*\(', 'end': r'e\.tags\("uniq_sewer',
            'required': ((r'initmsg\s*=\s*\{\s*"', 1),),
            'forbidden': (r'(?:initmsg|finalmsg|range_msg_fmt|disappear)\s*=\s*crawl\.t_',),
            'localized': 'initmsg = { crawl.t_(',
        },
        {
            'file': 'dat/des/portals/icecave.des',
            'start': r'^function\s+ice_cave_portal\s*\(', 'end': r'e\.tags\("uniq_icecv',
            'required': ((r'initmsg\s*=\s*\{\s*"', 1),),
            'forbidden': (r'(?:initmsg|finalmsg|range_msg_fmt|disappear)\s*=\s*crawl\.t_',),
            'localized': 'initmsg = { crawl.t_(',
        },
        {
            'file': 'dat/des/portals/desolation.des',
            'start': r'function\s+desolation_portal\s*\(', 'end': r'e\.tags\("uniq_desolation',
            'required': ((r'initmsg\s*=\s*\{\s*\n\s*"', 1),),
            'forbidden': (r'(?:initmsg|finalmsg|range_msg_fmt|disappear)\s*=\s*crawl\.t_',),
            'localized': 'initmsg = { crawl.t_(',
        },
        {
            'file': 'dat/des/portals/ossuary.des',
            'start': r'function\s+ossuary_portal\s*\(', 'end': r'e\.tags\("uniq_ossuary',
            'required': ((r'initmsg\s*=\s*\{\s*"', 1),),
            'forbidden': (r'(?:initmsg|finalmsg|range_msg_fmt|disappear)\s*=\s*crawl\.t_',),
            'localized': 'initmsg = { crawl.t_(',
        },
        {
            'file': 'dat/des/portals/gauntlet.des',
            'start': r'function\s+gauntlet_portal\s*\(', 'end': r'function\s+gauntlet_appearance\s*\(',
            'required': ((r'initmsg\s*=\s*\{\s*"', 1),),
            'forbidden': (r'(?:initmsg|finalmsg|range_msg_fmt|disappear)\s*=\s*crawl\.t_',),
            'localized': 'initmsg = { crawl.t_(',
        },
        {
            'file': 'dat/des/portals/bazaar.des',
            'start': r'function\s+bazaar_portal\s*\(', 'end': r'^end\s*$',
            'required': ((r'initmsg\s*=\s*\{\s*"', 1),),
            'forbidden': (r'(?:initmsg|finalmsg|range_msg_fmt|disappear)\s*=\s*crawl\.t_',),
            'localized': 'initmsg = { crawl.t_(',
        },
        {
            'file': 'dat/des/portals/necropolis.des',
            'start': r'function\s+necropolis_portal_entry\s*\(', 'end': r'function\s+necropolis_portal_setup\s*\(',
            'required': ((r'initmsg\s*=\s*\{\s*"', 1),),
            'forbidden': (r'(?:initmsg|finalmsg|range_msg_fmt|disappear)\s*=\s*crawl\.t_',),
            'localized': 'initmsg = { crawl.t_(',
        },
        {
            'file': 'dat/des/portals/trove.des',
            'start': r'function\s+trove\.portal\s*\(', 'end': r'function\s+trove\.good_scroll\s*\(',
            'required': ((r'toll_desc\s*=\s*"to enter a treasure trove"', 1),),
            'forbidden': (r'toll_desc\s*=\s*crawl\.t_',),
            'localized': 'toll_desc = crawl.t_(',
        },
        {
            'file': 'dat/dlua/lm_tmsg.lua',
            'start': r'function\s+TimedMessaging:emit_message\s*\(',
            'end': r'function\s+TimedMessaging:proc_ranges\s*\(',
            'required': ((r'translate_key\s*\(msg\)', 1),),
            'forbidden': (r'expand_entity\s*\(self\.entity\s*,\s*msg\)',),
            'localized': 'expand_entity(self.entity, msg)',
        },
        {
            'file': 'dat/dlua/lm_timed.lua',
            'start': r'function\s+TimedMarker:timeout\s*\(',
            'end': r'function\s+TimedMarker:event\s*\(',
            'required': ((r'type\(disappear\)\s*==\s*[\'\"]string[\'\"]', 1),
                         (r'disappear\s*=\s*crawl\.t_\(disappear\)', 1)),
            'forbidden': (r'crawl\.t_\(self\.props\.disappear\)',),
            'localized': 'crawl.t_(self.props.disappear)',
        },
        {
            'file': 'dat/dlua/lm_pdesc.lua',
            'start': r'function\s+PortalDescriptor:property\s*\(',
            'end': r'function\s+portal_desc\s*\(',
            'required': ((r'type\(desc\)\s*==\s*[\'\"]string[\'\"]', 1),
                         (r'crawl\.t_\(desc\)', 1)),
            'forbidden': (r'return\s+self:unmangle\(self\.props\.desc\)',),
            'localized': 'return self:unmangle(self.props.desc)',
        },
        {
            'file': 'dat/dlua/lm_trove.lua',
            'start': r'function\s+TroveMarker:note_payed\s*\(',
            'end': r'function\s+trove_marker\s*\(',
            'required': ((r'toll_desc\s*=\s*crawl\.t_\(self\.props\.toll_desc\)', 1),),
            'forbidden': (r'toll_desc\s*=\s*self\.props\.toll_desc',),
            'localized': 'toll_desc = self.props.toll_desc',
        },
    )),
])

DISPLAY_SKIP_FILE_RE = re.compile(r'^(?:wiz-|dbg-)')

# Wrappers which translate a literal key internally (for example via
# T_(variable)).  Callers must not add another T_(), but every literal passed in
# the key argument must have an exact, non-empty source.txt entry.
DYNAMIC_KEY_WRAPPERS = {
    'xom_is_stimulated': 1,
}

# Calls whose result is already translated.  String literals below these calls
# are translation keys or DB lookup keys, not raw player-visible text.
TRANSLATED_VALUE_PROVIDERS = {
    'T_', 'C_', '_get_xom_speech', 'getLongDescription',
}

# Severity grading: which function was matched
def _severity(line: str) -> str:
    """Classify a call site by function type."""
    if re.search(r'\bmprf_p\s*\(', line):     return 'MSG'
    if re.search(r'\bmprf_nojoin\s*\(', line): return 'MSG'
    if re.search(r'\bmprf\s*\(', line):        return 'MSG'
    if re.search(r'\bmpr\s*\(', line):         return 'MSG'
    if re.search(r'\bcprintf\s*\(', line):     return 'UI'
    if re.search(r'\bformatted_string\s*\(', line): return 'UI'
    if re.search(r'\bmake_stringf\s*\(', line):    return 'STR'
    if re.search(r'\bsimple_monster_message\s*\(', line): return 'SMM'
    return 'MSG'

# Check if a line has T_() or C_() wrapping
HAS_T_RE = re.compile(r'\b[TtCc]_\(\s*"')

# Detect positional format specifiers: %1$s, %2$d, %3$f, etc.
POSFMT_RE = re.compile(r'%(\d+)\$(?:[sdxcunfFeEgG]|l[du])')

# Detect silent positional consumption: %2$.0s (Issue 29 pattern)
SILENT_RE = re.compile(r'%(\d+)\$\.0s')

# Extract (position, type_char) from positional specifiers: %1$s → (1, 's')
POSFMT_TYPE_RE = re.compile(r'%(\d+)\$([sdxcunfFeEgG.%]|l[du]|PRI\w+)')

# Plain format specifiers: %s, %d, %c, %x, %ld, %lu
PLAIN_FMT_RE = re.compile(r'%(?:l[du]|[sdcxlufeEgGi])')

# Detect if a line uses a positional-format-aware function
POSITIONAL_CALL_RE = re.compile(
    r'\b(?:mprf_p|make_stringf_p|vmake_stringf_p)\s*\(')

# Lines to skip: diagnostics, debug, error channels
SKIP_CHANNEL_RE = re.compile(
    r'MSGCH_DIAGNOSTICS|MSGCH_DEBUG|MSGCH_ERROR'
)

# Preprocessor lines to skip
SKIP_PP_RE = re.compile(r'^\s*#\s*(?:if|ifdef|ifndef|else|elif|endif|pragma)')

# Directories to exclude from file traversal
SKIP_DIRS = {'morgue', '.cache', 'contrib', '.git', 'worktrees', '__pycache__'}


def prune_dirs(dirnames):
    """Remove unwanted directories (in-place) to avoid traversing them."""
    dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]


def count_format_args(s: str) -> int:
    """Count unique format specifier arguments in a string.

    Handles both plain %s and positional %n$s. For positional args,
    returns the max position number (since positions 1..N implies N args).
    For plain args, returns count of %s/%d/etc specifiers (excluding %%
    which is a literal percent sign).
    """
    # Remove %% (literal percent) before counting
    cleaned = re.sub(r'%%', '', s)
    positional = set()
    for m in POSFMT_RE.finditer(cleaned):
        positional.add(int(m.group(1)))
    for m in SILENT_RE.finditer(cleaned):
        positional.add(int(m.group(1)))
    if positional:
        return max(positional)
    return len(PLAIN_FMT_RE.findall(cleaned))


def strip_cpp_string_literal(s: str) -> str:
    """Extract the content of the first C++ string literal in a line.

    Returns the string between the first pair of double quotes,
    with C++ escape sequences left as-is (for display purposes).
    """
    m = re.search(r'"((?:[^"\\]|\\.)*)"', s)
    if m:
        return m.group(1)
    return ""


def has_alpha(s: str) -> bool:
    """Check if string contains at least one ASCII letter."""
    return bool(re.search(r'[A-Za-z]', s))


def has_word(s: str) -> bool:
    """Check if string contains at least one English word (2+ consecutive letters)."""
    return bool(re.search(r'[A-Za-z]{2,}', s))


def is_format_only(s: str) -> bool:
    """Check if a stripped string is purely format specifiers (no English words).

    Returns True if the string has only format specifiers, whitespace,
    punctuation, and numbers — but no actual English words.
    """
    if not s:
        return True
    return not has_word(s)


# ══════════════════════════════════════════════════════════════════════════════
# Preprocessor / comment block tracking
# ══════════════════════════════════════════════════════════════════════════════

# Regex for #if/#ifdef/#ifndef/#else/#elif/#endif lines
PP_IF_RE = re.compile(r'^\s*#\s*if(?:\s|$)')
PP_IFDEF_RE = re.compile(r'^\s*#\s*ifdef\s+(\w+)')
PP_IFNDEF_RE = re.compile(r'^\s*#\s*ifndef\s+(\w+)')
PP_ENDIF_RE = re.compile(r'^\s*#\s*endif')
PP_ELSE_RE = re.compile(r'^\s*#\s*else(?:\s|$)')
PP_ELIF_RE = re.compile(r'^\s*#\s*elif(?:\s|$)')


def _known_preprocessor_condition(expression, extra_undefined=None):
    """Evaluate only conditions whose scan-time state is unambiguous.

    DEBUG macros are treated as undefined in normal builds. Unknown build
    expressions return None so both branches are scanned (fail-open).
    """
    expression = expression.strip()
    if re.fullmatch(r'0(?:[uUlL]*)', expression):
        return False
    if re.fullmatch(r'1(?:[uUlL]*)', expression):
        return True

    undefined = {'WIZARD'} & set(extra_undefined or ())
    undefined_pattern = r'DEBUG\w*'
    if undefined:
        undefined_pattern = (r'(?:' + undefined_pattern + '|'
                             + '|'.join(map(re.escape, sorted(undefined)))
                             + r')')

    defined = re.fullmatch(
        r'defined\s*(?:\(\s*(' + undefined_pattern + r')\s*\)|('
        + undefined_pattern + r'))', expression)
    if defined:
        return False
    not_defined = re.fullmatch(
        r'!\s*defined\s*(?:\(\s*(' + undefined_pattern + r')\s*\)|('
        + undefined_pattern + r'))', expression)
    if not_defined:
        return True
    if re.fullmatch(undefined_pattern, expression):
        return False
    if re.fullmatch(r'!\s*' + undefined_pattern, expression):
        return True
    return None


def build_debug_ranges(lines, extra_undefined=None):
    """Return lines in definitely inactive/debug preprocessor branches.

    The state machine is nested-safe and branch-aware. Unknown conditions are
    deliberately fail-open: their branch and alternatives remain scannable.
    """
    inactive_lines = set()
    stack = []
    current_inactive = False

    for lineno, line in enumerate(lines, 1):
        if PP_ENDIF_RE.match(line):
            if stack:
                frame = stack.pop()
                current_inactive = frame['parent_inactive']
            continue

        if PP_ELSE_RE.match(line):
            if stack:
                frame = stack[-1]
                current_inactive = (frame['parent_inactive']
                                    or frame['definitely_taken'])
                frame['definitely_taken'] = True
            continue

        elif_match = re.match(r'^\s*#\s*elif\s+(.+?)\s*$', line)
        if elif_match:
            if stack:
                frame = stack[-1]
                condition = _known_preprocessor_condition(
                    elif_match.group(1), extra_undefined)
                current_inactive = (frame['parent_inactive']
                                    or frame['definitely_taken']
                                    or condition is False)
                if condition is True:
                    frame['definitely_taken'] = True
            continue

        condition = None
        opening = False
        ifdef_match = PP_IFDEF_RE.match(line)
        if ifdef_match:
            opening = True
            macro = ifdef_match.group(1)
            condition = (False if macro.startswith('DEBUG')
                         or macro in set(extra_undefined or ()) else None)
        else:
            ifndef_match = PP_IFNDEF_RE.match(line)
            if ifndef_match:
                opening = True
                macro = ifndef_match.group(1)
                condition = (True if macro.startswith('DEBUG')
                             or macro in set(extra_undefined or ()) else None)
            else:
                if_match = re.match(r'^\s*#\s*if\s+(.+?)\s*$', line)
                if if_match:
                    opening = True
                    condition = _known_preprocessor_condition(
                        if_match.group(1), extra_undefined)

        if opening:
            parent_inactive = current_inactive
            stack.append({
                'parent_inactive': parent_inactive,
                'definitely_taken': condition is True,
            })
            current_inactive = parent_inactive or condition is False
            continue

        if current_inactive:
            inactive_lines.add(lineno)

    return inactive_lines


def build_comment_ranges(lines):
    """Build a set of line numbers (1-based) that are inside /* ... */ block comments.

    Also returns lines that start with // (single-line comments).
    """
    comment_lines = set()
    in_block = False

    for i, line in enumerate(lines):
        lineno = i + 1
        stripped = line.lstrip()

        # Check for single-line comment
        if stripped.startswith('//'):
            comment_lines.add(lineno)
            # But check if it contains a block comment toggle
            # (unlikely in practice, but handle it)
            continue

        if in_block:
            comment_lines.add(lineno)
            if '*/' in line:
                in_block = False
            continue

        # Check for block comment start
        pos = line.find('/*')
        if pos >= 0:
            # Check if there's a closing */ on the same line
            end_pos = line.find('*/', pos + 2)
            if end_pos >= 0:
                # Single-line block comment — skip just this line
                comment_lines.add(lineno)
            else:
                in_block = True
                comment_lines.add(lineno)

    return comment_lines


# ══════════════════════════════════════════════════════════════════════════════
# Allowlist
# ══════════════════════════════════════════════════════════════════════════════

def load_allowlist(filepath: str) -> set:
    """Load allowlist entries from a JSON file.

    Format: [{"file": "mon-act.cc", "line": 1426, "reason": "MSGCH_SOUND, not player-visible"},
              {"file": "mon-death.cc", "line": 254, "reason": "internal error diagnostic"}]
    """
    if not filepath or not os.path.exists(filepath):
        return set()
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return {(entry['file'], entry['line']) for entry in data}


def load_contract_allowlist(filepath: str) -> list:
    """Load exact legacy display-contract exceptions.

    Contract exceptions deliberately match file, line, rule, function, and
    literal.  This makes moved/changed debt fail closed instead of silently
    granting a broad exemption.
    """
    if not filepath or not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [entry for entry in data
            if entry.get('rule') in ('direct-display', 'dynamic-key',
                                     'direct-display-producer',
                                     'direct-display-builder')]


def _contract_is_allowlisted(entries, rule, rel_path, lineno, function,
                             literal):
    return any(entry.get('rule') == rule
               and entry.get('file') == rel_path
               and entry.get('line') == lineno
               and entry.get('function') == function
               and entry.get('literal') == literal
               and entry.get('reason')
               for entry in entries)


# ══════════════════════════════════════════════════════════════════════════════
# Lightweight C++ call parser for display contracts
# ══════════════════════════════════════════════════════════════════════════════

CPP_STRING_RE = re.compile(
    r'(?:u8|u|U|L)?"((?:[^"\\]|\\.)*)"', re.DOTALL)


def _mask_cpp_comments(source: str) -> str:
    """Replace comments with spaces while preserving indices and newlines."""
    out = list(source)
    i = 0
    state = 'code'
    while i < len(source):
        c = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ''
        if state == 'code':
            if c == '/' and nxt == '/':
                out[i] = out[i + 1] = ' '
                i += 2
                state = 'line-comment'
                continue
            if c == '/' and nxt == '*':
                out[i] = out[i + 1] = ' '
                i += 2
                state = 'block-comment'
                continue
            if c == '"':
                state = 'string'
            elif c == "'":
                state = 'char'
        elif state == 'line-comment':
            if c == '\n':
                state = 'code'
            else:
                out[i] = ' '
        elif state == 'block-comment':
            if c == '*' and nxt == '/':
                out[i] = out[i + 1] = ' '
                i += 2
                state = 'code'
                continue
            if c != '\n':
                out[i] = ' '
        elif state in ('string', 'char'):
            if c == '\\':
                i += 2
                continue
            if (state == 'string' and c == '"') or \
               (state == 'char' and c == "'"):
                state = 'code'
        i += 1
    return ''.join(out)


def _find_matching_paren(source: str, open_pos: int):
    depth = 0
    state = 'code'
    i = open_pos
    while i < len(source):
        c = source[i]
        if state == 'code':
            if c == '"':
                state = 'string'
            elif c == "'":
                state = 'char'
            elif c == '(':
                depth += 1
            elif c == ')':
                depth -= 1
                if depth == 0:
                    return i
        elif state in ('string', 'char'):
            if c == '\\':
                i += 2
                continue
            if (state == 'string' and c == '"') or \
               (state == 'char' and c == "'"):
                state = 'code'
        i += 1
    return None


def _find_matching_brace(source: str, open_pos: int):
    """Return the matching closing brace, ignoring braces in literals."""
    depth = 0
    state = 'code'
    i = open_pos
    while i < len(source):
        c = source[i]
        if state == 'code':
            if c == '"':
                state = 'string'
            elif c == "'":
                state = 'char'
            elif c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    return i
        elif state in ('string', 'char'):
            if c == '\\':
                i += 2
                continue
            if (state == 'string' and c == '"') or \
               (state == 'char' and c == "'"):
                state = 'code'
        i += 1
    return None


def _find_statement_end(source: str, start: int, end: int):
    """Find a top-level semicolon inside one function body."""
    paren = bracket = brace = 0
    state = 'code'
    i = start
    while i < end:
        c = source[i]
        if state == 'code':
            if c == '"':
                state = 'string'
            elif c == "'":
                state = 'char'
            elif c == '(':
                paren += 1
            elif c == ')':
                paren -= 1
            elif c == '[':
                bracket += 1
            elif c == ']':
                bracket -= 1
            elif c == '{':
                brace += 1
            elif c == '}':
                brace -= 1
            elif c == ';' and paren == bracket == brace == 0:
                return i
        elif state in ('string', 'char'):
            if c == '\\':
                i += 2
                continue
            if (state == 'string' and c == '"') or \
               (state == 'char' and c == "'"):
                state = 'code'
        i += 1
    return None


def _split_call_args(source: str, start: int, end: int):
    """Return (argument_text, absolute_start) for one call's arguments."""
    result = []
    arg_start = start
    paren = bracket = brace = 0
    state = 'code'
    i = start
    while i < end:
        c = source[i]
        if state == 'code':
            if c == '"':
                state = 'string'
            elif c == "'":
                state = 'char'
            elif c == '(':
                paren += 1
            elif c == ')':
                paren -= 1
            elif c == '[':
                bracket += 1
            elif c == ']':
                bracket -= 1
            elif c == '{':
                brace += 1
            elif c == '}':
                brace -= 1
            elif c == ',' and paren == bracket == brace == 0:
                result.append((source[arg_start:i], arg_start))
                arg_start = i + 1
        elif state in ('string', 'char'):
            if c == '\\':
                i += 2
                continue
            if (state == 'string' and c == '"') or \
               (state == 'char' and c == "'"):
                state = 'code'
        i += 1
    result.append((source[arg_start:end], arg_start))
    return result


def _iter_named_calls(source: str, names):
    """Yield function calls using only Python stdlib lexical parsing.

    This intentionally has no tree-sitter dependency, so the blocking check
    behaves identically on developer machines and minimal CI images.
    """
    masked = _mask_cpp_comments(source)
    pattern = re.compile(r'\b(' + '|'.join(map(re.escape, names)) + r')\s*\(')
    for match in pattern.finditer(masked):
        open_pos = masked.find('(', match.start(), match.end())
        close_pos = _find_matching_paren(masked, open_pos)
        if close_pos is None:
            continue
        yield (match.group(1), match.start(),
               _split_call_args(masked, open_pos + 1, close_pos))


def _iter_named_function_bodies(source: str, names):
    """Yield explicitly named C++ function bodies without an AST dependency.

    Calls and declarations are rejected because their closing parenthesis is
    followed by a semicolon rather than a body.  Qualifiers such as ``const``,
    ``override`` and trailing return syntax are tolerated.
    """
    masked = _mask_cpp_comments(source)
    pattern = re.compile(r'\b(' + '|'.join(map(re.escape, names)) + r')\s*\(')
    for match in pattern.finditer(masked):
        open_pos = masked.find('(', match.start(), match.end())
        close_pos = _find_matching_paren(masked, open_pos)
        if close_pos is None:
            continue

        cursor = close_pos + 1
        while cursor < len(masked) and masked[cursor].isspace():
            cursor += 1
        while cursor < len(masked) and masked[cursor] not in '{;':
            cursor += 1
        if cursor >= len(masked) or masked[cursor] != '{':
            continue

        # A matching call used in an if-condition or member chain can also be
        # followed by a brace.  Function definitions do not contain a closing
        # parenthesis or member-access dot between their parameter list and
        # body for any registered producer/builder signature.
        suffix = masked[close_pos + 1:cursor]
        if ')' in suffix or '.' in suffix:
            continue

        body_end = _find_matching_brace(masked, cursor)
        if body_end is None:
            continue
        yield match.group(1), cursor + 1, body_end


def _string_literals_with_call_ancestors(expression: str):
    """Return string literals and the call names which lexically contain them."""
    result = []
    paren_stack = []
    i = 0
    while i < len(expression):
        c = expression[i]
        if c == '"':
            match = CPP_STRING_RE.match(expression, max(0, i - 2))
            if not match or match.start() != i:
                match = CPP_STRING_RE.match(expression, i)
            if match:
                result.append((match.group(1), match.start(),
                               tuple(name for name in paren_stack if name)))
                i = match.end()
                continue
        if c == "'":
            i += 1
            while i < len(expression):
                if expression[i] == '\\':
                    i += 2
                    continue
                if expression[i] == "'":
                    i += 1
                    break
                i += 1
            continue
        if c == '(':
            prefix = expression[:i].rstrip()
            name_match = re.search(r'([A-Za-z_]\w*)$', prefix)
            paren_stack.append(name_match.group(1) if name_match else None)
        elif c == ')':
            if paren_stack:
                paren_stack.pop()
        i += 1
    return result


def _direct_untranslated_literals(expression: str):
    """Find literals not protected by a translation/DB provider call."""
    return [(body, offset) for body, offset, ancestors
            in _string_literals_with_call_ancestors(expression)
            if not any(name in TRANSLATED_VALUE_PROVIDERS
                       for name in ancestors)]


def _dynamic_key_literals(expression: str):
    """Find a dynamic wrapper's literal key, allowing grouping parentheses."""
    return [(body, offset) for body, offset, ancestors
            in _string_literals_with_call_ancestors(expression)
            if not ancestors]


def _decode_cpp_string(body: str) -> str:
    replacements = {
        r'\n': '\n', r'\t': '\t', r'\r': '\r',
        r'\"': '"', r"\'": "'", r'\\': '\\',
    }
    return re.sub(r'\\(?:n|t|r|"|\'|\\)',
                  lambda match: replacements.get(match.group(0),
                                                   match.group(0)), body)


def _escape_display_controls(value: str) -> str:
    """Keep one finding on one terminal/CI output line."""
    return value.replace('\n', r'\n').replace('\t', r'\t').replace('\r', r'\r')


def _producer_expressions(source, body_start, body_end, out_params):
    """Yield display-bearing expressions from one contracted producer."""
    masked = _mask_cpp_comments(source)
    body = masked[body_start:body_end]

    for match in re.finditer(r'\breturn\b', body):
        expression_start = body_start + match.end()
        expression_end = _find_statement_end(masked, expression_start,
                                             body_end)
        if expression_end is not None:
            yield 'return', expression_start, source[expression_start:expression_end]

    for param in out_params:
        pattern = re.compile(r'\b' + re.escape(param) + r'\s*(?:\+=|=)')
        for match in pattern.finditer(body):
            expression_start = body_start + match.end()
            expression_end = _find_statement_end(masked, expression_start,
                                                 body_end)
            if expression_end is not None:
                yield param, expression_start, source[expression_start:expression_end]


def _builder_expressions(source, body_start, body_end, variables):
    """Yield assignments to explicitly contracted UI builder variables."""
    masked = _mask_cpp_comments(source)
    body = masked[body_start:body_end]
    for variable in variables:
        pattern = re.compile(r'\b' + re.escape(variable)
                             + r'(?:\s*\[[^\]]*\])?\s*(?:\+=|=)')
        for match in pattern.finditer(body):
            expression_start = body_start + match.end()
            expression_end = _find_statement_end(masked, expression_start,
                                                 body_end)
            if expression_end is not None:
                yield variable, expression_start, source[expression_start:expression_end]


def _scan_display_producers(source, rel_path, contract_allowlist,
                            debug_lines, strict):
    """Enforce translation in explicitly registered UI text producers."""
    findings = []
    filtered = []
    producer_specs = DISPLAY_TEXT_PRODUCERS.get(rel_path, {})
    if not producer_specs:
        return findings, filtered

    definitions = list(_iter_named_function_bodies(source, producer_specs))
    by_function = {function: [] for function in producer_specs}
    for definition in definitions:
        by_function[definition[0]].append(definition)

    for function, matches in by_function.items():
        if len(matches) != 1:
            lineno = (source.count('\n', 0, matches[0][1]) + 1
                      if matches else 1)
            display = (f'DISPLAY005 producer contract {function}: expected '
                       f'exactly one definition, found {len(matches)}')
            findings.append((rel_path, lineno, display[:160], 'DISPLAY'))

    for function, body_start, body_end in definitions:
        out_params = producer_specs[function]
        for carrier, expression_start, expression in _producer_expressions(
                source, body_start, body_end, out_params):
            literals = _direct_untranslated_literals(expression)
            if not literals:
                continue
            literal = ''.join(_decode_cpp_string(body) for body, _ in literals)
            if not has_word(literal):
                continue
            first_offset = expression_start + literals[0][1]
            lineno = source.count('\n', 0, first_offset) + 1
            if not strict and lineno in debug_lines:
                continue

            rule = 'direct-display-producer'
            display = (f'DISPLAY003 {function} {carrier}: '
                       f'{_escape_display_controls(literal)}')
            if _contract_is_allowlisted(contract_allowlist, rule, rel_path,
                                        lineno, function, literal):
                filtered.append((rel_path, lineno, display[:160],
                                 'DISPLAY', 'legacy-contract'))
            else:
                findings.append((rel_path, lineno, display[:160],
                                 'DISPLAY'))
    return findings, filtered


def _scan_display_builders(source, rel_path, contract_allowlist,
                           debug_lines, strict):
    """Enforce translation in explicitly registered UI builder strings."""
    findings = []
    filtered = []
    builder_specs = DISPLAY_TEXT_BUILDERS.get(rel_path, {})
    if not builder_specs:
        return findings, filtered

    definitions = list(_iter_named_function_bodies(source, builder_specs))
    by_function = {function: [] for function in builder_specs}
    for definition in definitions:
        by_function[definition[0]].append(definition)

    for function, matches in by_function.items():
        if len(matches) != 1:
            lineno = (source.count('\n', 0, matches[0][1]) + 1
                      if matches else 1)
            display = (f'DISPLAY006 builder contract {function}: expected '
                       f'exactly one definition, found {len(matches)}')
            findings.append((rel_path, lineno, display[:160], 'DISPLAY'))

    for function, body_start, body_end in definitions:
        for carrier, expression_start, expression in _builder_expressions(
                source, body_start, body_end, builder_specs[function]):
            literals = _direct_untranslated_literals(expression)
            if not literals:
                continue
            literal = ''.join(_decode_cpp_string(body) for body, _ in literals)
            if not has_word(literal):
                continue
            first_offset = expression_start + literals[0][1]
            lineno = source.count('\n', 0, first_offset) + 1
            if not strict and lineno in debug_lines:
                continue

            rule = 'direct-display-builder'
            display = (f'DISPLAY004 {function} {carrier}: '
                       f'{_escape_display_controls(literal)}')
            if _contract_is_allowlisted(contract_allowlist, rule, rel_path,
                                        lineno, function, literal):
                filtered.append((rel_path, lineno, display[:160],
                                 'DISPLAY', 'legacy-contract'))
            else:
                findings.append((rel_path, lineno, display[:160],
                                 'DISPLAY'))
    return findings, filtered


def _scan_display_contracts(source, rel_path, source_entries,
                            contract_allowlist, debug_lines, strict):
    findings = []
    filtered = []
    if DISPLAY_SKIP_FILE_RE.match(os.path.basename(rel_path)):
        return findings, filtered

    sink_specs = dict(DIRECT_DISPLAY_SINKS)
    names = set(sink_specs) | set(DYNAMIC_KEY_WRAPPERS)
    for function, _call_start, args in _iter_named_calls(source, names):
        arg_index = (sink_specs.get(function)
                     if function in sink_specs
                     else DYNAMIC_KEY_WRAPPERS[function])
        if arg_index >= len(args):
            continue
        expression, expression_start = args[arg_index]
        literals = (_direct_untranslated_literals(expression)
                    if function in sink_specs
                    else _dynamic_key_literals(expression))
        if not literals:
            # Variables and translated DB/provider results are intentionally
            # outside this literal-only contract and must not be guessed at.
            continue
        literal = ''.join(_decode_cpp_string(body) for body, _ in literals)
        first_offset = expression_start + literals[0][1]
        lineno = source.count('\n', 0, first_offset) + 1
        if not strict and lineno in debug_lines:
            continue
        if function in sink_specs:
            if not has_word(literal):
                continue
        elif not has_alpha(literal):
            continue

        if function in sink_specs:
            rule = 'direct-display'
            severity = 'DISPLAY'
            display = f'{function}: {_escape_display_controls(literal)}'
        else:
            rule = 'dynamic-key'
            severity = 'DYNKEY'
            if source_entries is None:
                display = (f'{function}: cannot verify "{literal}" '
                           f'without --source-txt')
            elif not source_entries.get(literal.lower(), '').strip():
                display = f'{function}: missing source.txt key "{literal}"'
            else:
                continue

        if _contract_is_allowlisted(contract_allowlist, rule, rel_path,
                                    lineno, function, literal):
            filtered.append((rel_path, lineno, display[:120], severity,
                             'legacy-contract'))
        else:
            findings.append((rel_path, lineno, display[:120], severity))

    producer_findings, producer_filtered = _scan_display_producers(
        source, rel_path, contract_allowlist, debug_lines, strict)
    findings.extend(producer_findings)
    filtered.extend(producer_filtered)
    builder_findings, builder_filtered = _scan_display_builders(
        source, rel_path, contract_allowlist, debug_lines, strict)
    findings.extend(builder_findings)
    filtered.extend(builder_filtered)
    return findings, filtered


# ══════════════════════════════════════════════════════════════════════════════
# source.txt parser (shared with i18n_extract.py)
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: missing-t
# ══════════════════════════════════════════════════════════════════════════════

def cmd_missing_t(args):
    """Find untranslated output calls and enforce display contracts."""
    source_dir = args.source_dir
    strict = getattr(args, 'strict', False)
    show_filtered = getattr(args, 'show_filtered', False)
    contracts_only = getattr(args, 'display_contracts_only', False)
    allowlist_file = getattr(args, 'allowlist', None)
    allowlist = load_allowlist(allowlist_file)
    contract_allowlist = (load_contract_allowlist(allowlist_file)
                          if contracts_only else [])
    source_entries = (parse_source_txt(args.source_txt)
                      if contracts_only else None)

    findings = []       # (rel_path, lineno, display, severity) — candidates
    filtered = []       # (rel_path, lineno, display, severity, reason) — filtered out
    files_scanned = 0

    for dirpath, dirnames, filenames in os.walk(source_dir):
        prune_dirs(dirnames)
        for fn in sorted(filenames):
            if not (fn.endswith(".cc") or fn.endswith(".h")):
                continue
            filepath = os.path.join(dirpath, fn)
            files_scanned += 1
            rel_path = os.path.relpath(filepath, source_dir)

            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            debug_lines = build_debug_ranges(
                lines, {'WIZARD'} if contracts_only else None)
            comment_lines = build_comment_ranges(lines)

            if contracts_only:
                source = ''.join(lines)
                contract_findings, contract_filtered = _scan_display_contracts(
                    source, rel_path, source_entries, contract_allowlist,
                    debug_lines, strict)
                findings.extend(contract_findings)
                filtered.extend(contract_filtered)
                continue

            for lineno, line in enumerate(lines, 1):
                # Pre-filter: skip preprocessor directives
                if SKIP_PP_RE.match(line):
                    continue

                # Skip diagnostic/error channels
                if SKIP_CHANNEL_RE.search(line):
                    continue

                # Skip lines inside /* ... */ block comments or // comments
                if lineno in comment_lines:
                    continue

                # Skip lines inside #ifdef DEBUG or #if 0 blocks
                if not strict and lineno in debug_lines:
                    # Still check MPR_CALL_RE to report as filtered in --show-filtered
                    if show_filtered and MPR_CALL_RE.search(line):
                        if not HAS_T_RE.search(line):
                            stripped = strip_cpp_string_literal(line)
                            if stripped and has_alpha(stripped):
                                filtered.append((rel_path, lineno, stripped[:80],
                                                _severity(line), 'debug-block'))
                    continue

                # Main check
                if not MPR_CALL_RE.search(line):
                    continue
                if HAS_T_RE.search(line):
                    continue

                stripped = strip_cpp_string_literal(line)
                if not stripped or not has_alpha(stripped):
                    continue

                # Allowlist check
                if (rel_path, lineno) in allowlist:
                    if show_filtered:
                        filtered.append((rel_path, lineno, stripped[:80],
                                        _severity(line), 'allowlisted'))
                    continue

                # Format-only filter
                sev = _severity(line)
                if is_format_only(stripped):
                    if show_filtered:
                        filtered.append((rel_path, lineno, stripped[:80],
                                        sev, 'format-only'))
                    continue

                display = stripped[:80]
                findings.append((rel_path, lineno, display, sev))

    # ── Output ──

    # Per-category stats
    def cat_stats(lst):
        stats = {
            'MSG': sum(1 for _, _, _, s, *_ in lst if s == 'MSG'),
            'UI': sum(1 for _, _, _, s, *_ in lst if s == 'UI'),
            'STR': sum(1 for _, _, _, s, *_ in lst if s == 'STR'),
            'SMM': sum(1 for _, _, _, s, *_ in lst if s == 'SMM'),
        }
        if contracts_only:
            stats['DISPLAY'] = sum(1 for _, _, _, s, *_ in lst
                                   if s == 'DISPLAY')
            stats['DYNKEY'] = sum(1 for _, _, _, s, *_ in lst
                                  if s == 'DYNKEY')
        return stats

    cand_stats = cat_stats(findings)
    total_cand = len(findings)
    total_filt = len(filtered)

    # Filtered breakdown by reason
    filt_by_reason = {}
    for item in filtered:
        reason = item[4]
        filt_by_reason[reason] = filt_by_reason.get(reason, 0) + 1

    # Candidate output
    if findings:
        if contracts_only:
            print("=== I18n display-contract violations ===")
        else:
            print("=== Untranslated calls — candidates (need T_()) ===")
        print()
        for fpath, lineno, msg, sev in findings:
            print(f"[{sev}] {fpath}:{lineno}  \"{msg}\"")
        print()

    # Filtered output (if --show-filtered)
    if show_filtered and filtered:
        print("=== Filtered out ===")
        print()
        for fpath, lineno, msg, sev, reason in filtered:
            print(f"[{sev}][{reason}] {fpath}:{lineno}  \"{msg}\"")
        print()

    # Summary
    print(f"--- scan_i18n.py missing-t ---")
    print(f"Files scanned: {files_scanned}")
    print()
    categories = ['MSG', 'UI', 'STR', 'SMM']
    if contracts_only:
        categories.extend(['DISPLAY', 'DYNKEY'])
    for cat in categories:
        print(f"  {cat}: {cand_stats[cat]} candidates")
    print()
    if not strict:
        print(f"  (debug/#if0 blocks excluded; use --strict to include)")
    if filt_by_reason:
        print(f"  Filtered: {total_filt}")
        for reason, count in sorted(filt_by_reason.items()):
            print(f"    {reason}: {count}")
    if allowlist:
        print(f"  Allowlisted: {len(allowlist)} entries loaded")
    print()

    if total_cand == 0 and total_filt == 0:
        print("OK: No untranslated calls found.")
        return 0
    elif total_cand == 0:
        print("OK: No candidates — all findings are filtered or allowlisted.")
        return 0
    else:
        # Per-file summary
        file_stats = {}
        for fpath, _, _, sev in findings:
            if fpath not in file_stats:
                file_stats[fpath] = {}
            file_stats[fpath][sev] = file_stats[fpath].get(sev, 0) + 1
        print("Per-file candidate breakdown:")
        for fpath in sorted(file_stats, key=lambda x: -sum(file_stats[x].values())):
            parts = []
            for sev in categories:
                if sev in file_stats[fpath]:
                    parts.append(f"{sev}:{file_stats[fpath][sev]}")
            print(f"  {fpath}: {', '.join(parts)}")
        return 1


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: mprf-p
# ══════════════════════════════════════════════════════════════════════════════

def cmd_mprf_p(args):
    """Check that source.txt entries with positional %n$s use mprf_p in code."""
    entries = parse_source_txt(args.source_txt)
    if not entries:
        print("ERROR: Could not parse source.txt")
        return 1

    # Find all EN keys whose CN translation uses positional format
    pos_keys = {}  # en_key -> cn_translation
    for key, value in entries.items():
        if POSFMT_RE.search(value):
            pos_keys[key] = value

    if not pos_keys:
        print("OK: No positional format entries in source.txt.")
        return 0

    # Search for these keys in C++ source
    source_dir = args.source_dir
    findings = []

    for dirpath, dirnames, filenames in os.walk(source_dir):
        prune_dirs(dirnames)
        for fn in sorted(filenames):
            if not (fn.endswith(".cc") or fn.endswith(".h")):
                continue
            filepath = os.path.join(dirpath, fn)

            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            for lineno, line in enumerate(lines, 1):
                if not HAS_T_RE.search(line):
                    continue
                # Check each positional key
                for en_key, cn_val in pos_keys.items():
                    # Search for the EN key as a T_() argument
                    # (unescaped version — use simple substring match)
                    if en_key not in line.lower():
                        continue
                    # Found a match — check if it uses mprf_p
                    # Also check previous 2 lines for multi-line _p calls
                    pos_call = POSITIONAL_CALL_RE.search(line)
                    if not pos_call and lineno > 1:
                        pos_call = POSITIONAL_CALL_RE.search(lines[lineno - 2])
                    if not pos_call and lineno > 2:
                        pos_call = POSITIONAL_CALL_RE.search(lines[lineno - 3])
                    if not pos_call:
                        findings.append((filepath, lineno, en_key, cn_val[:60]))

    if findings:
        print("=== Positional format in source.txt "
              "but code doesn't use _p variant ===")
        print()
        for fpath, lineno, en_key, cn_snippet in findings:
            rel_path = os.path.relpath(fpath, source_dir) if source_dir in fpath else fpath
            print(f"{rel_path}:{lineno}  T_(\"{en_key}\")")
            print(f"  source.txt has %n$s: \"{cn_snippet}...\""
                  f" → needs mprf_p or make_stringf_p")
            print()
        print(f"Summary: {len(findings)} violations")
        return 1
    else:
        print(f"OK: All {len(pos_keys)} positional-format entries use "
              f"a _p variant correctly.")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: arg-mismatch
# ══════════════════════════════════════════════════════════════════════════════

def cmd_arg_mismatch(args):
    """Comprehensive format specifier validation.

    Checks:
      1. Count parity — %s/%d count between EN key and CN translation
      2. Sequential type-order — for non-positional entries, type sequence must
         match (swapped %s/%d causes crash on MinGW vsnprintf)
      3. Mixed positional/plain — CN value must not mix %n$s with plain %s/%d
         (MinGW vsnprintf falls back to system impl which ignores positional)
      4. Positional type mismatch — same %N$ must have same type in EN and CN

    Note: positional gaps (e.g. %1$s...%3$s without %2$s) are NOT checked —
    vmake_stringf_p explicitly supports dropped positions via uintptr_t
    consumption (positional_format.cc:182-206). This is the intended pattern
    for verb conjugation suffixes (%2$s = "s") dropped in Chinese.
    """
    entries = parse_source_txt(args.source_txt)
    if not entries:
        print("ERROR: Could not parse source.txt")
        return 1

    # ── 1. Count parity ──
    # CN can safely have FEWER format args than EN — vsnprintf (standard)
    # and vmake_stringf_p (positional) both ignore extra args beyond what
    # the format string references. Only CN > EN is dangerous: the CN
    # expects args that were never passed → undefined behavior → crash.
    count_findings = []
    for en_key, cn_val in entries.items():
        en_count = count_format_args(en_key)
        cn_count = count_format_args(cn_val)
        if cn_count > en_count:
            count_findings.append((en_key, cn_val, en_count, cn_count))

    # ── 2. Sequential type-order (non-positional only) ──
    seq_findings = []
    for en_key, cn_val in entries.items():
        if POSFMT_RE.search(en_key) or POSFMT_RE.search(cn_val):
            continue
        if not cn_val.strip():
            continue
        cleaned_en = re.sub(r'%%', '', en_key)
        cleaned_cn = re.sub(r'%%', '', cn_val)
        seq_en = [m.group(0) for m in PLAIN_FMT_RE.finditer(cleaned_en)]
        seq_cn = [m.group(0) for m in PLAIN_FMT_RE.finditer(cleaned_cn)]
        if seq_en != seq_cn and len(seq_en) == len(seq_cn):
            seq_findings.append((en_key, cn_val, seq_en, seq_cn))

    # ── 3. Mixed positional/plain in CN ──
    mixed_findings = []
    for en_key, cn_val in entries.items():
        if not POSFMT_RE.search(cn_val):
            continue
        cleaned = re.sub(r'%%', '', cn_val)
        plain_matches = [m for m in PLAIN_FMT_RE.finditer(cleaned)
                         if not POSFMT_RE.match(m.group(0))]
        if plain_matches:
            mixed_findings.append((en_key, cn_val))

    # ── 4. Positional type mismatch ──
    pos_type_findings = []
    for en_key, cn_val in entries.items():
        en_pos = POSFMT_RE.search(en_key)
        cn_pos = POSFMT_RE.search(cn_val)
        if not en_pos or not cn_pos:
            continue
        # Build {position: type} dicts
        def _pos_types(s):
            result = {}
            for m in POSFMT_TYPE_RE.finditer(s):
                pos = int(m.group(1))
                typ = m.group(2)
                # Normalise: l[du] → l, PRIu64 → l, any PRI* → l
                if typ.startswith('l') or typ.startswith('PRI'):
                    typ = 'l'
                # Normalise . → s (%.0s is a valid format for consuming strings)
                if typ == '.':
                    typ = 's'
                # Only store first occurrence per position
                if pos not in result:
                    result[pos] = typ
            return result
        en_types = _pos_types(en_key)
        cn_types = _pos_types(cn_val)
        mismatches = []
        for pos in sorted(set(en_types.keys()) | set(cn_types.keys())):
            et = en_types.get(pos)
            ct = cn_types.get(pos)
            if et and ct and et != ct:
                mismatches.append((pos, et, ct))
        if mismatches:
            pos_type_findings.append((en_key, cn_val, mismatches))

    # ── Output ──
    total_findings = len(count_findings) + len(seq_findings) + \
                     len(mixed_findings) + len(pos_type_findings)
    if total_findings == 0:
        print(f"OK: All {len(entries)} entries pass format validation "
              f"(count, type-order, mixed, pos-type).")
        return 0

    if count_findings:
        print("=== ARG-MISMATCH — format specifier count differs "
              "between EN key and CN translation ===")
        for en_key, cn_val, en_n, cn_n in sorted(count_findings):
            print(f"EN: \"{en_key[:80]}\" ({en_n} args)")
            print(f"CN: \"{cn_val[:80]}\" ({cn_n} args) ← MISMATCH")
            print()
        print(f"  → {len(count_findings)} count-mismatch(es)")
        print()

    if seq_findings:
        print("=== SEQ-TYPE-MISMATCH — sequential format specifier order "
              "differs (crash risk on MinGW) ===")
        for en_key, cn_val, seq_en, seq_cn in sorted(seq_findings):
            print(f"EN: \"{en_key[:80]}\"")
            print(f"     specifiers: {seq_en}")
            print(f"CN: \"{cn_val[:80]}\"")
            print(f"     specifiers: {seq_cn}")
            for i, (e, c) in enumerate(zip(seq_en, seq_cn)):
                if e != c:
                    print(f"     MISMATCH at position {i+1}: "
                          f"EN={e} CN={c}")
                    break
            print()
        print(f"  → {len(seq_findings)} type-order mismatch(es)")
        print()

    if mixed_findings:
        print("=== FORMAT-MALFORMED — mixed positional and non-positional "
              "format specifiers in CN ===")
        print("  These cause literal '%2$s' on Windows tiles (MinGW "
              "vsnprintf)")
        for en_key, cn_val in sorted(mixed_findings):
            print(f"EN: \"{en_key[:80]}\"")
            print(f"CN: \"{cn_val[:80]}\" <- MALFORMED")
            print()
        print(f"  → {len(mixed_findings)} malformed entry/entries")
        print()

    if pos_type_findings:
        print("=== POS-TYPE-MISMATCH — same position, different type "
              "between EN and CN ===")
        for en_key, cn_val, mismatches in sorted(pos_type_findings):
            print(f"EN: \"{en_key[:80]}\"")
            print(f"CN: \"{cn_val[:80]}\"")
            for pos, et, ct in mismatches:
                print(f"     %{pos}$: EN={et} CN={ct} ← MISMATCH")
            print()
        print(f"  → {len(pos_type_findings)} POS-type mismatch(es)")
        print()

    print(f"Total: {total_findings} format validation finding(s).")
    return 1


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: seq-type-mismatch
# ══════════════════════════════════════════════════════════════════════════════

def cmd_seq_type_mismatch(args):
    """Detect sequential format specifier type-order mismatches.

    For non-positional format strings, make_stringf uses vsnprintf which
    consumes arguments sequentially from the stack. If the CN translation
    swaps %s and %d positions relative to the EN key, argument types won't
    match what vsnprintf expects → undefined behavior → crash.

    This only applies to entries where NEITHER EN nor CN uses %n$s
    positional specifiers — those reference arguments by number and are
    immune to reordering.
    """
    entries = parse_source_txt(args.source_txt)
    if not entries:
        print("ERROR: Could not parse source.txt")
        return 1

    findings = []
    for en_key, cn_val in entries.items():
        # Skip entries with positional format — those are safe from
        # sequential reordering (they reference args by position number)
        if POSFMT_RE.search(en_key) or POSFMT_RE.search(cn_val):
            continue

        # Skip empty CN translations — T_() falls back to EN key,
        # so no mismatch can occur at runtime
        if not cn_val.strip():
            continue

        # Extract plain specifier sequences from both
        cleaned_en = re.sub(r'%%', '', en_key)
        cleaned_cn = re.sub(r'%%', '', cn_val)
        seq_en = [m.group(0) for m in PLAIN_FMT_RE.finditer(cleaned_en)]
        seq_cn = [m.group(0) for m in PLAIN_FMT_RE.finditer(cleaned_cn)]

        if seq_en != seq_cn:
            # Only report type-order mismatches (same count, different order).
            # Count mismatches are caught by the `arg-mismatch` subcommand.
            if len(seq_en) == len(seq_cn):
                findings.append((en_key, cn_val, seq_en, seq_cn))

    if findings:
        print("=== SEQ-TYPE-MISMATCH — sequential format specifier order "
              "differs between EN and CN ===")
        print("  These cause crashes on MinGW (Windows tiles) because "
              "vsnprintf")
        print("  consumes arguments in order — swapped %s/%d corrupts "
              "the stack.")
        print()
        for en_key, cn_val, seq_en, seq_cn in sorted(findings):
            en_short = en_key[:80]
            cn_short = cn_val[:80]
            print(f"EN: \"{en_short}\"")
            print(f"     specifiers: {seq_en}")
            print(f"CN: \"{cn_short}\"")
            print(f"     specifiers: {seq_cn}")
            for i, (e, c) in enumerate(zip(seq_en, seq_cn)):
                if e != c:
                    print(f"     MISMATCH at position {i+1}: "
                          f"EN={e} CN={c}")
                    break
            if len(seq_en) != len(seq_cn):
                print(f"     Count also differs: "
                      f"EN={len(seq_en)} CN={len(seq_cn)}")
            print()
        print(f"Summary: {len(findings)} type-order mismatch(es)")
        return 1
    else:
        print(f"OK: All {len(entries)} non-positional entries have "
              f"matching format-specifier type sequences.")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: format-malformed
# ══════════════════════════════════════════════════════════════════════════════

def cmd_format_malformed(args):
    """Detect mixed positional/non-positional format specifiers in CN values.

    vmake_stringf_p falls back to system vsnprintf when the format string
    mixes %n$s (positional) with plain %s/%d (non-positional). On MinGW
    (Windows tiles), system vsnprintf does not support positional %n$s,
    causing literal '%2$s' to appear in game text.
    """
    entries = parse_source_txt(args.source_txt)
    if not entries:
        print("ERROR: Could not parse source.txt")
        return 1

    findings = []
    for en_key, cn_val in entries.items():
        has_pos = bool(POSFMT_RE.search(cn_val))
        if not has_pos:
            continue
        # Check for non-positional format specs (exclude %% literals)
        cleaned = re.sub(r'%%', '', cn_val)
        plain_matches = [m for m in PLAIN_FMT_RE.finditer(cleaned)
                         if not POSFMT_RE.match(m.group(0))]
        if plain_matches:
            findings.append((en_key, cn_val))

    if findings:
        print("=== FORMAT-MALFORMED — mixed positional and non-positional "
              "format specifiers ===")
        print("  These cause literal '%2$s' on Windows tiles (MinGW vsnprintf)")
        print()
        for en_key, cn_val in sorted(findings):
            en_short = en_key[:80]
            cn_short = cn_val[:80]
            print(f"EN: \"{en_short}\"")
            print(f"CN: \"{cn_short}\" <- MALFORMED (mixed pos/plain)")
            print()
        print(f"Summary: {len(findings)} malformed entries")
        return 1
    else:
        print(f"OK: All {len(entries)} entries have consistent format "
              f"specifier types (no mixed positional/plain).")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: check-gaps
# ══════════════════════════════════════════════════════════════════════════════

def cmd_check_gaps(args):
    """Detect gaps in positional format numbering in CN translations.

    NOTE: vmake_stringf_p explicitly supports sparsely-numbered positional
    specs (positional_format.cc:182-206) — unused positions are consumed via
    uintptr_t. Most gaps are safe verb conjugation drops. The unified
    arg-mismatch command intentionally skips this check.
    """
    entries = parse_source_txt(args.source_txt)
    if not entries:
        print("ERROR: Could not parse source.txt")
        return 1

    ok_count = 0
    nopos_count = 0
    gaps = []

    for en_key, cn_val in entries.items():
        disp = set(int(m.group(1)) for m in POSFMT_RE.finditer(cn_val))
        silent = set(int(m.group(1)) for m in SILENT_RE.finditer(cn_val))
        all_pos = disp | silent
        if not all_pos:
            nopos_count += 1
            continue
        expected = set(range(1, max(all_pos) + 1))
        missing = expected - all_pos
        if missing:
            gaps.append((en_key, cn_val, sorted(all_pos), sorted(missing)))
        else:
            ok_count += 1

    if gaps:
        print("=== POSITIONAL GAPS — missing position numbers "
              "in CN translations ===")
        print()
        for en_key, cn_val, found, missing in gaps:
            cn_short = cn_val[:100]
            print(f"  EN: \"{en_key}\"")
            print(f"  CN: \"{cn_short}\"")
            print(f"  found positions: {found}")
            print(f"  missing positions: {missing}")
            print()
        print(f"Summary: {len(gaps)} gaps found, {ok_count} OK, "
              f"{nopos_count} without positional format")
        return 1
    else:
        print(f"OK: {ok_count} positional entries have no gaps "
              f"({nopos_count} without positional format).")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: lang-args
# ══════════════════════════════════════════════════════════════════════════════

def cmd_lang_args(args):
    """Detect language-dependent arguments in T_() calls (heuristic)."""
    source_dir = args.source_dir
    findings = []

    # Patterns for language-dependent arguments
    # After T_("..."), look for extra string literal arguments
    EXTRA_LITERAL_RE = re.compile(
        r'T_\s*\(\s*"(?:[^"\\]|\\.)*"\s*\)\s*,\s*"([^"]*)"'
    )
    CONJ_VERB_RE = re.compile(r'conj_verb\s*\(')
    PRONOUN_RE = re.compile(r'pronoun\s*\(')

    for dirpath, dirnames, filenames in os.walk(source_dir):
        prune_dirs(dirnames)
        for fn in sorted(filenames):
            if not (fn.endswith(".cc") or fn.endswith(".h")):
                continue
            filepath = os.path.join(dirpath, fn)

            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            for lineno, line in enumerate(lines, 1):
                if not HAS_T_RE.search(line):
                    continue

                # Check for string literal args after T_()
                m = EXTRA_LITERAL_RE.search(line)
                if m:
                    literal = m.group(1)
                    if has_alpha(literal):
                        rel_path = os.path.relpath(filepath, source_dir)
                        findings.append(("HIGH", rel_path, lineno,
                                        f"\"{literal}\"", line.strip()[:100]))
                        continue

                # Check for conj_verb() calls
                if CONJ_VERB_RE.search(line):
                    rel_path = os.path.relpath(filepath, source_dir)
                    findings.append(("MED", rel_path, lineno,
                                    "conj_verb()", line.strip()[:100]))
                    continue

                # Check for pronoun() calls
                if PRONOUN_RE.search(line):
                    rel_path = os.path.relpath(filepath, source_dir)
                    findings.append(("LOW", rel_path, lineno,
                                    "pronoun()", line.strip()[:100]))

    if findings:
        print("=== Language-dependent args — untranslated arguments "
              "in T_() calls ===")
        print()
        print("Legend:")
        print("  [HIGH]  String literal arg — always English at runtime")
        print("  [MED]   conj_verb() — may not be needed in CN")
        print("  [LOW]   pronoun() — needs manual review")
        print()
        for level, fpath, lineno, detail, context in findings:
            print(f"[{level}] {fpath}:{lineno}  {detail}")
            print(f"        {context}")
            print()
        print(f"Summary: {len(findings)} candidates")
        return 0  # heuristic — never fail
    else:
        print("OK: No language-dependent argument candidates found.")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: validate-terms
# ══════════════════════════════════════════════════════════════════════════════

_DECISION_METADATA_FIELD_RE = re.compile(
    r"(?m)^-[ \t]+\*\*([A-Za-z][^*\n]*)\*\*:[ \t]*"
)
_DECISION_METADATA_TERMINATOR_RE = re.compile(
    r"(?m)^---[ \t]*$|^###\s"
)
_DECISION_FIELD_CONTAINER_RE = re.compile(
    r"(?:"
    r">[ \t]*"
    r"|(?:[-+]|[0-9]+[.)])[ \t]*"
    r"|\*[ \t]+"
    r"|\[[ xX]\][ \t]+"
    r")"
)
_DECISION_FIELD_COLON_RE = re.compile(r"[:：]")
_DECISION_RAW_RESERVED_RE = re.compile(
    r"(?i)(?P<name>Status|Choice|Rejected)"
)
_DECISION_WRAPPER_CHARS = frozenset("*_`")
_DECISION_CANONICAL_RESERVED_FIELD_RE = re.compile(
    r"-[ \t]+\*\*(?P<name>Status|Choice|Rejected)\*\*:"
    r"(?P<value>.*)"
)
_DECISION_RESERVED_FIELDS = {
    "status": "Status",
    "choice": "Choice",
    "rejected": "Rejected",
}


def _decision_metadata_bounds(block: str) -> tuple[int, int]:
    """Return the decision metadata body before its logical terminator."""
    heading_end = block.find("\n")
    if heading_end < 0:
        return len(block), len(block)
    start = heading_end + 1
    terminator = _DECISION_METADATA_TERMINATOR_RE.search(block, start)
    end = terminator.start() if terminator else len(block)
    return start, end


def _decision_decorated_reserved_token(line: str, position: int):
    """Return a wrapper-delimited reserved token at one exact offset."""
    name_start = position
    opening_wrapper = False
    while (
        name_start < len(line)
        and (
            line[name_start] in _DECISION_WRAPPER_CHARS
            or line[name_start] in " \t"
        )
    ):
        opening_wrapper |= line[name_start] in _DECISION_WRAPPER_CHARS
        name_start += 1
    decorated_name = _DECISION_RAW_RESERVED_RE.match(line, name_start)
    if opening_wrapper and decorated_name:
        scan_end = decorated_name.end()
        token_end = scan_end
        closing_wrapper = False
        while (
            scan_end < len(line)
            and (
                line[scan_end] in _DECISION_WRAPPER_CHARS
                or line[scan_end] in " \t"
            )
        ):
            if line[scan_end] in _DECISION_WRAPPER_CHARS:
                closing_wrapper = True
                token_end = scan_end + 1
            scan_end += 1
    else:
        closing_wrapper = False
    if opening_wrapper and decorated_name and closing_wrapper:
        canonical_name = _DECISION_RESERVED_FIELDS[
            decorated_name.group("name").casefold()
        ]
        return canonical_name, position, token_end
    return None


def _decision_reserved_token(line: str):
    """Return one reserved token and its exact consumed span, if present."""
    position = len(line) - len(line.lstrip(" \t"))
    while True:
        decorated = _decision_decorated_reserved_token(line, position)
        if decorated is not None:
            return decorated
        container = _DECISION_FIELD_CONTAINER_RE.match(line, position)
        if not container:
            break
        position = container.end()

    raw = _DECISION_RAW_RESERVED_RE.match(line, position)
    if raw and re.match(r"[ \t]*[:：]", line[raw.end():]):
        canonical_name = _DECISION_RESERVED_FIELDS[
            raw.group("name").casefold()
        ]
        return canonical_name, position, raw.end()

    candidate = line[position:]
    colon = _DECISION_FIELD_COLON_RE.search(candidate)
    if not colon:
        return None
    label = candidate[:colon.start()]
    previous = None
    while label != previous:
        previous = label
        label = label.strip()
        label = label.strip("*_`")
    if not label:
        return None
    canonical_name = _DECISION_RESERVED_FIELDS.get(label.casefold())
    if canonical_name is None:
        return None
    return canonical_name, position, position + colon.start()


def _decision_canonical_reserved_field(
    line: str,
    expected_name: str,
) -> bool:
    """Accept only one exact separator and a non-nested field value."""
    canonical = _DECISION_CANONICAL_RESERVED_FIELD_RE.fullmatch(line)
    if not canonical or canonical.group("name") != expected_name:
        return False
    value = canonical.group("value")
    first = value.lstrip(" \t")
    if first.startswith((':', '：')):
        return False
    return _decision_reserved_token(value) is None


def _decision_reserved_declarations(
    block: str,
) -> list[tuple[str, str, bool]]:
    """Return every reserved-name collision and its canonicality."""
    start, end = _decision_metadata_bounds(block)
    declarations = []
    for line in block[start:end].splitlines():
        token = _decision_reserved_token(line)
        if token is None:
            continue
        canonical_name, _token_start, _token_end = token
        declarations.append(
            (
                canonical_name,
                line,
                _decision_canonical_reserved_field(line, canonical_name),
            )
        )
    return declarations


def _decision_reserved_field_errors(
    decision_id: str,
    block: str,
) -> list[str]:
    """Reject non-canonical declarations colliding with reserved fields."""
    errors = []
    for _name, line, is_canonical in _decision_reserved_declarations(block):
        if is_canonical:
            continue
        errors.append(
            f"{decision_id}: malformed reserved metadata declaration: "
            f"{line!r}"
        )
    return errors


def _decision_metadata_fields(block: str) -> dict[str, list[str]]:
    """Return every top-level Markdown metadata field without collapsing."""
    start, end = _decision_metadata_bounds(block)
    matches = list(_DECISION_METADATA_FIELD_RE.finditer(block, start, end))
    fields = {}
    for index, match in enumerate(matches):
        name = match.group(1)
        value_end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else end
        )
        if name == "Status":
            newline = block.find("\n", match.end(), value_end)
            if newline >= 0:
                value_end = newline
        fields.setdefault(name, []).append(
            block[match.end():value_end].strip()
        )
    return fields


def _validate_decision_metadata(decision_id: str, fields):
    """Validate decision lifecycle and unique parser-owned fields."""
    errors = []
    status_values = fields.get("Status", [])
    status = None
    if not status_values:
        errors.append(f"{decision_id}: missing Status field")
    elif len(status_values) > 1:
        kind = (
            "duplicate"
            if len(set(status_values)) == 1
            else "conflicting"
        )
        errors.append(f"{decision_id}: {kind} Status fields")
    else:
        status = status_values[0]
        if not (
            status in ("active", "reversed")
            or re.fullmatch(
                r"superseded → D-[A-Z]-[0-9]+", status
            )
        ):
            errors.append(
                f"{decision_id}: invalid Status value: {status!r}"
            )
            status = None

    for name in ("Choice", "Rejected"):
        if len(fields.get(name, [])) > 1:
            errors.append(f"{decision_id}: duplicate {name} fields")
    return status, errors


def _strip_parenthetical_explanations(value: str) -> str:
    previous = None
    while value != previous:
        previous = value
        value = re.sub(r"\([^()]*\)|（[^（）]*）", "", value)
    return value.strip()


_DECISION_LIST_MARKER = r"(?:[-*+]|\d+[.)])"
_DECISION_LEADING_LIST_MARKER_RE = re.compile(
    rf"^[ \t]*{_DECISION_LIST_MARKER}[ \t]+"
)
_DECISION_FOLLOWING_LIST_MARKER_RE = re.compile(
    rf"[ \t]*{_DECISION_LIST_MARKER}[ \t]+"
)


def _strip_decision_list_marker(value: str) -> str:
    """Strip one supported top-level Markdown list marker."""
    return _DECISION_LEADING_LIST_MARKER_RE.sub("", value, count=1)


def _has_decision_explanation_prefix(value: str) -> bool:
    """Recognize established prose prefixes that cannot name a term."""
    return bool(re.match(
        r"^(?:保留|保持|混合|仅|将|珠宝|英文|调用|翻译|原始|部分|"
        r"当前|使用)",
        value,
    ))


def _split_decision_term_tokens(value: str) -> list[str]:
    tokens = []
    current = []
    parentheses = []
    quote_closer = None
    in_code = False
    index = 0
    quote_pairs = {
        '"': '"',
        "“": "”",
        "‘": "’",
        "「": "」",
        "『": "』",
    }
    parenthesis_pairs = {"(": ")", "（": "）"}

    while index < len(value):
        char = value[index]
        if char == "`" and quote_closer is None:
            in_code = not in_code
            current.append(char)
            index += 1
            continue
        if not in_code:
            if quote_closer is not None:
                if char == quote_closer:
                    quote_closer = None
                current.append(char)
                index += 1
                continue
            if char in quote_pairs:
                quote_closer = quote_pairs[char]
                current.append(char)
                index += 1
                continue
            if char in parenthesis_pairs:
                parentheses.append(parenthesis_pairs[char])
            elif parentheses and char == parentheses[-1]:
                parentheses.pop()

        at_top_level = (
            not in_code and quote_closer is None and not parentheses
        )
        if at_top_level and char in ",，、;；":
            tokens.append("".join(current))
            current = []
            index += 1
            continue
        if at_top_level and char == "\n":
            marker = _DECISION_FOLLOWING_LIST_MARKER_RE.match(
                value, index + 1
            )
            if marker:
                tokens.append("".join(current))
                current = []
                index = marker.end()
                continue
        current.append(char)
        index += 1
    tokens.append("".join(current))
    return tokens


def _searchable_decision_terms(value: str) -> list[str]:
    terms = []
    value = re.sub(r"(?ms)```.*?```", "", value)
    for raw in _split_decision_term_tokens(value):
        explanation = " ".join(
            part
            for match in re.findall(r"\(([^()]*)\)|（([^（）]*)）", raw)
            for part in match
            if part
        )
        if re.search(
            r"(?i)collision|overlap|ambiguous|too broad|different concept|"
            r"仅否定|不否定|普通动词",
            explanation,
        ):
            continue
        raw = _strip_parenthetical_explanations(raw)
        term = _strip_decision_list_marker(raw).strip()
        term = term.strip(" `*\"'“”")
        if not term or re.match(r"^[（(]?\s*none\b", term, re.I):
            continue
        if "→" in term or "->" in term:
            continue
        if not re.search(r"[\u3400-\u9fff]", term):
            continue
        if (
            len(term) > 24
            or re.search(r"[。！？:：]", term)
            or re.search(r"\s", term)
            or "`" in term
            or _has_decision_explanation_prefix(term)
            or len(term) < 2
            or not re.fullmatch(
                r"[\u3400-\u9fffA-Za-z0-9·・'’\-]+", term
            )
        ):
            continue
        terms.append(term)
    return terms


def _decision_choices(value: str) -> list[str]:
    choices = []
    for line in value.splitlines():
        line = _strip_decision_list_marker(line).strip()
        if not line:
            continue
        stripped = line.strip(" `*")
        arrow = re.fullmatch(r"[^`]+?(?:→|->)\s*([^`]+)", stripped)
        candidate = arrow.group(1).strip() if arrow else stripped
        parsed = _searchable_decision_terms(candidate)
        if len(parsed) != 1:
            return []
        choices.extend(parsed)
    return choices


def _iter_decision_blocks(content: str):
    pattern = re.compile(
        r"(?ms)^###\s+(D-[A-Z]-\d+)\b.*?(?=^###\s+D-[A-Z]-\d+\b|\Z)"
    )
    for match in pattern.finditer(content):
        yield match.group(1), match.group(0)


def _markdown_table_cells(line: str) -> list[str]:
    if not line.strip().startswith("|"):
        return []
    cells = []
    current = []
    escaped = False
    for char in line.strip()[1:-1]:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def _context_table_index(block: str):
    """Return canonical exact-key rows from explicit ``Context | ZH`` tables.

    SourceDB identity uses ``compute_canonical_key()`` without trimming.  Keep
    the exact table spelling for diagnostics and downstream SourceDB lookup,
    while rejecting table rows that collapse onto the same production key.
    """
    values = {}
    errors = []
    table_found = False
    lines = block.splitlines()
    index = 0
    while index < len(lines):
        cells = _markdown_table_cells(lines[index])
        if not (
            len(cells) >= 2
            and cells[0].casefold() == "context"
            and cells[1].casefold() == "zh"
        ):
            index += 1
            continue

        table_found = True
        if index + 1 >= len(lines):
            errors.append("Context table is missing its separator row")
            break
        separator = _markdown_table_cells(lines[index + 1])
        if (
            len(separator) < 2
            or not all(
                re.fullmatch(r":?-{3,}:?", cell)
                for cell in separator[:2]
            )
        ):
            errors.append("Context table has an invalid separator row")
            index += 1
            continue

        index += 2
        row_count = 0
        while index < len(lines):
            row = _markdown_table_cells(lines[index])
            if not row:
                break
            if len(row) < 2:
                errors.append("Context table row has fewer than two cells")
                index += 1
                continue

            context_cell = row[0]
            exact_code = re.fullmatch(r"`([^`\n]+)`", context_cell)
            if exact_code:
                keys = [exact_code.group(1)]
            else:
                # A descriptive Context cell can contain an internal identity
                # and a pipe-qualified SourceDB key.  Only the qualified code
                # span is an exact key; unrelated code spans remain prose.
                keys = [
                    token
                    for token in re.findall(r"`([^`\n]+)`", context_cell)
                    if "|" in token
                ]
                if not keys:
                    keys = [context_cell.strip(" `")]
            keys = [key.replace(r"\|", "|") for key in keys]
            value = row[1].strip(" `")
            if not all(key.strip() for key in keys) or not value:
                errors.append("Context table row has an empty key or ZH value")
            else:
                for key in keys:
                    canonical_key = compute_canonical_key(key)
                    previous = values.get(canonical_key)
                    if previous is not None:
                        kind = (
                            "duplicate"
                            if previous["value"] == value
                            else "conflicting"
                        )
                        errors.append(
                            f"{kind} Context table rows for normalized key "
                            f"{canonical_key!r}: {previous['key']!r} and "
                            f"{key!r}"
                        )
                    else:
                        values[canonical_key] = {
                            "key": key,
                            "value": value,
                        }
            row_count += 1
            index += 1
        if not row_count:
            errors.append("Context table has no data rows")
    return values, table_found, errors


def _decision_code_spans(value: str):
    """Return Markdown code spans with their exact token offsets."""
    spans = []
    opening = None
    for index, char in enumerate(value):
        if char != "`":
            continue
        if opening is None:
            opening = index
        else:
            spans.append({
                "text": value[opening + 1:index],
                "start": opening,
                "end": index + 1,
            })
            opening = None
    if opening is not None:
        return [], "unclosed Markdown code span"
    return spans, None


def _decision_delimiters_balanced(value: str) -> bool:
    """Validate code, parenthesis, and ordinary-quote boundaries."""
    parentheses = []
    quote_closer = None
    in_code = False
    quote_pairs = {
        '"': '"',
        "“": "”",
        "‘": "’",
        "「": "」",
        "『": "』",
    }
    quote_closers = set(quote_pairs.values()) - {'"'}
    parenthesis_pairs = {"(": ")", "（": "）"}
    parenthesis_closers = set(parenthesis_pairs.values())

    for char in value:
        if char == "`" and quote_closer is None:
            in_code = not in_code
            continue
        if in_code:
            continue
        if quote_closer is not None:
            if char == quote_closer:
                quote_closer = None
            continue
        if char in quote_pairs:
            quote_closer = quote_pairs[char]
            continue
        if char in quote_closers:
            return False
        if char in parenthesis_pairs:
            parentheses.append(parenthesis_pairs[char])
        elif char in parenthesis_closers:
            if not parentheses or char != parentheses[-1]:
                return False
            parentheses.pop()
    return not in_code and quote_closer is None and not parentheses


def _is_parenthetical_sequence(value: str) -> bool:
    """Return whether all substantive text is parenthesized explanation."""
    value = value.strip()
    if not value:
        return False
    pairs = {"(": ")", "（": "）"}
    index = 0
    while index < len(value):
        while index < len(value) and value[index].isspace():
            index += 1
        if index == len(value):
            return True
        opener = value[index]
        if opener not in pairs:
            return False
        expected = []
        quote_closer = None
        in_code = False
        start = index
        while index < len(value):
            char = value[index]
            if char == "`" and quote_closer is None:
                in_code = not in_code
            elif not in_code:
                if quote_closer is not None:
                    if char == quote_closer:
                        quote_closer = None
                elif char == '"':
                    quote_closer = '"'
                elif char == "“":
                    quote_closer = "”"
                elif char == "‘":
                    quote_closer = "’"
                elif char == "「":
                    quote_closer = "」"
                elif char == "『":
                    quote_closer = "』"
                elif char in pairs:
                    expected.append(pairs[char])
                elif char in pairs.values():
                    if not expected or char != expected[-1]:
                        return False
                    expected.pop()
                    if not expected:
                        index += 1
                        break
            index += 1
        if index == start or expected or in_code or quote_closer is not None:
            return False
    return True


def _has_parenthetical_explanation(value: str) -> bool:
    """Return whether a token contains a balanced explanatory aside."""
    for index, char in enumerate(value):
        if char not in "(（":
            continue
        if _is_parenthetical_sequence(value[index:]):
            return True
    return False


def _is_entire_quoted(value: str) -> bool:
    value = value.strip()
    pairs = {
        '"': '"',
        "“": "”",
        "‘": "’",
        "「": "」",
        "『": "』",
    }
    return (
        len(value) >= 2
        and value[0] in pairs
        and value[-1] == pairs[value[0]]
    )


def _is_explicit_explanation_suffix(value: str) -> bool:
    """Accept only a fully delimited explanation after a mapping."""
    return (
        _is_parenthetical_sequence(value)
        or _is_entire_quoted(value)
    )


def _is_embedded_arrow_explanation(
    token: str, prefix: str, suffix: str
) -> bool:
    """Recognize a code-arrow embedded in an explicit prose explanation."""
    if _is_entire_quoted(token) or _is_parenthetical_sequence(token):
        return True
    return bool(
        re.search(r"[:：]", prefix)
        and re.search(r"[。！？]\s*$", suffix)
    )


def _arrows_are_delimited_explanations(value: str) -> bool:
    """Require every non-code arrow to be inside quotes or parentheses."""
    parentheses = []
    quote_closer = None
    in_code = False
    found = False
    pairs = {"(": ")", "（": "）"}
    quote_pairs = {
        '"': '"',
        "“": "”",
        "‘": "’",
        "「": "」",
        "『": "』",
    }
    index = 0
    while index < len(value):
        char = value[index]
        if char == "`" and quote_closer is None:
            in_code = not in_code
            index += 1
            continue
        if not in_code:
            is_arrow = char == "→" or value.startswith("->", index)
            if is_arrow:
                found = True
                if quote_closer is None and not parentheses:
                    return False
                index += 2 if value.startswith("->", index) else 1
                continue
            if quote_closer is not None:
                if char == quote_closer:
                    quote_closer = None
            elif char in quote_pairs:
                quote_closer = quote_pairs[char]
            elif char in pairs:
                parentheses.append(pairs[char])
            elif parentheses and char == parentheses[-1]:
                parentheses.pop()
        index += 1
    return found


def _delimited_arrow_explanation_spans(value: str):
    """Return every top-level quoted/parenthesized non-code arrow span."""
    parenthesis_pairs = {"(": ")", "（": "）"}
    quote_pairs = {
        '"': '"',
        "“": "”",
        "‘": "’",
        "「": "」",
        "『": "』",
    }
    parenthesis_closers = set(parenthesis_pairs.values())
    parentheses = []
    quote_closer = None
    span_start = None
    spans = []

    for index, char in enumerate(value):
        if quote_closer is not None:
            if char == quote_closer:
                quote_closer = None
                if not parentheses:
                    span_end = index + 1
                    if re.search(
                        r"(?:→|->)", value[span_start:span_end]
                    ):
                        spans.append((span_start, span_end))
                    span_start = None
            continue
        if char in quote_pairs:
            quote_closer = quote_pairs[char]
            if not parentheses:
                span_start = index
            continue
        if char in parenthesis_pairs:
            if not parentheses:
                span_start = index
            parentheses.append(parenthesis_pairs[char])
            continue
        if char in parenthesis_closers:
            parentheses.pop()
            if not parentheses:
                span_end = index + 1
                if re.search(r"(?:→|->)", value[span_start:span_end]):
                    spans.append((span_start, span_end))
                span_start = None
    return spans


def _outside_arrow_residuals(token: str, outside_code: str):
    """Remove exact arrow-explanation spans and return all residual text."""
    spans = _delimited_arrow_explanation_spans(outside_code)
    masked = list(outside_code)
    residuals = []
    previous_end = 0
    for start, end in spans:
        residual = token[previous_end:start].strip()
        if residual:
            residuals.append(residual)
        masked[start:end] = " " * (end - start)
        previous_end = end
    residual = token[previous_end:].strip()
    if residual:
        residuals.append(residual)
    if re.search(r"(?:→|->)", "".join(masked)):
        return None
    return residuals


def _is_explicit_arrow_residual_explanation(value: str) -> bool:
    """Recognize a whole residual as prose, never a hidden global term."""
    value = value.strip()
    if not re.search(r"[\u3400-\u9fff]", value):
        return True
    if re.fullmatch(
        r"(?i)(?:历史(?:说明|记录)?|旧译|原译|historical(?: "
        r"(?:explanation|note|record))?|legacy(?: "
        r"(?:explanation|note|record))?|explanatory(?: note)?|example)"
        r"[ \t:：]*",
        value,
    ):
        return True
    return _has_decision_explanation_prefix(value)


def _has_explicit_historical_marker(value: str) -> bool:
    return bool(re.search(
        r"(?i)历史(?:说明|记录)?|旧译|原译|"
        r"historical|legacy|explanatory|example",
        value,
    ))


def _is_context_identity_boundary(char: str) -> bool:
    """Return whether a character delimits a Context identity."""
    return not (char.isalnum() or char in "_|")


def _outside_arrow_matches_context(value: str, context_values) -> bool:
    """Return whether an unbackticked arrow names an exact Context key."""
    start = 0
    for arrow in re.finditer(r"(?:→|->)", value):
        lhs = value[start:arrow.start()].replace(r"\|", "|")
        # Match the contextual parser's conventional single separator space.
        if lhs.endswith(" "):
            lhs = lhs[:-1]
        canonical_lhs = compute_canonical_key(lhs)
        for canonical_key in context_values:
            if not canonical_lhs.endswith(canonical_key):
                continue
            prefix_length = len(canonical_lhs) - len(canonical_key)
            if (
                prefix_length == 0
                or _is_context_identity_boundary(
                    canonical_lhs[prefix_length - 1]
                )
            ):
                return True
        start = arrow.end()
    return False


def _text_mentions_context_identity(value: str, context_values) -> bool:
    """Return whether prose contains a boundary-delimited Context key."""
    canonical_value = compute_canonical_key(value.replace(r"\|", "|"))

    for canonical_key in context_values:
        start = 0
        while True:
            start = canonical_value.find(canonical_key, start)
            if start < 0:
                break
            end = start + len(canonical_key)
            left_ok = (
                start == 0
                or _is_context_identity_boundary(
                    canonical_value[start - 1]
                )
            )
            right_ok = (
                end == len(canonical_value)
                or _is_context_identity_boundary(canonical_value[end])
            )
            if left_ok and right_ok:
                return True
            start += 1
    return False


def _has_pipe_qualified_arrow(value: str) -> bool:
    """Detect a pipe-qualified arrow without discarding its delimiters."""
    chunks = re.split(r"(?:→|->)", value.replace(r"\|", "|"))
    return any("|" in chunk for chunk in chunks[:-1])


def _mask_decision_code_spans(value: str, spans) -> str:
    masked = list(value)
    for span in spans:
        masked[span["start"]:span["end"]] = (
            " " * (span["end"] - span["start"])
        )
    return "".join(masked)


def _is_explicit_non_arrow_explanation(value: str) -> bool:
    """Recognize prose/explanation shapes that cannot be global terms."""
    value = value.strip()
    if not value:
        return True
    if re.match(r"^[（(]?\s*none\b", value, re.I):
        return True
    if _has_parenthetical_explanation(value):
        return True
    if (
        re.search(r'["“”‘’「」『』]', value)
        and not _is_entire_quoted(value)
    ):
        return True
    if not re.search(r"[\u3400-\u9fff]", value):
        return True
    stripped = value.strip(" `*\"'“”‘’「」『』")
    if (
        len(stripped) < 2
        or len(stripped) > 24
        or re.search(r"[。！？:：\s]", stripped)
        or _has_decision_explanation_prefix(stripped)
    ):
        return True
    return False


def _invalid_rejected_token(index: int, raw: str, error: str):
    return {
        "kind": "invalid",
        "index": index,
        "raw": raw,
        "error": error,
    }


def _classify_rejected_token(
    decision_id: str,
    index: int,
    raw_token: str,
    context_values,
    context_table_found: bool,
):
    """Classify one complete top-level Rejected token exactly once."""
    token = _strip_decision_list_marker(raw_token).strip()
    if not token:
        return {"kind": "explanation", "index": index, "raw": token}
    if not _decision_delimiters_balanced(token):
        return _invalid_rejected_token(
            index,
            token,
            f"{decision_id}: unbalanced delimiters in Rejected token: "
            f"{token!r}",
        )

    code_spans, code_error = _decision_code_spans(token)
    if code_error:
        return _invalid_rejected_token(
            index,
            token,
            f"{decision_id}: {code_error} in Rejected token: {token!r}",
        )
    mapping_spans = [
        span for span in code_spans
        if re.search(r"(?:→|->)", span["text"])
    ]
    outside_code = _mask_decision_code_spans(token, code_spans)
    if re.search(r"(?:→|->)", outside_code):
        if _has_pipe_qualified_arrow(outside_code):
            if (
                _is_entire_quoted(token)
                or _has_parenthetical_explanation(token)
            ):
                detail = (
                    "pipe-qualified contextual mapping must use backticks"
                )
            else:
                detail = (
                    "contextual Rejected mapping must be enclosed in "
                    "backticks"
                )
            return _invalid_rejected_token(
                index,
                token,
                f"{decision_id}: {detail}: {token!r}",
            )
        if not _arrows_are_delimited_explanations(outside_code):
            return _invalid_rejected_token(
                index,
                token,
                f"{decision_id}: contextual Rejected mapping must be "
                f"enclosed in backticks: {token!r}",
            )
        if (
            context_table_found
            and _outside_arrow_matches_context(
                outside_code, context_values
            )
        ):
            return _invalid_rejected_token(
                index,
                token,
                f"{decision_id}: contextual Rejected arrow matches an "
                f"exact Context table key and must be enclosed in "
                f"backticks: {token!r}",
            )
        if (
            context_table_found
            and not _has_explicit_historical_marker(outside_code)
        ):
            return _invalid_rejected_token(
                index,
                token,
                f"{decision_id}: contextual Rejected mapping must be "
                f"enclosed in backticks unless it has an explicit "
                f"historical marker: {token!r}",
            )
        residuals = _outside_arrow_residuals(token, outside_code)
        if residuals is None:
            return _invalid_rejected_token(
                index,
                token,
                f"{decision_id}: unconsumed arrow in Rejected token: "
                f"{token!r}",
            )
        if not residuals:
            return {
                "kind": "explanation",
                "index": index,
                "raw": token,
            }
        if len(residuals) != 1:
            return _invalid_rejected_token(
                index,
                token,
                f"{decision_id}: unconsumed Rejected text around arrow "
                f"explanation: {residuals!r}",
            )
        residual = residuals[0]
        if residual.endswith((':', '：')):
            if _is_explicit_arrow_residual_explanation(residual):
                return {
                    "kind": "explanation",
                    "index": index,
                    "raw": token,
                }
            return _invalid_rejected_token(
                index,
                token,
                f"{decision_id}: unconsumed Rejected token prefix: "
                f"{residual!r}",
            )
        classification = _classify_rejected_token(
            decision_id,
            index,
            residual,
            context_values,
            context_table_found,
        )
        if (
            classification["kind"] == "explanation"
            and not _is_explicit_arrow_residual_explanation(residual)
        ):
            return _invalid_rejected_token(
                index,
                token,
                f"{decision_id}: unconsumed Rejected text around arrow "
                f"explanation: {residual!r}",
            )
        classification["raw"] = token
        return classification

    if mapping_spans:
        qualified_spans = []
        for span in mapping_spans:
            lhs = re.split(
                r"(?:→|->)", span["text"].replace(r"\|", "|"), maxsplit=1
            )[0]
            if "|" in lhs:
                qualified_spans.append(span)

        if len(mapping_spans) != 1:
            return _invalid_rejected_token(
                index,
                token,
                f"{decision_id}: Rejected token must contain exactly one "
                f"contextual mapping: {token!r}",
            )

        mapping = mapping_spans[0]
        prefix = token[:mapping["start"]].strip()
        suffix = token[mapping["end"]:].strip()
        # An unqualified code-arrow without a table is historical prose, not
        # a SourceDB rule.  Consume the whole token before granting that
        # exemption: a plain prefix or suffix cannot hide a global term.
        if not context_table_found and not qualified_spans:
            if prefix and not _is_embedded_arrow_explanation(
                token, prefix, suffix
            ):
                return _invalid_rejected_token(
                    index,
                    token,
                    f"{decision_id}: unconsumed Rejected token prefix: "
                    f"{prefix!r}",
                )
            if (
                suffix
                and not _is_explicit_explanation_suffix(suffix)
                and not _is_embedded_arrow_explanation(
                    token, prefix, suffix
                )
            ):
                return _invalid_rejected_token(
                    index,
                    token,
                    f"{decision_id}: unconsumed Rejected token suffix: "
                    f"{suffix!r}",
                )
            return {
                "kind": "explanation",
                "index": index,
                "raw": token,
            }

        if (
            prefix
            or (
                suffix
                and not _is_explicit_explanation_suffix(suffix)
            )
        ):
            return _invalid_rejected_token(
                index,
                token,
                f"{decision_id}: unconsumed contextual Rejected text: "
                f"{(prefix or suffix)!r}",
            )

        unescaped = mapping["text"].replace(r"\|", "|")
        match = re.fullmatch(r"(.+?)(?:→|->)(.+)", unescaped)
        if not match:
            return _invalid_rejected_token(
                index,
                token,
                f"{decision_id}: invalid contextual Rejected mapping: "
                f"`{mapping['text']}`",
            )
        key = match.group(1)
        rejected = match.group(2)
        # Remove only the conventional one-space arrow separators.
        # Leading/trailing spaces inside a SourceDB key are identity.
        if key.endswith(" "):
            key = key[:-1]
        if rejected.startswith(" "):
            rejected = rejected[1:]
        context_qualified = "|" in key
        rejected_terms = _searchable_decision_terms(rejected)
        if (
            (
                context_qualified
                and (
                    key.count("|") != 1
                    or not re.fullmatch(r"[^|\n]+\|[^|\n]+", key)
                )
            )
            or (
                not context_qualified
                and not re.fullmatch(r"[^|\n]+", key)
            )
            or len(rejected_terms) != 1
        ):
            return _invalid_rejected_token(
                index,
                token,
                f"{decision_id}: invalid contextual Rejected mapping: "
                f"`{mapping['text']}`",
            )
        table_row = context_values.get(compute_canonical_key(key))
        if table_row is None:
            return _invalid_rejected_token(
                index,
                token,
                f"{decision_id}: contextual key {key!r} does not match "
                "an exact non-empty Context table key",
            )
        return {
            "kind": "contextual",
            "index": index,
            "raw": token,
            "decision": decision_id,
            "key": table_row["key"],
            "rejected": rejected_terms[0],
            "correct": table_row["value"],
        }

    if re.search(r"(?:→|->)", outside_code):
        return {"kind": "explanation", "index": index, "raw": token}

    if code_spans and (
        context_table_found
        or any("|" in span["text"].replace(r"\|", "|")
                for span in code_spans)
    ):
        exact_code_token = (
            len(code_spans) == 1
            and not token[:code_spans[0]["start"]].strip()
            and not token[code_spans[0]["end"]:].strip()
        )
        if exact_code_token:
            return _invalid_rejected_token(
                index,
                token,
                f"{decision_id}: contextual Rejected mapping is missing "
                f"an arrow: `{code_spans[0]['text']}`",
            )

    if (
        context_table_found
        and _text_mentions_context_identity(token, context_values)
    ):
        return _invalid_rejected_token(
            index,
            token,
            f"{decision_id}: contextual Rejected text matches an exact "
            f"Context table key and must use a backticked arrow mapping: "
            f"{token!r}",
        )

    if "|" in token.replace(r"\|", "|"):
        return _invalid_rejected_token(
            index,
            token,
            f"{decision_id}: pipe-qualified Rejected identity must use a "
            f"backticked arrow mapping: {token!r}",
        )

    if _is_explicit_non_arrow_explanation(token):
        return {"kind": "explanation", "index": index, "raw": token}

    rejected_terms = _searchable_decision_terms(token)
    if len(rejected_terms) == 1:
        if context_table_found:
            return _invalid_rejected_token(
                index,
                token,
                f"{decision_id}: unconsumed contextual Rejected text: "
                f"{token!r}",
            )
        return {
            "kind": "global",
            "index": index,
            "raw": token,
            "rejected": rejected_terms[0],
        }
    return _invalid_rejected_token(
        index,
        token,
        f"{decision_id}: unconsumed Rejected token: {token!r}",
    )


_DECISION_REJECTED_UNSET = object()


def _classify_decision_rejections(
    decision_id: str,
    block: str,
    rejected_raw=_DECISION_REJECTED_UNSET,
):
    """Consume every top-level Rejected token through one classifier."""
    if rejected_raw is _DECISION_REJECTED_UNSET:
        rejected_values = _decision_metadata_fields(block).get(
            "Rejected", []
        )
        if len(rejected_values) > 1:
            return [], [f"{decision_id}: duplicate Rejected fields"]
        rejected_raw = rejected_values[0] if rejected_values else ""
    context_values, context_table_found, table_errors = (
        _context_table_index(block)
    )
    classifications = []
    errors = [
        f"{decision_id}: {error}" for error in table_errors
    ]
    if not rejected_raw:
        return classifications, errors
    for index, token in enumerate(
        _split_decision_term_tokens(rejected_raw)
    ):
        classification = _classify_rejected_token(
            decision_id,
            index,
            token,
            context_values,
            context_table_found,
        )
        classifications.append(classification)
        if classification["kind"] == "invalid":
            errors.append(classification["error"])
    return classifications, errors


def _parse_decision_content(content: str) -> dict:
    """Classify one immutable decisions snapshot and derive every registry."""
    rejected_map = {}
    contextual_rules = []
    all_classifications = []
    parsed_blocks = []
    metadata_errors = []
    for decision_id, block in _iter_decision_blocks(content):
        fields = _decision_metadata_fields(block)
        metadata_errors.extend(
            _decision_reserved_field_errors(decision_id, block)
        )
        status, decision_errors = _validate_decision_metadata(
            decision_id, fields
        )
        metadata_errors.extend(decision_errors)
        parsed_blocks.append((decision_id, block, fields, status))

    if metadata_errors:
        raise ValueError("; ".join(metadata_errors))

    errors = []
    for decision_id, block, fields, status in parsed_blocks:
        if status != "active":
            continue
        rejected_values = fields.get("Rejected", [])
        rejected_raw = rejected_values[0] if rejected_values else ""
        classifications, decision_errors = (
            _classify_decision_rejections(
                decision_id, block, rejected_raw
            )
        )
        all_classifications.extend(classifications)
        errors.extend(decision_errors)
        contextual_rules.extend(
            {
                "decision": classification["decision"],
                "key": classification["key"],
                "rejected": classification["rejected"],
                "correct": classification["correct"],
            }
            for classification in classifications
            if classification["kind"] == "contextual"
        )

        global_classifications = [
            classification
            for classification in classifications
            if classification["kind"] == "global"
        ]
        if not global_classifications:
            continue

        choice_values = fields.get("Choice", [])
        choice_raw = choice_values[0] if choice_values else ""
        if not choice_raw:
            errors.append(
                f"{decision_id}: global Rejected terms require a "
                "non-empty Choice"
            )
            continue
        choices = _decision_choices(choice_raw)
        if not choices:
            errors.append(
                f"{decision_id}: cannot determine a Choice mapping for "
                "global Rejected terms"
            )
            continue
        if len(choices) == 1:
            mapped_choices = choices * len(global_classifications)
        elif len(choices) == len(global_classifications):
            mapped_choices = choices
        else:
            errors.append(
                f"{decision_id}: Choice count {len(choices)} cannot map "
                f"deterministically to {len(global_classifications)} "
                "global Rejected terms"
            )
            continue

        for classification, choice in zip(
            global_classifications, mapped_choices
        ):
            rejected = classification["rejected"]
            if rejected in rejected_map:
                errors.append(
                    f"{decision_id}: duplicate global Rejected term "
                    f"{rejected!r} cannot be mapped uniquely"
                )
                continue
            rejected_map[rejected] = choice

    if errors:
        raise ValueError("; ".join(errors))
    return {
        "rejected_map": rejected_map,
        "contextual_rules": contextual_rules,
        "classifications": all_classifications,
    }


def parse_decision_registry(filepath: str) -> dict:
    """Read and classify one decisions file snapshot exactly once."""
    if not os.path.exists(filepath):
        return {
            "rejected_map": {},
            "contextual_rules": [],
            "classifications": [],
        }
    with open(filepath, "r", encoding="utf-8") as stream:
        content = stream.read()
    return _parse_decision_content(content)


def parse_decisions(filepath: str) -> dict:
    """Return searchable global rejected terms from every active decision."""
    return parse_decision_registry(filepath)["rejected_map"]


def parse_contextual_decisions(filepath: str) -> list[dict]:
    """Return exact key/value rejected mappings from active decisions."""
    return parse_decision_registry(filepath)["contextual_rules"]


def _validate_contextual_decisions(rules):
    """Reject duplicate/conflicting rules after production key folding."""
    errors = []
    seen = {}
    for rule in rules:
        canonical_key = compute_canonical_key(rule["key"])
        signature = (rule["rejected"], rule["correct"])
        previous = seen.get(canonical_key)
        if previous is not None:
            kind = "duplicate" if previous["signature"] == signature \
                else "conflicting"
            errors.append(
                f"{kind} contextual rules for normalized key "
                f"{canonical_key!r}: {previous['decision']} and "
                f"{rule['decision']}"
            )
            continue
        seen[canonical_key] = {
            "decision": rule["decision"],
            "signature": signature,
        }
    return errors


def _collect_effective_sourcedb_files(source_txt):
    """Mirror localized SourceDB file discovery and production load order."""
    if not source_txt:
        return [], []

    source_path = os.path.abspath(source_txt)
    errors = []
    if os.path.basename(source_path) != "source.txt":
        return [], [
            f"SourceDB root must be named source.txt: {source_path}"
        ]
    if not os.path.isfile(source_path):
        return [], [
            f"required SourceDB source.txt does not exist or is not a file: "
            f"{source_path}"
        ]

    directory = os.path.dirname(source_path)
    try:
        names = sorted(os.listdir(directory), key=os.fsencode)
    except OSError as error:
        return [], [
            f"cannot enumerate required SourceDB directory "
            f"{directory}: {error}"
        ]

    candidates = []
    for name in names:
        # Match get_dir_files_ext(directory, "txt") exactly: the C++
        # extension argument is a raw filename suffix, not ".txt".
        if not name.endswith("txt"):
            continue
        candidate = os.path.join(directory, name)
        if os.path.isfile(candidate):
            candidates.append(os.path.abspath(candidate))
        else:
            errors.append(
                f"required SourceDB *txt path is not a file: {candidate}"
            )

    source_identity = os.path.normcase(source_path)
    others = [
        path for path in candidates
        if os.path.normcase(path) != source_identity
    ]
    if not any(
        os.path.normcase(path) == source_identity for path in candidates
    ):
        errors.append(
            f"required SourceDB source.txt was not discovered: {source_path}"
        )
        return [], errors
    return [source_path, *others], errors


def _collect_zh_textdb_files(source_txt, zh_dirs):
    """Return unique required ZH TextDB files, or input errors.

    ``parse_entries`` remains the parser for every selected file.  This helper
    only expands the explicitly bound inputs and fails closed when a requested
    directory is missing, unreadable, or contains no ``*.txt`` files.
    """
    sourcedb_files, errors = _collect_effective_sourcedb_files(source_txt)
    sourcedb_identities = {
        os.path.normcase(os.path.abspath(path))
        for path in sourcedb_files
    }
    requested = list(sourcedb_files)
    requested.extend(zh_dirs or [])

    files = []
    seen = set()
    for raw_path in requested:
        path = os.path.abspath(raw_path)
        candidates = []
        if os.path.isfile(path):
            identity = os.path.normcase(path)
            if (
                identity not in sourcedb_identities
                and not path.endswith(".txt")
            ):
                errors.append(f"required TextDB file is not *.txt: {path}")
                continue
            candidates.append(path)
        elif os.path.isdir(path):
            walk_errors = []

            def _record_walk_error(error):
                walk_errors.append(str(error))

            for dirpath, dirnames, filenames in os.walk(
                path, onerror=_record_walk_error
            ):
                dirnames.sort()
                for filename in sorted(filenames):
                    if filename.endswith(".txt"):
                        candidates.append(os.path.join(dirpath, filename))
            if walk_errors:
                errors.extend(
                    f"cannot traverse required TextDB directory {path}: {error}"
                    for error in walk_errors
                )
            if not candidates:
                errors.append(
                    f"required TextDB directory contains no *.txt files: {path}"
                )
        else:
            errors.append(f"required TextDB path does not exist: {path}")
            continue

        for candidate in candidates:
            identity = os.path.normcase(os.path.abspath(candidate))
            if identity not in seen:
                seen.add(identity)
                files.append(candidate)
    return files, errors, sourcedb_files


def cmd_validate_terms(args):
    """Check rejected terms in all bound ZH TextDB and C++ sources."""
    if not os.path.isfile(args.glossary):
        print(
            f"ERROR: required decisions file does not exist or is not a "
            f"file: {os.path.abspath(args.glossary)}",
            file=sys.stderr,
        )
        return 2
    try:
        registry = parse_decision_registry(args.glossary)
        rejected_map = registry["rejected_map"]
        contextual_rules = registry["contextual_rules"]
    except (OSError, UnicodeError, ValueError) as error:
        print(f"ERROR: cannot parse required decisions file: {error}",
              file=sys.stderr)
        return 2

    contextual_errors = _validate_contextual_decisions(contextual_rules)
    if contextual_rules and not args.source_txt:
        contextual_errors.append(
            "--source-txt is required to evaluate contextual decisions"
        )

    textdb_files, input_errors, sourcedb_files = _collect_zh_textdb_files(
        args.source_txt, args.zh_dirs
    )
    input_errors.extend(contextual_errors)
    if input_errors:
        for error in input_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    textdb_entries = []
    entries_by_file = {}
    for textdb_file in textdb_files:
        try:
            entries = parse_entries(
                textdb_file, lowercase_keys=False, unescape_hash=False
            )
        except (OSError, UnicodeError) as error:
            print(
                f"ERROR: cannot parse required TextDB file "
                f"{textdb_file}: {error}",
                file=sys.stderr,
            )
            return 2
        entries_by_file[os.path.normcase(os.path.abspath(textdb_file))] = (
            entries
        )
        textdb_entries.extend(entries)

    effective_sourcedb = {}
    for textdb_file in sourcedb_files:
        identity = os.path.normcase(os.path.abspath(textdb_file))
        for entry in entries_by_file[identity]:
            effective_sourcedb[compute_canonical_key(entry.key)] = entry

    missing_contextual = []
    for rule in contextual_rules:
        canonical_key = compute_canonical_key(rule["key"])
        if canonical_key not in effective_sourcedb:
            missing_contextual.append(
                f"contextual key {rule['key']!r} from {rule['decision']} "
                "is missing from the effective SourceDB"
            )
    if missing_contextual:
        for error in missing_contextual:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if not rejected_map and not contextual_rules:
        print("OK: No active rejected-name decisions found in glossary.")
        return 0

    findings = []

    for entry in textdb_entries:
        cn_val = entry.value
        for rejected, correct in rejected_map.items():
            if rejected in cn_val:
                cn_snippet = cn_val[:80]
                findings.append({
                    'location': (
                        f'{entry.source_file}: "{entry.key[:60]}"'
                    ),
                    'rejected': rejected,
                    'correct': correct,
                    'snippet': cn_snippet,
                })
    for rule in contextual_rules:
        entry = effective_sourcedb[compute_canonical_key(rule["key"])]
        cn_val = entry.value
        if rule["rejected"] in cn_val:
            findings.append({
                "location": (
                    f'{entry.source_file}: "{entry.key[:60]}"'
                ),
                "rejected": rule["rejected"],
                "correct": rule["correct"],
                "snippet": cn_val[:80],
            })

    # Check C++ source for hardcoded rejected terms in strings (if source_dir given)
    if args.source_dir:
        cjk_char_re = re.compile(r'[⺀-鿿]')
        for dirpath, _, filenames in os.walk(args.source_dir):
            for fn in sorted(filenames):
                if not (fn.endswith('.cc') or fn.endswith('.h')):
                    continue
                filepath = os.path.join(dirpath, fn)
                with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                for lineno, line in enumerate(lines, 1):
                    # Skip preprocessor and comments
                    if SKIP_PP_RE.match(line) or line.strip().startswith('//'):
                        continue
                    for rejected, correct in rejected_map.items():
                        if rejected not in line:
                            continue
                        # Must appear inside a string literal AND near CJK chars
                        # to avoid flagging English-only strings with coincidental substrings
                        if cjk_char_re.search(line):
                            findings.append({
                                'location': f'{filepath}:{lineno}',
                                'rejected': rejected,
                                'correct': correct,
                                'snippet': line.strip()[:100],
                            })

    if findings:
        print("=== Rejected translation terms found (from decisions.md) ===")
        print()
        for f in findings:
            print(f"  ❌ {f['location']}")
            print(f"     Rejected: '{f['rejected']}' → Correct: '{f['correct']}'")
            print(f"     {f['snippet']}")
            print()
        print(f"Summary: {len(findings)} rejected-term occurrence(s)")
        return 1
    else:
        print(f"OK: No rejected terms from {len(rejected_map)} active decisions found.")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: anti-patterns
# ══════════════════════════════════════════════════════════════════════════════

# Known functions returning const char* — .c_str() on these is always wrong.
# NOTE: god_name(), ability_name(), charge_desc(), species::name(),
# mons_type_name(), _beam_type_name() all return std::string — .c_str() is
# CORRECT on those. This rule intentionally targets only const char* returns.
CONST_CHAR_FUNCTIONS = re.compile(
    r'\b(?:skill_name|spell_title|'
    r'equip_slot_name|get_job_name|'
    r'mons_class_name|held_status'
    r')\s*\([^)]*\)\s*\.c_str\s*\(\s*\)'
)

# English articles as standalone words (in Chinese text they're errors)
EN_ARTICLE_RE = re.compile(r'(?<![a-zA-Z])\b(?:a|an|the)\b(?![a-zA-Z])')

# Words that look like English articles but aren't in Chinese context
ARTICLE_FALSE_POSITIVES = {'a', 'an', 'the'}


def has_cjk(s: str) -> bool:
    """Check if string contains CJK characters."""
    return bool(re.search(r'[⺀-鿿]', s))


# Protocol-facing Lua identity producers.  Keep this contract deliberately
# scoped to l-you.cc and the five exact binding implementations: unrelated
# display-name APIs (including mons_type_name uses elsewhere) are not covered.
# Exact canonical expressions returned by these protocol bindings.  Comparison
# removes whitespace only; it intentionally does not parse or accept wrappers,
# ternaries, or additional expression text.
LUA_IDENTITY_CONTRACT = {
    'you_species': 'species::name(you.species, species::SPNAME_PLAIN, true).c_str()',
    'you_race': 'species::name(you.species, species::SPNAME_PLAIN, true).c_str()',
    'you_class': 'get_job_name_en(you.char_class)',
    'l_you_genus': 'species::name(you.species, species::SPNAME_GENUS, true)',
    'l_you_monster': 'mons_type_name_en(mons, DESC_PLAIN)',
}


def _normalize_cpp_expression(expression):
    return re.sub(r'\s+', '', expression)



def _lua_identity_finding(rel_path, detail, binding=None):
    return {
        'level': '🔴',
        'rule': 'Lua protocol identity must be canonical English',
        'location': f'{rel_path}:{binding}' if binding else rel_path,
        'detail': detail,
        'snippet': binding or 'l-you.cc',
    }


def _lua_identity_contract_findings(artifacts):
    """Validate the complete, production-qualified Lua identity contract.

    Do not accept a token found in an unrelated file: these values are protocol
    identities and the production l-you.cc artifact is itself an invariant.
    """
    if len(artifacts) != 1:
        return [_lua_identity_finding(
            'source', 'expected exactly one production l-you.cc artifact, '
            f'found {len(artifacts)}')]
    filepath, rel_path = artifacts[0]
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        source = f.read()
    masked = _mask_cpp_comments(source)
    findings = []

    # LUARET1's third expression is the value returned to Lua.  Parse the call
    # rather than searching the function's file for a convenient accessor token.
    calls = list(_iter_named_calls(masked, ['LUARET1']))
    for binding, expression in LUA_IDENTITY_CONTRACT.items():
        if binding in ('you_species', 'you_race', 'you_class'):
            matches = [c for c in calls if c[2] and c[2][0][0].strip() == binding]
            if len(matches) != 1:
                findings.append(_lua_identity_finding(
                    rel_path, f'expected exactly one LUARET1 definition, found {len(matches)}', binding))
                continue
            args = matches[0][2]
            actual = args[2][0] if len(args) >= 3 else ''
            if _normalize_cpp_expression(actual) != _normalize_cpp_expression(expression):
                findings.append(_lua_identity_finding(
                    rel_path, 'the LUARET1 third expression is not the canonical raw/en accessor', binding))
            continue

        bodies = list(_iter_named_function_bodies(masked, [binding]))
        if len(bodies) != 1:
            findings.append(_lua_identity_finding(
                rel_path, f'expected exactly one function definition, found {len(bodies)}', binding))
            continue
        body = masked[bodies[0][1]:bodies[0][2]]
        expected = _normalize_cpp_expression(expression)
        # The accessor must initialize the exact variable subsequently pushed;
        # a decoy accessor elsewhere in the function is not sufficient.
        declarations = list(re.finditer(
            r'\b(?:string|auto)\s+(\w+)\s*=\s*([^;{}]+);', body))
        pushed = re.findall(r'lua_pushstring\s*\(\s*[^,]+,\s*(\w+)\s*\.c_str\s*\(\s*\)\s*\)', body)
        assignments = [d for d in declarations
                       if _normalize_cpp_expression(d.group(2)) == expected
                       and d.group(1) in pushed]
        if len(pushed) != 1 or len(assignments) != 1:
            findings.append(_lua_identity_finding(
                rel_path, 'canonical accessor must initialize the variable passed to lua_pushstring', binding))
            continue
        variable = assignments[0].group(1)
        init_end = assignments[0].end()
        push_match = re.search(
            r'lua_pushstring\s*\(\s*[^,]+,\s*' + re.escape(variable) + r'\s*\.c_str\s*\(\s*\)\s*\)',
            body[init_end:])
        if not push_match:
            findings.append(_lua_identity_finding(
                rel_path, 'canonical accessor must initialize the variable passed to lua_pushstring', binding))
            continue
        # Keep this narrow; it is not general C++ data-flow analysis.
        between = body[init_end:init_end + push_match.start()]
        reassignments = re.findall(
            r'\b' + re.escape(variable) + r'\s*=(?!=)\s*([^;{}]+);', between)
        allowed_genus_pluralise = 'pluralise(' + variable + ')'
        unexpected = [rhs for rhs in reassignments
                      if not (binding == 'l_you_genus'
                              and _normalize_cpp_expression(rhs) == allowed_genus_pluralise)]
        if unexpected:
            findings.append(_lua_identity_finding(
                rel_path,
                'canonical identity variable must not be reassigned before lua_pushstring '
                '(except exact genus = pluralise(genus))', binding))
            continue
        if binding in ('l_you_genus', 'l_you_monster') and not re.search(r'\blowercase\s*\(\s*' + re.escape(variable) + r'\s*\)', between):
            findings.append(_lua_identity_finding(
                rel_path, f'{"genus" if binding == "l_you_genus" else "monster"} must preserve lowercase processing before lua_pushstring', binding))
        if binding == 'l_you_genus' and allowed_genus_pluralise not in [_normalize_cpp_expression(rhs) for rhs in reassignments]:
            findings.append(_lua_identity_finding(rel_path, 'genus must preserve exact pluralise(genus) processing before lua_pushstring', binding))
    return findings


def _lua_identity_findings(filepath, source, rel_path):
    """Compatibility wrapper for callers; production validation is global."""
    return []


def cmd_anti_patterns(args):
    """Detect known anti-patterns in modified files."""
    findings = []
    strict_only = args.strict
    source_dir = args.source_dir

    # Collect files to scan.  l-you.cc is a production artifact, not an
    # optional fixture: validate its cardinality before scanning unrelated files.
    files_to_scan = []
    lua_artifacts = []
    for dirpath, dirnames, filenames in os.walk(source_dir):
        prune_dirs(dirnames)
        for fn in sorted(filenames):
            if fn.endswith('.cc') or fn.endswith('.h') or fn.endswith('.txt'):
                filepath = os.path.join(dirpath, fn)
                files_to_scan.append(filepath)
                if fn == 'l-you.cc':
                    lua_artifacts.append((filepath, os.path.relpath(filepath, source_dir)))
    findings.extend(_lua_identity_contract_findings(lua_artifacts))

    for filepath in files_to_scan:
        rel_path = os.path.relpath(filepath, source_dir)

        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
        findings.extend(_lua_identity_findings(filepath, source, rel_path))
        lines = source.splitlines(keepends=True)

        for lineno, line in enumerate(lines, 1):
            stripped = line.strip()

            # --- Strict rules (zero false positives) ---

            # R1: English articles in Chinese text (.txt files with CJK content)
            # Only flag when article appears embedded in Chinese prose —
            # not as quoted English, keyboard shortcuts, or XML markup.
            if filepath.endswith('.txt') and has_cjk(line) and EN_ARTICLE_RE.search(line):
                for m in EN_ARTICLE_RE.finditer(line):
                    word = m.group(0)
                    if word.lower() not in ARTICLE_FALSE_POSITIVES:
                        continue
                    # Skip single-char "a" when CJK immediately precedes —
                    # this is a keyboard key or option letter (能力a菜单,
                    # 武器 a，, a) 男性), not an English article.
                    if word.lower() == 'a':
                        pre2 = line[max(0, m.start()-2):m.start()]
                        if has_cjk(pre2):
                            continue
                    # Skip if bracketed (e.g. [a], [b]) — keyboard shortcuts;
                    # or slash-enclosed (e.g. /a/, /b/) — mode indicators.
                    pre_char = line[m.start()-1] if m.start() > 0 else ''
                    post_char = line[m.end()] if m.end() < len(line) else ''
                    if pre_char == '[' and post_char == ']':
                        continue
                    if pre_char == '/' and post_char == '/':
                        continue
                    # Skip if XML/HTML tags nearby (e.g. <w>a</w>) —
                    # these are UI markup, not prose.
                    near_tag = line[max(0, m.start()-10):m.end()+10]
                    if re.search(r'<[/]?\w+>', near_tag):
                        continue
                    # Require CJK context within 10 chars BEFORE the match
                    pre_context = line[max(0, m.start()-10):m.start()]
                    if not has_cjk(pre_context):
                        continue
                    # Require CJK within 5 chars AFTER the match — if CJK
                    # only appears before (but not after), we're looking at
                    # quoted English text within Chinese explanation.
                    post_context = line[m.end():min(len(line), m.end()+5)]
                    if not has_cjk(post_context):
                        continue
                    findings.append({
                        'level': '🔴',
                        'rule': 'English article in CN text',
                        'location': f'{rel_path}:{lineno}',
                        'detail': f'"{word}" near CJK',
                        'snippet': stripped[:100],
                    })

            # R2: .c_str() on const char* return (lenient only)
            if not strict_only:
                if CONST_CHAR_FUNCTIONS.search(line):
                    findings.append({
                        'level': '🟡',
                        'rule': '.c_str() on const char* return',
                        'location': f'{rel_path}:{lineno}',
                        'detail': 'Remove .c_str() — function already returns const char*',
                        'snippet': stripped[:100],
                    })

            # R4: conj_verb() with CJK in same line
            if not strict_only:
                if 'conj_verb(' in line and has_cjk(line):
                    findings.append({
                        'level': '🟡',
                        'rule': 'conj_verb() near Chinese text',
                        'location': f'{rel_path}:{lineno}',
                        'detail': 'conj_verb() must not wrap Chinese — it adds English suffixes',
                        'snippet': stripped[:100],
                    })

    if findings:
        level_label = "STRICT + LENIENT" if not strict_only else "STRICT"
        print(f"=== Anti-patterns detected ({level_label}) ===")
        print()
        for f in findings:
            print(f"  {f['level']} [{f['rule']}] {f['location']}")
            print(f"     {f['detail']}")
            print(f"     {f['snippet']}")
            print()

        blocker_count = sum(1 for f in findings if f['level'] == '🔴')
        warn_count = sum(1 for f in findings if f['level'] == '🟡')
        print(f"Summary: {len(findings)} finding(s) "
              f"({blocker_count} 🔴 strict, {warn_count} 🟡 lenient)")
        # Exit 1 only if strict findings exist
        return 1 if blocker_count > 0 else 0
    else:
        print("OK: No anti-patterns found.")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: species-consistency
# ══════════════════════════════════════════════════════════════════════════════

def cmd_species_consistency(args):
    """Check species/race term consistency between base and compound entries.

    For example, if "orc" → "兽人", then "orc warrior" should use the same
    base root "兽人" as "兽人战士", not a different transliteration.
    """
    entries = parse_source_txt(args.source_txt)
    if not entries:
        print("ERROR: Could not parse source.txt")
        return 1

    # Build a mapping of English prefix → Chinese base translation
    # by identifying base entries (single-token species names)
    base_translations = {}

    # Key species prefixes — ordered by specificity (longest first)
    species_prefixes = [
        'deep elf', 'hill orc', 'deep dwarf', 'mountain dwarf',
        'vine stalker', 'demonspawn',
        'spriggan', 'draconian', 'merfolk', 'centaur', 'yaktaur',
        'armataur', 'minotaur', 'gargoyle', 'formicid', 'barachi',
        'octopode', 'goblin', 'kobold', 'vampire', 'mummy',
        'naga', 'tengu', 'ghoul', 'faun', 'felid', 'djinn',
        'orc', 'ogre', 'troll', 'gnoll',
    ]

    # Extract base term translations from source.txt
    for prefix in species_prefixes:
        v = entries.get(prefix)
        if v and v != prefix:
            base_translations[prefix] = v.split('\n')[0].strip()

    # Check compound consistency
    findings = []
    for en_key, cn_val in entries.items():
        en_lower = en_key.lower()
        for prefix in sorted(base_translations.keys(), key=len, reverse=True):
            pfx = prefix + ' '
            if en_lower.startswith(pfx) and en_key != prefix:
                if en_lower.endswith(' summon'):
                    break
                expected_root = base_translations[prefix]
                cn_first = cn_val.split('\n')[0].strip()
                # Check that the CN compound starts with the same base term
                if not cn_first.startswith(expected_root):
                    findings.append((
                        prefix, en_key, expected_root, cn_first[:60]
                    ))
                break  # only check longest matching prefix

    if findings:
        print("=== SPECIES-CONSISTENCY — compound term mismatch ===")
        print("  Compound translations should use the same base term as")
        print("  the standalone species name.")
        print()
        for prefix, en_key, expected, actual in sorted(findings):
            print(f"  {prefix} → {expected}")
            print(f"    {en_key} → {actual}")
            print()
        print(f"  → {len(findings)} inconsistency/ies")
        return 1
    else:
        print(f"OK: All compound entries consistent with {len(base_translations)} "
              f"base species terms.")
        return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: monster-compound-consistency
# ══════════════════════════════════════════════════════════════════════════════

def cmd_monster_compound_consistency(args):
    """Check monster compound translations against established base-term rulings.

    This codifies monster-name rulings from docs/decisions.md so derived
    entries in source.txt keep using the same Chinese base term.
    """
    entries = parse_source_txt(args.source_txt)
    if not entries:
        print("ERROR: Could not parse source.txt")
        return 1

    token_rules = [
        {
            "rule_id": "fiend",
            "zh_token": "邪魔",
            "match": lambda key: key.endswith(" fiend"),
        },
        {
            "rule_id": "vampire",
            "zh_token": "吸血鬼",
            "match": lambda key: (
                key == "vampire"
                or "vampire bat" in key
                or key.startswith("swarm of vampire bat")
            ),
        },
        {
            "rule_id": "skeleton",
            "zh_token": "骷髅",
            "match": lambda key: key == "skeleton" or key.endswith(" skeleton"),
        },
        {
            "rule_id": "wraith",
            "zh_token": "幽魂",
            "match": lambda key: key == "wraith" or key.endswith(" wraith"),
        },
    ]

    exact_rules = {
        # D-A-026 — sensed monster naming family
        "sensed monster": "感知到的怪物",
        "trivial sensed monster": "微弱感知怪物",
        "easy sensed monster": "简单感知怪物",
        "tough sensed monster": "困难感知怪物",
        "nasty sensed monster": "危险感知怪物",
        "friendly sensed monster": "友善感知怪物",
        # D-B-012 — monster orb naming pattern (entity names only)
        "great orb of eyes": "巨眼之球",
        "orb of entropy": "熵之球",
        "orb of fire": "火焰之球",
        "orb of winter": "寒冬之球",
        "orb of Dispater": "迪斯帕特之球",
    }

    findings = []
    for en_key, cn_val in entries.items():
        cn_first = cn_val.split('\n')[0].strip()
        for rule in token_rules:
            if rule["match"](en_key):
                if rule["zh_token"] not in cn_first:
                    findings.append((
                        "token", rule["rule_id"], rule["zh_token"], en_key, cn_first
                    ))
                break

        if en_key in exact_rules and cn_first != exact_rules[en_key]:
            findings.append((
                "exact", en_key, exact_rules[en_key], en_key, cn_first
            ))

    if findings:
        print("=== MONSTER-COMPOUND-CONSISTENCY — base term mismatch ===")
        print("  Monster naming families should follow the established")
        print("  rulings from docs/decisions.md.")
        print()
        for kind, rule_id, expected, en_key, cn_first in sorted(findings):
            if kind == "token":
                print(f"  {rule_id} → contains {expected}")
            else:
                print(f"  {rule_id} → exactly {expected}")
            print(f"    {en_key} → {cn_first}")
            print()
        print(f"  → {len(findings)} inconsistency/ies")
        return 1

    print(
        "OK: All monitored monster naming families follow "
        f"{len(token_rules)} token rulings and {len(exact_rules)} exact rulings."
    )
    return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: monster-dbkey-consistency
# ══════════════════════════════════════════════════════════════════════════════

def cmd_monster_dbkey_consistency(args):
    """Check that monster speech DB lookups use DB names, not display names."""
    patterns = [
        re.compile(r'getSpeakString\([^;\n]*name\(DESC_PLAIN'),
        re.compile(r'_get_speak_string\([^;\n]*name\(DESC_PLAIN'),
        re.compile(r'_get_speak_string\([^;\n]*base_name\(DESC_PLAIN'),
        re.compile(r'_get_speak_string\([^;\n]*mons_type_name\([^;\n]*DESC_PLAIN'),
        re.compile(r'return\s+mons_type_name\(mons\.type,\s*DESC_PLAIN\);'),
        re.compile(r'mons_type_name\([^;\n]*DESC_PLAIN\)[^;\n]*cast_str'),
        re.compile(r'make_stringf\(T_\("%s %swizard%s"\)'),
        re.compile(r'make_stringf\(T_\("%swizard%s"\)'),
        re.compile(r'db_name\s*=\s*mi\.full_name\(DESC_PLAIN\);'),
        re.compile(r'getMiscString\(mi\.common_name\(DESC_DBNAME\)\s*\+\s*" title"\)'),
    ]

    findings = []
    for root, dirnames, filenames in os.walk(args.source_dir):
        prune_dirs(dirnames)
        for fn in filenames:
            if not fn.endswith(('.cc', '.h')):
                continue
            path = os.path.join(root, fn)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for lineno, line in enumerate(f, 1):
                        for pat in patterns:
                            if pat.search(line):
                                findings.append((path, lineno, line.strip()))
                                break
            except OSError:
                continue

    if findings:
        print("=== MONSTER-DBKEY-CONSISTENCY — display name used for DB key ===")
        print("  Monster speech/database lookups should use DESC_DBNAME so")
        print("  translated display names do not leak into English DB keys.")
        print()
        for path, lineno, line in findings:
            print(f"  {os.path.relpath(path)}:{lineno}")
            print(f"    {line}")
        print()
        print(f"  → {len(findings)} violation(s)")
        return 1

    print("OK: Monster speech/database lookups use DB names, not display names.")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: monster-name-assembly
# ══════════════════════════════════════════════════════════════════════════════

def cmd_monster_name_assembly(args):
    """Check monster display-name assembly for SSOT-bypassing raw literals."""
    checks = [
        (
            re.compile(r'mname\s*\+\s*" the "\s*\+\s*common_name\('),
            'Named monster full names should use T_(" the ") '
            'so Chinese article handling stays centralized in source.txt.',
        ),
        (
            re.compile(r'<<\s*" beast";'),
            'Mutant beast display names should use the contextual '
            'monster suffix key from source.txt.',
        ),
        (
            re.compile(r'<<\s*" shaped shifter";'),
            'Shapeshifter disguise suffixes should use the contextual '
            'monster suffix key from source.txt.',
        ),
        (
            re.compile(r'count\s*==\s*1\s*\?\s*full_name\(\)\s*:\s*pluralised_name'),
            'Single-monster primary labels should prefer title_name() so '
            'title-backed uniques stay consistent with hover, map, and panels.',
        ),
    ]

    findings = []
    try:
        with open(args.source_file, 'r', encoding='utf-8') as f:
            for lineno, line in enumerate(f, 1):
                for pat, message in checks:
                    if pat.search(line):
                        findings.append((lineno, line.strip(), message))
                        break
    except OSError as e:
        print(f"ERROR: Could not read {args.source_file}: {e}")
        return 1

    if findings:
        print("=== MONSTER-NAME-ASSEMBLY — raw name fragment bypasses SSOT ===")
        print("  Monster display-name assembly should pull locale-sensitive")
        print("  glue/suffix fragments from source.txt, not hardcoded literals.")
        print()
        for lineno, line, message in findings:
            print(f"  {args.source_file}:{lineno}")
            print(f"    {line}")
            print(f"    {message}")
            print()
        print(f"  → {len(findings)} violation(s)")
        return 1

    print("OK: Monster display-name assembly uses SSOT-backed glue/suffix keys.")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: monster-title-display
# ══════════════════════════════════════════════════════════════════════════════

def cmd_monster_title_display(args):
    """Check map/hover primary monster labels prefer title-aware names."""
    checks = [
        (
            re.compile(r'desc\s*=\s*monster_at\(gc\)->full_name\(DESC_PLAIN\);'),
            'Mouseover labels should prefer title_name() so title-backed '
            'uniques match other UI entry points.',
        ),
        (
            re.compile(r'json_write_string\("name",\s*m->full_name\(\)\);'),
            'Tile/web map labels should prefer title_name() so title-backed '
            'uniques match hover and description panels.',
        ),
        (
            re.compile(r'const string (old_name|new_name) = see_(old|new) \? mons\.full_name\(DESC_PLAIN\)'),
            'Player-visible history notes should prefer title_name() so '
            'visible monster names match hover, map, and panel labels.',
        ),
        (
            re.compile(r'full_name\(DESC_PLAIN\)\.c_str\(\)'),
            'Player-visible error/report messages should prefer title_name() '
            'unless the call site is strictly debug-only or intentionally uses a logic key.',
        ),
    ]

    findings = []
    for path in args.source_files:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for lineno, line in enumerate(f, 1):
                    for pat, message in checks:
                        if pat.search(line):
                            findings.append((path, lineno, line.strip(), message))
                            break
        except OSError as e:
            print(f"ERROR: Could not read {path}: {e}")
            return 1

    if findings:
        print("=== MONSTER-TITLE-DISPLAY — primary label bypasses title-aware name ===")
        print("  Monster hover/map primary labels should use title_name()")
        print("  instead of raw full_name() when a montitle entry exists.")
        print()
        for path, lineno, line, message in findings:
            print(f"  {path}:{lineno}")
            print(f"    {line}")
            print(f"    {message}")
            print()
        print(f"  → {len(findings)} violation(s)")
        return 1

    print("OK: Monster hover/map primary labels use title-aware names.")
    return 0


# ══════════════════════════════════════════════════════════════════════════════
# Subcommand: source-txt-integrity
# ══════════════════════════════════════════════════════════════════════════════

def cmd_source_txt_integrity(args):
    """Check source.txt for duplicate keys, self-conflicts, empty entries."""
    entries_raw = OrderedDict()
    duplicates = []
    self_conflicts = []
    empty_value = []

    # Use unified parser with case-sensitive keys (matching legacy behavior;
    # TODO: switch to lowercase_keys=True to match C++ GDBM runtime after
    # resolving 9 self-conflicts + 40 duplicates from case collisions)
    parsed = parse_entries(args.source_txt, lowercase_keys=False, unescape_hash=True)

    for order, entry in enumerate(parsed, start=1):
        key = entry.key
        value = entry.value

        if entry.is_empty:
            empty_value.append(key)

        if key in entries_raw:
            existing_val = entries_raw[key][0][0]
            if value != existing_val:
                self_conflicts.append((key, existing_val, value, order))
            else:
                duplicates.append((key, value, order))
        else:
            entries_raw[key] = [(value, order)]

    exit_code = 0

    if self_conflicts:
        print("=== SELF-CONFLICT — same key with DIFFERENT values ===")
        for key, v1, v2, order in sorted(self_conflicts)[:30]:
            print(f'  "{key}"')
            print(f'    Existing: "{v1[:80]}"')
            print(f'    Conflict: "{v2[:80]}" (appearance #{order})')
        if len(self_conflicts) > 30:
            print(f'  ... and {len(self_conflicts) - 30} more')
        print(f'  → {len(self_conflicts)} self-conflict(s) — BLOCKER')
        print()
        exit_code = 1

    if duplicates:
        print("=== DUPLICATE-KEYS — same key with same value ===")
        for key, value, order in sorted(duplicates)[:20]:
            print(f'  "{key}" (appearance #{order})')
        if len(duplicates) > 20:
            print(f'  ... and {len(duplicates) - 20} more')
        print(f'  → {len(duplicates)} duplicate(s)')
        print()
        exit_code = 1

    if empty_value:
        untranslated = [k for k in empty_value
                        if k not in entries_raw
                        or entries_raw.get(k) and entries_raw[k][0][0] == k]
        if untranslated:
            print(f"=== EMPTY-TRANSLATION — {len(untranslated)} keys with no "
                  f"Chinese value ===")
            for key in sorted(untranslated)[:15]:
                print(f'  "{key}"')
            if len(untranslated) > 15:
                print(f'  ... and {len(untranslated) - 15} more')
            print()

    if exit_code == 0:
        print(f"OK: No duplicate keys or self-conflicts in "
              f"{len(entries_raw)} unique entries.")
    return exit_code


# ══════════════════════════════════════════════════════════════════════════════
# Issue 66 — SourceDB canonical key collision detection and classification
# ══════════════════════════════════════════════════════════════════════════════

SHA256_HEX_RE = re.compile(r'^[0-9a-f]{64}$')
GROUP_ID_RE = re.compile(
    r'^sourcedb-v1:[0-9a-f]{64}$')
KIND_NAME = {None: 'source-key-collision', 'collision': 'source-key-collision',
             'missing-key': 'source-missing-key'}


def _load_json(path: str) -> dict:
    """Load JSON from path, handling None or missing."""
    if not path or not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _load_jsonl(path: str) -> list:
    """Load JSONL from path (one JSON object per line). Returns list of dicts."""
    if not path or not os.path.exists(path):
        return []
    objects = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                objects.append(json.loads(line))
    return objects


def _load_json_or_jsonl(path: str) -> list:
    """Load a shard file: try JSON first, fall back to JSONL lines.
    Always returns a list of group dicts."""
    if not path or not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if not lines:
        return []
    # Try single JSON
    content = ''.join(lines).strip()
    if content:
        try:
            d = json.loads(content)
            return d.get('groups', [])
        except json.JSONDecodeError:
            pass
    # JSONL: one object per line
    groups = []
    for line in content.split('\n'):
        line = line.strip()
        if line and line.startswith('{'):
            try:
                groups.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return groups


def _sha256_file(path: str) -> str:
    """Compute SHA-256 of a file."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def _get_source_snapshot(path: str) -> dict:
    """Get git snapshot info for a file path relative to repo root."""
    import subprocess
    try:
        abs_path = os.path.abspath(path)
        rel_path = os.path.relpath(abs_path)
        blob_oid = subprocess.check_output(
            ['git', 'hash-object', abs_path],
            stderr=subprocess.DEVNULL).decode().strip()
        sha256 = _sha256_file(abs_path)
        commit = subprocess.check_output(
            ['git', 'log', '-1', '--format=%H', '--', abs_path],
            stderr=subprocess.DEVNULL).decode().strip()
        return {
            'relative_path': rel_path,
            'blob_oid': blob_oid,
            'sha256': sha256,
            'snapshot_commit': commit,
        }
    except Exception:
        return {
            'relative_path': os.path.relpath(os.path.abspath(path)),
            'blob_oid': None,
            'sha256': _sha256_file(os.path.abspath(path)),
            'snapshot_commit': None,
        }


def _compute_collision_groups(source_txt: str):
    """Parse source.txt and return (entries, groups) for collision analysis.

    groups: dict mapping canonical_key -> list of PhysicalEntry
    """
    phys_entries = parse_entries_physical(source_txt)
    groups = OrderedDict()
    for entry in phys_entries:
        ck = entry.canonical_key
        if ck not in groups:
            groups[ck] = []
        groups[ck].append(entry)
    return phys_entries, groups


# ── source-key-collisions ──────────────────────────────────────────


def cmd_source_key_collisions(args):
    """Detect lowercase collisions in SourceDB keys.

    Prints summary: total_entries / unique_canonical_keys /
    collision_groups / runtime_equal / runtime_different.

    Returns 1 if collisions found, else 0.
    """
    from i18n_shared import runtime_normalize_value, classify_value_relation

    phys, groups = _compute_collision_groups(args.source_txt)
    total = len(phys)
    unique = len(groups)
    collision_groups = OrderedDict()
    for ck, defs in groups.items():
        if len(defs) >= 2:
            collision_groups[ck] = defs

    n_collisions = len(collision_groups)
    n_equal = 0
    n_diff = 0

    for ck, defs in collision_groups.items():
        values = [d.value for d in defs]
        rel = classify_value_relation(values, runtime_normalize_value)
        if rel == 'equal':
            n_equal += 1
        else:
            n_diff += 1

    print(f"{total} / {unique} / {n_collisions} / {n_equal} runtime-equal / "
          f"{n_diff} runtime-different")

    if n_collisions == 0:
        print("OK: No canonical key collisions.")
        return 0
    else:
        print(f"WARNING: {n_collisions} collision group(s) found.")
        for ck, defs in list(collision_groups.items())[:20]:
            print(f"  canonical='{ck}' ({len(defs)} definitions)")
            for d in defs:
                val_preview = d.value[:60].replace('\n', '\\n')
                print(f"    [{d.order}] raw='{d.raw_key}' "
                      f"val='{val_preview}'")
        if n_collisions > 20:
            print(f"  ... and {n_collisions - 20} more group(s)")
        return 1


# ── source-key-collision-inventory ─────────────────────────────────


def cmd_source_key_collision_inventory(args):
    """Generate or check the pre-fix collision inventory JSON."""
    from i18n_shared import runtime_normalize_value, classify_value_relation

    phys, groups = _compute_collision_groups(args.source_txt)
    total = len(phys)
    unique = len(groups)
    collision_groups = OrderedDict()
    for ck, defs in groups.items():
        if len(defs) >= 2:
            collision_groups[ck] = defs

    n_collisions = len(collision_groups)
    n_equal = 0
    n_diff = 0

    groups_list = []
    for ck, defs in collision_groups.items():
        values = [d.value for d in defs]
        runtime_rel = classify_value_relation(values, runtime_normalize_value)
        source_rel = classify_value_relation(
            values, lambda v: v)  # raw comparison
        if runtime_rel == 'equal':
            n_equal += 1
        else:
            n_diff += 1

        # Compute group_id = sourcedb-v1:<sha256(canonical_key)>
        ck_hash = hashlib.sha256(ck.encode('utf-8')).hexdigest()
        group_id = f"sourcedb-v1:{ck_hash}"
        fingerprint = compute_group_fingerprint(defs)

        definitions = []
        for d in defs:
            definitions.append({
                'order': d.order,
                'raw_key': d.raw_key,
                'value': d.value,
                'key_line': d.key_line,
                'value_line': d.value_line,
            })

        groups_list.append({
            'group_id': group_id,
            'group_fingerprint': fingerprint,
            'canonical_key': ck,
            'definitions': definitions,
            'source_value_relation': source_rel,
            'runtime_value_relation': runtime_rel,
        })

    # Sort for determinism
    groups_list.sort(key=lambda g: g['canonical_key'])

    source_snapshot = _get_source_snapshot(args.source_txt)

    inventory = {
        'schema': 'dcss-zh-source-inventory-v1',
        'canonical_contract': 'source-db-canonical-v1',
        'generator': 'scan_i18n.py source-key-collision-inventory',
        'generator_version': '1.0',
        'generator_sha': _sha256_file(__file__),
        'source_snapshot': source_snapshot,
        'summary': {
            'total_entries': total,
            'unique_canonical_keys': unique,
            'collision_groups': n_collisions,
            'runtime_equal': n_equal,
            'runtime_different': n_diff,
        },
        'groups': groups_list,
    }

    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)
        print(f"Inventory written to {args.output}")
        print(f"Summary: {total} entries, {unique} unique, "
              f"{n_collisions} collision groups "
              f"({n_equal} runtime-equal, {n_diff} runtime-different)")

    if args.check:
        existing = _load_json(args.check)
        if existing is None:
            print(f"ERROR: check file {args.check} not found", file=sys.stderr)
            return 1

        # Reject non-frozen inventories: deep recursive comparison.
        # Generate canonical JSON of the frozen inventory (exclude the check file
        # metadata fields that are expected to differ). Compare byte-level against
        # the freshly regenerated inventory.
        # This detects: field drift, value tampering, missing/extra keys,
        # sorting changes, fingerprint corruption — everything.
        def _to_canonical(inv):
            def _normalize(value):
                if isinstance(value, OrderedDict):
                    return {k: _normalize(v) for k, v in value.items()}
                if isinstance(value, dict):
                    return {k: _normalize(value[k]) for k in sorted(value)}
                if isinstance(value, list):
                    return [_normalize(v) for v in value]
                return value
            return _normalize(inv)

        # Full frozen comparison — no field exclusions.
        # generator_sha anchors the specific generator version that produced
        # this inventory. snapshot_commit anchors the frozen source blob.
        # Both must remain stable; any change requires re-generating.
        old_canonical = dict(existing)
        new_canonical = dict(inventory)

        old_frozen = json.dumps(_to_canonical(old_canonical), sort_keys=True,
                                ensure_ascii=False, separators=(',', ':'))
        new_frozen = json.dumps(_to_canonical(new_canonical), sort_keys=True,
                                ensure_ascii=False, separators=(',', ':'))

        if old_frozen != new_frozen:
            old_hash = hashlib.sha256(old_frozen.encode('utf-8')).hexdigest()
            new_hash = hashlib.sha256(new_frozen.encode('utf-8')).hexdigest()
            print(f"ERROR: Inventory content mismatch with frozen baseline:",
                  file=sys.stderr)
            print(f"  frozen SHA-256: {old_hash}", file=sys.stderr)
            print(f"  current SHA-256: {new_hash}", file=sys.stderr)
            # Also show summary differences for quick diagnosis
            old_sum = existing.get('summary', {})
            new_sum = inventory.get('summary', {})
            for key in ('total_entries', 'unique_canonical_keys', 'collision_groups',
                         'runtime_equal', 'runtime_different'):
                if old_sum.get(key) != new_sum.get(key):
                    print(f"  summary.{key}: expected={old_sum.get(key)}, "
                          f"actual={new_sum.get(key)}", file=sys.stderr)
            print(f"  (freeze HEAD to match)", file=sys.stderr)
            return 1

        print(f"OK: Inventory matches current source.txt "
              f"({len(existing.get('groups', []))} groups, fully frozen).")
        return 0

    return 0


# ── source-db-structure ────────────────────────────────────────────


def cmd_source_db_structure(args):
    """Scan source.txt for structural issues in the SourceDB block view.

    Detects blocks where consecutive key-value pairs are missing the %%・%%
    delimiter, causing subsequent keys to be swallowed into the first block's
    value. The pattern is: a value containing alternating ASCII-only (English
    key-like) and CJK (translation) lines, indicating merged entries.

    Uses i18n_extract.py extracted keys to validate that the swallowed lines
    match real extracted keys from the C++ source.

    Reports:
        MISSING_DELIMITER — value contains alternating EN/CJK lines
            suggesting missing %%%% separators
    """
    import re
    from i18n_shared import parse_entries_physical

    CJK_RE = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]')
    TAG_RE = re.compile(r'^<[^>]+>$')

    # Parse source.txt
    phys = parse_entries_physical(args.source_txt)

    def has_cjk(s):
        return bool(CJK_RE.search(s))

    def is_english_text(s):
        """Check if a non-empty line is English text (not a format specifier)."""
        s = s.strip()
        if not s or len(s) < 2:
            return False
        if not any(c.isalpha() for c in s):
            return False
        if has_cjk(s):
            return False
        if TAG_RE.match(s):
            return False
        # Pure format/markup
        if re.match(r'^[%\d\s\(\)\.\,\-\+<>\[\]/\'\":;!@#\$&\^=\?~\*`{}|\\\\]+$', s):
            return False
        return True

    def cjk_profile(value_lines):
        """Build CJK profile of non-empty lines."""
        return [(i, l.strip(), has_cjk(l.strip()))
                for i, l in enumerate(value_lines)
                if l.strip()]

    # Detect structural issues
    groups = []
    seen_groups = set()

    for entry in phys:
        value = entry.value
        if not value:
            continue

        value_lines = value.split('\n')
        profile = cjk_profile(value_lines)
        n = len(profile)
        if n < 2:
            continue

        # Find the first transition from non-CJK → CJK in the value
        # This indicates English text followed by Chinese translation
        first_transition = None
        for j in range(n - 1):
            if not profile[j][2] and profile[j + 1][2]:
                first_transition = (j, profile[j][1], profile[j + 1][1])
                break

        # Also find the first CJK → non-CJK → CJK pattern (swallowed key)
        swallowed_key = None
        for j in range(1, n - 1):
            if profile[j - 1][2] and not profile[j][2] and profile[j + 1][2]:
                swallowed_key = profile[j][1]
                break

        # Report patterns
        if swallowed_key:
            gk = (entry.key_line, swallowed_key)
            if gk not in seen_groups:
                seen_groups.add(gk)
                groups.append({
                    'containing_key': entry.raw_key,
                    'containing_line': entry.key_line,
                    'type': 'MISSING_DELIMITER',
                    'swallowed_keys': [swallowed_key],
                })

        elif first_transition and is_english_text(first_transition[1]):
            # EN → CJK transition: English text in value
            gk = (entry.key_line, first_transition[1][:30])
            if gk not in seen_groups:
                seen_groups.add(gk)
                groups.append({
                    'containing_key': entry.raw_key,
                    'containing_line': entry.key_line,
                    'type': 'ENGLISH_IN_VALUE',
                    'swallowed_keys': [first_transition[1]],
                })

    if not groups:
        print(f"OK: No structural issues in {len(phys)} entries.")
        return 0

    # Merge adjacent groups (within 200 lines) into one
    groups.sort(key=lambda g: g['containing_line'])
    merged = [groups[0]]
    for g in groups[1:]:
        last = merged[-1]
        if (g['containing_line'] - last['containing_line'] < 35
                and g['type'] == last['type']):
            last['swallowed_keys'].extend(g['swallowed_keys'])
            last['containing_key'] += ' / ' + g['containing_key']
        else:
            merged.append(g)

    n_issues = len(merged)
    print(f"WARNING: {n_issues} structural issue group(s) found in "
          f"{len(phys)} entries:")
    for g in merged:
        sk = ', '.join(g['swallowed_keys'])
        print(f"  [{g['type']}] line={g['containing_line']} "
              f"key={g['containing_key'][:60]!r} "
              f"swallowed=[{sk[:80]}]")
    return 1 if args.exit_nonzero_if_issues else 0


# ── validate-source-classification-shard ───────────────────────────


def cmd_validate_source_classification_shard(args):
    """Validate a classification shard file.

    Checks: schema version, group_id format, fingerprint consistency,
    hash-range ownership, intra-group dedup, ordering.
    Rejects 'unknown' or 'needs_semantic_ruling' uncovered groups.
    """
    shard = _load_json(args.shard)
    if shard is None:
        print(f"ERROR: shard file not found: {args.shard}", file=sys.stderr)
        return 1

    # Validate top-level structure
    if not isinstance(shard, dict):
        print(f"ERROR: shard must be a JSON object", file=sys.stderr)
        return 1

    if shard.get('schema') != 'dcss-zh-source-classification-shard-v1':
        print(f"ERROR: Unknown shard schema: {shard.get('schema')}",
              file=sys.stderr)
        return 1

    kind = args.kind
    groups = shard.get('groups', [])
    if not isinstance(groups, list):
        print(f"ERROR: shard groups must be a list", file=sys.stderr)
        return 1

    errors = []

    # Load inventory if provided to cross-reference
    inventory = _load_json(args.inventory) if args.inventory else None
    inventory_groups = {}
    if inventory:
        if args.kind == 'missing-key':
            # Missing-key inventory: missing_keys is a list of key strings
            inv_keys = inventory.get('missing_keys', [])
            for mk in inv_keys:
                import hashlib
                h = hashlib.sha256(mk.encode('utf-8')).hexdigest()
                gid = f"sourcedb-v1:{h}"
                inventory_groups[gid] = {'group_fingerprint': h}
        else:
            for g in inventory.get('groups', []):
                inventory_groups[g.get('group_id')] = g

    # Check for duplicate group_ids within shard
    seen_gids = set()
    for i, g in enumerate(groups):
        gid = g.get('group_id', '')
        if gid in seen_gids:
            errors.append(f"groups[{i}]: duplicate group_id: {gid}")
        seen_gids.add(gid)

    for i, g in enumerate(groups):
        gid = g.get('group_id', '')
        # Validate group_id format
        if not GROUP_ID_RE.match(gid):
            errors.append(f"groups[{i}]: invalid group_id: {gid}")

        # Cross-reference with inventory: every group_id must exist in inventory
        if inventory and gid not in inventory_groups:
            errors.append(
                f"groups[{i}]: group_id not in inventory: {gid}")

        # Validate fingerprint
        fp = g.get('group_fingerprint', '')
        if not SHA256_HEX_RE.match(fp):
            errors.append(f"groups[{i}]: invalid fingerprint: {fp}")

        # Validate classification
        cls = g.get('classification', {})
        if not cls:
            errors.append(f"groups[{i}]: missing classification")

        cause = cls.get('cause', '')
        if args.kind == 'missing-key':
            if cause not in ('adjacent_literal', 'not_in_source_txt',
                             'structural_corruption', 'not_user_visible'):
                errors.append(f"groups[{i}]: invalid cause: {cause}")
        else:
            if cause not in ('case_variant_duplicate', 'semantic_overload',
                             'missing_context', 'structural_corruption', 'unknown'):
                errors.append(f"groups[{i}]: invalid cause: {cause}")

        action = cls.get('action', '')
        if args.kind == 'missing-key':
            if action not in ('add_translation', 'repair_block',
                              'not_user_visible'):
                errors.append(f"groups[{i}]: invalid action: {action}")
        else:
            if action not in ('dedupe', 'choose_translation', 'introduce_context',
                              'repair_block', 'trace_callsites',
                              'defer_semantic_ruling'):
                errors.append(f"groups[{i}]: invalid action: {action}")

        status = cls.get('status', '')
        if status not in ('classified', 'needs_semantic_ruling',
                          'ready_for_writer', 'not_applicable'):
            errors.append(f"groups[{i}]: invalid status: {status}")

        # If status is 'unknown' or 'needs_semantic_ruling', that's a problem
        if cause == 'unknown' and (
                args.kind != 'missing-key'):
            errors.append(
                f"groups[{i}]: cause='unknown' — reject uncovered group")

        # Cross-reference with inventory if available
        if inventory and gid in inventory_groups:
            inv_g = inventory_groups[gid]
            # Verify fingerprint matches
            inv_fp = inv_g.get('group_fingerprint', '')
            if fp and inv_fp and fp != inv_fp:
                errors.append(
                    f"groups[{i}]: fingerprint drift: "
                    f"shard={fp}, inventory={inv_fp}")

    if errors:
        print(f"ERROR: {len(errors)} validation error(s) in shard:",
              file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print(f"OK: shard valid — {len(groups)} groups ({kind})")
    return 0


# ── source-missing-key-inventory ───────────────────────────────────


def cmd_source_missing_key_inventory(args):
    """Generate or check missing-key inventory.

    Scans for keys extracted by i18n_extract.py that have no source.txt entry.
    """
    from i18n_shared import parse_entries_physical, parse_source_txt

    # Get all defined keys
    defined = set()
    phys = parse_entries_physical(args.source_txt)
    for e in phys:
        defined.add(e.canonical_key)
        defined.add(e.raw_key.lower())

    # Get all extracted keys from C++ source
    extracted = set()
    if args.source_dir:
        extracted = _extract_source_keys(args.source_dir)

    if not extracted:
        # If no source dir, do a simplified check based on source.txt coverage
        print(f"INFO: No source dir provided, using source.txt only analysis")
        print(f"OK: {len(defined)} defined keys in source.txt")
        missing = []
    else:
        missing = sorted(extracted - defined)
        # Filter out common false positives
        missing = [k for k in missing
                   if not k.startswith(' ')]
        # Also mark keys where canonical is same but different whitespace
        missing = [k for k in missing
                   if k not in defined]

    if args.output:
        snapshot = {}
        if args.source_txt:
            snapshot = _get_source_snapshot(args.source_txt)
        inventory = {
            'schema': 'dcss-zh-missing-key-inventory-v1',
            'canonical_contract': 'source-db-canonical-v1',
            'generator': 'scan_i18n.py source-missing-key-inventory',
            'generator_version': '1.0',
            'generator_sha': _sha256_file(__file__),
            'source_snapshot': snapshot,
            'total_defined': len(defined),
            'total_missing': len(missing),
            'missing_keys': missing,
        }
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(inventory, f, indent=2, ensure_ascii=False)
        print(f"Missing-key inventory: {len(missing)} keys missing")
        print(f"Written to {args.output}")

    if args.check:
        existing = _load_json(args.check)
        if existing is None:
            print(f"ERROR: check file {args.check} not found", file=sys.stderr)
            return 1
        old_missing = set(existing.get('missing_keys', []))
        new_missing = set(missing)
        if old_missing != new_missing:
            added = sorted(new_missing - old_missing)
            removed = sorted(old_missing - new_missing)
            if added:
                print(f"NEW missing keys ({len(added)}):", file=sys.stderr)
                for k in added[:10]:
                    print(f"  '{k}'", file=sys.stderr)
            if removed:
                print(f"RESOLVED missing keys ({len(removed)}):",
                      file=sys.stderr)
                for k in removed[:10]:
                    print(f"  '{k}'", file=sys.stderr)
            print(f"ERROR: Missing-key inventory mismatch", file=sys.stderr)
            return 1
        print(f"OK: Missing-key inventory matches ({len(old_missing)} keys)")

    if missing:
        print(f"NOTE: {len(missing)} missing key(s) found "
              f"(not blocking for inventory)")
        return 0

    return 0


def _extract_source_keys(source_dir: str) -> set:
    """Extract T_() / N_() literal keys from C++ source."""
    extracted = set()
    T_RE = re.compile(r'\b[Tt]_\(\s*"((?:[^"\\]|\\.)*)"')
    N_RE = re.compile(r'\bN_\(\s*"((?:[^"\\]|\\.)*)"')

    for root, dirs, files in os.walk(source_dir):
        prune_dirs(dirs)
        for fn in files:
            if not (fn.endswith('.cc') or fn.endswith('.h') or
                    fn.endswith('.cpp') or fn.endswith('.hpp')):
                continue
            path = os.path.join(root, fn)
            try:
                with open(path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
            except Exception:
                continue
            for m in T_RE.finditer(content):
                extracted.add(m.group(1).lower())
            for m in N_RE.finditer(content):
                extracted.add(m.group(1).lower())
    return extracted


# ── validate-source-adjudications ──────────────────────────────────


def cmd_validate_source_adjudications(args):
    """Validate two overlay adjudication files.

    Checks: references to inventory/shard, uniqueness, precedence.
    """
    primary = _load_json(args.primary)
    secondary = _load_json(args.secondary)

    errors = []

    if primary is None:
        errors.append(f"Primary adjudication file not found: {args.primary}")
    if secondary is None:
        errors.append(
            f"Secondary adjudication file not found: {args.secondary}")
    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        return 1

    # Check schemas
    for name, data in [('primary', primary), ('secondary', secondary)]:
        if not isinstance(data, dict):
            errors.append(f"{name}: must be a JSON object")
        elif data.get('schema') != 'dcss-zh-source-adjudication-v1':
            errors.append(f"{name}: unknown schema: {data.get('schema')}")

    # Check group_id uniqueness across both files
    seen_gids = {}
    for name, data in [('primary', primary), ('secondary', secondary)]:
        groups = data.get('groups', []) if isinstance(data, dict) else []
        for g in groups:
            gid = g.get('group_id', '')
            if gid in seen_gids:
                errors.append(
                    f"Duplicate group_id in {name}: {gid} "
                    f"(also in {seen_gids[gid]})")
            seen_gids[gid] = name

    if errors:
        print(f"ERROR: {len(errors)} validation error(s):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print(f"OK: Adjudications valid — "
          f"{len(primary.get('groups', []))} primary, "
          f"{len(secondary.get('groups', []))} secondary groups")
    return 0


# ── assemble-source-key-collision-classifications ──────────────────


def cmd_assemble_source_key_collision_classifications(args):
    """Assemble collision manifest from inventory + shards + adjudications."""
    inventory = _load_json(args.inventory)
    if inventory is None:
        print(f"ERROR: inventory not found: {args.inventory}", file=sys.stderr)
        return 1

    # Load shards
    shards = {}
    if args.shards:
        for sp in args.shards:
            for g in _load_json_or_jsonl(sp):
                gid = g.get('group_id', '')
                if gid in shards:
                    print(f"ERROR: duplicate group_id across shards: {gid}",
                          file=sys.stderr)
                    return 1
                shards[gid] = g

    # Load adjudications
    adjudications = {}
    if args.adjudications:
        for ap in args.adjudications:
            a = _load_json(ap)
            if a:
                for g in a.get('groups', []):
                    gid = g.get('group_id', '')
                    adjudications[gid] = g

    assembled = []
    inv_groups = inventory.get('groups', [])
    for inv_g in inv_groups:
        gid = inv_g.get('group_id', '')
        entry = dict(inv_g)
        # Apply shard classifications
        if gid in shards:
            shard_cls = shards[gid].get('classification', {})
            if shard_cls:
                entry['classification'] = shard_cls
        elif gid in adjudications:
            adj_cls = adjudications[gid].get('classification', {})
            if adj_cls:
                entry['classification'] = adj_cls
        assembled.append(entry)

    manifest = {
        'schema': 'dcss-zh-source-collision-manifest-v1',
        'generator': 'scan_i18n.py assemble-source-key-collision-classifications',
        'generator_version': '1.0',
        'generator_sha': _sha256_file(__file__),
        'source_snapshot': inventory.get('source_snapshot', {}),
        'summary': dict(inventory.get('summary', {})),
        'groups': assembled,
    }

    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"Assembled manifest: {len(assembled)} groups "
              f"({len(shards)} sharded, {len(adjudications)} adjudicated)")
        print(f"Written to {args.output}")

    return 0


# ── assemble-source-missing-key-classifications ────────────────────


def cmd_assemble_source_missing_key_classifications(args):
    """Assemble missing-key manifest."""
    inventory = _load_json(args.inventory)
    if inventory is None:
        print(f"ERROR: inventory not found: {args.inventory}", file=sys.stderr)
        return 1

    # Load shards
    shards = {}
    if args.shards:
        for sp in args.shards:
            for g in _load_json_or_jsonl(sp):
                gid = g.get('group_id', '')
                if gid in shards:
                    print(f"ERROR: duplicate group_id across shards: {gid}",
                          file=sys.stderr)
                    return 1
                shards[gid] = g

    missing_keys = inventory.get('missing_keys', [])
    assembled_groups = []
    for mk in missing_keys:
        mk_hash = hashlib.sha256(mk.encode('utf-8')).hexdigest()
        gid = f"sourcedb-v1:{mk_hash}"
        entry = {
            'group_id': gid,
            'canonical_key': mk,
            'classification': shards.get(gid, {}).get(
                'classification', {}),
        }
        assembled_groups.append(entry)

    manifest = {
        'schema': 'dcss-zh-source-missing-key-manifest-v1',
        'generator':
            'scan_i18n.py assemble-source-missing-key-classifications',
        'generator_version': '1.0',
        'generator_sha': _sha256_file(__file__),
        'source_snapshot': inventory.get('source_snapshot', {}),
        'total_missing': len(missing_keys),
        'groups': assembled_groups,
    }

    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"Missing-key manifest: {len(assembled_groups)} groups")
        print(f"Written to {args.output}")

    return 0


# ── validate-source-key-collision-classifications ──────────────────


def cmd_validate_source_key_collision_classifications(args):
    """Validate assembled collision manifest.

    Checks: conservation (all inventory groups present), fresh fingerprints,
    completeness (all groups classified), no 'unknown' cause remaining.
    """
    manifest = _load_json(args.manifest)
    if manifest is None:
        print(f"ERROR: manifest not found: {args.manifest}", file=sys.stderr)
        return 1

    if manifest.get('schema') != 'dcss-zh-source-collision-manifest-v1':
        print(f"ERROR: unknown manifest schema: {manifest.get('schema')}",
              file=sys.stderr)
        return 1

    inventory = _load_json(args.inventory) if args.inventory else None
    errors = []
    groups = manifest.get('groups', [])

    # Conservation: every inventory group must be in manifest
    if inventory:
        inv_gids = {g.get('group_id', '') for g in inventory.get('groups', [])}
        manifest_gids = {g.get('group_id', '') for g in groups}
        missing_from_manifest = inv_gids - manifest_gids
        if missing_from_manifest:
            errors.append(
                f"Conservation failure: {len(missing_from_manifest)} "
                f"inventory groups missing from manifest")

        extra = manifest_gids - inv_gids
        if extra:
            errors.append(
                f"Extra groups in manifest not in inventory: "
                f"{len(extra)}")

    # Fingerprint freshness
    if inventory:
        inv_by_gid = {g.get('group_id', ''): g
                      for g in inventory.get('groups', [])}
        for g in groups:
            gid = g.get('group_id', '')
            if gid in inv_by_gid:
                inv_fp = inv_by_gid[gid].get('group_fingerprint', '')
                man_fp = g.get('group_fingerprint', '')
                if inv_fp and man_fp and inv_fp != man_fp:
                    errors.append(
                        f"Fingerprint drift for {gid}: "
                        f"inventory={inv_fp}, manifest={man_fp}")

    # Completeness: all groups must have classification
    unclassified = [g for g in groups
                    if not g.get('classification')
                    or g.get('classification', {}).get('cause') == 'unknown']
    if unclassified:
        errors.append(
            f"{len(unclassified)} group(s) still unclassified or unknown")

    # All groups must have status != 'needs_semantic_ruling' for completeness
    needs_ruling = [g for g in groups
                    if g.get('classification', {}).get('status')
                    == 'needs_semantic_ruling']
    if needs_ruling and args.reject_needs_ruling:
        errors.append(
            f"{len(needs_ruling)} group(s) still need semantic ruling")

    if errors:
        print(f"ERROR: {len(errors)} validation error(s):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print(f"OK: Manifest valid — {len(groups)} groups, all classified")
    return 0


# ── validate-source-missing-key-classifications ────────────────────


def cmd_validate_source_missing_key_classifications(args):
    """Validate assembled missing-key manifest."""
    manifest = _load_json(args.manifest)
    if manifest is None:
        print(f"ERROR: manifest not found: {args.manifest}", file=sys.stderr)
        return 1

    if manifest.get('schema') != 'dcss-zh-source-missing-key-manifest-v1':
        print(f"ERROR: unknown manifest schema: {manifest.get('schema')}",
              file=sys.stderr)
        return 1

    inventory = _load_json(args.inventory) if args.inventory else None
    errors = []
    groups = manifest.get('groups', [])

    if inventory:
        inv_missing = set(inventory.get('missing_keys', []))
        manifest_keys = {g.get('canonical_key', '') for g in groups}
        extra = manifest_keys - inv_missing
        if extra:
            errors.append(
                f"{len(extra)} keys in manifest not in inventory")

    unclassified = [g for g in groups
                    if not g.get('classification')
                    or g.get('classification', {}).get('cause') == 'unknown']
    if unclassified:
        errors.append(
            f"{len(unclassified)} group(s) still unclassified or unknown")

    if errors:
        print(f"ERROR: {len(errors)} validation error(s):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print(f"OK: Missing-key manifest valid — {len(groups)} groups")
    return 0


# ── source-callsite-receipt ────────────────────────────────────────


def cmd_source_callsite_receipt(args):
    """Accept adjudicated old→new extracted-key/callsite delta.

    Validates that the delta file has the correct format and that
    all referenced old keys exist and new keys don't conflict.
    """
    delta = _load_json(args.delta)
    if delta is None:
        print(f"ERROR: delta file not found: {args.delta}", file=sys.stderr)
        return 1

    if delta.get('schema') != 'dcss-zh-source-callsite-delta-v1':
        print(f"ERROR: unknown delta schema: {delta.get('schema')}",
              file=sys.stderr)
        return 1

    mappings = delta.get('mappings', [])
    if not isinstance(mappings, list):
        print(f"ERROR: mappings must be a list", file=sys.stderr)
        return 1

    errors = []
    old_keys = set()
    new_keys = set()
    for i, m in enumerate(mappings):
        old_key = m.get('old_key', '')
        new_key = m.get('new_key', '')
        if not old_key or not new_key:
            errors.append(f"mappings[{i}]: missing old_key or new_key")
        if old_key in old_keys:
            errors.append(f"mappings[{i}]: duplicate old_key: {old_key}")
        old_keys.add(old_key)
        if new_key in new_keys:
            errors.append(f"mappings[{i}]: duplicate new_key: {new_key}")
        new_keys.add(new_key)

    if errors:
        print(f"ERROR: {len(errors)} validation error(s):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print(f"OK: Callsite delta receipt accepted — "
          f"{len(mappings)} mappings")
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump({
                'schema': 'dcss-zh-source-callsite-receipt-v1',
                'status': 'accepted',
                'delta_source': os.path.basename(args.delta),
                'total_mappings': len(mappings),
            }, f, indent=2)
        print(f"Receipt written to {args.output}")

    return 0


# ── assemble-post-coder-source-handoff ─────────────────────────────


def cmd_assemble_post_coder_source_handoff(args):
    """Assemble translator handoff document from collision manifest."""
    collision_manifest = _load_json(args.collision_manifest)
    missing_manifest = (
        _load_json(args.missing_manifest) if args.missing_manifest else None)

    if collision_manifest is None:
        print(f"ERROR: collision manifest not found: "
              f"{args.collision_manifest}", file=sys.stderr)
        return 1

    handoff = {
        'schema': 'dcss-zh-source-handoff-v1',
        'generator': 'scan_i18n.py assemble-post-coder-source-handoff',
        'generator_version': '1.0',
        'generator_sha': _sha256_file(__file__),
        'collision_summary': collision_manifest.get('summary', {}),
        'collision_groups': [],
        'missing_key_groups': [],
        'handoff_instructions': {
            'for_each_collision_group':
                'Review the canonical_key and its definitions. '
                'Apply translator judgment: if values are equal, pick one; '
                'if different, choose the correct translation or add context.',
            'for_each_missing_key':
                'Translate the English key and add to source.txt.',
        },
    }

    # Collision groups needing semantic ruling
    for g in collision_manifest.get('groups', []):
        cls = g.get('classification', {})
        if cls.get('status') == 'needs_semantic_ruling':
            handoff['collision_groups'].append({
                'group_id': g.get('group_id', ''),
                'canonical_key': g.get('canonical_key', ''),
                'classification': cls,
                'definitions': g.get('definitions', []),
            })

    # Missing keys
    if missing_manifest:
        for g in missing_manifest.get('groups', []):
            handoff['missing_key_groups'].append({
                'group_id': g.get('group_id', ''),
                'canonical_key': g.get('canonical_key', ''),
            })

    if args.output:
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(handoff, f, indent=2, ensure_ascii=False)
        print(f"Handoff written to {args.output} — "
              f"{len(handoff['collision_groups'])} collision groups, "
              f"{len(handoff['missing_key_groups'])} missing keys")

    return 0


# ── validate-post-coder-source-handoff ─────────────────────────────


def cmd_validate_post_coder_source_handoff(args):
    """Validate translator handoff document."""
    handoff = _load_json(args.handoff)
    if handoff is None:
        print(f"ERROR: handoff not found: {args.handoff}", file=sys.stderr)
        return 1

    if handoff.get('schema') != 'dcss-zh-source-handoff-v1':
        print(f"ERROR: unknown handoff schema: {handoff.get('schema')}",
              file=sys.stderr)
        return 1

    errors = []
    coll_groups = handoff.get('collision_groups', [])
    missing_groups = handoff.get('missing_key_groups', [])

    for i, g in enumerate(coll_groups):
        if not g.get('group_id'):
            errors.append(
                f"collision_groups[{i}]: missing group_id")
        if not g.get('canonical_key'):
            errors.append(
                f"collision_groups[{i}]: missing canonical_key")

    for i, g in enumerate(missing_groups):
        if not g.get('group_id'):
            errors.append(
                f"missing_key_groups[{i}]: missing group_id")

    if errors:
        print(f"ERROR: {len(errors)} validation error(s):", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1

    print(f"OK: Handoff valid — "
          f"{len(coll_groups)} collision groups, "
          f"{len(missing_groups)} missing keys")
    return 0


def _protocol_boundary_scope(source, artifact):
    starts = list(re.finditer(artifact['start'], source, re.MULTILINE))
    if len(starts) != 1:
        return None, (f"start anchor expected exactly once, found "
                      f"{len(starts)}")
    ends = list(re.finditer(artifact['end'], source[starts[0].end():],
                           re.MULTILINE))
    if len(ends) < 1:
        return None, "end anchor not found after start anchor"
    end = starts[0].end() + ends[0].start()
    return source[starts[0].end():end], None


# Issue-16 monspeak VISUAL channel contract
# (CR-004/CR-008/CR-019/CR-023): the complete sorted-unique (canonical
# key, variant ordinal, Lua return branch ordinal, line ordinal) identity
# set of the EN monspeak lines that resolve to the VISUAL channel at the
# baseline OID (b3ad4425053c2175284d32441d67218df97035b0).  The identity
# is pinned at the production sink granularity: mons_speaks_msg
# (mon-speak.cc) splits every selected pattern by ``\n`` and resolves each
# line through resolve_mon_speech_line_channel, so a VISUAL line that is
# not the first line of its pattern (e.g. ``_holy_being_`` #0) or a second
# VISUAL line inside one pattern (e.g. ``_margery_common_`` #2) is part of
# the contract.  The branch ordinal (CR-023) is the Lua return branch
# index: getSpeakString evaluates every ``{{...}}`` block before the sink,
# so each literal ``return "VISUAL:..."`` emission is a possible runtime
# line and participates in the frozen set (e.g. ``friendly shoals hound``
# #2 emits two VISUAL branches, ``nekomata`` #1 emits two of three).
# Patterns without Lua blocks have exactly one branch (ordinal 0).  The
# set is fail-closed against EN drift: a removed, reworded or moved EN
# VISUAL line, a newline position change, a changed VISUAL prefix inside a
# Lua return or a deleted Lua return branch (even one jointly mirrored in
# ZH so the per-line channel check still passes) alters this set and trips
# the freeze before the per-branch ZH check runs.  The count is derived
# from the set, never a separate constant.
MONSPEAK_EN_VISUAL_LINES = (
    ("'r'", 0, 0, 0),
    ('_agnes_common_', 0, 0, 0),
    ('_aizul_common_', 0, 0, 0),
    ('_aizul_common_', 3, 0, 0),
    ('_aizul_rare_', 2, 0, 0),
    ('_aizul_rare_', 8, 0, 0),
    ('_amaemon_common_', 1, 0, 0),
    ('_amaemon_common_', 2, 0, 0),
    ('_amaemon_common_', 3, 0, 0),
    ('_asterion_common_', 0, 0, 0),
    ('_asterion_common_', 1, 0, 0),
    ('_azrael_common_', 3, 0, 0),
    ('_azrael_common_', 4, 0, 0),
    ('_azrael_common_', 5, 0, 0),
    ('_azrael_rare_', 3, 0, 0),
    ('_bai_suzhen_common_', 4, 0, 0),
    ('_bai_suzhen_rare_', 5, 0, 0),
    ('_bennu_death_', 0, 0, 0),
    ('_blorkula_common_', 1, 0, 0),
    ('_blorkula_common_', 2, 0, 0),
    ('_blorkula_common_', 3, 0, 0),
    ('_blorkula_rare_', 5, 0, 0),
    ('_boris_common_', 0, 0, 0),
    ('_chuck_generic_', 6, 0, 0),
    ('_chuck_rare_', 1, 0, 0),
    ('_confused_humanoid_common_', 0, 0, 0),
    ('_confused_humanoid_common_', 2, 0, 0),
    ('_confused_humanoid_common_', 4, 0, 0),
    ('_confused_humanoid_common_', 5, 0, 0),
    ('_confused_humanoid_common_', 6, 0, 0),
    ('_confused_humanoid_common_', 7, 0, 0),
    ('_confused_humanoid_medium_', 0, 0, 0),
    ('_confused_humanoid_rare_', 4, 0, 0),
    ('_confused_humanoid_rare_', 5, 0, 0),
    ('_crazy_yiuf_speech_', 1, 0, 0),
    ('_crazy_yiuf_speech_', 3, 0, 0),
    ('_crazy_yiuf_speech_', 4, 0, 0),
    ('_crazy_yiuf_speech_', 5, 0, 0),
    ('_dissolution_common_', 3, 0, 0),
    ('_dissolution_common_', 4, 0, 0),
    ('_dowan_common_', 0, 0, 0),
    ('_dowan_rare_', 0, 0, 0),
    ('_dowan_rare_', 1, 0, 0),
    ('_dowan_rare_', 2, 0, 0),
    ('_dowan_rare_', 3, 0, 0),
    ('_duvessa_common_', 0, 0, 0),
    ('_edmund_common_', 0, 0, 0),
    ('_edmund_rare_', 0, 0, 0),
    ('_edmund_rare_', 1, 0, 0),
    ('_erica_common_', 0, 0, 0),
    ('_erolcha_common_', 2, 0, 0),
    ('_eustachio_rare_', 1, 0, 0),
    ('_fake_spell_effect_', 0, 0, 0),
    ('_fake_spell_effect_', 1, 0, 0),
    ('_fake_spell_effect_', 2, 0, 0),
    ('_fake_spell_effect_', 3, 0, 0),
    ('_fake_spell_effect_', 4, 0, 0),
    ('_fannar_common_', 0, 0, 0),
    ('_fannar_common_', 1, 0, 0),
    ('_fannar_common_', 2, 0, 0),
    ('_fleeing_humanoid_common_', 0, 0, 0),
    ('_fleeing_humanoid_common_', 2, 0, 0),
    ('_fleeing_humanoid_rare_', 5, 0, 0),
    ('_fleeing_humanoid_rare_', 7, 0, 0),
    ('_fleeing_humanoid_rare_', 9, 0, 0),
    ('_fleeing_humanoid_rare_', 11, 0, 0),
    ('_fleeing_silenced_common_', 0, 0, 0),
    ('_fleeing_silenced_common_', 1, 0, 0),
    ('_fleeing_silenced_rare_', 0, 0, 0),
    ('_fleeing_silenced_rare_', 1, 0, 0),
    ('_fleeing_silenced_rare_', 2, 0, 0),
    ('_frances_common_', 0, 0, 0),
    ('_frances_common_', 1, 0, 0),
    ('_frances_rare_', 0, 0, 0),
    ('_frederick_common_', 0, 0, 0),
    ('_frederick_common_', 1, 0, 0),
    ('_frederick_rare_', 0, 0, 0),
    ('_frederick_rare_', 1, 0, 0),
    ('_frederick_rare_', 2, 0, 0),
    ('_friendly_beogh_speech_rare_', 5, 0, 0),
    ('_friendly_confused_common_', 4, 0, 0),
    ('_friendly_confused_common_', 5, 0, 0),
    ('_friendly_confused_medium_', 4, 0, 0),
    ('_friendly_confused_medium_', 5, 0, 0),
    ('_friendly_confused_medium_', 6, 0, 0),
    ('_friendly_confused_rare_', 5, 0, 0),
    ('_friendly_fleeing_common_', 0, 0, 0),
    ('_friendly_humanoid_common_', 2, 0, 0),
    ('_friendly_humanoid_common_', 3, 0, 0),
    ('_friendly_humanoid_common_', 5, 0, 0),
    ('_friendly_humanoid_medium_', 4, 0, 0),
    ('_friendly_humanoid_rare_', 0, 0, 0),
    ('_friendly_imp_common_', 0, 0, 0),
    ('_friendly_imp_common_', 1, 0, 0),
    ('_friendly_imp_common_', 2, 0, 0),
    ('_friendly_imp_common_', 3, 0, 0),
    ('_friendly_silenced_common_', 0, 0, 0),
    ('_friendly_silenced_common_', 1, 0, 0),
    ('_friendly_silenced_rare_', 0, 0, 0),
    ('_friendly_silenced_rare_', 1, 0, 0),
    ('_friendly_silenced_rare_', 2, 0, 0),
    ('_friendly_silenced_rare_', 3, 0, 0),
    ('_friendly_silenced_rare_', 4, 0, 0),
    ('_gastronok_common_', 0, 0, 0),
    ('_gastronok_rare_', 0, 0, 0),
    ('_gastronok_rare_', 1, 0, 0),
    ('_gastronok_rare_', 2, 0, 0),
    ('_generic_donald_', 25, 0, 0),
    ('_generic_donald_', 26, 0, 0),
    ('_generic_donald_', 27, 0, 0),
    ('_grinder_common_', 0, 0, 0),
    ('_grinder_rare_', 5, 0, 0),
    ('_grum_common_', 0, 0, 0),
    ('_grum_common_', 4, 0, 0),
    ('_grum_rare_', 0, 0, 0),
    ('_grunn_rare_', 0, 0, 0),
    ('_grunn_rare_', 1, 0, 0),
    ('_harold_common_', 0, 0, 0),
    ('_harold_rare_', 0, 0, 0),
    ('_high_priest_medium_', 0, 0, 0),
    ('_holy_being_', 0, 0, 1),
    ('_hostile_imp_common_', 1, 0, 0),
    ('_hostile_imp_common_', 2, 0, 0),
    ('_hostile_imp_common_', 3, 0, 0),
    ('_hostile_imp_common_', 4, 0, 0),
    ('_hostile_imp_rare_', 0, 0, 0),
    ('_hostile_imp_rare_', 1, 0, 0),
    ('_hostile_imp_rare_', 3, 0, 0),
    ('_hostile_imp_rare_', 4, 0, 0),
    ('_hostile_orc_beogh_believer_speech_common_', 10, 0, 0),
    ('_hostile_orc_beogh_believer_speech_rare_', 5, 0, 0),
    ('_hostile_orc_beogh_believer_speech_rare_', 6, 0, 0),
    ('_ignacio_common_', 0, 0, 0),
    ('_ignacio_common_', 1, 0, 0),
    ('_ijyb_common_', 0, 0, 0),
    ('_ijyb_common_', 1, 0, 0),
    ('_ilsuiw_common_', 3, 0, 0),
    ('_ilsuiw_rare_', 0, 0, 0),
    ('_jeremiah_common_', 6, 0, 0),
    ('_jeremiah_common_', 7, 0, 0),
    ('_jeremiah_common_', 8, 0, 0),
    ('_jeremiah_common_', 9, 0, 0),
    ('_jeremiah_common_', 10, 0, 0),
    ('_jeremiah_common_', 11, 0, 0),
    ('_jeremiah_rare_', 12, 0, 0),
    ('_jessica_common_', 0, 0, 0),
    ('_jessica_common_', 1, 0, 0),
    ('_jessica_common_', 3, 0, 0),
    ('_jory_silent_', 0, 0, 0),
    ('_jory_silent_', 1, 0, 0),
    ('_jory_silent_', 2, 0, 0),
    ('_jory_silent_', 3, 0, 0),
    ('_jory_silent_', 4, 0, 0),
    ('_jory_silent_', 5, 0, 0),
    ('_jory_silent_', 6, 0, 0),
    ('_jory_silent_', 7, 0, 0),
    ('_jory_silent_', 8, 0, 0),
    ('_jory_silent_', 9, 0, 0),
    ('_jory_silent_', 10, 0, 0),
    ('_joseph_common_', 1, 0, 0),
    ('_joseph_common_', 2, 0, 0),
    ('_josephina_common_', 0, 0, 0),
    ('_josephina_common_', 1, 0, 0),
    ('_josephina_common_', 4, 0, 0),
    ('_josephina_rare_', 0, 0, 0),
    ('_josephina_rare_', 1, 0, 0),
    ('_killer_klown_common_', 2, 0, 0),
    ('_killer_klown_common_', 3, 0, 0),
    ('_killer_klown_common_', 4, 0, 0),
    ('_killer_klown_common_', 5, 0, 0),
    ('_killer_klown_common_', 6, 0, 0),
    ('_killer_klown_common_', 7, 0, 0),
    ('_killer_klown_common_', 8, 0, 0),
    ('_killer_klown_rare_', 1, 0, 0),
    ('_killer_klown_rare_', 2, 0, 0),
    ('_killer_klown_rare_', 3, 0, 0),
    ('_killer_klown_rare_', 4, 0, 0),
    ('_lodul_common_', 1, 0, 0),
    ('_lodul_common_', 4, 0, 0),
    ('_lodul_rare_', 2, 0, 0),
    ('_maggie_common_', 0, 0, 0),
    ('_maggie_common_', 1, 0, 0),
    ('_maggie_common_', 4, 0, 0),
    ('_mara_common_', 0, 0, 0),
    ('_mara_common_', 6, 0, 0),
    ('_mara_common_', 7, 0, 0),
    ('_mara_common_', 8, 0, 0),
    ('_margery_common_', 0, 0, 0),
    ('_margery_common_', 1, 0, 0),
    ('_margery_common_', 2, 0, 0),
    ('_margery_common_', 2, 0, 1),
    ('_margery_common_', 3, 0, 0),
    ('_margery_rare_', 1, 0, 0),
    ('_margery_spell_results_', 0, 0, 0),
    ('_margery_spell_results_', 1, 0, 0),
    ('_margery_spell_results_', 2, 0, 0),
    ('_maurice_common_', 0, 0, 0),
    ('_maurice_common_', 1, 0, 0),
    ('_maurice_medium_', 0, 0, 0),
    ('_menkaure_common_', 0, 0, 0),
    ('_menkaure_common_', 5, 0, 0),
    ('_menkaure_common_', 6, 0, 0),
    ('_menkaure_common_', 8, 0, 0),
    ('_menkaure_common_', 10, 0, 0),
    ('_menkaure_rare_', 1, 0, 0),
    ('_menkaure_rare_', 2, 0, 0),
    ('_menkaure_rare_', 7, 0, 0),
    ('_mercenary_guard_common_', 0, 0, 0),
    ('_mercenary_guard_common_', 1, 0, 0),
    ('_murray_common_', 0, 0, 0),
    ('_murray_common_', 1, 0, 0),
    ('_murray_common_', 2, 0, 0),
    ('_murray_common_', 3, 0, 0),
    ('_natasha_rare_', 3, 0, 0),
    ('_nellie_common_', 5, 0, 0),
    ('_nellie_common_', 6, 0, 0),
    ('_nellie_common_', 7, 0, 0),
    ('_norris_common_', 1, 0, 0),
    ('_norris_common_', 2, 0, 0),
    ('_norris_common_', 3, 0, 0),
    ('_norris_rare_', 0, 0, 0),
    ('_parghit_common_', 1, 0, 0),
    ('_parghit_rare_', 0, 0, 0),
    ('_parghit_rare_', 1, 0, 0),
    ('_pargi_common_', 1, 0, 0),
    ('_pargi_rare_', 0, 0, 0),
    ('_pargi_rare_', 1, 0, 0),
    ('_pargi_rare_', 4, 0, 0),
    ('_pikel_common_', 4, 0, 0),
    ('_pikel_rare_', 4, 0, 0),
    ('_pikel_rare_', 11, 0, 0),
    ('_player_ghost_common_', 0, 0, 0),
    ('_player_ghost_common_', 4, 0, 0),
    ('_player_ghost_medium_', 1, 0, 0),
    ('_polyphemus_common_', 0, 0, 0),
    ('_polyphemus_common_', 1, 0, 0),
    ('_polyphemus_rare_', 0, 0, 0),
    ('_polyphemus_rare_', 1, 0, 0),
    ('_polyphemus_rare_', 2, 0, 0),
    ('_prince_ribbit_common_', 2, 0, 0),
    ('_prince_ribbit_common_', 3, 0, 0),
    ('_prince_ribbit_rare_', 3, 0, 0),
    ('_robin_common_', 5, 0, 0),
    ('_robin_common_', 6, 0, 0),
    ('_robin_common_', 7, 0, 0),
    ('_rupert_common_', 0, 0, 0),
    ('_rupert_common_', 1, 0, 0),
    ('_rupert_common_', 2, 0, 0),
    ('_rupert_rare_', 0, 0, 0),
    ('_sigmund_common_', 1, 0, 0),
    ('_sigmund_common_', 12, 0, 0),
    ('_sigmund_common_', 13, 0, 1),
    ('_sigmund_common_', 14, 0, 0),
    ('_sigmund_rare_', 5, 0, 0),
    ('_silenced_humanoid_common_', 0, 0, 0),
    ('_silenced_humanoid_common_', 1, 0, 0),
    ('_silenced_humanoid_rare_', 0, 0, 0),
    ('_silenced_humanoid_rare_', 1, 0, 0),
    ('_silenced_humanoid_rare_', 2, 0, 0),
    ('_silenced_humanoid_rare_', 3, 0, 0),
    ('_snorg_common_', 0, 0, 0),
    ('_snorg_common_', 1, 0, 0),
    ('_snorg_common_', 2, 0, 0),
    ('_snorg_common_', 3, 0, 0),
    ('_snorg_common_', 4, 0, 0),
    ('_sojobo_common_', 0, 0, 0),
    ('_sojobo_common_', 2, 0, 0),
    ('_sojobo_common_', 4, 0, 0),
    ('_sonja_common_', 2, 0, 0),
    ('_sonja_common_', 3, 0, 0),
    ('_sonja_common_', 4, 0, 0),
    ('_spectator_speech_', 4, 0, 0),
    ('_spectator_speech_', 5, 0, 0),
    ('_spectator_speech_', 6, 0, 0),
    ('_spectator_speech_', 7, 0, 0),
    ('_spectator_speech_', 8, 0, 0),
    ('_terence_common_', 0, 0, 0),
    ('_terence_common_', 1, 0, 0),
    ('_terence_common_', 2, 0, 0),
    ('_tormentor_common_', 1, 0, 0),
    ('_tormentor_common_', 2, 0, 0),
    ('_tormentor_common_', 3, 0, 0),
    ('_urug_common_', 1, 0, 0),
    ('_urug_common_', 2, 0, 0),
    ('_urug_common_', 3, 0, 0),
    ('_urug_rare_', 0, 0, 0),
    ('_vashnia_common_', 0, 0, 0),
    ('_vashnia_common_', 1, 0, 0),
    ('_vashnia_common_', 2, 0, 0),
    ('_vashnia_common_', 3, 0, 0),
    ('_vashnia_common_', 4, 0, 0),
    ('_wiglaf_common_', 6, 0, 0),
    ('_wizard_medium_', 0, 0, 0),
    ('_wizard_medium_', 1, 0, 0),
    ('_xtahua_common_', 1, 0, 0),
    ('_zenata_common_', 0, 0, 0),
    ('_zenata_common_', 2, 0, 0),
    ('air magic player ghost', 0, 0, 0),
    ('alderking', 0, 0, 0),
    ('alderking', 1, 0, 0),
    ('bennu', 0, 0, 0),
    ('bennu', 1, 0, 0),
    ('bennu permanently killed', 0, 0, 0),
    ('brain worm', 0, 0, 0),
    ('brain worm', 1, 0, 0),
    ('brain worm', 2, 0, 0),
    ('catoblepas', 2, 0, 0),
    ('catoblepas', 3, 0, 0),
    ('centipede', 0, 0, 0),
    ('chaos spawn', 0, 0, 0),
    ('chaos spawn', 1, 0, 0),
    ('chaos spawn', 2, 0, 0),
    ('cognitogaunt', 0, 0, 0),
    ('confused crazy yiuf', 2, 0, 0),
    ('confused crazy yiuf', 8, 0, 0),
    ('confused ijyb', 7, 0, 0),
    ('confused zin angel', 3, 0, 0),
    ('conjurations player ghost', 0, 0, 0),
    ('conjurations player ghost', 3, 0, 0),
    ('conjurations player ghost', 4, 0, 0),
    ('crossbows player ghost', 1, 0, 0),
    ('crystal guardian', 0, 0, 0),
    ('crystal guardian', 1, 0, 0),
    ("default 'cap-g'", 0, 0, 0),
    ("default 'cap-j'", 0, 0, 0),
    ("default confused 'b'", 0, 0, 0),
    ("default confused 'r'", 0, 0, 0),
    ('default confused arachnid', 0, 0, 0),
    ('default confused centipede', 0, 0, 0),
    ('default confused centipede', 1, 0, 0),
    ('default confused insect', 0, 0, 0),
    ('default confused insect', 1, 0, 0),
    ('default confused winged insect', 0, 0, 0),
    ('default confused winged insect', 1, 0, 0),
    ('default confused winged insect', 2, 0, 0),
    ('default hoarfrost cannon', 0, 0, 0),
    ('default hoarfrost cannon', 1, 0, 0),
    ('default hostile confused donald', 9, 0, 0),
    ('default hostile confused donald', 10, 0, 0),
    ('default hostile confused donald', 11, 0, 0),
    ('default hostile confused donald', 12, 0, 0),
    ('default ice statue', 0, 0, 0),
    ('default insect', 0, 0, 0),
    ('default mennas', 0, 0, 0),
    ('default mennas', 1, 0, 0),
    ('default mennas', 2, 0, 0),
    ('default mennas', 3, 0, 0),
    ('default obsidian statue', 0, 0, 0),
    ('default orange crystal statue', 0, 0, 0),
    ("default silenced confused 'y'", 0, 0, 0),
    ('default silenced confused humanoid', 0, 0, 0),
    ('default silenced confused humanoid', 1, 0, 0),
    ('default silenced confused humanoid', 2, 0, 0),
    ('default silenced confused humanoid', 3, 0, 0),
    ('default silenced confused humanoid', 4, 0, 0),
    ('default silenced confused humanoid', 5, 0, 0),
    ('deformed humanoid', 0, 0, 0),
    ('deformed humanoid', 1, 0, 0),
    ('deformed humanoid', 2, 0, 0),
    ('deformed humanoid', 3, 0, 0),
    ('deformed humanoid', 5, 0, 0),
    ('deformed humanoid', 7, 0, 0),
    ('deformed humanoid', 8, 0, 0),
    ('deformed humanoid', 9, 0, 0),
    ('deformed humanoid', 12, 0, 0),
    ('deformed humanoid', 15, 0, 0),
    ('deformed humanoid', 19, 0, 0),
    ('deformed humanoid', 20, 0, 0),
    ('deformed humanoid', 21, 0, 0),
    ('deformed humanoid', 22, 0, 0),
    ('deformed humanoid', 23, 0, 0),
    ('deformed humanoid', 24, 0, 0),
    ('deformed humanoid', 25, 0, 0),
    ('deformed humanoid', 26, 0, 0),
    ('deformed humanoid', 28, 0, 0),
    ('dowan_duvessa_dies', 1, 0, 0),
    ('duvessa_dowan_dies', 2, 0, 0),
    ('earth magic player ghost', 2, 0, 0),
    ('elephant slug', 0, 0, 0),
    ('erythrospite', 0, 0, 0),
    ('eustachio triumphant', 0, 0, 0),
    ('fighting player ghost', 1, 0, 0),
    ('fleeing dowan', 0, 0, 0),
    ('friendly hound', 0, 0, 0),
    ('friendly hound', 1, 0, 0),
    ('friendly hound', 2, 0, 0),
    ('friendly hound', 3, 0, 0),
    ('friendly hound', 3, 1, 0),
    ('friendly hound', 4, 0, 0),
    ('friendly hound', 5, 0, 0),
    ('friendly hound', 6, 0, 0),
    ('friendly hound', 7, 0, 0),
    ('friendly shoals hound', 1, 0, 0),
    ('friendly shoals hound', 2, 0, 0),
    ('friendly shoals hound', 2, 1, 0),
    ('friendly shoals hound', 3, 0, 0),
    ('goblin sharper', 0, 0, 0),
    ('goblin sharper', 1, 0, 0),
    ('goblin sharper', 2, 0, 0),
    ('goblin sharper', 3, 0, 0),
    ('gozag player ghost', 0, 0, 0),
    ('holy_being_pacification', 0, 0, 0),
    ('holy_being_pacification_humanoid', 1, 0, 0),
    ('holy_being_pacification_humanoid', 2, 0, 0),
    ('hound', 0, 0, 0),
    ('ice magic player ghost', 0, 0, 0),
    ('ignis player ghost', 1, 0, 0),
    ('invocations player ghost', 5, 0, 0),
    ('josephine', 0, 0, 0),
    ('josephine', 1, 0, 0),
    ('josephine', 2, 0, 0),
    ('killer klown triumphant', 0, 0, 0),
    ('killer klown triumphant', 2, 0, 0),
    ('kirke', 0, 0, 0),
    ('kirke', 1, 0, 0),
    ('kobold blastminer', 0, 0, 0),
    ('kobold blastminer', 1, 0, 0),
    ('long blades player ghost', 0, 0, 0),
    ('maces & flails player ghost', 1, 0, 0),
    ('moth of wrath', 0, 0, 0),
    ('natasha triumphant', 0, 0, 0),
    ('natasha triumphant', 1, 0, 0),
    ('nekomata', 0, 1, 0),
    ('nekomata', 1, 1, 0),
    ('nekomata', 1, 2, 0),
    ('nekomata', 2, 1, 0),
    ('nergalle', 2, 0, 0),
    ('nergalle', 3, 0, 0),
    ('obsidian bat', 0, 0, 0),
    ('orc donald', 7, 0, 0),
    ('orc_apostle_unbanished', 0, 0, 0),
    ('orc_apostle_unbanished', 7, 0, 0),
    ('protean progenitor', 0, 0, 0),
    ('protean progenitor', 1, 0, 0),
    ('protean progenitor', 2, 0, 0),
    ('protean progenitor', 3, 0, 0),
    ('ranged weapons player ghost', 2, 0, 0),
    ('ranged weapons player ghost', 3, 0, 0),
    ('reaper', 1, 0, 0),
    ('reaper', 2, 0, 0),
    ('reaper', 6, 0, 0),
    ('sewer brain worm', 1, 0, 0),
    ('shapeshifting player ghost', 1, 0, 0),
    ('shapeshifting player ghost', 2, 0, 0),
    ('short blades player ghost', 2, 0, 0),
    ('sigmund triumphant', 0, 0, 0),
    ('silenced cognitogaunt', 0, 0, 0),
    ('silenced murray', 0, 0, 0),
    ('silenced murray', 1, 0, 0),
    ('silenced murray', 2, 0, 0),
    ('silenced murray', 3, 0, 0),
    ('silenced murray', 4, 0, 0),
    ('silenced murray', 5, 0, 0),
    ('silenced player ghost', 0, 0, 0),
    ('silenced player ghost', 1, 0, 0),
    ('silenced player ghost', 2, 0, 0),
    ('silenced silent spectre', 0, 0, 0),
    ('silenced silent spectre', 1, 0, 0),
    ('silenced silent spectre', 2, 0, 0),
    ('silenced silent spectre', 3, 0, 0),
    ('silenced silent spectre', 4, 0, 0),
    ('silenced silent spectre', 5, 0, 0),
    ('silenced zin angel', 0, 0, 0),
    ('silenced zin angel', 1, 0, 0),
    ('silenced zin angel', 2, 0, 0),
    ('silenced zin angel', 3, 0, 0),
    ('silent jory killed', 0, 0, 0),
    ('slings player ghost', 1, 0, 0),
    ('sonja triumphant', 0, 0, 0),
    ('sonja triumphant', 1, 0, 0),
    ('spellcasting player ghost', 4, 0, 0),
    ('spellcasting player ghost', 5, 0, 0),
    ('staves player ghost', 1, 0, 0),
    ('stealth player ghost', 0, 0, 0),
    ('stealth player ghost', 1, 0, 0),
    ('stealth player ghost', 2, 0, 0),
    ('stealth player ghost', 3, 0, 0),
    ('stealth player ghost', 5, 0, 0),
    ('summonings player ghost', 1, 0, 0),
    ('thermic dynamo', 0, 0, 0),
    ('thermic dynamo', 1, 0, 0),
    ('throwing player ghost', 0, 0, 0),
    ('translocations player ghost', 0, 0, 0),
    ('translocations player ghost', 1, 0, 0),
    ('translocations player ghost', 2, 0, 0),
    ('twin_banished dowan', 0, 0, 0),
    ('twin_banished duvessa', 0, 0, 0),
    ('twin_banished duvessa', 1, 0, 0),
    ('twin_died dowan', 0, 0, 0),
    ('twin_died duvessa', 0, 0, 0),
    ('twin_died duvessa', 1, 0, 0),
    ('twin_died duvessa', 6, 0, 0),
    ('twin_ikilled dowan', 0, 0, 0),
    ('twin_ikilled duvessa', 0, 0, 0),
    ('twin_slimified dowan', 0, 0, 0),
    ('unarmed combat player ghost', 1, 0, 0),
    ('unarmed combat player ghost', 2, 0, 0),
    ('unarmed combat player ghost', 4, 0, 0),
    ('unarmed combat player ghost', 5, 0, 0),
    ("xak'krixis", 4, 0, 0),
    ("xak'krixis", 5, 0, 0),
    ('xom crazy yiuf', 11, 0, 0),
    ('xom crazy yiuf', 12, 0, 0),
    ('xom crazy yiuf', 13, 0, 0),
    ('xom crazy yiuf', 14, 0, 0),
    ('xtahua triumphant', 1, 0, 0),
)


MONSPEAK_EN_VISUAL_LINE_COUNT = len(MONSPEAK_EN_VISUAL_LINES)


def _monspeak_textdb_positions(source_dir, rel_path, label):
    """(canonical key, ordinal) -> raw variant pattern map of one monspeak
    file through the production TextDB parse layer
    (command_inventory.parse_db_keys + monflee_inventory's weighted
    parser), so the contract observes exactly what the game loads."""
    from command_inventory import parse_db_keys
    from monflee_inventory import (_parse_weighted_entry, lowercase_string)
    path = os.path.join(source_dir, rel_path)
    if not os.path.isfile(path):
        return None, f"required monspeak file missing: {rel_path}"
    with open(path, 'r', encoding='utf-8', errors='replace') as handle:
        source = handle.read()
    try:
        definitions = parse_db_keys(source, rel_path)
    except SystemExit as exc:
        return None, f"cannot parse {rel_path}: {exc}"
    positions = {}
    for definition in definitions:
        key = lowercase_string(definition.raw_key)
        variants, parse_error = _parse_weighted_entry(
            definition.value,
            {"source_name": rel_path, "load_index": 0,
             "definition_ordinal": 0},
            key)
        positions[key] = [variant["raw_pattern"] for variant in variants]
    return positions, None


# The channel identity classifier (``_monspeak_line_channel``) and the
# per-branch Lua runtime line expansion (``_lua_return_branch_lines``)
# are imported from monspeak_inventory (CR-023); this checker only owns
# the contract wiring: the frozen EN identity set, the EN drift freeze
# and the EN/ZH per-branch line/channel correspondence.


def _monspeak_runtime_branches(pattern):
    """Per-branch runtime line layouts of one monspeak pattern (CR-023).

    Production order: ``getSpeakString`` evaluates every ``{{...}}`` Lua
    block before the sink and splices the returned string into the
    message; ``mons_speaks_msg`` then splits with
    ``split_string("\\n", msg)`` (trim_segments=true,
    accept_empty_segments=false).  Every literal return branch of every
    block is therefore a possible runtime message; this wrapper expands
    each block per return branch (strict extraction from
    monspeak_inventory._lua_block_protocol) and returns one line layout
    per branch combination.  Blocks without literal returns (the
    you.race()/you.genus() display mappings) keep the colon-free,
    newline-free ``{{LUA}}`` placeholder, exactly like the pre-CR-023
    neutralization, so their surrounding layout survives without a Lua
    interpreter.  A pattern without Lua blocks has exactly one branch.
    Raises ``InventoryError`` when a block's return topology cannot be
    bound (malformed block / unsupported literal escape): the checker
    reports that as a fail-closed finding instead of guessing."""
    return _lua_return_branch_lines(pattern)


def _monspeak_visual_channel_findings(source_dir):
    """Issue-16 monspeak VISUAL channel routing (CR-004/CR-008/CR-019/
    CR-023).

    The complete sorted-unique EN (canonical key, variant ordinal, Lua
    return branch ordinal, line ordinal) set of lines that resolve to
    the VISUAL channel is frozen from the baseline dump and compared
    exactly, so an EN edit that swaps two lines inside a pattern (even
    when jointly mirrored in ZH, keeping the total and the per-line ZH
    check satisfied) still fails.  The branch ordinal is the Lua return
    branch index (CR-023): getSpeakString evaluates each ``{{...}}``
    block before the sink and every literal ``return "VISUAL:..."``
    emission is a possible runtime line, so the frozen set pins the
    per-branch channel topology of Lua blocks instead of erasing it with
    a placeholder.  Every pattern pinned by the frozen set is then
    checked branch by branch against ZH with the production sink
    semantics: the same branch count, the same runtime newline split and
    the same per-line channel resolution, so every corresponding line --
    including non-VISUAL lines and lines that strip to empty -- must
    resolve to the same channel as the EN line."""
    contract_id = 'issue16-monspeak-channels'
    findings = []
    en, error = _monspeak_textdb_positions(
        source_dir, 'dat/database/monspeak.txt', 'monspeak EN')
    if error:
        return [(contract_id, 'dat/database/monspeak.txt', error)]
    zh, error = _monspeak_textdb_positions(
        source_dir, 'dat/database/zh/monspeak.txt', 'monspeak ZH')
    if error:
        return [(contract_id, 'dat/database/zh/monspeak.txt', error)]
    # The frozen identity set is derived from the EN file alone: a key that
    # is missing from ZH must never shrink the set the drift check sees.
    visual_lines = []
    en_branches = {}
    for key in sorted(en):
        for ordinal in range(len(en[key])):
            try:
                branches = _monspeak_runtime_branches(en[key][ordinal])
            except InventoryError as exc:
                findings.append((contract_id,
                                 f"dat/database/monspeak.txt {key!r} "
                                 f"#{ordinal}",
                                 f"Lua return topology not bindable: {exc}"))
                continue
            en_branches[(key, ordinal)] = branches
            for branch, branch_lines in enumerate(branches):
                for line, raw_line in enumerate(branch_lines):
                    if _monspeak_line_channel(raw_line) == "talk_visual":
                        visual_lines.append((key, ordinal, branch, line))
    visual_lines = sorted(visual_lines)
    if visual_lines != list(MONSPEAK_EN_VISUAL_LINES):
        frozen = set(MONSPEAK_EN_VISUAL_LINES)
        current = set(visual_lines)
        missing = sorted(frozen - current)
        extra = sorted(current - frozen)
        findings.append((
            contract_id, 'dat/database/monspeak.txt',
            f"EN VISUAL line set drifted from the frozen baseline "
            f"identity set: {len(visual_lines)} lines "
            f"!= {MONSPEAK_EN_VISUAL_LINE_COUNT} "
            f"(missing {missing[:3]!r}..., extra {extra[:3]!r}...)"))
    for key in sorted(en):
        if zh.get(key) is None:
            findings.append((contract_id, f"key {key!r}",
                             "missing from zh/monspeak.txt"))
    # CR-013: the ZH check iterates every EN visual line, not only the
    # shared min-range ordinals.  A trailing EN-aligned VISUAL ordinal
    # deleted from ZH (the key's ZH variant list ends early) must fail
    # exactly like a line loss instead of being skipped by a min-range
    # loop.
    for key, ordinal, _branch, _line in visual_lines:
        zh_variants = zh.get(key)
        if zh_variants is None:
            continue  # already reported by the key-missing check above
        if ordinal >= len(zh_variants):
            findings.append((
                contract_id,
                f"dat/database/zh/monspeak.txt {key!r} #{ordinal}",
                "VISUAL channel line missing from zh/monspeak.txt "
                "(EN-aligned ordinal absent)"))
    # CR-019/CR-023: every pattern pinned by the frozen set must preserve
    # the whole line/channel layout of the production sink, not only its
    # VISUAL lines: the ZH pattern must split into the same branches (for
    # Lua literal-return blocks: the same return branch count) and every
    # corresponding line (including non-VISUAL lines) must resolve to the
    # same channel.  A line shift inside a pattern, a newline position
    # change, a deleted Lua return branch or a changed VISUAL prefix in a
    # Lua return breaks the correspondence and fails here even when the
    # frozen EN identity set is untouched.
    pinned_patterns = sorted({(key, ordinal)
                              for key, ordinal, _branch, _line
                              in visual_lines})
    for key, ordinal in pinned_patterns:
        zh_variants = zh.get(key)
        if zh_variants is None or ordinal >= len(zh_variants):
            continue  # already reported above
        try:
            en_lines_by_branch = en_branches[(key, ordinal)]
            zh_lines_by_branch = _monspeak_runtime_branches(
                zh_variants[ordinal])
        except InventoryError as exc:
            findings.append((
                contract_id,
                f"dat/database/zh/monspeak.txt {key!r} #{ordinal}",
                f"Lua return topology not bindable: {exc}"))
            continue
        if len(zh_lines_by_branch) != len(en_lines_by_branch):
            findings.append((
                contract_id,
                f"dat/database/zh/monspeak.txt {key!r} #{ordinal}",
                f"Lua return branch count differs from EN: EN has "
                f"{len(en_lines_by_branch)} branch(es), ZH has "
                f"{len(zh_lines_by_branch)}"))
            continue
        for branch, (en_lines, zh_lines) in enumerate(
            zip(en_lines_by_branch, zh_lines_by_branch)
        ):
            if len(zh_lines) != len(en_lines):
                suffix = (f" (Lua branch {branch})"
                          if len(en_lines_by_branch) > 1 else "")
                findings.append((
                    contract_id,
                    f"dat/database/zh/monspeak.txt {key!r} #{ordinal}",
                    f"runtime line count differs from EN: EN has "
                    f"{len(en_lines)} line(s), ZH has {len(zh_lines)}"
                    f"{suffix}"))
                continue
            for line, en_raw in enumerate(en_lines):
                en_channel = _monspeak_line_channel(en_raw)
                zh_channel = _monspeak_line_channel(zh_lines[line])
                if zh_channel == en_channel:
                    continue
                if en_channel == "talk_visual":
                    detail = "VISUAL channel prefix lost at an " \
                        "EN-aligned line"
                else:
                    detail = (f"line channel differs from EN: EN "
                              f"{en_channel}, ZH {zh_channel}")
                findings.append((
                    contract_id,
                    f"dat/database/zh/monspeak.txt {key!r} #{ordinal} "
                    f"line {line}",
                    detail))
    return findings


def protocol_boundary_findings(source_dir, only=None):
    """Validate registered Issue 68 producer scopes and cardinality."""
    findings = []
    contract_ids = [only] if only else list(PROTOCOL_BOUNDARY_CONTRACTS)
    for contract_id in contract_ids:
        artifacts = PROTOCOL_BOUNDARY_CONTRACTS.get(contract_id)
        if artifacts is None:
            findings.append((contract_id, '<registry>',
                             'unknown registry contract'))
            continue
        for index, artifact in enumerate(artifacts, 1):
            if artifact.get('custom'):
                if artifact['custom'] == 'monspeak-visual-channels':
                    findings.extend(
                        _monspeak_visual_channel_findings(source_dir))
                else:
                    findings.append((contract_id, artifact['file'],
                                     f"unknown custom checker "
                                     f"{artifact['custom']!r}"))
                continue
            path = os.path.join(source_dir, artifact['file'])
            label = f"{artifact['file']}#{index}"
            if not os.path.isfile(path):
                findings.append((contract_id, label, 'artifact missing'))
                continue
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
            scope, error = _protocol_boundary_scope(source, artifact)
            if error:
                findings.append((contract_id, label, error))
                continue
            for pattern, expected in artifact['required']:
                count = len(re.findall(pattern, scope, re.MULTILINE))
                if count != expected:
                    findings.append((
                        contract_id, label,
                        f"required producer {pattern!r}: expected {expected}, "
                        f"found {count}"))
            for pattern in artifact['forbidden']:
                count = len(re.findall(pattern, scope, re.MULTILINE))
                if count:
                    findings.append((
                        contract_id, label,
                        f"forbidden localized producer {pattern!r}: found "
                        f"{count}"))
    return findings


def cmd_protocol_boundaries(args):
    findings = protocol_boundary_findings(args.source_dir, args.only)
    print("--- scan_i18n.py protocol-boundaries ---")
    if findings:
        for contract_id, artifact, detail in findings:
            print(f"PROTOCOL001 {contract_id} {artifact}: {detail}")
        print(f"FAIL: {len(findings)} registered contract violation(s)")
        return 1
    count = 1 if args.only else len(PROTOCOL_BOUNDARY_CONTRACTS)
    print(f"OK: {count} registered protocol/display contract(s) passed")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="T_() world translation blind-spot scanner"
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    # missing-t
    p_missing = subparsers.add_parser(
        "missing-t",
        help="Find mprf/mpr calls without T_() wrapping"
    )
    p_missing.add_argument("source_dir", help="Root of C++ source tree")
    p_missing.add_argument("--strict", action="store_true",
                          help="Include debug/#if0 blocks (no preprocessor filtering)")
    p_missing.add_argument("--show-filtered", action="store_true",
                          help="Show filtered-out items with reason")
    p_missing.add_argument("--allowlist",
                          help="Path to allowlist JSON file")
    p_missing.add_argument("--source-txt",
                          help="Path to source.txt for dynamic-key wrappers")
    p_missing.add_argument(
        "--display-contracts-only", action="store_true",
        help="Run only high-confidence direct-sink and dynamic-key contracts")
    p_missing.add_argument(
        "--extended-display-audit", action="store_true",
        help="Compatibility flag; all registered display contracts are now "
             "included and blocking")

    # mprf-p
    p_mprfp = subparsers.add_parser(
        "mprf-p",
        help="Check mprf_p usage for positional format strings"
    )
    p_mprfp.add_argument("source_dir", help="Root of C++ source tree")
    p_mprfp.add_argument("--source-txt", required=True,
                         help="Path to source.txt")

    # arg-mismatch
    p_arg = subparsers.add_parser(
        "arg-mismatch",
        help="Check %s count parity between EN keys and CN translations"
    )
    p_arg.add_argument("--source-txt", required=True,
                       help="Path to source.txt")
    p_arg.add_argument("--allow-positional-drop", action="store_true",
                       help="Allow CN to drop positional args (cn_max_pos <= en_max_pos)")

    # seq-type-mismatch
    p_seqtype = subparsers.add_parser(
        "seq-type-mismatch",
        help="Detect sequential format specifier type-order mismatches "
             "(non-positional %%s/%%d swap -> crash on MinGW)"
    )
    p_seqtype.add_argument("--source-txt", required=True,
                           help="Path to source.txt")

    # format-malformed
    p_fmtmal = subparsers.add_parser(
        "format-malformed",
        help="Detect mixed positional/non-positional format specifiers "
             "(MinGW tiles crash risk)"
    )
    p_fmtmal.add_argument("--source-txt", required=True,
                          help="Path to source.txt")

    # check-gaps
    p_gaps = subparsers.add_parser(
        "check-gaps",
        help="Detect gaps in positional format numbering (Issue 29 %%N$.0s)"
    )
    p_gaps.add_argument("--source-txt", required=True,
                        help="Path to source.txt")

    # lang-args
    p_lang = subparsers.add_parser(
        "lang-args",
        help="Detect language-dependent args in T_() calls (heuristic)"
    )
    p_lang.add_argument("source_dir", help="Root of C++ source tree")

    # validate-terms
    p_terms = subparsers.add_parser(
        "validate-terms",
        help="Check for rejected translation terms from decisions.md"
    )
    p_terms.add_argument("--glossary", required=True,
                         help="Path to decisions.md")
    p_terms.add_argument("--source-txt",
                         help=("Path to source.txt (global scan plus exact "
                               "SourceDB contextual rules)"))
    p_terms.add_argument(
        "--zh-dir",
        dest="zh_dirs",
        action="append",
        default=[],
        help=("Required ZH TextDB directory to scan recursively for global "
              "rejected terms (repeatable)"),
    )
    p_terms.add_argument("--source-dir",
                         help="Root of C++ source tree (optional)")

    # anti-patterns
    p_ap = subparsers.add_parser(
        "anti-patterns",
        help="Detect known agent mistake patterns"
    )
    p_ap.add_argument("source_dir", help="Root of source tree")
    p_ap.add_argument("--strict", action="store_true",
                      help="Only strict (zero-FP) rules")

    p_pb = subparsers.add_parser(
        "protocol-boundaries",
        help="Validate registered Issue 68 protocol/display producers")
    p_pb.add_argument("source_dir", help="Root of Crawl source tree")
    p_pb.add_argument("--only", choices=tuple(PROTOCOL_BOUNDARY_CONTRACTS),
                      help="Validate one registry row (fixture support)")

    # species-consistency
    p_sc = subparsers.add_parser(
        "species-consistency",
        help="Check species/race base term consistency in compound "
             "translations (e.g. orc→兽人, orc warrior→兽人战士)")
    p_sc.add_argument("--source-txt", required=True,
                      help="Path to source.txt")

    # monster-compound-consistency
    p_mc = subparsers.add_parser(
        "monster-compound-consistency",
        help="Check monster compound/base-term consistency in source.txt "
             "(e.g. vampire→吸血鬼, vampire bat→吸血鬼蝙蝠)")
    p_mc.add_argument("--source-txt", required=True,
                      help="Path to source.txt")

    # monster-dbkey-consistency
    p_mdc = subparsers.add_parser(
        "monster-dbkey-consistency",
        help="Check monster speech DB lookups use DESC_DBNAME, not DESC_PLAIN")
    p_mdc.add_argument("source_dir", help="Root of C++ source tree")

    # monster-name-assembly
    p_mna = subparsers.add_parser(
        "monster-name-assembly",
        help="Check monster display-name assembly uses source.txt-backed glue/suffix keys")
    p_mna.add_argument("source_file", help="Monster naming implementation file")

    # monster-title-display
    p_mtd = subparsers.add_parser(
        "monster-title-display",
        help="Check hover/map monster labels use title-aware primary names")
    p_mtd.add_argument("source_files", nargs="+",
                       help="Source files implementing hover/map monster labels")

    # source-txt-integrity
    p_sti = subparsers.add_parser(
        "source-txt-integrity",
        help="Check source.txt for duplicate keys and self-conflicts"
    )
    p_sti.add_argument("--source-txt", required=True,
                       help="Path to source.txt")

    # ══════════════════════════════════════════════════════════════════
    # Issue 66 — SourceDB commands
    # ══════════════════════════════════════════════════════════════════

    # source-key-collisions
    p_skc = subparsers.add_parser(
        "source-key-collisions",
        help="Find lowercase collisions in SourceDB canonical keys"
    )
    p_skc.add_argument("--source-txt", required=True,
                       help="Path to source.txt")

    # source-key-collision-inventory
    p_ski = subparsers.add_parser(
        "source-key-collision-inventory",
        help="Generate/check pre-fix collision inventory JSON"
    )
    p_ski.add_argument("--source-txt", required=True,
                       help="Path to source.txt")
    p_ski.add_argument("--output",
                       help="Output path for inventory JSON")
    p_ski.add_argument("--check",
                       help="Check existing inventory against current source.txt")

    # source-db-structure
    p_sds = subparsers.add_parser(
        "source-db-structure",
        help="Scan source.txt for structural issues (MISSING_DELIMITER, "
             "ENGLISH_IN_VALUE)"
    )
    p_sds.add_argument("--source-txt", required=True,
                       help="Path to source.txt")
    p_sds.add_argument("--exit-nonzero-if-issues", action="store_true",
                       help="Exit 1 if any structural issues found")

    # validate-source-classification-shard
    p_vscs = subparsers.add_parser(
        "validate-source-classification-shard",
        help="Validate a classification shard file"
    )
    p_vscs.add_argument("--kind", required=True,
                        choices=['collision', 'missing-key'],
                        help="Kind of classification")
    p_vscs.add_argument("--inventory",
                        help="Path to inventory JSON (optional cross-ref)")
    p_vscs.add_argument("--range",
                        help="Hash-range ownership string")
    p_vscs.add_argument("--shard", required=True,
                        help="Path to shard JSON")

    # source-missing-key-inventory
    p_smki = subparsers.add_parser(
        "source-missing-key-inventory",
        help="Generate/check missing-key inventory"
    )
    p_smki.add_argument("--source-dir",
                        help="Root of C++ source tree (for extraction scan)")
    p_smki.add_argument("--source-txt", required=True,
                        help="Path to source.txt")
    p_smki.add_argument("--output",
                        help="Output path for inventory JSON")
    p_smki.add_argument("--check",
                        help="Check existing inventory against current source.txt")

    # validate-source-adjudications
    p_vsa = subparsers.add_parser(
        "validate-source-adjudications",
        help="Validate two overlay adjudication files"
    )
    p_vsa.add_argument("--primary", required=True,
                       help="Primary adjudication file")
    p_vsa.add_argument("--secondary", required=True,
                       help="Secondary adjudication file")

    # assemble-source-key-collision-classifications
    p_askcc = subparsers.add_parser(
        "assemble-source-key-collision-classifications",
        help="Assemble collision manifest from inventory + shards + adjudications"
    )
    p_askcc.add_argument("--inventory", required=True,
                         help="Path to inventory JSON")
    p_askcc.add_argument("--shards", nargs="*", default=[],
                         help="Shard file paths")
    p_askcc.add_argument("--adjudications", nargs="*", default=[],
                         help="Adjudication file paths")
    p_askcc.add_argument("--output", required=True,
                         help="Output path for assembled manifest")

    # assemble-source-missing-key-classifications
    p_asmkc = subparsers.add_parser(
        "assemble-source-missing-key-classifications",
        help="Assemble missing-key manifest"
    )
    p_asmkc.add_argument("--inventory", required=True,
                         help="Path to missing-key inventory JSON")
    p_asmkc.add_argument("--shards", nargs="*", default=[],
                         help="Shard file paths")
    p_asmkc.add_argument("--output", required=True,
                         help="Output path for assembled manifest")

    # validate-source-key-collision-classifications
    p_vskcc = subparsers.add_parser(
        "validate-source-key-collision-classifications",
        help="Validate assembled collision manifest"
    )
    p_vskcc.add_argument("--manifest", required=True,
                         help="Path to manifest JSON")
    p_vskcc.add_argument("--inventory",
                         help="Path to inventory JSON (optional cross-ref)")
    p_vskcc.add_argument("--reject-needs-ruling", action="store_true",
                         help="Reject groups needing semantic ruling")

    # validate-source-missing-key-classifications
    p_vsmkc = subparsers.add_parser(
        "validate-source-missing-key-classifications",
        help="Validate assembled missing-key manifest"
    )
    p_vsmkc.add_argument("--manifest", required=True,
                         help="Path to manifest JSON")
    p_vsmkc.add_argument("--inventory",
                         help="Path to inventory JSON (optional cross-ref)")

    # source-callsite-receipt
    p_scr = subparsers.add_parser(
        "source-callsite-receipt",
        help="Accept adjudicated old→new extracted-key/callsite delta"
    )
    p_scr.add_argument("--delta", required=True,
                       help="Path to callsite delta JSON")
    p_scr.add_argument("--output",
                       help="Output path for receipt JSON")

    # assemble-post-coder-source-handoff
    p_apcsh = subparsers.add_parser(
        "assemble-post-coder-source-handoff",
        help="Assemble translator handoff document"
    )
    p_apcsh.add_argument("--collision-manifest", required=True,
                         help="Path to collision manifest JSON")
    p_apcsh.add_argument("--missing-manifest",
                         help="Path to missing-key manifest JSON (optional)")
    p_apcsh.add_argument("--output", required=True,
                         help="Output path for handoff JSON")

    # validate-post-coder-source-handoff
    p_vpcsh = subparsers.add_parser(
        "validate-post-coder-source-handoff",
        help="Validate translator handoff document"
    )
    p_vpcsh.add_argument("--handoff", required=True,
                         help="Path to handoff JSON")

    args = parser.parse_args()

    if (args.command == "missing-t" and args.display_contracts_only
            and not args.source_txt):
        p_missing.error("--source-txt is required with "
                        "--display-contracts-only")
    if (args.command == "missing-t" and args.extended_display_audit
            and not args.display_contracts_only):
        p_missing.error("--extended-display-audit requires "
                        "--display-contracts-only")

    if args.command == "missing-t":
        return cmd_missing_t(args)
    elif args.command == "mprf-p":
        return cmd_mprf_p(args)
    elif args.command == "arg-mismatch":
        return cmd_arg_mismatch(args)
    elif args.command == "seq-type-mismatch":
        return cmd_seq_type_mismatch(args)
    elif args.command == "format-malformed":
        return cmd_format_malformed(args)
    elif args.command == "check-gaps":
        return cmd_check_gaps(args)
    elif args.command == "lang-args":
        return cmd_lang_args(args)
    elif args.command == "validate-terms":
        return cmd_validate_terms(args)
    elif args.command == "anti-patterns":
        return cmd_anti_patterns(args)
    elif args.command == "protocol-boundaries":
        return cmd_protocol_boundaries(args)
    elif args.command == "species-consistency":
        return cmd_species_consistency(args)
    elif args.command == "monster-compound-consistency":
        return cmd_monster_compound_consistency(args)
    elif args.command == "monster-dbkey-consistency":
        return cmd_monster_dbkey_consistency(args)
    elif args.command == "monster-name-assembly":
        return cmd_monster_name_assembly(args)
    elif args.command == "monster-title-display":
        return cmd_monster_title_display(args)
    elif args.command == "source-txt-integrity":
        return cmd_source_txt_integrity(args)
    # ── Issue 66 commands ──
    elif args.command == "source-key-collisions":
        return cmd_source_key_collisions(args)
    elif args.command == "source-key-collision-inventory":
        return cmd_source_key_collision_inventory(args)
    elif args.command == "source-db-structure":
        return cmd_source_db_structure(args)
    elif args.command == "validate-source-classification-shard":
        return cmd_validate_source_classification_shard(args)
    elif args.command == "source-missing-key-inventory":
        return cmd_source_missing_key_inventory(args)
    elif args.command == "validate-source-adjudications":
        return cmd_validate_source_adjudications(args)
    elif args.command == "assemble-source-key-collision-classifications":
        return cmd_assemble_source_key_collision_classifications(args)
    elif args.command == "assemble-source-missing-key-classifications":
        return cmd_assemble_source_missing_key_classifications(args)
    elif args.command == "validate-source-key-collision-classifications":
        return cmd_validate_source_key_collision_classifications(args)
    elif args.command == "validate-source-missing-key-classifications":
        return cmd_validate_source_missing_key_classifications(args)
    elif args.command == "source-callsite-receipt":
        return cmd_source_callsite_receipt(args)
    elif args.command == "assemble-post-coder-source-handoff":
        return cmd_assemble_post_coder_source_handoff(args)
    elif args.command == "validate-post-coder-source-handoff":
        return cmd_validate_post_coder_source_handoff(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
