import io
import json
import os
import tempfile
import unittest
from app import app, init_db, seed_demo_data_if_empty

class FeatureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        import app as appmod
        appmod.DB_PATH = __import__("pathlib").Path(self.tmp.name)
        init_db()
        self.client = app.test_client()
        # Seed demo dataset
        seed_demo_data_if_empty()

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except OSError:
            pass

    def test_five_illustrative_incidents_exist_with_correct_properties(self):
        """Verify all 5 illustrative incidents required by Prompt Section 7 exist."""
        incidents = self.client.get("/api/incidents").get_json()
        inc_by_id = {i["id"]: i for i in incidents}

        # 1. Possible freezer malfunction — Store ST-104 — High severity — Store Operations — Investigating
        self.assertIn("FS-0104", inc_by_id)
        i1 = inc_by_id["FS-0104"]
        self.assertEqual(i1["store_id"], "ST-104")
        self.assertEqual(i1["severity"], "High")
        self.assertEqual(i1["department"], "Store Operations")
        self.assertEqual(i1["status"], "Investigating")
        self.assertTrue(i1["is_demo"])

        # 2. Incorrect allergen label reported — Store ST-208 — Critical severity — Appropriate food-safety owner — Escalation required
        self.assertIn("FS-0208", inc_by_id)
        i2 = inc_by_id["FS-0208"]
        self.assertEqual(i2["store_id"], "ST-208")
        self.assertEqual(i2["severity"], "Critical")
        self.assertTrue(i2["escalated"])

        # 3. Repeated stockout reports — Store ST-116 — Medium severity — Supply Chain — Assigned
        self.assertIn("FS-0116", inc_by_id)
        i3 = inc_by_id["FS-0116"]
        self.assertEqual(i3["store_id"], "ST-116")
        self.assertEqual(i3["severity"], "Medium")
        self.assertEqual(i3["department"], "Supply Chain")
        self.assertEqual(i3["status"], "Assigned")

        # 4. Mobile app ordering failure — Store ST-305 — High severity — Digital — Action in progress
        self.assertIn("FS-0305", inc_by_id)
        i4 = inc_by_id["FS-0305"]
        self.assertEqual(i4["store_id"], "ST-305")
        self.assertEqual(i4["severity"], "High")
        self.assertEqual(i4["department"], "Digital")
        self.assertEqual(i4["status"], "Action in progress")

        # 5. Customer service complaint — Store ST-091 — Low severity — Appropriate owner — Pending review
        self.assertIn("FS-0091", inc_by_id)
        i5 = inc_by_id["FS-0091"]
        self.assertEqual(i5["store_id"], "ST-091")
        self.assertEqual(i5["severity"], "Low")
        self.assertEqual(i5["status"], "Detected — awaiting review")

    def test_view_location_and_severity_endpoint_and_audit(self):
        """Verify the mandatory 'View Location & Severity' view event is tracked."""
        view_res = self.client.post("/api/incidents/FS-0104/view", json={"actor": "Alex Chen"})
        self.assertEqual(view_res.status_code, 200)

        # Check audit log contains the view action
        detail = self.client.get("/api/incidents/FS-0104").get_json()
        self.assertTrue(any(a["action"] == "investigation_opened" for a in detail["audit"]))

    def test_location_coordinates_and_missing_location_honesty(self):
        """Verify store ST-104 has real coordinates and ST-091 honestly reports missing location."""
        i_st104 = self.client.get("/api/incidents/FS-0104").get_json()
        self.assertIsNotNone(i_st104["store"]["latitude"])
        self.assertIsNotNone(i_st104["store"]["longitude"])
        self.assertIn("1420 N Michigan Ave", i_st104["store"]["address"])

        i_st091 = self.client.get("/api/incidents/FS-0091").get_json()
        # ST-091 must NOT invent GPS coordinates
        self.assertIsNone(i_st091["store"]["latitude"])
        self.assertIsNone(i_st091["store"]["longitude"])
        self.assertIsNone(i_st091["store"]["address"])
        self.assertEqual(i_st091["store"]["region"], "Pacific Northwest Region")

    def test_incident_deep_link_page(self):
        """Verify route /incidents/FS-0104 returns 200 HTML response."""
        res = self.client.get("/incidents/FS-0104")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Voice of Store", res.data)

    def test_investigation_form_submission_persists(self):
        """Verify investigation findings, verdict, and corrective action persist."""
        res = self.client.post("/api/incidents/FS-0104/investigate", json={
            "findings": "Walk-in compressor motor overheated. Backup condenser engaged.",
            "verdict": "Confirmed",
            "corrective_action": "Dispatched technician WO-9921.",
            "note": "Temperature stabilized at 3°C.",
            "actor": "Marcus Vance"
        })
        self.assertEqual(res.status_code, 200)

        # Re-fetch incident
        updated = self.client.get("/api/incidents/FS-0104").get_json()
        self.assertEqual(updated["investigation_verdict"], "Confirmed")
        self.assertIn("overheated", updated["investigation_findings"])
        self.assertEqual(updated["status"], "Action in progress")

    def test_escalation_endpoint(self):
        """Verify escalation sets Critical severity and logs reason."""
        res = self.client.post("/api/incidents/FS-0116/escalate", json={
            "actor": "Alex Chen",
            "reason": "Baby formula shortage exceeds 72 hours across 2 nearby stores."
        })
        self.assertEqual(res.status_code, 200)
        updated = self.client.get("/api/incidents/FS-0116").get_json()
        self.assertTrue(updated["escalated"])
        self.assertEqual(updated["priority"], "Critical")
        self.assertEqual(updated["status"], "Pending verification")

    def test_feedback_pagination(self):
        """Verify paginated feedback API."""
        res = self.client.get("/api/feedback?page=1&limit=10").get_json()
        self.assertIn("records", res)
        self.assertIn("total", res)
        self.assertEqual(res["page"], 1)
        self.assertEqual(res["limit"], 10)
        self.assertLessEqual(len(res["records"]), 10)

    def test_overview_metrics(self):
        """Verify overview summary counts reflect live database."""
        ov = self.client.get("/api/overview").get_json()
        self.assertGreater(ov["stats"]["total_feedback"], 0)
        self.assertGreater(ov["stats"]["active_incidents"], 0)
        self.assertGreaterEqual(ov["stats"]["critical_high_incidents"], 1)
        self.assertIn("needs_attention", ov)
        self.assertIn("recent_activity", ov)

    def test_notifications_endpoint_and_routing(self):
        """Verify notification bell data: header style, time ago, incident details, and deep link route."""
        res = self.client.get("/api/notifications")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("notifications", data)
        self.assertIn("unread_count", data)
        self.assertGreater(len(data["notifications"]), 0)

        # Verify item format matches requested style: "New alert received", time_ago, title, severity
        notif = data["notifications"][0]
        self.assertEqual(notif["header"], "New alert received")
        self.assertIn("ago", notif["time_ago"])
        self.assertTrue(bool(notif["title"]))
        self.assertIn(notif["severity"], ["Critical", "High", "Medium", "Low"])
        self.assertTrue(bool(notif["incident_id"]))

        # Verify clicking notification target route loads the exact incident
        inc_res = self.client.get(f"/api/incidents/{notif['incident_id']}")
        self.assertEqual(inc_res.status_code, 200)
        inc_data = inc_res.get_json()
        self.assertEqual(inc_data["id"], notif["incident_id"])
        self.assertEqual(inc_data["summary"], notif["title"])

if __name__ == "__main__":
    unittest.main()
