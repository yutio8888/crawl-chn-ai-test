# Multi-Agent Parallel Architecture — Problems & Fixes

Analysis of P1-P4 batch translation session failures. Date: 2026-07-07.

> **Historical incident analysis for the downstream 0.34.1 work.** Paths,
> proposed priorities, tool behavior, and missing safeguards below describe the
> repository at the incident boundary. Current routing and policy are defined by
> `AGENTS.md`, `.agents/policies/`, and the maintained verification scripts.
> Reproduce any alleged gap on the current default branch before opening or
> scheduling work; GitHub Issues is the only current backlog.

---

## 1. Root Cause Summary Per Problem

### Problem 1: Mass Duplicate Entries from P4b Agent

**Root cause**: The P4b agent was tasked with adding 489 missing monster names but appended
all 667 YAML names to source.txt without first checking which entries already existed.
This created 777 duplicate keys with conflicting translations (e.g., `deep elf`:
`精灵` from decisions.md vs `暗精灵` from new appends).

**Why it happened**: The CLAUDE.md "Agent-Prone Mistakes" table (line 698) already
documents this rule:

> | Duplicate source.txt keys | Agent adds key that already exists | Agent must `grep` source.txt before adding |

But this is passive documentation — agents don't actively enforce it. There is
no programmatic `grep` step in any agent skill definition or CI script.

**Impact**: 777 duplicate keys, last-writer-wins overwrote decisions.md-approved
translations with ad-hoc alternatives.

---

### Problem 2: Case Sensitivity Inconsistency

There are **four different case-handling strategies** across the toolchain:

| Component | Case behavior | Location |
|-----------|--------------|----------|
| C++ `_parse_text_db()` | **Lowercases** keys when loading GDBM | `database.cc:580` |
| C++ `_query_database()` | Lowercases key if `canonicalise_key=true` | `database.cc:783` |
| C++ `i18n_source_lookup()` | Uses **original case** in `i18n_index` map (but GDBM lowercases) | `database.cc:1072` |
| Python `scan_i18n.py::parse_source_txt()` | **Lowercases** keys (`stripped.lower()`) | `scan_i18n.py:317` |
| Python `audit_data_i18n.py::parse_source_txt()` | **Preserves original case** (no `.lower()`) | `audit_data_i18n.py:30` |

**The mismatch**: `audit_data_i18n.py` does a case-sENSITIVE `name in src_entries` check (line 76)
while `scan_i18n.py` lowercases all keys, and the C++ engine is effectively case-insensitive.
This caused ~40 false "missing" reports when YAML monster names (mixed case) were
compared against lowercased source.txt entries.

Note that `audit_data_i18n.py` does have a partial workaround (line 58):
`src_entries_lower = {k.lower(): True for k in src_entries}`, but the primary check
at line 76 is still case-sensitive. The lower lookup only catches exact-lower-match
misses, not the reverse (YAML title-case key not matching a lowercased source.txt key).

---

### Problem 3: No Pre-Consolidation Overlap Detection

The multi-agent parallel development pattern (CLAUDE.md line 661-685) describes:

```
1. SPAN: Launch N agents simultaneously, each with isolation: worktree
         Each agent works on different files (no overlap)
2. WAIT:  All agents complete and commit in their own worktrees
3. CONSOLIDATE: Create a consolidate-* worktree from chn-0.34.1-base
                Cherry-pick ALL agent commits into it
                Resolve source.txt conflicts (see below)
```

**The gap**: "Each agent works on different files (no overlap)" is enforced only
by human coordination — there is no programmatic check. When multiple agents all
modify `source.txt` (adding entries to the end), git sees them as non-conflicting
because the append regions don't overlap line-range-wise. But the **content-level
conflict** (same EN key added by two agents with different CN translations) goes
undetected until runtime.

The CLAUDE.md conflict resolution advice (line 683) — `sed` to keep both sides —
actively **preserves** duplicate entries rather than flagging them:

```bash
sed -i '/^<<<<<<< HEAD$/d; /^=======$/d; /^>>>>>>> .*$/d' source.txt
```

This is the right approach for git-level merge conflicts, but it assumes the
consolidation step also runs a duplicate-key check, which it doesn't.

---

### Problem 4: No Dedup Check in CI Pipeline

Neither `post-coder.sh` (the `YELLOW`-path automated scan invoked by `review_at_merge.sh`)
nor `post-reviewer.sh` checks for duplicate keys in `source.txt`.

What `post-coder.sh` currently runs:
- `i18n_extract.py validate` — T_() key coverage
- `audit_data_i18n.py` — data-driven source coverage
- `scan_i18n.py mprf-p` — positional format compatibility
- `scan_i18n.py arg-mismatch` — format specifier parity
- `scan_i18n.py anti-patterns` — known mistake patterns
- `scan_string_concat.py` — string concatenation blind spots
- `smoke_test.sh` — ZH mode compile smoke

What's **missing**: A simple `source.txt` integrity checker that verifies:
1. No duplicate EN keys
2. No EN keys without corresponding translation
3. No conflicting duplicate entries (same key, different CN values)

---

### Problem 5: Species Consistency Checker Built Reactively

The `species-consistency` subcommand in `scan_i18n.py` was built after species
term mismatches were already committed. It is only invoked in `post-reviewer.sh`
(line 28-29, the review-phase gate), not in `post-coder.sh` (the pre-merge gate).

This means a code-change commit that introduces species term inconsistency would
pass `post-coder.sh` (the YELLOW gate) and only be caught at review time — which
happens after merge in the current workflow.

---

### Problem 6: Agent Blind Spots in CLAUDE.md

CLAUDE.md documents agent concurrency rules (max 4, worktree isolation, compile
with -j4) but has **zero guidance** on source.txt safety protocols for agents:

| Missing guideline | Why needed |
|-------------------|------------|
| grep-before-add protocol | Prevent duplicate entries (Problem 1) |
| decisions.md term lookup | Prevent translation inconsistency (Problem 1 cont.) |
| Post-add self-verification | Catch errors before commit |
| source.txt append format spec | Consistent %%%% separator usage |
| Case normalization for lookups | Prevent false duplicate detection |

The "Agent-Prone Mistakes" table (line 689-699) documents common errors but is
merely warning text — agents don't programmatically enforce these rules.

---

## 2. Architecture Gaps Identified

### Gap A: No Source-of-Truth Integrity Layer

There is no automated check that validates `source.txt` structural integrity
as an independent concern. The existing checks all operate on the *content* of
entries (format specs, anti-patterns, terminology) but none verify structural
properties: uniqueness of keys, absence of self-conflicts, key format consistency.

### Gap B: Python Tool Case-Sensitivity Disagreement

Two Python tools (`scan_i18n.py` and `audit_data_i18n.py`) have **independent**
implementations of `parse_source_txt()` with different case normalization behavior.
There is no shared library — each tool re-implements the parser.

### Gap C: Consolation Step is Manual and Unguarded

The consolidation worktree step relies entirely on human (or agent) judgment
to detect content-level conflicts. There is no automated pre-merge overlap
analysis or post-merge integrity check in the workflow.

### Gap D: CI Gates are Phase-Siloed

The review pipeline has three phases:
1. `post-coder.sh` — post-code-change (runs at merge time for YELLOW)
2. `post-translator.sh` — post-translation (runs at merge time for YELLOW content)
3. `post-reviewer.sh` — post-review (runs after review, not at merge time)

But `species-consistency`, `cross-file terms`, and `validate-terms` are only in
`post-reviewer.sh`. They fire *after* the merge gate, not before. A commit with
species term inconsistency passes the pre-merge check and only fails the
post-hoc review check.

### Gap E: Agent Skills Lack Safety Protocols

The `zh-translator` and `crawl-coder` skill definitions don't include:
- Pre-write: grep source.txt + check decisions.md
- Post-write: self-validate with dedup check
- Commit gate: run `post-coder.sh` before `git commit`

---

## 3. Specific, Actionable Improvements

### Fix 1: Add `source-txt-integrity` Subcommand to `scan_i18n.py`

**Priority**: P0 (blocks Problems 1, 4)

Add a new subcommand that validates source.txt structural integrity:

```python
# In scan_i18n.py, adding to existing subcommands

def cmd_source_txt_integrity(args):
    """Check source.txt for duplicate keys, self-conflicts, and empty entries."""
    entries_raw = OrderedDict()  # key -> list of (cn_value, appearance_order)
    duplicates = []
    self_conflicts = []
    empty_value = []

    with open(args.source_txt, 'r', encoding='utf-8') as f:
        content = f.read()

    order = 0
    for block in re.split(r'^%%%%\n', content, flags=re.MULTILINE)[1:]:
        block = block.strip()
        parts = block.split('\n\n', 1)
        if len(parts) != 2:
            continue
        key = parts[0].strip().lower()  # normalize to lowercase (match C++ behavior)
        value = parts[1].rstrip('\n').strip()
        order += 1

        if key in entries_raw:
            existing_value = entries_raw[key][0][0]
            if value != existing_value:
                self_conflicts.append((key, existing_value, value, order))
            else:
                duplicates.append((key, value, order))
        else:
            entries_raw[key] = [(value, order)]

        if not value:
            empty_value.append(key)

    exit_code = 0

    if duplicates:
        print("=== DUPLICATE-KEYS — same key with same value, already exists ===")
        for key, value, order in sorted(duplicates)[:20]:
            print(f"  \"{key}\" (appearance #{order})")
        if len(duplicates) > 20:
            print(f"  ... and {len(duplicates) - 20} more")
        print(f"  → {len(duplicates)} duplicate(s)")
        print()
        exit_code = 1

    if self_conflicts:
        print("=== SELF-CONFLICT — same key with DIFFERENT values ===")
        for key, v1, v2, order in sorted(self_conflicts)[:20]:
            print(f"  \"{key}\"")
            print(f"    Existing: \"{v1[:60]}\"")
            print(f"    Conflict: \"{v2[:60]}\" (appearance #{order})")
        if len(self_conflicts) > 20:
            print(f"  ... and {len(self_conflicts) - 20} more")
        print(f"  → {len(self_conflicts)} self-conflict(s) — BLOCKER")
        print()
        exit_code = 1

    if empty_value:
        print("=== EMPTY-TRANSLATION — key with no translation ===")
        for key in sorted(empty_value)[:20]:
            print(f"  \"{key}\"")
        if len(empty_value) > 20:
            print(f"  ... and {len(empty_value) - 20} more")
        print(f"  → {len(empty_value)} empty entry/ies")
        print()
        # empty entries are not blockers (T_() falls back to EN key)
        # but they indicate incomplete work

    if exit_code == 0:
        print(f"OK: No duplicate keys or self-conflicts in {len(entries_raw)} unique entries.")
    return exit_code
```

**Register** in the `main()` argparse and dispatch (add alongside existing subcommands).

**Add to post-coder.sh** at the very beginning (before format checks):

```bash
echo "--- source.txt integrity (dedup + self-conflicts) ---"
python3 .claude/scripts/scan_i18n.py source-txt-integrity \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt 2>&1 || true
```

**Also add to post-reviewer.sh** (it's relevant there too).

---

### Fix 2: Normalize Case in `audit_data_i18n.py`

**Priority**: P1 (blocks Problem 2)

Add `.lower()` to `audit_data_i18n.py::parse_source_txt()` (line 30):

```python
# Before (line 30):
entries[parts[0].strip()] = parts[1].rstrip('\n').strip()

# After:
entries[parts[0].strip().lower()] = parts[1].rstrip('\n').strip()
```

Then remove the separate `src_entries_lower` workaround in `check_monster_names` (line 58)
since the primary dict is now already lowercased:

```python
# Remove line 58:
# src_entries_lower = {k.lower(): True for k in src_entries}

# Simplify line 76 from:
# if name in src_entries or name.lower() in src_entries_lower:
# To:
if name.lower() in src_entries:
```

**Also normalize YAML names to lowercase for comparison** in `check_monster_names` (line 54):

```python
yaml_names.add(m.group(1).lower())  # was: yaml_names.add(m.group(1))
```

This makes the comparison fully case-insensitive, matching the C++ runtime behavior.

---

### Fix 3: Add Consolidation Pre-Flight Check Script

**Priority**: P1 (blocks Problem 3)

Create `.claude/scripts/pre_consolidation_check.sh`:

```bash
#!/bin/bash
# pre_consolidation_check.sh — check for overlapping key ranges in agent worktrees
# before consolidation.
#
# Usage:
#   bash .claude/scripts/pre_consolidation_check.sh <target-branch> <worktree1> <worktree2> ...
#
# Reports which source.txt entries would conflict (same EN key from different branches).

set -euo pipefail

TARGET="${1:-chn-0.34.1-base}"
shift
WORKTREES=("$@")

if [ ${#WORKTREES[@]} -lt 2 ]; then
    echo "Need at least 2 worktree branches to compare."
    exit 1
fi

TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

echo "=== Pre-consolidation overlap check ==="
echo "  target: $TARGET"
echo "  worktrees: ${WORKTREES[*]}"
echo ""

declare -A ALL_KEYS
OVERLAPS_FOUND=0

for WT in "${WORKTREES[@]}"; do
    # Extract keys added by this worktree (relative to target)
    git diff "$TARGET..$WT" -- crawl-ref/source/dat/i18n/zh/source.txt \
        > "$TMPDIR/$WT.diff" 2>/dev/null || true

    if [ ! -s "$TMPDIR/$WT.diff" ]; then
        echo "  $WT: no source.txt changes"
        continue
    fi

    # Extract keys from the + side of the diff (lines starting with + but not +++ or +%%)
    python3 -c "
import re, sys
with open('$TMPDIR/$WT.diff') as f:
    content = f.read()
# Find all + lines that are likely keys (not %%%%, not comments, not continuation values)
keys = set()
for line in content.split('\n'):
    if line.startswith('+') and not line.startswith('+++') and not line.startswith('+%%%%'):
        stripped = line[1:].strip()
        if stripped and not stripped.startswith('#'):
            # Key lines are non-empty, non-comment lines after a %%%%
            keys.add(stripped.lower())
for k in sorted(keys):
    print(k)
" > "$TMPDIR/$WT.keys" 2>/dev/null
done

# Cross-reference all worktree keys
for ((i=0; i<${#WORKTREES[@]}; i++)); do
    for ((j=i+1; j<${#WORKTREES[@]}; j++)); do
        WTA="${WORKTREES[$i]}"
        WTB="${WORKTREES[$j]}"
        if [ -f "$TMPDIR/$WTA.keys" ] && [ -f "$TMPDIR/$WTB.keys" ]; then
            OVERLAPS=$(comm -12 <(sort "$TMPDIR/$WTA.keys") <(sort "$TMPDIR/$WTB.keys"))
            if [ -n "$OVERLAPS" ]; then
                echo "⚠ OVERLAP: $WTA ↔ $WTB"
                echo "$OVERLAPS" | while read -r key; do
                    echo "    - \"$key\""
                done
                echo ""
                OVERLAPS_FOUND=1
            fi
        fi
    done
done

if [ $OVERLAPS_FOUND -eq 1 ]; then
    echo "✗ Overlapping key ranges detected. Resolve before consolidation."
    echo "  Options:"
    echo "    1. Deduplicate in one worktree (remove from the other)"
    echo "    2. Use a single sequential agent for shared key ranges"
    echo "    3. Consolidate sequentially (merge one, rebase others)"
    exit 1
else
    echo "✓ No key overlaps — safe to consolidate."
    exit 0
fi
```

**Wire into CLAUDE.md** multi-agent workflow: add step 1.5 after SPAN but before CONSOLIDATE:

```
1.5 PREFLIGHT: bash .claude/scripts/pre_consolidation_check.sh \
                  chn-0.34.1-base <wt1> <wt2> <wt3> ...
```

---

### Fix 4: Move Proactive Checks into `post-coder.sh` (Pre-Merge Gate)

**Priority**: P1 (blocks Problem 5)

Currently `post-reviewer.sh` runs `species-consistency`, `cross_file_terms.py`,
and `validate-terms`. These should also run in `post-coder.sh` so they fire
at the pre-merge YELLOW gate, not just the post-hoc review gate.

Add to `post-coder.sh` (after anti-patterns, before smoke test):

```bash
echo "--- Species term consistency ---"
python3 .claude/scripts/scan_i18n.py species-consistency \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt 2>&1 || true
echo ""
echo "--- Term validation (rejected names from decisions.md) ---"
python3 .claude/scripts/scan_i18n.py validate-terms \
    --glossary docs/decisions.md \
    --source-txt crawl-ref/source/dat/i18n/zh/source.txt 2>&1 || true
```

This makes the pre-merge gate catch these issues before they reach `chn-0.34.1-base`.

---

### Fix 5: Update CLAUDE.md — Source.txt Append-Safe Protocol

**Priority**: P0 (blocks Problem 1, 6)

Add a new subsection after "Agent Concurrency Limits" (line 643) and before
"Multi-Agent Parallel Development Pattern" (line 656):

```markdown
### Source.txt Append-Safe Protocol (MANDATORY for all agents)

Before adding ANY entry to `dat/i18n/zh/source.txt`:

1. **Grep-first**: Check if the EN key already exists:
   ```bash
   grep -nF "§KEY§" crawl-ref/source/dat/i18n/zh/source.txt
   ```
   If the key exists, do NOT append — the translation is already covered.

2. **Glossary lookup**: Check `docs/decisions.md` for term rulings:
   ```bash
   grep -A3 "Choice:" docs/decisions.md | grep -i "§keyword§"
   ```
   Use decisions.md-approved terms whenever applicable.

3. **Post-add self-check**: After writing entries, verify:
   ```bash
   python3 .claude/scripts/scan_i18n.py source-txt-integrity \
       --source-txt crawl-ref/source/dat/i18n/zh/source.txt
   ```

4. **Case discipline**: All EN keys must be in their exact C++ string literal form
   (copy the text inside `T_("...")` verbatim). Do NOT alter case. The C++ runtime
   handles case-insensitive lookup internally; the source.txt key must match the
   C++ literal for `i18n_extract.py` to cross-reference correctly.

5. **Never re-add all**: When tasked with adding "missing" entries from an
   enumeration (monsters, spells, etc.), NEVER blindly append all enumerated names.
   ALWAYS diff against existing keys first:
   ```bash
   # Extract existing keys
   python3 -c "
   import re
   with open('crawl-ref/source/dat/i18n/zh/source.txt') as f:
       keys = set()
       for block in re.split(r'^%%%%\n', f.read(), flags=re.MULTILINE)[1:]:
           parts = block.strip().split('\n\n', 1)
           if len(parts) == 2:
               keys.add(parts[0].strip().lower())
       for k in sorted(keys): print(k)
   " > /tmp/existing-keys.txt

   # Then add only the diff (new EN keys not in existing)
   ```
```

**Also update the "Agent-Prone Mistakes" table** (line 689-699) — add a new row:

```
| Mass duplicate re-add | Appending all 667 monster names when only 489 are missing | Use grep-first protocol; check existing keys before adding |
```

---

### Fix 6: Shared `parse_source_txt` Utility

**Priority**: P2 (long-term maintainability)

Both `scan_i18n.py` and `audit_data_i18n.py` have independent `parse_source_txt()`
implementations. Extract a shared utility:

```python
# .claude/scripts/i18n_shared.py (new file)

import re
import os
from collections import OrderedDict

def parse_source_txt(filepath: str, normalize_case: bool = True) -> OrderedDict:
    """Parse source.txt and return OrderedDict of key -> translation.

    Args:
        filepath: Path to source.txt
        normalize_case: If True, lowercase all keys (matching C++ runtime behavior)

    Returns:
        OrderedDict with keys in file order.
    """
    entries = OrderedDict()
    if not os.path.exists(filepath):
        return entries

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    for entry in re.split(r'^%%%%\n', content, flags=re.MULTILINE)[1:]:
        entry = entry.strip()
        parts = entry.split('\n\n', 1)
        if len(parts) == 2:
            key = parts[0].strip()
            if normalize_case:
                key = key.lower()
            entries[key] = parts[1].rstrip('\n').strip()
        elif len(parts) == 1 and '\n' in parts[0]:
            lines = parts[0].rstrip('\n').split('\n', 1)
            if len(lines) == 2:
                key = lines[0].strip()
                if normalize_case:
                    key = key.lower()
                entries[key] = lines[1].strip()

    return entries
```

Then update both `scan_i18n.py` and `audit_data_i18n.py` to import from this shared module.
This eliminates the case-handling divergence by centralizing it in one place.

---

### Fix 7: Add Agent Skill Safety Instructions

**Priority**: P2 (blocks Problem 6)

Update the `zh-translator` and `crawl-coder` skill definitions to include
source.txt safety as a built-in protocol. The skill files (`.opencode/skills/`)
should include:

For `crawl-coder` skill — add to pre-commit checklist:
```markdown
### Source.txt Integrity (always before commit)
- [ ] Ran `grep -nF "§KEY§" source.txt` for each key being added
- [ ] Checked `docs/decisions.md` for terminology rulings on affected entities
- [ ] Ran `python3 .claude/scripts/scan_i18n.py source-txt-integrity ...`
- [ ] No duplicate keys detected
```

For `zh-translator` skill — add to translation protocol:
```markdown
### Pre-Translation Checklist (before writing any entry)
1. Extract target EN keys
2. grep source.txt for each key — skip if exists
3. grep decisions.md for relevant term rulings
4. Use approved terminology from decisions.md
5. Write only NEW entries (keys not in existing source.txt)
```

---

## 4. Priority Order for Implementation

| Priority | Fix | Effort | Impact |
|----------|-----|--------|--------|
| **P0** | Fix 1: `source-txt-integrity` subcommand + add to post-coder.sh | ~30 min | Prevents Problem 1, 4 recurrence |
| **P0** | Fix 5: CLAUDE.md append-safe protocol | ~15 min (doc only) | Prevents Problem 1, 6 in future sessions |
| **P1** | Fix 2: Case normalization in audit_data_i18n.py | ~10 min | Eliminates 40+ false missing reports |
| **P1** | Fix 3: Pre-consolidation check script | ~20 min | Prevents Problem 3 at consolidation time |
| **P1** | Fix 4: Move proactive checks to post-coder.sh | ~5 min | Catches Problem 5 issues at pre-merge gate |
| **P2** | Fix 6: Shared parse_source_txt utility | ~20 min | Eliminates tool divergence for good |
| **P2** | Fix 7: Agent skill safety instructions | ~15 min | Prevents future agents from repeating mistakes |

**Recommended implementation order**: P0 fixes first (they prevent the most impactful
issues), then P1 (low effort, high leverage), then P2 (maintenance improvements).

**Total estimated effort**: ~2 hours for all fixes.

---

## Appendix: Case Sensitivity Reference

For future reference, here is the definitive case behavior of each layer:

| Layer | Case behavior | Rationale |
|-------|--------------|-----------|
| C++ `T_()` → `i18n_source_lookup()` | Threads original-case key through `i18n_index` (case-sensitive map lookup), but GDBM storage is lowercased. Net effect: **case-insensitive** for retrieval. | Historical — `_parse_text_db` lowercases for TextDB compatibility |
| `i18n_extract.py` | Extracts C++ string literals verbatim (preserves case) | Must match C++ source exactly |
| `scan_i18n.py::parse_source_txt()` | **Lowercases** keys | Matches C++ runtime behavior |
| `audit_data_i18n.py::parse_source_txt()` | **Preserves case** (BUG) | Missing `.lower()` — see Fix 2 |
| YAML monster names | Preserves case from YAML `name:` field | Source of truth; some are title case, some lowercase |
| `zh_monster_name()` map in `mon-util.cc` | Preserves case (used as-is in static array) | Hardcoded C++ map, must match YAML name |

**Rule of thumb for all Python tools**: Always call `.lower()` on source.txt keys.
The C++ runtime is case-insensitive (lowercased GDBM), and YAML names are unreliable
in their casing. The only place case must be preserved is when outputting a key
to the user (for copy-paste into C++ `T_()` calls).
