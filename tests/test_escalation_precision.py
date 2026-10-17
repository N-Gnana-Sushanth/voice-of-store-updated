"""Unit tests for the escalation precision metric and edge cases."""
import unittest
from evaluate import evaluate_dataset

class EscalationPrecisionTests(unittest.TestCase):
    def test_perfect_escalation_precision(self):
        """Test scenario where every flagged escalation matches ground truth."""
        records = [
            # High-risk allergen - system escalates, ground truth requires escalation (TP)
            {"id": "1", "text": "Peanut allergen label missing", "issue_type": "allergen_label",
             "severity": "Critical", "ground_truth_escalated": "1"},
            # Routine billing - system does not escalate, ground truth does not escalate (TN)
            {"id": "2", "text": "Wrong price on tag", "issue_type": "pricing",
             "severity": "Medium", "ground_truth_escalated": "0"},
        ]
        res = evaluate_dataset(records)
        esc = res["escalation_metrics"]
        self.assertIsInstance(esc, dict)
        self.assertEqual(esc["true_positives"], 1)
        self.assertEqual(esc["false_positives"], 0)
        self.assertEqual(esc["precision"], 1.0)
        self.assertIn("100% precision attained", esc["honest_assessment"])

    def test_all_false_positives(self):
        """Test scenario where system escalates but ground truth required none."""
        records = [
            # System escalates due to critical keyword, but ground truth says no escalation (FP)
            {"id": "1", "text": "Peanut allergen label missing", "issue_type": "allergen_label",
             "severity": "Critical", "ground_truth_escalated": "0"},
        ]
        res = evaluate_dataset(records)
        esc = res["escalation_metrics"]
        self.assertEqual(esc["true_positives"], 0)
        self.assertEqual(esc["false_positives"], 1)
        self.assertEqual(esc["precision"], 0.0)

    def test_zero_escalations_flagged(self):
        """Test zero division guard when no escalations are flagged."""
        records = [
            {"id": "1", "text": "Nice store and clean floors", "issue_type": "other",
             "severity": "Low", "ground_truth_escalated": "0"},
            {"id": "2", "text": "Looking for parking space", "issue_type": "other",
             "severity": "Low", "ground_truth_escalated": "0"},
        ]
        res = evaluate_dataset(records)
        esc = res["escalation_metrics"]
        self.assertEqual(esc["true_positives"], 0)
        self.assertEqual(esc["false_positives"], 0)
        self.assertEqual(esc["precision"], 0.0)

    def test_missing_ground_truth_escalation_reports_na(self):
        """Test unlabelled datasets honestly report N/A rather than fabricating a score."""
        records = [
            {"id": "1", "text": "Freezer warm", "issue_type": "freezer_failure", "severity": "High"},
            {"id": "2", "text": "Payment failed", "issue_type": "payment_failure", "severity": "High"},
        ]
        res = evaluate_dataset(records)
        self.assertEqual(res["escalation_metrics"], "N/A (ground truth escalation labels not provided in dataset)")

if __name__ == "__main__":
    unittest.main()
