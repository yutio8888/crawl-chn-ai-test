#!/usr/bin/env python3
"""Deterministic read-only card inventory for the R2 (Nemelex card names,
descriptions, deck membership, lifecycle) batch review.

Identity source: the card_type enum in crawl-ref/source/decks.h. Every
member is recorded in declaration order together with whether it sits
inside a `#if TAG_MAJOR_VERSION == 34` block, i.e. the removed-card
lifetime marker (CARD_SHAFT_REMOVED / CARD_STAIRS_REMOVED /
CARD_FAMINE_REMOVED); NUM_CARDS is the sentinel.

Name sources: the card_name_en() and card_name() switches in
crawl-ref/source/decks.cc (same case order). Every current member returns
its own string; the three TAG-34 removed members and NUM_CARDS share the
`a buggy card` return, and the function tail returns `a very buggy card`
(the switch fallthrough). card_name() uses T_("...") for every member
except CARD_WILD_MAGIC and CARD_WRATH, which use C_("card name", "...").

Display names are resolved with the PRODUCTION SourceDB semantics of
database.cc (`_parse_text_db` with trim_keys=false for the source
database, plus `i18n_source_lookup`): source.txt keys are lowercased into
a canonical key space, T_("en") queries canonical(en), and C_(ctx, en)
queries canonical(ctx|en) first and falls back to canonical(en); an empty
value is treated as a miss that falls back to English. The physical key
line is preserved verbatim (trim_keys=false: whitespace belongs to the
key; no \\# decode, no unescape), and a duplicate canonical key is a
fail-closed error (production DBM_REPLACE would silently let the last
definition win; for audit purposes that must never pass silently).

Each card record therefore reports the *actual production display value*
(name_zh), whether the exact-case physical key exists (exact_case_key),
whether the canonical lookup hit a key authored under a different
physical key -- a cross-domain collision (canonical_collision, e.g. the
baseline T_("Wrath") resolving to the weapon-inscription key
`wrath` -> 狂怒), whether the C_ context key exists (context_key), and a
human-readable T_/C_ resolution path (resolution).

Long descriptions are looked up by `<name> card` in
dat/descript/cards.txt (EN) and dat/descript/zh/cards.txt (ZH); each file
carries 24 keys (21 current cards, the removed `the Shaft card`, and the
`a buggy card` / `a very buggy card` sentinels; Famine/Stairs have no
description key). The TAG-34 card_name_en() switch cannot produce the
removed members' historical description keys (it returns the shared
`a buggy card` for them), so for removed members the tool derives the
base name from the enum identifier (CARD_SHAFT_REMOVED -> Shaft) and
resolves the key as `the <Base> card` when the EN description database
contains it, falling back to `<Base> card` and finally to the `the <Base>
card` form (which then simply reports desc_en/desc_zh false). This
reproduces the historical `the Shaft card` key mechanically from baseline
blobs only.

Deck membership is parsed from the four deck_archetype tables in
decks.cc (deck_of_escape / deck_of_destruction / deck_of_summoning /
deck_of_punishment), and lifecycle is cross-checked against the
card_is_removed() switch.

All parsers are fail-closed (R2-CODE-002): every region -- the card_type
enum, the card_name_en()/card_name()/card_is_removed() switches, the
fallthrough tail and the deck tables -- has a strict grammar, `#if`/
`#else`/`#endif` preprocessing frames must balance and close inside their
region, case->return forms and boolean literals must be exact, enum
members and cases must be unique, deck-table members must be enum
members, and every enum member must have exactly one lifecycle
(current/removed/sentinel). Any unconsumed non-comment token aborts the
run with exit code 1; a silently skipped syntax change can never pass.

The payload records a `baseline` commit (the review anchor) so the
inventory can be reproduced from any checkout: pass `--baseline-ref
<commit-ish>` to pin it (default: HEAD). All inputs are read from Git
objects at that commit via `git show <ref>:<path>` -- never from the
local worktree -- so the output is identical regardless of local
checkout state or uncommitted edits.

Input discovery mirrors database.cc exactly (R2-CODE3-001). The
localized SourceDB (dat/i18n/zh/) loads every `.txt` direct child of
the directory in sorted (std::sort) order with `source.txt` forced
first (TextDB child constructor, database.cc ~211-241); the localized
DescriptionDB (dat/descript/zh/) uses that directory scan only when
`dat/descript/zh/source.txt` exists (production's check file), and
otherwise inherits the parent's fixed input list (database.cc AllDBs[0]
"descriptions") filtered to the files that exist under the locale
directory. The English description fallback is the parent's fixed list
loaded from dat/descript/ in that exact order. The complete discovered
sequence is bound into the payload manifest (`inputs`, `*_input_sequence`)
together with every per-file SHA-256, so no input file can ever be
silently missing or extra. Each unique blob is read from Git exactly
once. Effective values model production DBM_REPLACE last-wins across
the load sequence: a later file's definition of a canonical key
overrides an earlier one, and every such override is recorded as an
override fact (`source_overrides` / `desc_en_overrides` /
`desc_zh_overrides`) instead of being silently dropped. Within one
file, a duplicate canonical key remains a fail-closed error (an
authoring collision that DBM_REPLACE would otherwise hide).

All git subprocesses (rev-parse, show, ls-tree) run under the shared
trusted git environment (i18n_shared.trusted_git_environment()), which
forces GIT_NO_REPLACE_OBJECTS=1 and strips caller-controlled GIT_* and
shell environment variables (R2-CODE3-003). A `git replace A B` ref
can therefore never substitute another commit's blobs for the exact
baseline OID the inventory claims to read.

The output JSON write is fail-closed (R2-CODE2-003): the output path
must be exactly one brand-new basename directly under the canonical
non-renamable temp root /tmp (root-owned, sticky; on macOS realpath
/private/tmp). Nested components, `.` and `..` components, relative
paths, renamable roots such as the OS user temp dir, and symlink
escapes are rejected; the trusted root is opened once and the target is
created with O_EXCL|O_NOFOLLOW (see write_inventory_output()).

Usage:
  python3 .claude/scripts/card_inventory.py --baseline-ref <commit> \
      --inventory-output /tmp/card-inventory-<new-file>.json

  --inventory-output must be a single brand-new basename directly under
  /tmp (the canonical root-owned sticky temp root; realpath /private/tmp
  on macOS); the target must not already exist.
"""
import argparse
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
from i18n_shared import (AuditInput, lowercase_string,  # noqa: E402
                         parse_entries_physical, runtime_normalize_value,
                         trusted_git_environment)

#: deck_archetype table name -> short deck membership value.
KNOWN_DECKS = ("deck_of_escape", "deck_of_destruction",
               "deck_of_summoning", "deck_of_punishment")
DECK_SHORT = {"deck_of_escape": "escape",
              "deck_of_destruction": "destruction",
              "deck_of_summoning": "summoning",
              "deck_of_punishment": "punishment"}
_TAG34_COND = "TAG_MAJOR_VERSION == 34"

#: Git-tree paths of the audited TextDB directories (repo-root relative).
I18N_ZH_DIR = "crawl-ref/source/dat/i18n/zh/"
DESCRIPT_DIR = "crawl-ref/source/dat/descript/"
DESCRIPT_ZH_DIR = "crawl-ref/source/dat/descript/zh/"

#: database.cc AllDBs[0] ("descriptions"): the fixed English input list in
#: load order. The parent loads every file in this exact order and stores
#: with DBM_REPLACE, so a later file overrides an earlier one.
EN_DESCRIPT_FILES = (
    "features.txt", "items.txt", "unident.txt", "unrand.txt",
    "monsters.txt", "spells.txt", "gods.txt", "branches.txt",
    "skills.txt", "ability.txt", "cards.txt", "commands.txt",
    "clouds.txt", "status.txt", "monstatus.txt", "mutations.txt",
    "passives.txt",
)


def resolve_commit(ref: str) -> str:
    """Resolve a git commit-ish to its full 40-hex SHA, fail-closed.

    Runs under the shared trusted git environment
    (i18n_shared.trusted_git_environment()), which forces
    GIT_NO_REPLACE_OBJECTS=1 so a `git replace` ref can never resolve
    the rev to another object (R2-CODE3-003); the environment also
    strips caller-controlled GIT_* variables for determinism.
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
    git environment forces GIT_NO_REPLACE_OBJECTS=1 (R2-CODE3-003), so a
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


def git_ls_tree_blobs(ref: str, rel_dir: str) -> list[str]:
    """Direct-children blob (file) names under `rel_dir` at `ref`.

    Mirrors database.cc get_dir_files_ext(dir, "txt") with
    recursion_depth 0: only regular files directly inside the directory
    whose names end with `txt` are returned, in std::sort (byte
    lexicographic) order; subdirectories are excluded. Names are
    returned without the directory prefix, exactly like the C++
    directory listing. Runs under the trusted git environment
    (GIT_NO_REPLACE_OBJECTS=1, R2-CODE3-003). Fail-closed: a git error
    (unreadable tree) aborts the run; an absent or empty directory
    yields an empty list and the caller decides whether that is a
    production-valid empty sequence or a missing mandatory input.
    """
    r = subprocess.run(
        ["git", "ls-tree", "-z", ref, "--", rel_dir],
        capture_output=True, cwd=ROOT, env=trusted_git_environment())
    if r.returncode != 0:
        print(
            f"error: cannot enumerate {rel_dir} at {ref} "
            f"(git ls-tree exit code {r.returncode})",
            file=sys.stderr)
        if r.stderr.strip():
            print(r.stderr.decode("utf-8", "replace").strip(),
                  file=sys.stderr)
        raise SystemExit(1)
    names: list[str] = []
    prefix = rel_dir
    for item in r.stdout.decode("utf-8", "replace").split("\0"):
        if not item:
            continue
        meta, _, name = item.partition("\t")
        fields = meta.split(" ")
        if len(fields) != 3:
            raise SystemExit(
                f"unexpected git ls-tree entry {item[:80]!r} for "
                f"{rel_dir} at {ref}")
        _mode, obj_type, _oid = fields
        if obj_type != "blob":
            continue  # directories (and gitlinks) are not input files
        if not name.startswith(prefix):
            raise SystemExit(
                f"unexpected git ls-tree name {name!r} outside "
                f"{rel_dir} at {ref}")
        base = name[len(prefix):]
        if "/" in base or not base.endswith("txt"):
            continue  # nested children and non-.txt names are excluded
        names.append(base)
    return sorted(names)


def _order_source_first(files: list[str]) -> list[str]:
    """Mirror the database.cc child TextDB constructor ordering: the
    directory scan returns files sorted by std::sort, and `source.txt`
    is forced to the front so domain-specific files loaded later can
    override entries (DBM_REPLACE last-wins)."""
    return ([f for f in files if f == "source.txt"]
            + [f for f in files if f != "source.txt"])


def discover_source_db_files(ref: str) -> list[str]:
    """Complete production input sequence of the localized SourceDB.

    database.cc TextDB child constructor (lines ~211-241): when
    `dat/i18n/zh/source.txt` exists (it always does in the audited
    trees), every `.txt` direct child is discovered and ordered with
    source.txt first. Fail-closed (R2-CODE3-001): a tree without
    source.txt (or an unenumerable/empty directory) aborts instead of
    silently producing an empty SourceDB, because source.txt is the
    required audit input.
    """
    files = git_ls_tree_blobs(ref, I18N_ZH_DIR)
    if "source.txt" not in files:
        print(
            f"error: cannot discover the localized SourceDB inputs: "
            f"{I18N_ZH_DIR} at {ref} contains no source.txt "
            f"(found: {files or '<none>'})",
            file=sys.stderr)
        raise SystemExit(1)
    return _order_source_first(files)


def discover_desc_en_files(ref: str) -> list[str]:
    """English DescriptionDB input sequence: the fixed parent list of
    database.cc AllDBs[0] in load order. Production croaks on a missing
    mandatory English file (datafile_path with croak_on_fail in
    _regenerate_db), so a missing file here is fail-closed too."""
    files = set(git_ls_tree_blobs(ref, DESCRIPT_DIR))
    missing = [f for f in EN_DESCRIPT_FILES if f not in files]
    if missing:
        print(
            f"error: mandatory English description files missing from "
            f"the tree at {ref}: {missing} (production database.cc "
            f"croaks on these)",
            file=sys.stderr)
        raise SystemExit(1)
    return list(EN_DESCRIPT_FILES)


def discover_desc_zh_files(ref: str) -> list[str]:
    """Complete production input sequence of the localized
    DescriptionDB, mirroring the database.cc child TextDB constructor
    conditional exactly (lines ~211-241).

    * When `dat/descript/zh/source.txt` exists (production's check
      file), the child scans the locale directory: every `.txt` direct
      child, sorted, source.txt first.
    * Otherwise the child inherits the parent's fixed input list
      (EN_DESCRIPT_FILES) and _regenerate_db loads only the files that
      exist under the locale directory, in that fixed order.

    The discovered sequence is always surfaced in the payload manifest
    (`desc_zh_input_sequence`), so the effective branch is never
    silent.
    """
    files = git_ls_tree_blobs(ref, DESCRIPT_ZH_DIR)
    if "source.txt" in files:
        return _order_source_first(files)
    return [f for f in EN_DESCRIPT_FILES if f in files]


def _matching_brace(text: str, open_idx: int) -> int:
    """Index of the brace matching text[open_idx] ('{'), fail-closed.

    The bodies this helper walks (the card_type enum and the card_name /
    card_name_en / card_is_removed functions) contain no braces inside
    string literals, so a plain depth count is exact for them.
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
# Strict tokenizer (R2-CODE-002)
# ---------------------------------------------------------------------------

# Every token the audited regions may contain. A strict cursor loop
# consumes the whole region token by token; anything that matches no
# alternative aborts the run, so unknown syntax can never be skipped.
_SKIP_RE = re.compile(r"\s+|//[^\n]*")
_TOKEN_RE = re.compile(
    r"case\s+(?P<case_label>CARD_[A-Z0-9_]+|NUM_CARDS)\s*:"
    r"|return\s+C_\(\s*\"(?P<c_ctx>(?:[^\"\\]|\\.)*)\"\s*,\s*"
    r"\"(?P<c_key>(?:[^\"\\]|\\.)*)\"\s*\)\s*;"
    r"|return\s+T_\(\s*\"(?P<t_key>(?:[^\"\\]|\\.)*)\"\s*\)\s*;"
    r"|return\s+\"(?P<plain>(?:[^\"\\]|\\.)*)\"\s*;"
    r"|return\s+(?P<bool_val>true|false)\s*;"
    r"|(?P<default>default\s*:)"
    r"|(?P<directive>\#[^\n]*)"
    r"|(?P<lbrace>\{)"
    r"|(?P<rbrace>\})"
    r"|(?P<ident>CARD_[A-Z0-9_]+)"
    r"|(?P<integer>\d+)"
    r"|(?P<comma>,)")


def _token_kind(m: re.Match) -> str:
    """Name of the token alternative a strict-tokenizer match belongs to."""
    if m.group("case_label") is not None:
        return "case"
    if m.group("c_key") is not None:
        return "c_return"
    if m.group("t_key") is not None:
        return "t_return"
    if m.group("plain") is not None:
        return "plain_return"
    if m.group("bool_val") is not None:
        return "bool_return"
    if m.group("default") is not None:
        return "default"
    if m.group("directive") is not None:
        return "directive"
    if m.group("lbrace") is not None:
        return "lbrace"
    if m.group("rbrace") is not None:
        return "rbrace"
    if m.group("ident") is not None:
        return "ident"
    if m.group("integer") is not None:
        return "integer"
    if m.group("comma") is not None:
        return "comma"
    raise SystemExit("unrecognized token in strict parse")


def _strict_tokenize(text: str, region: str):
    """Yield every token in `text`, aborting on any unconsumed content.

    Whitespace and `//` comments are skipped between tokens. A position
    that matches no allowed token form (for example an unknown return
    statement, a stray identifier, or malformed punctuation) aborts the
    run, so a silently ignored syntax change can never slip through the
    audit.
    """
    pos = 0
    while pos < len(text):
        m = _SKIP_RE.match(text, pos)
        if m:
            pos = m.end()
            continue
        m = _TOKEN_RE.match(text, pos)
        if not m:
            raise SystemExit(
                f"unconsumed token in {region}: {text[pos:pos + 60]!r}")
        yield m
        pos = m.end()


def _require_no_tokens(text: str, region: str) -> None:
    """Fail if `text` contains any token (only whitespace/comments)."""
    for _m in _strict_tokenize(text, region):
        raise SystemExit(f"unexpected content in {region}")


def _norm_cond(cond: str) -> str:
    return re.sub(r"\s+", " ", cond).strip()


_COND_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?:\s*(?:==|!=|<=|>=|<|>)\s*"
    r"(?:[A-Za-z_][A-Za-z0-9_]*|\d+))?$")
_DEFINED_RE = re.compile(r"^!?defined\s+[A-Za-z_][A-Za-z0-9_]*$")


def _parse_directive(directive_text: str) -> tuple[str, str | None]:
    """Parse one preprocessor directive line into (kind, condition).

    kind is one of 'if'/'ifdef'/'ifndef'/'elif'/'else'/'endif'. The
    condition (if any) must be a single identifier comparison or a
    `[!]defined NAME` form; unknown directives and trailing tokens abort
    the run.
    """
    text = directive_text.strip()
    if "//" in text:
        text = text.split("//", 1)[0].rstrip()
    if text.startswith("#ifdef "):
        cond = text[7:].strip()
        if not _DEFINED_RE.fullmatch(cond):
            raise SystemExit(f"unexpected #ifdef condition {cond!r}")
        return ("ifdef", _norm_cond(cond))
    if text.startswith("#ifndef "):
        cond = text[8:].strip()
        if not _DEFINED_RE.fullmatch(cond):
            raise SystemExit(f"unexpected #ifndef condition {cond!r}")
        return ("ifndef", _norm_cond(cond))
    if text.startswith("#if "):
        cond = text[4:].strip()
        if not _COND_RE.fullmatch(cond):
            raise SystemExit(f"unexpected #if condition {cond!r}")
        return ("if", _norm_cond(cond))
    if text.startswith("#elif"):
        cond = text[5:].strip()
        if not _COND_RE.fullmatch(cond):
            raise SystemExit(f"unexpected #elif condition {cond!r}")
        return ("elif", _norm_cond(cond))
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
    #else/#elif bookkeeping (R2-CODE2-002).

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
    """Preprocessor frame tracker for the audited regions.

    Validates #if/#ifdef/#ifndef/#elif/#else/#endif pairing and closure
    (every TAG_MAJOR_VERSION == 34 block must open and close inside the
    region), rejects a duplicate #else and an #elif after #else, and
    reports whether the current point is inside an *active* TAG-34
    frame.
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

    def in_tag34(self) -> bool:
        return any(frame.cond == _TAG34_COND and frame.active
                   for frame in self.frames)


# ---------------------------------------------------------------------------
# Card source parsers (strict, R2-CODE-002)
# ---------------------------------------------------------------------------

def parse_card_enum(text: str) -> list[tuple[str, bool]]:
    """Return [(member, in_tag34), ...] from the card_type enum in
    declaration order.

    `text` is the file content supplied by the caller (read from the
    baseline Git blob, never from the worktree). `in_tag34` records
    whether the member sits inside a `#if TAG_MAJOR_VERSION == 34`
    conditional block, which is the removed-card lifetime marker.

    Strict grammar: every non-comment line is either a preprocessor
    directive (balanced and closed) or a comma-separated list of
    CARD_[A-Z0-9_]+ / NUM_CARDS members, optionally with `= <integer>`.
    Duplicate members and unknown tokens abort the run.
    """
    m = re.search(r"enum\s+card_type\s*\{", text)
    if not m:
        raise SystemExit("cannot find enum card_type in decks.h blob")
    open_idx = text.find("{", m.start())
    close_idx = _matching_brace(text, open_idx)
    body = text[open_idx + 1:close_idx]

    frames = _PreprocessorFrames("card_type enum (decks.h)")
    members: list[tuple[str, bool]] = []
    seen: set[str] = set()
    for raw in body.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        if line.startswith("#"):
            frames.handle(line)
            continue
        for part in line.split(","):
            part = part.strip()
            if not part:
                continue
            mm = re.fullmatch(
                r"(CARD_[A-Z0-9_]+|NUM_CARDS)(\s*=\s*\d+)?", part)
            if not mm:
                raise SystemExit(
                    f"unexpected token {part!r} in card_type enum "
                    f"(decks.h blob)")
            tok = mm.group(1)
            if tok in seen:
                raise SystemExit(
                    f"duplicate member {tok} in card_type enum "
                    f"(decks.h blob)")
            seen.add(tok)
            members.append((tok, frames.in_tag34()))
    frames.require_closed()
    return members


def _function_body(text: str, sig_re: re.Pattern) -> str:
    """Text of a card function (signature through its closing brace)."""
    m = sig_re.search(text)
    if not m:
        raise SystemExit("cannot find card function in decks.cc blob")
    open_idx = text.find("{", m.end())
    if open_idx < 0:
        raise SystemExit("card function has no body brace in decks.cc blob")
    close_idx = _matching_brace(text, open_idx)
    # Include the closing brace so callers can walk the region again.
    return text[m.start():close_idx + 1]


def _function_switch_regions(text: str, sig_re: re.Pattern, fn_name: str
                             ) -> tuple[str, str]:
    """Return (switch_body, tail) of a card function.

    The function body must start with exactly `switch (card) { ... }`;
    anything before the switch aborts the run. The tail is the text after
    the switch's closing brace up to the function's closing brace.
    """
    body = _function_body(text, sig_re)
    sig_end = body.find("{")
    if sig_end < 0:
        raise SystemExit(f"{fn_name} has no body brace in decks.cc blob")
    open_idx = body.find("{", sig_end)
    close_idx = _matching_brace(body, open_idx)
    interior = body[open_idx + 1:close_idx]
    m = re.search(r"switch\s*\(\s*card\s*\)\s*\{", interior)
    if not m:
        raise SystemExit(f"cannot find switch (card) in {fn_name} body")
    switch_open = interior.find("{", m.start())
    switch_close = _matching_brace(interior, switch_open)
    _require_no_tokens(interior[:m.start()],
                       f"{fn_name} body before switch")
    return (interior[switch_open + 1:switch_close],
            interior[switch_close + 1:])


def parse_card_switch(body: str, localized: bool
                      ) -> tuple[dict[str, object], list[str]]:
    """Parse one card switch body (strict).

    Returns ({case label: value}, ordered case labels). For the EN switch
    (localized=False) the value is the plain name string; for the
    localized switch it is (t_key, context_or_None).

    Grammar: a balanced sequence of preprocessor directives and
    case/return runs; consecutive case labels (the TAG-34 removed members
    and NUM_CARDS) share the following return, mirroring C fallthrough.
    Duplicate cases (including two consecutive occurrences of the same
    label, both still in the pending run before the shared return), a
    return without a preceding case, a case without a return, mixed or
    unknown return forms (including boolean returns and default:) and
    any stray token abort the run.
    """
    values: dict[str, object] = {}
    labels: list[str] = []
    pending: list[str] = []
    frames = _PreprocessorFrames("card switch")
    for m in _strict_tokenize(body, "card switch"):
        kind = _token_kind(m)
        if kind == "directive":
            frames.handle(m.group("directive"))
            continue
        if kind == "case":
            label = m.group("case_label")
            if label in values or label in pending:
                raise SystemExit(f"duplicate case {label} in card switch")
            pending.append(label)
            labels.append(label)
            continue
        if kind == "c_return":
            if not localized:
                raise SystemExit("unexpected C_() return in EN card switch")
            value: object = (m.group("c_key"), m.group("c_ctx"))
        elif kind == "t_return":
            if not localized:
                raise SystemExit("unexpected T_() return in EN card switch")
            value = (m.group("t_key"), None)
        elif kind == "plain_return":
            if localized:
                raise SystemExit(
                    "unexpected plain return in localized card switch")
            value = m.group("plain")
        elif kind == "bool_return":
            raise SystemExit("unexpected boolean return in card switch")
        elif kind == "default":
            raise SystemExit("unexpected default: in card switch")
        else:
            raise SystemExit(
                f"unexpected token ({kind}) in card switch")
        if not pending:
            raise SystemExit("return without preceding case in card switch")
        for label in pending:
            values[label] = value
        pending = []
    if pending:
        raise SystemExit(
            f"card switch case(s) without a return: {pending}")
    frames.require_closed()
    return values, labels


def parse_removed_cases(text: str) -> list[str]:
    """Strictly parse the card_is_removed() switch (R2-CODE3-002).

    The accepted grammar is exactly the documented canonical shape, no
    more and no less:

        switch (card)
        {
        #if TAG_MAJOR_VERSION == 34
        case CARD_...:
        case CARD_...:
            return true;
        #endif
        default:
            return false;
        }

    Concretely, the switch body must be, in order: the single top-level
    `#if TAG_MAJOR_VERSION == 34` directive; one or more consecutive
    `case CARD_...:` labels (the single pending case run, unique); the
    single `return true;` of that branch (which consumes the pending
    run); the matching `#endif`; `default:`; and `return false;` as the
    last token. The `default:` and `return false;` must sit outside the
    TAG-34 block, after it.

    Any deviation aborts: a nested conditional (`#if`/`#ifdef`/
    `#ifndef` inside the TAG-34 block), an extra branch (`#else`,
    `#elif`, a repeated `#if`), a repeated `#endif`, a case outside the
    TAG-34 block, a case after the `return true;`, a case without a
    return, a `return true;` without cases, more than one `return
    true;`, more than one `default:`, a boolean expression instead of
    the exact literal, or any content after `return false;` (including
    a stray preprocessor directive). The boolean literals must be
    exactly `true` / `false`.
    """
    switch_body, tail = _function_switch_regions(
        text, _SIG_RE["card_is_removed"], "card_is_removed")
    _require_no_tokens(tail, "card_is_removed body after switch")
    cases: list[str] = []
    pending: list[str] = []
    # Dedicated state machine: no generic frame tracking, so a nested
    # conditional can never be mistaken for the canonical TAG-34 block.
    # expect_if -> expect_cases -> expect_endif -> expect_default ->
    # expect_false -> done.
    state = "expect_if"
    for m in _strict_tokenize(switch_body, "card_is_removed switch"):
        kind = _token_kind(m)
        if kind == "directive":
            dir_kind, cond = _parse_directive(m.group("directive"))
            if state == "expect_if":
                if dir_kind != "if" or cond != _TAG34_COND:
                    raise SystemExit(
                        "card_is_removed switch must start with exactly "
                        f"`#if {_TAG34_COND}` (got "
                        f"{m.group('directive').strip()!r})")
                state = "expect_cases"
            elif state == "expect_endif":
                if dir_kind != "endif":
                    raise SystemExit(
                        "card_is_removed: unexpected directive "
                        f"{m.group('directive').strip()!r} after the "
                        "TAG-34 `return true;`; only the matching "
                        "`#endif` is allowed (nested conditionals, "
                        "extra branches and repeated #if/#else/#elif/"
                        "#endif forms are rejected)")
                state = "expect_default"
            else:
                raise SystemExit(
                    "card_is_removed: unexpected directive "
                    f"{m.group('directive').strip()!r} (the TAG-34 "
                    "block is the only conditional the switch may "
                    "contain)")
            continue
        if kind == "case":
            if state != "expect_cases":
                raise SystemExit(
                    "card_is_removed case after the TAG-34 "
                    "`return true;`")
            label = m.group("case_label")
            if label in cases or label in pending:
                raise SystemExit(
                    f"duplicate case {label} in card_is_removed switch")
            pending.append(label)
            continue
        if kind == "bool_return":
            if m.group("bool_val") == "true":
                if state != "expect_cases":
                    raise SystemExit(
                        "card_is_removed has more than one `return true;`")
                if not pending:
                    raise SystemExit(
                        "card_is_removed `return true;` without cases")
                cases.extend(pending)
                pending = []
                state = "expect_endif"
            else:
                if state != "expect_false":
                    raise SystemExit(
                        "card_is_removed `return false;` must follow "
                        "`default:` after the TAG-34 block")
                state = "done"
            continue
        if kind == "default":
            if state != "expect_default":
                raise SystemExit(
                    "card_is_removed default: must sit alone outside "
                    "the TAG-34 block, after `#endif`")
            state = "expect_false"
            continue
        raise SystemExit(
            f"unexpected token ({kind}) in card_is_removed switch")
    if state != "done":
        raise SystemExit(
            "card_is_removed switch must contain exactly the canonical "
            "shape: `#if TAG_MAJOR_VERSION == 34` + cases + `return "
            "true;` + `#endif` + `default:` + `return false;` "
            f"(ended in state {state!r})")
    return cases


def parse_fallthrough(region: str, localized: bool) -> object:
    """Value of the trailing `return` after the switch (the fallthrough
    name, e.g. `a very buggy card`), which no case label reaches.

    The region must contain exactly one return token (strict): for the EN
    function a plain string, for the localized function T_("...") or
    C_("...", "...").
    """
    tokens = list(_strict_tokenize(region, "card function tail"))
    if len(tokens) != 1:
        raise SystemExit(
            "card function tail must contain exactly one return "
            f"(got {len(tokens)} token(s))")
    m = tokens[0]
    if m.group("c_key") is not None:
        if not localized:
            raise SystemExit(
                "unexpected C_() fallthrough return in card_name_en")
        return (m.group("c_key"), m.group("c_ctx"))
    if m.group("t_key") is not None:
        if not localized:
            raise SystemExit(
                "unexpected T_() fallthrough return in card_name_en")
        return (m.group("t_key"), None)
    if m.group("plain") is not None:
        if localized:
            raise SystemExit(
                "unexpected plain fallthrough return in card_name")
        return m.group("plain")
    raise SystemExit("unexpected fallthrough return form in card function")


_SIG_RE = {
    "card_name_en": re.compile(
        r"\bcard_name_en\s*\(\s*card_type\s+card\s*\)"),
    "card_name": re.compile(r"\bcard_name\s*\(\s*card_type\s+card\s*\)"),
    "card_is_removed": re.compile(
        r"\bcard_is_removed\s*\(\s*card_type\s+card\s*\)"),
}


_DECK_TABLE_RE = re.compile(
    r"deck_archetype\s+(deck_of_[a-z_]+)\s*=\s*\{(.*?)\};", re.S)


def parse_deck_tables(text: str, enum_members: list[str]
                      ) -> dict[str, list[str]]:
    """Return {deck_of_<name>: [CARD_X in source order]} for the four
    deck_archetype tables in decks.cc (strict).

    `text` is the file content supplied by the caller (read from the
    baseline Git blob, never from the worktree). Each table body must be
    a sequence of `{ CARD_X, <integer> },` entries (an empty body is
    allowed); any other token aborts the run. An unknown or duplicate
    table name and a missing known table abort; every referenced card
    must be a card_type enum member and may appear at most once per
    table.
    """
    tables: dict[str, list[str]] = {}
    for m in _DECK_TABLE_RE.finditer(text):
        name, body = m.group(1), m.group(2)
        if name not in KNOWN_DECKS:
            raise SystemExit(
                f"unexpected deck_archetype table {name!r} in decks.cc blob")
        if name in tables:
            raise SystemExit(
                f"duplicate deck_archetype table {name!r} in decks.cc blob")
        tokens = list(_strict_tokenize(body, f"deck table {name}"))
        entries: list[str] = []
        i = 0
        while i < len(tokens):
            if _token_kind(tokens[i]) != "lbrace":
                raise SystemExit(
                    f"expected '{{' at start of an entry in deck table "
                    f"{name}")
            if (i + 1 >= len(tokens)
                    or _token_kind(tokens[i + 1]) != "ident"):
                raise SystemExit(
                    f"expected a card identifier in deck table {name}")
            if (i + 2 >= len(tokens)
                    or _token_kind(tokens[i + 2]) != "comma"):
                raise SystemExit(
                    f"expected ',' after the card in deck table {name}")
            if (i + 3 >= len(tokens)
                    or _token_kind(tokens[i + 3]) != "integer"):
                raise SystemExit(
                    f"expected an integer weight in deck table {name}")
            if (i + 4 >= len(tokens)
                    or _token_kind(tokens[i + 4]) != "rbrace"):
                raise SystemExit(
                    f"expected '}}' after the weight in deck table {name}")
            entries.append(tokens[i + 1].group("ident"))
            i += 5
            if i < len(tokens):
                if _token_kind(tokens[i]) != "comma":
                    raise SystemExit(
                        f"expected ',' between entries in deck table {name}")
                i += 1
        tables[name] = entries
    missing = [k for k in KNOWN_DECKS if k not in tables]
    if missing:
        raise SystemExit(
            f"missing deck_archetype tables in decks.cc blob: {missing}")
    member_set = set(enum_members)
    for name, entries in tables.items():
        for card in entries:
            if card not in member_set:
                raise SystemExit(
                    f"deck table {name} references {card} which is not a "
                    f"card_type enum member (decks.cc blob)")
        if len(set(entries)) != len(entries):
            raise SystemExit(
                f"deck table {name} lists a card more than once")
    return tables


def removed_base_name(member: str) -> str:
    """Historical base name derived from a removed member identifier:
    CARD_SHAFT_REMOVED -> Shaft, CARD_STAIRS_REMOVED -> Stairs,
    CARD_FAMINE_REMOVED -> Famine."""
    base = member
    if base.startswith("CARD_"):
        base = base[len("CARD_"):]
    if base.endswith("_REMOVED"):
        base = base[:-len("_REMOVED")]
    return " ".join(word.capitalize() for word in base.split("_"))


# ---------------------------------------------------------------------------
# Production SourceDB model (R2-CODE-001)
# ---------------------------------------------------------------------------

def _escape_key(raw: str) -> str:
    """Python mirror of database.cc i18n_escape_key(): normalize a C++
    runtime string to source.txt key format (backslash first, then \\r,
    \\n, \\t). Card keys are plain ASCII, but the mirror keeps the model
    exact for any key form."""
    s = raw.replace("\\", "\\\\")
    s = s.replace("\r", "\\r")
    s = s.replace("\n", "\\n")
    s = s.replace("\t", "\\t")
    return s


@dataclass
class SourceEntry:
    """One source-database entry with production parse semantics.

    raw_key: physical key line as-is (trim_keys=false, no \\# decode,
    no unescape; whitespace belongs to the key).
    canonical_key: lowercase(raw_key) -- the SourceDB lookup key space.
    value: ZH display value exactly as production i18n_source_lookup()
    would return it: leading blank lines stripped (_trim_leading_newlines
    at the _parse_text_db flush), the loader's trailing newline artifact
    removed, and i18n escape sequences decoded (i18n_unescape_value).
    source_file: basename of the input file this entry came from (the
    localized SourceDB may be split across several .txt files).
    """
    raw_key: str
    canonical_key: str
    value: str
    key_line: int
    value_line: int
    source_file: str


def parse_source_physical(text: str, source_file: str) -> list[SourceEntry]:
    """Parse one source-database file with production SourceDB semantics.

    Mirrors database.cc `_parse_text_db(..., trim_keys=false)` as
    implemented by i18n_shared.parse_entries_physical():
      - lines starting with '#' are comment lines, skipped everywhere;
      - '%%%%' block separators (starts-with match);
      - the key is the first non-empty line after a separator, preserved
        VERBATIM (trim_keys=false: whitespace belongs to the key; no
        \\# decode, no unescape);
      - the canonical key is lowercase(raw_key) (C++ lowercase());
      - value lines are right-trimmed of " \\t\\n\\r" and joined with \\n.

    The joined value is then normalized with the shared
    production-equivalent runtime_normalize_value() (trim_string_right +
    trim_leading_newlines + trailing \\r\\n strip + i18n_unescape_value),
    which reproduces the database.cc display pipeline exactly: the
    _parse_text_db flush applies _trim_leading_newlines to the
    accumulated value, i18n_source_lookup strips the trailing \\n loader
    artifact and then decodes i18n escapes. The raw physical parse would
    keep a leading blank line (e.g. `Key\n\n值\\n尾` -> '\\n值\\n尾')
    and literal escape text; the normalized value is the string the
    player actually sees (`值\n尾` with a real newline).

    `text` is the file content supplied by the caller (read from the
    baseline Git blob, never from the worktree); `source_file` is the
    input-file basename recorded on every returned entry.
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
    return [SourceEntry(
        raw_key=pe.raw_key,
        canonical_key=pe.canonical_key,
        value=runtime_normalize_value(pe.value),
        key_line=pe.key_line,
        value_line=pe.value_line,
        source_file=source_file,
    ) for pe in parse_entries_physical(source)]


class SourceDB:
    """Production-semantics SourceDB lookup model over the complete
    input sequence (R2-CODE3-001).

    The localized SourceDB is loaded from every discovered .txt file in
    database.cc load order (source.txt first, the rest in directory
    discovery order); each file is parsed with _parse_text_db
    (trim_keys=false) and stored with DBM_REPLACE, so a later file's
    definition of a canonical key overrides an earlier file's. This
    class merges the sequence with exactly that last-wins semantics and
    records every cross-file override as an override fact
    (`self.overrides`) instead of dropping it silently.

    Within one file, a duplicate canonical key is a fail-closed error:
    production DBM_REPLACE would silently let the last line win, hiding
    an authoring collision; the audit must never pass that silently.
    Cross-file overrides are the production mechanism domain-specific
    files use to move keys, so they are modeled and reported, not
    rejected.

    Lookup mirrors database.cc i18n_source_lookup():
      - T_(en): query canonical(i18n_escape_key(en)); an empty value is a
        miss and falls back to English.
      - C_(ctx, en): query canonical(i18n_escape_key("ctx|en")) first;
        only when that misses (or is empty), fall back to
        canonical(i18n_escape_key(en)); otherwise English.
    """

    def __init__(self, files: list[tuple[str, list[SourceEntry]]]):
        """files: [(input_file_basename, entries)] in production load
        order (source.txt first, remaining files in directory discovery
        order)."""
        self.entries: list[SourceEntry] = []
        self.overrides: list[dict[str, object]] = []
        self._by_canonical: dict[str, SourceEntry] = {}
        self._by_raw: dict[str, SourceEntry] = {}
        for source_file, file_entries in files:
            seen_in_file: dict[str, SourceEntry] = {}
            for entry in file_entries:
                prev_in_file = seen_in_file.get(entry.canonical_key)
                if prev_in_file is not None:
                    raise SystemExit(
                        f"{source_file} canonical key collision: "
                        f"{entry.canonical_key!r} defined by both "
                        f"{prev_in_file.raw_key!r} (line "
                        f"{prev_in_file.key_line}) and "
                        f"{entry.raw_key!r} (line {entry.key_line})")
                seen_in_file[entry.canonical_key] = entry
                prev_eff = self._by_canonical.get(entry.canonical_key)
                if prev_eff is not None:
                    self._record_override(entry, prev_eff)
                self._by_canonical[entry.canonical_key] = entry
                self._by_raw[entry.raw_key] = entry
                self.entries.append(entry)

    def _record_override(self, winner: SourceEntry,
                         superseded: SourceEntry) -> None:
        """Record one DBM_REPLACE override fact (later file wins)."""
        canon = winner.canonical_key
        rec = next((r for r in self.overrides
                    if r["canonical_key"] == canon), None)
        fact = {"file": superseded.source_file,
                "raw_key": superseded.raw_key,
                "key_line": superseded.key_line}
        if rec is None:
            self.overrides.append({
                "canonical_key": canon,
                "winner": {"file": winner.source_file,
                            "raw_key": winner.raw_key,
                            "key_line": winner.key_line},
                "superseded": [fact],
            })
        else:
            rec["superseded"].append(fact)  # type: ignore[union-attr]
            rec["winner"] = {"file": winner.source_file,
                              "raw_key": winner.raw_key,
                              "key_line": winner.key_line}

    def exact_case_key_exists(self, key: str) -> bool:
        """True when a physical key line equals `key` exactly in any
        input file of the sequence."""
        return key in self._by_raw

    def canonical(self, en: str, ctx: str | None = None) -> str:
        return lowercase_string(_escape_key(f"{ctx}|{en}" if ctx else en))

    def _physical(self, entry: SourceEntry) -> str:
        """Human-readable physical-key provenance for resolution paths:
        source.txt hits keep the historical compact form, hits from a
        later override file name the file."""
        if entry.source_file == "source.txt":
            return f"(physical key {entry.raw_key!r})"
        return (f"(physical key {entry.raw_key!r} in "
                f"{entry.source_file})")

    def lookup(self, en: str, ctx: str | None = None
               ) -> tuple[str | None, SourceEntry | None, str]:
        """Production lookup; returns (value, supplying_entry, path).

        value is None when production would display the English key
        (canonical miss or explicitly empty value). path is a
        human-readable T_/C_ resolution description.
        """
        if ctx:
            qualified = f"{ctx}|{en}"
            hit = self._fetch(qualified)
            if hit is not None:
                entry, value = hit
                return (value, entry,
                        f"C_({ctx!r}, {en!r}) -> canonical "
                        f"{self.canonical(en, ctx)!r} hit "
                        f"{self._physical(entry)}")
            hit = self._fetch(en)
            if hit is not None:
                entry, value = hit
                return (value, entry,
                        f"C_({ctx!r}, {en!r}) -> context key miss; "
                        f"canonical {self.canonical(en)!r} fallback hit "
                        f"{self._physical(entry)}")
            return (None, None,
                    f"C_({ctx!r}, {en!r}) -> context key "
                    f"{self.canonical(en, ctx)!r} and plain key "
                    f"{self.canonical(en)!r} both miss -> English fallback")
        hit = self._fetch(en)
        if hit is not None:
            entry, value = hit
            return (value, entry,
                    f"T_({en!r}) -> canonical {self.canonical(en)!r} hit "
                    f"{self._physical(entry)}")
        return (None, None,
                f"T_({en!r}) -> canonical {self.canonical(en)!r} miss "
                f"-> English fallback")

    def _fetch(self, en: str) -> tuple[SourceEntry, str] | None:
        entry = self._by_canonical.get(self.canonical(en))
        if entry is None or entry.value == "":
            return None
        return entry, entry.value


@dataclass
class DescEntry:
    """One TextDB (description) entry: raw physical key, value, the
    1-indexed key line and the input file it came from."""
    raw_key: str
    value: str
    key_line: int
    source_file: str


def parse_db_keys(text: str, source_file: str) -> list[DescEntry]:
    """Parse a TextDB file the way _parse_text_db() in database.cc does:
    `%%%%` block separators (a line whose first four characters are
    `%%%%`), lines starting with `#` skipped as comments everywhere, key =
    first remaining line of each block (trimmed; production also
    lowercases it -- presence and diff comparisons in this tool lowercase
    both sides), rest = value (each line right-trimmed, joined with \n).

    `text` is the file content supplied by the caller (read from the
    baseline Git blob, never from the worktree). `source_file` is the
    input-file basename recorded on every returned entry.
    """
    entries: list[DescEntry] = []
    key: str | None = None
    key_line = 0
    value_lines: list[str] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if not line or line[0] == '#':
            continue
        if line.startswith("%%%%"):
            if key is not None:
                entries.append(DescEntry(
                    raw_key=key, value="\n".join(value_lines),
                    key_line=key_line, source_file=source_file))
            key = None
            value_lines = []
            continue
        if key is None:
            key = line.strip()
            key_line = lineno
        else:
            value_lines.append(line.rstrip())
    if key is not None:
        entries.append(DescEntry(
            raw_key=key, value="\n".join(value_lines),
            key_line=key_line, source_file=source_file))
    return entries


def merge_desc_sequence(
        entries: list[DescEntry]
) -> tuple[dict[str, DescEntry], list[dict[str, object]]]:
    """Merge a DescriptionDB input sequence with production DBM_REPLACE
    last-wins semantics (R2-CODE3-001).

    `entries` is the concatenation of every file's entries in production
    load order. Production stores keys lowercased, so the effective key
    space is lowercase(raw_key); a later definition (within or across
    files) overrides an earlier one exactly like dbm_store(DBM_REPLACE).
    Returns (effective: lowercase key -> winning entry, override facts),
    where every override fact records the winner and the full superseded
    chain in load order.
    """
    effective: dict[str, DescEntry] = {}
    overrides: list[dict[str, object]] = []
    for entry in entries:
        canon = entry.raw_key.lower()
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


def _canonical_temp_root() -> str:
    """Canonical non-renamable temp root: realpath(/tmp), verified
    root-owned with the sticky bit.

    A root that an unprivileged process can rename (the OS user temp
    dir, e.g. /var/folders/... on macOS, is user-owned 0700) makes the
    R2-CODE2-003 race real: POSIX allows renaming an already-open
    directory, so a concurrent rename can relocate openat(dir_fd) writes
    out of the trusted root. /tmp is owned by uid 0 and carries the
    sticky bit, so no ordinary user can rename or replace it while its
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
            f"mode={oct(st.st_mode)}); refusing to write (R2-CODE2-003: "
            f"only the non-renamable /tmp root is permitted)",
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
    outside the root are rejected outright. This is the fix for the
    second R2 mechanical routing blocker (R2-CODE2-003): the previous
    implementation also trusted the OS user temp dir
    (tempfile.gettempdir()), which on macOS is a user-owned 0700
    directory that a concurrent process can rename while its descriptor
    is open -- POSIX allows renaming an open directory, so the
    "inside the temp root" guarantee did not survive to the final
    openat(dir_fd) write. Only the non-renamable /tmp root (root-owned,
    sticky) is accepted, so there is no parent chain and no open-root
    rename that could relocate the write; if /tmp itself were ever not
    root-owned sticky, the run fails closed instead of falling back to a
    renamable root.

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
            f"such as the OS user temp dir are rejected, R2-CODE2-003)",
            file=sys.stderr)
        raise SystemExit(1)
    raw_prefix = os.sep + os.sep.join(components[:prefix_end])
    canonical = os.sep + os.sep.join(root.split(os.sep)[1:])
    if raw_prefix not in ("/tmp", canonical):
        print(
            f"error: --inventory-output prefix {raw_prefix!r} is not "
            f"/tmp or its canonical form {canonical!r}; refusing to "
            f"write (R2-CODE2-003)",
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


def desc_key_for(name: str, name_en: str, tag34: set[str],
                 en_lm: dict[str, str]) -> str:
    """Description key (`<name> card`) for one enum member.

    Current and sentinel members use the card_name_en() value. Removed
    members cannot use the TAG-34 switch value (it is the shared `a buggy
    card`), so their historical key is derived from the enum identifier:
    prefer `the <Base> card` when the EN description database contains it
    (keys compared lowercased, like the production loader), then
    `<Base> card`, then the `the <Base> card` form itself (which then
    simply reports desc_en/desc_zh false).
    """
    if name in tag34:
        base = removed_base_name(name)
        for cand in (f"the {base} card", f"{base} card"):
            if cand.lower() in en_lm:
                return cand
        return f"the {base} card"
    if name_en.endswith(" card"):
        return name_en
    return name_en + " card"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--inventory-output",
        default="/tmp/card-inventory.json",
        help="output JSON path; must be an absolute path that is exactly "
             "one brand-new basename directly under /tmp (the canonical "
             "root-owned sticky temp root; realpath /private/tmp on "
             "macOS) -- nested components, '.', '..', relative paths, "
             "renamable roots such as the OS user temp dir and every "
             "other location are rejected; the trusted root is opened "
             "once with O_NOFOLLOW and the target is created with "
             "O_EXCL|O_NOFOLLOW (dir_fd-style), so an existing target, a "
             "symlinked target and every other unsafe form are rejected, "
             "directories are never auto-created, and no parent chain "
             "exists that could be renamed away; every rebuild needs a "
             "fresh filename or a deleted old file")
    ap.add_argument(
        "--baseline-ref",
        default="HEAD",
        help="git commit-ish recorded as the payload 'baseline' (the review "
             "anchor for reproducible rebuilds); resolved with "
             "`git rev-parse <ref>` to a full 40-hex SHA, default HEAD; "
             "all inputs -- decks.h, decks.cc, the complete discovered "
             "SourceDB sequence (dat/i18n/zh/*.txt), the complete "
             "DescriptionDB sequences (dat/descript/*.txt and "
             "dat/descript/zh/*.txt per database.cc discovery) and the "
             "glossary -- are read from this commit's Git objects via "
             "`git show`/`git ls-tree` under the trusted git environment, "
             "so the inventory is independent of local worktree state and "
             "of git replace refs")
    args = ap.parse_args()
    baseline = resolve_commit(args.baseline_ref)

    # Complete production input sequence discovery (R2-CODE3-001): the
    # SourceDB and DescriptionDB inputs are discovered from the baseline
    # Git tree exactly like database.cc (TextDB child constructor +
    # _regenerate_db), so a later-added domain file (e.g. zz-cards.txt)
    # is part of the audited sequence and its DBM_REPLACE overrides are
    # modeled, never silently ignored. Every unique blob is read once;
    # the manifest binds the discovered sequences and per-file digests
    # into the payload.
    source_files = discover_source_db_files(baseline)
    desc_en_files = discover_desc_en_files(baseline)
    desc_zh_files = discover_desc_zh_files(baseline)
    input_paths: dict[str, str] = {
        "decks.h": "crawl-ref/source/decks.h",
        "decks.cc": "crawl-ref/source/decks.cc",
    }
    input_paths.update({f"i18n/{f}": I18N_ZH_DIR + f
                        for f in source_files})
    input_paths.update({f"desc_en/{f}": DESCRIPT_DIR + f
                        for f in desc_en_files})
    input_paths.update({f"desc_zh/{f}": DESCRIPT_ZH_DIR + f
                        for f in desc_zh_files})
    blobs = {k: git_show_blob(baseline, rel)
             for k, rel in input_paths.items()}

    enum = parse_card_enum(blobs["decks.h"].decode("utf-8"))
    members = [name for name, _flag in enum]
    tag34 = {name for name, flag in enum if flag}
    decks_cc = blobs["decks.cc"].decode("utf-8")

    # Lifecycle conservation: every enum member has exactly one lifecycle
    # (current / removed / sentinel).
    if "NUM_CARDS" in tag34:
        raise SystemExit(
            "NUM_CARDS must not sit inside a TAG_MAJOR_VERSION == 34 "
            "block (decks.h blob)")
    sentinel = [n for n in members if n == "NUM_CARDS"]
    if len(sentinel) != 1:
        raise SystemExit(
            "NUM_CARDS sentinel missing from card_type enum (decks.h blob)")
    removed = sorted(tag34)
    current = [n for n in members if n not in tag34 and n != "NUM_CARDS"]
    if len(current) + len(removed) + len(sentinel) != len(members):
        raise SystemExit(
            "lifecycle conservation violated: an enum member has no "
            "single lifecycle (decks.h blob)")

    # card_name_en() and card_name() switches (same case order).
    en_switch, en_labels = parse_card_switch(
        _function_switch_regions(
            decks_cc, _SIG_RE["card_name_en"], "card_name_en")[0],
        localized=False)
    loc_switch, loc_labels = parse_card_switch(
        _function_switch_regions(
            decks_cc, _SIG_RE["card_name"], "card_name")[0],
        localized=True)

    if set(en_switch) != set(members) or set(loc_switch) != set(members):
        raise SystemExit(
            "card_name_en()/card_name() case labels do not cover exactly "
            "the card_type enum members (decks.cc blob)")
    if en_labels != loc_labels:
        raise SystemExit(
            "card_name_en() and card_name() switches are not in the same "
            "case order (decks.cc blob)")

    removed_cases = parse_removed_cases(decks_cc)
    if set(removed_cases) != tag34:
        raise SystemExit(
            "card_is_removed() cases disagree with the members inside the "
            "TAG_MAJOR_VERSION == 34 block (decks.cc blob)")

    en_fall = parse_fallthrough(
        _function_switch_regions(
            decks_cc, _SIG_RE["card_name_en"], "card_name_en")[1],
        localized=False)
    loc_fall = parse_fallthrough(
        _function_switch_regions(
            decks_cc, _SIG_RE["card_name"], "card_name")[1],
        localized=True)

    tables = parse_deck_tables(decks_cc, members)
    membership: dict[str, str] = {}
    for name in members:
        found = [t for t in KNOWN_DECKS if name in tables[t]]
        if len(found) > 1:
            raise SystemExit(
                f"card {name} appears in multiple deck tables: {found}")
        membership[name] = DECK_SHORT[found[0]] if found else "none"

    src = SourceDB([
        (f, parse_source_physical(blobs[f"i18n/{f}"].decode("utf-8"), f))
        for f in source_files])
    db_en_entries = [e for f in desc_en_files
                     for e in parse_db_keys(
                         blobs[f"desc_en/{f}"].decode("utf-8"), f)]
    db_zh_entries = [e for f in desc_zh_files
                     for e in parse_db_keys(
                         blobs[f"desc_zh/{f}"].decode("utf-8"), f)]
    # Effective description keyspaces with production DBM_REPLACE
    # last-wins across the complete load sequence.
    en_effective, desc_en_overrides = merge_desc_sequence(db_en_entries)
    zh_effective, desc_zh_overrides = merge_desc_sequence(db_zh_entries)
    en_lm = {k: e.raw_key for k, e in en_effective.items()}
    zh_lm = {k: e.raw_key for k, e in zh_effective.items()}

    inventory = []
    for name in members:
        lifecycle = ("removed" if name in tag34
                     else "sentinel" if name == "NUM_CARDS" else "current")
        name_en = en_switch[name]
        t_key, context = loc_switch[name]  # type: ignore[misc]
        lookup_key = f"{context}|{t_key}" if context else t_key
        zh, hit_entry, path = src.lookup(t_key, context)
        dk = desc_key_for(name, name_en, tag34, en_lm)
        entry = {
            "identity": f"card:{name}",
            "lifecycle": lifecycle,
            "name_en": name_en,
            "t_key": t_key,
            "context": context,
            "context_key": (src.exact_case_key_exists(lookup_key)
                            if context else None),
            "name_zh": zh,
            "name_display_fallback": zh is None,
            "exact_case_key": src.exact_case_key_exists(lookup_key),
            "canonical_collision": (hit_entry is not None
                                    and hit_entry.raw_key != lookup_key),
            "resolution": path,
            "deck_membership": membership[name],
            "desc_key": dk,
            "desc_en": dk.lower() in en_lm,
            "desc_zh": dk.lower() in zh_lm,
            "desc_en_value": (en_effective.get(dk.lower()).value
                               if dk.lower() in en_effective else None),
            "desc_zh_value": (zh_effective.get(dk.lower()).value
                               if dk.lower() in zh_effective else None),
        }
        if lifecycle == "removed":
            entry["removed_base_name"] = removed_base_name(name)
        inventory.append(entry)

    ft_key, ft_ctx = loc_fall  # type: ignore[misc]
    ft_lookup_key = f"{ft_ctx}|{ft_key}" if ft_ctx else ft_key
    ft_zh, ft_entry, ft_path = src.lookup(ft_key, ft_ctx)
    ft_desc_key = (ft_key if ft_key.endswith(" card")
                   else ft_key + " card")
    fallthrough_entry = {
        "name_en": en_fall,
        "t_key": ft_key,
        "context": ft_ctx,
        "context_key": (src.exact_case_key_exists(ft_lookup_key)
                        if ft_ctx else None),
        "name_zh": ft_zh,
        "name_display_fallback": ft_zh is None,
        "exact_case_key": src.exact_case_key_exists(ft_lookup_key),
        "canonical_collision": (ft_entry is not None
                                and ft_entry.raw_key != ft_lookup_key),
        "resolution": ft_path,
        "desc_key": ft_desc_key,
        "desc_en": ft_desc_key.lower() in en_lm,
        "desc_zh": ft_desc_key.lower() in zh_lm,
        "desc_en_value": (en_effective.get(ft_desc_key.lower()).value
                           if ft_desc_key.lower() in en_effective
                           else None),
        "desc_zh_value": (zh_effective.get(ft_desc_key.lower()).value
                           if ft_desc_key.lower() in zh_effective
                           else None),
    }

    # Production-semantics coverage record (replaces the old exact-case
    # missing_t_keys list): keys whose production display falls back to
    # English, and cards whose canonical lookup hit a different physical
    # key (cross-domain canonical collision).
    t_unresolved = sorted({
        (f"{e['context']}|{e['t_key']}" if e["context"] else e["t_key"])
        for e in inventory if e["name_display_fallback"]
    } | ({ft_lookup_key} if fallthrough_entry["name_display_fallback"]
         else set()))
    canonical_collisions = [e["identity"] for e in inventory
                            if e["canonical_collision"]]
    # Suspicious translated keys: plain source.txt keys that equal a card
    # EN name but are not referenced as a plain T_ key by any card (e.g. a
    # plain key for a name that is only used via a C_ context). Such keys
    # may belong to another domain (Torment is also a damage type), so
    # this list is reported only, never judged.
    plain_raw = {e.raw_key for e in src.entries if "|" not in e.raw_key}
    name_en_values = {e["name_en"] for e in inventory} | {en_fall}
    referenced_plain = {e["t_key"] for e in inventory
                        if e["context"] is None}
    if ft_ctx is None:
        referenced_plain.add(ft_key)
    extra_name_keys = sorted(
        k for k in plain_raw
        if k in name_en_values and k not in referenced_plain)

    en_only_desc_keys = sorted(
        en_lm[k] for k in en_lm.keys() - zh_lm.keys())
    zh_only_desc_keys = sorted(
        zh_lm[k] for k in zh_lm.keys() - en_lm.keys())

    payload = {
        "baseline": baseline,
        "glossary_sha256": hashlib.sha256(
            git_show_blob(baseline, "docs/glossary.md")).hexdigest(),
        "inputs": {
            k: {"path": input_paths[k],
                "sha256": hashlib.sha256(blobs[k]).hexdigest()}
            for k in input_paths
        },
        "source_input_sequence": source_files,
        "desc_en_input_sequence": desc_en_files,
        "desc_zh_input_sequence": desc_zh_files,
        "source_overrides": src.overrides,
        "desc_en_overrides": desc_en_overrides,
        "desc_zh_overrides": desc_zh_overrides,
        "enum_members": members,
        "removed_members": removed,
        "deck_tables": {DECK_SHORT[k]: tables[k] for k in KNOWN_DECKS},
        "switch_fallthrough": fallthrough_entry,
        "t_unresolved_keys": t_unresolved,
        "canonical_collisions": canonical_collisions,
        "extra_name_keys": extra_name_keys,
        "en_only_desc_keys": en_only_desc_keys,
        "zh_only_desc_keys": zh_only_desc_keys,
        "inventory": inventory,
    }
    digest = hashlib.sha256(json.dumps(
        payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    payload["inventory_sha256"] = digest

    out = write_inventory_output(
        args.inventory_output,
        json.dumps(payload, ensure_ascii=False, indent=1))

    n_current = sum(1 for e in inventory if e["lifecycle"] == "current")
    n_removed = sum(1 for e in inventory if e["lifecycle"] == "removed")
    n_sentinel = sum(1 for e in inventory if e["lifecycle"] == "sentinel")
    print(f"card inventory sha256: {digest}")
    print(f"enum members: {len(members)} "
          f"(current={n_current}, removed={n_removed}, "
          f"sentinel={n_sentinel})")
    print(f"switch coverage: card_name_en={len(en_labels)}, "
          f"card_name={len(loc_labels)}, same case order")
    print("deck tables: " + " ".join(
        f"{DECK_SHORT[k]}={len(tables[k])}" for k in KNOWN_DECKS))
    print(f"source DB input sequence ({len(source_files)}): "
          + " ".join(source_files))
    print(f"desc EN input sequence ({len(desc_en_files)}): "
          + " ".join(desc_en_files))
    print(f"desc ZH input sequence ({len(desc_zh_files)}): "
          + " ".join(desc_zh_files))
    print(f"source overrides: {src.overrides}")
    print(f"desc overrides: EN={desc_en_overrides} ZH={desc_zh_overrides}")
    print(f"T_ unresolved (English fallback): {t_unresolved}")
    print(f"canonical collisions: {canonical_collisions}")
    print(f"extra name keys: {extra_name_keys}")
    print(f"desc keys (effective): EN={len(en_effective)} "
          f"ZH={len(zh_effective)} "
          f"(EN-only={en_only_desc_keys}, ZH-only={zh_only_desc_keys})")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
