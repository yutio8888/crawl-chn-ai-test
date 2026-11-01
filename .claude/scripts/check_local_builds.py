#!/usr/bin/env python3
"""Reuse exact-head local PR builds; uncertainty means running normal CI."""

import argparse
import json
import os
from pathlib import Path
import re
import time
from urllib.request import Request, urlopen


CONTEXTS = {
    "linux": "local-build/linux-console",
    "windows": "local-build/windows-tiles",
    "android": "local-build/android-buildtest",
}


def no_skips():
    return {target: False for target in CONTEXTS}


def latest_successes(statuses, head):
    """GitHub lists statuses newest first; a newer failure overrides success."""
    result = no_skips()
    seen = set()
    if not isinstance(statuses, list):
        return result
    targets = {context: target for target, context in CONTEXTS.items()}
    for status in statuses:
        if not isinstance(status, dict):
            continue
        context = status.get("context")
        if not isinstance(context, str) or context in seen:
            continue
        seen.add(context)
        if context in targets:
            result[targets[context]] = (
                status.get("state") == "success"
                and status.get("description")
                == f"Equivalent PR build passed for {head}"
            )
    return result


def eligible_head(event, repository):
    pr = event.get("pull_request", {})
    head = pr.get("head", {})
    base = pr.get("base", {})
    if (head.get("repo") or {}).get("full_name") != repository:
        return None
    if (base.get("repo") or {}).get("full_name") != repository:
        return None
    head_sha, base_sha = head.get("sha", ""), base.get("sha", "")
    if not all(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{40}", sha)
               for sha in (head_sha, base_sha)):
        return None
    return head_sha, base_sha


def check(event_name, event, repository, get, wait_seconds=0, sleep=time.sleep):
    """Only same-repository PRs whose current base is included can reuse builds."""
    fallback = no_skips()
    if event_name != "pull_request":
        return fallback
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        return fallback
    candidate = eligible_head(event, repository)
    number = event.get("number")
    if not candidate or not isinstance(number, int) or number <= 0:
        return fallback
    head, _ = candidate
    # Do not reuse an old event after its PR head/base has moved.
    current = get(f"repos/{repository}/pulls/{number}")
    current_pair = eligible_head({"pull_request": current}, repository)
    if current_pair != candidate:
        return fallback
    base = current_pair[1]
    comparison = get(f"repos/{repository}/compare/{base}...{head}")
    if comparison.get("merge_base_commit", {}).get("sha") != base:
        return fallback

    deadline = time.monotonic() + wait_seconds
    while True:
        statuses = []
        # Bound pagination. If a context cannot be found, that build still runs.
        for page in range(1, 11):
            batch = get(f"repos/{repository}/commits/{head}/statuses"
                        f"?per_page=100&page={page}")
            if not isinstance(batch, list):
                return fallback
            statuses.extend(batch)
            found = {row.get("context") for row in statuses
                     if isinstance(row, dict)
                     and isinstance(row.get("context"), str)}
            if len(batch) < 100 or set(CONTEXTS.values()) <= found:
                break
        result = latest_successes(statuses, head)
        if all(result.values()) or time.monotonic() >= deadline:
            return result
        sleep(min(3, max(0, deadline - time.monotonic())))


def api_get(path):
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"https://api.github.com/{path}", headers=headers)
    with urlopen(request, timeout=15) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wait-seconds", type=int, default=15)
    args = parser.parse_args()
    result = no_skips()
    try:
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
        result = check(os.environ.get("GITHUB_EVENT_NAME"), event,
                       os.environ.get("GITHUB_REPOSITORY", ""), api_get,
                       max(0, min(args.wait_seconds, 30)))
    except Exception as exc:
        # This is an optimization, never a reason to block or omit validation.
        # Avoid printing API response bodies or authentication details.
        print(f"Local build lookup unavailable ({type(exc).__name__}); running CI.")
    lines = "".join(f"{key}={str(value).lower()}\n"
                    for key, value in result.items())
    print(lines, end="")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as output:
            output.write(lines)


if __name__ == "__main__":
    main()
