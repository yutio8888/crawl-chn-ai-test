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
except CARD_WILD_MAGIC, which uses C_("card name", "Wild Magic").

Display names are looked up in dat/i18n/zh/source.txt: plain keys match
directly, the C_ context key matches `card name|Wild Magic`. The known
gap (Wrath has no T_ key) is reproduced mechanically, together with full
coverage checks for every other referenced key.

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

The payload records a `baseline` commit (the review anchor) so the
inventory can be reproduced from any checkout: pass `--baseline-ref
<commit-ish>` to pin it (default: HEAD). All five input files and the
glossary are read from Git objects at that commit via `git show
<ref>:<path>` -- never from the local worktree -- so the output is
identical regardless of local checkout state or uncommitted edits.

The output JSON write is fail-closed (absolute path inside the OS temp
dir or /tmp, parent chain and target opened with O_NOFOLLOW / O_EXCL;
see write_inventory_output()).

Usage:
  python3 .claude/scripts/card_inventory.py --baseline-ref <commit> \
      --inventory-output /tmp/card-inventory.json
"""
import argparse
import errno
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

#: deck_archetype table name -> short deck membership value.
KNOWN_DECKS = ("deck_of_escape", "deck_of_destruction",
               "deck_of_summoning", "deck_of_punishment")
DECK_SHORT = {"deck_of_escape": "escape",
              "deck_of_destruction": "destruction",
              "deck_of_summoning": "summoning",
              "deck_of_punishment": "punishment"}
_TAG34_COND = "TAG_MAJOR_VERSION == 34"


def resolve_commit(ref: str) -> str:
    """Resolve a git commit-ish to its full 40-hex SHA, fail-closed."""
    r = subprocess.run(
        ["git", "rev-parse", "--verify", "--end-of-options",
         f"{ref}^{{commit}}"],
        capture_output=True, text=True, cwd=ROOT)
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
    from the Git object database, never from the worktree. Fail-closed:
    a non-zero exit or empty output (missing path or object) aborts the
    run with exit code 1.
    """
    r = subprocess.run(
        ["git", "show", "--end-of-options", f"{ref}:{rel_path}"],
        capture_output=True, cwd=ROOT)
    if r.returncode != 0 or not r.stdout:
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


def parse_card_enum(text: str) -> list[tuple[str, bool]]:
    """Return [(member, in_tag34), ...] from the card_type enum in
    declaration order.

    `text` is the file content supplied by the caller (read from the
    baseline Git blob, never from the worktree). `in_tag34` records
    whether the member sits inside a `#if TAG_MAJOR_VERSION == 34`
    conditional block, which is the removed-card lifetime marker. A
    minimal preprocessor frame tracker follows #if/#ifdef/#ifndef/
    #elif/#else/#endif inside the enum body; unknown tokens abort.
    """
    m = re.search(r"enum\s+card_type\s*\{", text)
    if not m:
        raise SystemExit("cannot find enum card_type in decks.h blob")
    open_idx = text.find("{", m.start())
    close_idx = _matching_brace(text, open_idx)
    body = text[open_idx + 1:close_idx]

    frames: list[tuple[str, bool]] = []  # (normalized condition, active)
    members: list[tuple[str, bool]] = []
    for raw in body.splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line:
            continue
        if line.startswith("#"):
            if line.startswith("#if "):
                frames.append((_norm_cond(line[4:]), True))
            elif line.startswith("#ifdef "):
                frames.append(("defined " + line[7:].strip(), True))
            elif line.startswith("#ifndef "):
                frames.append(("!defined " + line[8:].strip(), True))
            elif line.startswith("#elif"):
                if frames:
                    cond, active = frames[-1]
                    frames[-1] = (_norm_cond(line[5:].strip()), not active)
            elif line.startswith("#else"):
                if frames:
                    cond, active = frames[-1]
                    frames[-1] = (cond, not active)
            elif line.startswith("#endif"):
                if frames:
                    frames.pop()
            # other directives (#pragma etc.) do not occur inside the enum
            continue
        in_tag34 = any(cond == _TAG34_COND and active
                       for cond, active in frames)
        for tok in line.rstrip(",").split(","):
            tok = tok.strip().split("=")[0].strip()
            if not tok:
                continue
            if not re.fullmatch(r"(?:CARD_[A-Z0-9_]+|NUM_CARDS)", tok):
                raise SystemExit(
                    f"unexpected token {tok!r} in card_type enum "
                    f"(decks.h blob)")
            members.append((tok, in_tag34))
    return members


def _norm_cond(cond: str) -> str:
    return re.sub(r"\s+", " ", cond).strip()


def _function_body(text: str, sig_re: re.Pattern) -> str:
    """Text of a card function (signature through its closing brace)."""
    m = sig_re.search(text)
    if not m:
        raise SystemExit("cannot find card function in decks.cc blob")
    open_idx = text.find("{", m.end())
    if open_idx < 0:
        raise SystemExit("card function has no body brace in decks.cc blob")
    close_idx = _matching_brace(text, open_idx)
    return text[m.start():close_idx]


def _switch_body(body: str) -> str:
    """Text inside `switch (card) { ... }` within a function body."""
    m = re.search(r"switch\s*\(\s*card\s*\)\s*\{", body)
    if not m:
        raise SystemExit("cannot find switch (card) in card function body")
    open_idx = body.find("{", m.start())
    close_idx = _matching_brace(body, open_idx)
    return body[open_idx + 1:close_idx]


def _switch_region_tail(text: str, sig_re: re.Pattern) -> str:
    """Text of a card function after its `switch (card)` body closes
    (the region holding the fallthrough return)."""
    body = _function_body(text, sig_re)
    m = re.search(r"switch\s*\(\s*card\s*\)\s*\{", body)
    if not m:
        raise SystemExit("cannot find switch (card) in card function body")
    open_idx = body.find("{", m.start())
    close_idx = _matching_brace(body, open_idx)
    return body[close_idx + 1:]


_CASE_RE = re.compile(r"case\s+(CARD_[A-Z0-9_]+|NUM_CARDS)\s*:")
# Groups: 1 = C_ context, 2 = C_ key, 3 = T_ key, 4 = plain string.
_RETURN_RE = re.compile(
    r"return\s+C_\(\s*\"([^\"]*)\"\s*,\s*\"([^\"]*)\"\s*\)\s*;"
    r"|return\s+T_\(\s*\"([^\"]*)\"\s*\)\s*;"
    r"|return\s+\"([^\"]*)\"\s*;")
# Groups: 1 = case label, 2 = C_ context, 3 = C_ key, 4 = T_ key,
# 5 = plain string.
_TOK_RE = re.compile(
    r"case\s+(CARD_[A-Z0-9_]+|NUM_CARDS)\s*:"
    r"|return\s+C_\(\s*\"([^\"]*)\"\s*,\s*\"([^\"]*)\"\s*\)\s*;"
    r"|return\s+T_\(\s*\"([^\"]*)\"\s*\)\s*;"
    r"|return\s+\"([^\"]*)\"\s*;")


def parse_card_switch(body: str, localized: bool
                      ) -> tuple[dict[str, object], list[str]]:
    """Parse one card switch body.

    Returns ({case label: value}, ordered case labels). For the EN switch
    (localized=False) the value is the plain name string; for the
    localized switch it is (t_key, context_or_None). Consecutive case
    labels (the TAG-34 removed members and NUM_CARDS) share the following
    return, mirroring C fallthrough. Mixed or unknown return forms and
    cases without a return abort the run.
    """
    values: dict[str, object] = {}
    labels: list[str] = []
    pending: list[str] = []
    for m in _TOK_RE.finditer(body):
        if m.group(1) is not None:
            pending.append(m.group(1))
            labels.append(m.group(1))
            continue
        if m.group(2) is not None:      # C_("context", "key")
            value: object = (m.group(3), m.group(2))
            form = "context"
        elif m.group(4) is not None:    # T_("key")
            value = (m.group(4), None)
            form = "t"
        else:                           # plain "name"
            value = m.group(5)
            form = "plain"
        if ((localized and form == "plain")
                or (not localized and form != "plain")):
            raise SystemExit(
                f"mixed or unexpected return form ({form}) in card switch")
        if not pending:
            raise SystemExit("return without preceding case in card switch")
        for label in pending:
            values[label] = value
        pending = []
    if pending:
        raise SystemExit(
            f"card switch case(s) without a return: {pending}")
    return values, labels


def parse_fallthrough(region: str, localized: bool) -> object:
    """Value of the trailing `return` after the switch (the fallthrough
    name, e.g. `a very buggy card`), which no case label reaches."""
    m = _RETURN_RE.search(region)
    if not m:
        raise SystemExit("cannot find fallthrough return in card function")
    if localized:
        if m.group(2) is not None:      # C_("context", "key")
            return (m.group(2), m.group(1))
        if m.group(3) is not None:      # T_("key")
            return (m.group(3), None)
        raise SystemExit("unexpected fallthrough return form in card_name")
    if m.group(4) is None:
        raise SystemExit("unexpected fallthrough return form in card_name_en")
    return m.group(4)


_SIG_RE = {
    "card_name_en": re.compile(
        r"\bcard_name_en\s*\(\s*card_type\s+card\s*\)"),
    "card_name": re.compile(r"\bcard_name\s*\(\s*card_type\s+card\s*\)"),
    "card_is_removed": re.compile(
        r"\bcard_is_removed\s*\(\s*card_type\s+card\s*\)"),
}


def parse_removed_cases(text: str) -> list[str]:
    """Case labels of the card_is_removed() switch (the removed members).

    `text` is the decks.cc content supplied by the caller (read from the
    baseline Git blob, never from the worktree).
    """
    body = _function_body(text, _SIG_RE["card_is_removed"])
    return [m.group(1) for m in _CASE_RE.finditer(_switch_body(body))]


_DECK_TABLE_RE = re.compile(
    r"deck_archetype\s+(deck_of_[a-z_]+)\s*=\s*\{(.*?)\};", re.S)


def parse_deck_tables(text: str) -> dict[str, list[str]]:
    """Return {deck_of_<name>: [CARD_X in source order]} for the four
    deck_archetype tables in decks.cc.

    `text` is the file content supplied by the caller (read from the
    baseline Git blob, never from the worktree). An unknown table name or
    a missing known table aborts the run (schema-level fail-closed).
    """
    tables: dict[str, list[str]] = {}
    for m in _DECK_TABLE_RE.finditer(text):
        name, body = m.group(1), m.group(2)
        if name not in KNOWN_DECKS:
            raise SystemExit(
                f"unexpected deck_archetype table {name!r} in decks.cc blob")
        tables[name] = re.findall(r"CARD_[A-Z0-9_]+", body)
    missing = [k for k in KNOWN_DECKS if k not in tables]
    if missing:
        raise SystemExit(
            f"missing deck_archetype tables in decks.cc blob: {missing}")
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


def parse_source_keys(text: str) -> tuple[dict[str, str], dict[str, str]]:
    """Parse source.txt into (plain key -> ZH, "context|key" -> ZH).

    `text` is the file content supplied by the caller (read from the
    baseline Git blob, never from the worktree). Keys containing '|' are
    C_ context keys and are kept verbatim in the second dict.
    """
    plain: dict[str, str] = {}
    ctx: dict[str, str] = {}
    blocks = re.split(r"%%%%", text)
    for block in blocks:
        block = block.strip("\n")
        if not block:
            continue
        first, _, rest = block.partition("\n")
        key = first.strip()
        if not key:
            continue
        value = "\n".join(line for line in rest.splitlines()
                          if line.strip()) if rest else ""
        if "|" in key:
            ctx[key] = value
        else:
            plain[key] = value
    return plain, ctx


def parse_db_keys(text: str) -> dict[str, str]:
    """Parse a TextDB file the way _parse_text_db() in database.cc does:
    `%%%%` block separators (a line whose first four characters are
    `%%%%`), lines starting with `#` skipped as comments everywhere, key =
    first remaining line of each block, rest = value.

    `text` is the file content supplied by the caller (read from the
    baseline Git blob, never from the worktree). Keys are returned as
    written; the production loader lowercases them, so presence and diff
    comparisons in this tool lowercase both sides.
    """
    entries: dict[str, str] = {}
    key: str | None = None
    value_lines: list[str] = []
    for line in text.splitlines():
        if not line or line[0] == '#':
            continue
        if line.startswith("%%%%"):
            if key is not None:
                entries[key] = "\n".join(value_lines)
            key = None
            value_lines = []
            continue
        if key is None:
            key = line.strip()
        else:
            value_lines.append(line.rstrip())
    if key is not None:
        entries[key] = "\n".join(value_lines)
    return entries


def lower_key_map(entries: dict[str, str]) -> dict[str, str]:
    """Map lowercase key -> as-written key (production lookups lowercase
    TextDB keys, so presence/diff checks must too)."""
    return {k.lower(): k for k in entries}


def _allowed_temp_roots() -> list[str]:
    """Realpath-normalized roots under which output is permitted: the OS
    temp dir (tempfile.gettempdir()) plus the canonical /tmp, deduplicated
    (they differ on macOS when TMPDIR is set)."""
    roots = [os.path.realpath(tempfile.gettempdir())]
    tmp = os.path.realpath("/tmp")
    if tmp not in roots:
        roots.append(tmp)
    return roots


def write_inventory_output(raw: str, content: str) -> Path:
    """Fail-closed, race-free write of the inventory JSON.

    Pre-validation (kept from the previous implementation): the path
    must be absolute and its realpath must lie inside the OS temp dir
    (tempfile.gettempdir()) or /tmp.

    The write itself is openat-style and never follows a symlink:

    * The parent directory chain is opened level by level, starting
      from an fd of the canonical temp root: every component is opened
      with os.open(comp, O_RDONLY|O_DIRECTORY|O_NOFOLLOW,
      dir_fd=parent_fd). A symlink component fails with ELOOP, a
      missing component fails with ENOENT (directories are never
      auto-created), and a non-directory fails with ENOTDIR.
    * The final element is opened with os.open(base,
      O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW, 0o644, dir_fd=parent_fd):
      the target must not already exist (O_EXCL rejects it with EEXIST,
      so an existing regular file -- including a hardlink to a shared
      inode -- is never truncated or overwritten), and an existing
      symlink at the target fails with ELOOP and the output is never
      written through it. Callers must therefore pick a fresh path for
      every rebuild, or delete the old file first.

    There is no lstat-then-mkdir/write TOCTOU window: every step is a
    single atomic open that refuses to follow symlinks, and all opened
    directory fds are closed on every path. Any failure prints a clear
    error to stderr and exits 1; there is no fallback to a plain
    open/write.
    """
    p = Path(raw)
    if not p.is_absolute():
        print(
            f"error: --inventory-output must be an absolute path inside "
            f"{tempfile.gettempdir()!r} or /tmp; got {raw!r} "
            f"(relative path rejected)",
            file=sys.stderr)
        raise SystemExit(1)
    resolved = os.path.realpath(str(p))
    roots = _allowed_temp_roots()
    root = next((r for r in roots
                 if resolved == r or resolved.startswith(r + os.sep)),
                None)
    if root is None:
        print(
            f"error: --inventory-output must be inside the OS temp dir "
            f"({tempfile.gettempdir()!r}) or /tmp; {raw!r} resolves to "
            f"{resolved}",
            file=sys.stderr)
        raise SystemExit(1)

    # Locate the raw prefix (typically the temp-dir name itself, e.g.
    # /tmp) whose realpath is the permitted root; only components below
    # that prefix are walked with O_NOFOLLOW. This keeps the walk on the
    # path the user actually wrote, so an attacker-retargeted component
    # fails with ELOOP even if realpath() had resolved it to a temp-dir
    # location.
    parts = p.parts
    prefix_end = None
    for i in range(1, len(parts) + 1):
        if os.path.realpath(os.sep.join(parts[:i])) == root:
            prefix_end = i
            break
    if prefix_end is None:
        print(
            f"error: cannot locate temp root {root!r} inside output path "
            f"{raw!r}",
            file=sys.stderr)
        raise SystemExit(1)
    if len(parts) == prefix_end:
        print(
            f"error: --inventory-output {raw!r} resolves to the temp root "
            f"itself; refusing to write to it",
            file=sys.stderr)
        raise SystemExit(1)

    dir_components = parts[prefix_end:-1]
    basename = parts[-1]
    dir_fds: list[int] = []
    try:
        parent_fd = os.open(
            root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        dir_fds.append(parent_fd)
        for comp in dir_components:
            try:
                parent_fd = os.open(
                    comp, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                    dir_fd=parent_fd)
            except OSError as exc:
                print(
                    f"error: --inventory-output parent directory component "
                    f"{comp!r} of {raw!r} cannot be opened as a real "
                    f"directory without following a symlink: {exc}",
                    file=sys.stderr)
                raise SystemExit(1)
            dir_fds.append(parent_fd)
        try:
            final_fd = os.open(
                basename,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o644,
                dir_fd=parent_fd)
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
                    f"error: --inventory-output target {basename!r} of {raw!r} "
                    f"cannot be created or opened for writing without following "
                    f"a symlink: {exc}",
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
        for fd in dir_fds:
            try:
                os.close(fd)
            except OSError:
                pass
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
        help="output JSON path; must be an absolute path inside the OS "
             "temp dir or /tmp whose parent directory already exists; "
             "the parent chain and the target are opened with O_NOFOLLOW "
             "(dir_fd-style), so symlinked components, a symlinked target, "
             "and missing parent directories are all rejected, and "
             "directories are never auto-created; relative and other "
             "paths are rejected; the target itself must NOT already "
             "exist (O_EXCL): every rebuild needs a fresh filename or a "
             "deleted old file")
    ap.add_argument(
        "--baseline-ref",
        default="HEAD",
        help="git commit-ish recorded as the payload 'baseline' (the review "
             "anchor for reproducible rebuilds); resolved with "
             "`git rev-parse <ref>` to a full 40-hex SHA, default HEAD; "
             "all inputs (decks.h, decks.cc, source.txt, cards.txt, "
             "zh/cards.txt) and the glossary are read from this commit's "
             "Git objects via `git show`, so the inventory is independent "
             "of local worktree state")
    args = ap.parse_args()
    baseline = resolve_commit(args.baseline_ref)

    # All five inputs are read as Git blobs at the baseline commit (never
    # from the worktree), so the inventory is reproducible from any
    # checkout state; the digests below hash exactly those blob bytes.
    input_blobs = {
        "decks.h": "crawl-ref/source/decks.h",
        "decks.cc": "crawl-ref/source/decks.cc",
        "cards.txt": "crawl-ref/source/dat/descript/cards.txt",
        "zh/cards.txt": "crawl-ref/source/dat/descript/zh/cards.txt",
        "source.txt": "crawl-ref/source/dat/i18n/zh/source.txt",
    }
    blobs = {k: git_show_blob(baseline, rel)
             for k, rel in input_blobs.items()}

    enum = parse_card_enum(blobs["decks.h"].decode("utf-8"))
    members = [name for name, _flag in enum]
    tag34 = {name for name, flag in enum if flag}
    decks_cc = blobs["decks.cc"].decode("utf-8")

    # card_name_en() and card_name() switches (same case order).
    en_switch, en_labels = parse_card_switch(
        _switch_body(_function_body(decks_cc, _SIG_RE["card_name_en"])),
        localized=False)
    loc_switch, loc_labels = parse_card_switch(
        _switch_body(_function_body(decks_cc, _SIG_RE["card_name"])),
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
        _switch_region_tail(decks_cc, _SIG_RE["card_name_en"]),
        localized=False)
    loc_fall = parse_fallthrough(
        _switch_region_tail(decks_cc, _SIG_RE["card_name"]),
        localized=True)

    tables = parse_deck_tables(decks_cc)
    membership: dict[str, str] = {}
    for name in members:
        found = [t for t in KNOWN_DECKS if name in tables[t]]
        if len(found) > 1:
            raise SystemExit(
                f"card {name} appears in multiple deck tables: {found}")
        membership[name] = DECK_SHORT[found[0]] if found else "none"

    plain_t, ctx_t = parse_source_keys(blobs["source.txt"].decode("utf-8"))
    db_en = parse_db_keys(blobs["cards.txt"].decode("utf-8"))
    db_zh = parse_db_keys(blobs["zh/cards.txt"].decode("utf-8"))
    en_lm = lower_key_map(db_en)
    zh_lm = lower_key_map(db_zh)

    def zh_lookup(t_key: str, context: str | None) -> str | None:
        if context is not None:
            return ctx_t.get(f"{context}|{t_key}")
        return plain_t.get(t_key)

    missing_key_set: set[str] = set()
    inventory = []
    for name in members:
        lifecycle = ("removed" if name in tag34
                     else "sentinel" if name == "NUM_CARDS" else "current")
        name_en = en_switch[name]
        t_key, context = loc_switch[name]  # type: ignore[misc]
        zh = zh_lookup(t_key, context)
        if zh is None:
            missing_key_set.add(t_key)
        dk = desc_key_for(name, name_en, tag34, en_lm)
        entry = {
            "identity": f"card:{name}",
            "lifecycle": lifecycle,
            "name_en": name_en,
            "t_key": t_key,
            "context_key": context,
            "name_zh": zh,
            "missing_t_key": None if zh is not None else t_key,
            "deck_membership": membership[name],
            "desc_key": dk,
            "desc_en": dk.lower() in en_lm,
            "desc_zh": dk.lower() in zh_lm,
        }
        if lifecycle == "removed":
            entry["removed_base_name"] = removed_base_name(name)
        inventory.append(entry)

    ft_key, ft_ctx = loc_fall  # type: ignore[misc]
    ft_zh = zh_lookup(ft_key, ft_ctx)
    if ft_zh is None:
        missing_key_set.add(ft_key)
    ft_desc_key = (ft_key if ft_key.endswith(" card")
                   else ft_key + " card")
    fallthrough_entry = {
        "name_en": en_fall,
        "t_key": ft_key,
        "context_key": ft_ctx,
        "name_zh": ft_zh,
        "desc_key": ft_desc_key,
        "desc_en": ft_desc_key.lower() in en_lm,
        "desc_zh": ft_desc_key.lower() in zh_lm,
    }

    missing_t_keys = sorted(missing_key_set)
    # Suspicious translated keys: plain source.txt keys that equal a card
    # EN name but are not referenced as a plain T_ key by any card (e.g. a
    # plain key for a name that is only used via a C_ context). Such keys
    # may belong to another domain (Torment is also a damage type), so
    # this list is reported only, never judged.
    name_en_values = {e["name_en"] for e in inventory} | {en_fall}
    referenced_plain = {e["t_key"] for e in inventory
                        if e["context_key"] is None}
    if ft_ctx is None:
        referenced_plain.add(ft_key)
    extra_name_keys = sorted(
        k for k in plain_t
        if k in name_en_values and k not in referenced_plain)

    en_only_desc_keys = sorted(
        en_lm[k] for k in en_lm.keys() - zh_lm.keys())
    zh_only_desc_keys = sorted(
        zh_lm[k] for k in zh_lm.keys() - en_lm.keys())

    payload = {
        "baseline": baseline,
        "glossary_sha256": hashlib.sha256(
            git_show_blob(baseline, "docs/glossary.md")).hexdigest(),
        "digests": {
            k: hashlib.sha256(blobs[k]).hexdigest() for k in input_blobs
        },
        "enum_members": members,
        "removed_members": [name for name, flag in enum if flag],
        "deck_tables": {DECK_SHORT[k]: tables[k] for k in KNOWN_DECKS},
        "switch_fallthrough": fallthrough_entry,
        "missing_t_keys": missing_t_keys,
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
    print(f"missing T_ keys: {missing_t_keys}")
    print(f"extra name keys: {extra_name_keys}")
    print(f"desc keys: EN={len(db_en)} ZH={len(db_zh)} "
          f"(EN-only={en_only_desc_keys}, ZH-only={zh_only_desc_keys})")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
