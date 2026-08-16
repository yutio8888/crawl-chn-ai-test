#!/usr/bin/env bash
# run_isolated.sh — run a command in an isolated cgroup to protect the
# paseo.service daemon from heavy Python/test memory and CPU pressure.
#
# The Paseo daemon and its child processes share the paseo.service cgroup
# (MemoryMax=8G by default). Heavy Python tests, unittest discovery, and
# verification profiles run inside that cgroup can exhaust the budget and
# sever the outer connection. fork/nohup/setsid/start_new_session cannot
# escape the parent cgroup; only launching under a different cgroup works.
#
# When a user-level systemd session and paseo-workers.slice exist, this
# wrapper starts a transient service in that slice with MemoryHigh/MemoryMax
# and CPUWeight/CPUQuota limits. Otherwise (CI containers, no user systemd)
# it falls back to a direct exec so the call stays portable.
#
# Usage:
#   bash .claude/scripts/run_isolated.sh python3 .claude/scripts/tests/test_monspeak_inventory.py
#   bash .claude/scripts/run_isolated.sh bash .claude/scripts/verify_zh.sh --profile translation
#
# Limit overrides (env):
#   ZH_ISOLATE_MEMORY_HIGH  default 2G    (throttle, memcg.high)
#   ZH_ISOLATE_MEMORY_MAX   default 3G    (hard kill, memcg.max)
#   ZH_ISOLATE_CPU_WEIGHT   default 20    (lower priority vs daemon)
#   ZH_ISOLATE_CPU_QUOTA    default 200%  (soft cap, 2 cores)
#
# A python/python3 first argument is resolved to an absolute path, because a
# transient service may inherit a different PATH than the calling shell.
#
# Per-unit limits protect a single isolated command. For concurrent workers
# (e.g. run_all.sh launches up to four tests at once), also set an aggregate
# cap on the slice itself via a user drop-in such as
# ~/.config/systemd/user/paseo-workers.slice.d/limits.conf — the two layers
# are not interchangeable. That drop-in is machine-local and not tracked here.
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "run_isolated.sh: missing command" >&2
  exit 2
fi

# Resolve a bare python/python3 to an absolute path so the transient service
# does not depend on the caller's PATH.
case "${1:-}" in
  python | python3)
    if resolved="$(command -v "$1" 2>/dev/null)"; then
      shift
      set -- "$resolved" "$@"
    fi
    ;;
esac

mem_high="${ZH_ISOLATE_MEMORY_HIGH:-2G}"
mem_max="${ZH_ISOLATE_MEMORY_MAX:-3G}"
cpu_weight="${ZH_ISOLATE_CPU_WEIGHT:-20}"
cpu_quota="${ZH_ISOLATE_CPU_QUOTA:-200%}"

can_isolate() {
  command -v systemd-run >/dev/null 2>&1 \
    && systemctl --user show paseo-workers.slice --value --property=Id 2>/dev/null \
      | grep -q '^paseo-workers\.slice$'
}

if can_isolate; then
  unit="zh-isolate-$RANDOM-$$"
  exec systemd-run --user --pipe --wait --collect --quiet \
    --unit="$unit" \
    --slice=paseo-workers.slice \
    --same-dir \
    --property=MemoryHigh="$mem_high" \
    --property=MemoryMax="$mem_max" \
    --property=CPUWeight="$cpu_weight" \
    --property=CPUQuota="$cpu_quota" \
    -- "$@"
else
  # CI or no user-level systemd session: run directly so the call stays
  # portable. Callers that truly require isolation must check can_isolate
  # themselves before relying on this fallback.
  exec "$@"
fi
