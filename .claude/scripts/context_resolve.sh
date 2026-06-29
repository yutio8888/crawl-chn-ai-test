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
FILES=""

while [ $# -gt 0 ]; do
    case "$1" in
        --task-type) TASK_TYPE="$2"; shift 2 ;;
        --files) FILES="$2"; shift 2 ;;
        *) shift ;;
    esac
done

# Detect task type from keywords if not specified
if [ -z "$TASK_TYPE" ]; then
    if echo "$TASK $FILES" | grep -qiE 'translate|翻译|txt$|source\.txt|descript|database'; then
        TASK_TYPE="translate"
    elif echo "$TASK $FILES" | grep -qiE '\.cc$|\.h$|T_\(|mprf|compile|build|bug|fix'; then
        TASK_TYPE="code"
    elif echo "$TASK $FILES" | grep -qiE 'review|审查|audit|check'; then
        TASK_TYPE="review"
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

# ── Translation context ──
if [ "$TASK_TYPE" = "translate" ]; then
    echo "### Translation Rules"
    echo ""
    echo "- No articles (a/an/the), no plural markers"
    echo "- Adverbs BEFORE verbs"
    echo "- Add 了 after verbs for completed actions"
    echo "- Preserve all @keyword@, w:N weights, %%%% separators"
    echo ""

    # Detect domain-specific terminology
    if echo "$FILES $TASK" | grep -qi 'god\|神\|trog\|zin\|sif'; then
        echo "### God Names (from DECISIONS.md)"
        echo ""
        echo "| EN | ZH |"
        echo "|----|-----|"
        echo "| Sif Muna | 西芙·穆娜 |"
        echo "| Trog | 特洛格 |"
        echo "| Kikubaaqudgha | 奇库巴库哈 |"
        echo "| The Shining One | 光辉者 |"
        echo "| Zin | 辛 |"
        echo "| Vehumet | 维胡梅特 |"
        echo "| Xom | 佐姆 |"
        echo ""
    fi

    if echo "$FILES $TASK" | grep -qi 'spell\|magic\|法术\|咒\|魔法'; then
        echo "### Magic Terminology"
        echo ""
        echo "- spellpower = 法术威力 (NOT 法力 — that's MP)"
        echo "- Conjuration = 咒法系"
        echo "- Hexes = 诅咒系"
        echo "- Summoning = 召唤系"
        echo "- Necromancy = 死灵术"
        echo ""
    fi

    if echo "$FILES $TASK" | grep -qi 'monster\|creature\|怪物\|dragon\|demon\|undead'; then
        echo "### Monster Terminology"
        echo ""
        echo "- monster = 怪物"
        echo "- demon = 恶魔"
        echo "- undead = 亡灵"
        echo "- dragon = 龙"
        echo "- flee = 逃跑"
        echo ""
    fi

    echo "### Post-task: run \`bash .claude/scripts/post-translator.sh\`"
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
    echo "### Post-task: run \`bash .claude/scripts/post-coder.sh\`"
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
    echo "### Post-task: run \`bash .claude/scripts/post-reviewer.sh\`"
    echo ""
fi

echo "---"
echo "Full documentation: CLAUDE.md, docs/decisions.md, .claude/scripts/TOOLCHAIN.md"
