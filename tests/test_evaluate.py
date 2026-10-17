"""Unit tests for root-level evaluate.py module."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from evaluate import evaluate_dataset, run_evaluation, load_data

class EvaluateTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmppath = Path(self.tmpdir.name)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_load_data_discovers_synthetic_tag(self):
        """Test dataset loader marks synthetic data honestly."""
        csv_path = self.tmppath / "test_synth.csv"
        csv_path.write_text(
            "id,text,issue_type,severity,data_source\n"
            "T1,Freezer warm,freezer_failure,High,synthetic_test\n",
            encoding="utf-8"
        )
        records, dtype = load_data(csv_path)
        self.assertEqual(len(records), 1)
        self.assertIn("SYNTHETIC", dtype)

    def test_missing_data_file_raises_error(self):
        """Test missing file raises FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            load_data(self.tmppath / "non_existent.csv")

    def test_evaluate_dataset_computation(self):
        """Test metric calculation on known miniature records."""
        records = [
            {
                "id": "R1",
                "text": "Freezer temperature alarm sounding and ice cream melting",
                "issue_type": "freezer_failure",
                "severity": "High",
                "actionable": "1",
                "ground_truth_escalated": "0",
                "store_id": "ST-101",
                "timestamp": "2026-10-15T10:00:00Z",
                "actual_incident_start": "2026-10-13T10:00:00Z",
                "is_planted": "1"
            },
            {
                "id": "R2",
                "text": "Severe peanut allergy warning label missing on cookie packaging",
                "issue_type": "allergen_label",
                "severity": "Critical",
                "actionable": "1",
                "ground_truth_escalated": "1",
                "store_id": "ST-208",
                "timestamp": "2026-10-15T12:00:00Z",
                "actual_incident_start": "2026-10-14T12:00:00Z",
                "is_planted": "1"
            },
            {
                "id": "R3",
                "text": "Nice bright lighting in store today, pleasant experience",
                "issue_type": "other",
                "severity": "Low",
                "actionable": "0",
                "ground_truth_escalated": "0",
                "store_id": "ST-101",
                "timestamp": "2026-10-15T14:00:00Z"
            }
        ]
        res = evaluate_dataset(records, seed=42)
        
        # Check classification metrics structure
        self.assertIn("metrics", res)
        self.assertIn("issue_type", res["metrics"])
        self.assertIn("severity", res["metrics"])
        self.assertIn("actionable", res["metrics"])
        self.assertGreaterEqual(res["metrics"]["issue_type"]["accuracy"], 0.66)
        
        # Check escalation precision
        self.assertIn("escalation_metrics", res)
        esc = res["escalation_metrics"]
        self.assertIn("precision", esc)
        self.assertIn("recall", esc)
        self.assertIn("true_positives", esc)
        
        # Check planted incidents lead time
        self.assertIn("planted_incidents", res)
        pi = res["planted_incidents"]
        self.assertEqual(pi["total_planted_incidents"], 2)
        self.assertIsNotNone(pi["mean_lead_time_days"])

    def test_run_evaluation_json_output_file(self):
        """Test run_evaluation writing to machine-readable JSON."""
        csv_path = self.tmppath / "test_eval.csv"
        csv_path.write_text(
            "id,text,issue_type,severity,actionable\n"
            "E1,Freezer warm,freezer_failure,High,1\n"
            "E2,Card declined at checkout,payment_failure,High,1\n",
            encoding="utf-8"
        )
        json_out = self.tmppath / "out.json"
        res = run_evaluation(data_path=str(csv_path), output_path=str(json_out), fmt="text")
        
        self.assertTrue(json_out.exists())
        loaded = json.loads(json_out.read_text(encoding="utf-8"))
        self.assertEqual(loaded["record_count"], 2)
        self.assertIn("metrics", loaded)

if __name__ == "__main__":
    unittest.main()
