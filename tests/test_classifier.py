"""Comprehensive test suite for the upgraded classifier module."""
import os
from pathlib import Path
import tempfile
import unittest

from config.taxonomy import TAXONOMY, DEPARTMENTS, get_department, get_all_issue_types, validate_taxonomy
from services.classifier import (
    classify_feedback,
    classify_batch,
    is_mandatory_escalation,
    get_policy,
    get_highlight_terms,
    normalize_text,
    CRITICAL
)
from services.model_training import train_classifier, load_trained_model

class ClassifierTests(unittest.TestCase):
    def setUp(self):
        validate_taxonomy()

    def test_taxonomy_completeness_and_department_ownership(self):
        """Verify ~30 issue types exist and every type maps to one of the 5 allowed departments."""
        all_types = get_all_issue_types()
        self.assertGreaterEqual(len(all_types), 25)
        self.assertLessEqual(len(all_types), 35)

        for it in all_types:
            dept = get_department(it)
            self.assertIn(dept, DEPARTMENTS)
            self.assertIn("default_severity", TAXONOMY[it])
            self.assertIn("policy", TAXONOMY[it])

    def test_ordinary_text_classification(self):
        """Test standard customer statements."""
        res = classify_feedback("Freezer is warm and not cooling at all")
        self.assertEqual(res["issue_type"], "freezer_failure")
        self.assertIn("severity", res)
        self.assertIn("confidence", res)
        self.assertEqual(res["owner_department"], "Store Operations")

    def test_spelling_mistakes_and_noisy_text(self):
        """Verify character n-grams successfully classify typos and misspelling."""
        res = classify_feedback("frezer is wrm and iccream is mlting")
        self.assertEqual(res["issue_type"], "freezer_failure")

        res_bill = classify_feedback("doubl charg on crdit card statemnt, chargd twice")
        self.assertEqual(res_bill["issue_type"], "billing")

    def test_emoji_handling(self):
        """Verify inputs with emojis are correctly handled."""
        res_emoji = classify_feedback("💳❌ payment failed at terminal")
        self.assertEqual(res_emoji["issue_type"], "payment_failure")
        self.assertEqual(res_emoji["owner_department"], "Digital")

    def test_hinglish_and_transliteration(self):
        """Verify Hinglish and transliterated customer text."""
        res_hinglish = classify_feedback("Shelf bilkul empty hai, rice out of stock hai")
        self.assertEqual(res_hinglish["issue_type"], "stockout")
        self.assertEqual(res_hinglish["owner_department"], "Supply Chain")

    def test_safety_override_takes_precedence(self):
        """Verify safety keywords immediately override any lower prediction."""
        res = classify_feedback("Great polite customer service but found cockroach crawling on food counter")
        self.assertEqual(res["issue_type"], "hygiene")
        self.assertEqual(res["severity"], "High")
        self.assertEqual(res["method"], "safety_override")
        self.assertTrue(res["actionable"])

        res_allergy = classify_feedback("Missing peanut allergen label on cookie box")
        self.assertEqual(res_allergy["issue_type"], "allergen_label")
        self.assertIn(res_allergy["severity"], {"High", "Critical"})
        self.assertEqual(res_allergy["method"], "safety_override")

    def test_unknown_or_empty_text(self):
        """Verify empty and unknown general statements."""
        empty_res = classify_feedback("")
        self.assertEqual(empty_res["issue_type"], "other")
        self.assertEqual(empty_res["confidence"], 0.0)

        general_res = classify_feedback("The weather is nice today, I like the parking space")
        self.assertEqual(general_res["issue_type"], "other")
        self.assertFalse(general_res["actionable"])

    def test_model_persistence_and_reproducibility(self):
        """Verify model training, serialization, and deserialization without leaking."""
        with tempfile.TemporaryDirectory() as tmpdir:
            model_path = Path(tmpdir) / "test_model.joblib"
            train_classifier(model_path)
            self.assertTrue(model_path.exists())

            bundle = load_trained_model(model_path)
            self.assertIsNotNone(bundle)
            self.assertIn("pipeline", bundle)
            self.assertIn("metrics", bundle)
            self.assertGreater(bundle["metrics"]["test_accuracy"], 0.70)
            self.assertIn("calibration_notice", bundle)

    def test_batch_classification(self):
        """Verify batch classification matches individual calls."""
        texts = [
            "Freezer is warm and ice cream is melting",
            "Emergency fire exit is blocked by cartons",
            "Card payment failed repeatedly at checkout",
            "Great sunny day in the city"
        ]
        batch_res = classify_batch(texts)
        self.assertEqual(len(batch_res), 4)
        self.assertEqual(batch_res[0]["issue_type"], "freezer_failure")
        self.assertEqual(batch_res[1]["issue_type"], "health_safety_violation")
        self.assertEqual(batch_res[2]["issue_type"], "payment_failure")

    def test_backward_compatibility_interfaces(self):
        """Verify all original helper functions and constants exist."""
        self.assertTrue(is_mandatory_escalation("allergen_label", "peanut warning missing"))
        self.assertFalse(is_mandatory_escalation("pricing", "tag says 10 dollars"))
        
        policy = get_policy("food_safety")
        self.assertIn("HACCP", policy["policy"])
        
        terms = get_highlight_terms("allergen_label")
        self.assertTrue(len(terms) > 0)
        self.assertIn("allergen_label", CRITICAL)

if __name__ == "__main__":
    unittest.main()
