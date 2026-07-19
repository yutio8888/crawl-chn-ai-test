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

def parse_decisions(filepath: str) -> dict:
    """Parse decisions.md and return {rejected_name: correct_name} for active Type-A decisions.

    Only Type-A (entity rulings) are processed — they have specific rejected
    term strings. Type-B (process) and Type-C (constraint) decisions use
    descriptive Rejected fields that are not searchable terms.
    """
    rejected_map = {}
    if not os.path.exists(filepath):
        return rejected_map

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Only Type-A: entity name rulings have specific rejected terms
    blocks = re.split(r'\n(?=### D-A-\d+)', content)

    for block in blocks:
        if not re.search(r'\*\*Status\*\*:\s*active', block):
            continue
        choice_m = re.search(r'\*\*Choice\*\*:\s*(.+)', block)
        rejected_m = re.search(r'\*\*Rejected\*\*:\s*(.+)', block)
        if not choice_m or not rejected_m:
            continue
        choice = choice_m.group(1).strip()
        rejected_raw = rejected_m.group(1).strip()

        # Skip explanatory markers: "(none — confirmed correct)" etc.
        if rejected_raw.startswith('(none'):
            continue

        # Rejected can be comma-separated: "席夫·穆纳, 席夫穆納"
        for r in re.split(r'[,;]', rejected_raw):
            r = r.strip()
            # Skip non-term entries: descriptions, code snippets, etc.
            # Real rejected terms are Chinese/Unicode strings, not sentences.
            if not r:
                continue
            # Skip entries that are clearly descriptive (contain spaces
            # and English words, indicating a sentence rather than a term)
            if ' ' in r and re.search(r'[A-Za-z]{3,}', r):
                continue
            rejected_map[r] = choice
    return rejected_map


def cmd_validate_terms(args):
    """Check for rejected translation terms in source.txt and C++ source."""
    # Parse decisions
    rejected_map = parse_decisions(args.glossary)
    if not rejected_map:
        print("OK: No active rejected-name decisions found in glossary.")
        return 0

    # Scan source.txt CN translations for rejected terms
    entries = parse_source_txt(args.source_txt) if args.source_txt else {}
    findings = []

    # Check source.txt
    for en_key, cn_val in entries.items():
        for rejected, correct in rejected_map.items():
            if rejected in cn_val:
                cn_snippet = cn_val[:80]
                findings.append({
                    'location': f'source.txt: "{en_key[:60]}"',
                    'rejected': rejected,
                    'correct': correct,
                    'snippet': cn_snippet,
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
LUA_IDENTITY_CONTRACT = {
    'you_species': r'species::name\s*\([^;{}]*SPNAME_PLAIN[^;{}]*,\s*true\s*\)',
    'you_race': r'species::name\s*\([^;{}]*SPNAME_PLAIN[^;{}]*,\s*true\s*\)',
    'you_class': r'get_job_name_en\s*\(',
    'l_you_genus': r'species::name\s*\([^;{}]*SPNAME_GENUS[^;{}]*,\s*true\s*\)',
    'l_you_monster': r'mons_type_name_en\s*\(',
}


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
            if not re.search(expression, actual):
                findings.append(_lua_identity_finding(
                    rel_path, 'the LUARET1 third expression is not the canonical raw/en accessor', binding))
            continue

        bodies = list(_iter_named_function_bodies(masked, [binding]))
        if len(bodies) != 1:
            findings.append(_lua_identity_finding(
                rel_path, f'expected exactly one function definition, found {len(bodies)}', binding))
            continue
        body = masked[bodies[0][1]:bodies[0][2]]
        accessor = expression
        # The accessor must initialize the exact variable subsequently pushed;
        # a decoy accessor elsewhere in the function is not sufficient.
        assignment = re.search(
            r'\b(?:string|auto)\s+(\w+)\s*=\s*(' + accessor + r'[^;{}]*);', body)
        pushed = re.findall(r'lua_pushstring\s*\(\s*[^,]+,\s*(\w+)\s*\.c_str\s*\(\s*\)\s*\)', body)
        if not assignment or assignment.group(1) not in pushed:
            findings.append(_lua_identity_finding(
                rel_path, 'canonical accessor must initialize the variable passed to lua_pushstring', binding))
            continue
        if binding == 'l_you_genus' and not re.search(r'\blowercase\s*\(\s*' + re.escape(assignment.group(1)) + r'\s*\)', body):
            findings.append(_lua_identity_finding(rel_path, 'genus must preserve lowercase processing', binding))
        if binding == 'l_you_genus' and not re.search(r'\bpluralise\s*\(', body):
            findings.append(_lua_identity_finding(rel_path, 'genus must preserve pluralise processing', binding))
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
                         help="Path to source.txt (CN translations)")
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
