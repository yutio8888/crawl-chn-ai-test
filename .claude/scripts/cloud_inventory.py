#!/usr/bin/env python3
"""Deterministic read-only cloud inventory for the R1 (cloud names/descriptions)
batch review.

Identity source: the cloud_type enum in crawl-ref/source/cloud-type.h.
Name source: the clouds[] data table in crawl-ref/source/cloud.cc (terse and
verbose names are the first two string literals after each `// CLOUD_X,`
marker). Display names go through T_() (dat/i18n/zh/source.txt) and long
descriptions are looked up by `<terse name> cloud` in dat/descript/clouds.txt
(EN) and dat/descript/zh/clouds.txt (ZH).

Outputs a JSON inventory (rebuildable, temporary artifact) and a coverage
report proving: every enum member has a name entry, every name has a T_ key
(or is reported missing), every description key in EN exists in ZH (and vice
versa, so language-side orphans are detected), and a producer/consumer map
derived from code greps.

The payload records a `baseline` commit (the review anchor) so the
inventory can be reproduced from any checkout: pass `--baseline-ref
<commit-ish>` to pin it (default: HEAD).

Usage:
  python3 .claude/scripts/cloud_inventory.py --baseline-ref <commit> --inventory-output /tmp/cloud-inventory.json
"""
import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "crawl-ref" / "source"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def resolve_commit(ref: str) -> str:
    """Resolve a git commit-ish to its full 40-hex SHA, fail-closed."""
    r = subprocess.run(
        ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
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


def parse_enum(path: Path) -> list[str]:
    """Return the CLOUD_* enum member names in declaration order."""
    txt = path.read_text()
    m = re.search(r"enum cloud_type\s*\{(.*?)\};", txt, re.S)
    if not m:
        raise SystemExit(f"cannot parse cloud_type enum in {path}")
    body = m.group(1)
    names = []
    for line in body.splitlines():
        line = line.split("//")[0].strip()
        if not line or line.startswith("#"):
            continue
        for tok in line.rstrip(",").split(","):
            tok = tok.strip().split("=")[0].strip()
            if tok.startswith("CLOUD_"):
                names.append(tok)
    return names


def parse_cloud_data(path: Path) -> dict[str, dict]:
    """Extract {enum: {terse, verbose}} from the clouds[] table by matching
    each `// CLOUD_X,` comment with the following `{ "terse", "verbose" }`."""
    txt = path.read_text()
    out: dict[str, dict] = {}
    marker_re = re.compile(r"//\s*(CLOUD_[A-Z0-9_]+)\s*,?")
    entry_re = re.compile(r"\{\s*\"([^\"]*)\"\s*(?:,\s*\"([^\"]*)\")?")
    lines = txt.splitlines()
    i = 0
    while i < len(lines):
        mm = marker_re.search(lines[i])
        if mm:
            enum = mm.group(1)
            # find the `{ "terse"` entry within the next few lines
            j = i + 1
            while j < len(lines) and not lines[j].lstrip().startswith("{ \"") \
                    and j < i + 6:
                j += 1
            if j < len(lines):
                em = entry_re.search(lines[j])
                if em:
                    terse = em.group(1)
                    verbose = em.group(2)
                    out[enum] = {"terse": terse, "verbose": verbose}
                    i = j
                    continue
        i += 1
    return out


def parse_t_key(path: Path) -> dict[str, str]:
    """Parse source.txt: plain keys (no context prefix) -> ZH value."""
    txt = path.read_text()
    entries: dict[str, str] = {}
    blocks = re.split(r"%%%%", txt)
    for block in blocks:
        block = block.strip("\n")
        if not block:
            continue
        first, _, rest = block.partition("\n")
        key = first.strip()
        if not key or "|" in key:  # context-prefixed keys (verb|...) excluded
            continue
        value = "\n".join(line for line in rest.splitlines()
                          if line.strip()) if rest else ""
        entries[key] = value
    return entries


def parse_db_keys(path: Path) -> dict[str, str]:
    """Parse a TextDB file: `%%%%` blocks, key = first line, value = rest."""
    txt = path.read_text()
    entries: dict[str, str] = {}
    blocks = re.split(r"%%%%", txt)
    for block in blocks:
        block = block.strip("\n")
        if not block:
            continue
        first, _, rest = block.partition("\n")
        key = first.strip()
        if not key:
            continue
        entries[key] = rest.strip()
    return entries


def grep_producers(enum: str) -> list[str]:
    """Find code locations that create this cloud type (read-only grep)."""
    pats = [rf"place_cloud\s*\(\s*{enum}", rf"big_cloud\s*\(\s*{enum}"]
    hits = []
    for pat in pats:
        r = subprocess.run(
            ["grep", "-rn", "-E", pat, str(SRC)],
            capture_output=True, text=True, cwd=ROOT)
        for line in r.stdout.splitlines():
            if "/cloud.cc:" in line or "/cloud-type.h:" in line:
                continue
            rel = line.replace(str(SRC) + "/", "")
            hits.append(rel)
    return hits


def _allowed_temp_roots() -> list[str]:
    """Realpath-normalized roots under which output is permitted: the OS
    temp dir (tempfile.gettempdir()) plus the canonical /tmp, deduplicated
    (they differ on macOS when TMPDIR is set)."""
    roots = [os.path.realpath(tempfile.gettempdir())]
    tmp = os.path.realpath("/tmp")
    if tmp not in roots:
        roots.append(tmp)
    return roots


def _reject_symlink_components(p: Path) -> None:
    """Reject any *existing* component of the output path, from the root
    down to (and including) the final path element, that is a symbolic
    link. Non-existent components are skipped (mkdir creates them as
    ordinary directories). The permitted temp roots themselves (for
    example /tmp -> /private/tmp on macOS) are exempt: they are
    OS-level directories, not attacker-controlled components inside the
    permitted tree.

    This closes the TOCTOU window left by the realpath check: realpath()
    follows symlinks, so a symlink component that resolves inside the
    temp dir would pass that check even though it could be retargeted
    between validation and write. Fails closed (stderr + exit 1) before
    any mkdir/write.
    """
    roots = _allowed_temp_roots()
    cur = Path(p.anchor)
    found_root = False
    for part in p.parts[1:]:
        cur = cur / part
        # The shallowest prefix whose realpath is a permitted temp root
        # is the permitted root itself; only components *below* it are
        # attacker-controlled and must not be symlinks.
        if not found_root and os.path.realpath(str(cur)) in roots:
            found_root = True
            continue
        try:
            st = cur.lstat()
        except FileNotFoundError:
            continue  # not yet created; mkdir will make an ordinary dir
        except OSError as exc:
            print(
                f"error: cannot inspect output path component {cur}: {exc}",
                file=sys.stderr)
            raise SystemExit(1)
        if stat.S_ISLNK(st.st_mode):
            print(
                f"error: --inventory-output path component {cur} is a "
                f"symbolic link; refusing to write through it",
                file=sys.stderr)
            raise SystemExit(1)


def validate_output_path(raw: str) -> Path:
    """Fail-closed validation for --inventory-output.

    Only an absolute path that resolves (realpath, following symlinks)
    inside the OS temp dir (tempfile.gettempdir()) or /tmp is accepted,
    and no *existing* path component (from the root down to the final
    path element) may be a symbolic link: writing through a symlinked
    component is rejected before any mkdir/write. Relative repository
    paths and non-temp absolute paths are rejected too.
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
    for root in _allowed_temp_roots():
        if resolved == root or resolved.startswith(root + os.sep):
            _reject_symlink_components(p)
            return p
    print(
        f"error: --inventory-output must be inside the OS temp dir "
        f"({tempfile.gettempdir()!r}) or /tmp; {raw!r} resolves to "
        f"{resolved}",
        file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--inventory-output",
        default="/tmp/cloud-inventory.json",
        help="output JSON path; must be an absolute path inside the OS "
             "temp dir or /tmp with no symlink path component (existing "
             "components are lstat-checked; only the temp roots "
             "themselves are exempt); relative and other paths are "
             "rejected")
    ap.add_argument(
        "--baseline-ref",
        default="HEAD",
        help="git commit-ish recorded as the payload 'baseline' (the review "
             "anchor for reproducible rebuilds); resolved with "
             "`git rev-parse <ref>` to a full 40-hex SHA, default HEAD")
    args = ap.parse_args()
    baseline = resolve_commit(args.baseline_ref)

    enum_path = SRC / "cloud-type.h"
    data_path = SRC / "cloud.cc"
    source_txt = SRC / "dat" / "i18n" / "zh" / "source.txt"
    desc_en = SRC / "dat" / "descript" / "clouds.txt"
    desc_zh = SRC / "dat" / "descript" / "zh" / "clouds.txt"

    enums = parse_enum(enum_path)
    names = parse_cloud_data(data_path)
    t = parse_t_key(source_txt)
    db_en = parse_db_keys(desc_en)
    db_zh = parse_db_keys(desc_zh)

    # enum members without a data-table entry
    missing_data = [e for e in enums if e not in names]
    # data-table entries without enum members (unused leftovers)
    extra_data = [e for e in names if e not in enums]

    inventory = []
    for enum in enums:
        if enum not in names:
            inventory.append({
                "identity": f"cloud:{enum}", "lifecycle": "no_data_entry",
                "terse_en": None, "verbose_en": None,
                "terse_zh": None, "verbose_zh": None,
                "desc_key": None, "desc_en": False, "desc_zh": False,
                "producers": [], "missing_t_key": None,
            })
            continue
        terse = names[enum]["terse"]
        verbose = names[enum]["verbose"]
        desc_key = terse + " cloud"
        entry = {
            "identity": f"cloud:{enum}",
            "terse_en": terse,
            "verbose_en": verbose,
            "terse_zh": t.get(terse),
            "verbose_zh": t.get(verbose) if verbose else None,
            "desc_key": desc_key,
            "desc_en": desc_key in db_en,
            "desc_zh": desc_key in db_zh,
            "producers": grep_producers(enum),
            "missing_t_key": None if terse in t
                              or enum in ("CLOUD_NONE", "CLOUD_RANDOM_SMOKE",
                                          "CLOUD_RANDOM", "CLOUD_DEBUGGING")
                              else terse,
        }
        inventory.append(entry)

    # language-side-only description keys (ZH has no EN counterpart)
    zh_only_keys = sorted(set(db_zh) - set(db_en))
    en_only_keys = sorted(set(db_en) - set(db_zh))
    # T_ key coverage for names referenced by the data table
    name_keys = set()
    for e in inventory:
        if e["terse_en"]:
            name_keys.add(e["terse_en"])
        if e["verbose_en"]:
            name_keys.add(e["verbose_en"])
    missing_names = sorted(k for k in name_keys if k not in t)

    payload = {
        "baseline": baseline,
        "glossary_sha256": sha256_file(ROOT / "docs" / "glossary.md"),
        "digests": {
            "cloud-type.h": sha256_file(enum_path),
            "cloud.cc": sha256_file(data_path),
            "source.txt": sha256_file(source_txt),
            "clouds.txt": sha256_file(desc_en),
            "zh/clouds.txt": sha256_file(desc_zh),
        },
        "enum_members": enums,
        "missing_data_entries": missing_data,
        "extra_data_entries": extra_data,
        "zh_only_desc_keys": zh_only_keys,
        "en_only_desc_keys": en_only_keys,
        "missing_t_keys": missing_names,
        "inventory": inventory,
    }
    digest = hashlib.sha256(json.dumps(
        payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    payload["inventory_sha256"] = digest

    out = validate_output_path(args.inventory_output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=1))

    print(f"inventory sha256: {digest}")
    print(f"enum members: {len(enums)}")
    print(f"data entries: {len(names)}")
    print(f"missing data entries: {missing_data}")
    print(f"extra data entries: {extra_data}")
    print(f"missing T_ keys: {missing_names}")
    print(f"desc keys: EN-only={en_only_keys} ZH-only={zh_only_keys}")
    print(f"wrote {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
