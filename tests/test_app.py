import io, json, os, tempfile, unittest
from app import app, init_db

class R5Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False)
        self.tmp.close()
        import app as appmod
        appmod.DB_PATH = __import__("pathlib").Path(self.tmp.name)
        init_db()
        self.client = app.test_client()

    def tearDown(self):
        try: os.unlink(self.tmp.name)
        except OSError: pass

    def add(self, text, store="S-1", issue=None, timestamp="2026-10-16T10:00:00Z"):
        data={"text":text,"store_id":store,"timestamp":timestamp,"channel":"staff_note"}
        if issue: data["issue_type"]=issue
        return self.client.post("/api/feedback",json=data)

    def test_health_and_ui(self):
        self.assertEqual(self.client.get("/api/health").status_code,200)
        self.assertEqual(self.client.get("/").status_code,200)

    def test_mandatory_safety_signal_single_report(self):
        r=self.add("Possible allergen label is wrong on this product")
        self.assertEqual(r.status_code,201)
        incidents=self.client.get("/api/incidents").get_json()
        self.assertTrue(any(x["severity"]=="High" and x["issue_type"]=="allergen_label" for x in incidents))

    def test_repeated_issue_cluster(self):
        self.add("Freezer not cold",timestamp="2026-10-16T08:00:00Z")
        self.add("Freezer is warm again",timestamp="2026-10-16T09:00:00Z",issue="freezer_failure")
        incidents=self.client.get("/api/incidents").get_json()
        self.assertTrue(any(x["issue_type"]=="freezer_failure" and x["report_count"]>=2 for x in incidents))

    def test_original_evidence_preserved_and_update_persists(self):
        self.add("Customer says wrong bill charged twice")
        incident=self.client.get("/api/incidents").get_json()[0]
        updated=self.client.patch("/api/incidents/"+incident["id"],json={"status":"Under investigation","assigned_user":"Reviewer A","note":"Checking receipt"})
        self.assertEqual(updated.status_code,200)
        feedback=self.client.get("/api/feedback").get_json()
        self.assertTrue(any("wrong bill" in x["original_text"] for x in feedback))
        self.assertTrue(self.client.get("/api/incidents").get_json()[0]["audit"])

    def test_bad_feedback_rejected(self):
        self.assertEqual(self.client.post("/api/feedback",json={"text":"hello"}).status_code,400)

    def test_weekly_report_schema(self):
        self.add("Out of stock")
        report=self.client.get("/api/reports/weekly").get_json()
        self.assertIn("top_issues",report)
        self.assertIn("basis",report)

if __name__ == "__main__": unittest.main()
