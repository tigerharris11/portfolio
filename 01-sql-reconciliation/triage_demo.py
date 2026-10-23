"""Run anomaly_triage.sql on a small synthetic events/anomalies set.

    python triage_demo.py
"""
import random
import sqlite3
from pathlib import Path

HERE = Path(__file__).parent


def build(con: sqlite3.Connection, seed: int = 7) -> None:
    rng = random.Random(seed)
    con.executescript("""
        CREATE TABLE events (event_id INTEGER PRIMARY KEY, strategy TEXT, ticker TEXT, bar_ts TEXT);
        CREATE TABLE anomalies (anomaly_id INTEGER PRIMARY KEY, event_id INTEGER, resolved INTEGER);
    """)
    eid = 0
    for bar in range(300):
        for strategy in ("alpha", "beta", "gamma"):
            fires = 2 if rng.random() < 0.07 else 1          # occasional double-fire
            for _ in range(fires):
                eid += 1
                con.execute("INSERT INTO events VALUES (?,?,?,?)",
                            (eid, strategy, "MNQ", f"2026-09-08 09:{bar // 60:02d}:{bar % 60:02d}"))
    # Anomalies are more likely on double-fire bars: that is the signal the query surfaces.
    rows = con.execute("""SELECT e.event_id, COUNT(*) OVER (PARTITION BY strategy, ticker, bar_ts) AS n
                          FROM events e""").fetchall()
    aid = 0
    for event_id, n in rows:
        if rng.random() < (0.35 if n >= 2 else 0.02):
            aid += 1
            con.execute("INSERT INTO anomalies VALUES (?,?,?)", (aid, event_id, int(rng.random() < 0.2)))
    con.commit()


def main() -> list[tuple]:
    con = sqlite3.connect(":memory:")
    build(con)
    rows = con.execute((HERE / "anomaly_triage.sql").read_text(encoding="utf-8")).fetchall()
    buckets: dict[str, int] = {}
    for r in rows:
        buckets[r[-1]] = buckets.get(r[-1], 0) + 1
    print(f"{len(rows)} open anomalies:", buckets)
    return rows


if __name__ == "__main__":
    main()
