---
name: reconciliation-report
description: Reconcile two data sources that should agree (an internal ledger vs. an outside feed) and write an exception report a manager can act on. Use when asked to "reconcile", "tie out", "find mismatches" or "why don't these totals match".
---

# Reconciliation report

## Inputs
- Two tables or files and the key that should join them (e.g. `record_id`).
- The fields that must agree (status, amount, date) and the tolerance for each.

## Steps
1. **Completeness first.** Count rows and distinct keys on each side before comparing anything.
   If the counts differ, say so in the first line of the report.
2. **Duplicates.** `GROUP BY key HAVING COUNT(*) > 1` on each side. Dedupe before field checks so a
   duplicate never double-counts a mismatch.
3. **Missing on either side.** LEFT JOIN anti-joins in both directions.
4. **Field mismatches.** Join on the key; report one row per disagreeing field with both values.
5. **Summary table.** One row per exception type with a count. This goes at the top.
6. **Explain, don't just list.** For the largest exceptions, state the likely cause and the evidence.

## Guardrails
- Never "fix" data in either source. Report it; a person decides.
- If two totals are computed differently (e.g. one is capped by a page limit), document why they
  should not be reconciled instead of forcing them to match.
- Every number in the report comes from a query that is saved next to the report.
- No personal data (names, SSNs, account numbers) in the report. Use record keys.

## Definition of done
- [ ] Summary table at the top, exception counts add up
- [ ] Every exception type has at least one example row
- [ ] Queries saved and re-runnable
- [ ] Open questions listed for a human

## Change log (written by the tune loop; example entries)
- Added "document totals that should not be reconciled" after a dashboard count (capped at 50 by
  a page limit) was mistaken for the true count.
- Dedupe before field checks, so a duplicate feed row is not counted as two mismatches.
