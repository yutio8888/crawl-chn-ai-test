#!/bin/bash
# context_resolve.sh — Dynamic context injection for agent dispatch.
#
# Given a task description and target files, supplements the active role prompt
# with current-worktree terminology and a focused operational summary.
#
# Usage:
#   bash .claude/scripts/context_resolve.sh "translate god descriptions" \
#       --files crawl-ref/source/dat/database/zh/godspeak.txt
#   bash .claude/scripts/context_resolve.sh "add T_() to beam.cc" \
#       --task-type code

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

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
python3 "$SCRIPT_DIR/glossary_query.py" \
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
    echo "### Review Contract (review-contract-v5)"
    echo ""
    echo "#### Finding severity"
    echo "- **Blocker**: runtime/functional failure, undefined behaviour, protocol or lookup corruption, structural data damage, compilation failure, failure to review the complete prepared diff, an unmet confirmed acceptance criterion within that diff, or interrupted required verification"
    echo "- **Needs Fix**: definite semantic, terminology, accuracy, completeness, or language error without runtime corruption"
    echo "- **Suggestion**: non-required style preference"
    echo "- **Ready for Final Gate**: zero Blocker and zero Needs Fix; suggestions may remain"
    echo "- **Changes Requested**: at least one Needs Fix and no Blocker"
    echo "- **No-Go**: Blocker or incomplete immutable review scope"
    echo "- Plan non-goals do not excuse defects introduced by the prepared diff"
    echo "- A theoretical risk outside the acceptance criteria is non-blocking unless the prepared diff creates or materially worsens it"
    echo "- Prefer deleting unnecessary design, reusing repository mechanisms, and narrowing commitments before adding mechanisms"
    echo ""
    echo "#### Reviewer ownership"
    echo "- \`zh-code-reviewer\`: runtime safety, protocol/display separation, extraction and key coverage, format arguments, TextDB structure, borrowed translation lifetime, variadic calls, movement routing, English morphology, compilation, and scanner warning triage"
    echo "- \`translation-reviewer\`: EN/ZH semantic parity, glossary choice in context, facts and numbers, completeness, natural Chinese, terminology consistency, and character voice"
    echo "- Reviewers require the exact bundle created by \`review_prepare.sh\`, report its glossary SHA-256, and inspect existing development/targeted logs; do not run the final review profile"
    echo ""
    echo "### Code-review anti-patterns to check:"
    echo "- \`equip_slot_name()\` used for matching → needs \`_en()\` variant"
    echo "- \`god_name()\` for DB key construction → needs \`_god_name_en()\`"
    echo "- DB query key mismatch: EN key vs ZH code"
    echo ""
    echo "### Post-task: record immutable readiness for the supplied bundle"
    echo ""
    echo "Only the orchestrator runs the final profile after every routed reviewer is Ready:"
    echo "\`TERM=xterm-256color bash .claude/scripts/review_final_gate.sh <candidate> <target>\`"
    echo ""
fi

echo "---"
echo "Full documentation: AGENTS.md, docs/glossary.md, docs/decisions.md, .claude/scripts/TOOLCHAIN.md"
