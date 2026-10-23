"""Follow-up cadence engine: decides who gets a touch today and drafts it for human approval.

A public, simplified rebuild of the pattern behind an AI follow-up assistant I run for a
mortgage pipeline. The production version is private because it touches borrower data;
this one runs on fake leads and keeps the same guardrails:

  1. Allow-list import: only known-safe columns are kept. Anything else (SSN, DOB, income,
     account numbers) is dropped by code before it can reach a template or a model.
  2. Human approval: the engine only ever produces drafts. send() refuses unapproved drafts.
  3. Opt-out and quiet hours: STOP means stop, and nothing is drafted outside 9am-8pm.
  4. No invented numbers: a payment breakdown refuses to run without figures from the
     system of record.
  5. Same cadence for everyone: the rules depend on stage and dates, never on who the person is.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, datetime, time
from pathlib import Path

SAFE_COLUMNS = {"lead_id", "first_name", "stage", "last_contact", "opted_out", "preferred_channel"}

# Days to wait after the last touch, by stage.
CADENCE_DAYS = {
    "new": 1,
    "docs_requested": 2,
    "pre_approved": 4,
    "under_contract": 2,
    "locked": 3,
    "closed": None,          # no follow-up
}

TEMPLATES = {
    "new": "Hi {first_name}, thanks for reaching out. What's the best time this week to go over your options?",
    "docs_requested": "Hi {first_name}, quick check on the documents we discussed. Anything I can help you find?",
    "pre_approved": "Hi {first_name}, your pre-approval is still active. Have you found any homes you like?",
    "under_contract": "Hi {first_name}, congrats again on the contract. Is there anything you need from me before the next step?",
    "locked": "Hi {first_name}, your rate is locked. Have you had a chance to look at the open conditions?",
}

QUIET_START, QUIET_END = time(9, 0), time(20, 0)


@dataclass
class Draft:
    lead_id: str
    channel: str
    body: str
    approved: bool = False
    notes: list[str] = field(default_factory=list)


class NotApproved(Exception):
    pass


class MissingSystemFigures(Exception):
    pass


def load_leads(path: Path) -> tuple[list[dict], list[str]]:
    """Read leads and drop every column that is not on the allow-list."""
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        dropped = sorted(set(reader.fieldnames or []) - SAFE_COLUMNS)
        leads = [{k: v for k, v in row.items() if k in SAFE_COLUMNS} for row in reader]
    return leads, dropped


def is_due(lead: dict, today: date) -> bool:
    if lead.get("opted_out", "").strip().lower() in {"1", "true", "yes", "stop"}:
        return False
    wait = CADENCE_DAYS.get(lead["stage"])
    if wait is None:
        return False
    last = date.fromisoformat(lead["last_contact"])
    return (today - last).days >= wait


def todays_drafts(leads: list[dict], now: datetime) -> list[Draft]:
    if not (QUIET_START <= now.time() < QUIET_END):
        return []
    drafts = []
    for lead in leads:
        if is_due(lead, now.date()):
            body = TEMPLATES[lead["stage"]].format(first_name=lead["first_name"])
            drafts.append(Draft(lead["lead_id"], lead.get("preferred_channel") or "text", body))
    return drafts


def send(draft: Draft, transport=print) -> None:
    """The only way out. Refuses anything a human has not approved."""
    if not draft.approved:
        raise NotApproved(f"{draft.lead_id}: draft not approved; nothing sent")
    transport(f"[{draft.channel}] {draft.lead_id}: {draft.body}")


def payment_breakdown(figures: dict | None) -> dict:
    """Monthly payment from system-of-record figures. Refuses to guess."""
    required = ("loan_amount", "annual_rate", "term_months", "monthly_tax", "monthly_insurance")
    missing = [k for k in required if not figures or figures.get(k) in (None, "")]
    if missing:
        raise MissingSystemFigures(f"refusing to estimate; missing from system of record: {', '.join(missing)}")
    r = float(figures["annual_rate"]) / 12
    n = int(figures["term_months"])
    p = float(figures["loan_amount"])
    pi = p * r / (1 - (1 + r) ** -n) if r else p / n
    total = pi + float(figures["monthly_tax"]) + float(figures["monthly_insurance"])
    return {"principal_interest": round(pi, 2), "total_monthly": round(total, 2)}


if __name__ == "__main__":
    leads, dropped = load_leads(Path(__file__).with_name("sample_leads.csv"))
    print(f"Loaded {len(leads)} leads. Dropped columns on import: {dropped}")
    now = datetime(2026, 10, 23, 10, 30)
    drafts = todays_drafts(leads, now)
    print(f"{len(drafts)} drafts for {now:%Y-%m-%d %H:%M} (all pending approval):")
    for d in drafts:
        print(f"  {d.lead_id} [{d.channel}] {d.body}")
    try:
        send(drafts[0])
    except NotApproved as e:
        print("send() blocked:", e)
