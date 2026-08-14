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
  R5 STRING_RETURN_CALL HIGH — arg is a bare call to a function known to
                                return std::string

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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n_shared import (CPP_AST_SCAN_SKIP_DIRS, CPP_SOURCE_EXTENSIONS, ScanCoverage,
                         discover_source_files, has_relevant_parse_error,
                         _normalize_eol)

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

FORMAT_SLOTS = {
    "snprintf": (2,), "vsnprintf": (2,),
    "mprf": (0, 1, 2), "mprf_p": (0, 1, 2),
    "mprf_nojoin": (0, 1), "mprf_nocap": (0, 1, 2),
    "die": (2,),
}

# String-wrapping macros/functions whose result is const char* (safe as %s).
CONST_CHAR_WRAPPERS = {"T_", "N_", "C_", "gettext", "_"}

# Known functions that return const char* — safe to pass directly as %s.
# (std::string returners are intentionally NOT listed; they need .c_str().)
CONST_CHAR_FUNCS = {
    "skill_name", "spell_title", "dungeon_feature_name",
    "brand_type_name", "card_name", "rune_type_name", "mutation_name",
    "potion_type_name", "spell_english_name", "armour_ego_name",
    "artp_name", "duration_name", "equip_slot_name", "spelltype_long_name",
    "get_job_name", "mons_class_name", "held_status",
}

# Known std::string returners. A bare call in a %s slot is always UB and should
# block even though generic, unresolved calls remain advisory warnings.
STRING_RETURN_FUNCS = {"god_name", "conj_verb", "uppercase_first"}

# Methods whose return type depends on the receiver class.  These must never be
# folded into the simple-name sets above: DCSS has same-name methods with
# incompatible return types (for example monster_info::pronoun() returns
# const char*, while actor::pronoun() returns string).
CONST_CHAR_METHODS = {
    "suffix": {"attacked_monster_list"},
    "get_verb": {"EquipOnDelay", "EquipOffDelay"},
    "pronoun": {"monster_info"},
    "what": {
        "map_load_exception", "dgn_veto_exception", "corrupted_save",
        "bad_map_flag", "bad_level_id",
    },
    "damage_verb": {"scorefile_entry"},
    "kill_category_desc": {"mon_enchant"},
}

STRING_RETURN_METHODS = {
    "suffix": {"LookupType"},
    "get_verb": {
        "AuxAttackType", "AuxConstrict", "AuxKick", "AuxHeadbutt",
        "AuxPeck", "AuxTail", "AuxPunch", "AuxBite", "AuxPseudopods",
        "AuxTentacles", "AuxTouch", "AuxMaw", "AuxBlades",
        "AuxFisticloak", "AuxMedusaStinger", "AuxTalismanBlade",
    },
    "pronoun": {"actor", "monster", "player"},
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


def _declarator_identifiers(node, src):
    """Return identifiers declared by a variable/parameter declarator."""
    if node is None:
        return []
    if node.type == "identifier":
        return [_text(node, src)]
    if node.type == "function_declarator":
        return []
    # Do not mistake a function name or identifiers in an initializer for a
    # variable binding.  Wrapper declarators expose the actual declarator via
    # this field (pointer/reference/init/array declarations included).
    child = node.child_by_field_name("declarator")
    if child is not None:
        return _declarator_identifiers(child, src)
    identifiers = []
    for child in node.named_children:
        identifiers.extend(_declarator_identifiers(child, src))
    return identifiers


def _normalise_declared_type(type_text):
    """Reduce a declaration type to the class name useful for method lookup."""
    names = re.findall(r"[A-Za-z_]\w*", type_text)
    names = [n for n in names if n not in {
        "const", "volatile", "struct", "class", "typename",
    }]
    return names[-1] if names else ""


def _binding_scope(node):
    """Find the lexical scope in which a declaration can name a receiver."""
    parent = node.parent
    while parent is not None:
        if parent.type in {
            "compound_statement", "function_definition", "catch_clause",
            "lambda_expression", "class_specifier", "struct_specifier",
            "translation_unit",
        }:
            return parent
        parent = parent.parent
    return None


def _build_type_bindings(root, src):
    """Index explicitly declared variable/parameter types in one source file."""
    bindings = defaultdict(list)

    def visit(node, depth=0):
        if node.type in ("declaration", "parameter_declaration"):
            type_node = node.child_by_field_name("type")
            declared_type = (_normalise_declared_type(_text(type_node, src))
                             if type_node is not None else "")
            if declared_type:
                declarators = []
                if node.type == "parameter_declaration":
                    declarators.append(node.child_by_field_name("declarator"))
                else:
                    # A declaration may contain multiple declarators.
                    declarators.extend(c for c in node.named_children
                                       if c is not type_node
                                       and c.type not in {"type_qualifier",
                                                          "attribute_specifier"})
                scope = _binding_scope(node)
                if scope is not None:
                    for declarator in declarators:
                        for name in _declarator_identifiers(declarator, src):
                            bindings[name].append({
                                "type": declared_type,
                                "position": node.start_byte,
                                "scope_start": scope.start_byte,
                                "scope_end": scope.end_byte,
                                "depth": depth,
                            })
        for child in node.named_children:
            visit(child, depth + 1)

    visit(root)
    return bindings


def _receiver_expression(call_node):
    """Return the expression to the left of `.`/`->` for a method call."""
    function = call_node.child_by_field_name("function")
    if function is None or function.type != "field_expression":
        return None
    return function.child_by_field_name("argument")


def _enclosing_class(call_node, src):
    """Infer `this` type for an unqualified call in a class method."""
    ancestor = call_node.parent
    while ancestor is not None:
        if ancestor.type in ("class_specifier", "struct_specifier"):
            name = ancestor.child_by_field_name("name")
            if name is not None:
                return _normalise_declared_type(_text(name, src))
        if ancestor.type == "function_definition":
            declarator = ancestor.child_by_field_name("declarator")
            if declarator is not None:
                qualified = []

                def collect(node):
                    if node.type == "qualified_identifier":
                        qualified.append(node)
                    for child in node.named_children:
                        collect(child)

                collect(declarator)
                if qualified:
                    qualified_text = _text(qualified[0], src)
                    if "::" in qualified_text:
                        qualifier = qualified_text.rsplit("::", 1)[0]
                        return _normalise_declared_type(
                            qualifier.rsplit("::", 1)[-1])
        ancestor = ancestor.parent
    return ""


def _receiver_type(call_node, src, type_bindings):
    """Resolve the receiver's explicit static type, or return unknown."""
    receiver = _receiver_expression(call_node)
    if receiver is None:
        return _enclosing_class(call_node, src)
    if receiver.type == "this":
        return _enclosing_class(call_node, src)
    if receiver.type != "identifier":
        return ""

    name = _text(receiver, src)
    candidates = []
    for binding in type_bindings.get(name, []):
        if (binding["position"] <= call_node.start_byte
                and binding["scope_start"] <= call_node.start_byte
                < binding["scope_end"]):
            candidates.append(binding)
    if not candidates:
        return ""
    # Innermost scope wins; within it, use the nearest preceding declaration.
    return max(candidates, key=lambda b: (
        -(b["scope_end"] - b["scope_start"]), b["position"]))["type"]


def _identifier_type(node, src, type_bindings):
    if node.type != "identifier":
        return ""
    name = _text(node, src)
    candidates = [binding for binding in type_bindings.get(name, [])
                  if binding["position"] <= node.start_byte
                  and binding["scope_start"] <= node.start_byte
                  < binding["scope_end"]]
    if not candidates:
        return ""
    return max(candidates, key=lambda binding: (
        -(binding["scope_end"] - binding["scope_start"]),
        binding["position"]))["type"]


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


def _format_arg_index(callee, args, src):
    """Resolve the declared format slot, including the mprf_p overload."""
    for i in FORMAT_SLOTS.get(callee, (0,)):
        if i >= len(args):
            continue
        arg = args[i]
        if (arg.type in ("string_literal", "concatenated_string")
                or (arg.type == "call_expression"
                    and _is_const_char_wrapper_call(arg, src))):
            return i
    return -1


def _format_literal_text(node, src):
    """Extract the contents of a literal (possibly wrapped in T_()).

    This intentionally accepts only statically visible string literals. A
    dynamic format cannot be mapped safely without type/signature information,
    so callers conservatively skip it rather than classifying non-%s slots.
    """
    # C_(context, message) carries a non-format context literal before the
    # actual translated message. Parsing the whole call would let `%` tokens in
    # the context shift or invent variadic slots.
    if node.type == "call_expression" and _callee_name(node, src) == "C_":
        for child in node.named_children:
            if child.type == "argument_list":
                call_args = list(child.named_children)
                return (_format_literal_text(call_args[1], src)
                        if len(call_args) >= 2 else None)
        return None

    text = _text(node, src)
    literals = re.findall(r'"(?:\\.|[^"\\])*"', text)
    if not literals:
        return None
    return "".join(literal[1:-1] for literal in literals)


def _printf_string_arg_indexes(fmt):
    """Return zero-based variadic argument indexes consumed by %s conversions.

    Handles sequential and POSIX positional conversions, including `*` width
    and precision arguments. Invalid/incomplete conversions are ignored. Mixed
    positional/sequential formats are mapped according to the explicit indexes
    and the sequential cursor; such formats are invalid printf usage anyway.
    """
    indexes = []
    next_arg = 0
    i = 0

    def positional_index(pos):
        return int(pos) - 1 if pos is not None and int(pos) > 0 else None

    while i < len(fmt):
        if fmt[i] != "%":
            i += 1
            continue
        i += 1
        if i < len(fmt) and fmt[i] == "%":
            i += 1
            continue

        match = re.match(r"(\d+)\$", fmt[i:])
        value_pos = match.group(1) if match else None
        if match:
            i += match.end()

        while i < len(fmt) and fmt[i] in "#0- +'":
            i += 1

        if i < len(fmt) and fmt[i] == "*":
            i += 1
            match = re.match(r"(\d+)\$", fmt[i:])
            if match:
                i += match.end()
            else:
                next_arg += 1
        else:
            while i < len(fmt) and fmt[i].isdigit():
                i += 1

        if i < len(fmt) and fmt[i] == ".":
            i += 1
            if i < len(fmt) and fmt[i] == "*":
                i += 1
                match = re.match(r"(\d+)\$", fmt[i:])
                if match:
                    i += match.end()
                else:
                    next_arg += 1
            else:
                while i < len(fmt) and fmt[i].isdigit():
                    i += 1

        for length in ("hh", "ll", "I32", "I64", "h", "l", "j", "z", "t", "L", "q"):
            if fmt.startswith(length, i):
                i += len(length)
                break
        if i >= len(fmt):
            break

        conversion = fmt[i]
        i += 1
        arg_index = positional_index(value_pos)
        if arg_index is None:
            arg_index = next_arg
            next_arg += 1
        if conversion == "s":
            indexes.append(arg_index)

    return indexes


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


def _classify_vararg(arg, src, type_bindings):
    """Classify a variadic argument node. Returns (rule, risk) or (None, None)."""
    if _ends_with_cstr(arg, src):
        return None, None
    if arg.type == "call_expression" and _is_const_char_wrapper_call(arg, src):
        return None, None

    if _is_string_ctor(arg, src):
        return "STRING_CTOR", "HIGH"

    if _identifier_type(arg, src, type_bindings) in {"string", "basic_string"}:
        return "STRING_OBJECT", "HIGH"

    if arg.type == "binary_expression":
        for child in arg.children:
            if not child.is_named and _text(child, src) == "+":
                if _binary_has_string_operand(arg, src):
                    return "CONCAT", "HIGH"
                return None, None

    if arg.type == "conditional_expression":
        branches = list(arg.named_children)[1:]
        for branch in branches:
            rule, risk = _classify_vararg(branch, src, type_bindings)
            if risk == "HIGH" or _contains_string_temp(branch, src):
                return "TERNARY", "HIGH"
        return None, None

    if arg.type == "parenthesized_expression":
        for c in arg.named_children:
            return _classify_vararg(c, src, type_bindings)

    if arg.type == "call_expression":
        name = _callee_name(arg, src)
        receiver_type = _receiver_type(arg, src, type_bindings)
        if receiver_type in STRING_RETURN_METHODS.get(name, set()):
            return "STRING_RETURN_CALL", "HIGH"
        if receiver_type in CONST_CHAR_METHODS.get(name, set()):
            return None, None
        if name in STRING_RETURN_FUNCS:
            return "STRING_RETURN_CALL", "HIGH"
        if name and name not in CONST_CHAR_FUNCS and name not in CONST_CHAR_WRAPPERS:
            return "CALL_NO_CSTR", "WARN"
        return None, None

    return None, None


def _find_line(node, src):
    return node.start_point[0] + 1


def _scan_call(call_node, src, findings, type_bindings):
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
    fmt_idx = _format_arg_index(callee, args, src)
    if fmt_idx < 0:
        return
    fmt_text = _format_literal_text(args[fmt_idx], src)
    if fmt_text is None:
        return
    varargs = args[fmt_idx + 1:]
    for arg_idx in sorted(set(_printf_string_arg_indexes(fmt_text))):
        if arg_idx < 0 or arg_idx >= len(varargs):
            continue
        arg = varargs[arg_idx]
        rule, risk = _classify_vararg(arg, src, type_bindings)
        if rule:
            findings.append({
                "callee": callee,
                "rule": rule,
                "risk": risk,
                "line": _find_line(arg, src),
                "arg": _text(arg, src)[:80],
                "node": arg,
            })


def _walk(node, src, findings, type_bindings):
    if node.type == "call_expression":
        _scan_call(node, src, findings, type_bindings)
    for child in node.children:
        _walk(child, src, findings, type_bindings)


def scan_file(filepath, parser, validate_parse=False):
    with open(filepath, "rb") as f:
        raw = f.read()
    # Phase-1 end-of-line normalization: tree-sitter and the directive
    # lexer must consume the same bytes (CODE-003), so a CRLF or bare-CR
    # file parses exactly like its LF form. The mapping is line-count
    # preserving, so reported line numbers are identical to the original
    # file's physical lines.
    src = _normalize_eol(raw)
    tree = parser.parse(src)
    if validate_parse and has_relevant_parse_error(tree.root_node, src):
        raise ValueError(f"tree-sitter parse error in {filepath}")
    findings = []
    type_bindings = _build_type_bindings(tree.root_node, src)
    _walk(tree.root_node, src, findings, type_bindings)
    for f in findings:
        f["file"] = filepath
        del f["node"]
    return findings


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
            files.append(os.path.abspath(f))
    else:
        root = os.path.abspath(args.source_dir)
        try:
            files = [path for path in discover_source_files(
                root, skip_dirs=CPP_AST_SCAN_SKIP_DIRS)
                if os.path.basename(path) not in SKIP_FILES]
        except (OSError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2

    if not files:
        print("No C++ source files found to scan.", file=sys.stderr)
        return 2
    coverage.discovered = len(files)
    source_arg = os.path.abspath(args.source_dir or "")
    production_root = (os.path.basename(source_arg) == "source"
                       and os.path.basename(os.path.dirname(source_arg))
                       == "crawl-ref")
    validate_parse = bool(args.files) or not production_root

    lang = _Language(_tscpp.language())
    parser = _Parser(lang)

    all_findings = []
    for fp in files:
        try:
            all_findings.extend(scan_file(fp, parser, validate_parse))
            coverage.scanned += 1
        except (OSError, ValueError) as exc:
            coverage.failed.append(f"{fp}: {exc}")

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
            "coverage": coverage.as_dict(),
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

    if coverage.failed:
        for failure in coverage.failed:
            print(f"ERROR: {failure}", file=sys.stderr)
        return 2
    high_count = sum(1 for f in all_findings if f["risk"] == "HIGH")
    return 1 if high_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
