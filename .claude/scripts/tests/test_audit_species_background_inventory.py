#!/usr/bin/env python3

import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


TEST_DIR = Path(__file__).resolve().parent
SCRIPT = TEST_DIR.parent / "audit_species_background_inventory.py"

SPEC = importlib.util.spec_from_file_location(
    "audit_species_background_inventory", SCRIPT
)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
from i18n_shared import AuditInput


def review_input(path):
    data = path.read_bytes()
    return AuditInput(
        audit_commit=None,
        logical_path="fixtures/review.md",
        relative_path="fixtures/review.md",
        bytes=data,
        text=data.decode("utf-8", errors="strict"),
        sha256=hashlib.sha256(data).hexdigest(),
    )


def valid_rows():
    return [
        {
            "identity": "species:SP_TEST",
            "category": "species",
            "lifecycle": "current_playable",
            "current_chinese_name": "测试种族",
            "description_key": "Test Species",
            "english_description": "English.",
            "chinese_description": "中文。",
            "forms": {
                "plain": {"translation_present": True},
                "genus": {"translation_present": True},
            },
        },
        {
            "identity": "background:JOB_TEST",
            "category": "background",
            "lifecycle": "current_playable",
            "current_chinese_name": "测试背景",
            "description_key": "Test Background",
            "english_description": "English.",
            "chinese_description": "中文。",
            "forms": {
                "plain": {"translation_present": True},
            },
        },
    ]


class SpeciesBackgroundInventoryAuditTest(unittest.TestCase):
    def test_enum_parser_uses_only_active_concrete_identities(self):
        with tempfile.TemporaryDirectory() as directory:
            header = Path(directory) / "enum.txt"
            header.write_text(
                "SP_CURRENT,\n"
                "SP_ALIAS = SP_CURRENT,\n"
                "#if TAG_MAJOR_VERSION == 34\n"
                "SP_COMPAT,\n"
                "#endif\n",
                encoding="utf-8",
            )
            with mock.patch.object(
                MODULE, "active_source", return_value=header.read_text()
            ):
                self.assertEqual(
                    ["SP_CURRENT", "SP_COMPAT"],
                    MODULE.enum_identities(header, "SP_"),
                )

    def test_description_parser_reports_duplicate_runtime_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "descriptions.txt"
            path.write_text(
                "%%%%\nTest\nfirst\n%%%%\ntest\nsecond\n",
                encoding="utf-8",
            )
            entries, duplicates = MODULE.description_entries(path)
        self.assertEqual({"test": "second"}, entries)
        self.assertEqual(["test"], duplicates)

    def test_deprecated_jobs_follow_active_tag_without_hardcoded_version(self):
        sample = '{ JOB_OLD, { "Ol", "Old Job" } },\n'
        with mock.patch.object(MODULE, "active_source", return_value=sample):
            with mock.patch.object(
                MODULE, "tag_major_version", return_value=99
            ):
                rows = MODULE.deprecated_job_rows(Path("unused"))
        self.assertEqual(99, rows[0]["TAG_MAJOR_VERSION"])

        with mock.patch.object(MODULE, "active_source", return_value=""):
            self.assertEqual([], MODULE.deprecated_job_rows(Path("unused")))

    def test_inventory_violations_reject_each_minimal_mutation(self):
        rows = valid_rows()
        expected = {row["identity"] for row in rows}
        clean = MODULE.inventory_violations(
            rows,
            expected,
            {},
            {
                "english_species": {"test species"},
                "chinese_species": {"test species"},
                "english_backgrounds": {"test background"},
                "chinese_backgrounds": {"test background"},
            },
        )
        self.assertTrue(all(not value for value in clean.values()))

        duplicate = rows + [dict(rows[0])]
        self.assertEqual(
            ["species:SP_TEST"],
            MODULE.inventory_violations(duplicate, expected)["duplicates"],
        )

        self.assertEqual(
            ["background:JOB_MISSING"],
            MODULE.inventory_violations(
                rows, expected | {"background:JOB_MISSING"}
            )["missing_identities"],
        )

        self.assertEqual(
            ["background:JOB_TEST"],
            MODULE.inventory_violations(
                rows, {"species:SP_TEST"}
            )["unexpected_identities"],
        )

        missing_name = [dict(row) for row in rows]
        missing_name[0]["current_chinese_name"] = None
        self.assertEqual(
            ["species:SP_TEST"],
            MODULE.inventory_violations(
                missing_name, expected
            )["missing_chinese_names"],
        )

        missing_form = [dict(row) for row in rows]
        missing_form[0]["forms"] = {
            "plain": {"translation_present": False}
        }
        self.assertEqual(
            ["species:SP_TEST:plain"],
            MODULE.inventory_violations(
                missing_form, expected
            )["missing_chinese_forms"],
        )

        missing_description = [dict(row) for row in rows]
        missing_description[0]["chinese_description"] = None
        self.assertEqual(
            ["species:SP_TEST"],
            MODULE.inventory_violations(
                missing_description, expected
            )["missing_chinese_descriptions"],
        )

        stale = MODULE.inventory_violations(
            rows,
            expected,
            {"chinese_species": ["test species"]},
            {"chinese_species": {"test species", "stale"}},
        )
        self.assertEqual(
            {"chinese_species": ["test species"]},
            stale["duplicate_description_keys"],
        )
        self.assertEqual(
            {"chinese_species": ["stale"]},
            stale["unexpected_description_keys"],
        )

        cross_category = MODULE.inventory_violations(
            rows,
            expected,
            {},
            {
                "chinese_species": {"test species", "test background"},
                "chinese_backgrounds": {"test background"},
            },
        )
        self.assertEqual(
            {"chinese_species": ["test background"]},
            cross_category["unexpected_description_keys"],
        )

    def test_production_rows_equal_active_enum_inventory(self):
        payload = MODULE.build_inventory()
        identities = [row["identity"] for row in payload["rows"]]
        self.assertEqual(len(identities), len(set(identities)))
        self.assertEqual(MODULE.expected_identities(), set(identities))
        self.assertEqual(
            payload["count"],
            sum(payload["category_counts"].values()),
        )

    def test_review_coverage_requires_one_terminal_row_per_identity(self):
        payload = {
            "glossary_sha256": "a" * 64,
            "inventory_sha256": "b" * 64,
            "count": 2,
            "rows": [
                {"identity": "species:SP_TEST"},
                {"identity": "background:JOB_TEST"},
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"
            path.write_text(
                MODULE.render_review_results(
                    payload,
                    {
                        "species:SP_TEST": "keep",
                        "background:JOB_TEST": "adjust",
                    },
                ),
                encoding="utf-8",
            )
            coverage = MODULE.review_coverage(payload, review_input(path))
            self.assertTrue(coverage["coverage_equal"])

            lines = path.read_text(encoding="utf-8").splitlines()
            marker = lines.index(MODULE.STRICT_REVIEW_BEGIN)
            first = marker + 3
            second = marker + 4
            path.write_text("\n".join([
                *lines[:first], lines[second], lines[second],
                *lines[second + 1:]
            ]) + "\n", encoding="utf-8")
            coverage = MODULE.review_coverage(payload, review_input(path))
        self.assertFalse(coverage["coverage_equal"])
        self.assertEqual(
            ["species:SP_TEST"], coverage["duplicate_evidence_cards"]
        )
        self.assertEqual(
            ["background:JOB_TEST"], coverage["missing_evidence_cards"]
        )

    def test_strict_review_rejects_stale_bindings_fact_pending_and_extra(self):
        payload = {
            "glossary_sha256": "a" * 64,
            "inventory_sha256": "b" * 64,
            "count": 2,
            "rows": [
                {"identity": "background:JOB_TEST", "fact": "background"},
                {"identity": "species:SP_TEST", "fact": "species"},
            ],
        }
        clean = MODULE.render_review_results(
            payload,
            {
                "background:JOB_TEST": "keep",
                "species:SP_TEST": "adjust",
            },
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "results.md"
            path.write_text(clean, encoding="utf-8")
            self.assertTrue(MODULE.review_coverage(payload, review_input(path))[
                "coverage_equal"
            ])
            lines = clean.splitlines()
            marker = lines.index(MODULE.STRICT_REVIEW_BEGIN)
            metadata_index = marker + 1
            first_index = marker + 3
            second_index = marker + 4
            mutations = {}
            for field, value in (
                ("baseline", "0" * 40),
                ("glossary_sha256", "0" * 64),
                ("inventory_sha256", "1" * 64),
                ("identity_count", 3),
            ):
                changed = list(lines)
                metadata = json.loads(changed[metadata_index])
                metadata[field] = value
                changed[metadata_index] = json.dumps(
                    metadata, sort_keys=True, separators=(",", ":")
                )
                mutations[field] = changed
            first = json.loads(lines[first_index])
            mutations.update({
                "fact": [
                    *lines[:first_index],
                    json.dumps(
                        dict(first, fact_sha256="0" * 64),
                        sort_keys=True, separators=(",", ":"),
                    ),
                    *lines[first_index + 1:],
                ],
                "pending": [
                    *lines[:first_index],
                    json.dumps(
                        dict(first, terminal_conclusion="pending"),
                        sort_keys=True, separators=(",", ":"),
                    ),
                    *lines[first_index + 1:],
                ],
                "missing": [
                    *lines[:first_index],
                    *lines[first_index + 1:],
                ],
                "extra": [
                    *lines[:second_index + 1],
                    json.dumps(
                        dict(first, identity="species:SP_EXTRA"),
                        sort_keys=True, separators=(",", ":"),
                    ),
                    *lines[second_index + 1:],
                ],
                "reordered": [
                    *lines[:first_index],
                    lines[second_index],
                    lines[first_index],
                    *lines[second_index + 1:],
                ],
                "external-prose": [*lines, "unbound final assertion"],
                "missing-artifact-marker": [
                    line for line in lines
                    if line != MODULE.REVIEW_ARTIFACT_BEGIN
                ],
                "duplicate-artifact-marker": [
                    *lines[:lines.index(MODULE.REVIEW_ARTIFACT_BEGIN)],
                    MODULE.REVIEW_ARTIFACT_BEGIN,
                    MODULE.REVIEW_ARTIFACT_BEGIN,
                    *lines[lines.index(MODULE.REVIEW_ARTIFACT_BEGIN) + 1:],
                ],
            })
            summary_index = lines.index(MODULE.REVIEW_ARTIFACT_BEGIN) + 1
            summary = json.loads(lines[summary_index])
            for field in summary:
                changed = list(lines)
                mutated = dict(summary)
                mutated[field] = "mutated"
                changed[summary_index] = json.dumps(
                    mutated,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                mutations[f"summary-{field}"] = changed
            for name, changed in mutations.items():
                with self.subTest(mutation=name):
                    path.write_text(
                        "\n".join(changed) + "\n", encoding="utf-8"
                    )
                    self.assertFalse(MODULE.review_coverage(
                        payload, review_input(path)
                    )[
                        "coverage_equal"
                    ])

    def test_cli_writes_inventory_even_when_findings_exist(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "inventory.json"
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "--output", str(output)],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            self.assertIn(proc.returncode, (0, 1))
            self.assertTrue(output.is_file())
            self.assertIn(
                '"inventory_sha256"', output.read_text(encoding="utf-8")
            )


if __name__ == "__main__":
    unittest.main()
