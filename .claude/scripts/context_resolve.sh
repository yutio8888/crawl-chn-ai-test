#!/bin/bash
# Resolve task-relevant terminology and policy references, without duplicating
# policy bodies or adding build, commit, review, or publication requirements.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

usage() {
    cat <<'EOF'
Usage: context_resolve.sh "<task>" [--task-type translate|code|review|general]
                         [--files <paths...>] [--terminology auto|yes|no]
Resolve relevant glossary terms and policy references. Existing current output
can be reused within a task. Pure structural/tooling work can select no terms.
EOF
}
if [[ "${1:-}" == --help || "${1:-}" == -h ]]; then
    usage
    exit 0
fi
TASK="${1:-}"
shift 2>/dev/null || true
TASK_TYPE=""
TERMINOLOGY=auto
FILES=()
while [ $# -gt 0 ]; do
    case "$1" in
        --task-type|--terminology)
            [ $# -ge 2 ] || { echo "ERROR: $1 requires a value" >&2; exit 2; }
            case "$1" in
                --task-type) TASK_TYPE="$2" ;;
                --terminology) TERMINOLOGY="$2" ;;
            esac
            shift 2 ;;
        --files)
            shift
            [ $# -gt 0 ] && [[ "$1" != --* ]] || {
                echo "ERROR: --files requires at least one value" >&2; exit 2;
            }
            while [ $# -gt 0 ] && [[ "$1" != --* ]]; do
                FILES+=("$1"); shift
            done ;;
        *) echo "ERROR: unknown option $1" >&2; exit 2 ;;
    esac
done
if [[ -z "$TASK_TYPE" ]]; then
    if printf '%s\n' "$TASK" | grep -qiE 'review|审查|审核|audit'; then
        TASK_TYPE=review
    elif printf '%s\n' "$TASK ${FILES[*]}" | grep -qiE '\.cc|\.h|T_\(|C_\(|compile|build|代码|编译'; then
        TASK_TYPE=code
    elif printf '%s\n' "$TASK" | grep -qiE 'translat|翻译|译文'; then
        TASK_TYPE=translate
    else
        TASK_TYPE=general
    fi
fi
case "$TASK_TYPE" in
    translate|code|review|general) ;;
    *) echo "ERROR: invalid task type: $TASK_TYPE" >&2; exit 2 ;;
esac
case "$TERMINOLOGY" in
    auto|yes|no) ;;
    *) echo "ERROR: invalid terminology mode: $TERMINOLOGY" >&2; exit 2 ;;
esac

NEEDS_TERMS=0
I18N_POLICY=0
TOOL_POLICY=0
[[ "$TASK_TYPE" != translate ]] || NEEDS_TERMS=1
for file in "${FILES[@]}"; do
    case "${file#./}" in
        crawl-ref/source/dat/i18n/zh/*|crawl-ref/source/dat/database/zh/*|\
        crawl-ref/source/dat/descript/zh/*|docs/glossary.md|docs/glossary.utf8|\
        docs/decisions.md|docs/spell-naming-rules.md)
            NEEDS_TERMS=1; I18N_POLICY=1 ;;
        crawl-ref/source/*.cc|crawl-ref/source/*.h)
            I18N_POLICY=1 ;;
        .claude/scripts/*|.github/*)
            TOOL_POLICY=1 ;;
    esac
done
if [[ "${#FILES[@]}" -eq 0 ]] && printf '%s\n' "$TASK" | grep -qiE 'translat|terminolog|glossary|翻译|译文|术语'; then
    NEEDS_TERMS=1
fi
if printf '%s\n' "$TASK" | grep -qE 'T_\(|C_\('; then
    I18N_POLICY=1
    NEEDS_TERMS=1
fi
case "$TERMINOLOGY" in
    yes) NEEDS_TERMS=1 ;;
    no) NEEDS_TERMS=0 ;;
esac

echo "## Task context"
if [[ "$NEEDS_TERMS" -eq 1 ]]; then
    python3 "$SCRIPT_DIR/glossary_query.py" \
        --task "$TASK" --files "${FILES[@]}" --limit 120
else
    echo "Terminology: not selected; use --terminology yes if this task makes wording judgments."
fi
echo ""
echo "### Applicable policy references"
echo "Read only relevant sections not already present in current task context."
case "$TASK_TYPE" in
    translate)
        echo "- .agents/policies/translation-integrity.md"
        echo "- .agents/policies/asset-ownership.md" ;;
    code)
        echo "- .agents/policies/asset-ownership.md" ;;
    review)
        echo "- .agents/policies/review-contract.md"
        if [[ "$NEEDS_TERMS" -eq 1 ]]; then
            echo "- .agents/policies/translation-integrity.md"
        fi ;;
esac
if [[ "$I18N_POLICY" -eq 1 && "$TASK_TYPE" != translate ]]; then
    echo "- .agents/policies/i18n-safety.md"
fi
if [[ "$TOOL_POLICY" -eq 1 ]]; then
    echo "- .agents/policies/verification-authoring.md"
fi
echo "Verification selection and evidence reuse: docs/zh-testing.md."
echo "Task endpoint, existing authorization, and cleanup: AGENTS.md."
