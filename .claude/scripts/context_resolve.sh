#!/bin/bash
# context_resolve.sh — Dynamic context injection for agent dispatch.
#
# Given a task description and target files, outputs a minimal context
# block containing only the relevant terminology, constraints, and rules.
# This replaces the full agent prompt for focused tasks.
#
# Usage:
#   bash .claude/scripts/context_resolve.sh "translate god descriptions" \
#       --files dat/database/zh/godspeak.txt
#   bash .claude/scripts/context_resolve.sh "add T_() to beam.cc" \
#       --task-type code

set -euo pipefail

TASK="${1:-}"
shift 2>/dev/null || true

TASK_TYPE=""
FILES=()

while [ $# -gt 0 ]; do
    case "$1" in
        --task-type)
            [ $# -ge 2 ] || { echo "ERROR: --task-type requires a value" >&2; exit 1; }
            TASK_TYPE="$2"; shift 2 ;;
        --files)
            shift
            [ $# -ge 1 ] && [[ "$1" != --* ]] || {
                echo "ERROR: --files requires at least one value" >&2
                exit 1
            }
            while [ $# -gt 0 ] && [[ "$1" != --* ]]; do
                FILES+=("$1")
                shift
            done
            ;;
        *) shift ;;
    esac
done

# Detect task type from keywords if not specified
if [ -z "$TASK_TYPE" ]; then
    # Check review first (narrower patterns, higher priority)
    if echo "$TASK ${FILES[*]}" | grep -qiE 'review|审查|审核|audit'; then
        TASK_TYPE="review"
    # Check code second
    elif echo "$TASK ${FILES[*]}" | grep -qiE '\.cc$|\.h$|T_\(|mprf|compile|build|bug|fix|编译|代码|函数|修复|修改|添加'; then
        TASK_TYPE="code"
    # Check translate last (broadest patterns)
    elif echo "$TASK ${FILES[*]}" | grep -qiE 'translate|翻译|source\.txt|descript|database|dat/.*\.txt'; then
        TASK_TYPE="translate"
    else
        TASK_TYPE="general"
    fi
fi

echo "## Context Injection — $(date -Iminutes)"
echo ""

# ── Common constraints (always included) ──
echo "### Hard Constraints (all tasks)"
echo ""
echo "- NEVER translate Lua comparison strings (\`\"Mummy\"\`, \`\"Zin\"\`)"
echo "- NEVER call \`conj_verb()\` on Chinese strings"
echo "- Positional format \`%n\$s\` → use \`mprf_p\`, not \`mprf\`"
echo "- \`god_name()\` for DB lookup → use \`_god_name_en()\`"
echo ""

# Always resolve terminology from the current worktree.  The query includes a
# glossary hash so callers and reviewers can prove which revision was used.
python3 .claude/scripts/glossary_query.py \
    --task "$TASK" \
    --files "${FILES[@]}" \
    --limit 120
echo ""

# ── Translation context ──
if [ "$TASK_TYPE" = "translate" ]; then
    echo "### Translation Rules"
    echo ""
    echo "- No articles (a/an/the), no plural markers"
    echo "- Adverbs BEFORE verbs"
    echo "- Add 了 after verbs for completed actions"
    echo "- Preserve all @keyword@, w:N weights, %%%% separators"
    echo ""

    echo "### Post-task: run \`bash .claude/scripts/verify_zh.sh --profile translation\`"
    echo ""
fi

# ── Code context ──
if [ "$TASK_TYPE" = "code" ]; then
    echo "### Code Modification Rules"
    echo ""
    echo "- \`const char*\` return → no \`.c_str()\`"
    echo "- \`string\` return → need \`.c_str()\`"
    echo "- \`mprf_p\` for positional format strings"
    echo "- \`grep -F\` source.txt before appending"
    echo "- Compile: \`make -j4\` before commit"
    echo ""
    echo "### Post-task: run \`bash .claude/scripts/verify_zh.sh --profile code\`"
    echo ""
fi

# ── Review context ──
if [ "$TASK_TYPE" = "review" ]; then
    echo "### Review Framework"
    echo ""
    echo "- L1: Protocol/display separation (P0 — functional bugs)"
    echo "- L2: Translation completeness (P0 — user-visible English)"
    echo "- L3: Consistency (P0 — terminology/format)"
    echo "- L4: Content quality (P1)"
    echo "- L5: Database integrity (P1)"
    echo ""
    echo "### Key anti-patterns to check:"
    echo "- \`equip_slot_name()\` used for matching → needs \`_en()\` variant"
    echo "- \`god_name()\` for DB key construction → needs \`_god_name_en()\`"
    echo "- DB query key mismatch: EN key vs ZH code"
    echo ""
    echo "### Post-task: run \`bash .claude/scripts/verify_zh.sh --profile review\`"
    echo ""
fi

echo "---"
echo "Full documentation: CLAUDE.md, docs/glossary.md, docs/decisions.md, .claude/scripts/TOOLCHAIN.md"
