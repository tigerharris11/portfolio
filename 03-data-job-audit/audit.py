"""Audit scheduled data jobs against what they are *supposed* to produce.

On my own data platform, 10 scheduled jobs fed the reports I relied on. Nothing looked broken,
but checking each job against its expected output found 5 failing silently, 4 of them stale
for 3 to 23 days. "The job ran" and "the data is current" are different claims; this checks
the second one.

A job is flagged when:
  - MISSING  its output does not exist at all
  - STALE    its output is older than the expected cadence plus a grace period
  - EMPTY    the last run "succeeded" but wrote zero rows (classic silent failure)
  - SHRANK   it wrote far fewer rows than its recent normal
Everything here runs on a synthetic manifest. All data is fake.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


@dataclass
class JobState:
    name: str
    cadence_hours: float
    last_output_at: datetime | None
    last_exit_code: int | None
    last_rows: int | None
    typical_rows: int | None


def check(job: JobState, now: datetime, grace: float = 0.5, shrink_ratio: float = 0.3) -> list[str]:
    issues = []
    if job.last_output_at is None:
        return ["MISSING: no output has ever been written"]
    age_h = (now - job.last_output_at).total_seconds() / 3600
    limit = job.cadence_hours * (1 + grace)
    if age_h > limit:
        issues.append(f"STALE: last output {age_h / 24:.1f} days ago (expected every {job.cadence_hours:g}h)")
    if job.last_exit_code == 0 and job.last_rows == 0:
        issues.append("EMPTY: exit code 0 but 0 rows written")
    if job.last_rows and job.typical_rows and job.last_rows < job.typical_rows * shrink_ratio:
        issues.append(f"SHRANK: {job.last_rows} rows vs ~{job.typical_rows} typical")
    return issues


def load_manifest(path: Path) -> list[JobState]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    jobs = []
    for j in raw["jobs"]:
        ts = j.get("last_output_at")
        jobs.append(JobState(j["name"], j["cadence_hours"], datetime.fromisoformat(ts) if ts else None,
                             j.get("last_exit_code"), j.get("last_rows"), j.get("typical_rows")))
    return jobs


def report(jobs: list[JobState], now: datetime) -> str:
    lines = [f"# Data job audit, {now:%Y-%m-%d %H:%M}", "", "| job | status | detail |", "|---|---|---|"]
    failing = 0
    for job in jobs:
        issues = check(job, now)
        failing += bool(issues)
        lines.append(f"| {job.name} | {'FAIL' if issues else 'ok'} | {'; '.join(issues) or '-'} |")
    lines += ["", f"**{failing} of {len(jobs)} jobs need attention.**"]
    return "\n".join(lines)


if __name__ == "__main__":
    now = datetime(2026, 8, 21, 8, 0)
    print(report(load_manifest(Path(__file__).with_name("jobs_manifest.json")), now))
