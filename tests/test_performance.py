"""Performance scaling and benchmark tests for 1,000, 5,000, and 40,000 record batches."""
from datetime import datetime, timezone, timedelta
import os
from pathlib import Path
import tempfile
import time
import unittest

from app import app, init_db, import_feedback_batch
from services.classifier import classify_batch

class PerformanceScalingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        import app as appmod
        appmod.DB_PATH = Path(self.tmp.name)
        init_db()
        self.client = app.test_client()

    def tearDown(self):
        import gc
        gc.collect()
        try:
            os.unlink(self.tmp.name)
        except OSError:
            pass

    def _generate_synthetic_batch(self, count: int):
        base_time = datetime(2026, 10, 15, 8, 0, 0, tzinfo=timezone.utc)
        stores = ["ST-101", "ST-102", "ST-104", "ST-208", "ST-116", "ST-305", "ST-091"]
        phrases = [
            ("Freezer temperature alarm sounding and ice cream melting", "freezer_failure", "High"),
            ("Card payment failed repeatedly at POS register", "payment_failure", "High"),
            ("Possible peanut allergen label missing on cookie box", "allergen_label", "Critical"),
            ("Rice and cooking oil out of stock on shelves", "stockout", "Medium"),
            ("Cashier scanned item twice, duplicate charge on bill", "billing", "Medium"),
            ("Cockroach spotted near fresh produce section", "hygiene", "High"),
            ("Store was tidy and staff assisted with bags", "other", "Low"),
        ]
        batch = []
        for i in range(count):
            text, issue, sev = phrases[i % len(phrases)]
            store = stores[i % len(stores)]
            ts = (base_time + timedelta(seconds=i * 5)).isoformat()
            batch.append({
                "id": f"PERF-{count}-{i+1}",
                "store_id": store,
                "timestamp": ts,
                "channel": "app_feedback",
                "text": text,
                "issue_type": issue,
                "severity": sev,
                "actionable": 0 if issue == "other" else 1
            })
        return batch

    def test_batch_classifier_throughput(self):
        """Verify vectorizer + classifier throughput on 2,000 items."""
        texts = ["Freezer is warm and not cooling", "Emergency exit blocked", "Card declined"] * 700
        t0 = time.perf_counter()
        preds = classify_batch(texts)
        elapsed = time.perf_counter() - t0
        throughput = len(texts) / elapsed if elapsed > 0 else 0
        print(f"\n[BENCHMARK] Classifier: {len(texts)} texts in {elapsed:.3f}s ({throughput:.1f} texts/sec)")
        self.assertEqual(len(preds), len(texts))
        self.assertGreater(throughput, 1000.0) # > 1,000 texts/sec

    def test_1000_row_batch_ingestion(self):
        """Benchmark 1,000 records."""
        batch = self._generate_synthetic_batch(1000)
        t0 = time.perf_counter()
        inserted, dups, errs = import_feedback_batch(batch)
        elapsed = time.perf_counter() - t0
        throughput = 1000 / elapsed if elapsed > 0 else 0
        print(f"[BENCHMARK] Ingested 1,000 rows in {elapsed:.3f}s ({throughput:.1f} rows/sec)")
        self.assertEqual(inserted, 1000)
        self.assertEqual(errs, [])
        self.assertLess(elapsed, 5.0)

    def test_5000_row_batch_ingestion(self):
        """Benchmark 5,000 records."""
        batch = self._generate_synthetic_batch(5000)
        t0 = time.perf_counter()
        inserted, dups, errs = import_feedback_batch(batch)
        elapsed = time.perf_counter() - t0
        throughput = 5000 / elapsed if elapsed > 0 else 0
        print(f"[BENCHMARK] Ingested 5,000 rows in {elapsed:.3f}s ({throughput:.1f} rows/sec)")
        self.assertEqual(inserted, 5000)
        self.assertLess(elapsed, 10.0)

    def test_40000_row_batch_scaling_under_60_seconds(self):
        """Benchmark 40,000 records: must complete in under 60 seconds."""
        batch = self._generate_synthetic_batch(40000)
        t0 = time.perf_counter()
        inserted, dups, errs = import_feedback_batch(batch, batch_size=10000)
        elapsed = time.perf_counter() - t0
        throughput = 40000 / elapsed if elapsed > 0 else 0
        print(f"\n=======================================================")
        print(f" [BENCHMARK] 40,000 ROW BATCH INGESTION RESULTS:")
        print(f" Total Rows Ingested : {inserted:,}")
        print(f" Total Elapsed Time  : {elapsed:.2f} seconds")
        print(f" Ingestion Speed     : {throughput:,.1f} rows/second")
        print(f" Target Requirement  : Under 60.00 seconds")
        print(f" Margin Passed By    : {60.0 - elapsed:.2f} seconds")
        print(f"=======================================================\n")
        self.assertEqual(inserted, 40000)
        self.assertEqual(errs, [])
        self.assertLess(elapsed, 60.0) # Strictly < 60s target

if __name__ == "__main__":
    unittest.main()
