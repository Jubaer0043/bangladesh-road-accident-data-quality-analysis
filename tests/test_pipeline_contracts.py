"""Synthetic software fixtures are never used for analytical results."""

from datetime import datetime
from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import numpy as np
import pandas as pd

from bd_safety import acquisition
from bd_safety.cleaning import ambiguous_date, coordinates, parse_date, parse_hour, text
from bd_safety.config import MEMBER, ROOT
from bd_safety.model import participants
from bd_safety.statistics import (
    conditional_cluster_interval,
    contingency_effect,
    descriptor_bounds,
)


class ParsingContracts(unittest.TestCase):
    def test_excel_date_respected_and_slash_ambiguity_flagged(self):
        self.assertEqual(parse_date(datetime(2022, 6, 5)), pd.Timestamp("2022-06-05"))
        self.assertEqual(parse_date("14/2/2024"), pd.Timestamp("2024-02-14"))
        self.assertTrue(ambiguous_date("5/6/2022"))
        self.assertFalse(ambiguous_date(datetime(2022, 6, 5)))

    def test_invalid_date_is_missing_without_invented_correction(self):
        self.assertTrue(pd.isna(parse_date("IMG 2467")))
        self.assertTrue(pd.isna(parse_date("31/2/2024")))

    def test_time_formats_and_midnight(self):
        self.assertEqual(parse_hour("9.45 PM"), 21)
        self.assertEqual(parse_hour("12.01 am"), 0)
        self.assertEqual(parse_hour("23:00:00"), 23)
        self.assertTrue(np.isnan(parse_hour("24:01:00")))

    def test_coordinate_hemispheres_define_order(self):
        self.assertEqual(coordinates("23.8° N, 90.4° E"), (23.8, 90.4))
        self.assertTrue(np.isnan(coordinates("90.4, 23.8")[0]))

    def test_unknown_tokens_not_other_categories(self):
        self.assertTrue(pd.isna(text(" Unknown ")))
        self.assertEqual(text("Others"), "Others")
        self.assertEqual(text(" Two-Lane  "), "Two-Lane")

    def test_participants_overlap_without_duplicates(self):
        self.assertEqual(
            participants("Truck - Motorcycle collision"), ["Truck", "Motorcycle"]
        )
        self.assertEqual(participants("Bus hits bus"), ["Bus"])
        self.assertEqual(participants("Unspecified"), ["Unclassified"])


class StatisticalContracts(unittest.TestCase):
    def test_descriptive_cramers_v_known_independence_and_separation(self):
        independent = pd.DataFrame(
            {"x": ["a", "a", "b", "b"], "fatal_record": [0, 1, 0, 1]}
        )
        separated = pd.DataFrame(
            {"x": ["a", "a", "b", "b"], "fatal_record": [0, 0, 1, 1]}
        )
        self.assertAlmostEqual(contingency_effect(independent, "x")["cramers_v"], 0)
        result = contingency_effect(separated, "x")
        self.assertAlmostEqual(result["cramers_v"], 1)
        self.assertFalse(result["p_value_reported"])

    def test_cluster_bootstrap_retains_within_group_rows(self):
        frame = pd.DataFrame(
            {
                "descriptor_group": ["a", "a", "b", "b"],
                "lighting": ["Day", "Night", "Day", "Night"],
                "fatal_record": [0, 1, 0, 1],
            }
        )
        result = conditional_cluster_interval(frame, repetitions=100, seed=7)
        self.assertEqual((result["lower"], result["upper"]), (1, 1))
        self.assertEqual(
            result, conditional_cluster_interval(frame, repetitions=100, seed=7)
        )

    def test_descriptor_bounds_preserve_uncertain_identity(self):
        frame = pd.DataFrame(
            {"descriptor_group": ["a", "a", "b"], "fatal_record": [0, 1, 1]}
        )
        result = descriptor_bounds(frame)
        self.assertEqual(
            (result["fatal_share_lower"], result["fatal_share_upper"]), (0.5, 1)
        )


class ModelContracts(unittest.TestCase):
    def test_keys_and_participant_foreign_keys(self):
        with closing(sqlite3.connect(":memory:")) as con:
            con.executescript((ROOT / "sql/01_schema.sql").read_text())
            con.execute(
                "INSERT INTO records(source_row,descriptor_group) VALUES (2,'test')"
            )
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute(
                    "INSERT INTO records(source_row,descriptor_group) VALUES (2,'test')"
                )
            with self.assertRaises(sqlite3.IntegrityError):
                con.execute("INSERT INTO participants VALUES (999,'Truck')")


class OriginalProtection(unittest.TestCase):
    def test_checksum_changes_rejected_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            archive = base / "source.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr(MEMBER, b"test fixture; not real dataset")
            expected = hashlib.sha256(archive.read_bytes()).hexdigest()
            with patch.multiple(
                acquisition,
                RAW=base / "raw",
                EXTERNAL=base / "external",
                REPORTS=base / "reports",
                WORKBOOK=base / "raw/source.xlsx",
                PUBLISHED_SHA256=expected,
            ):
                first = acquisition.acquire(archive)
                self.assertEqual(first, acquisition.acquire(archive))
                acquisition.WORKBOOK.write_bytes(b"changed")
                with self.assertRaises(ValueError):
                    acquisition.verify_raw()
                with self.assertRaises(ValueError):
                    acquisition.acquire(archive)
                self.assertEqual(acquisition.WORKBOOK.read_bytes(), b"changed")

    def test_wrong_source_archive_rejected_before_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            archive = base / "wrong.zip"
            archive.write_bytes(b"wrong source")
            with patch.multiple(
                acquisition,
                RAW=base / "raw",
                EXTERNAL=base / "external",
                REPORTS=base / "reports",
            ):
                with self.assertRaises(ValueError):
                    acquisition.acquire(archive)
                self.assertFalse(any((base / "raw").iterdir()))


if __name__ == "__main__":
    unittest.main()
