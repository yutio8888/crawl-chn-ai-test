#!/bin/bash
# pre_consolidation_check.sh — detect overlapping key additions between worktrees
#
# Before consolidating multi-agent work into chn-0.34.1-base, verify that
# no two worktrees added the same EN key to source.txt with different
# translations. Content-level conflicts survive git merge cleanly.
#
# Usage:
#   bash .claude/scripts/pre_consolidation_check.sh <target> <wt1> <wt2> ...

set -euo pipefail

TARGET="${1:-chn-0.34.1-base}"
shift
WORKTREES=("$@")

if [ ${#WORKTREES[@]} -lt 1 ]; then
    echo "Usage: $0 <target-branch> <worktree1> [worktree2 ...]"
    exit 1
fi

SOURCE_TXT="crawl-ref/source/dat/i18n/zh/source.txt"

echo "=== Pre-consolidation check ==="
echo "  target:    $TARGET"
echo "  worktrees: ${WORKTREES[*]}"
echo ""

OVERLAPS=0

# Check 1: Each worktree compiles against target
for WT in "${WORKTREES[@]}"; do
    echo "--- $WT ---"
    # Find the worktree directory
    WT_DIR=$(git worktree list | grep "\[$WT\]" | awk '{print $1}' || true)
    if [ -z "$WT_DIR" ]; then
        echo "  ⚠ Worktree not found: $WT (skipping compile check)"
        continue
    fi
    if [ -f "$WT_DIR/$SOURCE_TXT" ]; then
        echo -n "  Build: "
        if make -j4 -C "$WT_DIR/crawl-ref/source" 2>&1 | grep -q "error:"; then
            echo "❌ FAIL"
            OVERLAPS=1
        else
            echo "✅"
        fi
    fi
done

# Check 2: Overlapping key additions
if [ ${#WORKTREES[@]} -ge 2 ]; then
    TMPDIR=$(mktemp -d)
    trap "rm -rf $TMPDIR" EXIT

    echo ""
    echo "--- Key overlap analysis ---"

    for WT in "${WORKTREES[@]}"; do
        git diff "$TARGET..$WT" -- "$SOURCE_TXT" > "$TMPDIR/$WT.diff" 2>/dev/null || true
        if [ ! -s "$TMPDIR/$WT.diff" ]; then
            echo "  $WT: no source.txt changes"
            continue
        fi
        # Extract added keys (lines starting with + but not +++, %%%%, comments)
        grep '^+[^+#]' "$TMPDIR/$WT.diff" | grep -v '^+%%%' | sed 's/^+//' > "$TMPDIR/$WT.added" 2>/dev/null || true
        # Keep only lines that look like keys (single line, not multi-line values)
        grep -v '^\s' "$TMPDIR/$WT.added" | sort -u > "$TMPDIR/$WT.keys" 2>/dev/null || true
        COUNT=$(wc -l < "$TMPDIR/$WT.keys")
        echo "  $WT: $COUNT keys added"
    done

    for ((i=0; i<${#WORKTREES[@]}; i++)); do
        for ((j=i+1; j<${#WORKTREES[@]}; j++)); do
            WTA="${WORKTREES[$i]}"
            WTB="${WORKTREES[$j]}"
            if [ -f "$TMPDIR/$WTA.keys" ] && [ -f "$TMPDIR/$WTB.keys" ]; then
                COMMON=$(comm -12 "$TMPDIR/$WTA.keys" "$TMPDIR/$WTB.keys")
                if [ -n "$COMMON" ]; then
                    echo ""
                    echo "  ⚠ OVERLAP: $WTA ↔ $WTB"
                    echo "$COMMON" | while read -r key; do
                        echo "    - \"$key\""
                    done
                    OVERLAPS=1
                fi
            fi
        done
    done
fi

echo ""
if [ $OVERLAPS -eq 0 ]; then
    echo "✅ No conflicts — safe to consolidate."
    exit 0
else
    echo "❌ Conflicts found. Resolve before consolidation."
    exit 2
fi
