#!/usr/bin/env python3
"""Focused tests for the external GitHub Actions proof helper and validator.

These tests never contact GitHub.  A fake ``gh`` fixture replays the small
GitHub API responses the trusted helper consumes, and every binding failure is
proved with a minimal negative mutation that breaks exactly one invariant.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
TEST_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = TEST_ROOT / "review_bundle.py"
SPEC = importlib.util.spec_from_file_location("review_bundle", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)
HELPER = TEST_ROOT / "fetch_github_ci_proof.py"

REPOSITORY = "fixture/fake-repo"
WORKFLOW_PATH = ".github/workflows/ci.yml"
RUN_ID = 32029487274
RUN_URL = f"https://github.com/{REPOSITORY}/actions/runs/{RUN_ID}"

FIXTURE_SPEC = {
    "enabled": True,
    "repository": REPOSITORY,
    "workflow_path": WORKFLOW_PATH,
    "allowed_events": ["workflow_dispatch", "push"],
    "externalizable_phases": ["policy-sync", "message-overlay-static"],
    "required_jobs": [
        {
            "id": "zh_ci_gate",
            "name_contains": "ZH CI Gate",
            "phases": ["policy-sync", "message-overlay-static"],
        },
    ],
    "proof_artifact": "github-actions-proof.json",
    "proof_schema": "dcss-zh-github-actions-proof-v1",
}


def canonical(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


class ExternalProofTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.temp = Path(self.temporary.name)
        self.repo = self.temp / "repo"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "user.email",
             "proof@example.invalid"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "config", "user.name", "Proof"],
            check=True,
        )
        workflow_dir = self.repo / ".github/workflows"
        workflow_dir.mkdir(parents=True)
        (workflow_dir / "ci.yml").write_text(
            "name: Build\non: workflow_dispatch\njobs: {}\n",
            encoding="utf-8",
        )
        (self.repo / ".gitignore").write_text("/.worktrees/\n", encoding="utf-8")
        (self.repo / "tracked.txt").write_text("base\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(self.repo), "add", "."], check=True
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "commit", "-qm", "base"],
            check=True,
        )
        self.target = self.git("rev-parse", "HEAD")
        subprocess.run(
            ["git", "-C", str(self.repo), "branch", "candidate"], check=True
        )
        subprocess.run(
            ["git", "-C", str(self.repo), "worktree", "add", "-q",
             ".worktrees/candidate", "candidate"],
            check=True,
        )
        candidate = self.repo / ".worktrees/candidate"
        (candidate / "tracked.txt").write_text(
            "候选内容\n", encoding="utf-8"
        )
        subprocess.run(
            ["git", "-C", str(candidate), "add", "tracked.txt"], check=True
        )
        subprocess.run(
            ["git", "-C", str(candidate), "commit", "-qm", "candidate"],
            check=True,
        )
        self.candidate = self.git("rev-parse", "candidate")
        self.workflow_blob = self.git(
            "rev-parse", f"{self.candidate}:{WORKFLOW_PATH}"
        )
        self.workflow_bytes = subprocess.check_output(
            ["git", "-C", str(self.repo), "cat-file", "blob",
             self.workflow_blob]
        )
        self.workflow_sha256 = hashlib.sha256(self.workflow_bytes).hexdigest()

        self.spec_path = self.temp / "external-ci.json"
        self.spec_path.write_bytes(canonical(FIXTURE_SPEC))

        self.run_json = self.temp / "run.json"
        self.jobs_json = self.temp / "jobs.json"
        self.fake_gh = self.temp / "fake-gh"
        self.fake_gh.write_text(
            """#!/usr/bin/env python3
import os
import sys

if os.environ.get('FAKE_GH_FAIL'):
    print('fake gh failure', file=sys.stderr)
    raise SystemExit(9)
print(' '.join(sys.argv[1:]), file=sys.stderr)
if 'jobs' in sys.argv[-1]:
    path = os.environ['FAKE_GH_JOBS_JSON']
else:
    path = os.environ['FAKE_GH_RUN_JSON']
with open(path, 'rb') as stream:
    sys.stdout.buffer.write(stream.read())
""",
            encoding="utf-8",
        )
        self.fake_gh.chmod(0o755)
        self.set_fixtures()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def git(self, *args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(self.repo), *args], text=True
        ).strip()

    def set_fixtures(
        self,
        run: dict | None = None,
        jobs: dict | None = None,
    ) -> None:
        if run is None:
            run = {
                "repository": {"full_name": REPOSITORY},
                "head_repository": {"full_name": REPOSITORY},
                "event": "workflow_dispatch",
                "head_sha": self.candidate,
                "head_branch": "candidate",
                "path": WORKFLOW_PATH,
                "status": "completed",
                "conclusion": "success",
                "html_url": RUN_URL,
                "id": RUN_ID,
                "workflow_id": 1,
            }
        run.setdefault("id", RUN_ID)
        run.setdefault("workflow_id", 1)
        if jobs is None:
            jobs = {
                "total_count": 1,
                "jobs": [
                    {
                        "id": 1001,
                        "name": "ZH CI Gate (static, ubuntu-latest)",
                        "status": "completed",
                        "conclusion": "success",
                    },
                ],
            }
        self.run_json.write_bytes(canonical(run))
        self.jobs_json.write_bytes(canonical(jobs))

    def run_helper(self) -> subprocess.CompletedProcess[bytes]:
        output = self.temp / "github-actions-proof.json"
        output.unlink(missing_ok=True)
        env = os.environ.copy()
        env["GH_BIN"] = os.fspath(self.fake_gh)
        env["FAKE_GH_RUN_JSON"] = os.fspath(self.run_json)
        env["FAKE_GH_JOBS_JSON"] = os.fspath(self.jobs_json)
        proc = subprocess.run(
            [
                sys.executable,
                os.fspath(HELPER),
                "--run-id",
                str(RUN_ID),
                "--external-ci-json",
                os.fspath(self.spec_path),
                "--candidate-head",
                self.candidate,
                "--target-head",
                self.target,
                "--repo",
                os.fspath(self.repo),
                "--output",
                os.fspath(output),
            ],
            cwd=self.repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )
        self.output = output
        return proc

    def proof_dict(self) -> dict:
        value = json.loads(self.output.read_bytes().decode("utf-8"))
        self.assertEqual(
            self.output.read_bytes(), canonical(value),
            "helper must write canonical JSON",
        )
        return value

    def contract(self) -> dict:
        return {
            "schema": MODULE.CONTRACT_SCHEMA,
            "verification_contract": MODULE.VERIFICATION_CONTRACT,
            "control_plane_files": [],
            "required_artifacts": [],
            "phase_plan": [
                {"id": "policy-sync", "required": True, "when": "always"},
                {"id": "message-overlay-static", "required": True,
                 "when": "always"},
            ],
            "external_ci": dict(FIXTURE_SPEC),
        }

    def validate(self, proof: dict) -> None:
        MODULE._validate_github_proof(
            proof,
            self.contract(),
            {"target_head": self.target, "candidate_head": self.candidate},
            self.repo,
        )

    def test_happy_path_helper_writes_canonical_bound_proof(self) -> None:
        proc = self.run_helper()
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        proof = self.proof_dict()
        self.assertEqual(proof["schema"], MODULE.GITHUB_ACTIONS_PROOF_SCHEMA)
        self.assertEqual(proof["repository"], REPOSITORY)
        self.assertEqual(proof["run_id"], RUN_ID)
        self.assertEqual(proof["run_url"], RUN_URL)
        self.assertEqual(proof["event"], "workflow_dispatch")
        self.assertEqual(proof["head_branch"], "candidate")
        self.assertEqual(proof["head_sha"], self.candidate)
        self.assertEqual(proof["workflow_path"], WORKFLOW_PATH)
        self.assertEqual(proof["workflow_sha"], self.workflow_blob)
        self.assertEqual(
            proof["workflow_blob_sha256_candidate"], self.workflow_sha256
        )
        self.assertEqual(
            proof["workflow_blob_sha256_target"], self.workflow_sha256
        )
        self.assertEqual(proof["status"], "completed")
        self.assertEqual(proof["conclusion"], "success")
        self.assertEqual(
            [job["id"] for job in proof["required_jobs"]], ["zh_ci_gate"]
        )
        self.assertEqual(
            proof["required_jobs"][0]["name"], "ZH CI Gate (static, ubuntu-latest)"
        )
        self.assertEqual(proof["required_jobs"][0]["status"], "completed")
        self.assertEqual(proof["required_jobs"][0]["conclusion"], "success")
        self.assertRegex(
            proof["api_digests"]["run_response_sha256"], r"^[0-9a-f]{64}$"
        )
        self.assertRegex(
            proof["api_digests"]["jobs_response_sha256"], r"^[0-9a-f]{64}$"
        )
        self.assertTrue(proof["fetched_at"])
        self.validate(proof)

    def assert_helper_rejects(self, label: str) -> None:
        proc = self.run_helper()
        self.assertNotEqual(
            proc.returncode, 0, f"{label}: helper unexpectedly succeeded"
        )
        self.assertFalse(
            self.output.exists(), f"{label}: helper wrote a proof on failure"
        )

    def test_wrong_head_sha_is_rejected(self) -> None:
        run = {
            "repository": {"full_name": REPOSITORY},
            "head_repository": {"full_name": REPOSITORY},
            "event": "workflow_dispatch",
            "head_sha": "0" * 40,
            "head_branch": "candidate",
            "path": WORKFLOW_PATH,
            "status": "completed",
            "conclusion": "success",
            "html_url": RUN_URL,
            "workflow_sha": self.workflow_blob,
        }
        self.set_fixtures(run=run)
        self.assert_helper_rejects("wrong head_sha")

    def test_wrong_repository_is_rejected(self) -> None:
        run = {
            "repository": {"full_name": "other/owner-repo"},
            "head_repository": {"full_name": "other/owner-repo"},
            "event": "workflow_dispatch",
            "head_sha": self.candidate,
            "head_branch": "candidate",
            "path": WORKFLOW_PATH,
            "status": "completed",
            "conclusion": "success",
            "html_url": RUN_URL,
            "workflow_sha": self.workflow_blob,
        }
        self.set_fixtures(run=run)
        self.assert_helper_rejects("wrong repository")

    def test_wrong_head_repository_is_rejected(self) -> None:
        run = {
            "repository": {"full_name": REPOSITORY},
            "head_repository": {"full_name": "evil/fork"},
            "event": "workflow_dispatch",
            "head_sha": self.candidate,
            "head_branch": "candidate",
            "path": WORKFLOW_PATH,
            "status": "completed",
            "conclusion": "success",
            "html_url": RUN_URL,
            "workflow_sha": self.workflow_blob,
        }
        self.set_fixtures(run=run)
        self.assert_helper_rejects("wrong head_repository")

    def test_disallowed_event_is_rejected(self) -> None:
        run = {
            "repository": {"full_name": REPOSITORY},
            "head_repository": {"full_name": REPOSITORY},
            "event": "pull_request",
            "head_sha": self.candidate,
            "head_branch": "candidate",
            "path": WORKFLOW_PATH,
            "status": "completed",
            "conclusion": "success",
            "html_url": RUN_URL,
            "workflow_sha": self.workflow_blob,
        }
        self.set_fixtures(run=run)
        self.assert_helper_rejects("disallowed pull_request event")

    def test_incomplete_or_failed_run_is_rejected(self) -> None:
        for field, value in (("status", "in_progress"), ("conclusion", "failure"),
                             ("conclusion", "cancelled")):
            with self.subTest(field=field, value=value):
                run = {
                    "repository": {"full_name": REPOSITORY},
                    "head_repository": {"full_name": REPOSITORY},
                    "event": "workflow_dispatch",
                    "head_sha": self.candidate,
                    "head_branch": "candidate",
                    "path": WORKFLOW_PATH,
                    "status": "completed",
                    "conclusion": "success",
                    "html_url": RUN_URL,
                    "workflow_sha": self.workflow_blob,
                }
                run[field] = value
                self.set_fixtures(run=run)
                self.assert_helper_rejects(f"{field}={value}")

    def test_workflow_path_drift_is_rejected(self) -> None:
        run = {
            "repository": {"full_name": REPOSITORY},
            "head_repository": {"full_name": REPOSITORY},
            "event": "workflow_dispatch",
            "head_sha": self.candidate,
            "head_branch": "candidate",
            "path": ".github/workflows/other.yml",
            "status": "completed",
            "conclusion": "success",
            "html_url": RUN_URL,
            "workflow_sha": self.workflow_blob,
        }
        self.set_fixtures(run=run)
        self.assert_helper_rejects("workflow path drift")

    def test_run_id_mismatch_is_rejected(self) -> None:
        run = {
            "repository": {"full_name": REPOSITORY},
            "head_repository": {"full_name": REPOSITORY},
            "event": "workflow_dispatch",
            "head_sha": self.candidate,
            "head_branch": "candidate",
            "path": WORKFLOW_PATH,
            "status": "completed",
            "conclusion": "success",
            "html_url": RUN_URL,
            "workflow_sha": self.workflow_blob,
            "id": RUN_ID + 1,
        }
        self.set_fixtures(run=run)
        self.assert_helper_rejects("run id mismatch")

    def test_candidate_target_workflow_drift_is_rejected(self) -> None:
        candidate = self.repo / ".worktrees/candidate"
        workflow = candidate / WORKFLOW_PATH
        workflow.write_text("name: Drifted\non: workflow_dispatch\njobs: {}\n",
                            encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(candidate), "add", WORKFLOW_PATH], check=True
        )
        subprocess.run(
            ["git", "-C", str(candidate), "commit", "-qm", "drift"],
            check=True,
        )
        drifted_head = self.git("rev-parse", "candidate")
        drifted_blob = self.git(
            "rev-parse", f"{drifted_head}:{WORKFLOW_PATH}"
        )
        self.assertNotEqual(drifted_blob, self.workflow_blob)
        self.set_fixtures(
            run={
                "repository": {"full_name": REPOSITORY},
                "head_repository": {"full_name": REPOSITORY},
                "event": "workflow_dispatch",
                "head_sha": drifted_head,
                "head_branch": "candidate",
                "path": WORKFLOW_PATH,
                "status": "completed",
                "conclusion": "success",
                "html_url": (
                    f"https://github.com/{REPOSITORY}/actions/runs/{RUN_ID}"
                ),
                "workflow_sha": drifted_blob,
            }
        )
        proc = subprocess.run(
            [
                sys.executable,
                os.fspath(HELPER),
                "--run-id", str(RUN_ID),
                "--external-ci-json", os.fspath(self.spec_path),
                "--candidate-head", drifted_head,
                "--target-head", self.target,
                "--repo", os.fspath(self.repo),
                "--output", os.fspath(self.temp / "proof-drift.json"),
            ],
            cwd=self.repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env={
                **os.environ,
                "GH_BIN": os.fspath(self.fake_gh),
                "FAKE_GH_RUN_JSON": os.fspath(self.run_json),
                "FAKE_GH_JOBS_JSON": os.fspath(self.jobs_json),
            },
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0, "drift helper succeeded")
        self.assertIn("drifted", proc.stderr.decode())

    def test_missing_required_job_is_rejected(self) -> None:
        jobs = {"total_count": 0, "jobs": []}
        self.set_fixtures(jobs=jobs)
        self.assert_helper_rejects("missing required job")

    def test_required_job_failure_is_rejected(self) -> None:
        jobs = {
            "total_count": 1,
            "jobs": [
                {
                    "id": 1001,
                    "name": "ZH CI Gate (static, ubuntu-latest)",
                    "status": "completed",
                    "conclusion": "failure",
                },
            ],
        }
        self.set_fixtures(jobs=jobs)
        self.assert_helper_rejects("required job failure")

    def test_optional_job_failure_does_not_fail_proof(self) -> None:
        jobs = {
            "total_count": 2,
            "jobs": [
                {
                    "id": 1001,
                    "name": "ZH CI Gate (static, ubuntu-latest)",
                    "status": "completed",
                    "conclusion": "success",
                },
                {
                    "id": 9999,
                    "name": "ZH Runtime Full",
                    "status": "completed",
                    "conclusion": "failure",
                },
            ],
        }
        self.set_fixtures(jobs=jobs)
        proc = self.run_helper()
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        proof = self.proof_dict()
        self.assertEqual(len(proof["required_jobs"]), 1)

    def test_gh_api_failure_is_rejected(self) -> None:
        env = os.environ.copy()
        env["GH_BIN"] = os.fspath(self.fake_gh)
        env["FAKE_GH_RUN_JSON"] = os.fspath(self.run_json)
        env["FAKE_GH_JOBS_JSON"] = os.fspath(self.jobs_json)
        env["FAKE_GH_FAIL"] = "1"
        output = self.temp / "proof-fail.json"
        proc = subprocess.run(
            [
                sys.executable, os.fspath(HELPER),
                "--run-id", str(RUN_ID),
                "--external-ci-json", os.fspath(self.spec_path),
                "--candidate-head", self.candidate,
                "--target-head", self.target,
                "--repo", os.fspath(self.repo),
                "--output", os.fspath(output),
            ],
            cwd=self.repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse(output.exists())

    def build_valid_proof(self) -> dict:
        proc = self.run_helper()
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        return self.proof_dict()

    def assert_invalid_proof(self, proof: dict, label: str) -> None:
        with self.assertRaises(MODULE.ReviewBundleError, msg=label):
            self.validate(proof)

    def test_validator_rejects_wrong_head_sha(self) -> None:
        proof = self.build_valid_proof()
        proof["head_sha"] = "0" * 40
        self.assert_invalid_proof(proof, "head_sha")

    def test_validator_rejects_wrong_repository(self) -> None:
        proof = self.build_valid_proof()
        proof["repository"] = "other/owner-repo"
        self.assert_invalid_proof(proof, "repository")

    def test_validator_rejects_incomplete_or_failed_run(self) -> None:
        for field, value in (("status", "queued"), ("conclusion", "failure")):
            with self.subTest(field=field, value=value):
                proof = self.build_valid_proof()
                proof[field] = value
                self.assert_invalid_proof(proof, f"{field}={value}")

    def test_validator_rejects_workflow_path_drift(self) -> None:
        proof = self.build_valid_proof()
        proof["workflow_path"] = ".github/workflows/other.yml"
        self.assert_invalid_proof(proof, "workflow path")

    def test_validator_rejects_workflow_blob_drift(self) -> None:
        proof = self.build_valid_proof()
        proof["workflow_blob_sha256_target"] = "0" * 64
        self.assert_invalid_proof(proof, "target workflow digest")

    def test_validator_rejects_workflow_sha_mismatch(self) -> None:
        proof = self.build_valid_proof()
        proof["workflow_sha"] = "0" * 40
        self.assert_invalid_proof(proof, "workflow_sha")

    def test_validator_rejects_missing_required_job(self) -> None:
        proof = self.build_valid_proof()
        proof["required_jobs"] = []
        self.assert_invalid_proof(proof, "missing required job")

    def test_validator_rejects_required_job_failure(self) -> None:
        proof = self.build_valid_proof()
        proof["required_jobs"][0]["conclusion"] = "failure"
        self.assert_invalid_proof(proof, "required job failure")

    def test_validator_rejects_forged_or_missing_fields(self) -> None:
        proof = self.build_valid_proof()
        proof.pop("fetched_at")
        self.assert_invalid_proof(proof, "missing fetched_at")

        proof = self.build_valid_proof()
        proof["extra"] = "forged"
        self.assert_invalid_proof(proof, "extra field must fail closed")

        proof = self.build_valid_proof()
        proof["required_jobs"][0]["forged"] = True
        self.assert_invalid_proof(proof, "extra job field")

        proof = self.build_valid_proof()
        proof["api_digests"].pop("jobs_response_sha256")
        self.assert_invalid_proof(proof, "missing api digest")

    def test_validator_rejects_wrong_hash_shape(self) -> None:
        proof = self.build_valid_proof()
        proof["api_digests"]["run_response_sha256"] = "not-a-hash"
        self.assert_invalid_proof(proof, "malformed api digest")

        proof = self.build_valid_proof()
        proof["workflow_sha"] = "short"
        self.assert_invalid_proof(proof, "malformed workflow_sha")

    def test_validator_rejects_disallowed_event(self) -> None:
        proof = self.build_valid_proof()
        proof["event"] = "pull_request"
        self.assert_invalid_proof(proof, "disallowed event")

    def test_validator_rejects_run_url_forgery(self) -> None:
        proof = self.build_valid_proof()
        proof["run_url"] = "https://evil.example/actions/runs/32029487274"
        self.assert_invalid_proof(proof, "run_url forgery")

    def test_validator_requires_contract_section(self) -> None:
        proof = self.build_valid_proof()
        contract = self.contract()
        contract.pop("external_ci")
        with self.assertRaises(MODULE.ReviewBundleError):
            MODULE._validate_github_proof(
                proof,
                contract,
                {"target_head": self.target, "candidate_head": self.candidate},
                self.repo,
            )


if __name__ == "__main__":
    unittest.main()