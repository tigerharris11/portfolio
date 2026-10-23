-- Reconcile an internal ledger against an outside feed (SQLite).
-- Each query answers one question. They run in order from reconcile.py.

-- name: completeness
-- How many records does each side have, and how many distinct IDs?
SELECT 'ledger' AS source, COUNT(*) AS row_count, COUNT(DISTINCT record_id) AS distinct_ids FROM ledger
UNION ALL
SELECT 'feed', COUNT(*), COUNT(DISTINCT record_id) FROM feed;

-- name: duplicates_in_feed
-- Same record delivered more than once.
SELECT record_id, COUNT(*) AS copies
FROM feed
GROUP BY record_id
HAVING COUNT(*) > 1
ORDER BY copies DESC, record_id;

-- name: missing_in_feed
-- In the ledger, never reached the outside system (LEFT JOIN anti-join).
SELECT l.record_id, l.event_ts, l.status
FROM ledger AS l
LEFT JOIN feed AS f ON f.record_id = l.record_id
WHERE f.record_id IS NULL
ORDER BY l.record_id;

-- name: missing_in_ledger
-- The outside system knows about it; we have no record.
SELECT f.record_id, f.event_ts
FROM (SELECT DISTINCT record_id, event_ts FROM feed) AS f
LEFT JOIN ledger AS l ON l.record_id = f.record_id
WHERE l.record_id IS NULL
ORDER BY f.record_id;

-- name: field_mismatches
-- Both sides have the record but disagree. Dedupe the feed first so a duplicate
-- doesn't double-count a mismatch. Each row says which field disagrees.
WITH feed_one AS (
    SELECT record_id, MIN(event_ts) AS event_ts, MIN(status) AS status, MIN(amount) AS amount
    FROM feed
    GROUP BY record_id
)
SELECT l.record_id,
       CASE
           WHEN l.status <> f.status                 THEN 'status'
           WHEN ABS(l.amount - f.amount) >= 0.01     THEN 'amount'
           WHEN DATE(l.event_ts) <> DATE(f.event_ts) THEN 'date'
       END AS field,
       l.status AS ledger_status, f.status AS feed_status,
       l.amount AS ledger_amount, f.amount AS feed_amount,
       ROUND(f.amount - l.amount, 2) AS amount_diff,
       CAST(JULIANDAY(f.event_ts) - JULIANDAY(l.event_ts) AS INTEGER) AS days_late
FROM ledger AS l
JOIN feed_one AS f ON f.record_id = l.record_id
WHERE l.status <> f.status
   OR ABS(l.amount - f.amount) >= 0.01
   OR DATE(l.event_ts) <> DATE(f.event_ts)
ORDER BY field, l.record_id;

-- name: exception_summary
-- One row per exception type: the table a manager actually reads.
WITH feed_one AS (
    SELECT record_id, MIN(event_ts) AS event_ts, MIN(status) AS status, MIN(amount) AS amount
    FROM feed GROUP BY record_id
),
exceptions AS (
    SELECT 'missing_in_feed' AS exception_type, l.record_id
    FROM ledger l LEFT JOIN feed_one f ON f.record_id = l.record_id WHERE f.record_id IS NULL
    UNION ALL
    SELECT 'missing_in_ledger', f.record_id
    FROM feed_one f LEFT JOIN ledger l ON l.record_id = f.record_id WHERE l.record_id IS NULL
    UNION ALL
    SELECT 'status_mismatch', l.record_id FROM ledger l JOIN feed_one f USING (record_id) WHERE l.status <> f.status
    UNION ALL
    SELECT 'amount_mismatch', l.record_id FROM ledger l JOIN feed_one f USING (record_id)
    WHERE l.status = f.status AND ABS(l.amount - f.amount) >= 0.01
    UNION ALL
    SELECT 'date_mismatch', l.record_id FROM ledger l JOIN feed_one f USING (record_id)
    WHERE l.status = f.status AND ABS(l.amount - f.amount) < 0.01 AND DATE(l.event_ts) <> DATE(f.event_ts)
    UNION ALL
    SELECT 'duplicate_in_feed', record_id FROM feed GROUP BY record_id HAVING COUNT(*) > 1
)
SELECT exception_type, COUNT(*) AS records
FROM exceptions
GROUP BY exception_type
ORDER BY records DESC;
