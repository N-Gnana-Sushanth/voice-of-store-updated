"""Unit tests for the statistical emerging-issue detector."""
from datetime import datetime, timedelta, timezone
import unittest

from services.emerging_detector import (
    calculate_rate_per_thousand,
    is_statistical_anomaly,
    detect_emerging_issues
)
from services.first_signal import detect_signals

class EmergingDetectorTests(unittest.TestCase):
    def test_rate_per_thousand_calculation(self):
        """Verify rate per 1,000 calculation."""
        self.assertEqual(calculate_rate_per_thousand(5, 100), 50.0)
        self.assertEqual(calculate_rate_per_thousand(2, 2000), 1.0)
        self.assertEqual(calculate_rate_per_thousand(0, 500), 0.0)

    def test_small_store_noise_suppression_floor(self):
        """Verify count floor suppresses alerts when count < min_count_floor."""
        # 2 reports with 0 baseline: below count floor of 3
        is_spike, p_val, z_sc, reason = is_statistical_anomaly(
            current_count=2,
            total_current_store_records=20,
            baseline_count=0,
            total_baseline_store_records=100,
            min_count_floor=3
        )
        self.assertFalse(is_spike)
        self.assertIn("Below minimum count floor", reason)

    def test_emerging_spike_detected(self):
        """Verify statistically significant spike is flagged."""
        # 6 reports when expected mean is ~0.5 per week
        is_spike, p_val, z_sc, reason = is_statistical_anomaly(
            current_count=6,
            total_current_store_records=100,
            baseline_count=2,
            total_baseline_store_records=400,
            baseline_weeks=4,
            min_count_floor=3,
            alpha=0.05
        )
        self.assertTrue(is_spike)
        self.assertLess(p_val, 0.05)
        self.assertGreater(z_sc, 2.0)
        self.assertIn("Statistically significant spike", reason)

    def test_normal_baseline_not_flagged(self):
        """Verify counts matching historical baseline are not flagged."""
        # 3 reports when baseline is 12 over 4 weeks (mean = 3.0)
        is_spike, p_val, z_sc, reason = is_statistical_anomaly(
            current_count=3,
            total_current_store_records=100,
            baseline_count=12,
            total_baseline_store_records=400,
            baseline_weeks=4,
            min_count_floor=3,
            alpha=0.05
        )
        self.assertFalse(is_spike)

    def test_mandatory_safety_bypass_single_occurrence(self):
        """Verify mandatory safety categories bypass count floor on single report."""
        now = datetime.now(timezone.utc)
        records = [
            {
                "id": "SAFE-1",
                "store_id": "ST-999",
                "timestamp": now.isoformat(),
                "original_text": "Missing peanut allergen label on bakery cookie box",
                "issue_type": "allergen_label",
                "channel": "customer_review"
            }
        ]
        alerts = detect_emerging_issues(records, min_count_floor=3)
        self.assertEqual(len(alerts), 1)
        self.assertTrue(alerts[0]["is_emerging"])
        self.assertEqual(alerts[0]["detection_type"], "safety_bypass")
        self.assertEqual(alerts[0]["current_count"], 1)

    def test_first_signal_integration(self):
        """Verify first_signal engine incorporates statistical anomaly metrics."""
        now = datetime.now(timezone.utc)
        records = [
            {"id": f"R-{i}", "store_id": "ST-777", "timestamp": (now - timedelta(hours=i)).isoformat(),
             "original_text": "Freezer is warm again and melting", "issue_type": "freezer_failure"}
            for i in range(5)
        ]
        signals = detect_signals(records, min_count_floor=3)
        self.assertTrue(len(signals) > 0)
        sig = signals[0]
        self.assertEqual(sig["store_id"], "ST-777")
        self.assertIn("rate_per_thousand", sig)
        self.assertIn("statistical_anomaly", sig)

if __name__ == "__main__":
    unittest.main()
