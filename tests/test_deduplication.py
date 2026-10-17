"""Unit tests for cross-channel de-duplication and corroboration."""
from datetime import datetime, timedelta, timezone
import unittest

from services.deduplication import (
    text_similarity,
    find_cross_channel_duplicates,
    cluster_cross_channel_incidents
)

class DeduplicationTests(unittest.TestCase):
    def test_text_similarity_metrics(self):
        """Verify identical, near-duplicate, and unrelated matching scores."""
        self.assertEqual(text_similarity("Freezer is warm", "Freezer is warm"), 1.0)
        self.assertGreater(text_similarity("Freezer is warm and ice cream melting", "Freezer is warm and ice cream is melting"), 0.85)
        self.assertLess(text_similarity("Freezer is warm", "Staff member was very polite"), 0.20)

    def test_cross_channel_duplicate_detection(self):
        """Verify duplicate reports across call_centre and online_review are identified."""
        now = datetime.now(timezone.utc)
        records = [
            {
                "id": "FB-101",
                "store_id": "ST-104",
                "timestamp": now.isoformat(),
                "channel": "call_centre",
                "original_text": "Freezer alarm sounding and dairy products are thawing"
            },
            {
                "id": "FB-102",
                "store_id": "ST-104",
                "timestamp": (now + timedelta(hours=3)).isoformat(),
                "channel": "online_review",
                "original_text": "Freezer alarm sounding and dairy products are thawing"
            }
        ]
        dups = find_cross_channel_duplicates(records, similarity_threshold=0.80, window_hours=48)
        self.assertEqual(len(dups), 1)
        self.assertEqual(dups[0]["canonical_id"], "FB-101")
        self.assertEqual(dups[0]["duplicate_id"], "FB-102")
        self.assertEqual(dups[0]["channel_1"], "call_centre")
        self.assertEqual(dups[0]["channel_2"], "online_review")

    def test_time_window_cutoff(self):
        """Verify duplicates outside the 48-hour window are not grouped together."""
        now = datetime.now(timezone.utc)
        records = [
            {"id": "A1", "store_id": "ST-104", "timestamp": now.isoformat(), "channel": "call_centre", "original_text": "Freezer broken"},
            {"id": "A2", "store_id": "ST-104", "timestamp": (now + timedelta(hours=60)).isoformat(), "channel": "online_review", "original_text": "Freezer broken"}
        ]
        dups = find_cross_channel_duplicates(records, window_hours=48)
        self.assertEqual(len(dups), 0)

    def test_store_separation(self):
        """Verify identical complaints at different stores are NOT marked as duplicates."""
        now = datetime.now(timezone.utc)
        records = [
            {"id": "S1", "store_id": "ST-104", "timestamp": now.isoformat(), "channel": "call_centre", "original_text": "Freezer broken"},
            {"id": "S2", "store_id": "ST-208", "timestamp": (now + timedelta(hours=1)).isoformat(), "channel": "online_review", "original_text": "Freezer broken"}
        ]
        dups = find_cross_channel_duplicates(records)
        self.assertEqual(len(dups), 0)

    def test_cluster_cross_channel_incidents(self):
        """Verify incident corroboration flags across channels."""
        feedback = [
            {"id": "F1", "channel": "call_centre"},
            {"id": "F2", "channel": "online_review"},
        ]
        incidents = [
            {"id": "FS-0104", "feedback_ids": ["F1", "F2"]}
        ]
        enriched = cluster_cross_channel_incidents(incidents, feedback)
        self.assertEqual(len(enriched), 1)
        self.assertTrue(enriched[0]["is_cross_channel_corroborated"])
        self.assertEqual(enriched[0]["channel_count"], 2)
        self.assertIn("Corroborated across 2 distinct channels", enriched[0]["channel_diversity_note"])

if __name__ == "__main__":
    unittest.main()
