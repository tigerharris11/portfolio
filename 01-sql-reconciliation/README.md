# SQL reconciliation and anomaly triage

Two sources that should agree, never quite do. This project finds every place they don't,
classifies why, and checks itself against a known answer.

**Skills:** SQL (SQLite) · LEFT JOIN anti-joins · CTEs · GROUP BY / HAVING duplicate checks ·
date math · Python (pandas) · data-quality reporting

## Run it

```bash
python reconcile.py      # builds recon.db with synthetic data, writes report.md
python triage_demo.py    # runs anomaly_triage.sql on synthetic alert data
```

## What it does

[`generate_data.py`](generate_data.py) creates 2,000 records in an internal **ledger** and an
outside **feed**, then injects known defects: missing records on each side, status, amount and
date disagreements, and duplicate deliveries. [`reconcile.sql`](reconcile.sql) finds them:

| Query | Question it answers |
|---|---|
| `completeness` | Do both sides have the same number of rows and distinct IDs? |
| `duplicates_in_feed` | Was anything delivered twice? |
| `missing_in_feed` / `missing_in_ledger` | What exists on one side only? (LEFT JOIN anti-joins) |
| `field_mismatches` | Where do both sides have the record but disagree, and on which field? |
| `exception_summary` | One row per exception type: the table a manager reads first |

The report compares what the SQL found with what was injected. Every category matches
([`report.md`](report.md)), and a unit test fails if it ever stops matching.

## Anomaly triage

[`anomaly_triage.sql`](anomaly_triage.sql) is rebuilt from a query I wrote for my own
trading-data platform (Cloudflare D1 / SQLite, 67,479 webhook events). Out of 164 unresolved
position mismatches, I needed the ones caused by an alerting system firing two alerts on the
same bar and delivering only one. The query LEFT JOINs each anomaly to its event, then to a CTE
that counts alerts per strategy, ticker and bar. In the real data, anomalies sat on 2+-alert
bars **36.4%** of the time against a **6.6%** base rate.

Two lessons are written into the comments: COALESCE a missing join to 0, and a 1-alert bar does
not *disprove* a double-fire (the dropped twin leaves no row), so the flag is evidence for a
person, never a reason to auto-close.

## Context

At Cardinal Financial I built tracking and reporting workflows in Excel, SQL and Python that
pulled 472+ loan records from 18+ sources into one view; cleaning it surfaced mismatched dates
and statuses between systems. On my own data platform I reconciled 31,239 records against a
second source and traced each of 1,138 exceptions to a cause. This folder is the same method on
public, synthetic data.
