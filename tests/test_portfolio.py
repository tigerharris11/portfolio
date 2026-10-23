"""Tests for every runnable project. Standard library unittest, so no test framework to install.

    python -m unittest discover -s tests -v
"""
import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(folder: str, module: str):
    path = ROOT / folder
    sys.path.insert(0, str(path))
    spec = importlib.util.spec_from_file_location(module, path / f"{module}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module] = mod
    spec.loader.exec_module(mod)
    return mod


class TestReconciliation(unittest.TestCase):
    def test_sql_finds_exactly_what_was_injected(self):
        recon = load("01-sql-reconciliation", "reconcile")
        with tempfile.TemporaryDirectory() as d:
            res = recon.run(Path(d) / "t.db")
        found = dict(zip(res["exception_summary"].exception_type, res["exception_summary"].records))
        injected = dict(zip(res["injected"].exception_type, res["injected"].injected))
        self.assertEqual(found, injected)

    def test_triage_flags_double_fires(self):
        triage = load("01-sql-reconciliation", "triage_demo")
        rows = triage.main()
        self.assertTrue(rows)
        for *_, alerts_on_bar, bucket in rows:
            self.assertEqual(bucket == "likely double-fire", alerts_on_bar >= 2)

    def test_triage_coalesces_missing_join_to_zero(self):
        con = sqlite3.connect(":memory:")
        con.executescript("""
            CREATE TABLE events (event_id INTEGER PRIMARY KEY, strategy TEXT, ticker TEXT, bar_ts TEXT);
            CREATE TABLE anomalies (anomaly_id INTEGER PRIMARY KEY, event_id INTEGER, resolved INTEGER);
            INSERT INTO anomalies VALUES (1, 999, 0);
        """)
        sql = (ROOT / "01-sql-reconciliation" / "anomaly_triage.sql").read_text(encoding="utf-8")
        (row,) = con.execute(sql).fetchall()
        self.assertEqual(row[4], 0)
        self.assertEqual(row[5], "other cause")


class TestFollowUpEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.eng = load("02-follow-up-engine", "engine")
        cls.leads, cls.dropped = cls.eng.load_leads(ROOT / "02-follow-up-engine" / "sample_leads.csv")

    def test_sensitive_columns_dropped(self):
        self.assertEqual(self.dropped, ["annual_income", "date_of_birth", "ssn"])
        for lead in self.leads:
            self.assertTrue(set(lead) <= self.eng.SAFE_COLUMNS)

    def test_opt_out_and_closed_never_drafted(self):
        drafts = self.eng.todays_drafts(self.leads, datetime(2026, 10, 23, 10, 30))
        ids = {d.lead_id for d in drafts}
        self.assertNotIn("L006", ids)   # STOP
        self.assertNotIn("L008", ids)   # do_not_contact
        self.assertEqual(ids, {"L001", "L003", "L004", "L007"})

    def test_quiet_hours(self):
        self.assertEqual(self.eng.todays_drafts(self.leads, datetime(2026, 10, 23, 21, 0)), [])

    def test_send_requires_approval(self):
        d = self.eng.Draft("L001", "text", "hi")
        with self.assertRaises(self.eng.NotApproved):
            self.eng.send(d, transport=lambda _: None)
        d.approved = True
        sent = []
        self.eng.send(d, transport=sent.append)
        self.assertEqual(len(sent), 1)

    def test_breakdown_refuses_without_figures(self):
        with self.assertRaises(self.eng.MissingSystemFigures):
            self.eng.payment_breakdown({"loan_amount": 300000})
        out = self.eng.payment_breakdown({"loan_amount": 300000, "annual_rate": 0.06, "term_months": 360,
                                          "monthly_tax": 300, "monthly_insurance": 100})
        self.assertAlmostEqual(out["principal_interest"], 1798.65, places=2)


class TestJobAudit(unittest.TestCase):
    def test_manifest_flags_five_of_ten(self):
        audit = load("03-data-job-audit", "audit")
        jobs = audit.load_manifest(ROOT / "03-data-job-audit" / "jobs_manifest.json")
        now = datetime(2026, 8, 21, 8, 0)
        failing = [j.name for j in jobs if audit.check(j, now)]
        self.assertEqual(len(jobs), 10)
        self.assertEqual(len(failing), 5)

    def test_empty_success_is_a_failure(self):
        audit = load("03-data-job-audit", "audit")
        job = audit.JobState("x", 24, datetime(2026, 8, 21, 7), 0, 0, 100)
        self.assertTrue(any(i.startswith("EMPTY") for i in audit.check(job, datetime(2026, 8, 21, 8))))


class TestRenderQueue(unittest.TestCase):
    def setUp(self):
        self.rq = load("04-ai-pipeline-architecture", "render_queue")
        self.t = datetime(2026, 10, 23)

    def job(self, jid, day):
        return self.rq.RenderJob(datetime(2026, 10, day), self.t, jid, "c")

    def test_earliest_publish_first_and_one_at_a_time(self):
        q = self.rq.RenderQueue(is_busy=lambda: False)
        q.enqueue(self.job("late", 30))
        q.enqueue(self.job("soon", 24))
        self.assertEqual(q.start_next().job_id, "soon")
        self.assertIsNone(q.start_next())
        q.finish("soon")
        self.assertEqual(q.start_next().job_id, "late")

    def test_fails_closed_when_busy_check_breaks(self):
        def broken():
            raise RuntimeError("cannot read GPU state")
        q = self.rq.RenderQueue(is_busy=broken)
        q.enqueue(self.job("a", 24))
        self.assertIsNone(q.start_next())

    def test_duplicate_enqueue_rejected(self):
        q = self.rq.RenderQueue(is_busy=lambda: False)
        q.enqueue(self.job("a", 24))
        with self.assertRaises(ValueError):
            q.enqueue(self.job("a", 25))


if __name__ == "__main__":
    unittest.main()
