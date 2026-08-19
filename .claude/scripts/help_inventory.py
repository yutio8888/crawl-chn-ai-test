#!/usr/bin/env python3
"""Exact-Git production inventory for Issue #52 HelpDB and FAQDB review.

The stable identity space is the union of the effective EN/ZH HelpDB keys and
the union of complete FAQ question/answer suffixes.  Text files are parsed
with the production ``_parse_text_db`` state machine reused from
``command_inventory.py``; in particular, comments after ``%%%%`` do not
become keys.  Every Help identity is tied to a source consumer literal and
every FAQ identity is tied to the real DBM enumeration, Q/A lookup, unwrap and
bullet-display path.

The tool records structural differences for human review but only treats
malformed markup/Lua, Q/A corruption, missing consumers and incomplete key
coverage as blockers.  It never judges translation quality.

Consumer, producer, and evidence locators bind to stable source-text
anchors (unique consumer fragments, TextDB keys, and call-site literals
with occurrence ordinals), so unrelated line-number shifts cannot drift a
frozen ledger, while any real consumer-shape change still fails closed
through the uniqueness checks.
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
    git_show_blob,
    merge_desc_sequence,
    parse_db_keys,
    resolve_commit,
    write_inventory_output,
)
from i18n_shared import (  # noqa: E402
    AuditInput,
    load_review_input,
    lowercase_string,
    review_input_metadata,
)
from tutorial_inventory import load_git_review_input  # noqa: E402


HELP_EN = "crawl-ref/source/dat/database/help.txt"
HELP_ZH = "crawl-ref/source/dat/database/zh/help.txt"
FAQ_EN = "crawl-ref/source/dat/database/FAQ.txt"
FAQ_ZH = "crawl-ref/source/dat/database/zh/FAQ.txt"
DATABASE_CC = "crawl-ref/source/database.cc"
DATABASE_H = "crawl-ref/source/database.h"
COMMAND_CC = "crawl-ref/source/command.cc"
MACRO_CC = "crawl-ref/source/macro.cc"
MENU_CC = "crawl-ref/source/menu.cc"
INVENT_CC = "crawl-ref/source/invent.cc"
KNOWN_ITEMS_CC = "crawl-ref/source/known-items.cc"
WIZ_MON_CC = "crawl-ref/source/wiz-mon.cc"
FORMAT_CC = "crawl-ref/source/format.cc"
COLOUR_CC = "crawl-ref/source/colour.cc"
GLOSSARY_MD = "docs/glossary.md"

HELP_CONSUMER_PATHS = (
    COMMAND_CC,
    MACRO_CC,
    MENU_CC,
    INVENT_CC,
    KNOWN_ITEMS_CC,
    WIZ_MON_CC,
)
INPUT_PATHS = (
    HELP_EN,
    HELP_ZH,
    FAQ_EN,
    FAQ_ZH,
    DATABASE_CC,
    DATABASE_H,
    *HELP_CONSUMER_PATHS,
    FORMAT_CC,
    COLOUR_CC,
    GLOSSARY_MD,
)

STRICT_REVIEW_BEGIN = "<!-- BEGIN STRICT HELP FAQ REVIEW EVIDENCE v1 -->"
STRICT_REVIEW_END = "<!-- END STRICT HELP FAQ REVIEW EVIDENCE v1 -->"
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
    "deferral_owner",
    "deferral_reason",
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

_HELP_KEY_RE = re.compile(r"[a-z0-9][a-z0-9.-]*")
_FAQ_KEY_RE = re.compile(r"([qa]):([a-z0-9][a-z0-9 ._-]*)")
_STRING_LITERAL_RE = re.compile(r'"([^"\\\n]*(?:\\.[^"\\\n]*)*)"')
_FORMAT_TAG_RE = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9:]*)>")
_ANY_ANGLE_RE = re.compile(r"<<[A-Za-z][A-Za-z0-9_-]*>|</?[A-Za-z][A-Za-z0-9:]*>")
_LUA_STRING_RE = re.compile(r'"(?:\\.|[^"\\])*"')
_LUA_COMPARE_RE = re.compile(r'(?:==|~=)\s*("(?:\\.|[^"\\])*")')
_URL_RE = re.compile(r"https?://[^\s<>）)]+")
_PATH_RE = re.compile(r"(?<![/:A-Za-z0-9_.-])(?:[A-Za-z0-9_.-]+/)+(?!/)")
_OPTION_RE = re.compile(r"\b[a-z][a-z0-9_]*(?:_dir|_file|_path)\b")
_QUOTED_COMMAND_RE = re.compile(r"(?<![A-Za-z])'([^'\n]{1,24})'(?![A-Za-z])")
_NUMBER_RE = re.compile(r"(?<![A-Za-z0-9])\d+(?:\.\d+)?(?![A-Za-z0-9])")
_W_CONTENT_RE = re.compile(r"<w>([^<>\n]*)</w>")


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _single_fragment(text: str, fragment: str, path: str) -> None:
    if text.count(fragment) != 1:
        raise RuntimeError(
            f"{path}: expected exactly one consumer fragment {fragment!r}"
        )
    return None


def _effective_entries(blobs: dict[str, bytes], path: str):
    text = blobs[path].decode("utf-8", errors="strict")
    entries = parse_db_keys(text, path)
    effective, overrides = merge_desc_sequence(entries)
    if overrides:
        raise RuntimeError(f"{path}: TextDB overrides are forbidden: {overrides}")
    empty = [
        {"raw_key": entry.raw_key, "key_line": entry.key_line}
        for entry in entries if not _desc_display(entry.value)
    ]
    if empty:
        raise RuntimeError(f"{path}: empty TextDB values are forbidden: {empty}")
    return entries, effective


def _help_entries(blobs: dict[str, bytes], path: str):
    entries, effective = _effective_entries(blobs, path)
    for entry in entries:
        canonical = lowercase_string(entry.raw_key)
        if not _HELP_KEY_RE.fullmatch(entry.raw_key) or canonical != entry.raw_key:
            raise RuntimeError(
                f"{path}:{entry.key_line}: invalid exact HelpDB key "
                f"{entry.raw_key!r}"
            )
    return entries, effective


def _faq_entries(blobs: dict[str, bytes], path: str):
    entries, effective = _effective_entries(blobs, path)
    by_kind: dict[str, dict[str, object]] = {"q": {}, "a": {}}
    order: list[str] = []
    for entry in entries:
        canonical = lowercase_string(entry.raw_key)
        match = _FAQ_KEY_RE.fullmatch(canonical)
        if not match:
            raise RuntimeError(
                f"{path}:{entry.key_line}: invalid FAQDB key {entry.raw_key!r}"
            )
        kind, suffix = match.groups()
        if kind == "q":
            order.append(suffix)
        by_kind[kind][suffix] = entry
    return entries, effective, by_kind, order


def _preprocessor_guards(text: str) -> list[tuple[int, tuple[str, ...]]]:
    """Return the active lexical guard stack at each line start.

    This is evidence only, not a C preprocessor evaluator.  It recognizes the
    simple guards surrounding current Help key literals and fails on unbalanced
    frames so a consumer edit cannot silently erase lifecycle evidence.
    """
    stack: list[str] = []
    result: list[tuple[int, tuple[str, ...]]] = []
    for lineno, line in enumerate(text.split("\n"), start=1):
        stripped = line.strip()
        if stripped.startswith("#ifdef "):
            stack.append(stripped[7:].strip())
        elif stripped.startswith("#ifndef "):
            stack.append("!" + stripped[8:].strip())
        elif stripped.startswith("#if "):
            stack.append(stripped[4:].strip())
        elif stripped.startswith("#elif "):
            if not stack:
                raise RuntimeError("preprocessor #elif without frame")
            stack[-1] = stripped[6:].strip()
        elif stripped == "#else":
            if not stack:
                raise RuntimeError("preprocessor #else without frame")
            stack[-1] = "else(" + stack[-1] + ")"
        elif stripped.startswith("#endif"):
            if not stack:
                raise RuntimeError("preprocessor #endif without frame")
            stack.pop()
        result.append((lineno, tuple(stack)))
    if stack:
        raise RuntimeError(f"unclosed preprocessor guard(s): {stack}")
    return result


def _extract_help_consumers(
    blobs: dict[str, bytes], keys: set[str]
) -> dict[str, list[dict[str, object]]]:
    facts: dict[str, list[dict[str, object]]] = {key: [] for key in keys}
    for path in HELP_CONSUMER_PATHS:
        text = blobs[path].decode("utf-8", errors="strict")
        guards = dict(_preprocessor_guards(text))
        literal_ordinals: Counter[str] = Counter()
        for match in _STRING_LITERAL_RE.finditer(text):
            literal = match.group(1)
            literal_ordinals[literal] += 1
            if literal not in keys:
                continue
            line = _line_number(text, match.start())
            facts[literal].append({
                "anchor": f'{path}@"{literal}"#{literal_ordinals[literal]}',
                "guards": list(guards[line]),
                "path": path,
            })
    return facts


def _verify_consumers(blobs: dict[str, bytes]) -> dict[str, str]:
    required = {
        DATABASE_CC: (
            'TextDB("help", "database/",',
            '{ "help.txt"      // database for outsourced help texts',
            'TextDB("FAQ", "database/",',
            '{ "FAQ.txt",      // database for Frequently Asked Questions',
            "string getHelpString(const string &topic)",
            "string help = _query_database(HelpDB, topic, false, true);",
            "vector<string> getAllFAQKeys()",
            'return _database_find_keys(FAQDB.get(), "^q.+", false);',
            "string getFAQ_Question(const string &key)",
            "string getFAQ_Answer(const string &question)",
            'string key = "a" + question.substr(1, question.length()-1);',
            "string val = unwrap_desc(_query_database(FAQDB, key, false, true));",
            'val = replace_all(val, "\\n\\n*", "\\n•");',
        ),
        DATABASE_H: (
            "string getHelpString(const string &topic);",
            "vector<string> getAllFAQKeys();",
            "string getFAQ_Question(const string &key);",
            "string getFAQ_Answer(const string &question);",
        ),
        COMMAND_CC: (
            "static void _handle_FAQ()",
            "vector<string> question_keys = getAllFAQKeys();",
            "string question = getFAQ_Question(question_keys[i]);",
            "string answer = getFAQ_Answer(key);",
            'answer = make_stringf(T_("Q: %s\\n%s"),',
            "void show_specific_helps(const vector<string> keys)",
            "string help = getHelpString(key);",
            'for (const string &line : split_string("\\n", help, false, true))\n'
            "            formatted_lines.push_back(formatted_string::parse_string(line));",
        ),
        MENU_CC: (
            "show_specific_help(_title_prompt_help_tag);",
            "show_specific_help(help_key());",
        ),
    }
    locations: dict[str, str] = {}
    for path, fragments in required.items():
        text = blobs[path].decode("utf-8", errors="strict")
        for fragment in fragments:
            _single_fragment(text, fragment, path)
            locations[f"{path}:{fragment}"] = f"{path}@{fragment}"
    return locations


def _accepted_format_tags(blobs: dict[str, bytes]) -> set[str]:
    colour = blobs[COLOUR_CC].decode("utf-8", errors="strict")
    match = re.search(
        r"static const char\* const cols\[(\d+)\]\s*=\s*\{(.*?)\};",
        colour,
        re.DOTALL,
    )
    if not match:
        raise RuntimeError(f"{COLOUR_CC}: terminal colour table changed")
    colours = set(re.findall(r'"([^"\n]+)"', match.group(2)))
    if len(colours) != int(match.group(1)):
        raise RuntimeError(f"{COLOUR_CC}: terminal colour table is ambiguous")
    colours.update({"lightgray", "darkgray"})
    format_text = blobs[FORMAT_CC].decode("utf-8", errors="strict")
    for fragment in ('if (tag == "h")', 'if (tag == "w")'):
        _single_fragment(format_text, fragment, FORMAT_CC)
    return colours | {"h", "w"}


def _markup_facts(value: str, allowed: set[str]) -> dict[str, object]:
    tags: list[dict[str, object]] = []
    unknown_angles: list[dict[str, object]] = []
    malformed: list[dict[str, object]] = []
    index = 0
    while index < len(value):
        start = value.find("<", index)
        if start < 0:
            break
        if start + 1 < len(value) and value[start + 1] == "<":
            match = _ANY_ANGLE_RE.match(value, start)
            if match:
                unknown_angles.append({
                    "line": _line_number(value, start),
                    "raw": match.group(0),
                })
                index = match.end()
            else:
                index = start + 2
            continue
        end = value.find(">", start + 1)
        newline = value.find("\n", start + 1)
        if end < 0 or (newline >= 0 and newline < end):
            malformed.append({
                "line": _line_number(value, start),
                "raw": value[start:newline if newline >= 0 else len(value)],
            })
            index = start + 1
            continue
        raw = value[start:end + 1]
        match = _FORMAT_TAG_RE.fullmatch(raw)
        if not match:
            malformed.append({"line": _line_number(value, start), "raw": raw})
        elif match.group(2) in allowed:
            tags.append({
                "closing": bool(match.group(1)),
                "line": _line_number(value, start),
                "name": match.group(2),
                "raw": raw,
            })
        else:
            unknown_angles.append({
                "line": _line_number(value, start),
                "raw": raw,
            })
        index = end + 1

    stack: list[str] = []
    errors: list[str] = []
    for tag in tags:
        name = str(tag["name"])
        if not tag["closing"]:
            stack.append(name)
        elif not stack or stack[-1] != name:
            errors.append(f"line {tag['line']}: unexpected </{name}>")
        else:
            stack.pop()
    errors.extend(f"unclosed <{name}>" for name in reversed(stack))
    sequence = [str(tag["raw"]) for tag in tags]
    unknown_sequence = [str(tag["raw"]) for tag in unknown_angles]
    return {
        "balance_errors": errors,
        "malformed": malformed,
        "tag_counts": dict(sorted(Counter(sequence).items())),
        "tag_sequence": sequence,
        "technical_angle_counts": dict(sorted(Counter(unknown_sequence).items())),
        "technical_angle_sequence": unknown_sequence,
    }


def _lua_facts(value: str) -> dict[str, object]:
    blocks: list[dict[str, object]] = []
    errors: list[str] = []
    index = 0
    while index < len(value):
        start = value.find("{{", index)
        stray = value.find("}}", index)
        if stray >= 0 and (start < 0 or stray < start):
            errors.append(f"line {_line_number(value, stray)}: unmatched }}}}")
            index = stray + 2
            continue
        if start < 0:
            break
        end = value.find("}}", start + 2)
        if end < 0:
            errors.append(f"line {_line_number(value, start)}: unbalanced {{{{")
            break
        body = value[start + 2:end]
        if not body.strip():
            errors.append(f"line {_line_number(value, start)}: empty Lua block")
        strings = _LUA_STRING_RE.findall(body)
        skeleton = _LUA_STRING_RE.sub('"<display>"', body)
        comparisons = _LUA_COMPARE_RE.findall(body)
        blocks.append({
            "comparison_literals": comparisons,
            "display_literal_count": len(strings) - len(comparisons),
            "line": _line_number(value, start),
            "skeleton": skeleton,
        })
        index = end + 2
    return {"blocks": blocks, "errors": errors}


def _clean_url(raw: str) -> str:
    return raw.rstrip(".,;:!?。；：！？、")


def _token_facts(value: str, allowed_tags: set[str]) -> dict[str, object]:
    markup = _markup_facts(value, allowed_tags)
    lua = _lua_facts(value)
    urls = [_clean_url(match.group(0)) for match in _URL_RE.finditer(value)]
    paths = [match.group(0) for match in _PATH_RE.finditer(value)]
    quoted = [match.group(1) for match in _QUOTED_COMMAND_RE.finditer(value)]
    numbers = [match.group(0) for match in _NUMBER_RE.finditer(value)]
    w_contents = [match.group(1) for match in _W_CONTENT_RE.finditer(value)]
    options = _OPTION_RE.findall(value)
    return {
        "blank_line_bullet_count": value.count("\n\n*"),
        "bullet_line_count": sum(
            1 for line in value.split("\n") if re.match(r"^\s*\* ", line)
        ),
        "lua": lua,
        "markup": markup,
        "numbers": numbers,
        "option_literals": options,
        "path_literals": paths,
        "quoted_command_literals": quoted,
        "urls": urls,
        "w_contents": w_contents,
    }


def _contract_comparison(
    english: dict[str, object], chinese: dict[str, object]
) -> dict[str, bool]:
    en_markup = english["markup"]
    zh_markup = chinese["markup"]
    en_lua = english["lua"]
    zh_lua = chinese["lua"]
    assert isinstance(en_markup, dict) and isinstance(zh_markup, dict)
    assert isinstance(en_lua, dict) and isinstance(zh_lua, dict)
    return {
        "blank_line_bullet_count": english["blank_line_bullet_count"]
        == chinese["blank_line_bullet_count"],
        "bullet_line_count": english["bullet_line_count"]
        == chinese["bullet_line_count"],
        "format_tag_counts": en_markup["tag_counts"] == zh_markup["tag_counts"],
        "format_tag_sequence": en_markup["tag_sequence"] == zh_markup["tag_sequence"],
        "lua_block_count": len(en_lua["blocks"]) == len(zh_lua["blocks"]),
        "lua_comparison_literals": [
            block["comparison_literals"] for block in en_lua["blocks"]
        ] == [block["comparison_literals"] for block in zh_lua["blocks"]],
        "lua_control_skeleton": [block["skeleton"] for block in en_lua["blocks"]]
        == [block["skeleton"] for block in zh_lua["blocks"]],
        "numbers": english["numbers"] == chinese["numbers"],
        "option_literals": english["option_literals"] == chinese["option_literals"],
        "path_literals": english["path_literals"] == chinese["path_literals"],
        "quoted_command_literals": english["quoted_command_literals"]
        == chinese["quoted_command_literals"],
        "technical_angle_counts": en_markup["technical_angle_counts"]
        == zh_markup["technical_angle_counts"],
        "technical_angle_sequence": en_markup["technical_angle_sequence"]
        == zh_markup["technical_angle_sequence"],
        "urls": english["urls"] == chinese["urls"],
        "w_contents": english["w_contents"] == chinese["w_contents"],
    }


def _token_errors(
    language: str, identity: str, facts: dict[str, object]
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    lua = facts["lua"]
    assert isinstance(lua, dict)
    # Markup anomalies remain exact inventory facts and review candidates.
    # The audit is expected to find existing bad tags; making them inventory
    # blockers would prevent freezing the very collection under review.  Lua
    # parse failure is different because it defeats control/display separation.
    if lua["errors"]:
        errors.append({
            "identity": identity,
            "kind": f"{language}-lua-errors",
            "detail": json.dumps(lua["errors"], ensure_ascii=False, sort_keys=True),
        })
    return errors


def _help_group(key: str) -> str:
    if key in {"pick-up", "known-menu"}:
        return "items, pickup, and known-items menus"
    if key in {"skill-menu", "spell-library"}:
        return "skills and spell library"
    if key in {"macro-menu", "console-keycodes", "wiz-monster"}:
        return "macros, platform keys, and wizard"
    return "map, search, travel, and annotation"


def _faq_group(suffix: str) -> str:
    if suffix in {"userdir", "interact"}:
        return "environment and community interaction"
    if suffix in {"version", "beta", "bug", "idea", "help", "changes", "tiles lag"}:
        return "project, release, support, and performance"
    return "gameplay goals, survival, and mechanics"


def _fact_sha(row: dict[str, object]) -> str:
    return hashlib.sha256(json.dumps(
        row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")).hexdigest()


def _pair_token_facts(
    question: str, answer: str, allowed_tags: set[str]
) -> dict[str, object]:
    return {
        "question": _token_facts(question, allowed_tags),
        "answer": _token_facts(answer, allowed_tags),
    }


def _pair_contract(
    english: dict[str, object], chinese: dict[str, object]
) -> dict[str, dict[str, bool]]:
    return {
        part: _contract_comparison(english[part], chinese[part])
        for part in ("question", "answer")
    }


def build_payload(baseline: str) -> dict[str, object]:
    blobs = {path: git_show_blob(baseline, path) for path in INPUT_PATHS}
    return build_payload_from_blobs(baseline, blobs)


def build_payload_from_blobs(
    baseline: str, blobs: dict[str, bytes]
) -> dict[str, object]:
    if set(blobs) != set(INPUT_PATHS):
        raise RuntimeError(
            "help inventory input manifest mismatch: "
            f"missing={sorted(set(INPUT_PATHS) - set(blobs))} "
            f"extra={sorted(set(blobs) - set(INPUT_PATHS))}"
        )
    consumer_locations = _verify_consumers(blobs)
    allowed_tags = _accepted_format_tags(blobs)

    _en_help_entries, en_help = _help_entries(blobs, HELP_EN)
    _zh_help_entries, zh_help = _help_entries(blobs, HELP_ZH)
    help_union = set(en_help) | set(zh_help)
    help_consumers = _extract_help_consumers(blobs, help_union)

    _en_faq_entries, _en_faq_effective, en_faq, en_faq_order = _faq_entries(
        blobs, FAQ_EN
    )
    _zh_faq_entries, _zh_faq_effective, zh_faq, zh_faq_order = _faq_entries(
        blobs, FAQ_ZH
    )
    en_q = set(en_faq["q"])
    en_a = set(en_faq["a"])
    zh_q = set(zh_faq["q"])
    zh_a = set(zh_faq["a"])
    faq_union = en_q | en_a | zh_q | zh_a

    blocking: list[dict[str, str]] = []
    for language, questions, answers in (
        ("english", en_q, en_a),
        ("chinese", zh_q, zh_a),
    ):
        for suffix in sorted(questions - answers):
            blocking.append({
                "identity": f"faq:{suffix}",
                "kind": f"{language}-question-without-answer",
                "detail": "FAQ question suffix lacks its matching answer",
            })
        for suffix in sorted(answers - questions):
            blocking.append({
                "identity": f"faq:{suffix}",
                "kind": f"{language}-answer-without-question",
                "detail": "FAQ answer suffix lacks its matching question",
            })
    for suffix in sorted((en_q | en_a) - (zh_q | zh_a)):
        blocking.append({
            "identity": f"faq:{suffix}",
            "kind": "english-faq-pair-missing-chinese",
            "detail": "English FAQ identity has no complete Chinese identity",
        })
    for suffix in sorted((zh_q | zh_a) - (en_q | en_a)):
        blocking.append({
            "identity": f"faq:{suffix}",
            "kind": "chinese-faq-pair-missing-english",
            "detail": "Chinese FAQ identity has no complete English identity",
        })
    if en_faq_order != zh_faq_order:
        blocking.append({
            "identity": "faq:__order__",
            "kind": "english-chinese-question-order-mismatch",
            "detail": json.dumps(
                {"english": en_faq_order, "chinese": zh_faq_order},
                ensure_ascii=False,
                sort_keys=True,
            ),
        })

    inventory: list[dict[str, object]] = []
    for key in sorted(help_union):
        en = en_help.get(key)
        zh = zh_help.get(key)
        english = _desc_display(en.value) if en else None
        chinese = _desc_display(zh.value) if zh else None
        identity = f"help:{key}"
        producers = help_consumers[key]
        if not producers:
            blocking.append({
                "identity": identity,
                "kind": "help-textdb-without-consumer-evidence",
                "detail": "HelpDB key has no exact literal in the audited consumer set",
            })
        guarded_console = bool(producers) and all(
            "!USE_TILE_LOCAL" in fact["guards"] for fact in producers
        )
        wizard_only = bool(producers) and all(
            fact["path"] == WIZ_MON_CC for fact in producers
        )
        lifecycle = (
            "console-only" if guarded_console else
            "wizard-only" if wizard_only else
            "current-player-help"
        )
        en_tokens = _token_facts(english or "", allowed_tags)
        zh_tokens = _token_facts(chinese or "", allowed_tags)
        comparison = _contract_comparison(en_tokens, zh_tokens)
        structural = sorted(field for field, equal in comparison.items() if not equal)
        row: dict[str, object] = {
            "identity": identity,
            "kind": "help",
            "key": key,
            "lifecycle": lifecycle,
            "english": english,
            "chinese": chinese,
            "english_key_line": en.key_line if en else None,
            "chinese_key_line": zh.key_line if zh else None,
            "producer": producers,
            "consumer": {
                "lookup": consumer_locations[
                    f"{DATABASE_CC}:string help = _query_database(HelpDB, topic, false, true);"
                ],
                "display": consumer_locations[
                    f'{COMMAND_CC}:for (const string &line : split_string("\\n", help, false, true))\n'
                    "            formatted_lines.push_back(formatted_string::parse_string(line));"
                ],
                "dynamic_menu": [
                    consumer_locations[f"{MENU_CC}:show_specific_help(_title_prompt_help_tag);"],
                    consumer_locations[f"{MENU_CC}:show_specific_help(help_key());"],
                ],
            },
            "display_context": "Specific HelpDB topic rendered by the formatted help scroller.",
            "dependency_group": _help_group(key),
            "english_tokens": en_tokens,
            "chinese_tokens": zh_tokens,
            "token_contract_equal": comparison,
            "structural_differences": structural,
        }
        row["fact_sha256"] = _fact_sha(row)
        inventory.append(row)
        blocking.extend(_token_errors("english", identity, en_tokens))
        blocking.extend(_token_errors("chinese", identity, zh_tokens))
        for field in ("lua_block_count", "lua_comparison_literals", "lua_control_skeleton"):
            if not comparison[field]:
                blocking.append({
                    "identity": identity,
                    "kind": f"lua-{field.replace('_', '-')}-mismatch",
                    "detail": "EN/ZH embedded Lua control structure differs",
                })
        if en is None:
            blocking.append({
                "identity": identity,
                "kind": "help-missing-english",
                "detail": "Help identity is absent from English HelpDB",
            })
        if zh is None:
            blocking.append({
                "identity": identity,
                "kind": "help-missing-chinese",
                "detail": "Help identity is absent from Chinese HelpDB",
            })

    faq_consumer = {
        "answer_lookup": consumer_locations[
            f"{DATABASE_CC}:string val = unwrap_desc(_query_database(FAQDB, key, false, true));"
        ],
        "bullet_transform": consumer_locations[
            f'{DATABASE_CC}:val = replace_all(val, "\\n\\n*", "\\n•");'
        ],
        "key_enumeration": consumer_locations[
            f'{DATABASE_CC}:return _database_find_keys(FAQDB.get(), "^q.+", false);'
        ],
        "menu": consumer_locations[f"{COMMAND_CC}:static void _handle_FAQ()"],
        "question_lookup": consumer_locations[
            f"{COMMAND_CC}:string question = getFAQ_Question(question_keys[i]);"
        ],
    }
    for suffix in en_faq_order + [
        value for value in sorted(faq_union) if value not in set(en_faq_order)
    ]:
        en_question = en_faq["q"].get(suffix)
        en_answer = en_faq["a"].get(suffix)
        zh_question = zh_faq["q"].get(suffix)
        zh_answer = zh_faq["a"].get(suffix)
        english = {
            "question": _desc_display(en_question.value) if en_question else None,
            "answer": _desc_display(en_answer.value) if en_answer else None,
        }
        chinese = {
            "question": _desc_display(zh_question.value) if zh_question else None,
            "answer": _desc_display(zh_answer.value) if zh_answer else None,
        }
        identity = f"faq:{suffix}"
        en_tokens = _pair_token_facts(
            english["question"] or "", english["answer"] or "", allowed_tags
        )
        zh_tokens = _pair_token_facts(
            chinese["question"] or "", chinese["answer"] or "", allowed_tags
        )
        comparison = _pair_contract(en_tokens, zh_tokens)
        structural = sorted(
            f"{part}.{field}"
            for part in ("question", "answer")
            for field, equal in comparison[part].items()
            if not equal
        )
        row = {
            "identity": identity,
            "kind": "faq",
            "key": suffix,
            "lifecycle": "current-faq-menu-entry",
            "english": english,
            "chinese": chinese,
            "english_key_lines": {
                "question": en_question.key_line if en_question else None,
                "answer": en_answer.key_line if en_answer else None,
            },
            "chinese_key_lines": {
                "question": zh_question.key_line if zh_question else None,
                "answer": zh_answer.key_line if zh_answer else None,
            },
            "producer": {
                "english_question_order": (
                    en_faq_order.index(suffix) if suffix in en_faq_order else None
                ),
                "chinese_question_order": (
                    zh_faq_order.index(suffix) if suffix in zh_faq_order else None
                ),
                "source_note": (
                    "File order is authoring evidence; runtime menu order is DBM "
                    "iteration order and is not guaranteed by the current consumer."
                ),
            },
            "consumer": faq_consumer,
            "display_context": (
                "FAQ menu question plus unwrapped answer; blank lines before "
                "asterisk bullets become Unicode bullets."
            ),
            "dependency_group": _faq_group(suffix),
            "english_tokens": en_tokens,
            "chinese_tokens": zh_tokens,
            "token_contract_equal": comparison,
            "structural_differences": structural,
        }
        row["fact_sha256"] = _fact_sha(row)
        inventory.append(row)
        for part in ("question", "answer"):
            blocking.extend(_token_errors(
                f"english-{part}", identity, en_tokens[part]
            ))
            blocking.extend(_token_errors(
                f"chinese-{part}", identity, zh_tokens[part]
            ))

    identities = [str(row["identity"]) for row in inventory]
    if len(identities) != len(set(identities)):
        raise RuntimeError("help/FAQ inventory identity uniqueness invariant failed")
    expected = [f"help:{key}" for key in sorted(help_union)] + [
        f"faq:{suffix}" for suffix in en_faq_order
    ] + [
        f"faq:{suffix}" for suffix in sorted(faq_union) if suffix not in set(en_faq_order)
    ]
    if identities != expected:
        raise RuntimeError("help/FAQ inventory order invariant failed")

    payload: dict[str, object] = {
        "baseline": baseline,
        "glossary_sha256": hashlib.sha256(blobs[GLOSSARY_MD]).hexdigest(),
        "inputs": {
            path: {"sha256": hashlib.sha256(blobs[path]).hexdigest()}
            for path in INPUT_PATHS
        },
        "help_en_keys": sorted(en_help),
        "help_zh_keys": sorted(zh_help),
        "help_union_keys": sorted(help_union),
        "help_en_minus_zh": sorted(set(en_help) - set(zh_help)),
        "help_zh_minus_en": sorted(set(zh_help) - set(en_help)),
        "faq_en_question_order": en_faq_order,
        "faq_zh_question_order": zh_faq_order,
        "faq_en_question_minus_answer": sorted(en_q - en_a),
        "faq_en_answer_minus_question": sorted(en_a - en_q),
        "faq_zh_question_minus_answer": sorted(zh_q - zh_a),
        "faq_zh_answer_minus_question": sorted(zh_a - zh_q),
        "faq_en_minus_zh": sorted((en_q | en_a) - (zh_q | zh_a)),
        "faq_zh_minus_en": sorted((zh_q | zh_a) - (en_q | en_a)),
        "faq_runtime_order_guaranteed": False,
        "explicit_exclusions": [
            "crawl-ref/source/dat/crawl_manual.txt",
            "crawl-ref/source/dat/quickstart.txt",
            "crawl-ref/source/dat/macros_guide.txt",
            "crawl-ref/source/dat/options_guide.txt",
            "crawl-ref/source/dat/tiles_help.txt",
            "generic ?/ lookup descriptions outside HelpDB and FAQDB",
        ],
        "blocking_violations": sorted(
            blocking,
            key=lambda value: (value["identity"], value["kind"], value["detail"]),
        ),
        "structural_review_candidates": [
            row["identity"] for row in inventory if row["structural_differences"]
        ],
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


def parse_review(
    review_input: AuditInput,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    text = review_input.text
    if text.count(STRICT_REVIEW_BEGIN) != 1 or text.count(STRICT_REVIEW_END) != 1:
        raise RuntimeError("strict Help/FAQ review block is missing or duplicated")
    block = text.split(STRICT_REVIEW_BEGIN, 1)[1].split(STRICT_REVIEW_END, 1)[0]
    if not block.startswith("\n") or not block.endswith("\n"):
        raise RuntimeError("strict Help/FAQ review framing is invalid")
    lines = block[1:-1].splitlines()
    if len(lines) < 4 or lines[1] != "```jsonl" or lines[-1] != "```":
        raise RuntimeError("strict Help/FAQ review structure is invalid")
    metadata = _load_json(lines[0], "Help/FAQ review metadata")
    expected_meta = {
        "baseline", "glossary_sha256", "identity_count", "inventory_sha256"
    }
    if not isinstance(metadata, dict) or set(metadata) != expected_meta:
        raise RuntimeError("strict Help/FAQ review metadata fields are invalid")
    if lines[0] != json.dumps(
        metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ):
        raise RuntimeError("strict Help/FAQ review metadata is not canonical JSON")
    if (
        not isinstance(metadata["baseline"], str)
        or not re.fullmatch(r"[0-9a-f]{40}", metadata["baseline"])
        or not isinstance(metadata["glossary_sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", metadata["glossary_sha256"])
        or not isinstance(metadata["inventory_sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", metadata["inventory_sha256"])
        or isinstance(metadata["identity_count"], bool)
        or not isinstance(metadata["identity_count"], int)
        or metadata["identity_count"] < 0
    ):
        raise RuntimeError("strict Help/FAQ review metadata values are invalid")
    cards: list[dict[str, object]] = []
    for number, line in enumerate(lines[2:-1], start=3):
        card = _load_json(line, f"Help/FAQ card at block line {number}")
        if not isinstance(card, dict) or set(card) != STRICT_CARD_FIELDS:
            raise RuntimeError("strict Help/FAQ evidence-card fields are invalid")
        if line != json.dumps(
            card, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ):
            raise RuntimeError("strict Help/FAQ card is not canonical JSON")
        cards.append(card)
    return metadata, cards


def _consumer_anchor_values(consumer: dict[str, object]) -> list[str]:
    anchors: list[str] = []
    for key in sorted(consumer):
        value = consumer[key]
        if isinstance(value, list):
            anchors.extend(str(item) for item in value)
        elif value is not None:
            anchors.append(str(value))
    return anchors


def _mechanical_fields(row: dict[str, object]) -> dict[str, object]:
    evidence: list[str] = []
    if row["kind"] == "help":
        evidence.extend(str(fact["anchor"]) for fact in row["producer"])
        evidence.append(
            f"{HELP_EN}@{row['key']}"
            if row["english_key_line"] is not None else HELP_EN
        )
        evidence.append(
            f"{HELP_ZH}@{row['key']}"
            if row["chinese_key_line"] is not None else HELP_ZH
        )
    else:
        suffix = row["key"]
        for path, field in (
            (FAQ_EN, "english_key_lines"),
            (FAQ_ZH, "chinese_key_lines"),
        ):
            lines = row[field]
            present: list[str] = []
            if lines["question"] is not None:
                present.append(f"{path}@q:{suffix}")
            if lines["answer"] is not None:
                present.append(f"{path}@a:{suffix}")
            evidence.extend(present or [path])
    evidence.extend(_consumer_anchor_values(row["consumer"]))
    return {
        "consumer": row["consumer"],
        "current_chinese": row["chinese"],
        "current_english": row["english"],
        "dependency_group": row["dependency_group"],
        "display_context": row["display_context"],
        "evidence_locations": evidence,
        "fact_sha256": row["fact_sha256"],
        "identity": row["identity"],
        "lifecycle": row["lifecycle"],
        "producer": row["producer"],
        "production_facts": row,
    }


def _typed_equal(left: object, right: object) -> bool:
    return json.dumps(
        left, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ) == json.dumps(
        right, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _specific(value: object) -> bool:
    return _nonempty(value) and value.strip().lower().strip(".。;；") not in {
        "n/a", "none", "not applicable", "tbd", "todo", "unknown",
        "不适用", "待定", "无",
    }


def _proposal_valid(current: object, proposal: object) -> bool:
    if isinstance(current, str):
        return _nonempty(proposal) and proposal != current
    if isinstance(current, dict):
        return (
            isinstance(proposal, dict)
            and set(proposal) == set(current)
            and all(_nonempty(value) for value in proposal.values())
            and not _typed_equal(current, proposal)
        )
    return False


def review_coverage(
    payload: dict[str, object], review_input: AuditInput
) -> dict[str, object]:
    metadata, cards = parse_review(review_input)
    inventory = payload["inventory"]
    assert isinstance(inventory, list)
    inventory_ids = [row["identity"] for row in inventory]
    review_ids = [card["identity"] for card in cards]
    expected = {row["identity"]: row for row in inventory}
    mismatches: list[str] = []
    invalid: list[str] = []
    for card in cards:
        identity = card["identity"]
        if identity in expected:
            for field, value in _mechanical_fields(expected[identity]).items():
                if not _typed_equal(card[field], value):
                    mismatches.append(f"{identity}:{field}")
        conclusion = card["terminal_conclusion"]
        proposal = card["proposed_translation"]
        if conclusion not in TERMINAL_CONCLUSIONS:
            invalid.append(f"{identity}:terminal_conclusion")
        if conclusion in {"adjust", "retranslate"}:
            if not _proposal_valid(card["current_chinese"], proposal):
                invalid.append(f"{identity}:proposed_translation")
        elif proposal is not None:
            invalid.append(f"{identity}:unexpected_proposal")
        for field in (
            "actual_behavior", "glossary_authority", "reviewer_rationale",
            "reentry_trigger",
        ):
            if not _nonempty(card[field]):
                invalid.append(f"{identity}:{field}")
        if card["confidence"] not in CONFIDENCE_LEVELS:
            invalid.append(f"{identity}:confidence")
        if (
            not isinstance(card["rejected_alternatives"], list)
            or any(not _nonempty(value) for value in card["rejected_alternatives"])
        ):
            invalid.append(f"{identity}:rejected_alternatives")
        deferred = isinstance(conclusion, str) and conclusion.startswith("defer ")
        if deferred:
            for field in ("deferral_reason", "deferral_owner", "reentry_trigger"):
                if not _specific(card[field]):
                    invalid.append(f"{identity}:{field}")
        elif card["deferral_reason"] is not None or card["deferral_owner"] is not None:
            invalid.append(f"{identity}:unexpected_deferral_fields")

    binding = {
        "baseline": metadata["baseline"] == payload["baseline"],
        "glossary_sha256": metadata["glossary_sha256"] == payload["glossary_sha256"],
        "identity_count": metadata["identity_count"] == len(inventory),
        "inventory_sha256": metadata["inventory_sha256"] == payload["inventory_sha256"],
    }
    inventory_duplicates = sorted(
        key for key, count in Counter(inventory_ids).items() if count > 1
    )
    review_duplicates = sorted(
        key for key, count in Counter(review_ids).items() if count > 1
    )
    inventory_minus_review = sorted(set(inventory_ids) - set(review_ids))
    review_minus_inventory = sorted(set(review_ids) - set(inventory_ids))
    order_matches = review_ids == inventory_ids
    coverage_equal = (
        all(binding.values())
        and len(review_ids) == len(inventory_ids)
        and not inventory_duplicates
        and not review_duplicates
        and not inventory_minus_review
        and not review_minus_inventory
        and order_matches
        and not mismatches
        and not invalid
    )
    return {
        **review_input_metadata(review_input),
        "evidence_card_count": len(cards),
        "terminal_conclusion_counts": dict(sorted(Counter(
            card["terminal_conclusion"] for card in cards
            if isinstance(card["terminal_conclusion"], str)
        ).items())),
        "binding_matches": binding,
        "inventory_duplicate_identities": inventory_duplicates,
        "duplicate_evidence_cards": review_duplicates,
        "inventory_minus_review": inventory_minus_review,
        "review_minus_inventory": review_minus_inventory,
        "canonical_card_order": order_matches,
        "mismatched_mechanical_fields": sorted(mismatches),
        "invalid_cards": sorted(invalid),
        "coverage_equal": coverage_equal,
    }


def candidate_agreement_from_payloads(
    payload: dict[str, object], review_input: AuditInput,
    candidate_payload: dict[str, object], candidate: str,
) -> dict[str, object]:
    coverage = review_coverage(payload, review_input)
    _metadata, cards = parse_review(review_input)
    candidate_rows = {
        row["identity"]: row for row in candidate_payload["inventory"]
    }
    translation_mismatches: list[str] = []
    for card in cards:
        identity = card["identity"]
        row = candidate_rows.get(identity)
        if row is None:
            translation_mismatches.append(identity)
            continue
        expected = (
            card["proposed_translation"]
            if card["terminal_conclusion"] in {"adjust", "retranslate"}
            else card["current_chinese"]
        )
        if not _typed_equal(row["chinese"], expected):
            translation_mismatches.append(identity)
    baseline_ids = [row["identity"] for row in payload["inventory"]]
    candidate_ids = [row["identity"] for row in candidate_payload["inventory"]]
    identity_equal = baseline_ids == candidate_ids
    zero_blockers = not candidate_payload["blocking_violations"]
    agrees = (
        coverage["coverage_equal"]
        and identity_equal
        and zero_blockers
        and not translation_mismatches
    )
    return {
        "candidate": candidate,
        "candidate_inventory_sha256": candidate_payload["inventory_sha256"],
        "candidate_identity_order_equal": identity_equal,
        "candidate_blocking_violations": candidate_payload["blocking_violations"],
        "translation_mismatches": sorted(translation_mismatches),
        "candidate_agrees": agrees,
    }


def candidate_agreement(
    payload: dict[str, object], review_input: AuditInput, candidate: str
) -> dict[str, object]:
    return candidate_agreement_from_payloads(
        payload, review_input, build_payload(candidate), candidate
    )


def _result_exit_code(payload: dict[str, object]) -> int:
    if payload["blocking_violations"]:
        return 1
    if "review_coverage" in payload and not payload["review_coverage"]["coverage_equal"]:
        return 1
    if "candidate_agreement" in payload and not payload["candidate_agreement"]["candidate_agrees"]:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-ref", default="HEAD")
    parser.add_argument("--candidate-ref")
    parser.add_argument("--inventory-output", default="/tmp/help-inventory.json")
    parser.add_argument("--review-results", type=Path)
    args = parser.parse_args()
    try:
        baseline = resolve_commit(args.baseline_ref)
        payload = build_payload(baseline)
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
        elif candidate:
            raise RuntimeError("--candidate-ref requires --review-results")
        out = write_inventory_output(
            args.inventory_output,
            json.dumps(payload, ensure_ascii=False, indent=1),
        )
    except (OSError, RuntimeError, UnicodeError, ValueError) as error:
        print(f"ERROR: Help/FAQ inventory failed: {error}", file=sys.stderr)
        return 2

    print(f"Help/FAQ inventory sha256: {payload['inventory_sha256']}")
    print(
        "Help EN/ZH/union identities: "
        f"{len(payload['help_en_keys'])}/{len(payload['help_zh_keys'])}/"
        f"{len(payload['help_union_keys'])}"
    )
    print(
        "FAQ EN/ZH question identities: "
        f"{len(payload['faq_en_question_order'])}/"
        f"{len(payload['faq_zh_question_order'])}"
    )
    print(f"total logical identities: {len(payload['inventory'])}")
    print(f"blocking violations: {len(payload['blocking_violations'])}")
    print(
        "structural review candidates: "
        + json.dumps(payload["structural_review_candidates"], ensure_ascii=False)
    )
    if "review_coverage" in payload:
        print("review coverage: " + json.dumps(
            payload["review_coverage"], ensure_ascii=False,
            sort_keys=True, separators=(",", ":")
        ))
    if "candidate_agreement" in payload:
        print("candidate agreement: " + json.dumps(
            payload["candidate_agreement"], ensure_ascii=False,
            sort_keys=True, separators=(",", ":")
        ))
    print(f"wrote {out}")
    return _result_exit_code(payload)


if __name__ == "__main__":
    raise SystemExit(main())
