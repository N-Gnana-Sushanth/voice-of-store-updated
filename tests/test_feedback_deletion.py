"""Comprehensive test suite for feedback deletion functionality.

Verifies:
1. DELETE /api/feedback/<id> deletes a record from SQLite.
2. 404 response on nonexistent or invalid feedback IDs.
3. Persistent removal across database sessions.
4. Cascade removal of evidence from incident_evidence table.
5. Updating incident report counts when linked feedback is deleted.
6. Clean removal of zero-evidence auto-detected incidents.
7. Preservation of manually investigated incidents with audit logs.
8. Metric synchronization in /api/overview.
"""
import json
import os
import pathlib
import tempfile
import unittest

from app import app, init_db, db_session
import app as appmod


class FeedbackDeletionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        self.tmp.close()
        appmod.DB_PATH = pathlib.Path(self.tmp.name)
        init_db()
        self.client = app.test_client()

    def tearDown(self):
        try:
            os.unlink(self.tmp.name)
        except OSError:
            pass

    def add_feedback(self, text, store="STORE-001", issue=None, severity=None, timestamp="2026-10-16T10:00:00Z"):
        payload = {
            "text": text,
            "store_id": store,
            "timestamp": timestamp,
            "channel": "staff_note"
        }
        if issue:
            payload["issue_type"] = issue
        if severity:
            payload["severity"] = severity
        resp = self.client.post("/api/feedback", json=payload)
        self.assertIn(resp.status_code, (200, 201))
        return resp.get_json()["id"]

    def test_delete_existing_feedback_success(self):
        """Test deleting an existing feedback record returns 200 and success payload."""
        fid = self.add_feedback("Test feedback for deletion", store="STORE-002")
        
        # Verify it exists
        get_res = self.client.get(f"/api/feedback/{fid}")
        self.assertEqual(get_res.status_code, 200)

        # Delete it
        del_res = self.client.delete(f"/api/feedback/{fid}")
        self.assertEqual(del_res.status_code, 200)
        data = del_res.get_json()
        self.assertTrue(data.get("deleted"))
        self.assertEqual(data.get("id"), fid)

        # Verify it no longer exists via single get
        get_after = self.client.get(f"/api/feedback/{fid}")
        self.assertEqual(get_after.status_code, 404)

        # Verify not in feedback list
        all_fb = self.client.get("/api/feedback").get_json()
        self.assertFalse(any(f["id"] == fid for f in all_fb))

    def test_delete_nonexistent_feedback_returns_404(self):
        """Test deleting a nonexistent feedback record returns 404 error."""
        res = self.client.delete("/api/feedback/NONEXISTENT-999")
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertIn("error", data)
        self.assertIn("not found", data["error"].lower())

    def test_deletion_persists_in_sqlite(self):
        """Test that record is permanently deleted from SQLite database."""
        fid = self.add_feedback("Permanent deletion test record", store="STORE-003")
        
        # Direct DB query before
        with db_session() as c:
            row = c.execute("SELECT id FROM feedback WHERE id = ?", (fid,)).fetchone()
            self.assertIsNotNone(row)

        del_res = self.client.delete(f"/api/feedback/{fid}")
        self.assertEqual(del_res.status_code, 200)

        # Direct DB query after
        with db_session() as c:
            row = c.execute("SELECT id FROM feedback WHERE id = ?", (fid,)).fetchone()
            self.assertIsNone(row)

    def test_cascade_evidence_and_report_count_decrement(self):
        """Test that deleting 1 of 2 feedback records linked to an incident updates report count."""
        # Add 2 allergen feedback records to trigger an incident cluster
        fid1 = self.add_feedback("Peanut allergy warning missing on cookie box", store="STORE-010", issue="allergen_label")
        fid2 = self.add_feedback("Another customer noted missing allergen label", store="STORE-010", issue="allergen_label")

        incidents = self.client.get("/api/incidents").get_json()
        matching = [i for i in incidents if i["store_id"] == "STORE-010" and i["issue_type"] == "allergen_label"]
        self.assertTrue(len(matching) > 0)
        inc_id = matching[0]["id"]
        self.assertGreaterEqual(matching[0]["report_count"], 2)

        # Delete fid1
        del_res = self.client.delete(f"/api/feedback/{fid1}")
        self.assertEqual(del_res.status_code, 200)

        # Check evidence table directly
        with db_session() as c:
            ev_f1 = c.execute("SELECT 1 FROM incident_evidence WHERE feedback_id = ?", (fid1,)).fetchone()
            self.assertIsNone(ev_f1)
            ev_f2 = c.execute("SELECT 1 FROM incident_evidence WHERE feedback_id = ?", (fid2,)).fetchone()
            self.assertIsNotNone(ev_f2)

        # Check incident report count decremented to 1
        inc_after = self.client.get(f"/api/incidents/{inc_id}").get_json()
        self.assertEqual(inc_after["report_count"], 1)

    def test_auto_detected_incident_removed_when_all_evidence_deleted(self):
        """Test that an uninvestigated auto-detected incident is removed when its sole evidence is deleted."""
        fid = self.add_feedback("Live cockroach in bakery section", store="STORE-020", issue="hygiene")
        
        incidents = self.client.get("/api/incidents").get_json()
        matching = [i for i in incidents if i["store_id"] == "STORE-020"]
        self.assertTrue(len(matching) > 0)
        inc_id = matching[0]["id"]

        # Delete the only feedback record
        del_res = self.client.delete(f"/api/feedback/{fid}")
        self.assertEqual(del_res.status_code, 200)

        # Auto-detected incident should now be cleaned up
        inc_after = self.client.get(f"/api/incidents/{inc_id}")
        self.assertEqual(inc_after.status_code, 404)

    def test_manual_investigation_preserved_when_evidence_deleted(self):
        """Test that an incident with manual investigation findings is preserved with report_count=0."""
        fid = self.add_feedback("Freezer completely down and ice cream warm", store="STORE-030", issue="freezer_failure")
        
        incidents = self.client.get("/api/incidents").get_json()
        matching = [i for i in incidents if i["store_id"] == "STORE-030"]
        self.assertTrue(len(matching) > 0)
        inc_id = matching[0]["id"]

        # Add manual investigation findings
        patch_res = self.client.patch(f"/api/incidents/{inc_id}", json={
            "status": "Under investigation",
            "assigned_user": "Sarah Connor",
            "investigation_findings": "Compressor motor 4B tripped breaker. Technician scheduled.",
            "note": "Investigation opened by Store Ops"
        })
        self.assertEqual(patch_res.status_code, 200)

        # Now delete the feedback record
        del_res = self.client.delete(f"/api/feedback/{fid}")
        self.assertEqual(del_res.status_code, 200)

        # The investigated incident MUST be preserved
        inc_after = self.client.get(f"/api/incidents/{inc_id}").get_json()
        self.assertEqual(inc_after["id"], inc_id)
        self.assertEqual(inc_after["report_count"], 0)
        self.assertEqual(inc_after["status"], "Under investigation")
        self.assertEqual(inc_after["assigned_user"], "Sarah Connor")
        self.assertIn("Compressor motor", inc_after["investigation_findings"])

    def test_overview_metrics_decrement_on_delete(self):
        """Test that /api/overview counts decrease when feedback is deleted."""
        fid1 = self.add_feedback("Store is out of organic milk", store="STORE-040", issue="stockout")
        fid2 = self.add_feedback("All butter shelves empty", store="STORE-040", issue="stockout")

        ov_before = self.client.get("/api/overview").get_json()
        fb_before = ov_before["stats"]["total_feedback"]

        # Delete 1 record
        self.client.delete(f"/api/feedback/{fid1}")

        ov_after = self.client.get("/api/overview").get_json()
        fb_after = ov_after["stats"]["total_feedback"]
        self.assertEqual(fb_after, fb_before - 1)


if __name__ == "__main__":
    unittest.main()
