#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["duckdb==2.0.0", "pyyaml==6.0.3"]
# ///
"""Hermetic regression tests: uv run scripts/test_rf_manifest.py."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import duckdb
import rf_manifest as rf
import yaml


class GeneratedMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "metadata.source.yml"
        self.source.write_bytes(rf.SOURCE.read_bytes())
        paths = {
            "SOURCE": self.source,
            "MANIFEST": self.root / "MANIFEST.tsv",
            "METADATA": self.root / "MANIFEST.meta.yml",
            "RF_DB": self.root / "rf.duckdb",
            "LOSS_DB": self.root / "loss.duckdb",
        }
        patcher = patch.multiple(rf, **paths)
        patcher.start()
        self.addCleanup(patcher.stop)
        with duckdb.connect(str(rf.RF_DB)) as con:
            con.execute(
                "CREATE TABLE filings (accession_number VARCHAR, d_filing DATE)"
            )
            con.execute(
                "INSERT INTO filings VALUES ('a','2020-01-01'),('b','2020-02-01'),('c','2020-03-01')"
            )
            con.execute(
                "CREATE TABLE item_1a (accession_number VARCHAR, text_blake3 VARCHAR, cik VARCHAR, word_count INTEGER, method VARCHAR)"
            )
            con.executemany(
                "INSERT INTO item_1a VALUES (?,?,?,?,?)",
                [
                    ("a", "a" * 64, "001", 20, "heading"),
                    ("b", "b" * 64, "002", 0, "not-applicable"),
                ],
            )
        with duckdb.connect(str(rf.LOSS_DB)) as con:
            con.execute(
                "CREATE TABLE loss_event (accession_number VARCHAR, items VARCHAR, cik VARCHAR, filing_date DATE)"
            )
            con.execute(
                "INSERT INTO loss_event VALUES ('loss','2.06','001','2021-01-01')"
            )

    def write(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(rf.cmd_write(None), 0)

    def check(self):
        with (
            contextlib.redirect_stdout(io.StringIO()),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            return rf.cmd_check(None)

    def test_identical_rebuild_and_derived_denominators(self):
        self.write()
        first = (rf.MANIFEST.read_bytes(), rf.METADATA.read_bytes())
        self.write()
        self.assertEqual(first, (rf.MANIFEST.read_bytes(), rf.METADATA.read_bytes()))
        self.assertEqual(self.check(), 0)
        c = yaml.safe_load(rf.METADATA.read_text())["coverage"]
        self.assertEqual(
            (c["filings_attempted"], c["substantive_spans"], c["not_applicable"]),
            (3, 1, 1),
        )
        self.assertEqual(c["stored_percent"], 66.7)
        self.assertEqual(c["substantive_percent"], 33.3)
        self.assertIn("unknown", c["loss_discovery_completeness"])
        self.assertIn("\tsha256\trevision\t", rf.MANIFEST.read_text())

    def test_broken_metadata_cannot_pass(self):
        self.write()
        rf.METADATA.write_text("broken YAML: [\n<ORGANIZATION>\n")
        self.assertEqual(self.check(), 1)

    def test_missing_output_cannot_pass(self):
        self.write()
        rf.METADATA.unlink()
        self.assertEqual(self.check(), 1)

    def test_missing_duplicate_upstream_and_changed_notes_cannot_pass(self):
        self.write()
        original = rf.MANIFEST.read_text()
        lines = original.splitlines(keepends=True)
        for mutant in (
            "".join(lines[:-1]),
            original + lines[-1],
            original.replace("3 filings", "999 filings"),
            original.replace("31ee0261", "41ee0261"),
        ):
            with self.subTest(mutant=mutant[:30]):
                rf.MANIFEST.write_text(mutant)
                self.assertEqual(self.check(), 1)

    def test_changed_statistics_fail_even_with_same_text_hash(self):
        self.write()
        with duckdb.connect(str(rf.RF_DB)) as con:
            con.execute("UPDATE item_1a SET word_count=99 WHERE accession_number='a'")
        self.assertEqual(self.check(), 1)

    def test_authored_input_changes_are_detected(self):
        self.write()
        self.source.write_text(self.source.read_text() + "\n# Authored revision\n")
        self.assertEqual(self.check(), 1)

    def test_invalid_hash_does_not_overwrite_outputs(self):
        self.write()
        before = (rf.MANIFEST.read_bytes(), rf.METADATA.read_bytes())
        with duckdb.connect(str(rf.RF_DB)) as con:
            con.execute(
                "UPDATE item_1a SET text_blake3=NULL WHERE accession_number='a'"
            )
        with self.assertRaisesRegex(ValueError, "BLAKE3"):
            rf.cmd_write(None)
        self.assertEqual(before, (rf.MANIFEST.read_bytes(), rf.METADATA.read_bytes()))

    def test_insertion_order_does_not_change_output(self):
        self.write()
        before = (rf.MANIFEST.read_bytes(), rf.METADATA.read_bytes())
        with duckdb.connect(str(rf.RF_DB)) as con:
            rows = con.execute(
                "SELECT * FROM item_1a ORDER BY accession_number DESC"
            ).fetchall()
            con.execute("DELETE FROM item_1a")
            con.executemany("INSERT INTO item_1a VALUES (?,?,?,?,?)", rows)
        self.write()
        self.assertEqual(before, (rf.MANIFEST.read_bytes(), rf.METADATA.read_bytes()))

    def test_empty_store_has_no_invented_rate(self):
        with duckdb.connect(str(rf.RF_DB)) as con:
            con.execute("DELETE FROM item_1a")
            con.execute("DELETE FROM filings")
        self.write()
        self.assertIsNone(
            yaml.safe_load(rf.METADATA.read_text())["coverage"]["stored_percent"]
        )


if __name__ == "__main__":
    unittest.main()
