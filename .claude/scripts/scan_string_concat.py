#!/usr/bin/env python3
"""
scan_string_concat.py — Tree-sitter-based C++ string concatenation scanner.

Detects bare (untranslated) string literals embedded in concatenation,
stream insertion, .append(), and compile-time adjacent-string expressions.
Complements scan_i18n.py by covering patterns regex cannot reliably see:
multi-line, chained <<, nested +, and .append() calls.

Usage:
    # Full scan
    scan_string_concat.py crawl-ref/source/

    # Specific files only
    scan_string_concat.py --files hiscores.cc,hints.cc

    # CI enforce mode (exit 2 if tree-sitter missing)
    scan_string_concat.py crawl-ref/source/ --require-parser --skip-low

    # Audit mode (include T_()-wrapped literals too)
    scan_string_concat.py crawl-ref/source/ --all

    # JSON output
    scan_string_concat.py crawl-ref/source/ --format json --json-output report.json

Dependencies: tree-sitter, tree-sitter-cpp (pip3 install tree-sitter tree-sitter-cpp)
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n_shared import CPP_SOURCE_EXTENSIONS, ScanCoverage, discover_source_files

# ── Tree-sitter availability ──────────────────────────────────────────────────

TREE_SITTER_AVAILABLE = False
_tscpp = None
_Language = None
_Parser = None

try:
    import tree_sitter_cpp as _tscpp
    from tree_sitter import Language as _Language
    from tree_sitter import Parser as _Parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    pass


# ── Configuration ─────────────────────────────────────────────────────────────

TRANSLATION_WRAPPERS = {"T_", "C_"}
"""Functions whose string-literal arguments are considered translated."""

TEXT_METHODS = {"append"}
"""Method names on std::string (or similar) that append text.
Expand to {"append", "assign", "insert", "replace"} in future versions."""

# Variable / receiver names that strongly suggest player-visible UI text
UI_VAR_NAMES = {
    "desc", "description", "text", "msg", "message",
    "name", "title", "summary", "info", "report",
    "short_desc", "long_desc", "death_desc",
    "prompt", "display", "status", "output",
    "help", "menu", "label", "tooltip", "note",
    "mapdesc", "lookup",
}

# File-path keywords: files that primarily deal with player-visible text
UI_FILE_KEYWORDS = {
    "hints", "hiscores", "tilereg", "describe", "menu",
    "ability", "notes", "chardump", "command", "directn",
    "item-name", "invent", "mon-info", "mon-death",
    "god-abil", "religion", "spl-damage", "spl-summoning",
    "output", "status", "player", "skills", "spells",
}

# Function-name keywords suggesting the enclosing function builds UI text
UI_FUNC_KEYWORDS = {
    "describe", "description", "menu", "prompt", "message",
    "hint", "score", "death", "ability", "spell", "skill",
    "name", "title", "tooltip", "help", "status", "note",
    "report", "summary", "display", "format", "print",
}

# Directories to skip during recursive walk
SKIP_DIRS = {"contrib", ".git", "worktrees", "__pycache__", "catch2-tests",
             "rltiles", "util"}

# Files to skip (third-party)
SKIP_FILES = {"catch_amalgamated.cc"}

# Regexes for exclusion and scoring
RE_FILE_PATH = re.compile(
    r'^(?:/|[A-Za-z]:\\|\./|\.\./)[^"]*\.[a-zA-Z]{2,4}$')
RE_MARKUP_TAG = re.compile(r'^</?[a-zA-Z][^>]*>$')
RE_COLOR_TAG = re.compile(r'^<(?:yellow|lightgrey|darkgrey|red|green|blue|'
                          r'magenta|cyan|white|w|c|b|magenta|brown)>$')
RE_FORMAT_ONLY = re.compile(
    r'^%'                       # leading %
    r'(?:[-+0 #]*)?'            # flags
    r'(?:\d+|\*)?'              # width
    r'(?:\.\d+)?'              # precision
    r'(?:l[du]|[sdxcunfFeEgG])'  # type
    r'$')
RE_SENTENCE_END = re.compile(r'[.!?](?:\s|$)')
RE_ALPHA = re.compile(r'[A-Za-z]')
RE_CJK = re.compile(r'[⺀-⿟⿰-鿿豈-﫿'
                    r'︰-﹏\U00020000-\U0002FFFF]')


# ── Utility Functions ─────────────────────────────────────────────────────────

def _text(node, source_bytes):
    """Extract source text from a tree-sitter node's byte range."""
    return source_bytes[node.start_byte:node.end_byte].decode(
        "utf-8", errors="replace")


def _has_alpha(s):
    """Check if string contains at least one ASCII letter."""
    return bool(RE_ALPHA.search(s))


def _has_cjk(s):
    """Check if string contains CJK characters."""
    return bool(RE_CJK.search(s))


def _is_markup_tag(s):
    """Check if a string is entirely a markup/color tag."""
    return bool(RE_COLOR_TAG.match(s) or RE_MARKUP_TAG.match(s))


def _is_format_only(s):
    """Check if a string is only a format specifier fragment."""
    return bool(RE_FORMAT_ONLY.match(s.strip()))


def _is_ascii_art(s):
    """Check if a string is ASCII art / table layout.
    - >70% non-alphanumeric non-whitespace characters (borders, separators)
    - OR >60% whitespace characters (spaced-out table headers)
    Combined with minimum length of 15 characters."""
    if len(s) < 15:
        return False
    total = len(s)
    whitespace_count = sum(1 for c in s if c.isspace())
    nonspace = [c for c in s if not c.isspace()]
    if not nonspace:
        return True
    non_alpha = sum(1 for c in nonspace if not c.isalnum())
    # Condition 1: mostly non-alphanumeric (borders, separators)
    if non_alpha / len(nonspace) > 0.7:
        return True
    # Condition 2: mostly whitespace (spaced-out table headers)
    if whitespace_count / total > 0.6:
        return True
    return False


def _is_file_path(s):
    """Check if a string looks like a file path."""
    s = s.strip()
    return bool(RE_FILE_PATH.match(s))


def _string_content(node, source_bytes):
    """Extract the actual string value (without quotes) from a string_literal
    or concatenated_string node, processing basic C escape sequences."""
    if node.type == "string_literal":
        raw = _text(node, source_bytes)
        # Handle raw string literals: R"(...)" or R"delim(...)delim"
        if raw.startswith('R"'):
            idx = raw.find('(')
            if idx >= 0:
                # Find matching )delim"
                return raw[idx+1:raw.rfind(')')]
            return raw
        # Handle prefixed strings: u8"...", L"...", u"...", U"..."
        if raw.startswith(('u8"', 'L"', 'u"', 'U"')):
            prefix_end = raw.index('"')
            raw = raw[prefix_end:]
        # Strip surrounding quotes
        if raw.startswith('"') and raw.endswith('"'):
            raw = raw[1:-1]
        return _unescape_cpp(raw)
    elif node.type == "concatenated_string":
        fragments = []
        for child in node.named_children:
            if child.type == "string_literal":
                fragments.append(_string_content(child, source_bytes))
        return "".join(fragments)
    return ""


def _unescape_cpp(s):
    """Decode basic C++ string-literal escape sequences.
    Matches the behavior of i18n_extract.py's cpp_unescape."""
    result = []
    i = 0
    while i < len(s):
        if s[i] == '\\' and i + 1 < len(s):
            c = s[i + 1]
            if c == 'n':
                result.append('\n')
            elif c == 't':
                result.append('\t')
            elif c == 'r':
                result.append('\r')
            elif c == '\\':
                result.append('\\')
            elif c == '"':
                result.append('"')
            elif c == "'":
                result.append("'")
            else:
                result.append(s[i:i+2])
            i += 2
        else:
            result.append(s[i])
            i += 1
    return ''.join(result)


# ── AST Helpers ───────────────────────────────────────────────────────────────

def _find_operator(node, source_bytes):
    """Find the operator anonymous child of an expression node.
    Returns the operator text (e.g. '+=', '<<', '+') or None."""
    for child in node.children:
        if not child.is_named:
            text = _text(child, source_bytes)
            if text in ('+=', '<<', '+', '='):
                return text
    return None


def _extract_receiver(node, source_bytes):
    """Extract the left-side receiver variable name from an expression.

    For += : walk the left child chain
    For << : walk the leftmost leaf of the binary_expression chain
    For .append() : get the object name from field_expression

    Returns a string like 'desc', 'text', 'buf', or '?' if unknown.
    """
    if node.type == "assignment_expression":
        left = None
        for child in node.named_children:
            if child.type in ("identifier", "field_expression",
                              "subscript_expression"):
                left = child
                break
        if left is None:
            return "?"
        return _extract_var_name(left, source_bytes)

    elif node.type == "binary_expression":
        # Walk the left chain to find the root receiver
        current = node
        while current.type == "binary_expression":
            left = None
            for child in current.named_children:
                if child.type in ("identifier", "field_expression",
                                  "subscript_expression", "binary_expression"):
                    left = child
                    break
            if left and left.type == "binary_expression":
                current = left
            elif left:
                return _extract_var_name(left, source_bytes)
            else:
                break
        return "?"

    elif node.type == "field_expression":
        obj = None
        for child in node.named_children:
            if child.type == "identifier":
                obj = child
                break
        if obj:
            return _text(obj, source_bytes)
        return "?"

    return "?"


def _extract_var_name(node, source_bytes):
    """Extract a readable variable name from various AST node types."""
    if node.type == "identifier":
        return _text(node, source_bytes)
    elif node.type == "field_expression":
        field = None
        for child in node.named_children:
            if child.type == "field_identifier":
                field = child
        if field:
            return _text(field, source_bytes)
        return _text(node, source_bytes)
    elif node.type == "subscript_expression":
        arr = None
        for child in node.named_children:
            if child.type == "identifier":
                arr = child
                break
        if arr:
            return _text(arr, source_bytes)
        return "?"
    elif node.type == "call_expression":
        func = None
        for child in node.named_children:
            if child.type in ("identifier", "field_expression",
                              "qualified_identifier"):
                func = child
                break
        if func:
            return _extract_var_name(func, source_bytes)
        return "?"
    return "?"


def _is_wrapped(literal_node, source_bytes):
    """Check if a string_literal node is an argument to a translation wrapper.

    Walks up: literal -> (argument_list) -> call_expression -> check callee.
    Also: literal -> concatenated_string -> (argument_list) -> call_expression.
    """
    parent = literal_node.parent
    if parent and parent.type == "concatenated_string":
        grandparent = parent.parent
        if grandparent and grandparent.type == "argument_list":
            great_grandparent = grandparent.parent
            if (great_grandparent and
                    great_grandparent.type == "call_expression"):
                callee = _extract_callee_name(great_grandparent, source_bytes)
                if callee in TRANSLATION_WRAPPERS:
                    return True

    # Direct: literal inside argument_list inside call_expression
    if parent and parent.type == "argument_list":
        grandparent = parent.parent
        if grandparent and grandparent.type == "call_expression":
            callee = _extract_callee_name(grandparent, source_bytes)
            if callee in TRANSLATION_WRAPPERS:
                return True

    return False


def _extract_callee_name(call_node, source_bytes):
    """Extract the callee function name from a call_expression node."""
    for child in call_node.named_children:
        if child.type == "identifier":
            return _text(child, source_bytes)
        elif child.type == "field_expression":
            return _extract_var_name(child, source_bytes)
        elif child.type == "qualified_identifier":
            return _extract_var_name(child, source_bytes)
    return ""


def _find_enclosing_function(node, source_bytes):
    """Walk up the AST to find the enclosing function definition name."""
    current = node
    while current:
        if current.type == "function_definition":
            declarator = None
            for child in current.named_children:
                if child.type == "function_declarator":
                    declarator = child
                    break
            if declarator:
                for child in declarator.named_children:
                    if child.type == "identifier":
                        return _text(child, source_bytes)
                    elif child.type == "field_identifier":
                        return _text(child, source_bytes)
                    elif child.type == "qualified_identifier":
                        return _text(child, source_bytes)
            return ""
        current = current.parent
    return ""


def _find_enclosing_line_text(node, source_bytes):
    """Get the full text of the enclosing source line."""
    row, _ = node.start_point
    lines = source_bytes.decode("utf-8", errors="replace").splitlines()
    if row < len(lines):
        return lines[row]
    return ""


def _collect_bare_literals(node, source_bytes, include_wrapped=False):
    """Recursively collect string_literal content from a subtree.
    Returns a list of (content, node, wrapped) tuples."""
    results = []

    def _recurse(n):
        if n.type == "string_literal":
            wrapped = _is_wrapped(n, source_bytes)
            if not wrapped or include_wrapped:
                content = _string_content(n, source_bytes)
                results.append((content, n, wrapped))
        elif n.type == "concatenated_string":
            wrapped = False
            parent = n.parent
            if parent and parent.type == "argument_list":
                gp = parent.parent
                if gp and gp.type == "call_expression":
                    callee = _extract_callee_name(gp, source_bytes)
                    if callee in TRANSLATION_WRAPPERS:
                        wrapped = True
            if not wrapped or include_wrapped:
                for child in n.named_children:
                    _recurse(child)
        else:
            for child in n.named_children:
                _recurse(child)

    _recurse(node)
    return results


# ── Detection Rules ────────────────────────────────────────────────────────────

def _check_compound_assign(node, source_bytes, filepath, findings,
                           include_wrapped, seen_literals):
    """R1: Detect `desc += "..."` patterns."""
    op = _find_operator(node, source_bytes)
    if op != "+=":
        return

    named_children = [c for c in node.named_children]
    if len(named_children) < 2:
        return
    rhs = named_children[-1]

    receiver = _extract_receiver(node, source_bytes)
    literals = _collect_bare_literals(rhs, source_bytes, include_wrapped)

    for content, lit_node, wrapped in literals:
        key = (lit_node.start_byte, lit_node.end_byte)
        if key in seen_literals:
            continue
        if not _has_alpha(content) and not _has_cjk(content):
            continue
        seen_literals.add(key)
        findings.append({
            "rule": "COMPOUND_ASSIGN",
            "node": lit_node,
            "receiver": receiver,
            "literal": content,
            "wrapped": wrapped,
        })


def _check_append_call(node, source_bytes, filepath, findings,
                       include_wrapped, seen_literals):
    """R2: Detect `buf.append("...")` patterns."""
    func_node = None
    args_node = None
    for child in node.named_children:
        if child.type == "field_expression":
            func_node = child
        elif child.type == "argument_list":
            args_node = child

    if func_node is None:
        return

    method_name = None
    for child in func_node.named_children:
        if child.type == "field_identifier":
            method_name = _text(child, source_bytes)
            break

    if method_name not in TEXT_METHODS:
        return

    receiver = _extract_receiver(func_node, source_bytes)

    if args_node is None:
        return

    for arg in args_node.named_children:
        if arg.type == "string_literal":
            key = (arg.start_byte, arg.end_byte)
            if key in seen_literals:
                continue
            wrapped = _is_wrapped(arg, source_bytes)
            if wrapped and not include_wrapped:
                continue
            content = _string_content(arg, source_bytes)
            if not _has_alpha(content) and not _has_cjk(content):
                continue
            seen_literals.add(key)
            findings.append({
                "rule": "APPEND_CALL",
                "node": arg,
                "receiver": receiver,
                "literal": content,
                "wrapped": wrapped,
            })


def _check_stream_insert(node, source_bytes, filepath, findings,
                         include_wrapped, seen_literals):
    """R3: Detect `text << "..."` patterns."""
    op = _find_operator(node, source_bytes)
    if op != "<<":
        return

    named_children = [c for c in node.named_children]
    if len(named_children) < 2:
        return
    rhs = named_children[-1]

    literals = _collect_bare_literals(rhs, source_bytes, include_wrapped)
    if not literals:
        return

    receiver = _extract_receiver(node, source_bytes)

    for content, lit_node, wrapped in literals:
        key = (lit_node.start_byte, lit_node.end_byte)
        if key in seen_literals:
            continue
        if not _has_alpha(content) and not _has_cjk(content):
            continue
        seen_literals.add(key)
        findings.append({
            "rule": "STREAM_INSERT",
            "node": lit_node,
            "receiver": receiver,
            "literal": content,
            "wrapped": wrapped,
        })


def _check_runtime_concat(node, source_bytes, filepath, findings,
                          include_wrapped, seen_literals):
    """R4: Detect `"..." + var` or `var + "..."` patterns."""
    op = _find_operator(node, source_bytes)
    if op != "+":
        return

    named_children = [c for c in node.named_children]
    if len(named_children) < 2:
        return
    left = named_children[0]

    literals = _collect_bare_literals(node, source_bytes, include_wrapped)
    if not literals:
        return

    parent = node.parent
    receiver = "?"
    if parent:
        if parent.type == "return_statement":
            receiver = "(return)"
        elif parent.type == "assignment_expression":
            receiver = _extract_receiver(parent, source_bytes)
        elif parent.type == "call_expression":
            receiver = "(arg)"
        else:
            if left.type == "identifier":
                receiver = _text(left, source_bytes)

    for content, lit_node, wrapped in literals:
        key = (lit_node.start_byte, lit_node.end_byte)
        if key in seen_literals:
            continue
        if not _has_alpha(content) and not _has_cjk(content):
            continue
        seen_literals.add(key)
        findings.append({
            "rule": "RUNTIME_CONCAT",
            "node": lit_node,
            "receiver": receiver,
            "literal": content,
            "wrapped": wrapped,
        })


def _check_compile_time_concat(node, source_bytes, filepath, findings,
                               include_wrapped):
    """R5: Detect `"a" "b"` compile-time adjacent string concatenation."""
    literal_children = [c for c in node.named_children
                        if c.type == "string_literal"]
    if len(literal_children) < 2:
        return

    wrapped = False
    parent = node.parent
    if parent and parent.type == "argument_list":
        gp = parent.parent
        if gp and gp.type == "call_expression":
            callee = _extract_callee_name(gp, source_bytes)
            if callee in TRANSLATION_WRAPPERS:
                wrapped = True

    if wrapped and not include_wrapped:
        return

    combined = _string_content(node, source_bytes)
    if not _has_alpha(combined) and not _has_cjk(combined):
        return

    receiver = _infer_concat_context(node, source_bytes)

    findings.append({
        "rule": "COMPILE_TIME",
        "node": node,
        "receiver": receiver,
        "literal": combined,
        "wrapped": wrapped,
    })


def _infer_concat_context(node, source_bytes):
    """Walk up from a concatenated_string or + expression to find context."""
    current = node
    while current:
        if current.type == "assignment_expression":
            return _extract_receiver(current, source_bytes)
        elif current.type == "return_statement":
            return "(return)"
        elif current.type == "call_expression":
            return "(arg)"
        elif current.type == "init_declarator":
            for child in current.named_children:
                if child.type == "identifier":
                    return _text(child, source_bytes)
            return "(init)"
        current = current.parent
    return "?"


# ── Exclusion Filters ─────────────────────────────────────────────────────────

def _hard_exclude(finding, filepath, source_bytes):
    """Return True if the finding should be hard-excluded (dropped entirely)."""
    content = finding["literal"]

    # E2: No alpha AND no CJK
    if not _has_alpha(content) and not _has_cjk(content):
        return True

    # E3: ASCII art
    if _is_ascii_art(content):
        return True

    # E4: File path
    if _is_file_path(content):
        return True

    # E5: Entirely markup/color tag
    if _is_markup_tag(content.strip()):
        return True

    # E6: Preprocessor directive
    node = finding["node"]
    line_text = _find_enclosing_line_text(node, source_bytes)
    if line_text.strip().startswith("#"):
        return True

    return False


# ── Risk Scoring ──────────────────────────────────────────────────────────────

def _display_stream_sinks(source_bytes):
    """Map local stream builders passed directly to display sinks."""
    source = source_bytes.decode("utf-8", errors="replace")
    sinks = {}
    pattern = re.compile(
        r"\b(?P<sink>mpr|mprf|mprf_p|cprintf|formatted_message_history)\s*"
        r"\(\s*(?P<receiver>[A-Za-z_]\w*)\s*\.\s*str\s*\(")
    for match in pattern.finditer(source):
        sinks[match.group("receiver")] = match.group("sink")
    return sinks


def _score_finding(finding, filepath, source_bytes, display_sinks=None):
    """Compute a numeric risk score for a finding."""
    score = 0
    reasons = []

    content = finding["literal"]
    receiver = finding["receiver"]
    node = finding["node"]
    display_sinks = display_sinks or {}

    if receiver in display_sinks:
        score += 6
        finding["sink"] = display_sinks[receiver]
        reasons.append(f"display-sink={display_sinks[receiver]} (+6)")

    # Detect layout strings: very low alphabetic ratio in non-whitespace chars
    nonspace = [c for c in content if not c.isspace()]
    alpha_ratio = 0.0
    if nonspace:
        alpha_count = sum(1 for c in nonspace if c.isalpha())
        alpha_ratio = alpha_count / len(nonspace)
    is_layout = alpha_ratio < 0.35 and len(nonspace) > 0

    # ── Positive signals ──────────────────────────────────────────────────

    # For layout strings, skip variable/file/function context bonuses
    # (they're format templates, not prose, regardless of container var name)
    if not is_layout:
        if receiver and receiver.lower() in UI_VAR_NAMES:
            score += 3
            reasons.append(f"receiver={receiver} (+3)")

    words = content.split()
    if len(words) >= 4:
        score += 2
        reasons.append("prose (+2)")

    if RE_SENTENCE_END.search(content):
        score += 1
        reasons.append("sentence-end (+1)")

    func_name = ""
    if not is_layout:
        func_name = _find_enclosing_function(node, source_bytes)
        if func_name:
            func_lower = func_name.lower()
            for kw in UI_FUNC_KEYWORDS:
                if kw in func_lower:
                    score += 2
                    reasons.append(f"func={func_name} (+2)")
                    break

        file_lower = os.path.basename(filepath).lower()
        for kw in UI_FILE_KEYWORDS:
            if kw in file_lower:
                score += 2
                reasons.append(f"file={os.path.basename(filepath)} (+2)")
                break
    else:
        func_name = _find_enclosing_function(node, source_bytes)

    if _has_cjk(content):
        score += 3
        reasons.append("has-cjk (+3)")

    # ── Negative signals ───────────────────────────────────────────────────

    line_text = _find_enclosing_line_text(node, source_bytes)
    if any(ch in line_text for ch in
           ("MSGCH_DIAGNOSTICS", "MSGCH_DEBUG", "MSGCH_ERROR")):
        score -= 3
        reasons.append("diagnostic-channel (-3)")

    if func_name:
        func_upper = func_name.upper()
        if any(ch in func_upper for ch in
               ("DIAGNOSTICS", "DEBUG", "ERROR_LOG")):
            score -= 3
            reasons.append("diagnostic-func (-3)")

    if _is_markup_tag(content.strip()):
        score -= 2
        reasons.append("markup-tag (-2)")

    if is_layout:
        score -= 1
        reasons.append(f"layout-string ({alpha_ratio:.0%} alpha) (-1)")

    if _is_format_only(content):
        score -= 1
        reasons.append("format-only (-1)")

    if _is_file_path(content):
        score -= 2
        reasons.append("file-path (-2)")

    return score, reasons


def _score_to_risk(score):
    """Map numeric score to risk level."""
    if score >= 4:
        return "HIGH"
    elif score >= 2:
        return "MED"
    else:
        return "LOW"


# ── AST Walker ────────────────────────────────────────────────────────────────

def _walk_node(node, source_bytes, filepath, findings, include_wrapped,
               seen_literals=None):
    """Recursively walk the AST and dispatch to rule detectors.

    seen_literals tracks (start_byte, end_byte) of already-reported string
    literals to prevent double-counting when outer expressions (e.g.,
    compound_assign) collect literals that inner expressions (e.g.,
    runtime_concat on the same RHS) would also report.
    """
    if seen_literals is None:
        seen_literals = set()

    if node.type in ("preproc_if", "preproc_ifdef", "preproc_else",
                     "preproc_elif", "preproc_include", "preproc_def",
                     "preproc_function_def"):
        return

    if node.type == "assignment_expression":
        _check_compound_assign(node, source_bytes, filepath, findings,
                               include_wrapped, seen_literals)
    elif node.type == "binary_expression":
        _check_stream_insert(node, source_bytes, filepath, findings,
                             include_wrapped, seen_literals)
        _check_runtime_concat(node, source_bytes, filepath, findings,
                              include_wrapped, seen_literals)
    elif node.type == "call_expression":
        _check_append_call(node, source_bytes, filepath, findings,
                           include_wrapped, seen_literals)
    elif node.type == "concatenated_string":
        _check_compile_time_concat(node, source_bytes, filepath, findings,
                                   include_wrapped)

    for child in node.children:
        _walk_node(child, source_bytes, filepath, findings, include_wrapped,
                   seen_literals)


# ── File Scanner ──────────────────────────────────────────────────────────────

def scan_file(filepath, parser, include_wrapped=False):
    """Parse a C++ source file and return a list of raw findings."""
    with open(filepath, "rb") as f:
        source_bytes = f.read()

    tree = parser.parse(source_bytes)
    findings = []
    _walk_node(tree.root_node, source_bytes, filepath, findings,
               include_wrapped)
    return findings, source_bytes


# ── Output Formatters ─────────────────────────────────────────────────────────

def format_text(findings, source_dir):
    """Format findings as human-readable text, matching scan_i18n.py style."""
    risk_order = {"HIGH": 0, "MED": 1, "LOW": 2}
    rule_labels = {
        "COMPOUND_ASSIGN": "COMPOUND_ASSIGN (+=)",
        "APPEND_CALL": "APPEND_CALL (.append)",
        "STREAM_INSERT": "STREAM_INSERT (<<)",
        "RUNTIME_CONCAT": "RUNTIME_CONCAT (+)",
        "COMPILE_TIME": "COMPILE_TIME (adjacent)",
    }
    rule_short = {
        "COMPOUND_ASSIGN": "+=",
        "APPEND_CALL": ".append",
        "STREAM_INSERT": "<<",
        "RUNTIME_CONCAT": "+",
        "COMPILE_TIME": "adjacent",
    }

    output = []
    rule_order = ("COMPOUND_ASSIGN", "APPEND_CALL", "STREAM_INSERT",
                  "RUNTIME_CONCAT", "COMPILE_TIME")

    for rule_name in rule_order:
        rule_findings = [f for f in findings if f["rule"] == rule_name]
        if not rule_findings:
            continue

        output.append(f"=== String concatenation: {rule_labels[rule_name]} ===")
        output.append("")

        rule_findings.sort(key=lambda f: (
            risk_order.get(f["risk"], 3),
            f["file"],
            f["line"],
        ))

        for f in rule_findings:
            rel_path = os.path.relpath(f["file"], source_dir) if source_dir else f["file"]
            lit = f["literal"].replace("\n", "\\n")[:80]
            wrapped_flag = " [W]" if f.get("wrapped") else ""
            output.append(f"  [{f['risk']:4s}] {rel_path}:{f['line']}"
                          f"  {f['receiver']} {rule_short[rule_name]} "
                          f"\"{lit}\"{wrapped_flag}")

        output.append("")

    # Summary
    output.append("Summary:")
    rule_counts = defaultdict(lambda: defaultdict(int))
    files_seen = set()

    for f in findings:
        rule_counts[f["rule"]][f["risk"]] += 1
        files_seen.add(f["file"])

    total = len(findings)
    for rule_name in rule_order:
        counts = rule_counts[rule_name]
        if counts:
            parts = [f"{risk}={counts.get(risk, 0)}"
                     for risk in ("HIGH", "MED", "LOW")]
            output.append(f"  {rule_name}: {sum(counts.values())} findings"
                          f" ({', '.join(parts)})")

    output.append(f"  TOTAL: {total} findings across {len(files_seen)} files")
    return "\n".join(output)


def format_json(findings, source_dir, coverage):
    """Format findings as structured JSON."""
    summary = defaultdict(lambda: defaultdict(int))
    per_file = defaultdict(lambda: defaultdict(int))

    finding_dicts = []
    for f in findings:
        rel_path = os.path.relpath(f["file"], source_dir) if source_dir else f["file"]
        finding_dicts.append({
            "file": rel_path,
            "line": f["line"],
            "column": f["col"],
            "rule": f["rule"],
            "risk": f["risk"],
            "score": f["score"],
            "literal": f["literal"],
            "receiver": f["receiver"],
            "wrapped": f.get("wrapped", False),
            "reason": f["reason"],
            "sink": f.get("sink"),
        })
        summary[f["rule"]][f["risk"]] += 1
        per_file[rel_path][f["risk"]] += 1
        per_file[rel_path]["total"] += 1

    has_wrapped = any(f.get("wrapped") for f in findings)

    return json.dumps({
        "meta": {
            "scanner": "scan_string_concat.py",
            "version": "1.0.0",
            "mode": "all" if has_wrapped else "bare-only",
            "source": source_dir or "(files)",
            "coverage": coverage.as_dict(),
        },
        "findings": finding_dicts,
        "summary": {
            rule: {
                "total": sum(vals.values()),
                "HIGH": vals.get("HIGH", 0),
                "MED": vals.get("MED", 0),
                "LOW": vals.get("LOW", 0),
            }
            for rule, vals in summary.items()
        },
        "per_file": dict(per_file),
    }, indent=2, ensure_ascii=False)


def _display_root(files_to_scan, source_dir):
    """Choose a path root stable between recursive and explicit-file scans."""
    if source_dir:
        return os.path.abspath(source_dir)

    source_roots = []
    for filename in files_to_scan:
        current = os.path.dirname(os.path.abspath(filename))
        while True:
            if (os.path.basename(current) == "source"
                    and os.path.basename(os.path.dirname(current)) == "crawl-ref"):
                source_roots.append(current)
                break
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
    if len(source_roots) == len(files_to_scan) and len(set(source_roots)) == 1:
        return source_roots[0]
    return os.path.commonpath([os.path.dirname(path) for path in files_to_scan])


# ── Main Entry Point ──────────────────────────────────────────────────────────

def main():
    argparser = argparse.ArgumentParser(
        description="Tree-sitter-based C++ string concatenation scanner "
                    "for i18n blind spots."
    )

    source_group = argparser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "source_dir", nargs="?", default=None,
        help="Root of C++ source tree for recursive scan")
    source_group.add_argument(
        "--files", type=str, default=None,
        help="Comma-separated list of specific files to scan")

    argparser.add_argument("--format", choices=("text", "json"), default="text",
                           help="Output format (default: text)")
    argparser.add_argument("--json-output", type=str, default=None,
                           help="Write JSON output to file")
    argparser.add_argument("--verbose", "-v", action="store_true",
                           help="Include extra context in output")

    argparser.add_argument("--min-risk", choices=("LOW", "MED", "HIGH"),
                           default="LOW",
                           help="Minimum risk level to report (default: LOW)")
    argparser.add_argument("--skip-low", action="store_true",
                           help="Exclude LOW-risk findings entirely")

    argparser.add_argument("--all", action="store_true",
                           help="Include T_()-wrapped literals (default: bare only)")
    argparser.add_argument("--require-parser", action="store_true",
                           help="Exit 2 if tree-sitter is unavailable")

    args = argparser.parse_args()

    # ── Check tree-sitter availability ────────────────────────────────────
    if not TREE_SITTER_AVAILABLE:
        msg = ("ERROR: tree-sitter is required but not installed. "
               "Install with: pip3 install tree-sitter tree-sitter-cpp")
        if args.require_parser:
            print(msg, file=sys.stderr)
            return 2
        else:
            print(f"Warning: {msg}", file=sys.stderr)
            print("Skipping string concatenation scan.", file=sys.stderr)
            return 0

    # ── Collect files to scan ─────────────────────────────────────────────
    files_to_scan = []
    coverage = ScanCoverage()

    if args.files:
        for f in args.files.split(","):
            f = f.strip()
            if not f:
                continue
            if (not os.path.isfile(f)
                    or os.path.splitext(f)[1].lower() not in CPP_SOURCE_EXTENSIONS):
                print(f"ERROR: File not found or not C++: {f}", file=sys.stderr)
                return 2
            files_to_scan.append(os.path.abspath(f))
    elif args.source_dir:
        source_dir = os.path.abspath(args.source_dir)
        try:
            files_to_scan = [path for path in discover_source_files(
                source_dir, skip_dirs=SKIP_DIRS)
                if os.path.basename(path) not in SKIP_FILES]
        except (OSError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    if not files_to_scan:
        print("No C++ source files found to scan.", file=sys.stderr)
        return 2
    coverage.discovered = len(files_to_scan)

    # ── Initialize parser ─────────────────────────────────────────────────
    lang = _Language(_tscpp.language())
    ts_parser = _Parser(lang)

    # ── Scan files ────────────────────────────────────────────────────────
    include_wrapped = args.all
    all_findings = []
    for filepath in files_to_scan:
        try:
            raw_findings, source_bytes = scan_file(filepath, ts_parser,
                                                   include_wrapped)
            coverage.scanned += 1
        except (OSError, ValueError) as exc:
            coverage.failed.append(f"{filepath}: {exc}")
            continue

        display_sinks = _display_stream_sinks(source_bytes)
        for finding in raw_findings:
            if _hard_exclude(finding, filepath, source_bytes):
                continue

            score, reasons = _score_finding(
                finding, filepath, source_bytes, display_sinks)
            risk = _score_to_risk(score)

            risk_order = {"LOW": 0, "MED": 1, "HIGH": 2}
            if risk_order[risk] < risk_order[args.min_risk]:
                continue

            if args.skip_low and risk == "LOW":
                continue

            node = finding["node"]
            finding["file"] = filepath
            finding["line"] = node.start_point[0] + 1
            finding["col"] = node.start_point[1] + 1
            finding["score"] = score
            finding["risk"] = risk
            finding["reason"] = reasons

            all_findings.append(finding)

    # ── Output ────────────────────────────────────────────────────────────
    out_dir = _display_root(files_to_scan, args.source_dir)

    if args.format == "json":
        output = format_json(all_findings, out_dir, coverage)
        if args.json_output:
            with open(args.json_output, "w", encoding="utf-8") as f:
                f.write(output)
            print(f"Report written to {args.json_output}")
        else:
            print(output)
    else:
        output = format_text(all_findings, out_dir)
        print(output)

    # ── Exit code ─────────────────────────────────────────────────────────
    if coverage.failed:
        for failure in coverage.failed:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 2

    high_count = sum(1 for f in all_findings if f["risk"] == "HIGH")
    med_count = sum(1 for f in all_findings if f["risk"] == "MED")
    low_count = sum(1 for f in all_findings if f["risk"] == "LOW")

    min_risk_order = {"LOW": 0, "MED": 1, "HIGH": 2}
    has_findings = (
        (min_risk_order["HIGH"] >= min_risk_order[args.min_risk] and high_count > 0) or
        (min_risk_order["MED"] >= min_risk_order[args.min_risk] and med_count > 0) or
        (min_risk_order["LOW"] >= min_risk_order[args.min_risk] and low_count > 0)
    )

    return 1 if has_findings else 0


if __name__ == "__main__":
    sys.exit(main())
