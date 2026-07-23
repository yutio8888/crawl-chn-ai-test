#!/usr/bin/env python3
"""
i18n_extract.py — Extract and validate immediate and deferred translation keys.

Scans C++ source files for T_("English"), C_("ctx", "English"),
N_("English"), and NC_("ctx", "English") calls,
and Lua files for crawl.t_("English") calls,
extracts the English keys, and compares them against source.txt entries.

The escape logic in i18n_escape() MUST exactly mirror the C++ function
i18n_escape_key() in database.cc. Any change to one requires a matching
change to the other.

Usage:
    # Extract all keys from source files
    ./i18n_extract.py extract crawl-ref/source/

    # Validate coverage: check which keys are missing from source.txt
    ./i18n_extract.py validate crawl-ref/source/ --source-txt dat/i18n/zh/source.txt

    # Generate stub entries for missing keys
    ./i18n_extract.py missing crawl-ref/source/ --source-txt dat/i18n/zh/source.txt

    # Show keys that are in source.txt but no longer used in code
    ./i18n_extract.py stale crawl-ref/source/ --source-txt dat/i18n/zh/source.txt"""

import argparse
import bisect
import json
import os
import re
import sys
from collections import OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from i18n_shared import (CPP_SOURCE_EXTENSIONS, ScanCoverage,
                         discover_source_files, parse_source_txt, read_utf8)


# ══════════════════════════════════════════════════════════════════════════════
# Escape specification — MUST mirror i18n_escape_key() in database.cc
# ══════════════════════════════════════════════════════════════════════════════
#
# Order constraint: backslash MUST be first. If any other replacement runs
# before it, the inserted backslash would be re-escaped (double-escaping).
#
# \\ and \" (in C++ source) are unescaped by the compiler before the string
# reaches T_(), so they are NOT handled here. The runtime string already
# contains literal \ and " — no conversion needed.
#
# source.txt keys are bare single lines. " is a regular character, not
# a string delimiter, and does not need escaping.
# ══════════════════════════════════════════════════════════════════════════════

def i18n_escape(raw: str) -> str:
    """Normalize a C++ runtime string to source.txt key format."""
    s = raw
    s = s.replace("\\", "\\\\")   # 1st: backslash first — it's the escape introducer
    s = s.replace("\r", "\\r")
    s = s.replace("\n", "\\n")
    s = s.replace("\t", "\\t")
    return s


# C++ extraction uses the lexer below rather than a whole-file regex. This is
# important: marker-looking text in comments, ordinary strings, and raw strings
# must not satisfy coverage, while adjacent C++ string literals form one key.


def cpp_unescape(s: str) -> str:
    """Convert C++ string-literal escape sequences to their runtime characters.

    Uses a single left-to-right scan. Sequential replace() is NOT correct
    for decoding — see the \\\\n counterexample below.

    Example: C++ "\\\\n" → source chars \\ \\ n → compiler produces
    \\ (backslash) + n (literal n), TWO characters, NOT a newline.
    Sequential replace would incorrectly produce a newline (0x0A) because
    the backslash inserted by the first rule gets consumed by the second.
    A single-pass scanner avoids this because it advances past both chars
    of the escape sequence without re-scanning the output.

    Known boundary: hex/octal escapes (\\x41, \\101) are not handled.
    DCSS text is unlikely to use them; if encountered, they pass through
    with the backslash stripped (the letter following \\ is kept as-is).
    """
    out = []
    simple = {
        'n': '\n', 'r': '\r', 't': '\t', '\\': '\\',
        '"': '"', "'": "'", '0': '\0',
        'a': '\a', 'b': '\b', 'f': '\f', 'v': '\v',
    }
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c == '\\' and i + 1 < n:
            nxt = s[i + 1]
            # Known escape: use mapped char. Unknown: keep the character
            # after backslash (e.g. "\\% " in a format string).
            out.append(simple.get(nxt, nxt))
            i += 2
        else:
            out.append(c)
            i += 1
    return ''.join(out)


class DeferredMarkerSyntaxError(ValueError):
    """A deferred marker was called with a non-literal argument."""


def _splice_cpp_lines(content: str):
    """Apply C++ phase-2 line splicing and preserve original offsets.

    Backslash-LF and backslash-CRLF pairs are removed before comments, tokens,
    and ordinary strings are recognized. Raw-string bodies retain their source
    spelling, as required by the later raw-string phase adjustment.
    """
    # Almost every production source file has no phase-2 splice.  Avoid an
    # otherwise full character-by-character copy and offset-list allocation in
    # that common case.  ``range`` preserves the indexing contract used by the
    # extractor while representing the identity offset map without allocating
    # one Python integer per source character.
    if "\\\n" not in content and "\\\r\n" not in content:
        return content, range(len(content))

    out, offsets = [], []
    i, n = 0, len(content)
    state = "normal"
    raw_prefixes = ("u8R\"", "uR\"", "UR\"", "LR\"", "R\"")

    def copy(count=1):
        nonlocal i
        out.extend(content[i:i + count])
        offsets.extend(range(i, i + count))
        i += count

    while i < n:
        # Phase 2 applies in every state except a genuine raw-string body.
        # Raw strings are recognized only from normal code below; R"(...)"
        # text inside a comment must never suppress comment line splicing.
        if content[i] == "\\":
            if i + 1 < n and content[i + 1] == "\n":
                i += 2
                continue
            if (i + 2 < n and content[i + 1] == "\r"
                    and content[i + 2] == "\n"):
                i += 3
                continue

        if state == "line_comment":
            if content[i] == "\n":
                copy()
                state = "normal"
            else:
                copy()
            continue

        if state == "block_comment":
            if content.startswith("*/", i):
                copy(2)
                state = "normal"
            else:
                copy()
            continue

        if state in {"string", "char"}:
            closing = '"' if state == "string" else "'"
            if content[i] == "\\" and i + 1 < n:
                copy(2)
            elif content[i] == closing:
                copy()
                state = "normal"
            else:
                copy()
            continue

        # Normal code: comments take precedence over any raw-looking text.
        if content.startswith("//", i):
            copy(2)
            state = "line_comment"
            continue
        if content.startswith("/*", i):
            copy(2)
            state = "block_comment"
            continue

        raw_prefix = next((p for p in raw_prefixes
                           if content.startswith(p, i)), None)
        if raw_prefix is not None:
            quote = i + len(raw_prefix) - 1
            open_paren = content.find("(", quote + 1, min(n, quote + 18))
            if open_paren >= 0:
                delimiter = content[quote + 1:open_paren]
                close = ")" + delimiter + '"'
                end = content.find(close, open_paren + 1)
                if end >= 0:
                    copy(end + len(close) - i)
                    continue

        if content[i] == '"':
            copy()
            state = "string"
        elif content[i] == "'":
            copy()
            state = "char"
        else:
            copy()
    return ''.join(out), offsets


def _cpp_tokens(content: str):
    """Yield (kind, value, offset) tokens needed to parse i18n calls.

    This deliberately small lexer understands comments, identifiers, ordinary
    and raw string literals, character literals, and punctuation. It is not a
    C++ parser, but unlike regex scanning it never searches inside skipped text.
    STRING values are already converted to their runtime contents.
    """
    i, n = 0, len(content)
    string_prefixes = ("u8R\"", "uR\"", "UR\"", "LR\"", "R\"",
                       "u8\"", "u\"", "U\"", "L\"", "\"")
    char_prefixes = ("u8'", "u'", "U'", "L'", "'")
    while i < n:
        if content[i].isspace():
            i += 1
            continue
        if content.startswith("//", i):
            end = content.find("\n", i + 2)
            body_end = n if end < 0 else end
            yield ("COMMENT", content[i + 2:body_end], i + 2)
            i = n if end < 0 else end + 1
            continue
        if content.startswith("/*", i):
            end = content.find("*/", i + 2)
            body_end = n if end < 0 else end
            yield ("COMMENT", content[i + 2:body_end], i + 2)
            i = n if end < 0 else end + 2
            continue

        prefix = next((p for p in string_prefixes
                       if content.startswith(p, i)), None)
        if prefix is not None:
            start = i
            if "R\"" in prefix:
                quote = i + len(prefix) - 1
                open_paren = content.find("(", quote + 1,
                                          min(n, quote + 18))
                if open_paren < 0:
                    i += len(prefix)
                    continue
                delimiter = content[quote + 1:open_paren]
                close = ")" + delimiter + '"'
                end = content.find(close, open_paren + 1)
                if end < 0:
                    i = n
                    continue
                yield ("STRING", content[open_paren + 1:end], start)
                i = end + len(close)
                continue

            quote = i + len(prefix) - 1
            j = quote + 1
            while j < n:
                if content[j] == "\\":
                    j += 2
                elif content[j] == '"':
                    break
                else:
                    j += 1
            if j >= n:
                i = n
                continue
            yield ("STRING", cpp_unescape(content[quote + 1:j]), start)
            i = j + 1
            continue

        char_prefix = next((p for p in char_prefixes
                            if content.startswith(p, i)), None)
        if char_prefix is not None:
            quote = i + len(char_prefix) - 1
            j = quote + 1
            while j < n:
                if content[j] == "\\":
                    j += 2
                elif content[j] == "'":
                    j += 1
                    break
                else:
                    j += 1
            i = j
            continue

        if content[i].isalpha() or content[i] == "_":
            start = i
            i += 1
            while i < n and (content[i].isalnum() or content[i] == "_"):
                i += 1
            yield ("IDENT", content[start:i], start)
            continue

        yield (content[i], content[i], i)
        i += 1


def _literal_argument(tokens, index, adjacent=True):
    """Parse a STRING token, joining adjacent tokens when requested."""
    if index >= len(tokens) or tokens[index][0] != "STRING":
        return None, index
    parts = []
    while index < len(tokens) and tokens[index][0] == "STRING":
        parts.append(tokens[index][1])
        index += 1
        if not adjacent:
            break
    return ''.join(parts), index


def _argument_end(tokens, index):
    """Find the comma/closing paren ending one call argument."""
    stack = []
    pairs = {"(": ")", "[": "]", "{": "}"}
    while index < len(tokens):
        kind = tokens[index][0]
        if kind in pairs:
            stack.append(pairs[kind])
        elif stack and kind == stack[-1]:
            stack.pop()
        elif not stack and kind in {",", ")"}:
            break
        index += 1
    return index


def _strip_grouping(tokens):
    while len(tokens) >= 2 and tokens[0][0] == "(" and tokens[-1][0] == ")":
        depth = 0
        closes_at_end = False
        for pos, token in enumerate(tokens):
            if token[0] == "(":
                depth += 1
            elif token[0] == ")":
                depth -= 1
                if depth == 0:
                    closes_at_end = pos == len(tokens) - 1
                    break
        if not closes_at_end:
            break
        tokens = tokens[1:-1]
    return tokens


def _finite_literal_leaves(tokens):
    """Return (literal leaves, complete) for a finite ?: expression."""
    tokens = _strip_grouping(list(tokens))
    literal, end = _literal_argument(tokens, 0, adjacent=True)
    if literal is not None and end == len(tokens):
        return [literal], True

    depth = 0
    question = None
    nested_questions = 0
    colon = None
    for pos, token in enumerate(tokens):
        kind = token[0]
        if kind in {"(", "[", "{"}:
            depth += 1
        elif kind in {")", "]", "}"}:
            depth -= 1
        elif depth == 0 and kind == "?":
            if question is None:
                question = pos
            else:
                nested_questions += 1
        elif depth == 0 and kind == ":" and question is not None:
            if nested_questions:
                nested_questions -= 1
            else:
                colon = pos
                break
    if question is None or colon is None:
        return [], False
    left, left_complete = _finite_literal_leaves(tokens[question + 1:colon])
    right, right_complete = _finite_literal_leaves(tokens[colon + 1:])
    return left + right, left_complete and right_complete


def _lua_tokens(content):
    """Tokenize enough Lua to find real crawl.t_(literal) calls."""
    i, size = 0, len(content)
    while i < size:
        if content[i].isspace():
            i += 1
            continue
        long_comment = re.match(r"--\[(=*)\[", content[i:])
        if long_comment:
            close = "]" + long_comment.group(1) + "]"
            end = content.find(close, i + long_comment.end())
            i = size if end < 0 else end + len(close)
            continue
        if content.startswith("--", i):
            end = content.find("\n", i + 2)
            i = size if end < 0 else end + 1
            continue
        long_string = re.match(r"\[(=*)\[", content[i:])
        if long_string:
            start = i
            close = "]" + long_string.group(1) + "]"
            body_start = i + long_string.end()
            end = content.find(close, body_start)
            if end < 0:
                raise ValueError(f"unterminated Lua long string at offset {start}")
            yield "STRING", content[body_start:end], start
            i = end + len(close)
            continue
        if content[i] in {'"', "'"}:
            quote, start = content[i], i
            i += 1
            raw = []
            while i < size and content[i] != quote:
                if content[i] == "\\" and i + 1 < size:
                    raw.extend(content[i:i + 2])
                    i += 2
                else:
                    raw.append(content[i])
                    i += 1
            if i >= size:
                raise ValueError(f"unterminated Lua string at offset {start}")
            i += 1
            yield "STRING", cpp_unescape(''.join(raw)), start
            continue
        if content[i].isalpha() or content[i] == "_":
            start = i
            i += 1
            while i < size and (content[i].isalnum() or content[i] == "_"):
                i += 1
            yield "IDENT", content[start:i], start
            continue
        yield content[i], content[i], i
        i += 1


def _extract_lua_calls(content):
    tokens = list(_lua_tokens(content))
    for i in range(len(tokens) - 5):
        if (tokens[i][:2] == ("IDENT", "crawl")
                and tokens[i + 1][0] == "."
                and tokens[i + 2][:2] == ("IDENT", "t_")
                and tokens[i + 3][0] == "("
                and tokens[i + 4][0] == "STRING"
                and tokens[i + 5][0] == ")"):
            yield tokens[i + 4][1], tokens[i][2]


def _is_marker_definition(content: str, offset: int, name: str) -> bool:
    """Return true only for the marker's own #define declaration line."""
    start = content.rfind("\n", 0, offset) + 1
    end = content.find("\n", offset)
    if end < 0:
        end = len(content)
    return re.match(rf"\s*#\s*define\s+{re.escape(name)}\s*\(",
                    content[start:end]) is not None


def _extract_comment_markers(comment: str, base_offset: int):
    """Yield deferred extraction annotations from one comment token.

    N_/NC_ syntax in comments is explicitly an annotation. Other surrounding
    comment text, including raw-string-looking text, has no C++ lexical meaning.
    Non-literal marker arguments fail closed just like markers in normal code.
    """
    cursor = 0
    marker_re = re.compile(r"\b(?:N_|NC_)\s*\(")
    while True:
        match = marker_re.search(comment, cursor)
        if match is None:
            return
        tokens = [token for token in _cpp_tokens(comment[match.start():])
                  if token[0] != "COMMENT"]
        name = match.group(0).split("(", 1)[0].strip()
        contextual = name == "NC_"
        if (len(tokens) < 3 or tokens[0][0] != "IDENT"
                or tokens[0][1] != name or tokens[1][0] != "("):
            raise DeferredMarkerSyntaxError(
                f"{name} comment annotation is malformed",
                base_offset + match.start())
        first, j = _literal_argument(tokens, 2, adjacent=True)
        if first is None:
            raise DeferredMarkerSyntaxError(
                f"{name} requires string-literal arguments",
                base_offset + match.start())
        if contextual:
            if j >= len(tokens) or tokens[j][0] != ",":
                raise DeferredMarkerSyntaxError(
                    "NC_ requires a literal context and key",
                    base_offset + match.start())
            second, j = _literal_argument(tokens, j + 1, adjacent=True)
            if second is None:
                raise DeferredMarkerSyntaxError(
                    "NC_ requires a literal context and key",
                    base_offset + match.start())
            key, ctx = second, first
        else:
            key, ctx = first, None
        if j >= len(tokens) or tokens[j][0] != ")":
            raise DeferredMarkerSyntaxError(
                f"{name} requires only string-literal arguments",
                base_offset + match.start())
        marker_end = match.start() + tokens[j][2] + 1
        yield key, ctx, base_offset + match.start()
        cursor = marker_end


def _extract_cpp_calls(content: str, ignore_marker_definitions=False):
    """Yield (runtime key, runtime context or None, source offset)."""
    spliced, original_offsets = _splice_cpp_lines(content)
    all_tokens = list(_cpp_tokens(spliced))
    tokens = [token for token in all_tokens if token[0] != "COMMENT"]
    results = []
    for i, token in enumerate(tokens):
        if token[0] != "IDENT" or token[1] not in {"T_", "C_", "N_", "NC_"}:
            continue
        contextual = token[1] in {"C_", "NC_"}
        deferred = token[1] in {"N_", "NC_"}
        if i + 1 >= len(tokens) or tokens[i + 1][0] != "(":
            continue
        # Join adjacent C++ string literals for all T_/C_/N_/NC_.
        # C++ compilers concatenate adjacent "foo" "bar" into "foobar";
        # our extractor mirrors this by joining consecutive STRING tokens.
        arg_end = _argument_end(tokens, i + 2)
        first, j = _literal_argument(tokens, i + 2, adjacent=True)
        if first is None:
            original_offset = original_offsets[token[2]]
            is_own_definition = (ignore_marker_definitions
                                 and _is_marker_definition(
                                     content, original_offset, token[1]))
            leaves, complete = _finite_literal_leaves(tokens[i + 2:arg_end])
            if not contextual and leaves and not deferred:
                results.extend((leaf, None, original_offset) for leaf in leaves)
                if not complete:
                    print(f"WARNING: dynamic {token[1]}() branch at offset "
                          f"{original_offset}; extracted literal arms only",
                          file=sys.stderr)
                continue
            if deferred and not is_own_definition:
                raise DeferredMarkerSyntaxError(
                    f"{token[1]} requires string-literal arguments",
                    original_offset)
            continue
        if contextual:
            if j >= len(tokens) or tokens[j][0] != ",":
                if deferred:
                    raise DeferredMarkerSyntaxError(
                        "NC_ requires a literal context and key",
                        original_offsets[token[2]])
                continue
            second_start = j + 1
            second_end = _argument_end(tokens, second_start)
            second, j = _literal_argument(tokens, second_start, adjacent=True)
            if second is None:
                leaves, complete = _finite_literal_leaves(
                    tokens[second_start:second_end])
                if leaves and not deferred:
                    results.extend((leaf, first, original_offsets[token[2]])
                                   for leaf in leaves)
                    if not complete:
                        print(f"WARNING: dynamic {token[1]}() branch at offset "
                              f"{original_offsets[token[2]]}; extracted literal arms only",
                              file=sys.stderr)
                    continue
                if deferred:
                    raise DeferredMarkerSyntaxError(
                        "NC_ requires a literal context and key",
                        original_offsets[token[2]])
                continue
            key, ctx = second, first
        else:
            key, ctx = first, None
        if j >= len(tokens) or tokens[j][0] != ")":
            if deferred:
                raise DeferredMarkerSyntaxError(
                    f"{token[1]} requires only string-literal arguments",
                    original_offsets[token[2]])
            continue
        results.append((key, ctx, original_offsets[token[2]]))

    for comment_token in (token for token in all_tokens
                          if token[0] == "COMMENT"):
        for key, ctx, spliced_offset in _extract_comment_markers(
                comment_token[1], comment_token[2]):
            results.append((key, ctx, original_offsets[spliced_offset]))

    yield from sorted(results, key=lambda result: result[2])


def extract_keys_from_file(filepath: str):
    """Yield (key, context, line_number) tuples from a C++ or Lua source file.

    key: the normalized source.txt key (cpp_unescape + i18n_escape applied)
    context: None for T_()/N_()/crawl.t_(), context string for C_()/NC_()
    """
    content = read_utf8(filepath)

    offsets = _build_lineno_map(content)
    lines = content.split("\n")

    is_lua = filepath.endswith(".lua")

    if is_lua:
        for key_runtime, offset in _extract_lua_calls(content):
            key = i18n_escape(key_runtime)
            lineno = _offset_to_lineno(offsets, offset)
            line_text = lines[lineno - 1].strip() if lineno <= len(lines) else ""
            yield (key, None, filepath, lineno, line_text)
        return

    try:
        calls = _extract_cpp_calls(
            content, ignore_marker_definitions=filepath.endswith("/i18n.h"))
        for key_runtime, ctx_runtime, offset in calls:
            key = i18n_escape(key_runtime)
            ctx = i18n_escape(ctx_runtime) if ctx_runtime is not None else None
            lineno = _offset_to_lineno(offsets, offset)
            line_text = lines[lineno - 1].strip() if lineno <= len(lines) else ""
            yield (key, ctx, filepath, lineno, line_text)
    except DeferredMarkerSyntaxError as exc:
        offset = exc.args[1]
        lineno = _offset_to_lineno(offsets, offset)
        raise DeferredMarkerSyntaxError(
            f"{filepath}:{lineno}: {exc.args[0]}") from None

    # Regexes intentionally require literal arguments. Dynamic T_(variable)
    # remains invisible and must be covered by explicit N_/NC_ markers or a
    # data-source audit; pretending to infer its possible values is unsafe.
    return


def _build_lineno_map(text: str) -> list:
    """Record byte offsets where each line starts. Use bisect for lookup."""
    offsets = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            offsets.append(i + 1)
    return offsets

def _offset_to_lineno(offsets: list, pos: int) -> int:
    """Convert byte offset to 1-based line number."""
    idx = bisect.bisect_right(offsets, pos) - 1
    return idx + 1  # 1-based


def scan_source_dir(root: str, coverage=None) -> list:
    """Walk source and extract T_/C_/N_/NC_/crawl.t_ literal keys."""
    all_keys = []  # [(key, context, file, line, line_text), ...]
    extensions = set(CPP_SOURCE_EXTENSIONS) | {".lua"}
    files = discover_source_files(root, extensions=extensions)
    coverage = coverage or ScanCoverage()
    coverage.discovered = len(files)
    if not files:
        raise ValueError(f"no supported source files found under {root}")
    for filepath in files:
        try:
            all_keys.extend(extract_keys_from_file(filepath))
            coverage.scanned += 1
        except (OSError, UnicodeError, ValueError) as exc:
            coverage.failed.append(f"{filepath}: {exc}")
    if coverage.failed:
        raise OSError("source scan failed: " + "; ".join(coverage.failed))
    return all_keys


def _scan_with_report(args):
    coverage = ScanCoverage()
    keys = scan_source_dir(args.source_dir, coverage)
    if getattr(args, "report_json", None):
        with open(args.report_json, "w", encoding="utf-8") as report:
            json.dump({"scanner": "i18n_extract.py",
                       "coverage": coverage.as_dict()}, report,
                      ensure_ascii=False, indent=2)
            report.write("\n")
    return keys


def _load_source_entries(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    return parse_source_txt(path)


def cmd_extract(args):
    """Print all extracted keys."""
    keys = _scan_with_report(args)
    # Sort by key, then by file
    keys.sort(key=lambda x: (x[0], x[2]))
    for key, ctx, fpath, lineno, line_text in keys:
        prefix = f"{ctx}|" if ctx else ""
        print(f"{prefix}{key}")
        if args.verbose:
            print(f"  {fpath}:{lineno}: {line_text}")


def cmd_validate(args):
    """Check which extracted keys are missing from source.txt."""
    keys = _scan_with_report(args)
    entries = _load_source_entries(args.source_txt)

    # Deduplicate keys
    seen = set()
    unique_keys = []
    for key, ctx, fpath, lineno, line_text in keys:
        full_key = f"{ctx}|{key}" if ctx else key
        if full_key not in seen:
            seen.add(full_key)
            unique_keys.append((full_key, fpath, lineno, line_text))

    missing = []
    for full_key, fpath, lineno, line_text in unique_keys:
        if full_key.lower() not in entries:
            missing.append((full_key, fpath, lineno, line_text))

    if not seen:
        print("WARNING: No T_() or C_() calls found in source directory.")
        return 2
    if missing:
        print(f"MISSING: {len(missing)} keys in source code but not in {args.source_txt}")
        print()
        for full_key, fpath, lineno, _ in sorted(missing):
            print(f"  {fpath}:{lineno}: {full_key}")
        print()
        print(f"Total: {len(seen)} unique keys, {len(missing)} missing "
              f"({100 * (len(seen) - len(missing)) / len(seen):.1f}% coverage)")
        return 1
    else:
        print(f"OK: All {len(seen)} keys found in {args.source_txt} (100% coverage)")
        return 0


def cmd_missing(args):
    """Print stub entries for missing keys."""
    keys = _scan_with_report(args)
    entries = _load_source_entries(args.source_txt)

    seen = set()
    missing_entries = OrderedDict()
    for key, ctx, fpath, lineno, line_text in keys:
        full_key = f"{ctx}|{key}" if ctx else key
        if full_key not in seen:
            seen.add(full_key)
            if full_key.lower() not in entries:
                # Show the key as it should appear in source.txt (with literal escapes)
                missing_entries[full_key] = (fpath, lineno)

    if not missing_entries:
        print(f"OK: No missing keys.")
        return 0

    for full_key, (fpath, lineno) in missing_entries.items():
        print("%%%%")
        print(full_key)
        print(f"⚠️[missing — {fpath}:{lineno}]")
    return 0


def cmd_stale(args):
    """Find keys in source.txt that are no longer referenced in code."""
    keys = _scan_with_report(args)
    entries = _load_source_entries(args.source_txt)

    referenced = set()
    for key, ctx, _, _, _ in keys:
        full_key = f"{ctx}|{key}" if ctx else key
        referenced.add(full_key.lower())

    stale = []
    for stored_key in entries:
        if stored_key.lower() not in referenced:
            stale.append(stored_key)

    if stale:
        print(f"STALE: {len(stale)} keys in {args.source_txt} with no "
              f"matching T_() call")
        print()
        for k in sorted(stale):
            print(f"  {k}")
        return 0
    else:
        print(f"OK: No stale keys.")
        return 0


def cmd_check_escapes(args):
    """Verify that source.txt keys with backslash follow the escape convention."""
    keys = _scan_with_report(args)
    entries = _load_source_entries(args.source_txt)

    # Collect all keys from code
    code_keys = set()
    for key, ctx, _, _, _ in keys:
        full_key = f"{ctx}|{key}" if ctx else key
        code_keys.add(full_key.lower())

    issues = []
    for stored_key in entries:
        if "\\" in stored_key:
            # Check: does this stored key, when cpp_unescaped + re-escaped,
            # match any code key?
            # This is a heuristic — we can't perfectly reverse without the
            # original C++ literal, but we can flag potential drift.
            if stored_key.lower() not in code_keys:
                # Try reversing the escape and see if the unescaped form
                # exists in code
                issues.append(stored_key)

    if issues:
        print(f"WARNING: {len(issues)} keys with backslash in source.txt"
              f" have no direct match in code. Manual review may be needed.")
        for k in sorted(issues):
            print(f"  {k}")
    else:
        print(f"OK: All backslash-containing keys have matches in code.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Extract and validate T_() translation keys"
    )
    subparsers = parser.add_subparsers(dest="command", help="Subcommands")

    p_extract = subparsers.add_parser("extract", help="Print all extracted keys")
    p_extract.add_argument("source_dir", help="Root of C++ source tree")
    p_extract.add_argument("-v", "--verbose", action="store_true")
    p_extract.add_argument("--report-json")

    p_validate = subparsers.add_parser("validate", help="Check key coverage")
    p_validate.add_argument("source_dir")
    p_validate.add_argument("--source-txt", required=True,
                            help="Path to source.txt")
    p_validate.add_argument("--report-json")

    p_missing = subparsers.add_parser("missing",
                                       help="Print stub entries for missing keys")
    p_missing.add_argument("source_dir")
    p_missing.add_argument("--source-txt", required=True)
    p_missing.add_argument("--report-json")

    p_stale = subparsers.add_parser("stale",
                                     help="Find unreferenced source.txt entries")
    p_stale.add_argument("source_dir")
    p_stale.add_argument("--source-txt", required=True)
    p_stale.add_argument("--report-json")

    p_escape = subparsers.add_parser("check-escapes",
                                      help="Check backslash escape consistency")
    p_escape.add_argument("source_dir")
    p_escape.add_argument("--source-txt", required=True)
    p_escape.add_argument("--report-json")

    args = parser.parse_args()

    try:
        if args.command == "extract":
            return cmd_extract(args)
        elif args.command == "validate":
            return cmd_validate(args)
        elif args.command == "missing":
            return cmd_missing(args)
        elif args.command == "stale":
            return cmd_stale(args)
        elif args.command == "check-escapes":
            return cmd_check_escapes(args)
        else:
            parser.print_help()
            return 1
    except (DeferredMarkerSyntaxError, OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
