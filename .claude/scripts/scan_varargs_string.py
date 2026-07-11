#!/usr/bin/env python3
"""
scan_varargs_string.py — Tree-sitter-based scanner for std::string passed to
printf-style variadic functions (Issue #42 class UB).

Passing a std::string object (not const char*) as a `%s` variadic argument to
make_stringf / mprf / etc. is undefined behavior: va_arg(ap, const char*) reads
the first 8 bytes of the std::string object (its SSO buffer / data pointer) and
interprets them as a char* — producing garbage / control characters at runtime.
The compiler's -Wformat does NOT reliably catch this through the PRINTF()
format attribute when the argument is a non-trivial class temporary, so this
static check exists as the gate.

Detected rules (variadic argument position only, i.e. AFTER the format string):

  R1 STRING_CTOR   HIGH — arg is/contains a `string(...)`/`std::string(...)`
                          construction not followed by `.c_str()`
  R2 CONCAT        HIGH — arg is a `+` expression (runtime string concatenation
                          yields a std::string temporary)
  R3 TERNARY       HIGH — arg is a ternary whose branch is a string ctor / concat
  R4 CALL_NO_CSTR  WARN — arg is a bare function call not ending in `.c_str()`
                          and not a known const char*-returning function
                          (verify the callee returns const char*, not std::string)

Usage:
    scan_varargs_string.py crawl-ref/source/
    scan_varargs_string.py --files prompt.cc,describe.cc
    scan_varargs_string.py crawl-ref/source/ --format json
    scan_varargs_string.py crawl-ref/source/ --require-parser   # exit 2 if no TS

Exit codes:
    0 — no HIGH findings (warnings allowed)
    1 — one or more HIGH findings (blocking)
    2 — tree-sitter unavailable and --require-parser given

Dependencies: tree-sitter, tree-sitter-cpp
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict

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


# printf-style variadic functions: name -> number of leading fixed args BEFORE
# the format string. The format string is at index == value; variadic %s args
# follow it. Overloads with different leading-arg counts are resolved at runtime
# by locating the first string-literal / T_() argument as the format string.
VARARG_FUNCS = {
    "make_stringf", "make_stringf_p", "vmake_stringf_p",
    "mprf", "mprf_p", "mprf_nojoin", "mprf_nocap",
    "cprintf", "nowrap_eol_cprintf",
    "die", "die_noline", "debuglog", "fail", "sysfail", "corrupted",
    "snprintf", "vsnprintf",
}

# String-wrapping macros/functions whose result is const char* (safe as %s).
CONST_CHAR_WRAPPERS = {"T_", "N_", "C_", "gettext", "_"}

# Known functions that return const char* — safe to pass directly as %s.
# (std::string returners are intentionally NOT listed; they need .c_str().)
CONST_CHAR_FUNCS = {
    "skill_name", "spell_title", "god_name", "dungeon_feature_name",
    "brand_type_name", "card_name", "rune_type_name", "mutation_name",
    "potion_type_name", "spell_english_name", "armour_ego_name",
    "artp_name", "duration_name", "equip_slot_name", "spelltype_long_name",
    "get_job_name", "mons_class_name", "held_status", "get_desc_quantity",
    "conj_verb", "pronoun", "uppercase_first",
}


def _text(node, src):
    return src[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _callee_name(call_node, src):
    """Return the simple callee identifier of a call_expression, or ''."""
    for child in call_node.named_children:
        if child.type == "identifier":
            return _text(child, src)
        if child.type == "qualified_identifier":
            last = None
            for c in child.named_children:
                if c.type == "identifier":
                    last = c
            return _text(last, src) if last else _text(child, src)
        if child.type == "field_expression":
            for c in child.named_children:
                if c.type == "field_identifier":
                    return _text(c, src)
        break
    return ""


def _is_const_char_wrapper_call(node, src):
    """True if node is a call to T_()/N_()/C_() (returns const char*)."""
    if node.type != "call_expression":
        return False
    return _callee_name(node, src) in CONST_CHAR_WRAPPERS


def _ends_with_cstr(node, src):
    """True if the expression node is a `....c_str()` call."""
    if node.type != "call_expression":
        return False
    for child in node.named_children:
        if child.type == "field_expression":
            for c in child.named_children:
                if c.type == "field_identifier" and _text(c, src) == "c_str":
                    return True
        break
    return False


def _is_string_ctor(node, src):
    """True if node is a `string(...)` / `std::string(...)` construction."""
    if node.type != "call_expression":
        return False
    name = _callee_name(node, src)
    return name in ("string", "basic_string") or _text(node, src).startswith(
        ("string(", "std::string(", "std::basic_string"))


def _contains_string_temp(node, src, depth=0):
    """Heuristic: does this expression evaluate to a std::string temporary?
    Detects string ctor and `+` concatenation, recursing through parens."""
    if depth > 8:
        return False
    if node.type == "parenthesized_expression":
        for c in node.named_children:
            if _contains_string_temp(c, src, depth + 1):
                return True
        return False
    if _is_string_ctor(node, src):
        return True
    if node.type == "binary_expression":
        for child in node.children:
            if not child.is_named and _text(child, src) == "+":
                return _binary_has_string_operand(node, src)
    return False


def _format_arg_index(args, src):
    """Locate the format-string argument among the call's argument nodes.
    Returns index of the first arg that is a string_literal, concatenated_string,
    or a const-char* wrapper call (T_(...)). Returns -1 if none found."""
    for i, arg in enumerate(args):
        if arg.type in ("string_literal", "concatenated_string"):
            return i
        if arg.type == "call_expression" and _is_const_char_wrapper_call(arg, src):
            return i
    return -1


def _binary_has_string_operand(node, src, depth=0):
    """True if a `+` binary_expression has at least one string-typed operand
    (string literal, concatenated string, or string(...) ctor), i.e. it is
    genuine string concatenation rather than integer/char arithmetic."""
    if depth > 8 or node.type != "binary_expression":
        return False
    for child in node.named_children:
        if child.type in ("string_literal", "concatenated_string"):
            return True
        if _is_string_ctor(child, src):
            return True
        if _ends_with_cstr(child, src):
            # `a.c_str() + n` is pointer arithmetic, not std::string — skip,
            # but `str + other.c_str()` still needs the str side; handled by
            # the string-literal / ctor checks above.
            continue
        if child.type == "parenthesized_expression":
            for c in child.named_children:
                if _binary_has_string_operand(c, src, depth + 1) or \
                   c.type in ("string_literal", "concatenated_string") or \
                   _is_string_ctor(c, src):
                    return True
        if child.type == "binary_expression" and \
                _binary_has_string_operand(child, src, depth + 1):
            return True
    return False


def _classify_vararg(arg, src):
    """Classify a variadic argument node. Returns (rule, risk) or (None, None)."""
    if _ends_with_cstr(arg, src):
        return None, None
    if arg.type == "call_expression" and _is_const_char_wrapper_call(arg, src):
        return None, None

    if _is_string_ctor(arg, src):
        return "STRING_CTOR", "HIGH"

    if arg.type == "binary_expression":
        for child in arg.children:
            if not child.is_named and _text(child, src) == "+":
                if _binary_has_string_operand(arg, src):
                    return "CONCAT", "HIGH"
                return None, None

    if arg.type == "conditional_expression":
        for c in arg.named_children:
            if _contains_string_temp(c, src):
                return "TERNARY", "HIGH"
        return None, None

    if arg.type == "parenthesized_expression":
        for c in arg.named_children:
            return _classify_vararg(c, src)

    if arg.type == "call_expression":
        name = _callee_name(arg, src)
        if name and name not in CONST_CHAR_FUNCS and name not in CONST_CHAR_WRAPPERS:
            return "CALL_NO_CSTR", "WARN"
        return None, None

    return None, None


def _find_line(node, src):
    return node.start_point[0] + 1


def _scan_call(call_node, src, findings):
    callee = _callee_name(call_node, src)
    if callee not in VARARG_FUNCS:
        return
    args_node = None
    for child in call_node.named_children:
        if child.type == "argument_list":
            args_node = child
            break
    if args_node is None:
        return
    args = [c for c in args_node.named_children]
    fmt_idx = _format_arg_index(args, src)
    if fmt_idx < 0:
        return
    fmt_text = _text(args[fmt_idx], src)
    if "%s" not in fmt_text:
        return
    for arg in args[fmt_idx + 1:]:
        rule, risk = _classify_vararg(arg, src)
        if rule:
            findings.append({
                "callee": callee,
                "rule": rule,
                "risk": risk,
                "line": _find_line(arg, src),
                "arg": _text(arg, src)[:80],
                "node": arg,
            })


def _walk(node, src, findings):
    if node.type == "call_expression":
        _scan_call(node, src, findings)
    for child in node.children:
        _walk(child, src, findings)


def scan_file(filepath, parser):
    try:
        with open(filepath, "rb") as f:
            src = f.read()
    except OSError as e:
        print(f"Warning: cannot read {filepath}: {e}", file=sys.stderr)
        return []
    tree = parser.parse(src)
    findings = []
    _walk(tree.root_node, src, findings)
    for f in findings:
        f["file"] = filepath
        del f["node"]
    return findings


SKIP_DIRS = {"contrib", ".git", "worktrees", ".worktrees", "__pycache__",
             "catch2-tests", "rltiles", "util"}
SKIP_FILES = {"catch_amalgamated.cc"}


def main():
    ap = argparse.ArgumentParser(
        description="Scan for std::string passed to printf-style variadic "
                    "functions (Issue #42 class UB).")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("source_dir", nargs="?", default=None)
    grp.add_argument("--files", type=str, default=None,
                     help="Comma-separated list of files to scan")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    ap.add_argument("--require-parser", action="store_true",
                    help="Exit 2 if tree-sitter is unavailable")
    ap.add_argument("--include-warn", action="store_true",
                    help="Report WARN (CALL_NO_CSTR) findings too")
    args = ap.parse_args()

    if not TREE_SITTER_AVAILABLE:
        msg = ("tree-sitter required but not installed. "
               "Install: pip3 install tree-sitter tree-sitter-cpp")
        if args.require_parser:
            print(f"ERROR: {msg}", file=sys.stderr)
            return 2
        print(f"Warning: {msg}\nSkipping varargs-string scan.", file=sys.stderr)
        return 0

    files = []
    if args.files:
        for f in args.files.split(","):
            f = f.strip()
            if f and os.path.isfile(f) and os.path.splitext(f)[1] in (".cc", ".h", ".cpp", ".hpp"):
                files.append(os.path.abspath(f))
    else:
        root = os.path.abspath(args.source_dir)
        for dp, dn, fn in os.walk(root):
            dn[:] = [d for d in dn if d not in SKIP_DIRS]
            for name in sorted(fn):
                if name in SKIP_FILES:
                    continue
                if os.path.splitext(name)[1] in (".cc", ".h"):
                    files.append(os.path.join(dp, name))

    if not files:
        print("No C++ source files found to scan.", file=sys.stderr)
        return 0

    lang = _Language(_tscpp.language())
    parser = _Parser(lang)

    all_findings = []
    for fp in files:
        all_findings.extend(scan_file(fp, parser))

    if not args.include_warn:
        all_findings = [f for f in all_findings if f["risk"] != "WARN"]

    root_dir = os.path.abspath(args.source_dir) if args.source_dir else os.getcwd()

    if args.format == "json":
        for f in all_findings:
            f["file"] = os.path.relpath(f["file"], root_dir)
        print(json.dumps({
            "scanner": "scan_varargs_string.py",
            "findings": all_findings,
            "summary": {
                "HIGH": sum(1 for f in all_findings if f["risk"] == "HIGH"),
                "WARN": sum(1 for f in all_findings if f["risk"] == "WARN"),
            },
        }, indent=2, ensure_ascii=False))
    else:
        high = [f for f in all_findings if f["risk"] == "HIGH"]
        warn = [f for f in all_findings if f["risk"] == "WARN"]
        if all_findings:
            print("=== std::string in printf-style variadic args (Issue #42 UB) ===\n")
            for f in sorted(all_findings, key=lambda x: (x["risk"] != "HIGH", x["file"], x["line"])):
                rel = os.path.relpath(f["file"], root_dir)
                print(f"  [{f['risk']:4s}] {rel}:{f['line']}  "
                      f"{f['callee']}(...) {f['rule']}: {f['arg']}")
            print(f"\nSummary: {len(high)} HIGH (blocking), {len(warn)} WARN")
        else:
            print("OK: No std::string passed to variadic functions.")

    high_count = sum(1 for f in all_findings if f["risk"] == "HIGH")
    return 1 if high_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
