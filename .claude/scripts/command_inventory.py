#!/usr/bin/env python3
"""Deterministic read-only command inventory for the R3 (commands
sub-batch) review.

Identity source: the command_type enum in crawl-ref/source/command-type.h.
Every member is recorded in declaration order; the first member must be
CMD_NO_CMD (the keybinding sentinel value 2000) and the last member must be
CMD_MAX_CMD, the "Must always be last" enum sentinel. The baseline enum has
306 members. (The task brief names the sentinel "NUM_COMMANDS"; that
identifier does not exist anywhere in the baseline tree -- the real
sentinel is CMD_MAX_CMD -- so the tool asserts and records CMD_MAX_CMD.)

Name sources: macro.cc `_command_name_list` (populated from the generated
`#include "cmd-name.h"`) feeds the two maps `_cmds_to_names`
(command enum value -> "CMD_X" name) and `_names_to_cmds` (name -> command
enum value) used by `command_to_name()` / `name_to_command()`. `cmd-name.h`
is generated at build time by util/cmd-name.pl from command-type.h and is NOT
tracked in Git, so the tool reproduces the generator's deterministic physical
entries exactly from the baseline enum blob: cmd-name.pl reads and discards
the CMD_NO_CMD anchor line, then emits every later member up to (but
excluding) CMD_DISABLE_MORE under its own identifier, skipping
CMD_MIN_*/CMD_MAX_* aliases. The generated array ends with
`{CMD_NO_CMD, nullptr}`, but macro.cc `init_keybindings()` stops before that
sentinel and never inserts CMD_NO_CMD into either map. Because the forward map
is keyed by enum value rather than identifier spelling, a skipped range alias
normally resolves to the physically emitted name that shares its value (for
example CMD_MIN_MENU -> CMD_MENU_UP); CMD_MIN_SYNTHETIC aliases the un-emitted
CMD_DISABLE_MORE value and still falls back to CMD_NO_CMD. The reverse map is
the identity map over the physical non-sentinel entries. `command_to_name()`
returns "CMD_NO_CMD" for any enum value outside the table (including
CMD_NO_CMD itself) and `name_to_command()` returns CMD_NO_CMD for any unknown
name -- the NO_CMD fallback exception to the `CMD_[A-Z0-9_]+` name shape.
The macro.cc audit regions (the include of cmd-name.h, the two map
declarations, and the exact bodies of name_to_command()/command_to_name())
are verified with exact fail-closed patterns, so a structural change to the
name-map machinery in macro.cc aborts the run.

Description keys: crawl-ref/source/dat/descript/commands.txt (EN) and
crawl-ref/source/dat/descript/zh/commands.txt (ZH) are parsed with the
production database.cc `_parse_text_db` semantics (trim_keys=true, the
description DB path): entries begin only after the first `%%%%`, comment
lines (first char '#') are the only skipped lines, blank lines inside a
value are preserved, value lines are right-trimmed per C++ rules
(" \\t\\n\\r" only), at flush only leading newlines are trimmed, and the
canonical key space is the production lowercase (lowercase_string) of the
C++-trimmed key line. The complete key list of each file is merged with
the production DBM_REPLACE last-wins semantics and every override
(including the baseline's in-file EN duplicate `CMD_EXPLORE_NO_REST`
terse key) is recorded as an override fact, never dropped silently. Only
the `CMD_*` key subspace is audited (the files also carry unrelated
`android command menu|*` keys); every CMD_-prefixed physical key must
match the `CMD_[A-Z0-9_]+( verbose)?` shape or the run aborts. The key
sets are reported split terse/verbose, with the en_only/zh_only
bidirectional differences; every key is back-referenced to its enum
member with name_to_command() semantics -- keys whose base name is absent
from the reverse table (e.g. the baseline ZH-only `CMD_SHOW_KEYBOARD
verbose`, which names a command that does not exist in the enum) are
reported truthfully in `unresolved_keys` / `stale_keys` instead of being
silently passed; the baseline itself contains such a key, so aborting on
it would make the tool unusable on the real tree.

Consumers modeled: describe.cc `get_command_description()` (USE_TILE_LOCAL)
looks up `command_to_name(cmd)` [+ " verbose"], with the verbose -> terse
(+ ".") -> key-name fallback chain; tilereg-cmd.cc consumes the terse form;
hints.cc `hint_replace_cmds()` expands `$cmd[CMD_X]` through
name_to_command() (an unknown name resolves to CMD_NO_CMD). Each inventory
entry reports the effective terse/verbose EN and ZH description values and
the production display strings of the full fallback chain.

The payload also binds the localized SourceDB `dat/i18n/zh/source.txt`
(parsed with the production trim_keys=false source semantics via
i18n_shared.parse_entries_physical: physical keys verbatim, canonical keys
lowercased, an in-file duplicate canonical key is a fail-closed error) and
reports any SourceDB canonical key in the `cmd_*` name space (a command
identity authored into the translatable SourceDB would be a cross-domain
hazard; command names are identity strings, never T_()/C_() keys). The
baseline source.txt contains none.

All inputs are read from Git objects at the baseline commit via
`git show <ref>:<path>` -- never from the local worktree -- under the
shared trusted git environment (i18n_shared.trusted_git_environment()),
which forces GIT_NO_REPLACE_OBJECTS=1 and strips caller-controlled GIT_*
variables, so a `git replace A B` ref can never substitute another
commit's blobs for the exact baseline OID.

The output JSON write is fail-closed (R2-CODE2-003 pattern): the output
path must be exactly one brand-new basename directly under the canonical
non-renamable temp root /tmp (root-owned, sticky; on macOS realpath
/private/tmp). Nested components, `.` and `..` components, relative
paths, renamable roots such as the OS user temp dir, and symlink escapes
are rejected; the trusted root is opened once and the target is created
with O_EXCL|O_NOFOLLOW (see write_inventory_output()).

With `--review-results`, the tool additionally reads one strict canonical
JSONL evidence-card block and proves exact, unique, identity-bound review
coverage against the rebuilt baseline inventory. Review coverage is appended
to the output payload only after the inventory digest is calculated.

Usage:
  python3 .claude/scripts/command_inventory.py --baseline-ref <commit> \
      --inventory-output /tmp/command-inventory-<new-file>.json \
      [--review-results docs/command-review-results.md]

  --inventory-output must be a single brand-new basename directly under
  /tmp (the canonical root-owned sticky temp root; realpath /private/tmp
  on macOS); the target must not already exist.
"""
import argparse
from collections import Counter
import errno
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from i18n_shared import (AuditInput, load_review_input,  # noqa: E402
                         lowercase_string, review_input_metadata,
                         parse_entries_physical, trim_leading_newlines,
                         trim_string, trim_string_right,
                         trusted_git_environment)

#: Git-tree paths of the audited inputs (repo-root relative).
COMMAND_TYPE_H = "crawl-ref/source/command-type.h"
MACRO_CC = "crawl-ref/source/macro.cc"
COMMANDS_EN = "crawl-ref/source/dat/descript/commands.txt"
COMMANDS_ZH = "crawl-ref/source/dat/descript/zh/commands.txt"
SOURCE_TXT = "crawl-ref/source/dat/i18n/zh/source.txt"
GLOSSARY_MD = "docs/glossary.md"

STRICT_REVIEW_BEGIN = "<!-- BEGIN STRICT REVIEW EVIDENCE v2 -->"
STRICT_REVIEW_END = "<!-- END STRICT REVIEW EVIDENCE v2 -->"
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
    "dependency_group",
    "display_context",
    "evidence_locations",
    "fact_sha256",
    "glossary_authority",
    "identity",
    "lifecycle",
    "lookup_name",
    "missing_t",
    "name_in_map",
    "producer",
    "production_facts",
    "proposed_translation",
    "reentry_trigger",
    "rejected_alternatives",
    "reviewer_rationale",
    "terminal_conclusion",
}
_VAGUE_DEFERRAL_VALUES = {
    "n/a", "none", "not applicable", "tbd", "todo", "unknown",
    "不适用", "待定", "无",
}

#: command_type enum sentinels/anchors asserted by the strict parser.
FIRST_MEMBER = "CMD_NO_CMD"
LAST_MEMBER = "CMD_MAX_CMD"
#: util/cmd-name.pl stops the generated name table at (exclusive)
#: CMD_DISABLE_MORE -- everything from it on is synthetic/unboundable.
NAME_TABLE_STOP = "CMD_DISABLE_MORE"

#: Strict member shape: CMD_ + uppercase ASCII letters/digits/underscore,
#: optionally `= <integer>` or `= CMD_X` (enum aliases like
#: CMD_MIN_TILE = CMD_EDIT_PLAYER_TILE). Group 2 captures the initializer.
_ENUM_MEMBER_RE = re.compile(
    r"(CMD_[A-Z0-9_]+)(?:\s*=\s*(\d+|CMD_[A-Z0-9_]+))?")

#: Description-key name shape (physical key line, production key trim
#: already applied): CMD_[A-Z0-9_]+ optionally followed by ` verbose`.
_KEY_NAME_RE = re.compile(r"CMD_[A-Z0-9_]+(?: verbose)?")

#: The canonical (lowercased) command-key shape, used to separate the
#: audited CMD_* subspace from unrelated keys (android command menu|*).
_CMD_CANON_RE = re.compile(r"cmd_[a-z0-9_]+(?: verbose)?")


def resolve_commit(ref: str) -> str:
    """Resolve a git commit-ish to its full 40-hex SHA, fail-closed.

    Runs under the shared trusted git environment
    (i18n_shared.trusted_git_environment()), which forces
    GIT_NO_REPLACE_OBJECTS=1 so a `git replace` ref can never resolve
    the rev to another object; the environment also strips
    caller-controlled GIT_* variables for determinism.
    """
    r = subprocess.run(
        ["git", "rev-parse", "--verify", "--end-of-options",
         f"{ref}^{{commit}}"],
        capture_output=True, text=True, cwd=ROOT,
        env=trusted_git_environment())
    oid = r.stdout.strip()
    if r.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", oid):
        print(
            f"error: --baseline-ref {ref!r} does not resolve to a commit "
            f"in {ROOT}",
            file=sys.stderr)
        if r.stderr.strip():
            print(r.stderr.strip(), file=sys.stderr)
        raise SystemExit(1)
    return oid


def git_show_blob(ref: str, rel_path: str) -> bytes:
    """Return the raw blob content of a tracked file at a git commit.

    The content comes from `git show <ref>:<rel_path>` (with
    `--end-of-options` so the ref can never be parsed as an option), i.e.
    from the Git object database, never from the worktree. The trusted
    git environment forces GIT_NO_REPLACE_OBJECTS=1, so a
    `git replace <ref> <other>` ref cannot substitute another commit's
    blob for the exact baseline OID. Fail-closed: a non-zero exit
    (missing path or object) aborts the run with exit code 1. A
    legitimate zero-byte blob (return code 0, empty output) is accepted.
    """
    r = subprocess.run(
        ["git", "show", "--end-of-options", f"{ref}:{rel_path}"],
        capture_output=True, cwd=ROOT, env=trusted_git_environment())
    if r.returncode != 0:
        print(
            f"error: cannot read {rel_path} at {ref} "
            f"(git show exit code {r.returncode})",
            file=sys.stderr)
        if r.stderr.strip():
            print(r.stderr.decode("utf-8", "replace").strip(),
                  file=sys.stderr)
        raise SystemExit(1)
    return r.stdout


def _matching_brace(text: str, open_idx: int) -> int:
    """Index of the brace matching text[open_idx] ('{'), fail-closed.

    The bodies this helper walks (the command_type enum) contain no
    braces inside string literals, so a plain depth count is exact.
    """
    depth = 0
    for i in range(open_idx, len(text)):
        ch = text[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
    raise SystemExit("unbalanced braces in baseline blob")


# ---------------------------------------------------------------------------
# Strict preprocessor frame tracking (R2-CODE-002 pattern)
# ---------------------------------------------------------------------------

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_COND_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\s*(?:==|!=|<=|>=|<|>)\s*"
    r"(?:[A-Za-z_][A-Za-z0-9_]*|\d+))?$")
_DEFINED_RE = re.compile(r"^!?defined\s+[A-Za-z_][A-Za-z0-9_]*$")


def _parse_directive(directive_text: str) -> tuple[str, str | None]:
    """Parse one preprocessor directive line into (kind, condition).

    kind is one of 'if'/'ifdef'/'ifndef'/'elif'/'else'/'endif'. The
    conditions are validated per kind: `#ifdef`/`#ifndef` take exactly
    one macro identifier (the command-type.h form, e.g. USE_TILE,
    __ANDROID__, TARGET_OS_MACOSX); `#if`/`#elif` take a single
    identifier comparison or a `[!]defined NAME` form. Unknown
    directives, malformed conditions and trailing tokens abort the run.
    """
    text = directive_text.strip()
    if "//" in text:
        text = text.split("//", 1)[0].rstrip()
    if text.startswith("#ifdef "):
        cond = text[7:].strip()
        if not _IDENT_RE.fullmatch(cond):
            raise SystemExit(f"unexpected #ifdef condition {cond!r}")
        return ("ifdef", cond)
    if text.startswith("#ifndef "):
        cond = text[8:].strip()
        if not _IDENT_RE.fullmatch(cond):
            raise SystemExit(f"unexpected #ifndef condition {cond!r}")
        return ("ifndef", cond)
    if text.startswith("#if "):
        cond = text[4:].strip()
        if not _COND_RE.fullmatch(cond):
            raise SystemExit(f"unexpected #if condition {cond!r}")
        return ("if", cond)
    if text.startswith("#elif"):
        cond = text[5:].strip()
        if not _COND_RE.fullmatch(cond):
            raise SystemExit(f"unexpected #elif condition {cond!r}")
        return ("elif", cond)
    if text.startswith("#else"):
        if text[5:].strip():
            raise SystemExit("unexpected trailing content after #else")
        return ("else", None)
    if text.startswith("#endif"):
        if text[6:].strip():
            raise SystemExit("unexpected trailing content after #endif")
        return ("endif", None)
    raise SystemExit(
        f"unknown preprocessor directive {directive_text.strip()!r}")


class _PreprocessorFrame:
    """One #if/#ifdef/#ifndef frame: condition, branch state and
    #else/#elif bookkeeping (R2-CODE2-002 pattern).

    active is True for the branch whose code the audit treats as live:
    the first branch is active, every later #elif/#else branch is active
    only when no earlier branch of the same frame was. ever_active
    records that, so a three-branch chain `#if A #elif B #elif C` has
    exactly one active branch (A), matching C preprocessor exclusivity
    instead of blindly flipping. saw_else records that the #else branch
    was taken, which makes a later #else (duplicate) or a later #elif
    (after #else) a C constraint violation that must abort.
    """

    __slots__ = ("cond", "active", "ever_active", "saw_else")

    def __init__(self, cond: str):
        self.cond = cond
        self.active = True
        self.ever_active = True
        self.saw_else = False


class _PreprocessorFrames:
    """Preprocessor frame tracker for the command_type enum.

    Validates #if/#ifdef/#ifndef/#elif/#else/#endif pairing and closure
    (every block must open and close inside the enum body), rejects a
    duplicate #else and an #elif after #else, and aborts on unmatched
    #endif.
    """

    def __init__(self, region: str):
        self.region = region
        self.frames: list[_PreprocessorFrame] = []

    def handle(self, directive_text: str) -> None:
        kind, cond = _parse_directive(directive_text)
        if kind in ("if", "ifdef", "ifndef"):
            self.frames.append(_PreprocessorFrame(cond))
        elif kind == "elif":
            if not self.frames:
                raise SystemExit(
                    f"#elif without matching #if in {self.region}")
            frame = self.frames[-1]
            if frame.saw_else:
                raise SystemExit(
                    f"#elif after #else in {self.region}")
            frame.cond = cond
            frame.active = not frame.ever_active
            frame.ever_active = frame.ever_active or frame.active
        elif kind == "else":
            if not self.frames:
                raise SystemExit(
                    f"#else without matching #if in {self.region}")
            frame = self.frames[-1]
            if frame.saw_else:
                raise SystemExit(
                    f"duplicate #else in {self.region}")
            frame.active = not frame.ever_active
            frame.ever_active = frame.ever_active or frame.active
            frame.saw_else = True
        else:  # endif
            if not self.frames:
                raise SystemExit(
                    f"unmatched #endif in {self.region}")
            self.frames.pop()

    def require_closed(self) -> None:
        if self.frames:
            raise SystemExit(
                f"unclosed #if block in {self.region}: "
                f"{[frame.cond for frame in self.frames]!r}")


# ---------------------------------------------------------------------------
# command_type enum parser (strict, fail-closed)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CommandEnum:
    """Parsed command_type declarations and their C++ integer values."""

    members: tuple[str, ...]
    values: dict[str, int]


def parse_command_enum(text: str) -> CommandEnum:
    """Return the command_type enum members and values.

    `text` is the file content supplied by the caller (read from the
    baseline Git blob, never from the worktree).

    Strict grammar: every non-comment line inside the enum body is
    either a preprocessor directive (balanced and closed) or a
    comma-separated list of CMD_[A-Z0-9_]+ members, optionally with
    `= <integer>` / `= CMD_X` aliases. Duplicate members, unknown
    tokens, an alias to an undeclared member, a missing trailing comma on
    any member line except the last, an unbalanced brace and an unclosed
    directive block abort the run. Values follow C++ enum semantics:
    explicit integers are used directly, named initializers copy the
    already-declared target's value, and uninitialized members increment
    the preceding value. The first member must be CMD_NO_CMD and the last
    CMD_MAX_CMD (the "Must always be last" enum sentinel).
    """
    m = re.search(r"enum\s+command_type\s*\{", text)
    if not m:
        raise SystemExit(
            "cannot find enum command_type in command-type.h blob")
    open_idx = text.find("{", m.start())
    close_idx = _matching_brace(text, open_idx)
    body = text[open_idx + 1:close_idx]

    frames = _PreprocessorFrames("command_type enum (command-type.h)")
    members: list[str] = []
    values: dict[str, int] = {}
    seen: set[str] = set()
    member_lines: list[tuple[str, int, bool]] = []
    # File-absolute line number of the enum body's first line (the body
    # text starts after the enum's opening brace).
    body_start_line = text[:open_idx + 1].count("\n") + 1
    for i, raw in enumerate(body.splitlines()):
        lineno = body_start_line + i
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        if line.startswith("#"):
            frames.handle(line)
            continue
        comma_less = not line.endswith(",")
        for part in line.split(","):
            part = part.strip()
            if not part:
                continue
            mm = _ENUM_MEMBER_RE.fullmatch(part)
            if not mm:
                raise SystemExit(
                    f"unexpected token {part!r} in command_type enum "
                    f"(command-type.h blob, line {lineno})")
            tok = mm.group(1)
            if tok in seen:
                raise SystemExit(
                    f"duplicate member {tok} in command_type enum "
                    f"(command-type.h blob)")
            seen.add(tok)
            members.append(tok)
            initializer = mm.group(2)
            if initializer is None:
                value = values[members[-2]] + 1 if len(members) > 1 else 0
            elif initializer.isdigit():
                value = int(initializer)
            else:
                if initializer not in values:
                    raise SystemExit(
                        f"enum member {tok} aliases undeclared member "
                        f"{initializer} (command-type.h blob, line "
                        f"{lineno})")
                value = values[initializer]
            values[tok] = value
            member_lines.append((tok, lineno, comma_less))
    frames.require_closed()

    # A member-bearing line may omit the trailing comma only when it is
    # the LAST member-bearing line of the enum (CMD_MAX_CMD in the
    # baseline); anything earlier is a grammar violation that a missing
    # comma between members would also produce.
    for tok, lineno, comma_less in member_lines[:-1]:
        if comma_less:
            raise SystemExit(
                f"command_type enum member line {lineno} does not end "
                f"with ',' (command-type.h blob)")
    if not members:
        raise SystemExit("command_type enum has no members")
    if members[0] != FIRST_MEMBER:
        raise SystemExit(
            f"command_type enum must start with {FIRST_MEMBER} "
            f"(got {members[0]!r})")
    if members[-1] != LAST_MEMBER:
        raise SystemExit(
            f"command_type enum must end with the sentinel {LAST_MEMBER} "
            f"(got {members[-1]!r})")
    if NAME_TABLE_STOP not in members:
        raise SystemExit(
            f"command_type enum must contain {NAME_TABLE_STOP} "
            f"(the util/cmd-name.pl name-table stop marker)")
    return CommandEnum(tuple(members), values)


def generate_name_table(command_enum: CommandEnum) -> dict[str, str]:
    """Reproduce the physical rows util/cmd-name.pl emits.

    cmd-name.pl's first loop consumes the CMD_NO_CMD anchor without
    emitting it. Every later member up to the first CMD_DISABLE_MORE
    (exclusive, the generator's `last if ...` stop) maps to its own
    identifier string, skipping CMD_MIN_*/CMD_MAX_* aliases (which are
    not physical commands). Its final `{CMD_NO_CMD, nullptr}` line is
    only the generated-array sentinel: macro.cc stops before it, so
    neither map contains CMD_NO_CMD. This return value is keyed by the
    physical identifier solely to preserve and expose generator parity;
    `generate_value_name_table()` separately models the production
    `_cmds_to_names` insertion keyed by integer enum value.

    Invariants (fail-closed): every name fullmatches CMD_[A-Z0-9_]+; the
    table has no duplicate names; every mapped member has exactly one
    name; every mapped name resolves back to its own member.
    """
    members = command_enum.members
    if not members or members[0] != FIRST_MEMBER:
        raise SystemExit(
            f"name-table input must start with {FIRST_MEMBER}")
    table: dict[str, str] = {}
    for member in members[1:]:
        if member == NAME_TABLE_STOP:
            break
        if member.startswith("CMD_MIN_") or member.startswith("CMD_MAX_"):
            continue
        table[member] = member
    for name in table.values():
        if not re.fullmatch(r"CMD_[A-Z0-9_]+", name):
            raise SystemExit(
                f"generated command name {name!r} violates the "
                f"CMD_[A-Z0-9_]+ shape")
    if len(set(table.values())) != len(table):
        raise SystemExit(
            "generated name table contains a duplicate name")
    for member, name in table.items():
        if table.get(name) != member:
            raise SystemExit(
                f"name table back-reference broken for {member!r} -> "
                f"{name!r}")
    return table


def generate_value_name_table(command_enum: CommandEnum,
                              name_table: dict[str, str]) -> dict[int, str]:
    """Model production `_cmds_to_names` (integer enum value -> name).

    `init_keybindings()` inserts only the physical cmd-name.h rows, but
    indexes `_cmds_to_names` by `data.cmd`. Consequently a non-emitted
    alias identifier can resolve through a physically emitted member
    with the same integer value. Two physical names for one value would
    trip production's `_cmds_to_names` uniqueness ASSERT and therefore
    fail closed here too.
    """
    table: dict[int, str] = {}
    for member, name in name_table.items():
        value = command_enum.values[member]
        if value in table:
            raise SystemExit(
                f"physical command names {table[value]!r} and {name!r} "
                f"share enum value {value}")
        table[value] = name
    return table


# ---------------------------------------------------------------------------
# macro.cc name-map machinery verification (strict, fail-closed)
# ---------------------------------------------------------------------------

#: The exact macro.cc regions the audit relies on: the generated-name
#: table include, the two map declarations, and the exact bodies of
#: name_to_command()/command_to_name() with their CMD_NO_CMD fallbacks.
#: A structural change to any of them aborts the run.
_MACRO_TABLE_RE = re.compile(
    r"static\s+command_name\s+_command_name_list\[\]\s*=\s*\{\s*"
    r"#include\s+\"cmd-name\.h\"\s*\};")
_MACRO_MAPS_RE = re.compile(
    r"static\s+name_to_cmd_map\s+_names_to_cmds\s*;\s*"
    r"static\s+cmd_to_name_map\s+_cmds_to_names\s*;")
_MACRO_NAME_TO_COMMAND_RE = re.compile(
    r"\bcommand_type\s+name_to_command\s*\(\s*string\s+name\s*\)\s*\{\s*"
    r"return\s+static_cast\s*<\s*command_type\s*>\s*\(\s*lookup\s*\(\s*"
    r"_names_to_cmds\s*,\s*name\s*,\s*CMD_NO_CMD\s*\)\s*\)\s*;\s*\}")
_MACRO_COMMAND_TO_NAME_RE = re.compile(
    r"\bstring\s+command_to_name\s*\(\s*command_type\s+cmd\s*\)\s*\{\s*"
    r"return\s+lookup\s*\(\s*_cmds_to_names\s*,\s*cmd\s*,\s*"
    r"\"CMD_NO_CMD\"\s*\)\s*;\s*\}")


def verify_macro_cc(text: str) -> None:
    """Verify the macro.cc regions that consume the generated name table.

    `text` is the file content supplied by the caller (read from the
    baseline Git blob, never from the worktree). Each region must occur
    exactly once and match its canonical form exactly (the command_name
    list initializer with the `#include "cmd-name.h"` line, the two map
    declarations, and the exact bodies of name_to_command() /
    command_to_name() with the CMD_NO_CMD fallback). Missing, duplicated
    or mutated regions abort the run, so a change to the name-map
    machinery can never silently change what the inventory models.
    """
    checks = [
        ("_command_name_list[] with #include \"cmd-name.h\"",
         _MACRO_TABLE_RE),
        ("_names_to_cmds / _cmds_to_names declarations", _MACRO_MAPS_RE),
        ("name_to_command() body with CMD_NO_CMD fallback",
         _MACRO_NAME_TO_COMMAND_RE),
        ("command_to_name() body with \"CMD_NO_CMD\" fallback",
         _MACRO_COMMAND_TO_NAME_RE),
    ]
    for label, pattern in checks:
        hits = pattern.findall(text)
        if len(hits) != 1:
            raise SystemExit(
                f"macro.cc must contain exactly one {label} "
                f"(found {len(hits)})")


# ---------------------------------------------------------------------------
# Production DescriptionDB parse (R2-CODE4-001 pattern)
# ---------------------------------------------------------------------------

@dataclass
class DescEntry:
    """One TextDB (description) entry with production parse semantics.

    raw_key: the physical key line after the production key trim
        (trim_string: " \\t\\n\\r" both ends); NOT lowercased -- the
        canonical form is lowercase_string(raw_key), exactly the key
        database.cc `_parse_text_db` stores (trim_string + lowercase).
    value: the value exactly as database.cc stores it: every value line
        right-trimmed per C++ rules (trim_string_right, " \\t\\n\\r" only,
        blank lines stay blank) and appended with '\\n', then at flush
        only leading newlines trimmed (_trim_leading_newlines). Internal
        blank lines and the loader's trailing-newline artifact are
        therefore preserved.
    key_line: 1-indexed line of the physical key line (the first line
        whose C++-trimmed form is non-empty).
    source_file: basename of the input file this entry came from.
    """
    raw_key: str
    value: str
    key_line: int
    source_file: str


def parse_db_keys(text: str, source_file: str) -> list[DescEntry]:
    """Parse a TextDB file exactly like database.cc `_parse_text_db`
    (trim_keys=true, the description DB path: `_store_text_db(...,
    !is_source)` with UTF8FileLineInput).

    The state machine mirrors the C++ line by line:
      - lines are split on '\\n' only (UTF8FileLineInput::get_line reads
        with fgets and erases one trailing '\\n'); a trailing "\\r" stays
        on the line and is removed by the C++-rule trims. The final
        empty element of a '\\n'-terminated file is the phantom empty
        read LineInput performs before reporting EOF and IS processed
        (e.g. as one extra blank value line); a file not ending in '\\n'
        has no such element. Python splitlines() is NOT used: it splits
        on many more separators than production.
      - comment lines (first char '#') are skipped everywhere, before
        and after the first separator, and inside values;
      - '%%%%' block separators (starts-with match) flush the current
        entry and only then start entry mode;
      - content before the first '%%%%' (a file header, a prelude, a
        bare line) NEVER becomes an entry: `in_entry` stays false;
      - the key is the first line whose C++-trimmed form (trim_string,
        " \\t\\n\\r" both ends) is non-empty; blank and whitespace-only
        lines keep the key position open, exactly like the C++
        key.empty() state;
      - every other line is a value line: C++ right-trim only
        (trim_string_right, " \\t\\n\\r"), blank lines stay blank, and
        each line is appended with '\\n';
      - at flush (next '%%%%' or EOF) only leading newlines are trimmed
        (trim_leading_newlines, C++ _trim_leading_newlines), so internal
        blank lines and the loader's trailing-newline artifact are
        preserved exactly as stored in the DB.

    The canonical key is lowercase_string(raw_key) (production applies
    lowercase() after the key trim); callers must use that canonical key
    space, not Python str.lower().

    `text` is the file content supplied by the caller (read from the
    baseline Git blob, never from the worktree); `source_file` is the
    input-file basename recorded on every returned entry.
    """
    entries: list[DescEntry] = []
    key: str | None = None
    key_line = 0
    value_lines: list[str] = []
    in_entry = False
    for lineno, line in enumerate(text.split("\n"), start=1):
        if line and line[0] == '#':
            continue
        if line.startswith("%%%%"):
            if key is not None:
                entries.append(DescEntry(
                    raw_key=key,
                    value=trim_leading_newlines("".join(
                        v + "\n" for v in value_lines)),
                    key_line=key_line, source_file=source_file))
            key = None
            value_lines = []
            in_entry = True
            continue
        if not in_entry:
            continue
        if key is None:
            trimmed = trim_string(line)
            if trimmed:
                key = trimmed
                key_line = lineno
        else:
            value_lines.append(trim_string_right(line))
    if key is not None:
        entries.append(DescEntry(
            raw_key=key,
            value=trim_leading_newlines("".join(
                v + "\n" for v in value_lines)),
            key_line=key_line, source_file=source_file))
    return entries


def merge_desc_sequence(
        entries: list[DescEntry]
) -> tuple[dict[str, DescEntry], list[dict[str, object]]]:
    """Merge a DescriptionDB input sequence with production DBM_REPLACE
    last-wins semantics.

    `entries` is the concatenation of every file's entries in production
    load order. Production stores keys lowercased with the C++
    lowercase_string() rules (database.cc `_parse_text_db` applies
    lowercase() after the key trim), so the effective key space is
    lowercase_string(raw_key); a later definition (within or across
    files) overrides an earlier one exactly like dbm_store(DBM_REPLACE).
    Returns (effective: canonical key -> winning entry, override facts),
    where every override fact records the winner and the full superseded
    chain in load order.
    """
    effective: dict[str, DescEntry] = {}
    overrides: list[dict[str, object]] = []
    for entry in entries:
        canon = lowercase_string(entry.raw_key)
        prev = effective.get(canon)
        if prev is not None:
            rec = next((r for r in overrides
                        if r["canonical_key"] == canon), None)
            fact = {"file": prev.source_file, "raw_key": prev.raw_key,
                    "key_line": prev.key_line}
            if rec is None:
                overrides.append({
                    "canonical_key": canon,
                    "winner": {"file": entry.source_file,
                                "raw_key": entry.raw_key,
                                "key_line": entry.key_line},
                    "superseded": [fact],
                })
            else:
                rec["superseded"].append(fact)  # type: ignore[union-attr]
                rec["winner"] = {"file": entry.source_file,
                                  "raw_key": entry.raw_key,
                                  "key_line": entry.key_line}
        effective[canon] = entry
    return effective, overrides


def _desc_display(value: str) -> str:
    """The string production actually displays for a non-empty
    description entry: `get_command_description()` returns
    `result.substr(0, result.length() - 1)`, which strips exactly the
    loader's trailing '\\n' artifact."""
    return value[:-1] if value else value


# ---------------------------------------------------------------------------
# SourceDB key space (production trim_keys=false semantics)
# ---------------------------------------------------------------------------

def parse_source_keys(text: str, source_file: str
                      ) -> tuple[list[object], dict[str, object]]:
    """Parse the localized SourceDB source.txt key space with production
    semantics.

    Mirrors card_inventory.py's SourceDB parse via
    i18n_shared.parse_entries_physical(): physical key lines are
    preserved verbatim (trim_keys=false: whitespace belongs to the key,
    no \\# decode, no unescape), the canonical key is
    lowercase_string(raw_key), and a duplicate canonical key within the
    file is a fail-closed error (production DBM_REPLACE would silently
    let the last definition win; for audit purposes that must never pass
    silently).

    Returns (entries, by_canonical). `text` is the file content
    supplied by the caller (read from the baseline Git blob, never from
    the worktree).
    """
    payload = text.encode("utf-8")
    source = AuditInput(
        audit_commit=None,
        logical_path=f"dat/i18n/zh/{source_file}",
        relative_path=f"dat/i18n/zh/{source_file}",
        bytes=payload,
        text=text,
        sha256=hashlib.sha256(payload).hexdigest(),
    )
    entries: list[object] = []
    by_canonical: dict[str, object] = {}
    for pe in parse_entries_physical(source):
        prev = by_canonical.get(pe.canonical_key)
        if prev is not None:
            raise SystemExit(
                f"{source_file} canonical key collision: "
                f"{pe.canonical_key!r} defined by both "
                f"{prev.raw_key!r} (line {prev.key_line}) and "
                f"{pe.raw_key!r} (line {pe.key_line})")
        by_canonical[pe.canonical_key] = pe
        entries.append(pe)
    return entries, by_canonical


# ---------------------------------------------------------------------------
# Fail-closed output writer (R2-CODE2-003 pattern, reused verbatim)
# ---------------------------------------------------------------------------

def _canonical_temp_root() -> str:
    """Canonical non-renamable temp root: realpath(/tmp), verified
    root-owned with the sticky bit.

    A root that an unprivileged process can rename (the OS user temp
    dir, e.g. /var/folders/... on macOS, is user-owned 0700) makes the
    write race real: POSIX allows renaming an already-open directory,
    so a concurrent rename can relocate openat(dir_fd) writes out of
    the trusted root. /tmp is owned by uid 0 and carries the sticky
    bit, so no ordinary user can rename or replace it while its
    descriptor is open; the opened root fd is therefore pinned for the
    whole write. Any other root -- including the renamable OS temp dir
    -- is rejected up front (fail-closed); there is no renamable-root
    option at all.
    """
    tmp = os.path.realpath("/tmp")
    try:
        st = os.stat(tmp)
    except OSError as exc:
        print(
            f"error: cannot stat the canonical temp root {tmp!r}: {exc}",
            file=sys.stderr)
        raise SystemExit(1)
    if st.st_uid != 0 or not (st.st_mode & stat.S_ISVTX):
        print(
            f"error: canonical temp root {tmp!r} is not a root-owned "
            f"sticky directory (uid={st.st_uid}, "
            f"mode={oct(st.st_mode)}); refusing to write: only the "
            f"non-renamable /tmp root is permitted",
            file=sys.stderr)
        raise SystemExit(1)
    return tmp


def write_inventory_output(raw: str, content: str) -> Path:
    """Fail-closed write of the inventory JSON: a single brand-new
    basename directly under the canonical non-renamable temp root.

    The output path must be absolute and must be exactly one path
    component below /tmp (or its canonical realpath form, e.g.
    /private/tmp on macOS): nested components, `.` and `..` components,
    relative paths, the root itself, and any path that realpath-resolves
    outside the root are rejected outright. Only the non-renamable /tmp
    root (root-owned, sticky) is accepted, so there is no parent chain
    and no open-root rename that could relocate the write; if /tmp
    itself were ever not root-owned sticky, the run fails closed instead
    of falling back to a renamable root.

    The trusted root is opened once with O_RDONLY|O_DIRECTORY|O_NOFOLLOW
    on its canonical realpath (never through a symlink) and the final
    element is created with os.open(base, O_WRONLY|O_CREAT|O_EXCL|
    O_NOFOLLOW, dir_fd=root_fd).

    * The target must not already exist (O_EXCL rejects an existing file
      -- including a hardlink to a shared inode -- with EEXIST, so the
      output is never truncated or overwritten).
    * An existing symlink at the target fails with ELOOP (or EEXIST) and
      the output is never written through it; a symlinked target that
      resolves outside the root also fails the realpath containment
      check.
    * Directories are never auto-created and no component is followed as
      a symlink.

    Callers must therefore pick a fresh basename for every rebuild, or
    delete the old file first. There is no lstat-then-create TOCTOU
    window: every step is a single atomic open that refuses to follow
    symlinks. Any failure prints a clear error to stderr and exits 1;
    there is no fallback to a plain open/write.
    """
    p = Path(raw)
    if not p.is_absolute():
        print(
            f"error: --inventory-output must be an absolute path directly "
            f"under /tmp; got {raw!r} (relative path rejected)",
            file=sys.stderr)
        raise SystemExit(1)
    root = _canonical_temp_root()

    # Analyze the raw spelling, not a normalized form: '.' and '..'
    # components must be rejected even when they are lexically neutral.
    components = [part for part in raw.split(os.sep) if part]
    if any(part in (".", "..") for part in components):
        print(
            f"error: --inventory-output must not contain '.' or '..' "
            f"path components; got {raw!r}",
            file=sys.stderr)
        raise SystemExit(1)

    # Locate the raw prefix (e.g. /tmp, or the canonical /private/tmp)
    # whose realpath is the trusted root. Exactly one component may
    # follow that prefix: the brand-new basename. Nested components are
    # rejected (there is no parent chain to walk, so a concurrent rename
    # of an opened parent can never relocate the final write out of the
    # trusted root).
    prefix_end = None
    for i in range(1, len(components) + 1):
        if os.path.realpath(os.sep + os.sep.join(components[:i])) == root:
            prefix_end = i
            break
    if prefix_end is None:
        print(
            f"error: --inventory-output must be a single brand-new "
            f"basename directly under the canonical non-renamable temp "
            f"root {root!r}; {raw!r} is not under it (renamable roots "
            f"such as the OS user temp dir are rejected)",
            file=sys.stderr)
        raise SystemExit(1)
    raw_prefix = os.sep + os.sep.join(components[:prefix_end])
    canonical = os.sep + os.sep.join(root.split(os.sep)[1:])
    if raw_prefix not in ("/tmp", canonical):
        print(
            f"error: --inventory-output prefix {raw_prefix!r} is not "
            f"/tmp or its canonical form {canonical!r}; refusing to "
            f"write",
            file=sys.stderr)
        raise SystemExit(1)
    if len(components) == prefix_end:
        print(
            f"error: --inventory-output {raw!r} resolves to the temp root "
            f"itself; refusing to write to it",
            file=sys.stderr)
        raise SystemExit(1)
    remaining = components[prefix_end:]
    if len(remaining) != 1:
        print(
            f"error: --inventory-output must be a single brand-new "
            f"basename directly under the temp root {root!r}; nested "
            f"components are rejected ({raw!r} has {len(remaining)} "
            f"component(s) below the root)",
            file=sys.stderr)
        raise SystemExit(1)
    basename = remaining[0]
    if basename in (".", ".."):
        print(
            f"error: --inventory-output basename must not be '.' or '..'; "
            f"got {basename!r}",
            file=sys.stderr)
        raise SystemExit(1)

    # A symlink anywhere in the path would resolve outside the root.
    resolved = os.path.realpath(str(p))
    if not (resolved == root or resolved.startswith(root + os.sep)):
        print(
            f"error: --inventory-output {raw!r} resolves to {resolved}, "
            f"outside the canonical temp root {root!r}; symlinked "
            f"targets are rejected",
            file=sys.stderr)
        raise SystemExit(1)

    try:
        root_fd = os.open(
            root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    except OSError as exc:
        print(
            f"error: cannot open temp root {root!r}: {exc}",
            file=sys.stderr)
        raise SystemExit(1)
    try:
        try:
            final_fd = os.open(
                basename,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o644,
                dir_fd=root_fd)
        except OSError as exc:
            if exc.errno == errno.EEXIST:
                print(
                    f"error: --inventory-output target {raw!r} already "
                    f"exists; refusing to overwrite it (output path must be "
                    f"a brand-new file -- pick a fresh filename or delete "
                    f"the old file first)",
                    file=sys.stderr)
            else:
                print(
                    f"error: --inventory-output target {basename!r} of "
                    f"{raw!r} cannot be created or opened for writing "
                    f"without following a symlink: {exc}",
                    file=sys.stderr)
            raise SystemExit(1)
        try:
            fh = os.fdopen(final_fd, "w", encoding="utf-8")
        except OSError as exc:
            try:
                os.close(final_fd)
            except OSError:
                pass
            print(
                f"error: cannot open inventory for writing at {raw!r}: "
                f"{exc}",
                file=sys.stderr)
            raise SystemExit(1)
        try:
            with fh:
                fh.write(content)
        except OSError as exc:
            print(
                f"error: failed to write inventory to {raw!r}: {exc}",
                file=sys.stderr)
            raise SystemExit(1)
    finally:
        os.close(root_fd)
    return p


# ---------------------------------------------------------------------------
# Inventory construction
# ---------------------------------------------------------------------------

def split_cmd_keys(entries: list[DescEntry],
                   effective: dict[str, DescEntry]
                   ) -> tuple[set[str], set[str], list[str]]:
    """(terse, verbose, duplicate_physical) over the audited CMD_* key
    subspace of one description database.

    Only canonical keys in the command space (cmd_* and
    `cmd_* verbose`) are audited; unrelated keys (the files' android
    command menu|* entries) are out of scope. A malformed CMD_-shaped
    canonical key aborts the run (fail-closed name-shape rule).
    duplicate_physical lists physical raw keys that occur more than
    once among the parsed entries (the DBM_REPLACE override facts carry
    the details; the effective map alone cannot show them because it
    keeps only the winning definition).
    """
    terse: set[str] = set()
    verbose: set[str] = set()
    seen_raw: dict[str, int] = {}
    for entry in entries:
        seen_raw[entry.raw_key] = seen_raw.get(entry.raw_key, 0) + 1
    duplicates = sorted(raw for raw, n in seen_raw.items()
                        if n > 1 and raw.startswith("CMD_"))
    for canon in effective:
        if not canon.startswith("cmd_"):
            continue
        if not _CMD_CANON_RE.fullmatch(canon):
            raise SystemExit(
                f"malformed command description key {canon!r} (expected "
                f"cmd_[a-z0-9_]+ or cmd_[a-z0-9_]+ verbose)")
        if canon.endswith(" verbose"):
            verbose.add(canon)
        else:
            terse.add(canon)
    return terse, verbose, duplicates


def build_inventory(command_enum: CommandEnum,
                    name_table: dict[str, str],
                    en_effective: dict[str, DescEntry],
                    zh_effective: dict[str, DescEntry]
                    ) -> list[dict[str, object]]:
    """One inventory record per enum member (declaration order).

    identity: `command:<CMD_X>` for every raw enum member identifier.
    name_in_map records whether cmd-name.pl physically emitted that
    identifier; lookup_name independently records the name resolved from
    its integer enum value, or the production CMD_NO_CMD fallback.
    lifecycle: `current` when the member has at least one commands.txt
    key in either language (union of the EN/ZH key spaces), `unused`
    otherwise (no commands.txt key -- the member is never described).
    terse_en/terse_zh/verbose_en/verbose_zh are the effective production
    description values or null; *_display_* model the full
    get_command_description() chain (verbose -> terse(+ ".") ->
    command_to_name() key-name fallback); missing_t lists the ZH keys
    absent while the EN counterpart exists (the translation gap facts).
    """
    value_name_table = generate_value_name_table(command_enum, name_table)
    inventory: list[dict[str, object]] = []
    for member in command_enum.members:
        physical_name = name_table.get(member)
        name = value_name_table.get(command_enum.values[member])
        lookup_name = name if name is not None else "CMD_NO_CMD"
        terse_canon = lowercase_string(name) if name else None
        verbose_canon = lowercase_string(f"{name} verbose") if name else None
        terse_en = (en_effective[terse_canon].value
                    if name and terse_canon in en_effective else None)
        terse_zh = (zh_effective[terse_canon].value
                    if name and terse_canon in zh_effective else None)
        verbose_en = (en_effective[verbose_canon].value
                      if name and verbose_canon in en_effective else None)
        verbose_zh = (zh_effective[verbose_canon].value
                      if name and verbose_canon in zh_effective else None)

        has_key = bool(name and (
            terse_canon in en_effective or terse_canon in zh_effective
            or verbose_canon in en_effective
            or verbose_canon in zh_effective))
        lifecycle = "current" if has_key else "unused"

        terse_display_en = (_desc_display(terse_en)
                            if terse_en is not None else lookup_name)
        terse_display_zh = (_desc_display(terse_zh)
                            if terse_zh is not None else lookup_name)
        if verbose_en is not None:
            verbose_display_en = _desc_display(verbose_en)
        elif terse_en is not None:
            verbose_display_en = terse_display_en + "."
        else:
            verbose_display_en = lookup_name
        if verbose_zh is not None:
            verbose_display_zh = _desc_display(verbose_zh)
        elif terse_zh is not None:
            verbose_display_zh = terse_display_zh + "."
        else:
            verbose_display_zh = lookup_name

        missing_t: list[str] = []
        if name is not None:
            if terse_en is not None and terse_zh is None:
                missing_t.append("terse_zh")
            if verbose_en is not None and verbose_zh is None:
                missing_t.append("verbose_zh")

        inventory.append({
            "identity": f"command:{member}",
            "member": member,
            "name_in_map": physical_name is not None,
            "lookup_name": lookup_name,
            "lifecycle": lifecycle,
            "terse_en": terse_en,
            "terse_zh": terse_zh,
            "verbose_en": verbose_en,
            "verbose_zh": verbose_zh,
            "terse_display_en": terse_display_en,
            "terse_display_zh": terse_display_zh,
            "verbose_display_en": verbose_display_en,
            "verbose_display_zh": verbose_display_zh,
            "missing_t": missing_t,
        })
    return inventory


# ---------------------------------------------------------------------------
# Strict review-ledger coverage (identity-bound canonical JSONL)
# ---------------------------------------------------------------------------

def fact_sha256(row: dict[str, object]) -> str:
    """Digest one complete inventory row in canonical JSON form."""
    encoded = json.dumps(
        row,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def mechanical_card_fields(row: dict[str, object]) -> dict[str, object]:
    """Rebuild every evidence-card field derived from production facts."""
    return {
        "current_chinese": {
            field: row[field]
            for field in (
                "terse_zh",
                "verbose_zh",
                "terse_display_zh",
                "verbose_display_zh",
            )
        },
        "current_english": {
            field: row[field]
            for field in (
                "terse_en",
                "verbose_en",
                "terse_display_en",
                "verbose_display_en",
            )
        },
        "fact_sha256": fact_sha256(row),
        "identity": row["identity"],
        "lifecycle": row["lifecycle"],
        "lookup_name": row["lookup_name"],
        "missing_t": row["missing_t"],
        "name_in_map": row["name_in_map"],
        "production_facts": row,
    }


def _load_strict_json(line: str, label: str) -> object:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON value {value}")

    try:
        return json.loads(line, parse_constant=reject_constant)
    except (json.JSONDecodeError, ValueError) as error:
        raise RuntimeError(f"invalid {label} JSON") from error


def parse_strict_review_evidence(review_input: AuditInput
                                 ) -> tuple[dict[str, object],
                                            list[dict[str, object]]]:
    """Parse the document's one marker-bound canonical JSONL card block."""
    text = review_input.text
    if (text.count(STRICT_REVIEW_BEGIN) != 1
            or text.count(STRICT_REVIEW_END) != 1):
        raise RuntimeError(
            "strict review evidence block is missing or duplicated")
    before, remainder = text.split(STRICT_REVIEW_BEGIN, 1)
    block_text, after = remainder.split(STRICT_REVIEW_END, 1)
    del before, after
    if not block_text.startswith("\n") or not block_text.endswith("\n"):
        raise RuntimeError("strict review evidence block framing is invalid")
    lines = block_text[1:-1].splitlines()
    if len(lines) < 4 or lines[1] != "```jsonl" or lines[-1] != "```":
        raise RuntimeError("strict review evidence block structure is invalid")

    metadata = _load_strict_json(lines[0], "strict review metadata")
    metadata_fields = {
        "baseline", "glossary_sha256", "identity_count", "inventory_sha256",
    }
    if not isinstance(metadata, dict) or set(metadata) != metadata_fields:
        raise RuntimeError("strict review metadata fields are invalid")
    if lines[0] != json.dumps(
        metadata, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ):
        raise RuntimeError("strict review metadata is not canonical JSON")
    if (not isinstance(metadata["baseline"], str)
            or not re.fullmatch(r"[0-9a-f]{40}", metadata["baseline"])
            or not isinstance(metadata["glossary_sha256"], str)
            or not re.fullmatch(
                r"[0-9a-f]{64}", metadata["glossary_sha256"])
            or not isinstance(metadata["inventory_sha256"], str)
            or not re.fullmatch(
                r"[0-9a-f]{64}", metadata["inventory_sha256"])
            or isinstance(metadata["identity_count"], bool)
            or not isinstance(metadata["identity_count"], int)
            or metadata["identity_count"] < 0):
        raise RuntimeError("strict review metadata values are invalid")

    cards: list[dict[str, object]] = []
    for line_number, line in enumerate(lines[2:-1], start=3):
        card = _load_strict_json(
            line, f"strict review evidence card at block line {line_number}")
        if not isinstance(card, dict) or set(card) != STRICT_CARD_FIELDS:
            raise RuntimeError("strict review evidence-card fields are invalid")
        if line != json.dumps(
            card, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ):
            raise RuntimeError(
                "strict review evidence card is not canonical JSON")
        if not isinstance(card["identity"], str) or not card["identity"]:
            raise RuntimeError("strict review evidence-card identity is invalid")
        cards.append(card)
    return metadata, cards


def _nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _vague_deferral_value(value: object) -> bool:
    return (
        isinstance(value, str)
        and value.strip().lower().strip(".。;；") in _VAGUE_DEFERRAL_VALUES
    )


def review_coverage(payload: dict[str, object], review_input: AuditInput
                    ) -> dict[str, object]:
    """Prove metadata, identity, fact, decision, and evidence invariants."""
    metadata, cards = parse_strict_review_evidence(review_input)
    inventory = payload["inventory"]
    if not isinstance(inventory, list):
        raise RuntimeError("inventory rows are unavailable for review binding")
    inventory_ids = [row["identity"] for row in inventory]
    review_ids = [card["identity"] for card in cards]
    conclusion_counts = dict(sorted(Counter(
        card["terminal_conclusion"] for card in cards
        if isinstance(card["terminal_conclusion"], str)
    ).items()))
    inventory_set = set(inventory_ids)
    review_set = set(review_ids)
    inventory_duplicates = sorted(
        identity for identity, count in Counter(inventory_ids).items()
        if count > 1
    )
    review_duplicates = sorted(
        identity for identity, count in Counter(review_ids).items()
        if count > 1
    )
    expected_by_id = {row["identity"]: row for row in inventory}

    mismatched_mechanical_fields = sorted(
        f"{card['identity']}:{field}"
        for card in cards
        if card["identity"] in expected_by_id
        for field, expected in mechanical_card_fields(
            expected_by_id[card["identity"]]
        ).items()
        if card[field] != expected
    )
    invalid_terminal = sorted(
        card["identity"] for card in cards
        if (not isinstance(card["terminal_conclusion"], str)
            or card["terminal_conclusion"] not in TERMINAL_CONCLUSIONS)
    )
    empty_rationales = sorted(
        card["identity"] for card in cards
        if not _nonempty_string(card["reviewer_rationale"])
    )
    invalid_reentry = sorted(
        card["identity"] for card in cards
        if not _nonempty_string(card["reentry_trigger"])
    )
    invalid_deferrals = sorted(
        card["identity"] for card in cards
        if (isinstance(card["terminal_conclusion"], str)
            and card["terminal_conclusion"].startswith("defer ")
            and (
                not _nonempty_string(card["reviewer_rationale"])
                or _vague_deferral_value(card["reviewer_rationale"])
                or not _nonempty_string(card["reentry_trigger"])
                or _vague_deferral_value(card["reentry_trigger"])
            ))
    )
    required_string_fields = (
        "actual_behavior",
        "consumer",
        "dependency_group",
        "display_context",
        "glossary_authority",
        "producer",
    )
    invalid_evidence_fields = sorted(
        f"{card['identity']}:{field}"
        for card in cards
        for field in required_string_fields
        if not _nonempty_string(card[field])
    )
    invalid_evidence_locations = sorted(
        card["identity"] for card in cards
        if (not isinstance(card["evidence_locations"], list)
            or not card["evidence_locations"]
            or any(not _nonempty_string(value)
                   for value in card["evidence_locations"]))
    )
    invalid_confidence = sorted(
        card["identity"] for card in cards
        if (not isinstance(card["confidence"], str)
            or card["confidence"] not in CONFIDENCE_LEVELS)
    )
    invalid_proposed_translation = sorted(
        card["identity"] for card in cards
        if (card["proposed_translation"] is not None
            and not _nonempty_string(card["proposed_translation"]))
    )
    invalid_rejected_alternatives = sorted(
        card["identity"] for card in cards
        if (not isinstance(card["rejected_alternatives"], list)
            or any(not _nonempty_string(value)
                   for value in card["rejected_alternatives"]))
    )
    binding_matches = {
        "baseline": metadata["baseline"] == payload["baseline"],
        "glossary_sha256": (
            metadata["glossary_sha256"] == payload["glossary_sha256"]
        ),
        "identity_count": metadata["identity_count"] == len(inventory),
        "inventory_sha256": (
            metadata["inventory_sha256"] == payload["inventory_sha256"]
        ),
    }
    order_matches = review_ids == inventory_ids
    inventory_minus_review = sorted(inventory_set - review_set)
    review_minus_inventory = sorted(review_set - inventory_set)
    coverage_equal = (
        all(binding_matches.values())
        and len(review_ids) == len(inventory_ids)
        and not inventory_duplicates
        and not review_duplicates
        and not inventory_minus_review
        and not review_minus_inventory
        and order_matches
        and not mismatched_mechanical_fields
        and not invalid_terminal
        and not empty_rationales
        and not invalid_reentry
        and not invalid_deferrals
        and not invalid_evidence_fields
        and not invalid_evidence_locations
        and not invalid_confidence
        and not invalid_proposed_translation
        and not invalid_rejected_alternatives
    )
    return {
        **review_input_metadata(review_input),
        "review_results": review_input.logical_path,
        "review_results_sha256": review_input.sha256,
        "evidence_card_count": len(cards),
        "terminal_conclusion_counts": conclusion_counts,
        "binding_matches": binding_matches,
        "inventory_duplicate_identities": inventory_duplicates,
        "duplicate_evidence_cards": review_duplicates,
        "inventory_minus_review": inventory_minus_review,
        "review_minus_inventory": review_minus_inventory,
        "canonical_card_order": order_matches,
        "mismatched_mechanical_fields": mismatched_mechanical_fields,
        "invalid_terminal_conclusions": invalid_terminal,
        "empty_reviewer_rationales": empty_rationales,
        "invalid_reentry_triggers": invalid_reentry,
        "invalid_deferrals": invalid_deferrals,
        "invalid_evidence_fields": invalid_evidence_fields,
        "invalid_evidence_locations": invalid_evidence_locations,
        "invalid_confidence": invalid_confidence,
        "invalid_proposed_translation": invalid_proposed_translation,
        "invalid_rejected_alternatives": invalid_rejected_alternatives,
        "coverage_equal": coverage_equal,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--inventory-output",
        default="/tmp/command-inventory.json",
        help="output JSON path; must be an absolute path that is exactly "
             "one brand-new basename directly under /tmp (the canonical "
             "root-owned sticky temp root; realpath /private/tmp on "
             "macOS) -- nested components, '.', '..', relative paths, "
             "renamable roots such as the OS user temp dir and every "
             "other location are rejected; the trusted root is opened "
             "once with O_NOFOLLOW and the target is created with "
             "O_EXCL|O_NOFOLLOW, so an existing target, a symlinked "
             "target and every other unsafe form are rejected, "
             "directories are never auto-created, and no parent chain "
             "exists that could be renamed away; every rebuild needs a "
             "fresh filename or a deleted old file")
    ap.add_argument(
        "--baseline-ref",
        default="HEAD",
        help="git commit-ish recorded as the payload 'baseline' (the "
             "review anchor for reproducible rebuilds); resolved with "
             "`git rev-parse <ref>` to a full 40-hex SHA, default HEAD; "
             "all inputs -- command-type.h, macro.cc, the EN/ZH "
             "commands.txt description files, the localized SourceDB "
             "source.txt and the glossary -- are read from this "
             "commit's Git objects via `git show` under the trusted git "
             "environment, so the inventory is independent of local "
             "worktree state and of git replace refs")
    ap.add_argument(
        "--review-results",
        type=Path,
        help="also validate the unique canonical strict evidence-card "
             "block in this review ledger against the rebuilt inventory")
    args = ap.parse_args()
    baseline = resolve_commit(args.baseline_ref)

    input_paths = {
        "command-type.h": COMMAND_TYPE_H,
        "macro.cc": MACRO_CC,
        "commands_en": COMMANDS_EN,
        "commands_zh": COMMANDS_ZH,
        "source.txt": SOURCE_TXT,
    }
    blobs = {k: git_show_blob(baseline, rel)
             for k, rel in input_paths.items()}

    # -- Identity source: the command_type enum (strict). ----------------
    command_enum = parse_command_enum(
        blobs["command-type.h"].decode("utf-8"))
    members = list(command_enum.members)
    name_table = generate_name_table(command_enum)
    unmapped = [m for m in members if m not in name_table]
    if len(members) != len(set(members)):
        raise SystemExit("command_type enum contains a duplicate member")

    # -- Name-map machinery in macro.cc (strict, exact regions). ----------
    verify_macro_cc(blobs["macro.cc"].decode("utf-8"))

    # -- Description DBs with production _parse_text_db semantics. --------
    en_entries = parse_db_keys(blobs["commands_en"].decode("utf-8"),
                               "commands.txt")
    zh_entries = parse_db_keys(blobs["commands_zh"].decode("utf-8"),
                               "commands.txt")
    en_effective, en_overrides = merge_desc_sequence(en_entries)
    zh_effective, zh_overrides = merge_desc_sequence(zh_entries)
    en_terse, en_verbose, en_dups = split_cmd_keys(en_entries,
                                                    en_effective)
    zh_terse, zh_verbose, zh_dups = split_cmd_keys(zh_entries,
                                                   zh_effective)
    en_lines = len([e for e in en_entries if e.raw_key.startswith("CMD_")])
    zh_lines = len([e for e in zh_entries if e.raw_key.startswith("CMD_")])

    # Physical key shape (name shape rule, NO_CMD fallback exempt): every
    # CMD_-prefixed key must be CMD_[A-Z0-9_]+ optionally ` verbose`.
    for label, entries in (("EN", en_entries), ("ZH", zh_entries)):
        for e in entries:
            if e.raw_key.startswith("CMD_") \
                    and not _KEY_NAME_RE.fullmatch(e.raw_key):
                raise SystemExit(
                    f"commands.txt ({label}) key {e.raw_key!r} violates "
                    f"the CMD_[A-Z0-9_]+( verbose)? shape")

    # -- Key -> enum member back-reference (name_to_command semantics). ---
    # name_to_command() looks up the exact generated name; the canonical
    # description keys are the lowercase of those names, so the reverse
    # table is compared in the same lowercase canonical space.
    reverse_canon = {lowercase_string(name): name
                     for name in name_table.values()}
    members_canon = {lowercase_string(m) for m in members}
    unresolved: list[str] = []
    stale: list[str] = []
    for canon in sorted(en_terse | en_verbose | zh_terse | zh_verbose):
        base = (canon[:-len(" verbose")] if canon.endswith(" verbose")
                else canon)
        if base not in reverse_canon:
            unresolved.append(canon)
            if base not in members_canon:
                stale.append(base)

    # -- Bidirectional key differences (terse/verbose separated). --------
    en_only_terse = sorted(en_terse - zh_terse)
    en_only_verbose = sorted(en_verbose - zh_verbose)
    zh_only_terse = sorted(zh_terse - en_terse)
    zh_only_verbose = sorted(zh_verbose - en_verbose)
    # T_ gap: EN keys whose ZH counterpart is missing.
    missing_zh = sorted((en_terse | en_verbose) - (zh_terse | zh_verbose))

    # -- SourceDB key space (fail-closed duplicate canonical keys). ------
    source_entries, source_canonical = parse_source_keys(
        blobs["source.txt"].decode("utf-8"), "source.txt")
    source_cmd_keys = sorted(
        canon for canon in source_canonical
        if re.fullmatch(r"cmd_[a-z0-9_]+", canon))

    # -- Inventory: one record per enum member. --------------------------
    inventory = build_inventory(command_enum, name_table, en_effective,
                                zh_effective)
    if len(inventory) != len(members):
        raise SystemExit(
            f"inventory size {len(inventory)} != enum member count "
            f"{len(members)}")

    payload = {
        "baseline": baseline,
        "glossary_sha256": hashlib.sha256(
            git_show_blob(baseline, GLOSSARY_MD)).hexdigest(),
        "inputs": {
            k: {"path": input_paths[k],
                "sha256": hashlib.sha256(blobs[k]).hexdigest()}
            for k in input_paths
        },
        "enum_members": members,
        "sentinel": LAST_MEMBER,
        "name_map": name_table,
        "unmapped_members": unmapped,
        "commands_en": {
            "key_lines": en_lines,
            "terse": sorted(en_terse),
            "verbose": sorted(en_verbose),
            "duplicate_keys": en_dups,
        },
        "commands_zh": {
            "key_lines": zh_lines,
            "terse": sorted(zh_terse),
            "verbose": sorted(zh_verbose),
            "duplicate_keys": zh_dups,
        },
        "en_only_keys": {"terse": en_only_terse, "verbose": en_only_verbose},
        "zh_only_keys": {"terse": zh_only_terse, "verbose": zh_only_verbose},
        "unresolved_keys": unresolved,
        "stale_keys": stale,
        "missing_zh_keys": missing_zh,
        "commands_en_overrides": en_overrides,
        "commands_zh_overrides": zh_overrides,
        "source_keys": {
            "entries": len(source_entries),
            "cmd_shape_collisions": source_cmd_keys,
        },
        "inventory": inventory,
    }
    digest = hashlib.sha256(json.dumps(
        payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    payload["inventory_sha256"] = digest

    if args.review_results:
        try:
            review_input = load_review_input(ROOT, args.review_results)
            payload["review_input"] = review_input_metadata(review_input)
            payload["review_coverage"] = review_coverage(
                payload, review_input)
        except (OSError, RuntimeError, ValueError) as error:
            print(
                f"ERROR: command review coverage could not be checked: "
                f"{error}",
                file=sys.stderr,
            )
            return 2

    out = write_inventory_output(
        args.inventory_output,
        json.dumps(payload, ensure_ascii=False, indent=1))

    n_current = sum(1 for e in inventory if e["lifecycle"] == "current")
    n_unused = sum(1 for e in inventory if e["lifecycle"] == "unused")
    print(f"command inventory sha256: {digest}")
    print(f"enum members: {len(members)} (current={n_current}, "
          f"unused={n_unused}, sentinel={LAST_MEMBER})")
    print(f"name map: {len(name_table)} entries; unmapped members: "
          f"{len(unmapped)}")
    print(f"commands.txt EN: {en_lines} key lines, "
          f"{len(en_terse) + len(en_verbose)} unique "
          f"(terse={len(en_terse)}, verbose={len(en_verbose)}, "
          f"duplicates={en_dups})")
    print(f"commands.txt ZH: {zh_lines} key lines, "
          f"{len(zh_terse) + len(zh_verbose)} unique "
          f"(terse={len(zh_terse)}, verbose={len(zh_verbose)}, "
          f"duplicates={zh_dups})")
    print(f"en_only keys: terse={en_only_terse} verbose={en_only_verbose}")
    print(f"zh_only keys: terse={zh_only_terse} verbose={zh_only_verbose}")
    print(f"unresolved description keys (name_to_command -> CMD_NO_CMD): "
          f"{unresolved}")
    print(f"stale keys (no enum member): {stale}")
    print(f"missing_zh_keys (EN present, ZH absent): {missing_zh}")
    print(f"commands overrides: EN={en_overrides} ZH={zh_overrides}")
    print(f"source.txt: {len(source_entries)} entries; "
          f"CMD-shaped keys: {source_cmd_keys}")
    print(f"inventory entries: {len(inventory)} (= enum members)")
    if "review_coverage" in payload:
        print("review coverage: " + json.dumps(
            payload["review_coverage"],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ))
    print(f"wrote {out}")
    if ("review_coverage" in payload
            and not payload["review_coverage"]["coverage_equal"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
