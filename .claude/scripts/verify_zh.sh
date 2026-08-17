#!/bin/bash
# verify_zh.sh — Single-entry verification dispatcher for DCSS Chinese translation.
#
# Usage:
#   verify_zh.sh --profile translation   # Translation / data-file changes
#   verify_zh.sh --profile code           # C++ / i18n code changes
#   verify_zh.sh --profile review         # Final-gate internal profile
#   verify_zh.sh --profile ci             # CI gate (union of translation + code)
#   review_final_gate.sh <candidate> <target>  # Supported review entry point
#   verify_zh.sh --profile code --scope changed
#   verify_zh.sh --profile review --base <rev> --head <rev> \
#       --routing-sha256 <sha256> --control-plane-sha256 <sha256>
#   verify_zh.sh --profile review --base <rev> --head <rev> \
#       --github-actions-proof <proof.json> --github-proof-artifact <name> \
#       --github-externalized-phases <csv>
#
# --base and --head bind a run to an immutable commit range. They must be used
# together. For bound runs, the checked-out HEAD must equal --head and glossary
# diff checks automatically compare against --base.
#
# --github-actions-proof switches an internal final-gate review run into
# external-CI mode: the listed externalized phases are recorded as proven by a
# bound GitHub Actions proof instead of running locally. Only review_bundle.py
# may pass this flag; every other call uses the default fully local mode.
#
# Exit codes:
#   0 — all blocking checks passed
#   1 — one or more blocking checks failed
#   2 — invalid arguments or an invalid commit range

set -euo pipefail
export GIT_NO_REPLACE_OBJECTS=1
unset ZH_VERIFY_AUDIT_ROOT ZH_VERIFY_AUDIT_COMMIT
unset ZH_VERIFY_CONTROL_ROOT ZH_VERIFY_CONTROL_COMMIT

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
GITHUB_ACTIONS_PROOF=""
GITHUB_ACTIONS_RUN=""
GITHUB_PROOF_ARTIFACT=""
GITHUB_EXTERNALIZED_PHASES=""
VERIFICATION_CONTRACT="dcss-zh-review-v5"
RUN_DIR=""
RUN_ID=""
REPORT_FILE=""
WRAPPER_FILE=""
METADATA_FILE=""
PHASES_FILE=""
ITEM_INVENTORY_FILE=""
CHARACTER_INVENTORY_FILE=""
GOD_INVENTORY_FILE=""
SPECIES_BACKGROUND_INVENTORY_FILE=""
MONSTER_INVENTORY_FILE=""
WORLD_INVENTORY_FILE=""
METADATA_INITIALIZED=0
FINALIZED=0
RESULTS=0
STARTED_AT=""
GLOSSARY_SHA256=""
WORKTREE=""
CHANGED_FILES=""
RISK_CPP_I18N=0
RISK_CJK_RUNTIME=0
RISK_ZH_TEST_RUNTIME=0
RISK_MESSAGE_OVERLAY=0

usage() {
    cat <<'EOF'
Usage: verify_zh.sh --profile <translation|code|review|ci> [--scope changed|full]
                    [--base <rev> --head <rev>] [--full]
                    [--output-dir <path>] [--routing-sha256 <sha256>]
                    [--control-plane-sha256 <sha256>]
                    [--github-actions-proof <proof.json>]
                    [--github-actions-run <run-id>]
                    [--github-proof-artifact <name>]
                    [--github-externalized-phases <csv>]

Profiles:
  translation   Translation / data-file changes
  code          C++ / i18n code changes
  review        Final-gate internal review report; use review_final_gate.sh
  ci            CI gate (translation + code union)

Evidence range:
  --base <rev>  Comparison base; requires --head
  --head <rev>  Candidate commit; requires --base and must be checked out

Scope and runtime:
  --scope changed|full  Task profiles default to changed; review/ci to full
  --full                Alias for --scope full plus the full runtime suite

External CI (review profile only, invoked by review_bundle.py):
  --github-actions-proof <path>       Canonical github-actions-proof.json
  --github-actions-run <run-id>       GitHub Actions run id (audit log only)
  --github-proof-artifact <name>      Proof artifact name inside the run dir
  --github-externalized-phases <csv>  Phases replaced by the bound proof
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
        --profile|--base|--head|--scope|--output-dir|--routing-sha256|--control-plane-sha256|--github-actions-proof|--github-actions-run|--github-proof-artifact|--github-externalized-phases)
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
                --github-actions-proof) GITHUB_ACTIONS_PROOF="$2" ;;
                --github-actions-run) GITHUB_ACTIONS_RUN="$2" ;;
                --github-proof-artifact) GITHUB_PROOF_ARTIFACT="$2" ;;
                --github-externalized-phases) GITHUB_EXTERNALIZED_PHASES="$2" ;;
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
[[ "$WORKTREE" = /* ]] \
    || argument_error "Git worktree top-level must be an absolute path"
WORKTREE=$(cd "$WORKTREE" && pwd -P) \
    || argument_error "Git worktree top-level cannot be resolved"
CWD_TOP=$(git -C "$(pwd -P)" rev-parse --show-toplevel 2>/dev/null) \
    || argument_error "current working directory is not inside a Git worktree"
CWD_TOP=$(cd "$CWD_TOP" && pwd -P) \
    || argument_error "current working directory Git top-level cannot be resolved"
[[ "$CWD_TOP" == "$WORKTREE" ]] \
    || argument_error "current working directory Git top-level does not match worktree"
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
    if ! git merge-base --is-ancestor "$BASE_SHA" "$HEAD_SHA"; then
        argument_error "--base must be an ancestor of --head"
    fi
    DIFF_HASH=$(git diff --binary "$BASE_SHA..$HEAD_SHA" | git hash-object --stdin)
    DIFF_SHA256=$(git diff --no-ext-diff --no-textconv --binary --full-index \
        "$BASE_SHA..$HEAD_SHA" -- | sha256sum | awk '{print $1}')
    export GLOSSARY_DIFF_BASE="$BASE_SHA"
    export ZH_VERIFY_AUDIT_ROOT="$WORKTREE"
    export ZH_VERIFY_AUDIT_COMMIT="$HEAD_SHA"
    CONTROL_ROOT=$(git -C "$SCRIPT_DIR/../.." rev-parse --show-toplevel \
        2>/dev/null) \
        || argument_error "trusted control scripts are not inside a Git worktree"
    [[ "$CONTROL_ROOT" = /* ]] \
        || argument_error "trusted control Git top-level must be absolute"
    CONTROL_ROOT=$(cd "$CONTROL_ROOT" && pwd -P) \
        || argument_error "trusted control Git top-level cannot be resolved"
    CONTROL_HEAD=$(git -C "$CONTROL_ROOT" rev-parse --verify HEAD \
        2>/dev/null) \
        || argument_error "trusted control worktree has no valid HEAD"
    if [[ "$CONTROL_HEAD" != "$BASE_SHA" && "$CONTROL_HEAD" != "$HEAD_SHA" ]]; then
        argument_error \
            "trusted control HEAD must equal bound base or head: $CONTROL_HEAD"
    fi
    if [[ -n "$(git -C "$CONTROL_ROOT" status --porcelain \
        --untracked-files=all)" ]]; then
        argument_error "bound verification requires a clean trusted control worktree"
    fi
    export ZH_VERIFY_CONTROL_ROOT="$CONTROL_ROOT"
    export ZH_VERIFY_CONTROL_COMMIT="$CONTROL_HEAD"
fi

for digest_name in ROUTING_SHA256 CONTROL_PLANE_SHA256; do
    digest_value="${!digest_name}"
    if [[ -n "$digest_value" && ! "$digest_value" =~ ^[0-9a-f]{64}$ ]]; then
        digest_label=$(printf '%s' "$digest_name" | tr '[:upper:]' '[:lower:]')
        argument_error "$digest_label must be a lowercase SHA-256"
    fi
done

# ── External GitHub Actions proof mode (review profile only) ──
# review_bundle.py is the only sanctioned caller. Default behaviour is the
# fully local profile; proof mode is explicit and fail-closed.
is_externalized_phase() {
    local padded=",${GITHUB_EXTERNALIZED_PHASES},"
    [[ "$padded" == *",$1,"* ]]
}
if [[ -n "$GITHUB_ACTIONS_PROOF" ]]; then
    [[ "$PROFILE" == review ]] \
        || argument_error "--github-actions-proof requires --profile review"
    [[ -n "$BASE" && -n "$HEAD" ]] \
        || argument_error "--github-actions-proof requires a bound --base/--head review run"
    [[ -f "$GITHUB_ACTIONS_PROOF" && ! -L "$GITHUB_ACTIONS_PROOF" ]] \
        || argument_error "GitHub Actions proof file is missing or unsafe: $GITHUB_ACTIONS_PROOF"
    [[ -n "$GITHUB_PROOF_ARTIFACT" && "$GITHUB_PROOF_ARTIFACT" != */* ]] \
        || argument_error "--github-proof-artifact must name a single artifact file"
    python3 - "$GITHUB_ACTIONS_PROOF" "$HEAD_SHA" <<'PY' || argument_error "GitHub Actions proof failed validation"
import json
import sys
import re

path, head_sha = sys.argv[1:]
try:
    with open(path, encoding="utf-8") as stream:
        proof = json.load(stream)
except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
    raise SystemExit(f"proof JSON is invalid: {exc}")
if not isinstance(proof, dict):
    raise SystemExit("proof must be a JSON object")
for key in ("schema", "repository", "head_sha", "status", "conclusion",
            "required_jobs"):
    if key not in proof:
        raise SystemExit(f"proof is missing {key}")
if not isinstance(proof["head_sha"], str) \
        or not re.fullmatch(r"[0-9a-f]{40,64}", proof["head_sha"]):
    raise SystemExit("proof head_sha is invalid")
if proof["head_sha"] != head_sha:
    raise SystemExit("proof head_sha does not match the bound head")
if proof["status"] != "completed" or proof["conclusion"] != "success":
    raise SystemExit("proof run is not completed/success")
if not isinstance(proof["required_jobs"], list) or not proof["required_jobs"]:
    raise SystemExit("proof required_jobs must be a non-empty list")
if not isinstance(proof["repository"], str) or not proof["repository"]:
    raise SystemExit("proof repository is invalid")
PY
fi
if [[ -n "$GITHUB_ACTIONS_RUN" && -z "$GITHUB_ACTIONS_PROOF" ]]; then
    argument_error "--github-actions-run requires --github-actions-proof"
fi
if [[ -n "$GITHUB_ACTIONS_PROOF" && -z "$GITHUB_ACTIONS_RUN" ]]; then
    argument_error "--github-actions-proof requires --github-actions-run"
fi

# The changed set is used only to narrow checks that accept explicit file
# lists and to select risk tests. Global integrity and policy gates remain full.
if [[ -n "$BASE_SHA" ]]; then
    CHANGED_FILES=$(git diff --no-renames --name-only "$BASE_SHA..$HEAD_SHA")
else
    CHANGED_FILES=$({
        git diff --no-renames --name-only HEAD
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
                    diff_text=$(git diff --no-renames -U0 \
                        "$BASE_SHA..$HEAD_SHA" -- "$changed_file" || true)
                elif git ls-files --error-unmatch -- "$changed_file" >/dev/null 2>&1; then
                    diff_text=$(git diff --no-renames -U0 HEAD \
                        -- "$changed_file" || true)
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
            .claude/scripts/decorlines_inventory.py|\
            .claude/scripts/graffiti_inventory.py|\
            .claude/scripts/miscast_inventory.py|\
            .claude/scripts/monflee_inventory.py|\
            .claude/scripts/monspeak_inventory.py|\
            .claude/scripts/shout_inventory.py|\
            .claude/scripts/tests/test_message_overlay.py|\
            .claude/scripts/tests/test_audit_monspell_behavior.py|\
            .claude/scripts/tests/test_decorlines_inventory.py|\
            .claude/scripts/tests/test_graffiti_inventory.py|\
            .claude/scripts/tests/test_miscast_inventory.py|\
            .claude/scripts/tests/test_monflee_inventory.py|\
            .claude/scripts/tests/test_monspeak_inventory.py|\
            .claude/scripts/tests/test_shout_inventory.py|\
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
        case "$changed_file" in
            crawl-ref/source/catch2-tests/test_zh_*.cc|\
            crawl-ref/source/catch2-tests/test_zh_*.h|\
            crawl-ref/source/catch2-tests/test_mon_cast_target.cc)
                RISK_ZH_TEST_RUNTIME=1
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
ITEM_INVENTORY_FILE="$RUN_DIR/item-name-inventory.json"
CHARACTER_INVENTORY_FILE="$RUN_DIR/character-mechanics-inventory.json"
GOD_INVENTORY_FILE="$RUN_DIR/god-inventory.json"
SPECIES_BACKGROUND_INVENTORY_FILE="$RUN_DIR/species-background-inventory.json"
MONSTER_INVENTORY_FILE="$RUN_DIR/monster-name-inventory.json"
WORLD_INVENTORY_FILE="$RUN_DIR/world-inventory.json"
WRAPPER_FILE="$OUTPUT_DIR/verify-${PROFILE}-${RUN_ID}.log"
mkdir -p "$RUN_DIR"
: > "$PHASES_FILE"
if [[ -n "$GITHUB_ACTIONS_PROOF" ]]; then
    cp "$GITHUB_ACTIONS_PROOF" "$RUN_DIR/$GITHUB_PROOF_ARTIFACT"
fi

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
        "$RISK_CPP_I18N" "$RISK_CJK_RUNTIME" "$RISK_ZH_TEST_RUNTIME" \
        "$RISK_MESSAGE_OVERLAY" \
        "$EXPLICIT_FULL" "$PHASES_FILE" "$REPORT_FILE" \
        "$ITEM_INVENTORY_FILE" "$CHARACTER_INVENTORY_FILE" \
        "$GOD_INVENTORY_FILE" "$SPECIES_BACKGROUND_INVENTORY_FILE" \
        "$MONSTER_INVENTORY_FILE" "$WORLD_INVENTORY_FILE" \
        "$GITHUB_PROOF_ARTIFACT" "$GITHUB_ACTIONS_RUN" <<'PY'
import hashlib
import json
import os
import sys

(
    path, status, profile, base, head, diff_hash, diff_sha256,
    glossary_sha256, worktree, started_at, completed_at, failures, run_id,
    scope, routing_sha256, control_plane_sha256, verification_contract,
    risk_cpp_i18n, risk_cjk_runtime, risk_zh_test_runtime,
    risk_message_overlay, explicit_full, phases_path, report_path,
    item_inventory_path, character_inventory_path, god_inventory_path,
    species_background_inventory_path, monster_inventory_path,
    world_inventory_path, gha_proof_artifact, gha_run_id,
) = sys.argv[1:]
phases = []
if os.path.isfile(phases_path):
    with open(phases_path, encoding="utf-8") as stream:
        for line in stream:
            line = line.rstrip("\n")
            if not line:
                continue
            parts = line.split("\t")
            phase_id, required, phase_status, exit_code = parts[0:4]
            phase_source = parts[4] if len(parts) > 4 and parts[4] else "local"
            record = {
                "id": phase_id,
                "required": required == "1",
                "status": phase_status,
                "exit_code": int(exit_code),
            }
            if phase_source != "local":
                record["source"] = phase_source
            phases.append(record)
artifacts = []
if os.path.isfile(report_path):
    data = open(report_path, "rb").read()
    artifacts.append({
        "path": "verify.log",
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    })
for artifact_path, artifact_name in (
    (character_inventory_path, "character-mechanics-inventory.json"),
    (god_inventory_path, "god-inventory.json"),
    (item_inventory_path, "item-name-inventory.json"),
    (monster_inventory_path, "monster-name-inventory.json"),
    (species_background_inventory_path, "species-background-inventory.json"),
    (world_inventory_path, "world-inventory.json"),
):
    if not os.path.isfile(artifact_path):
        continue
    data = open(artifact_path, "rb").read()
    artifacts.append({
        "path": artifact_name,
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
    "risk_zh_test_runtime": risk_zh_test_runtime == "1",
    "risk_message_overlay": risk_message_overlay == "1",
    "runtime_mode": ("full" if explicit_full == "1" else
                     "catch2" if profile != "ci"
                     and (profile == "review" or risk_cjk_runtime == "1"
                          or risk_zh_test_runtime == "1")
                     else "none"),
    "phases": phases,
    "artifacts": artifacts,
    "worktree": worktree,
    "started_at": started_at,
    "completed_at": completed_at or None,
    "failures": int(failures),
}
if gha_proof_artifact:
    proof_path = os.path.join(os.path.dirname(path), gha_proof_artifact)
    if os.path.isfile(proof_path):
        data = open(proof_path, "rb").read()
        artifacts.append({
            "path": gha_proof_artifact,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
        try:
            proof = json.loads(data.decode("utf-8", errors="strict"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SystemExit(f"proof artifact is invalid JSON: {exc}")
        payload["external_ci"] = {
            "schema": proof.get("schema"),
            "repository": proof.get("repository"),
            "run_id": proof.get("run_id"),
            "proof_artifact": gha_proof_artifact,
            "github_actions_run": gha_run_id or None,
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

# Record a phase that was proven by the bound GitHub Actions proof instead of
# running locally. The metadata validator only accepts this source for phases
# listed in the trusted contract's externalizable set, so a caller cannot use
# it to hide missing local evidence.
record_external_phase() {
    local phase_id="$1" required="$2" label="$3"
    echo "=== $label ==="
    echo "EXTERNAL: proven by bound GitHub Actions CI proof (source=github-actions)"
    echo "RESULT: PASS (external)"
    printf '%s\t%s\tpass\t0\tgithub-actions\n' "$phase_id" "$required" >> "$PHASES_FILE"
    echo ""
}

# ── Dispatch by profile ──
{
    echo "=== verify_zh.sh --profile $PROFILE @ $STARTED_AT ==="
    echo "Run ID: $RUN_ID"
    echo "Scope: $SCOPE"
    echo "Risk: cpp_i18n=$RISK_CPP_I18N cjk_runtime=$RISK_CJK_RUNTIME zh_test_runtime=$RISK_ZH_TEST_RUNTIME message_overlay=$RISK_MESSAGE_OVERLAY explicit_full=$EXPLICIT_FULL"
    if [[ -n "$BASE_SHA" ]]; then
        echo "Base: $BASE_SHA"
        echo "Head: $HEAD_SHA"
        echo "Diff hash: $DIFF_HASH"
        echo "Diff SHA-256: $DIFF_SHA256"
    fi
    echo "Glossary SHA-256: $GLOSSARY_SHA256"
    echo ""

    if is_externalized_phase "policy-sync"; then
        record_external_phase "policy-sync" 1 \
            "Agent/Skill policy synchronization (external GitHub Actions evidence)"
    else
        run_phase "policy-sync" 1 "Agent/Skill policy synchronization" \
            python3 "$SCRIPT_DIR/check_agent_policies.py" --root "$WORKTREE" \
            || RESULTS=$((RESULTS + 1))
    fi

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
        python3 "$SCRIPT_DIR/audit_item_name_inventory.py" \
            --output "$ITEM_INVENTORY_FILE" || rc=$?
        python3 "$SCRIPT_DIR/check_default_utf8.py" \
            --defaults-dir "$WORKTREE/crawl-ref/source/dat/defaults" || rc=$?
        return "$rc"
    }
    if is_externalized_phase "source-db-static"; then
        record_external_phase "source-db-static" 1 \
            "Source/DB static integrity (external GitHub Actions evidence)"
    else
        run_phase "source-db-static" 1 "Source/DB static integrity" \
            run_source_db_static || RESULTS=$((RESULTS + 1))
    fi

    case "$PROFILE" in
        translation)
            run_phase "translation-static" 1 "Translation verification (post-translator.sh)" \
                bash "$SCRIPT_DIR/post-translator.sh" || RESULTS=$((RESULTS + 1))
            ;;
        code)
            run_phase "code-static" 1 "Code verification (post-coder.sh)" \
                env ZH_VERIFY_SOURCE_DB_STATIC_COMPLETE=1 \
                    bash "$SCRIPT_DIR/post-coder.sh" || RESULTS=$((RESULTS + 1))
            ;;
        review)
            run_phase "review-static" 1 "Review verification (post-reviewer.sh)" \
                env ZH_VERIFY_SOURCE_DB_STATIC_COMPLETE=1 \
                    bash "$SCRIPT_DIR/post-reviewer.sh" || RESULTS=$((RESULTS + 1))
            run_review_ledgers() {
                local rc=0
                local ledgers=(
                    "$WORKTREE/docs/character-mechanics-review-results.md"
                    "$WORKTREE/docs/god-review-results.md"
                    "$WORKTREE/docs/item-extended-review-results.md"
                    "$WORKTREE/docs/monster-review-results.md"
                    "$WORKTREE/docs/species-background-review-results.md"
                    "$WORKTREE/docs/world-review-results.md"
                )
                PYTHONDONTWRITEBYTECODE=1 \
                    PYTHONPATH="$SCRIPT_DIR${PYTHONPATH:+:$PYTHONPATH}" \
                    python3 - "$WORKTREE" "${ledgers[@]}" <<'PY' || return $?
import sys
from pathlib import Path

from review_bundle import _path_under_checkout

checkout = Path(sys.argv[1])
for supplied in sys.argv[2:]:
    _path_under_checkout(checkout, supplied, "review ledger")
PY
                python3 "$SCRIPT_DIR/audit_character_mechanics_inventory.py" \
                    --review-results \
                    "${ledgers[0]}" \
                    --output "$CHARACTER_INVENTORY_FILE" || rc=$?
                python3 "$SCRIPT_DIR/audit_god_inventory.py" \
                    --review-results "${ledgers[1]}" \
                    --output "$GOD_INVENTORY_FILE" || rc=$?
                python3 "$SCRIPT_DIR/audit_species_background_inventory.py" \
                    --review-results \
                    "${ledgers[4]}" \
                    --output "$SPECIES_BACKGROUND_INVENTORY_FILE" || rc=$?
                python3 "$SCRIPT_DIR/audit_item_name_inventory.py" \
                    --scope issue29-v2 \
                    --review-base 01dc9911ec9948aff661f6ec0b9b0a798fcf909d \
                    --review-results \
                    "${ledgers[2]}" \
                    --output "$ITEM_INVENTORY_FILE" || rc=$?
                python3 "$SCRIPT_DIR/monster_name_ssot.py" \
                    --inventory-output "$MONSTER_INVENTORY_FILE" \
                    --review-results "${ledgers[3]}" \
                    --baseline-ref \
                    7e7e7e78f5ab7c7fc5f5ee458a205850510ad15c || rc=$?
                python3 "$SCRIPT_DIR/audit_world_inventory.py" \
                    --review-results "${ledgers[5]}" \
                    --output "$WORLD_INVENTORY_FILE" || rc=$?
                return "$rc"
            }
            run_phase "review-ledgers" 1 "Strict review ledger audit" \
                run_review_ledgers || RESULTS=$((RESULTS + 1))
            ;;
        ci)
            # --profile ci is truly static: no make, no runtime execution.
            # source-db-static (run above) + translation-static + code-static.
            run_phase "translation-static" 1 "Translation verification (static)" \
                bash "$SCRIPT_DIR/post-translator.sh" || RESULTS=$((RESULTS + 1))
            run_phase "code-static" 1 "Code verification (post-coder.sh, static)" \
                env ZH_VERIFY_SOURCE_DB_STATIC_COMPLETE=1 \
                    bash "$SCRIPT_DIR/post-coder.sh" || RESULTS=$((RESULTS + 1))
            ;;
    esac

    run_message_overlay_static() {
        if [[ -n "${ZH_VERIFY_MESSAGE_OVERLAY_STATIC_COMMAND:-}" ]]; then
            bash -c "$ZH_VERIFY_MESSAGE_OVERLAY_STATIC_COMMAND"
            return
        fi
        # test_monspeak_inventory.py (66 tests, heavy candidate audits,
        # >15 min) is excluded from this static chain: it exceeds the
        # GitHub-hosted runner budget on CI.  Run it directly when the
        # full monspeak gate is needed:
        #   python3 .claude/scripts/tests/test_monspeak_inventory.py
        python3 "$SCRIPT_DIR/tests/test_message_overlay.py" \
            && python3 "$SCRIPT_DIR/tests/test_audit_monspell_behavior.py" \
            && python3 "$SCRIPT_DIR/tests/test_decorlines_inventory.py" \
            && python3 "$SCRIPT_DIR/tests/test_graffiti_inventory.py" \
            && python3 "$SCRIPT_DIR/tests/test_miscast_inventory.py" \
            && python3 "$SCRIPT_DIR/tests/test_monflee_inventory.py" \
            && python3 "$SCRIPT_DIR/tests/test_monspell_inventory.py" \
            && python3 "$SCRIPT_DIR/tests/test_shout_inventory.py" \
            && python3 "$SCRIPT_DIR/tests/test_wpnnoise_inventory.py" \
            && python3 "$SCRIPT_DIR/generate_message_overlay.py" \
                --manifest .claude/data/message-overlay/monspell.json \
                --inventory .claude/data/message-overlay/monspell-phase0-inventory.json \
                --check crawl-ref/source/fork-message-overlay.generated.inc \
            && python3 "$SCRIPT_DIR/audit_message_overlay.py" \
                --manifest .claude/data/message-overlay/monspell.json \
                --inventory .claude/data/message-overlay/monspell-phase0-inventory.json \
                --sidecar crawl-ref/source/fork-message-overlay.generated.inc
    }
    if is_externalized_phase "message-overlay-static"; then
        record_external_phase "message-overlay-static" 1 \
            "TextDB message overlay static audit (external GitHub Actions evidence)"
    else
        run_phase "message-overlay-static" 1 "TextDB message overlay static audit" \
            run_message_overlay_static || RESULTS=$((RESULTS + 1))
    fi

    resolve_build_python() {
        local candidate resolved

        if [[ -n "${ZH_VERIFY_BUILD_PYTHON:-}" ]]; then
            candidate="$ZH_VERIFY_BUILD_PYTHON"
            if "$candidate" -c 'import yaml' >/dev/null 2>&1; then
                printf '%s\n' "$candidate"
                return 0
            fi
            echo "ERROR: ZH_VERIFY_BUILD_PYTHON cannot import PyYAML: $candidate" >&2
            return 1
        fi

        for candidate in python3 /usr/bin/python3 python; do
            resolved="$(command -v "$candidate" 2>/dev/null || true)"
            if [[ -n "$resolved" ]] \
                && "$resolved" -c 'import yaml' >/dev/null 2>&1
            then
                printf '%s\n' "$resolved"
                return 0
            fi
        done

        echo "ERROR: no Python interpreter with PyYAML is available." >&2
        echo "Set ZH_VERIFY_BUILD_PYTHON to a suitable interpreter." >&2
        return 1
    }

    run_incremental_build() {
        if [[ -n "${ZH_VERIFY_BUILD_COMMAND:-}" ]]; then
            bash -c "$ZH_VERIFY_BUILD_COMMAND"
        else
            local build_python
            build_python="$(resolve_build_python)" || return 2
            make -C crawl-ref/source PYTHON="$build_python" -j4
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
        if is_externalized_phase "cpp-build"; then
            record_external_phase "cpp-build" 1 \
                "Risk gate: incremental C++ build (external GitHub Actions evidence)"
        else
            run_phase "cpp-build" 1 "Risk gate: incremental C++ build" run_incremental_build \
                || RESULTS=$((RESULTS + 1))
        fi
        run_phase "zh-smoke" 1 "Risk gate: ZH smoke" run_zh_smoke \
            || RESULTS=$((RESULTS + 1))
    fi

    if [[ "$EXPLICIT_FULL" -eq 1 ]]; then
        run_phase "zh-runtime-full" 1 "Risk gate: full ZH runtime" run_runtime full \
            || RESULTS=$((RESULTS + 1))
    elif [[ "$PROFILE" != ci && ( "$RISK_CJK_RUNTIME" -eq 1 || "$RISK_ZH_TEST_RUNTIME" -eq 1 || "$PROFILE" == review ) ]]; then
        # post_zh_runtime.sh calls its build-and-run Catch2 path "catch2";
        # its "fast" mode only re-aggregates an existing evidence directory.
        # ci profile is truly static — skip runtime entirely.
        if is_externalized_phase "zh-runtime-catch2"; then
            record_external_phase "zh-runtime-catch2" 1 \
                "Risk gate: fast ZH runtime (external GitHub Actions evidence)"
        else
            run_phase "zh-runtime-catch2" 1 "Risk gate: fast ZH runtime" run_runtime catch2 \
                || RESULTS=$((RESULTS + 1))
        fi
    fi

    echo "Summary: $RESULTS blocking failure(s)"
    echo "=== verify_zh.sh complete ==="
} > "$REPORT_FILE" 2>&1

# A bound review is only immutable if the checkout stays at the exact clean
# candidate for the entire run. Strict ledger consumers read their candidate
# Git blobs once; this terminal check also rejects any non-glossary worktree
# drift left by another process or by a verification phase.
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
if [[ -n "$HEAD_SHA" ]]; then
    FINAL_WORKTREE_STATUS=$(git status --porcelain=v1 \
        --untracked-files=all 2>/dev/null || printf '%s' '<git-status-failed>')
    if [[ -n "$FINAL_WORKTREE_STATUS" ]]; then
        printf 'ERROR: candidate worktree changed during verification.\n' \
            >> "$REPORT_FILE"
        EVIDENCE_DRIFT=1
    fi
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
