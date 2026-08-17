#!/usr/bin/env python3
"""Fetch and bind a GitHub Actions run into the schema-v5 external CI proof.

The final gate never accepts caller-supplied CI JSON.  This trusted
control-plane helper is the only component that may query the GitHub REST API
through ``gh`` at final-gate time, and it writes a canonical
``github-actions-proof.json`` artifact only after every binding check passes:

- the run belongs to the contract-fixed repository;
- the event is in the contract allow-list (workflow_dispatch / push; pull
  request merge-ref results are rejected);
- ``head_sha`` equals the exact candidate head;
- the run path equals the contract workflow path;
- the workflow blob at the candidate head equals the workflow blob at the
  target/base head (no workflow drift), and the recorded workflow blob SHA-1
  and SHA-256 identities are recomputed and re-verified;
- the run is ``completed`` with ``conclusion == success``;
- every contract-required job is present in the run's job list and is itself
  ``completed``/``success`` (optional or skipped jobs never become required).

API response digests are recorded over the exact raw bytes returned by ``gh``
so a later read-only validator can confirm the recorded proof was generated
from one fixed API snapshot.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

PROOF_SCHEMA = "dcss-zh-github-actions-proof-v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_OID_RE = re.compile(r"^[0-9a-f]{40,64}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SAFE_PATH_RE = re.compile(r"^[A-Za-z0-9_./-]+$")

TRUSTED_PREFIXES = (
    ".claude/scripts/",
    ".github/workflows/",
)
GH_OK = 0
GH_FAIL = 1


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return GH_FAIL


def _scrubbed_environment() -> dict[str, str]:
    environment = os.environ.copy()
    for name in list(environment):
        if name in {
            "BASH_ENV",
            "ENV",
            "CDPATH",
            "GIT_EXEC_PATH",
            "GIT_DIR",
            "GIT_WORK_TREE",
            "GIT_INDEX_FILE",
            "GIT_OBJECT_DIRECTORY",
            "GIT_ALTERNATE_OBJECT_DIRECTORIES",
            "GIT_COMMON_DIR",
            "GIT_CEILING_DIRECTORIES",
            "GIT_DISCOVERY_ACROSS_FILESYSTEM",
            "GIT_EXTERNAL_DIFF",
            "GIT_DIFF_OPTS",
            "GH_HOST",
            "GH_ENTERPRISE_TOKEN",
            "LD_PRELOAD",
            "LD_LIBRARY_PATH",
            "PYTHONHOME",
            "PYTHONPATH",
            "MAKEFLAGS",
            "MFLAGS",
            "MAKEFILES",
            "CC",
            "CXX",
            "CFLAGS",
            "CXXFLAGS",
            "CPPFLAGS",
            "LDFLAGS",
        } or name.startswith(("GIT_", "ZH_VERIFY_", "ZH_RUNTIME_")):
            environment.pop(name, None)
    environment["GIT_NO_REPLACE_OBJECTS"] = "1"
    return environment


def _run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        command,
        cwd=os.fspath(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=_scrubbed_environment(),
    )


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _load_spec(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    try:
        spec = json.loads(data.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"external CI spec is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(spec, dict):
        raise ValueError("external CI spec must be a JSON object")
    expected_fields = frozenset(
        (
            "enabled",
            "repository",
            "workflow_path",
            "allowed_events",
            "externalizable_phases",
            "required_jobs",
            "proof_artifact",
            "proof_schema",
        )
    )
    if frozenset(spec) != expected_fields:
        raise ValueError("external CI spec top-level fields are invalid")
    for key in sorted(expected_fields):
        if key not in spec:
            raise ValueError(f"external CI spec is missing {key}")
    if spec.get("enabled") is not True:
        raise ValueError("external CI is not enabled")
    externalizable = spec.get("externalizable_phases")
    if not isinstance(externalizable, list) or not externalizable:
        raise ValueError("external CI externalizable_phases are invalid")
    if not all(isinstance(phase, str) and phase for phase in externalizable):
        raise ValueError("external CI externalizable_phases are invalid")
    proof_artifact = spec.get("proof_artifact")
    if (
        not isinstance(proof_artifact, str)
        or not proof_artifact
        or "/" in proof_artifact
        or "\\" in proof_artifact
    ):
        raise ValueError("external CI proof_artifact is invalid")
    repository = spec.get("repository")
    if not isinstance(repository, str) or not REPOSITORY_RE.fullmatch(repository):
        raise ValueError("external CI repository is invalid")
    workflow_path = spec.get("workflow_path")
    if (
        not isinstance(workflow_path, str)
        or not SAFE_PATH_RE.fullmatch(workflow_path)
        or not workflow_path.startswith(TRUSTED_PREFIXES)
    ):
        raise ValueError("external CI workflow path is invalid")
    events = spec.get("allowed_events")
    if not isinstance(events, list) or not events or not all(
        isinstance(event, str) and event for event in events
    ):
        raise ValueError("external CI allowed_events are invalid")
    jobs = spec.get("required_jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ValueError("external CI required_jobs are invalid")
    seen_jobs: set[str] = set()
    covered_phases: set[str] = set()
    for index, job in enumerate(jobs):
        if not isinstance(job, dict) or frozenset(job) != frozenset(
            ("id", "name_contains", "phases")
        ):
            raise ValueError(f"external CI required_jobs[{index}] is invalid")
        job_id = job.get("id")
        if not isinstance(job_id, str) or not job_id or job_id in seen_jobs:
            raise ValueError(f"external CI required job id is invalid: {job_id!r}")
        seen_jobs.add(job_id)
        name_contains = job.get("name_contains")
        if not isinstance(name_contains, str) or not name_contains:
            raise ValueError(f"external CI required job {job_id} has no name matcher")
        job_phases = job.get("phases")
        if not isinstance(job_phases, list) or not job_phases:
            raise ValueError(f"external CI required job {job_id} has no phases")
        for phase in job_phases:
            if phase not in externalizable:
                raise ValueError(
                    f"external CI required job {job_id} covers a phase that is "
                    "not externalizable"
                )
            covered_phases.add(phase)
    if covered_phases != set(externalizable):
        raise ValueError(
            "external CI required jobs must cover exactly the externalizable "
            "phase set"
        )
    if spec.get("proof_schema") != PROOF_SCHEMA:
        raise ValueError("external CI proof schema is invalid")
    return spec


def _api_digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _parse_json(raw: bytes, label: str) -> dict[str, Any]:
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _git(repo: Path, *args: str) -> bytes:
    proc = _run(["git", "-C", os.fspath(repo), *args], repo)
    if proc.returncode:
        message = proc.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(message or f"git {' '.join(args)} failed")
    return proc.stdout


def _workflow_blob(repo: Path, commit: str, workflow_path: str) -> tuple[str, bytes]:
    if not GIT_OID_RE.fullmatch(commit):
        raise ValueError("immutable commit id is invalid")
    blob_id = _git(repo, "rev-parse", f"{commit}:{workflow_path}").decode(
        "ascii", errors="strict"
    ).strip()
    if not GIT_OID_RE.fullmatch(blob_id):
        raise ValueError(f"workflow blob id is invalid at {commit}")
    content = _git(repo, "cat-file", "blob", blob_id)
    return blob_id, content


def _api_jobs(
    spec: dict[str, Any],
    repository: str,
    run_id: int,
    gh_bin: str,
    repo: Path,
) -> tuple[list[dict[str, Any]], bytes, dict[str, Any]]:
    job_proc = _run(
        [
            gh_bin,
            "--hostname",
            "github.com",
            "api",
            f"repos/{repository}/actions/runs/{run_id}/jobs?per_page=100",
        ],
        repo,
    )
    if job_proc.returncode:
        message = job_proc.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(message or "gh jobs API call failed")
    raw_jobs = job_proc.stdout
    jobs_value = _parse_json(raw_jobs, "GitHub Actions jobs response")
    jobs = jobs_value.get("jobs")
    if not isinstance(jobs, list):
        raise ValueError("GitHub Actions jobs response is missing jobs")
    total_count = jobs_value.get("total_count")
    if (
        isinstance(total_count, bool)
        or not isinstance(total_count, int)
        or total_count != len(jobs)
    ):
        raise ValueError(
            "GitHub Actions jobs response is incomplete or has an invalid total_count"
        )
    return jobs, raw_jobs, jobs_value


def fetch_and_bind_proof(
    run_id: int,
    spec: dict[str, Any],
    candidate_head: str,
    target_head: str,
    repo: Path,
    output: Path,
    gh_bin: str,
) -> dict[str, Any]:
    if isinstance(run_id, bool) or not isinstance(run_id, int) or run_id <= 0:
        raise ValueError("GitHub Actions run id must be a positive integer")
    repository = str(spec["repository"])
    run_proc = _run(
        [
            gh_bin,
            "--hostname",
            "github.com",
            "api",
            f"repos/{repository}/actions/runs/{run_id}",
        ],
        repo,
    )
    if run_proc.returncode:
        message = run_proc.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(message or "gh run API call failed")
    raw_run = run_proc.stdout
    run = _parse_json(raw_run, "GitHub Actions run response")
    if run.get("id") != run_id:
        raise ValueError("run id does not match the requested run id")

    run_repository = run.get("repository")
    if not isinstance(run_repository, dict) or run_repository.get(
        "full_name"
    ) != repository:
        raise ValueError("run repository does not match the contract repository")
    head_repository = run.get("head_repository")
    if not isinstance(head_repository, dict) or head_repository.get(
        "full_name"
    ) != repository:
        raise ValueError(
            "run head_repository does not match the contract repository"
        )

    event = run.get("event")
    if event not in spec["allowed_events"]:
        raise ValueError(
            f"workflow event {event!r} is not allowed by the contract"
        )
    head_sha = run.get("head_sha")
    if not isinstance(head_sha, str) or not GIT_OID_RE.fullmatch(head_sha):
        raise ValueError("run head_sha is invalid")
    if head_sha != candidate_head:
        raise ValueError(
            f"run head_sha {head_sha} does not match candidate {candidate_head}"
        )
    head_branch = run.get("head_branch")
    if not isinstance(head_branch, str) or not head_branch:
        raise ValueError("run head_branch is missing")
    path = run.get("path")
    if path != spec["workflow_path"]:
        raise ValueError(
            f"run workflow path {path!r} does not match contract "
            f"{spec['workflow_path']!r}"
        )
    status = run.get("status")
    conclusion = run.get("conclusion")
    if status != "completed" or conclusion != "success":
        raise ValueError(
            f"run must be completed/success, got status={status!r} "
            f"conclusion={conclusion!r}"
        )
    run_url = run.get("html_url")
    expected_url = f"https://github.com/{repository}/actions/runs/{run_id}"
    if run_url != expected_url:
        raise ValueError("run html_url does not match the bound run id")

    candidate_blob, candidate_content = _workflow_blob(
        repo, candidate_head, str(spec["workflow_path"])
    )
    target_blob, target_content = _workflow_blob(
        repo, target_head, str(spec["workflow_path"])
    )
    if candidate_blob != target_blob or candidate_content != target_content:
        raise ValueError(
            "workflow drifted between target/base and candidate heads"
        )
    candidate_sha256 = hashlib.sha256(candidate_content).hexdigest()
    target_sha256 = hashlib.sha256(target_content).hexdigest()
    if candidate_sha256 != target_sha256:
        raise ValueError("workflow blob digest drifted between target and candidate")

    jobs, raw_jobs, _jobs_value = _api_jobs(spec, repository, run_id, gh_bin, repo)
    required_jobs: list[dict[str, Any]] = []
    for planned in spec["required_jobs"]:
        job_id = planned.get("id")
        name_contains = planned.get("name_contains")
        if not isinstance(job_id, str) or not job_id:
            raise ValueError("contract required job id is invalid")
        if not isinstance(name_contains, str) or not name_contains:
            raise ValueError("contract required job name matcher is invalid")
        matched = [
            job
            for job in jobs
            if isinstance(job, dict)
            and isinstance(job.get("name"), str)
            and name_contains in job["name"]
        ]
        if len(matched) != 1:
            raise ValueError(
                f"required job {job_id!r} must match exactly one run job, "
                f"found {len(matched)}"
            )
        job = matched[0]
        job_status = job.get("status")
        job_conclusion = job.get("conclusion")
        if job_status != "completed" or job_conclusion != "success":
            raise ValueError(
                f"required job {job_id!r} failed or did not complete: "
                f"status={job_status!r} conclusion={job_conclusion!r}"
            )
        api_job_id = job.get("id")
        if isinstance(api_job_id, bool) or not isinstance(api_job_id, int) or api_job_id <= 0:
            raise ValueError(f"required job {job_id!r} has an invalid API id")
        required_jobs.append(
            {
                "id": job_id,
                "name": str(job["name"]),
                "api_job_id": api_job_id,
                "status": job_status,
                "conclusion": job_conclusion,
            }
        )

    proof = {
        "schema": spec["proof_schema"],
        "repository": repository,
        "run_id": run_id,
        "run_url": expected_url,
        "event": event,
        "head_branch": head_branch,
        "head_sha": head_sha,
        "workflow_path": str(spec["workflow_path"]),
        "workflow_sha": candidate_blob,
        "workflow_blob_sha256_candidate": candidate_sha256,
        "workflow_blob_sha256_target": target_sha256,
        "status": status,
        "conclusion": conclusion,
        "required_jobs": required_jobs,
        "api_digests": {
            "run_response_sha256": _api_digest(raw_run),
            "jobs_response_sha256": _api_digest(raw_jobs),
        },
        "fetched_at": _utc_timestamp(),
    }
    return proof


def _utc_timestamp() -> str:
    import datetime

    return datetime.datetime.now(datetime.timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--external-ci-json", required=True)
    parser.add_argument("--candidate-head", required=True)
    parser.add_argument("--target-head", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--gh-bin", default=None)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        run_id_raw = args.run_id
        try:
            run_id = int(run_id_raw)
        except ValueError:
            raise ValueError(f"GitHub Actions run id is not an integer: {run_id_raw}")
        spec = _load_spec(Path(args.external_ci_json))
        gh_bin = args.gh_bin or os.environ.get("GH_BIN") or "gh"
        gh_path = shutil.which(gh_bin)
        if not gh_path:
            raise ValueError(f"gh binary is unavailable: {gh_bin}")
        proof_path = Path(args.output)
        proof_path.parent.mkdir(parents=True, exist_ok=True)
        proof = fetch_and_bind_proof(
            run_id,
            spec,
            str(args.candidate_head),
            str(args.target_head),
            Path(args.repo),
            proof_path,
            gh_path,
        )
        proof_bytes = canonical_json_bytes(proof)
        temporary = proof_path.with_name(
            f".{proof_path.name}.tmp.{os.getpid()}"
        )
        with open(temporary, "wb") as stream:
            stream.write(proof_bytes)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, proof_path)
        sys.stdout.buffer.write(proof_bytes)
        sys.stdout.buffer.write(b"\n")
        return GH_OK
    except (ValueError, OSError) as exc:
        return fail(str(exc))


if __name__ == "__main__":
    raise SystemExit(main())
