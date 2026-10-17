"""Test suite for duplicate prevention and translation integrity."""
import unittest
import os
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Use isolated temp database for test
temp_db = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
temp_db_path = temp_db.name
temp_db.close()
os.environ["R5_DB_PATH"] = temp_db_path

import app
from app import create_feedback, get_feedback, sync_first_signal, db_session, enrich_incident_details, rowdict


class DuplicatePreventionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.init_db()

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(temp_db_path)
        except OSError:
            pass

    def test_01_rapid_identical_submission_idempotency(self):
        """Identical feedback submitted in rapid succession (e.g. double click) must not create duplicate records."""
        now = datetime.now(timezone.utc).isoformat()
        rec = {
            "store_id": "STORE-004",
            "text": "Paal stock illa",
            "channel": "staff_note",
            "timestamp": now,
        }
        fid1, err1 = create_feedback(rec)
        self.assertIsNotNone(fid1)
        self.assertIsNone(err1)

        # Immediate re-submission of identical feedback
        fid2, err2 = create_feedback(rec)
        self.assertEqual(fid1, fid2, "Rapid duplicate submission must return the existing record ID")
        self.assertIn("Duplicate", str(err2))

        # Verify only 1 record exists in database
        with db_session() as c:
            count = c.execute("SELECT COUNT(*) FROM feedback WHERE store_id = ? AND original_text = ?", ("STORE-004", "Paal stock illa")).fetchone()[0]
            self.assertEqual(count, 1, "Database should contain exactly 1 feedback row for the rapid double submission")

    def test_02_distinct_reports_are_preserved(self):
        """Distinct reports with different content or different stores must both be preserved."""
        now = datetime.now(timezone.utc).isoformat()
        rec_a = {
            "store_id": "STORE-004",
            "text": "Paal stock illa",
            "channel": "staff_note",
            "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        }
        rec_b = {
            "store_id": "STORE-004",
            "text": "Curd is also out of stock on top shelf",
            "channel": "staff_note",
            "timestamp": now,
        }
        fid_a, _ = create_feedback(rec_a)
        fid_b, _ = create_feedback(rec_b)

        self.assertNotEqual(fid_a, fid_b)
        all_recs = get_feedback({"store_id": "STORE-004"})
        fids = [r["id"] for r in all_recs]
        self.assertIn(fid_a, fids)
        self.assertIn(fid_b, fids)

    def test_03_get_feedback_has_no_duplicate_rows(self):
        """get_feedback must return uniquely identified records even after evidence joins."""
        all_recs = get_feedback()
        seen = set()
        for r in all_recs:
            self.assertNotIn(r["id"], seen, f"Duplicate feedback ID {r['id']} returned by get_feedback")
            seen.add(r["id"])

    def test_04_incident_clustering_deduplication(self):
        """sync_first_signal must maintain only ONE incident for the same store and category cluster."""
        # Insert 3 related feedback items for STORE-999
        ts = datetime.now(timezone.utc)
        for i in range(3):
            create_feedback({
                "store_id": "STORE-999",
                "text": f"Freezer temperature alarm sounding in dairy aisle report {i}",
                "timestamp": (ts + timedelta(minutes=i * 5)).isoformat(),
                "channel": "staff_note"
            })

        sync_first_signal()

        with db_session() as c:
            incs = c.execute("SELECT id, store_id, issue_type, report_count FROM incidents WHERE store_id = 'STORE-999'").fetchall()
            self.assertEqual(len(incs), 1, "Only one incident row should exist for STORE-999 freezer_failure cluster")
            inc_id = incs[0][0]
            rep_count = incs[0][3]
            self.assertGreaterEqual(rep_count, 3, "Report count should reflect all linked feedback")

        # Running sync_first_signal again should NOT create another incident
        sync_first_signal()
        with db_session() as c:
            incs_after = c.execute("SELECT id FROM incidents WHERE store_id = 'STORE-999'").fetchall()
            self.assertEqual(len(incs_after), 1, "sync_first_signal must remain idempotent and not duplicate incidents")

    def test_05_translation_fields_preserved(self):
        """create_feedback must populate description_en, source_language, and is_translated while preserving original_text."""
        now = datetime.now(timezone.utc).isoformat()
        rec = {
            "store_id": "STORE-005",
            "text": "दूध खराब हो गया है",
            "channel": "staff_note",
            "timestamp": now,
        }
        fid, err = create_feedback(rec)
        self.assertIsNotNone(fid)

        with db_session() as c:
            row = rowdict(c.execute("SELECT * FROM feedback WHERE id = ?", (fid,)).fetchone())
            self.assertEqual(row["original_text"], "दूध खराब हो गया है", "Original regional text must never be modified")
            self.assertIn("Milk", row["description_en"])
            self.assertEqual(row["source_language"], "hi")
            self.assertEqual(row["is_translated"], 1)

    def test_06_english_reports_not_overwritten(self):
        """Pure English reports must be stored with description_en equal to original text and is_translated=0."""
        text = "fix this ASAP AC not working"
        rec = {
            "store_id": "STORE-006",
            "text": text,
            "channel": "staff_note",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        fid, _ = create_feedback(rec)

        with db_session() as c:
            row = rowdict(c.execute("SELECT * FROM feedback WHERE id = ?", (fid,)).fetchone())
            self.assertEqual(row["original_text"], text)
            self.assertEqual(row["description_en"], text)
            self.assertEqual(row["is_translated"], 0)
            self.assertEqual(row["source_language"], "en")


if __name__ == "__main__":
    unittest.main()
