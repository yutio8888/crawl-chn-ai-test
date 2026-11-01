#!/usr/bin/env python3
"""Local CI reuse must never turn unavailable evidence into a skipped build."""

import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "check_local_builds.py"
spec = importlib.util.spec_from_file_location("check_local_builds", SCRIPT)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
HEAD, BASE, OTHER = "a" * 40, "b" * 40, "c" * 40
REPO = "owner/crawl"


def status(target, state="success", head=HEAD):
    return {"context": gate.CONTEXTS[target], "state": state,
            "description": f"Equivalent PR build passed for {head}"}


def event():
    return {"number": 7, "pull_request": {
        "head": {"sha": HEAD, "repo": {"full_name": REPO}},
        "base": {"sha": BASE, "repo": {"full_name": REPO}},
    }}


class LocalBuildGateTest(unittest.TestCase):
    def setUp(self):
        self.event = event()
        self.current = copy.deepcopy(self.event["pull_request"])
        self.merge_base = BASE
        self.statuses = [status("linux"), status("windows"), status("android")]
        self.calls = []

    def get(self, path):
        self.calls.append(path)
        if "/pulls/" in path:
            return self.current
        if "/compare/" in path:
            return {"merge_base_commit": {"sha": self.merge_base}}
        self.assertIn(f"/commits/{HEAD}/statuses", path)
        return self.statuses

    def check(self, event_name="pull_request"):
        return gate.check(event_name, self.event, REPO, self.get)

    def test_exact_head_successes_skip_both(self):
        self.assertEqual({"linux": True, "windows": True, "android": True}, self.check())

    def test_platforms_are_independent(self):
        self.statuses = [status("windows")]
        self.assertEqual({"linux": False, "windows": True, "android": False}, self.check())
        self.statuses = [status("linux")]
        self.assertEqual({"linux": True, "windows": False, "android": False}, self.check())

    def test_latest_failure_or_pending_overrides_older_success(self):
        for state in ("failure", "error", "pending"):
            with self.subTest(state=state):
                self.statuses = [status("windows", state), status("windows"),
                                 status("android")]
                self.assertEqual({"linux": False, "windows": False, "android": True}, self.check())

    def test_old_head_or_unrecognized_description_cannot_skip(self):
        self.statuses = [status("windows", head=OTHER), status("android")]
        self.statuses[1]["description"] = "looks good"
        self.assertEqual(gate.no_skips(), self.check())

    def test_missing_or_malformed_statuses_run_ci(self):
        for value in ([], {}, [None, {"context": []}]):
            with self.subTest(value=value):
                self.statuses = value
                self.assertEqual(gate.no_skips(), self.check())

    def test_other_checks_do_not_authorize_or_block_reuse(self):
        self.statuses.insert(0, {"context": "other-test", "state": "failure"})
        self.assertTrue(all(self.check().values()))

    def test_fork_pr_never_queries_api(self):
        self.event["pull_request"]["head"]["repo"]["full_name"] = "fork/crawl"
        self.assertEqual(gate.no_skips(), self.check())
        self.assertEqual([], self.calls)

    def test_non_pr_events_keep_full_builds(self):
        for name in ("push", "schedule", "workflow_dispatch"):
            self.assertEqual(gate.no_skips(), self.check(name))
        self.assertEqual([], self.calls)

    def test_diverged_base_does_not_reuse_head_build(self):
        self.merge_base = OTHER
        self.assertEqual(gate.no_skips(), self.check())
        self.assertFalse(any("/statuses" in path for path in self.calls))

    def test_updated_pr_head_does_not_reuse_old_event(self):
        self.current["head"]["sha"] = OTHER
        self.assertEqual(gate.no_skips(), self.check())

    def test_current_base_must_be_included_even_if_event_base_is_old(self):
        self.current["base"]["sha"] = OTHER
        self.assertEqual(gate.no_skips(), self.check())
        self.assertFalse(any("/compare/" in path for path in self.calls))
        self.merge_base = OTHER
        self.assertEqual(gate.no_skips(), self.check())

    def test_invalid_repository_or_head_does_not_query_api(self):
        self.assertEqual(gate.no_skips(), gate.check(
            "pull_request", self.event, "../other", self.get))
        self.event["pull_request"]["head"]["sha"] = "branch"
        self.assertEqual(gate.no_skips(), self.check())
        self.assertEqual([], self.calls)

    def test_pagination_keeps_newest_status(self):
        first = [status("windows", "failure")] + [
            {"context": f"other/{i}", "state": "success"} for i in range(99)]
        original_get = self.get

        def paged(path):
            if "/statuses" not in path:
                return original_get(path)
            return first if path.endswith("&page=1") else [status("windows"), status("android")]

        self.assertEqual({"linux": False, "windows": False, "android": True}, gate.check(
            "pull_request", self.event, REPO, paged))

    def test_short_poll_accepts_statuses_published_after_push(self):
        now = [0]
        original_get = self.get

        def get(path):
            if "/statuses" in path and now[0] == 0:
                return []
            return original_get(path)

        def sleep(seconds):
            now[0] += seconds

        with patch.object(gate.time, "monotonic", lambda: now[0]):
            self.assertTrue(all(gate.check(
                "pull_request", self.event, REPO, get, 6, sleep).values()))
        self.assertEqual(3, now[0])

    def test_api_failure_outputs_false_and_successful_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            payload, output = Path(temp) / "event", Path(temp) / "output"
            payload.write_text(json.dumps(self.event))
            env = {"GITHUB_EVENT_NAME": "pull_request", "GITHUB_EVENT_PATH": str(payload),
                   "GITHUB_REPOSITORY": REPO, "GITHUB_OUTPUT": str(output)}
            with patch.dict(os.environ, env), patch.object(sys, "argv", [str(SCRIPT)]), \
                    patch.object(gate, "api_get", side_effect=RuntimeError("secret")):
                gate.main()
            self.assertEqual("linux=false\nwindows=false\nandroid=false\n", output.read_text())

    def test_cli_bad_event_keeps_normal_ci_enabled(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output"
            result = subprocess.run([sys.executable, str(SCRIPT)], check=True,
                                    env={**os.environ, "GITHUB_EVENT_PATH": temp,
                                         "GITHUB_OUTPUT": str(output)},
                                    capture_output=True, text=True)
            self.assertIn("running CI", result.stdout)
            self.assertEqual("linux=false\nwindows=false\nandroid=false\n", output.read_text())


if __name__ == "__main__":
    unittest.main()
