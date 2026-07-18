#!/usr/bin/env python3
"""Focused tests for immutable schema-v3 review bundles."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import contextmanager
from pathlib import Path


sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / "review_bundle.py"
SPEC = importlib.util.spec_from_file_location("review_bundle", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(MODULE)
GLOSSARY_SOURCE = SCRIPT.parents[2] / "docs/glossary.md"
GLOSSARY_SHA256 = hashlib.sha256(GLOSSARY_SOURCE.read_bytes()).hexdigest()
CLASSIFIER_SOURCE = """#!/usr/bin/env python3
import argparse
import json
import os
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--repo', required=True)
parser.add_argument('--base', required=True)
parser.add_argument('--head', required=True)
args = parser.parse_args()
if os.environ.get('FAKE_CLASSIFIER_REQUIRE_CLEAN_ENV'):
    unsafe = ('PYTHONPATH', 'LD_PRELOAD', 'BASH_ENV', 'GIT_DIR',
              'ZH_VERIFY_RUNTIME_COMMAND')
    expected = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
    if any(os.environ.get(name) for name in unsafe) or os.environ.get('PATH') != expected:
        print('unsafe classifier environment', file=sys.stderr)
        raise SystemExit(9)
result = {
    'schema_version': 1,
    'classification': 'code',
    'reviewers': ['zh-code-reviewer'],
    'files': ['tracked.txt'],
    'note': '可信路由',
    'source': {'type': 'git', 'base': args.base, 'head': args.head},
}
print(json.dumps(result, ensure_ascii=False, indent=2))
"""


class ReviewBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.temp = Path(self.temporary.name)
        self.repo = self.temp / "repo"
        self.run_cmd("git", "init", "-q", str(self.repo), cwd=self.temp, check=True)
        self.run_cmd(
            "git", "config", "user.email", "review-bundle@example.invalid",
            cwd=self.repo, check=True,
        )
        self.run_cmd("git", "config", "user.name", "Review Bundle Test", cwd=self.repo, check=True)
        trusted = self.repo / ".trusted"
        trusted.mkdir()
        self.classifier = self.repo / MODULE.TRUSTED_CLASSIFIER_PATH
        self.classifier.parent.mkdir(parents=True)
        self.classifier.write_text(CLASSIFIER_SOURCE, encoding="utf-8")
        self.classifier.chmod(0o755)
        self.verifier = trusted / "fake_verify.py"
        self.contract = trusted / "final_contract.json"
        contract = {
            "schema": MODULE.CONTRACT_SCHEMA,
            "verification_contract": "dcss-zh-review-v3",
            "control_plane_files": [
                MODULE.TRUSTED_CLASSIFIER_PATH,
                ".trusted/fake_verify.py",
                ".trusted/final_contract.json",
            ],
            "phase_plan": [
                {"id": "policy-sync", "required": True, "when": "always"},
                {"id": "review-static", "required": True, "when": "always"},
                {"id": "message-overlay-static", "required": True, "when": "always"},
                {"id": "optional-advisory", "required": False, "when": "always",
                 "allow_skip": True},
                {"id": "message-overlay-catch2", "required": True,
                 "when": "risk_message_overlay"},
                {"id": "cpp-build", "required": True, "when": "risk_cpp_i18n"},
                {"id": "zh-smoke", "required": True, "when": "risk_cpp_i18n"},
                {"id": "zh-runtime-catch2", "required": True,
                 "when": "review_profile"},
            ],
        }
        self.contract.write_bytes(MODULE.canonical_json_bytes(contract))
        self.verifier.write_text(
            """#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--profile', required=True)
parser.add_argument('--base', required=True)
parser.add_argument('--head', required=True)
parser.add_argument('--scope', required=True)
parser.add_argument('--output-dir', required=True)
parser.add_argument('--routing-sha256', required=True)
parser.add_argument('--control-plane-sha256', required=True)
args = parser.parse_args()
count = os.environ.get('FAKE_VERIFY_COUNT')
if count:
    with open(count, 'a', encoding='utf-8') as stream:
        stream.write('run\\n')
delay = float(os.environ.get('FAKE_VERIFY_SLEEP', '0'))
if delay:
    time.sleep(delay)
mode = os.environ.get('FAKE_VERIFY_MODE', 'pass')
unsafe_names = (
    'ZH_VERIFY_RUNTIME_COMMAND',
    'ZH_VERIFY_BUILD_COMMAND',
    'ZH_RUNTIME_SOURCE_DIR',
    'BASH_ENV',
    'PYTHONPATH',
    'LD_PRELOAD',
    'MAKEFLAGS',
    'GIT_DIR',
)
if any(os.environ.get(name) for name in unsafe_names):
    mode = 'unsafe-env'
expected_path = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
if os.environ.get('FAKE_VERIFY_REQUIRE_SYSTEM_PATH') and os.environ.get('PATH') != expected_path:
    mode = 'unsafe-env'
run_id = f'fake-{time.time_ns()}-{os.getpid()}'
run_dir = Path(args.output_dir) / run_id
run_dir.mkdir(parents=True)
verify_log = run_dir / 'verify.log'
verify_log.write_text(f'fake verifier mode={mode}\\n', encoding='utf-8')
diff = subprocess.check_output([
    'git', 'diff', '--no-ext-diff', '--no-textconv', '--binary', '--full-index',
    f'{args.base}..{args.head}', '--',
])
glossary = Path('docs/glossary.md').read_bytes()
phase_plan = [('policy-sync', True), ('review-static', True),
              ('message-overlay-static', True), ('optional-advisory', False),
              ('zh-runtime-catch2', True)]
phase_status = 'fail' if mode == 'fail' else 'pass'
phase_exit = 7 if mode == 'fail' else 0
phases = [
    {'id': item, 'required': required,
     'status': ('skip' if not required else
                phase_status if index == 0 else 'pass'),
     'exit_code': phase_exit if index == 0 else 0}
    for index, (item, required) in enumerate(phase_plan)
]
if mode == 'missing-phase':
    phases.pop()
metadata = {
    'schema_version': 2 if mode == 'v2' else 3,
    'verification_contract': 'dcss-zh-review-v3',
    'run_id': 'wrong-run' if mode == 'wrong-run-id' else run_id,
    'status': 'fail' if mode == 'fail' else 'pass',
    'profile': 'code' if mode == 'wrong-profile' else args.profile,
    'scope': 'changed' if mode == 'wrong-scope' else args.scope,
    'base': args.base,
    'head': args.head,
    'diff_sha256': hashlib.sha256(diff).hexdigest(),
    'glossary_sha256': hashlib.sha256(glossary).hexdigest(),
    'routing_sha256': args.routing_sha256,
    'control_plane_sha256': args.control_plane_sha256,
    'risk_cpp_i18n': False,
    'risk_cjk_runtime': False,
    'risk_message_overlay': False,
    'runtime_mode': 'catch2',
    'phases': phases,
    'artifacts': [{
        'path': 'verify.log',
        'size': verify_log.stat().st_size,
        'sha256': hashlib.sha256(verify_log.read_bytes()).hexdigest(),
    }],
    'failures': 1 if mode == 'fail' else 0,
}
(run_dir / 'metadata.json').write_text(json.dumps(metadata), encoding='utf-8')
if mode == 'symlink-artifact':
    verify_log.unlink()
    verify_log.symlink_to('/dev/null')
if mode == 'mutate':
    Path('mutation.txt').write_text('dirty', encoding='utf-8')
if mode == 'move-ref':
    subprocess.run(['git', 'commit', '--allow-empty', '-qm', 'move candidate ref'], check=True)
print(f'fake run {run_id}')
raise SystemExit(7 if mode == 'fail' else 0)
""",
            encoding="utf-8",
        )
        self.verifier.chmod(0o755)
        shell_scripts = self.repo / ".claude/scripts"
        shutil.copy2(SCRIPT, shell_scripts / "review_bundle.py")
        shutil.copy2(SCRIPT.parent / "review_final_gate.sh", shell_scripts / "review_final_gate.sh")
        shell_verifier = shell_scripts / "verify_zh.sh"
        shutil.copy2(self.verifier, shell_verifier)
        shell_contract_path = shell_scripts / "data/review_verification_contract_v3.json"
        shell_contract_path.parent.mkdir(parents=True)
        shell_contract = dict(contract)
        shell_contract["control_plane_files"] = sorted([
            MODULE.TRUSTED_CLASSIFIER_PATH,
            ".claude/scripts/data/review_verification_contract_v3.json",
            ".claude/scripts/review_bundle.py",
            ".claude/scripts/review_final_gate.sh",
            ".claude/scripts/verify_zh.sh",
        ])
        shell_contract_path.write_bytes(MODULE.canonical_json_bytes(shell_contract))
        docs = self.repo / "docs"
        docs.mkdir()
        (docs / "glossary.md").write_bytes(
            GLOSSARY_SOURCE.read_bytes()
        )
        (self.repo / ".gitignore").write_text("/.worktrees/\n", encoding="utf-8")
        (self.repo / "tracked.txt").write_text("base\n", encoding="utf-8")
        self.run_cmd("git", "add", ".gitignore", ".claude", ".trusted", "docs/glossary.md", "tracked.txt",
                     cwd=self.repo, check=True)
        self.run_cmd("git", "commit", "-qm", "base", cwd=self.repo, check=True)
        self.run_cmd("git", "branch", "target", cwd=self.repo, check=True)
        self.run_cmd("git", "branch", "candidate", cwd=self.repo, check=True)
        self.run_cmd("git", "worktree", "add", "-q", ".worktrees/candidate", "candidate",
                     cwd=self.repo, check=True)
        self.candidate = self.repo / ".worktrees/candidate"
        (self.candidate / "tracked.txt").write_text("候选内容\n", encoding="utf-8")
        self.run_cmd("git", "add", "tracked.txt", cwd=self.candidate, check=True)
        self.run_cmd("git", "commit", "-qm", "candidate", cwd=self.candidate, check=True)
        self.base = self.git("rev-parse", "target", cwd=self.repo)
        self.head = self.git("rev-parse", "candidate", cwd=self.repo)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    @staticmethod
    def run_cmd(*args: str, cwd: Path, check: bool = False) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        return subprocess.run(
            args, cwd=cwd, text=True, capture_output=True, check=check, env=env
        )

    def git(self, *args: str, cwd: Path) -> str:
        return self.run_cmd("git", *args, cwd=cwd, check=True).stdout.strip()

    def create(self) -> dict:
        return MODULE.create_bundle(
            self.candidate, "target", "HEAD", GLOSSARY_SHA256, self.classifier
        )

    def ready(self) -> dict:
        created = self.create()
        MODULE.record_readiness(
            self.candidate, created["bundle_id"], "zh-code-reviewer", 0, 0
        )
        return created

    def run_final(self, created: dict, **kwargs: object) -> dict:
        return MODULE.run_final(
            self.candidate,
            created["bundle_id"],
            self.repo,
            self.verifier,
            self.contract,
            **kwargs,
        )

    @contextmanager
    def fake_environment(self, **values: str):
        old = {name: os.environ.get(name) for name in values}
        try:
            os.environ.update(values)
            yield
        finally:
            for name, value in old.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

    def first_attempt_path(self, created: dict) -> Path:
        attempts = Path(created["bundle_path"]) / "attempts"
        return next(path for path in attempts.iterdir() if not path.name.startswith("."))

    def rewrite_attempt_metadata(self, attempt: Path, metadata: dict) -> None:
        metadata_bytes = MODULE.canonical_json_bytes(metadata)
        (attempt / "metadata.json").write_bytes(metadata_bytes)
        completion_path = attempt / "completion.json"
        completion = json.loads(completion_path.read_bytes())
        completion["metadata_sha256"] = hashlib.sha256(metadata_bytes).hexdigest()
        completion_path.write_bytes(MODULE.canonical_json_bytes(completion))

    @staticmethod
    def evidence_snapshot(path: Path) -> dict[str, tuple[str, bytes]]:
        result: dict[str, tuple[str, bytes]] = {}
        for item in sorted(path.rglob("*")):
            relative = item.relative_to(path).as_posix()
            if item.is_symlink():
                result[relative] = ("symlink", os.readlink(item).encode())
            elif item.is_dir():
                result[relative] = ("directory", b"")
            else:
                result[relative] = ("file", item.read_bytes())
        return result

    def test_linked_worktree_common_dir_identity_and_raw_diff_sha(self) -> None:
        result = self.create()
        common = Path(self.git(
            "rev-parse", "--path-format=absolute", "--git-common-dir", cwd=self.candidate
        ))
        self.assertEqual(MODULE.git_common_dir(self.candidate), common)
        bundle_path = Path(result["bundle_path"])
        self.assertEqual(bundle_path.parent, common / "zh-review-evidence/v3")

        raw_diff = subprocess.check_output(
            [
                "git", "diff", "--no-ext-diff", "--no-textconv", "--binary",
                "--full-index", f"{self.base}..{self.head}", "--",
            ],
            cwd=self.candidate,
        )
        expected_diff = hashlib.sha256(raw_diff).hexdigest()
        manifest_bytes = (bundle_path / "bundle.json").read_bytes()
        manifest = json.loads(manifest_bytes)
        self.assertEqual(manifest, {
            "schema": "dcss-zh-review-bundle-v3",
            "target_head": self.base,
            "candidate_head": self.head,
            "diff_sha256": expected_diff,
            "glossary_sha256": GLOSSARY_SHA256,
            "routing_sha256": result["routing_sha256"],
        })
        self.assertEqual(manifest_bytes, MODULE.canonical_json_bytes(manifest))
        self.assertFalse(manifest_bytes.endswith(b"\n"))
        identity = {key: manifest[key] for key in MODULE.IDENTITY_FIELDS}
        self.assertEqual(
            bundle_path.name,
            hashlib.sha256(MODULE.canonical_json_bytes(identity)).hexdigest(),
        )

    def test_routing_and_readiness_are_cryptographically_bound(self) -> None:
        created = self.create()
        bundle_path = Path(created["bundle_path"])
        routing_bytes = (bundle_path / "routing.json").read_bytes()
        routing = json.loads(routing_bytes)
        self.assertEqual(routing_bytes, MODULE.canonical_json_bytes(routing))
        self.assertEqual(routing["source"], {
            "type": "git", "base": self.base, "head": self.head,
        })
        self.assertEqual(
            hashlib.sha256(routing_bytes).hexdigest(), created["routing_sha256"]
        )

        with self.assertRaises(MODULE.ReviewBundleError):
            MODULE.record_readiness(
                self.candidate, created["bundle_id"], "translation-reviewer", 0, 0
            )
        status = MODULE.record_readiness(
            self.candidate, created["bundle_id"], "zh-code-reviewer", 0, 0, 2
        )
        self.assertTrue(status["ready"])
        readiness_path = bundle_path / "readiness/zh-code-reviewer.json"
        readiness_bytes = readiness_path.read_bytes()
        readiness = json.loads(readiness_bytes)
        self.assertEqual(readiness_bytes, MODULE.canonical_json_bytes(readiness))
        self.assertEqual(readiness["bundle_id"], created["bundle_id"])
        self.assertEqual(readiness["bundle_sha256"], created["bundle_sha256"])
        self.assertEqual(readiness["routing_sha256"], created["routing_sha256"])
        self.assertEqual(readiness["reviewer"], "zh-code-reviewer")
        self.assertTrue(readiness["ready"])
        with MODULE.final_gate(self.candidate, created["bundle_id"]) as gated:
            self.assertTrue(gated["ready"])

    def test_trusted_classifier_scrubs_loader_and_override_environment(self) -> None:
        with self.fake_environment(
            FAKE_CLASSIFIER_REQUIRE_CLEAN_ENV="1",
            PYTHONPATH="/tmp/unsafe-python-path",
            LD_PRELOAD="/tmp/unsafe-preload.so",
            BASH_ENV="/tmp/unsafe-bash-env",
            GIT_DIR="/tmp/not-the-repository",
            ZH_VERIFY_RUNTIME_COMMAND="true",
            PATH="/tmp/unsafe-path",
        ):
            created = self.create()
        self.assertEqual(created["routing"]["reviewers"], ["zh-code-reviewer"])

    def test_forged_classifier_is_rejected_before_evidence_write(self) -> None:
        forged = self.temp / "forged_classifier.py"
        forged.write_text(
            CLASSIFIER_SOURCE.replace(
                "'classification': 'code'", "'classification': 'none'"
            ).replace(
                "'reviewers': ['zh-code-reviewer']", "'reviewers': []"
            ),
            encoding="utf-8",
        )
        forged.chmod(0o755)
        with self.assertRaisesRegex(
            MODULE.ReviewBundleError, "target-head classifier"
        ):
            MODULE.create_bundle(
                self.candidate, "target", "HEAD", GLOSSARY_SHA256, forged
            )
        self.assertFalse(
            (self.repo / ".git/zh-review-evidence/v3").exists(),
            "forged routing must be rejected before evidence directories exist",
        )

    def test_cli_describe_create_record_status_and_validate(self) -> None:
        common = [
            "--repo", str(self.candidate),
            "--target", "target",
            "--candidate", "HEAD",
            "--glossary-sha256", GLOSSARY_SHA256,
            "--classifier", str(self.classifier),
        ]
        described_proc = self.run_cmd(
            sys.executable, str(SCRIPT), "describe", *common,
            cwd=self.candidate, check=True,
        )
        described = json.loads(described_proc.stdout)
        self.assertFalse(Path(described["bundle_path"]).exists())
        created = json.loads(self.run_cmd(
            sys.executable, str(SCRIPT), "create", *common,
            cwd=self.candidate, check=True,
        ).stdout)
        self.assertEqual(created["bundle_id"], described["bundle_id"])

        selector = ["--repo", str(self.candidate), "--bundle", created["bundle_id"]]
        recorded = json.loads(self.run_cmd(
            sys.executable, str(SCRIPT), "record-readiness", *selector,
            "--reviewer", "zh-code-reviewer", "--blocker", "0",
            "--needs-fix", "0", "--suggestion", "1",
            cwd=self.candidate, check=True,
        ).stdout)
        self.assertTrue(recorded["ready"])
        status_proc = self.run_cmd(
            sys.executable, str(SCRIPT), "status", *selector,
            cwd=self.candidate,
        )
        self.assertEqual(status_proc.returncode, MODULE.FINAL_GATE_REQUIRED)
        status = json.loads(status_proc.stdout)
        validated = json.loads(self.run_cmd(
            sys.executable, str(SCRIPT), "validate", *selector,
            cwd=self.candidate, check=True,
        ).stdout)
        self.assertTrue(status["ready"])
        self.assertTrue(validated["valid"])

    def test_blocker_prevents_readiness(self) -> None:
        created = self.create()
        status = MODULE.record_readiness(
            self.candidate, created["bundle_id"], "zh-code-reviewer", 1, 0, 0
        )
        self.assertFalse(status["ready"])
        self.assertEqual(status["not_ready_reviewers"], ["zh-code-reviewer"])
        with self.assertRaisesRegex(MODULE.ReviewBundleError, "not ready"):
            with MODULE.final_gate(self.candidate, created["bundle_id"]):
                self.fail("a blocker-bearing readiness record passed the final gate")

    def test_needs_fix_prevents_readiness(self) -> None:
        created = self.create()
        status = MODULE.record_readiness(
            self.candidate, created["bundle_id"], "zh-code-reviewer", 0, 1, 0
        )
        self.assertFalse(status["ready"])
        self.assertEqual(status["not_ready_reviewers"], ["zh-code-reviewer"])

    def test_dirty_candidate_is_rejected_before_evidence_write(self) -> None:
        (self.candidate / "untracked.txt").write_text("dirty\n", encoding="utf-8")
        with self.assertRaisesRegex(MODULE.ReviewBundleError, "candidate checkout is dirty"):
            self.create()
        self.assertFalse(
            (self.repo / ".git/zh-review-evidence/v3").exists(),
            "dirty rejection must happen before evidence directories are created",
        )

    def test_glossary_mismatch_and_non_ancestor_fail_before_evidence_write(self) -> None:
        evidence = self.repo / ".git/zh-review-evidence/v3"
        with self.assertRaisesRegex(MODULE.ReviewBundleError, "glossary_sha256"):
            MODULE.create_bundle(
                self.candidate, "target", "HEAD", "0" * 64, self.classifier
            )
        self.assertFalse(
            evidence.exists(),
            "glossary mismatch must be rejected before evidence directories exist",
        )

        tree = self.git("rev-parse", f"{self.base}^{{tree}}", cwd=self.repo)
        sibling = subprocess.run(
            ["git", "commit-tree", tree, "-p", self.base],
            cwd=self.repo,
            text=True,
            input="sibling target\n",
            capture_output=True,
            check=True,
        ).stdout.strip()
        with self.assertRaisesRegex(MODULE.ReviewBundleError, "not an ancestor"):
            MODULE.create_bundle(
                self.candidate, sibling, "HEAD", GLOSSARY_SHA256, self.classifier
            )
        self.assertFalse(
            evidence.exists(),
            "non-ancestor input must be rejected before evidence directories exist",
        )

    def test_atomic_write_once_rejects_content_conflict(self) -> None:
        created = self.create()
        bundle_path = Path(created["bundle_path"])
        manifest_path = bundle_path / "bundle.json"
        manifest_path.write_bytes(MODULE.canonical_json_bytes({"conflict": True}))
        with self.assertRaisesRegex(MODULE.ContentConflictError, "content conflict"):
            self.create()
        self.assertEqual(
            manifest_path.read_bytes(), MODULE.canonical_json_bytes({"conflict": True})
        )

    def test_symlink_and_stale_temp_objects_are_rejected(self) -> None:
        described = MODULE.describe_bundle(
            self.candidate, "target", "HEAD", GLOSSARY_SHA256, self.classifier
        )
        root = MODULE.evidence_root(self.candidate, create=True)
        bundle_path = root / described["bundle_id"]
        bundle_path.mkdir()
        outside = self.temp / "outside.json"
        outside.write_text("{}", encoding="utf-8")
        (bundle_path / "bundle.json").symlink_to(outside)
        with self.assertRaisesRegex(MODULE.UnsafeObjectError, "symlink"):
            self.create()
        self.assertEqual(outside.read_text(encoding="utf-8"), "{}")

        (bundle_path / "bundle.json").unlink()
        (bundle_path / ".tmp-stale").write_text("partial", encoding="utf-8")
        with self.assertRaisesRegex(MODULE.UnsafeObjectError, "temporary"):
            self.create()

    def test_final_pass_seals_approval_and_never_reruns(self) -> None:
        created = self.ready()
        count = self.temp / "verify-count"
        with self.fake_environment(FAKE_VERIFY_COUNT=str(count)):
            result = self.run_final(created)
            reused = self.run_final(created, retry_failed=True)
        self.assertEqual(result["state"], "MERGEABLE")
        self.assertEqual(reused["state"], "MERGEABLE")
        self.assertTrue(result["approved"])
        self.assertEqual(count.read_text(encoding="utf-8").splitlines(), ["run"])
        bundle_path = Path(created["bundle_path"])
        approval_path = bundle_path / "final-approval.json"
        approval = json.loads(approval_path.read_bytes())
        self.assertEqual(
            approval_path.read_bytes(), MODULE.canonical_json_bytes(approval)
        )
        self.assertEqual(approval["bundle_id"], created["bundle_id"])
        self.assertEqual(approval["routing_sha256"], created["routing_sha256"])
        self.assertEqual(len(result["attempts"]), 1)
        self.assertFalse((bundle_path / MODULE.RUNNING_NAME).exists())
        self.assertFalse(any(
            path.name.startswith(".staging-")
            for path in (bundle_path / "attempts").iterdir()
        ))
        attempt = self.first_attempt_path(created)
        metadata = json.loads((attempt / "metadata.json").read_bytes())
        completion = json.loads((attempt / "completion.json").read_bytes())
        control = MODULE._control_plane_from_commit(
            self.candidate,
            self.base,
            ".trusted/final_contract.json",
            ".trusted/fake_verify.py",
        )
        self.assertEqual(metadata["routing_sha256"], created["routing_sha256"])
        self.assertEqual(
            metadata["control_plane_sha256"], control["control_plane_sha256"]
        )
        self.assertEqual(completion["contract_sha256"], control["contract_sha256"])
        self.assertIn("fake run", (attempt / "verify.log").read_text(encoding="utf-8"))
        self.assertEqual(
            approval["readiness"],
            [{
                "reviewer": "zh-code-reviewer",
                "sha256": result["readiness_sha256"]["zh-code-reviewer"],
            }],
        )

    def test_final_verifier_scrubs_override_and_loader_environment(self) -> None:
        created = self.ready()
        with self.fake_environment(
            ZH_VERIFY_RUNTIME_COMMAND="true",
            ZH_VERIFY_BUILD_COMMAND="true",
            ZH_RUNTIME_SOURCE_DIR="/tmp/not-the-candidate",
            BASH_ENV="/tmp/unsafe-bash-env",
            GIT_DIR="/tmp/not-the-repository",
            PYTHONPATH="/tmp/unsafe-python-path",
            LD_PRELOAD="/tmp/unsafe-preload.so",
            MAKEFLAGS="--eval=all:;@true",
            PATH="/tmp/unsafe-path",
            FAKE_VERIFY_REQUIRE_SYSTEM_PATH="1",
        ):
            result = self.run_final(created)
        self.assertEqual(result["state"], "MERGEABLE")
        attempt = self.first_attempt_path(created)
        self.assertIn(
            "fake verifier mode=pass",
            (attempt / "verify.log").read_text(encoding="utf-8"),
        )

    def test_failed_attempt_requires_explicit_retry_with_distinct_id(self) -> None:
        created = self.ready()
        count = self.temp / "verify-count"
        with self.fake_environment(
            FAKE_VERIFY_COUNT=str(count), FAKE_VERIFY_MODE="fail"
        ):
            failed = self.run_final(created)
        self.assertEqual(failed["state"], "EVIDENCE_FAILED")
        self.assertFalse(failed["approved"])
        with self.fake_environment(FAKE_VERIFY_COUNT=str(count)):
            unchanged = self.run_final(created)
            passed = self.run_final(created, retry_failed=True)
        self.assertEqual(unchanged["state"], "EVIDENCE_FAILED")
        self.assertEqual(passed["state"], "MERGEABLE")
        self.assertEqual(count.read_text(encoding="utf-8").splitlines(), ["run", "run"])
        attempt_ids = [item["attempt_id"] for item in passed["attempts"]]
        self.assertEqual(len(attempt_ids), 2)
        self.assertEqual(len(set(attempt_ids)), 2)

    def test_concurrent_run_final_executes_fake_verifier_once(self) -> None:
        created = self.ready()
        count = self.temp / "verify-count"
        command = [
            sys.executable,
            str(SCRIPT),
            "run-final",
            "--repo",
            str(self.candidate),
            "--bundle",
            created["bundle_id"],
            "--target-repo",
            str(self.repo),
            "--verifier",
            str(self.verifier),
            "--contract",
            str(self.contract),
        ]
        env = os.environ.copy()
        env.update(
            PYTHONDONTWRITEBYTECODE="1",
            FAKE_VERIFY_COUNT=str(count),
            FAKE_VERIFY_SLEEP="0.3",
        )
        first = subprocess.Popen(
            command, cwd=self.candidate, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
        )
        second = subprocess.Popen(
            command, cwd=self.candidate, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
        )
        deadline = time.monotonic() + 5
        while not count.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        active = MODULE.status_bundle(self.candidate, created["bundle_id"])
        self.assertEqual(active["exit_code"], MODULE.FINAL_GATE_RUNNING)
        first_stdout, first_stderr = first.communicate(timeout=10)
        second_stdout, second_stderr = second.communicate(timeout=10)
        self.assertEqual(first.returncode, 0, first_stdout + first_stderr)
        self.assertEqual(second.returncode, 0, second_stdout + second_stderr)
        self.assertEqual(count.read_text(encoding="utf-8").splitlines(), ["run"])
        self.assertEqual(json.loads(first_stdout)["state"], "MERGEABLE")
        self.assertEqual(json.loads(second_stdout)["state"], "MERGEABLE")

    def test_sigterm_publishes_completed_interrupted_attempt(self) -> None:
        created = self.ready()
        count = self.temp / "verify-count"
        command = [
            sys.executable, str(SCRIPT), "run-final",
            "--repo", str(self.candidate), "--bundle", created["bundle_id"],
            "--target-repo", str(self.repo), "--verifier", str(self.verifier),
            "--contract", str(self.contract),
        ]
        env = os.environ.copy()
        env.update(
            PYTHONDONTWRITEBYTECODE="1",
            FAKE_VERIFY_COUNT=str(count),
            FAKE_VERIFY_SLEEP="5",
        )
        process = subprocess.Popen(
            command, cwd=self.candidate, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
        )
        deadline = time.monotonic() + 5
        while not count.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(count.exists(), "fake verifier did not start")
        process.terminate()
        stdout, stderr = process.communicate(timeout=10)
        self.assertEqual(process.returncode, MODULE.EVIDENCE_FAILED, stdout + stderr)
        result = json.loads(stdout)
        self.assertEqual(result["state"], "EVIDENCE_FAILED")
        self.assertEqual(result["attempts"][0]["outcome"], "interrupted")
        attempt = self.first_attempt_path(created)
        self.assertTrue((attempt / MODULE.COMPLETION_NAME).is_file())
        self.assertFalse((Path(created["bundle_path"]) / MODULE.APPROVAL_NAME).exists())

    def test_sigkill_residue_cannot_approve_and_needs_recovery(self) -> None:
        created = self.ready()
        count = self.temp / "verify-count"
        command = [
            sys.executable, str(SCRIPT), "run-final",
            "--repo", str(self.candidate), "--bundle", created["bundle_id"],
            "--target-repo", str(self.repo), "--verifier", str(self.verifier),
            "--contract", str(self.contract),
        ]
        env = os.environ.copy()
        env.update(
            PYTHONDONTWRITEBYTECODE="1",
            FAKE_VERIFY_COUNT=str(count),
            FAKE_VERIFY_SLEEP="5",
        )
        process = subprocess.Popen(
            command, cwd=self.candidate, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
        )
        deadline = time.monotonic() + 5
        while not count.exists() and time.monotonic() < deadline:
            time.sleep(0.01)
        self.assertTrue(count.exists(), "fake verifier did not start")
        process.kill()
        process.communicate(timeout=10)
        time.sleep(0.05)
        stale = MODULE.status_bundle(self.candidate, created["bundle_id"])
        self.assertEqual(stale["exit_code"], MODULE.STALE_EVIDENCE)
        self.assertFalse((Path(created["bundle_path"]) / MODULE.APPROVAL_NAME).exists())
        recovered = self.run_final(created, recover_stale=True)
        self.assertEqual(recovered["state"], "MERGEABLE")

    def test_stale_running_requires_explicit_recovery_and_live_marker_blocks(self) -> None:
        created = self.ready()
        bundle_path = Path(created["bundle_path"])
        attempts = bundle_path / "attempts"
        attempts.mkdir()
        operation_id = "attempt-stale"
        (attempts / f".staging-{operation_id}").mkdir()
        marker = {
            "schema": MODULE.RUNNING_SCHEMA,
            "bundle_id": created["bundle_id"],
            "operation_id": operation_id,
            "pid": 99999999,
            "proc_start": "missing",
            "boot_id": MODULE._boot_id(),
            "staging_name": f".staging-{operation_id}",
            "target_head": self.base,
            "candidate_head": self.head,
            "routing_sha256": created["routing_sha256"],
            "started_ns": "1",
        }
        (bundle_path / MODULE.RUNNING_NAME).write_bytes(
            MODULE.canonical_json_bytes(marker)
        )
        stale = MODULE.status_bundle(self.candidate, created["bundle_id"])
        self.assertEqual(stale["exit_code"], MODULE.STALE_EVIDENCE)
        with self.assertRaises(MODULE.StaleEvidenceError):
            self.run_final(created)
        recovered = self.run_final(created, recover_stale=True)
        self.assertEqual(recovered["state"], "MERGEABLE")

        # A marker bound to a live process may never be recovered explicitly.
        approval = bundle_path / MODULE.APPROVAL_NAME
        approval.unlink()
        for attempt in list(attempts.iterdir()):
            if attempt.is_dir():
                import shutil
                shutil.rmtree(attempt)
        live_id = "attempt-live"
        (attempts / f".staging-{live_id}").mkdir()
        marker.update(
            operation_id=live_id,
            pid=os.getpid(),
            proc_start=MODULE._proc_start_token(os.getpid()),
            boot_id=MODULE._boot_id(),
            staging_name=f".staging-{live_id}",
        )
        (bundle_path / MODULE.RUNNING_NAME).write_bytes(
            MODULE.canonical_json_bytes(marker)
        )
        running = MODULE.status_bundle(self.candidate, created["bundle_id"])
        self.assertEqual(running["exit_code"], MODULE.FINAL_GATE_RUNNING)
        with self.assertRaisesRegex(MODULE.ReviewBundleError, "live"):
            self.run_final(created, recover_stale=True)

    def test_metadata_phase_profile_scope_run_id_and_v2_tampering_is_rejected(self) -> None:
        created = self.ready()
        result = self.run_final(created)
        bundle_path = Path(created["bundle_path"])
        (bundle_path / MODULE.APPROVAL_NAME).unlink()
        attempt = self.first_attempt_path(created)
        metadata_path = attempt / "metadata.json"
        completion_path = attempt / "completion.json"
        original_metadata = metadata_path.read_bytes()
        original_completion = completion_path.read_bytes()
        cases = {
            "profile": lambda value: value.__setitem__("profile", "code"),
            "scope": lambda value: value.__setitem__("scope", "changed"),
            "run_id": lambda value: value.__setitem__("run_id", "wrong-run"),
            "missing phase": lambda value: value["phases"].pop(),
            "illegal skip": lambda value: value["phases"][0].update(
                status="skip", exit_code=0
            ),
            "v2": lambda value: value.__setitem__("schema_version", 2),
        }
        for label, mutate in cases.items():
            with self.subTest(label=label):
                metadata = json.loads(original_metadata)
                mutate(metadata)
                self.rewrite_attempt_metadata(attempt, metadata)
                with self.assertRaises(MODULE.ReviewBundleError):
                    MODULE.validate_bundle(self.candidate, created["bundle_id"])
                metadata_path.write_bytes(original_metadata)
                completion_path.write_bytes(original_completion)
        self.assertEqual(result["state"], "MERGEABLE")

    def test_artifact_symlink_missing_completion_and_unknown_object_are_rejected(self) -> None:
        created = self.ready()
        self.run_final(created)
        bundle_path = Path(created["bundle_path"])
        (bundle_path / MODULE.APPROVAL_NAME).unlink()
        attempt = self.first_attempt_path(created)
        verify_log = attempt / "verify.log"
        original_log = verify_log.read_bytes()
        verify_log.write_bytes(original_log + b"tamper")
        with self.assertRaisesRegex(MODULE.ReviewBundleError, "artifact"):
            MODULE.validate_bundle(self.candidate, created["bundle_id"])
        verify_log.write_bytes(original_log)
        outside = self.temp / "outside.log"
        outside.write_text("outside", encoding="utf-8")
        verify_log.unlink()
        verify_log.symlink_to(outside)
        with self.assertRaises(MODULE.UnsafeObjectError):
            MODULE.validate_bundle(self.candidate, created["bundle_id"])
        verify_log.unlink()
        verify_log.write_bytes(original_log)
        completion = attempt / MODULE.COMPLETION_NAME
        original_completion = completion.read_bytes()
        completion.unlink()
        with self.assertRaises(MODULE.ReviewBundleError):
            MODULE.validate_bundle(self.candidate, created["bundle_id"])
        completion.write_bytes(original_completion)
        (attempt / "unknown.bin").write_bytes(b"unknown")
        with self.assertRaises(MODULE.UnsafeObjectError):
            MODULE.validate_bundle(self.candidate, created["bundle_id"])

    def test_wrong_final_approval_binding_is_rejected(self) -> None:
        created = self.ready()
        self.run_final(created)
        approval_path = Path(created["bundle_path"]) / MODULE.APPROVAL_NAME
        original = approval_path.read_bytes()
        cases = {
            "routing": ("routing_sha256", "0" * 64),
            "other verification id": ("attempt_id", "attempt-other-verification"),
            "other verification digest": ("attempt_sha256", "0" * 64),
        }
        for label, (field, value) in cases.items():
            with self.subTest(label=label):
                approval = json.loads(original)
                approval[field] = value
                approval_path.write_bytes(MODULE.canonical_json_bytes(approval))
                with self.assertRaisesRegex(MODULE.ReviewBundleError, "approval"):
                    MODULE.validate_bundle(self.candidate, created["bundle_id"])
                status = MODULE.status_bundle(self.candidate, created["bundle_id"])
                self.assertEqual(status["exit_code"], MODULE.INVALID_EVIDENCE)
                approval_path.write_bytes(original)
        self.assertEqual(
            MODULE.status_bundle(self.candidate, created["bundle_id"])["state"],
            "MERGEABLE",
        )

    def test_dirty_checkouts_ancestry_and_verifier_mutation_fail_closed(self) -> None:
        created = self.ready()
        dirty_candidate = self.candidate / "dirty-candidate"
        dirty_candidate.write_text("dirty", encoding="utf-8")
        with self.assertRaisesRegex(MODULE.ReviewBundleError, "dirty"):
            self.run_final(created)
        dirty_candidate.unlink()
        dirty_target = self.repo / "dirty-target"
        dirty_target.write_text("dirty", encoding="utf-8")
        with self.assertRaisesRegex(MODULE.ReviewBundleError, "dirty"):
            self.run_final(created)
        dirty_target.unlink()
        with self.fake_environment(FAKE_VERIFY_MODE="mutate"):
            with self.assertRaisesRegex(MODULE.ReviewBundleError, "dirty"):
                self.run_final(created)
        self.assertFalse((Path(created["bundle_path"]) / MODULE.APPROVAL_NAME).exists())
        (self.candidate / "mutation.txt").unlink()

        tree = self.git("rev-parse", f"{self.base}^{{tree}}", cwd=self.repo)
        sibling = subprocess.run(
            ["git", "commit-tree", tree, "-p", self.base],
            cwd=self.repo, text=True, input="sibling target\n",
            capture_output=True, check=True,
        ).stdout.strip()
        with self.assertRaisesRegex(MODULE.ReviewBundleError, "not an ancestor"):
            MODULE.create_bundle(
                self.candidate, sibling, "HEAD", GLOSSARY_SHA256, self.classifier
            )

    def test_shell_final_gate_rejects_ref_move_during_verification(self) -> None:
        created = self.ready()
        environment = os.environ.copy()
        environment.update(PYTHONDONTWRITEBYTECODE="1", FAKE_VERIFY_MODE="move-ref")
        proc = subprocess.run(
            ["bash", ".claude/scripts/review_final_gate.sh", "candidate", "target"],
            cwd=self.repo,
            text=True,
            capture_output=True,
            env=environment,
            check=False,
        )
        self.assertEqual(proc.returncode, MODULE.STALE_EVIDENCE, proc.stdout + proc.stderr)
        self.assertIn("branch ref moved", proc.stderr)
        self.assertFalse((Path(created["bundle_path"]) / MODULE.APPROVAL_NAME).exists())

    def test_status_is_byte_for_byte_read_only_and_reports_lifecycle_codes(self) -> None:
        created = self.ready()
        bundle_path = Path(created["bundle_path"])
        before = self.evidence_snapshot(bundle_path)
        first = MODULE.status_bundle(self.candidate, created["bundle_id"])
        second = MODULE.status_bundle(self.candidate, created["bundle_id"])
        after = self.evidence_snapshot(bundle_path)
        self.assertEqual(first, second)
        self.assertEqual(first["state"], "FINAL_GATE_REQUIRED")
        self.assertEqual(first["exit_code"], MODULE.FINAL_GATE_REQUIRED)
        self.assertTrue(first["ready"])
        self.assertEqual(before, after)

    def test_passing_attempt_without_approval_is_reused_without_rerun(self) -> None:
        created = self.ready()
        count = self.temp / "verify-count"
        with self.fake_environment(FAKE_VERIFY_COUNT=str(count)):
            self.run_final(created)
            approval = Path(created["bundle_path"]) / MODULE.APPROVAL_NAME
            approval.unlink()
            status = MODULE.status_bundle(self.candidate, created["bundle_id"])
            self.assertEqual(status["exit_code"], MODULE.FINAL_APPROVAL_REQUIRED)
            sealed = self.run_final(created)
        self.assertEqual(sealed["state"], "MERGEABLE")
        self.assertEqual(count.read_text(encoding="utf-8").splitlines(), ["run"])

    def test_bundle_flock_serializes_concurrent_final_gate(self) -> None:
        created = self.create()
        bundle_path = Path(created["bundle_path"])
        started = self.temp / "child-started"
        acquired = self.temp / "child-acquired"
        child_code = """
import importlib.util
import pathlib
import sys
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('review_bundle_child', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
pathlib.Path(sys.argv[3]).write_text('started', encoding='utf-8')
with module.bundle_lock(pathlib.Path(sys.argv[2])):
    pathlib.Path(sys.argv[4]).write_text('acquired', encoding='utf-8')
"""
        with MODULE.bundle_lock(bundle_path):
            proc = subprocess.Popen(
                [
                    sys.executable, "-B", "-c", child_code, str(SCRIPT),
                    str(bundle_path), str(started), str(acquired),
                ],
                cwd=self.candidate,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            deadline = time.monotonic() + 5
            while not started.exists() and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(started.exists(), "child did not reach lock attempt")
            time.sleep(0.2)
            self.assertFalse(acquired.exists(), "concurrent lock unexpectedly succeeded")
        stdout, stderr = proc.communicate(timeout=5)
        self.assertEqual(proc.returncode, 0, stdout + stderr)
        self.assertTrue(acquired.exists())


if __name__ == "__main__":
    unittest.main()
