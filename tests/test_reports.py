"""Unit tests for reporting, multi-region aggregation, and printable brief."""
from datetime import datetime, timedelta, timezone
import tempfile
import unittest

from app import app, init_db
from services.reports import build_weekly_report, build_multi_region_brief

class ReportsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        import app as appmod
        appmod.DB_PATH = __import__("pathlib").Path(self.tmp.name)
        init_db()
        self.client = app.test_client()

    def tearDown(self):
        try:
            import os
            os.unlink(self.tmp.name)
        except OSError:
            pass

    def test_multi_region_brief_grouping_and_rate_normalization(self):
        """Verify stores are correctly joined to regions and rates are normalized per 1,000."""
        now = datetime.now(timezone.utc)
        # ST-104 is Midwest Region, ST-208 is Northeast Region
        records = [
            {"id": "F1", "store_id": "ST-104", "timestamp": now.isoformat(), "issue_type": "freezer_failure", "severity": "High"},
            {"id": "F2", "store_id": "ST-104", "timestamp": now.isoformat(), "issue_type": "freezer_failure", "severity": "High"},
            {"id": "F3", "store_id": "ST-208", "timestamp": now.isoformat(), "issue_type": "allergen_label", "severity": "Critical"},
        ]
        incidents = [
            {"id": "FS-0104", "store_id": "ST-104", "summary": "Freezer issue", "severity": "High", "status": "Investigating"},
            {"id": "FS-0208", "store_id": "ST-208", "summary": "Allergen issue", "severity": "Critical", "status": "Pending verification"},
        ]
        brief = build_multi_region_brief(records, incidents, days=7, now=now)
        
        self.assertEqual(brief["total_feedback"], 3)
        self.assertEqual(brief["total_incidents"], 2)
        
        reg_by_name = {r["region"]: r for r in brief["regions"]}
        self.assertIn("Midwest Region", reg_by_name)
        self.assertIn("Northeast Region", reg_by_name)
        
        midwest = reg_by_name["Midwest Region"]
        self.assertEqual(midwest["feedback_volume"], 2)
        self.assertEqual(midwest["incident_count"], 1)
        # 1 incident / 2 feedback * 1000 = 500.0 per 1,000
        self.assertEqual(midwest["normalized_rate_per_k"], 500.0)

    def test_regional_brief_trend_indicators(self):
        """Verify trend indicator arrow logic against baseline."""
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=7)
        # Baseline records in prior 4 weeks (days 8-35)
        records = [
            # 10 current records for freezer_failure in ST-104 (Midwest)
            {"id": f"C{i}", "store_id": "ST-104", "timestamp": now.isoformat(), "issue_type": "freezer_failure", "severity": "High"}
            for i in range(10)
        ] + [
            # Baseline: only 4 records over 4 weeks (1 per week) -> huge spike (+900%)
            {"id": f"B{i}", "store_id": "ST-104", "timestamp": (start - timedelta(days=5)).isoformat(), "issue_type": "freezer_failure", "severity": "High"}
            for i in range(4)
        ]
        brief = build_multi_region_brief(records, [], days=7, now=now)
        midwest = [r for r in brief["regions"] if r["region"] == "Midwest Region"][0]
        top_issue = midwest["top_issues"][0]
        self.assertEqual(top_issue["issue_type"], "freezer_failure")
        self.assertEqual(top_issue["trend"], "↑")

    def test_regional_brief_endpoints(self):
        """Verify /api/reports/regional-brief and printable view return 200."""
        api_res = self.client.get("/api/reports/regional-brief")
        self.assertEqual(api_res.status_code, 200)
        data = api_res.get_json()
        self.assertIn("regions", data)
        self.assertIn("total_feedback", data)

        print_res = self.client.get("/reports/regional-brief/print")
        self.assertEqual(print_res.status_code, 200)
        self.assertIn(b"Multi-Region Executive Brief", print_res.data)
        self.assertIn(b"Isolated Print Styles", print_res.data)

if __name__ == "__main__":
    unittest.main()
