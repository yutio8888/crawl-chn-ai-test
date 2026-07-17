#!/bin/bash
# verify_zh.sh — Single-entry verification dispatcher for DCSS Chinese translation.
#
# Usage:
#   verify_zh.sh --profile translation   # Translation / data-file changes
#   verify_zh.sh --profile code           # C++ / i18n code changes
#   verify_zh.sh --profile review         # Pre-merge review
#   verify_zh.sh --profile ci             # CI gate (union of translation + code)
#   verify_zh.sh --profile review --base <rev> --head <rev>
#   verify_zh.sh --profile code --scope changed
#   verify_zh.sh --profile review --full  # full static + full runtime
#   verify_zh.sh --profile review --base <rev> --head <rev> \
#       --routing-sha256 <sha256> --control-plane-sha256 <sha256>
#
# --base and --head bind a run to an immutable commit range. They must be used
# together. For bound runs, the checked-out HEAD must equal --head and glossary
# diff checks automatically compare against --base.
#
# Exit codes:
#   0 — all blocking checks passed
#   1 — one or more blocking checks failed
#   2 — invalid arguments or an invalid commit range

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROFILE=""
SCOPE=""
EXPLICIT_FULL=0
BASE=""
HEAD=""
BASE_SHA=""
HEAD_SHA=""
DIFF_HASH=""
DIFF_SHA256=""
OUTPUT_DIR=".claude/metrics/verify"
ROUTING_SHA256=""
CONTROL_PLANE_SHA256=""
VERIFICATION_CONTRACT="dcss-zh-review-v3"
RUN_DIR=""
RUN_ID=""
REPORT_FILE=""
WRAPPER_FILE=""
METADATA_FILE=""
PHASES_FILE=""
METADATA_INITIALIZED=0
FINALIZED=0
RESULTS=0
STARTED_AT=""
GLOSSARY_SHA256=""
WORKTREE=""
CHANGED_FILES=""
RISK_CPP_I18N=0
RISK_CJK_RUNTIME=0
RISK_MESSAGE_OVERLAY=0

usage() {
    cat <<'EOF'
Usage: verify_zh.sh --profile <translation|code|review|ci> [--scope changed|full]
                    [--base <rev> --head <rev>] [--full]
                    [--output-dir <path>] [--routing-sha256 <sha256>]
                    [--control-plane-sha256 <sha256>]

Profiles:
  translation   Translation / data-file changes
  code          C++ / i18n code changes
  review        Pre-merge review report
  ci            CI gate (translation + code union)

Evidence range:
  --base <rev>  Comparison base; requires --head
  --head <rev>  Candidate commit; requires --base and must be checked out

Scope and runtime:
  --scope changed|full  Task profiles default to changed; review/ci to full
  --full                Alias for --scope full plus the full runtime suite
EOF
    exit 2
}

argument_error() {
    echo "ERROR: $*" >&2
    exit 2
}

# ── Parse arguments ──
while [[ $# -gt 0 ]]; do
    case "$1" in
        --profile|--base|--head|--scope|--output-dir|--routing-sha256|--control-plane-sha256)
            [[ $# -ge 2 && -n "${2:-}" ]] \
                || argument_error "$1 requires a value"
            case "$1" in
                --profile) PROFILE="$2" ;;
                --base) BASE="$2" ;;
                --head) HEAD="$2" ;;
                --scope) SCOPE="$2" ;;
                --output-dir) OUTPUT_DIR="$2" ;;
                --routing-sha256) ROUTING_SHA256="$2" ;;
                --control-plane-sha256) CONTROL_PLANE_SHA256="$2" ;;
            esac
            shift 2
            ;;
        --full)
            SCOPE="full"
            EXPLICIT_FULL=1
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            argument_error "unknown option: $1"
            ;;
    esac
done

[[ -n "$PROFILE" ]] || argument_error "--profile is required"
if [[ -n "$BASE" && -z "$HEAD" ]] || [[ -z "$BASE" && -n "$HEAD" ]]; then
    argument_error "--base and --head must be provided together"
fi

# ── Validate profile and optional immutable range ──
case "$PROFILE" in
    translation|code|review|ci) ;;
    *)
        argument_error "unknown profile '$PROFILE'. Valid: translation, code, review, ci"
        ;;
esac

if [[ -z "$SCOPE" ]]; then
    case "$PROFILE" in
        translation|code) SCOPE="changed" ;;
        review|ci) SCOPE="full" ;;
    esac
fi
case "$SCOPE" in
    changed|full) ;;
    *) argument_error "unknown scope '$SCOPE'. Valid: changed, full" ;;
esac

WORKTREE=$(git rev-parse --show-toplevel 2>/dev/null) \
    || argument_error "verification must run inside a git worktree"
CURRENT_HEAD=$(git rev-parse --verify HEAD 2>/dev/null) \
    || argument_error "the current worktree has no valid HEAD commit"

if [[ -n "$BASE" ]]; then
    BASE_SHA=$(git rev-parse --verify "${BASE}^{commit}" 2>/dev/null) \
        || argument_error "--base does not name a commit: $BASE"
    HEAD_SHA=$(git rev-parse --verify "${HEAD}^{commit}" 2>/dev/null) \
        || argument_error "--head does not name a commit: $HEAD"
    if [[ "$CURRENT_HEAD" != "$HEAD_SHA" ]]; then
        argument_error "current worktree HEAD ($CURRENT_HEAD) does not equal --head ($HEAD_SHA)"
    fi
    if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
        argument_error "bound verification requires a clean worktree"
    fi
    DIFF_HASH=$(git diff --binary "$BASE_SHA..$HEAD_SHA" | git hash-object --stdin)
    DIFF_SHA256=$(git diff --no-ext-diff --no-textconv --binary --full-index \
        "$BASE_SHA..$HEAD_SHA" -- | sha256sum | awk '{print $1}')
    export GLOSSARY_DIFF_BASE="$BASE_SHA"
fi

for digest_name in ROUTING_SHA256 CONTROL_PLANE_SHA256; do
    digest_value="${!digest_name}"
    if [[ -n "$digest_value" && ! "$digest_value" =~ ^[0-9a-f]{64}$ ]]; then
        argument_error "${digest_name,,} must be a lowercase SHA-256"
    fi
done

# The changed set is used only to narrow checks that accept explicit file
# lists and to select risk tests. Global integrity and policy gates remain full.
if [[ -n "$BASE_SHA" ]]; then
    CHANGED_FILES=$(git diff --name-only "$BASE_SHA..$HEAD_SHA")
else
    CHANGED_FILES=$({
        git diff --name-only HEAD
        git ls-files --others --exclude-standard
    } | LC_ALL=C sort -u)
fi
export ZH_VERIFY_SCOPE="$SCOPE"
export ZH_VERIFY_CHANGED_FILES="$CHANGED_FILES"

if [[ -n "$CHANGED_FILES" ]]; then
    while IFS= read -r changed_file; do
        [[ -n "$changed_file" ]] || continue
        case "$changed_file" in
            crawl-ref/source/*.c|crawl-ref/source/*.cc|crawl-ref/source/*.cpp|\
            crawl-ref/source/*.cxx|crawl-ref/source/*.h|crawl-ref/source/*.hh|\
            crawl-ref/source/*.hpp|crawl-ref/source/*.hxx)
                if [[ -n "$BASE_SHA" ]]; then
                    diff_text=$(git diff -U0 "$BASE_SHA..$HEAD_SHA" -- "$changed_file" || true)
                elif git ls-files --error-unmatch -- "$changed_file" >/dev/null 2>&1; then
                    diff_text=$(git diff -U0 HEAD -- "$changed_file" || true)
                else
                    # git diff omits untracked files; represent the new file as
                    # additions so risk classification sees its i18n content.
                    diff_text=$(sed 's/^/+/' -- "$changed_file" 2>/dev/null || true)
                fi
                if grep -Eq '^[+-].*(T_|C_|N_|i18n|language|translated_)' <<<"$diff_text"; then
                    RISK_CPP_I18N=1
                fi
                ;;
        esac
        case "$changed_file" in
            .claude/data/message-overlay/*|\
            .claude/scripts/*message_overlay*|\
            .claude/scripts/audit_monspell_behavior.py|\
            .claude/scripts/tests/test_message_overlay.py|\
            .claude/scripts/tests/test_audit_monspell_behavior.py|\
            docs/textdb-i18n-*|\
            crawl-ref/source/database.cc|crawl-ref/source/database.h|\
            crawl-ref/source/fork-message-overlay.*|\
            crawl-ref/source/mon-cast.cc|crawl-ref/source/mon-cast-target.h|\
            crawl-ref/source/mon-cast-message-keys.*|\
            crawl-ref/source/mon-speak.cc|crawl-ref/source/mon-speak.h|\
            crawl-ref/source/catch2-tests/monspell_candidate_artifact.*|\
            crawl-ref/source/catch2-tests/test_fork_message_overlay.cc|\
            crawl-ref/source/catch2-tests/test_mon_cast_candidate_dump.cc|\
            crawl-ref/source/catch2-tests/test_mon_cast_target.cc|\
            crawl-ref/source/mon-cast-target.cc|\
            crawl-ref/source/mon-cast.h|\
            crawl-ref/source/mon-util.cc|crawl-ref/source/mon-util.h|\
            crawl-ref/source/stringutil.cc|crawl-ref/source/stringutil.h|\
            crawl-ref/source/catch2-tests/test_mon_cast_message_keys.cc|\
            crawl-ref/source/catch2-tests/test_textdb_phase0.cc|\
            dat/database/monspell.txt|\
            dat/database/zh/monspell.txt)
                RISK_MESSAGE_OVERLAY=1
                ;;
        esac
        case "$changed_file" in
            *font*|*Font*|*cjk*|*CJK*|*unicode*|*char-width*|*tile*font*|\
            crawl-ref/source/tiles*.cc|crawl-ref/source/tiles*.h|\
            crawl-ref/source/test/zh_runtime.lua|test/baselines/zh/*)
                RISK_CJK_RUNTIME=1
                ;;
        esac
    done <<< "$CHANGED_FILES"
fi

GLOSSARY_FILE="$WORKTREE/docs/glossary.md"
[[ -f "$GLOSSARY_FILE" ]] \
    || argument_error "glossary not found: $GLOSSARY_FILE"
GLOSSARY_SHA256=$(sha256sum "$GLOSSARY_FILE" | awk '{print $1}')

# ── Setup per-run evidence ──
STARTED_AT=$(date -Iseconds)
RUN_STAMP=$(date '+%Y%m%dT%H%M%S%N%z')
RUN_ID="${RUN_STAMP}-${$}-${CURRENT_HEAD:0:12}"
RUN_DIR="$OUTPUT_DIR/$RUN_ID"
REPORT_FILE="$RUN_DIR/verify.log"
METADATA_FILE="$RUN_DIR/metadata.json"
PHASES_FILE="$RUN_DIR/phases.tsv"
WRAPPER_FILE="$OUTPUT_DIR/verify-${PROFILE}-${RUN_ID}.log"
mkdir -p "$RUN_DIR"
: > "$PHASES_FILE"

# Write metadata through a sibling temporary file and atomically replace the
# public file. Arguments are JSON-encoded by Python, not interpolated into JSON.
write_metadata() {
    local status="$1"
    local completed_at="$2"
    local failures="$3"
    python3 - \
        "$METADATA_FILE" "$status" "$PROFILE" "$BASE_SHA" "$HEAD_SHA" \
        "$DIFF_HASH" "$DIFF_SHA256" "$GLOSSARY_SHA256" "$WORKTREE" \
        "$STARTED_AT" "$completed_at" "$failures" "$RUN_ID" "$SCOPE" \
        "$ROUTING_SHA256" "$CONTROL_PLANE_SHA256" "$VERIFICATION_CONTRACT" \
        "$RISK_CPP_I18N" "$RISK_CJK_RUNTIME" "$RISK_MESSAGE_OVERLAY" \
        "$EXPLICIT_FULL" "$PHASES_FILE" "$REPORT_FILE" <<'PY'
import json
import os
import sys

(
    path, status, profile, base, head, diff_hash, diff_sha256,
    glossary_sha256, worktree, started_at, completed_at, failures, run_id,
    scope, routing_sha256, control_plane_sha256, verification_contract,
    risk_cpp_i18n, risk_cjk_runtime, risk_message_overlay, explicit_full,
    phases_path, report_path,
) = sys.argv[1:]
phases = []
if os.path.isfile(phases_path):
    with open(phases_path, encoding="utf-8") as stream:
        for line in stream:
            line = line.rstrip("\n")
            if not line:
                continue
            phase_id, required, phase_status, exit_code = line.split("\t")
            phases.append({
                "id": phase_id,
                "required": required == "1",
                "status": phase_status,
                "exit_code": int(exit_code),
            })
artifacts = []
if os.path.isfile(report_path):
    import hashlib
    data = open(report_path, "rb").read()
    artifacts.append({
        "path": "verify.log",
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    })
payload = {
    "schema_version": 3,
    "verification_contract": verification_contract,
    "run_id": run_id,
    "status": status,
    "profile": profile,
    "scope": scope,
    "base": base or None,
    "head": head or None,
    "diff_hash": diff_hash or None,
    "diff_sha256": diff_sha256 or None,
    "glossary_sha256": glossary_sha256,
    "routing_sha256": routing_sha256 or None,
    "control_plane_sha256": control_plane_sha256 or None,
    "risk_cpp_i18n": risk_cpp_i18n == "1",
    "risk_cjk_runtime": risk_cjk_runtime == "1",
    "risk_message_overlay": risk_message_overlay == "1",
    "runtime_mode": ("full" if explicit_full == "1" else
                     "catch2" if profile in ("review", "ci") or risk_cjk_runtime == "1"
                     else "none"),
    "phases": phases,
    "artifacts": artifacts,
    "worktree": worktree,
    "started_at": started_at,
    "completed_at": completed_at or None,
    "failures": int(failures),
}
directory = os.path.dirname(path)
temporary = os.path.join(directory, f".{os.path.basename(path)}.tmp.{os.getpid()}")
with open(temporary, "w", encoding="utf-8") as stream:
    json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
    stream.write("\n")
    stream.flush()
    os.fsync(stream.fileno())
os.replace(temporary, path)
PY
}

write_wrapper() {
    local status="$1"
    local completed_at="$2"
    local temporary="${WRAPPER_FILE}.tmp.${$}"
    {
        echo "run_id=$RUN_ID"
        echo "profile=$PROFILE"
        echo "status=$status"
        echo "failures=$RESULTS"
        echo "started_at=$STARTED_AT"
        echo "completed_at=$completed_at"
        echo "report=$REPORT_FILE"
        echo "metadata=$METADATA_FILE"
        echo "Summary: $RESULTS blocking failure(s)"
        echo "=== verify_zh.sh complete ==="
    } > "$temporary"
    mv -f "$temporary" "$WRAPPER_FILE"
}

finalize_unexpected_exit() {
    local rc=$?
    if [[ "$METADATA_INITIALIZED" -eq 1 && "$FINALIZED" -eq 0 ]]; then
        set +e
        [[ "$RESULTS" -gt 0 ]] || RESULTS=1
        local completed_at
        completed_at=$(date -Iseconds)
        write_metadata "fail" "$completed_at" "$RESULTS"
        write_wrapper "fail" "$completed_at"
    fi
    return "$rc"
}

handle_signal() {
    local signal_rc="$1"
    set +e
    [[ "$RESULTS" -gt 0 ]] || RESULTS=1
    local completed_at
    completed_at=$(date -Iseconds)
    write_metadata "interrupted" "$completed_at" "$RESULTS"
    write_wrapper "interrupted" "$completed_at"
    FINALIZED=1
    trap - EXIT INT TERM HUP
    exit "$signal_rc"
}

write_metadata "running" "" 0
METADATA_INITIALIZED=1
trap finalize_unexpected_exit EXIT
trap 'handle_signal 130' INT
trap 'handle_signal 143' TERM
trap 'handle_signal 129' HUP

# ── Run phase function ──
run_phase() {
    local phase_id="$1" required="$2" label="$3"
    shift 3
    local phase_rc=0

    echo "=== $label ==="
    if "$@" 2>&1; then
        echo "RESULT: PASS"
        printf '%s\t%s\tpass\t0\n' "$phase_id" "$required" >> "$PHASES_FILE"
    else
        phase_rc=$?
        echo "RESULT: FAIL (exit $phase_rc)"
        printf '%s\t%s\tfail\t%s\n' "$phase_id" "$required" "$phase_rc" >> "$PHASES_FILE"
    fi
    echo ""
    return "$phase_rc"
}

# ── Dispatch by profile ──
{
    echo "=== verify_zh.sh --profile $PROFILE @ $STARTED_AT ==="
    echo "Run ID: $RUN_ID"
    echo "Scope: $SCOPE"
    echo "Risk: cpp_i18n=$RISK_CPP_I18N cjk_runtime=$RISK_CJK_RUNTIME message_overlay=$RISK_MESSAGE_OVERLAY explicit_full=$EXPLICIT_FULL"
    if [[ -n "$BASE_SHA" ]]; then
        echo "Base: $BASE_SHA"
        echo "Head: $HEAD_SHA"
        echo "Diff hash: $DIFF_HASH"
        echo "Diff SHA-256: $DIFF_SHA256"
    fi
    echo "Glossary SHA-256: $GLOSSARY_SHA256"
    echo ""

    run_phase "policy-sync" 1 "Agent/Skill policy synchronization" \
        python3 "$SCRIPT_DIR/check_agent_policies.py" --root "$WORKTREE" \
        || RESULTS=$((RESULTS + 1))

    # ── source-db-static: REQUIRED for ALL profiles, NOT bypassable ──
    run_source_db_static() {
        local rc=0
        python3 "$SCRIPT_DIR/scan_i18n.py" source-db-structure \
            --source-txt "$WORKTREE/crawl-ref/source/dat/i18n/zh/source.txt" \
            --exit-nonzero-if-issues || rc=$?
        python3 "$SCRIPT_DIR/scan_i18n.py" source-key-collisions \
            --source-txt "$WORKTREE/crawl-ref/source/dat/i18n/zh/source.txt" || rc=$?
        python3 "$SCRIPT_DIR/i18n_extract.py" validate "$WORKTREE/crawl-ref/source" \
            --source-txt "$WORKTREE/crawl-ref/source/dat/i18n/zh/source.txt" || rc=$?
        return "$rc"
    }
    run_phase "source-db-static" 1 "Source/DB static integrity" \
        run_source_db_static || RESULTS=$((RESULTS + 1))

    case "$PROFILE" in
        translation)
            run_phase "translation-static" 1 "Translation verification (post-translator.sh)" \
                bash "$SCRIPT_DIR/post-translator.sh" || RESULTS=$((RESULTS + 1))
            ;;
        code)
            run_phase "code-static" 1 "Code verification (post-coder.sh)" \
                bash "$SCRIPT_DIR/post-coder.sh" || RESULTS=$((RESULTS + 1))
            ;;
        review)
            run_phase "review-static" 1 "Review verification (post-reviewer.sh)" \
                bash "$SCRIPT_DIR/post-reviewer.sh" || RESULTS=$((RESULTS + 1))
            ;;
        ci)
            # --profile ci is truly static: no make, no runtime execution.
            # source-db-static (run above) + translation-static + code-static.
            run_phase "translation-static" 1 "Translation verification (static)" \
                bash "$SCRIPT_DIR/post-translator.sh" || RESULTS=$((RESULTS + 1))
            run_phase "code-static" 1 "Code verification (post-coder.sh, static)" \
                bash "$SCRIPT_DIR/post-coder.sh" || RESULTS=$((RESULTS + 1))
            ;;
    esac

    run_message_overlay_static() {
        if [[ -n "${ZH_VERIFY_MESSAGE_OVERLAY_STATIC_COMMAND:-}" ]]; then
            bash -c "$ZH_VERIFY_MESSAGE_OVERLAY_STATIC_COMMAND"
            return
        fi
        python3 "$SCRIPT_DIR/tests/test_message_overlay.py" \
            && python3 "$SCRIPT_DIR/tests/test_audit_monspell_behavior.py" \
            && python3 "$SCRIPT_DIR/generate_message_overlay.py" \
                --manifest .claude/data/message-overlay/monspell.json \
                --inventory .claude/data/message-overlay/monspell-phase0-inventory.json \
                --check crawl-ref/source/fork-message-overlay.generated.inc \
            && python3 "$SCRIPT_DIR/audit_message_overlay.py" \
                --manifest .claude/data/message-overlay/monspell.json \
                --inventory .claude/data/message-overlay/monspell-phase0-inventory.json \
                --sidecar crawl-ref/source/fork-message-overlay.generated.inc
    }
    run_message_overlay_catch2() {
        if [[ -n "${ZH_VERIFY_MESSAGE_OVERLAY_CATCH2_COMMAND:-}" ]]; then
            bash -c "$ZH_VERIFY_MESSAGE_OVERLAY_CATCH2_COMMAND"
            return
        fi
        make -C crawl-ref/source catch2-tests-executable \
            STDFLAG=-std=c++14 -j4 \
            && (cd crawl-ref/source \
                && ./catch2-tests-executable \
                    '[message-overlay]' --reporter compact)
    }

    run_phase "message-overlay-static" 1 "TextDB message overlay static audit" \
        run_message_overlay_static || RESULTS=$((RESULTS + 1))
    if [[ "$RISK_MESSAGE_OVERLAY" -eq 1 ]]; then
        run_phase "message-overlay-catch2" 1 "Risk gate: TextDB message overlay Catch2" \
            run_message_overlay_catch2 || RESULTS=$((RESULTS + 1))
    fi


    run_incremental_build() {
        if [[ -n "${ZH_VERIFY_BUILD_COMMAND:-}" ]]; then
            bash -c "$ZH_VERIFY_BUILD_COMMAND"
        else
            make -C crawl-ref/source -j4 STDFLAG=-std=c++14
        fi
    }
    run_zh_smoke() {
        if [[ -n "${ZH_VERIFY_SMOKE_COMMAND:-}" ]]; then
            bash -c "$ZH_VERIFY_SMOKE_COMMAND"
        else
            bash "$SCRIPT_DIR/smoke_test.sh"
        fi
    }
    run_runtime() {
        local mode="$1"
        if [[ -n "${ZH_VERIFY_RUNTIME_COMMAND:-}" ]]; then
            bash -c "$ZH_VERIFY_RUNTIME_COMMAND $mode"
        else
            bash "$SCRIPT_DIR/post_zh_runtime.sh" "$mode"
        fi
    }

    if [[ "$RISK_CPP_I18N" -eq 1 && "$PROFILE" != ci ]]; then
        # ci profile is truly static — no make, no runtime
        run_phase "cpp-build" 1 "Risk gate: incremental C++ build" run_incremental_build \
            || RESULTS=$((RESULTS + 1))
        run_phase "zh-smoke" 1 "Risk gate: ZH smoke" run_zh_smoke \
            || RESULTS=$((RESULTS + 1))
    fi

    if [[ "$EXPLICIT_FULL" -eq 1 ]]; then
        run_phase "zh-runtime-full" 1 "Risk gate: full ZH runtime" run_runtime full \
            || RESULTS=$((RESULTS + 1))
    elif [[ "$PROFILE" != ci && ( "$RISK_CJK_RUNTIME" -eq 1 || "$PROFILE" == review ) ]]; then
        # post_zh_runtime.sh calls its build-and-run Catch2 path "catch2";
        # its "fast" mode only re-aggregates an existing evidence directory.
        # ci profile is truly static — skip runtime entirely.
        run_phase "zh-runtime-catch2" 1 "Risk gate: fast ZH runtime" run_runtime catch2 \
            || RESULTS=$((RESULTS + 1))
    fi

    echo "Summary: $RESULTS blocking failure(s)"
    echo "=== verify_zh.sh complete ==="
} > "$REPORT_FILE" 2>&1

# A bound review is only immutable if the checkout and terminology source stay
# unchanged for the entire run, not merely at startup.
EVIDENCE_DRIFT=0
FINAL_HEAD=$(git rev-parse --verify HEAD 2>/dev/null || true)
FINAL_GLOSSARY_SHA256=$(sha256sum "$GLOSSARY_FILE" 2>/dev/null | awk '{print $1}')
if [[ -n "$HEAD_SHA" && "$FINAL_HEAD" != "$HEAD_SHA" ]]; then
    printf 'ERROR: worktree HEAD changed during verification: %s -> %s\n' \
        "$HEAD_SHA" "${FINAL_HEAD:-<missing>}" >> "$REPORT_FILE"
    EVIDENCE_DRIFT=1
fi
if [[ "$FINAL_GLOSSARY_SHA256" != "$GLOSSARY_SHA256" ]]; then
    printf 'ERROR: glossary changed during verification: %s -> %s\n' \
        "$GLOSSARY_SHA256" "${FINAL_GLOSSARY_SHA256:-<missing>}" >> "$REPORT_FILE"
    EVIDENCE_DRIFT=1
fi
if [[ "$EVIDENCE_DRIFT" -ne 0 ]]; then
    RESULTS=$((RESULTS + 1))
fi

# ── Finalize evidence and report ──
COMPLETED_AT=$(date -Iseconds)
if [[ "$RESULTS" -gt 0 ]]; then
    FINAL_STATUS="fail"
    FINAL_RC=1
else
    FINAL_STATUS="pass"
    FINAL_RC=0
fi
write_metadata "$FINAL_STATUS" "$COMPLETED_AT" "$RESULTS"
write_wrapper "$FINAL_STATUS" "$COMPLETED_AT"
FINALIZED=1

echo ""
echo "=== verify-zh --profile $PROFILE ==="
echo "Run ID: $RUN_ID"
echo "Report: $REPORT_FILE"
echo "Metadata: $METADATA_FILE"
echo "Wrapper: $WRAPPER_FILE"
echo "Failures: $RESULTS"
echo ""

exit "$FINAL_RC"
