#!/usr/bin/env python3
"""Tests for Issue 66 C — SourceDB lowercase collision scanner and pipeline."""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / ".claude/scripts/scan_i18n.py"
FIXTURES = ROOT / ".claude/scripts/tests/fixtures/source-key-collisions"

# Import the module for unit testing
import importlib.util
SPEC = importlib.util.spec_from_file_location("scan_i18n", SCRIPT)
SCAN = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(SCAN)


def _run_cmd(*args, expect_failure=False):
    """Run scan_i18n.py with given args, return (exit_code, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)] + list(args),
        capture_output=True, text=True,
        timeout=30,
    )
    ec = result.returncode
    if expect_failure:
        if ec == 0:
            print(f"UNEXPECTED SUCCESS: {' '.join(args)}")
            print(f"stdout: {result.stdout[:500]}")
            print(f"stderr: {result.stderr[:500]}")
    else:
        if ec != 0:
            print(f"UNEXPECTED FAILURE: {' '.join(args)}")
            print(f"stdout: {result.stdout[:500]}")
            print(f"stderr: {result.stderr[:500]}")
    return ec, result.stdout, result.stderr


class TestSourceKeyCollisions(unittest.TestCase):
    """Test the source-key-collisions command."""

    def test_no_collisions(self):
        """No collisions should return 0."""
        f = str(FIXTURES / "no_collisions.txt")
        ec, out, err = _run_cmd("source-key-collisions", "--source-txt", f)
        self.assertEqual(ec, 0, f"Expected exit 0, got {ec}")
        self.assertIn("OK: No canonical key collisions", out)

    def test_case_collisions_detected(self):
        """Case collisions should be detected and return 1."""
        f = str(FIXTURES / "case_collisions.txt")
        ec, out, err = _run_cmd("source-key-collisions", "--source-txt", f)
        self.assertEqual(ec, 1, f"Expected exit 1, got {ec}")
        self.assertIn("WARNING: 5 collision group(s) found", out)


class TestSourceKeyCollisionInventory(unittest.TestCase):
    """Test the source-key-collision-inventory command."""

    def test_generate_inventory(self):
        """Generate inventory for collisions fixture."""
        f = str(FIXTURES / "case_collisions.txt")
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf:
            out_path = tf.name
        try:
            ec, out, err = _run_cmd(
                "source-key-collision-inventory",
                "--source-txt", f,
                "--output", out_path)
            self.assertEqual(ec, 0, f"Expected exit 0, got {ec}")
            self.assertTrue(os.path.exists(out_path))
            with open(out_path) as fh:
                data = json.load(fh)
            self.assertEqual(data['schema'], 'dcss-zh-source-inventory-v1')
            self.assertIn('groups', data)
            self.assertEqual(len(data['groups']), 5)
            self.assertEqual(data['summary']['collision_groups'], 5)
        finally:
            os.unlink(out_path)

    def test_check_inventory(self):
        """Check inventory matches source.txt."""
        f = str(FIXTURES / "case_collisions.txt")
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf:
            out_path = tf.name
        try:
            _run_cmd("source-key-collision-inventory",
                     "--source-txt", f, "--output", out_path)
            ec, out, err = _run_cmd(
                "source-key-collision-inventory",
                "--source-txt", f, "--check", out_path)
            self.assertEqual(ec, 0, f"Expected exit 0, got {ec}")
            self.assertIn("OK: Inventory matches", out)
        finally:
            os.unlink(out_path)

    def test_check_mismatch(self):
        """Check should fail when source.txt differs."""
        f1 = str(FIXTURES / "case_collisions.txt")
        f2 = str(FIXTURES / "no_collisions.txt")
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf:
            out_path = tf.name
        try:
            # Generate from collisions fixture
            _run_cmd("source-key-collision-inventory",
                     "--source-txt", f1, "--output", out_path)
            # Check against different source.txt
            ec, out, err = _run_cmd(
                "source-key-collision-inventory",
                "--source-txt", f2, "--check", out_path)
            self.assertNotEqual(ec, 0, "Expected non-zero for mismatch")
        finally:
            os.unlink(out_path)


class TestSourceDBStructure(unittest.TestCase):
    """Test the source-db-structure command."""

    def test_normal_file(self):
        """No structural issues in clean file."""
        f = str(FIXTURES / "no_collisions.txt")
        ec, out, err = _run_cmd("source-db-structure",
                                "--source-txt", f)
        self.assertEqual(ec, 0)
        self.assertIn("No structural issues", out)

    def test_structural_issues_detected(self):
        """Structural issues should be detected."""
        f = str(FIXTURES / "structural_issues.txt")
        ec, out, err = _run_cmd(
            "source-db-structure",
            "--source-txt", f,
            "--exit-nonzero-if-issues")
        self.assertNotEqual(ec, 0, "Expected non-zero for structural issues")
        self.assertIn("structural issue", out.lower())
        self.assertIn("MISSING_DELIMITER", out)


class TestValidateSourceClassificationShard(unittest.TestCase):
    """Test validate-source-classification-shard."""

    def _make_shard(self, groups, schema="dcss-zh-source-classification-shard-v1"):
        d = {"schema": schema, "kind": "collision", "groups": groups}
        return d

    def test_valid_shard(self):
        """Valid shard passes validation."""
        gid = "sourcedb-v1:" + "a" * 64
        fp = "b" * 64
        shard = self._make_shard([{
            "group_id": gid,
            "group_fingerprint": fp,
            "classification": {
                "cause": "case_variant_duplicate",
                "action": "dedupe",
                "status": "classified",
                "owner": "translator",
                "confidence": "high",
                "evidence": [],
                "rationale": "Test",
            }
        }])
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf:
            json.dump(shard, tf)
            tf_path = tf.name
        try:
            ec, out, err = _run_cmd(
                "validate-source-classification-shard",
                "--kind", "collision",
                "--shard", tf_path)
            self.assertEqual(ec, 0, f"Expected exit 0, got {ec}")
        finally:
            os.unlink(tf_path)

    def test_malformed_shard(self):
        """Missing group_id should fail."""
        shard = self._make_shard([{
            "group_fingerprint": "b" * 64,
            "classification": {
                "cause": "case_variant_duplicate",
                "action": "dedupe",
                "status": "classified",
            }
        }])
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf:
            json.dump(shard, tf)
            tf_path = tf.name
        try:
            ec, out, err = _run_cmd(
                "validate-source-classification-shard",
                "--kind", "collision",
                "--shard", tf_path)
            self.assertNotEqual(ec, 0, "Expected non-zero for malformed")
        finally:
            os.unlink(tf_path)

    def test_unknown_cause_rejected(self):
        """Groups with cause='unknown' should be rejected."""
        gid = "sourcedb-v1:" + "a" * 64
        shard = self._make_shard([{
            "group_id": gid,
            "group_fingerprint": "b" * 64,
            "classification": {
                "cause": "unknown",
                "action": "defer_semantic_ruling",
                "status": "needs_semantic_ruling",
            }
        }])
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf:
            json.dump(shard, tf)
            tf_path = tf.name
        try:
            ec, out, err = _run_cmd(
                "validate-source-classification-shard",
                "--kind", "collision",
                "--shard", tf_path)
            self.assertNotEqual(ec, 0,
                                "Expected non-zero for unknown cause")
        finally:
            os.unlink(tf_path)

    def test_fingerprint_drift_detected(self):
        """Fingerprint mismatch between shard and inventory should fail."""
        inv_f = str(FIXTURES / "case_collisions.txt")
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as inv_tf:
            inv_path = inv_tf.name
        try:
            # Generate inventory from fixture
            _run_cmd("source-key-collision-inventory",
                     "--source-txt", inv_f, "--output", inv_path)

            # Load inventory to get a real group_id and wrong fingerprint
            with open(inv_path) as fh:
                inv_data = json.load(fh)
            if not inv_data.get('groups'):
                self.skipTest("No collision groups in fixture")
            first_group = inv_data['groups'][0]
            gid = first_group['group_id']

            # Create shard with WRONG fingerprint
            shard = self._make_shard([{
                "group_id": gid,
                "group_fingerprint": "f" * 64,  # wrong fingerprint
                "classification": {
                    "cause": "case_variant_duplicate",
                    "action": "dedupe",
                    "status": "classified",
                }
            }])
            with tempfile.NamedTemporaryFile(
                    mode='w', suffix='.json', delete=False) as shard_tf:
                json.dump(shard, shard_tf)
                shard_path = shard_tf.name
            try:
                ec, out, err = _run_cmd(
                    "validate-source-classification-shard",
                    "--kind", "collision",
                    "--inventory", inv_path,
                    "--shard", shard_path)
                self.assertNotEqual(ec, 0,
                                    "Expected non-zero for fingerprint drift")
            finally:
                os.unlink(shard_path)
        finally:
            os.unlink(inv_path)


class TestSourceMissingKeyInventory(unittest.TestCase):
    """Test source-missing-key-inventory."""

    def test_generate_with_source_dir(self):
        """Generate missing-key inventory (no source dir for speed)."""
        f = str(FIXTURES / "no_collisions.txt")
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf:
            out_path = tf.name
        try:
            ec, out, err = _run_cmd(
                "source-missing-key-inventory",
                "--source-txt", f,
                "--output", out_path)
            self.assertEqual(ec, 0)
            self.assertTrue(os.path.exists(out_path))
            with open(out_path) as fh:
                data = json.load(fh)
            self.assertEqual(data['schema'],
                             'dcss-zh-missing-key-inventory-v1')
        finally:
            os.unlink(out_path)


class TestValidateSourceAdjudications(unittest.TestCase):
    """Test validate-source-adjudications."""

    def test_valid_adjudications(self):
        """Two valid adjudication files pass."""
        schema = "dcss-zh-source-adjudication-v1"
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf1:
            json.dump({"schema": schema, "groups": []}, tf1)
            p1 = tf1.name
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf2:
            json.dump({"schema": schema, "groups": []}, tf2)
            p2 = tf2.name
        try:
            ec, out, err = _run_cmd(
                "validate-source-adjudications",
                "--primary", p1,
                "--secondary", p2)
            self.assertEqual(ec, 0)
        finally:
            os.unlink(p1)
            os.unlink(p2)

    def test_duplicate_group_id_across_files(self):
        """Same group_id in both files should fail."""
        schema = "dcss-zh-source-adjudication-v1"
        gid = "sourcedb-v1:" + "a" * 64
        g = {"group_id": gid}
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf1:
            json.dump({"schema": schema, "groups": [g]}, tf1)
            p1 = tf1.name
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf2:
            json.dump({"schema": schema, "groups": [g]}, tf2)
            p2 = tf2.name
        try:
            ec, out, err = _run_cmd(
                "validate-source-adjudications",
                "--primary", p1,
                "--secondary", p2)
            self.assertNotEqual(ec, 0,
                                "Expected non-zero for duplicate gid")
        finally:
            os.unlink(p1)
            os.unlink(p2)


class TestAssembleSourceKeyCollisionClassifications(unittest.TestCase):
    """Test assemble-source-key-collision-classifications."""

    def test_assemble_from_inventory(self):
        """Assemble manifest from inventory."""
        f = str(FIXTURES / "case_collisions.txt")
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as inv_tf:
            inv_path = inv_tf.name
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as out_tf:
            out_path = out_tf.name
        try:
            _run_cmd("source-key-collision-inventory",
                     "--source-txt", f, "--output", inv_path)
            ec, out, err = _run_cmd(
                "assemble-source-key-collision-classifications",
                "--inventory", inv_path,
                "--output", out_path)
            self.assertEqual(ec, 0)
            self.assertTrue(os.path.exists(out_path))
            with open(out_path) as fh:
                data = json.load(fh)
            self.assertEqual(data['schema'],
                             'dcss-zh-source-collision-manifest-v1')
            self.assertIn('groups', data)
        finally:
            for p in [inv_path, out_path]:
                if os.path.exists(p):
                    os.unlink(p)


class TestAssembleSourceMissingKeyClassifications(unittest.TestCase):
    """Test assemble-source-missing-key-classifications."""

    def test_assemble_missing_key_manifest(self):
        """Assemble missing-key manifest."""
        f = str(FIXTURES / "no_collisions.txt")
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as inv_tf:
            inv_path = inv_tf.name
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as out_tf:
            out_path = out_tf.name
        try:
            _run_cmd("source-missing-key-inventory",
                     "--source-txt", f, "--output", inv_path)
            ec, out, err = _run_cmd(
                "assemble-source-missing-key-classifications",
                "--inventory", inv_path,
                "--output", out_path)
            self.assertEqual(ec, 0)
            with open(out_path) as fh:
                data = json.load(fh)
            self.assertEqual(data['schema'],
                             'dcss-zh-source-missing-key-manifest-v1')
        finally:
            for p in [inv_path, out_path]:
                if os.path.exists(p):
                    os.unlink(p)


class TestValidateSourceKeyCollisionClassifications(unittest.TestCase):
    """Test validate-source-key-collision-classifications."""

    def test_validate_manifest(self):
        """Validate a correctly assembled manifest."""
        f = str(FIXTURES / "case_collisions.txt")
        with tempfile.TemporaryDirectory() as td:
            inv_path = os.path.join(td, "inventory.json")
            out_path = os.path.join(td, "manifest.json")

            # Generate inventory
            _run_cmd("source-key-collision-inventory",
                     "--source-txt", f, "--output", inv_path)

            # Load inventory and add classifications to all groups
            with open(inv_path) as fh:
                inv_data = json.load(fh)
            for g in inv_data.get('groups', []):
                g['classification'] = {
                    "cause": "case_variant_duplicate",
                    "action": "dedupe",
                    "status": "classified",
                    "owner": "translator",
                    "confidence": "high",
                    "evidence": [],
                    "rationale": "Test classification for validation",
                }
            # Write classified inventory
            classified_inv = os.path.join(td, "classified_inv.json")
            with open(classified_inv, 'w') as fh:
                json.dump(inv_data, fh)

            # Assemble with classified inventory as a shard
            ec, out, err = _run_cmd(
                "assemble-source-key-collision-classifications",
                "--inventory", inv_path,
                "--shards", classified_inv,
                "--output", out_path)
            self.assertEqual(ec, 0)

            # Now validate
            ec, out, err = _run_cmd(
                "validate-source-key-collision-classifications",
                "--manifest", out_path,
                "--inventory", inv_path)
            self.assertEqual(ec, 0,
                             f"Expected exit 0, got {ec}\n{out}\n{err}")

    def test_incomplete_manifest_fails(self):
        """Manifest with unclassified groups should fail."""
        manifest = {
            "schema": "dcss-zh-source-collision-manifest-v1",
            "groups": [{
                "group_id": "sourcedb-v1:" + "a" * 64,
                "canonical_key": "test",
                "group_fingerprint": "b" * 64,
            }]
        }
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf:
            json.dump(manifest, tf)
            m_path = tf.name
        try:
            ec, out, err = _run_cmd(
                "validate-source-key-collision-classifications",
                "--manifest", m_path)
            self.assertNotEqual(ec, 0,
                                "Expected non-zero for incomplete manifest")
        finally:
            os.unlink(m_path)


class TestValidateSourceMissingKeyClassifications(unittest.TestCase):
    """Test validate-source-missing-key-classifications."""

    def test_validate_missing_key_manifest(self):
        """Validate a correctly assembled missing-key manifest."""
        f = str(FIXTURES / "no_collisions.txt")
        with tempfile.TemporaryDirectory() as td:
            inv_path = os.path.join(td, "inventory.json")
            out_path = os.path.join(td, "manifest.json")
            _run_cmd("source-missing-key-inventory",
                     "--source-txt", f, "--output", inv_path)
            _run_cmd("assemble-source-missing-key-classifications",
                     "--inventory", inv_path, "--output", out_path)
            ec, out, err = _run_cmd(
                "validate-source-missing-key-classifications",
                "--manifest", out_path,
                "--inventory", inv_path)
            self.assertEqual(ec, 0)


class TestSourceCallsiteReceipt(unittest.TestCase):
    """Test source-callsite-receipt."""

    def test_valid_delta(self):
        """Valid callsite delta is accepted."""
        delta = {
            "schema": "dcss-zh-source-callsite-delta-v1",
            "mappings": [
                {"old_key": "old_key_1", "new_key": "new_key_1"},
            ]
        }
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf:
            json.dump(delta, tf)
            d_path = tf.name
        try:
            ec, out, err = _run_cmd(
                "source-callsite-receipt",
                "--delta", d_path)
            self.assertEqual(ec, 0)
        finally:
            os.unlink(d_path)

    def test_dup_old_key_fails(self):
        """Duplicate old_key should be rejected."""
        delta = {
            "schema": "dcss-zh-source-callsite-delta-v1",
            "mappings": [
                {"old_key": "same_key", "new_key": "new_1"},
                {"old_key": "same_key", "new_key": "new_2"},
            ]
        }
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf:
            json.dump(delta, tf)
            d_path = tf.name
        try:
            ec, out, err = _run_cmd(
                "source-callsite-receipt",
                "--delta", d_path)
            self.assertNotEqual(ec, 0,
                                "Expected non-zero for duplicate old_key")
        finally:
            os.unlink(d_path)


class TestAssemblePostCoderSourceHandoff(unittest.TestCase):
    """Test assemble-post-coder-source-handoff."""

    def test_assemble_handoff(self):
        """Assemble handoff from collision manifest."""
        f = str(FIXTURES / "case_collisions.txt")
        with tempfile.TemporaryDirectory() as td:
            inv_path = os.path.join(td, "inv.json")
            coll_path = os.path.join(td, "coll.json")
            hf_path = os.path.join(td, "handoff.json")

            _run_cmd("source-key-collision-inventory",
                     "--source-txt", f, "--output", inv_path)
            _run_cmd("assemble-source-key-collision-classifications",
                     "--inventory", inv_path, "--output", coll_path)
            ec, out, err = _run_cmd(
                "assemble-post-coder-source-handoff",
                "--collision-manifest", coll_path,
                "--output", hf_path)
            self.assertEqual(ec, 0)
            self.assertTrue(os.path.exists(hf_path))
            with open(hf_path) as fh:
                data = json.load(fh)
            self.assertEqual(data['schema'], 'dcss-zh-source-handoff-v1')


class TestValidatePostCoderSourceHandoff(unittest.TestCase):
    """Test validate-post-coder-source-handoff."""

    def test_validate_handoff(self):
        """Validate a correctly assembled handoff."""
        f = str(FIXTURES / "case_collisions.txt")
        with tempfile.TemporaryDirectory() as td:
            inv_path = os.path.join(td, "inv.json")
            coll_path = os.path.join(td, "coll.json")
            hf_path = os.path.join(td, "handoff.json")

            _run_cmd("source-key-collision-inventory",
                     "--source-txt", f, "--output", inv_path)
            _run_cmd("assemble-source-key-collision-classifications",
                     "--inventory", inv_path, "--output", coll_path)
            _run_cmd("assemble-post-coder-source-handoff",
                     "--collision-manifest", coll_path,
                     "--output", hf_path)
            ec, out, err = _run_cmd(
                "validate-post-coder-source-handoff",
                "--handoff", hf_path)
            self.assertEqual(ec, 0)

    def test_missing_group_id_fails(self):
        """Handoff with missing group_id should fail."""
        handoff = {
            "schema": "dcss-zh-source-handoff-v1",
            "collision_groups": [{
                "canonical_key": "test",
            }],
            "missing_key_groups": [],
        }
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf:
            json.dump(handoff, tf)
            h_path = tf.name
        try:
            ec, out, err = _run_cmd(
                "validate-post-coder-source-handoff",
                "--handoff", h_path)
            self.assertNotEqual(ec, 0,
                                "Expected non-zero for missing group_id")
        finally:
            os.unlink(h_path)


class TestSourceDBCommandIntegrity(unittest.TestCase):
    """End-to-end verification of source-key-collisions on real source.txt.

    This test verifies the exact expected output on the frozen HEAD.
    """

    def test_production_source_txt(self):
        """Run on actual source.txt — must match exact summary."""
        source_txt = ROOT / "crawl-ref/source/dat/i18n/zh/source.txt"
        if not source_txt.exists():
            self.skipTest("Production source.txt not available")
        ec, out, err = _run_cmd(
            "source-key-collisions", "--source-txt", str(source_txt))
        self.assertEqual(ec, 1)
        # Exact summary from spec: 13226 / 13117 / 109 / 63 / 46
        self.assertIn("13226 / 13117 / 109", out)

    def test_production_inventory_deterministic(self):
        """Inventory must be deterministic (109 groups)."""
        source_txt = ROOT / "crawl-ref/source/dat/i18n/zh/source.txt"
        if not source_txt.exists():
            self.skipTest("Production source.txt not available")
        with tempfile.NamedTemporaryFile(
                mode='w', suffix='.json', delete=False) as tf:
            out_path = tf.name
        try:
            ec, out, err = _run_cmd(
                "source-key-collision-inventory",
                "--source-txt", str(source_txt),
                "--output", out_path)
            self.assertEqual(ec, 0)
            with open(out_path) as fh:
                data = json.load(fh)
            self.assertEqual(data['summary']['collision_groups'], 109)
            self.assertEqual(len(data['groups']), 109)
        finally:
            os.unlink(out_path)


if __name__ == "__main__":
    unittest.main()
