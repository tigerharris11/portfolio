-- Anomaly triage: rank unresolved mismatches by likely cause.
--
-- Pattern rebuilt from a query I wrote for my own trading-data platform (Cloudflare D1 / SQLite).
-- An alerting system sometimes fires two alerts on the same bar and delivers only one.
-- For every open anomaly, count how many alerts landed on that same strategy, ticker and bar.
-- Anomalies sitting on 2+-alert bars are the likely "double-fire" cases.
--
-- Two lessons baked in:
--   1. COALESCE to 0: a LEFT JOIN with no match means "no alerts on that bar", not NULL.
--   2. A dropped twin alert leaves no row, so a 1-alert bar does NOT disprove a double-fire.
--      The flag is evidence for a human, never a reason to auto-close the row.

WITH alerts_per_bar AS (
    SELECT strategy, ticker, bar_ts, COUNT(*) AS alerts_on_bar
    FROM events
    GROUP BY strategy, ticker, bar_ts
)
SELECT a.anomaly_id,
       e.strategy,
       e.ticker,
       e.bar_ts,
       COALESCE(apb.alerts_on_bar, 0)                   AS alerts_on_bar,
       CASE WHEN COALESCE(apb.alerts_on_bar, 0) >= 2
            THEN 'likely double-fire' ELSE 'other cause' END AS triage_bucket
FROM anomalies AS a
LEFT JOIN events AS e
       ON e.event_id = a.event_id
LEFT JOIN alerts_per_bar AS apb
       ON apb.strategy = e.strategy
      AND apb.ticker   = e.ticker
      AND apb.bar_ts   = e.bar_ts
WHERE a.resolved = 0
ORDER BY alerts_on_bar DESC, a.anomaly_id;
