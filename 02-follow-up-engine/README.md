# Follow-up cadence engine (with guardrails)

A public rebuild of the core of an **AI follow-up assistant** I built with Claude Code and Python
for a residential mortgage pipeline and use every day. It decides who needs a follow-up today and
drafts the message, but **a person approves every message before it sends**.

**Skills:** Python · rules engines · data minimization · human-in-the-loop design · CSV/ETL ·
unit testing · workflow automation

## Run it

```bash
python engine.py
```

```
Loaded 8 leads. Dropped columns on import: ['annual_income', 'date_of_birth', 'ssn']
4 drafts for 2026-10-23 10:30 (all pending approval):
  L001 [text] Hi Avery, thanks for reaching out. What's the best time this week to go over your options?
  ...
send() blocked: L001: draft not approved; nothing sent
```

## Guardrails (the part that matters)

| Guardrail | How it's enforced |
|---|---|
| Sensitive data never enters the workflow | Import keeps an **allow-list** of columns; SSN, DOB, income and anything unknown are dropped in code |
| A person approves every message | The engine only creates drafts; `send()` raises unless `approved=True` |
| Opt-outs and quiet hours | `STOP` ends follow-up; nothing is drafted outside 9am-8pm |
| No invented numbers | `payment_breakdown()` refuses to run without figures from the system of record |
| Same rules for everyone | Cadence depends on stage and dates only |

## The production version

The private version adds a written map of the lender's systems (loan origination system, CRM,
texting, email folders), **39 message templates**, a per-lead ledger and borrower approval
breakdowns. It was built in two days and runs daily. It stays private because it works with
borrower files; this rebuild uses fake leads only.
