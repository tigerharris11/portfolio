"""Generate two synthetic sources that *should* agree, with known defects injected.

Source A ("ledger") is what an internal system recorded. Source B ("feed") is what an
outside system reported. Real reconciliation work is finding where they disagree and why.

Every defect is injected on purpose and counted, so the SQL in reconcile.sql can be
checked against a known answer. All data is fake.
"""
import random
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
N_RECORDS = 2_000
STATUSES = ["application", "processing", "underwriting", "approved", "closing", "funded"]


def build(db_path: Path, n: int = N_RECORDS, seed: int = SEED) -> dict:
    rng = random.Random(seed)
    start = datetime(2026, 1, 5, 9, 0)
    ledger, feed = [], []
    injected = {"missing_in_feed": 0, "missing_in_ledger": 0, "status_mismatch": 0,
                "amount_mismatch": 0, "date_mismatch": 0, "duplicate_in_feed": 0}

    for i in range(1, n + 1):
        rid = f"R{i:05d}"
        ts = start + timedelta(minutes=37 * i + rng.randint(0, 30))
        status = rng.choice(STATUSES)
        amount = round(rng.uniform(90_000, 850_000), 2)
        ledger.append((rid, ts.strftime("%Y-%m-%d %H:%M"), status, amount))

        roll = rng.random()
        if roll < 0.010:                       # never reached the outside system
            injected["missing_in_feed"] += 1
            continue
        f_status, f_amount, f_ts = status, amount, ts
        if roll < 0.030:
            f_status = rng.choice([s for s in STATUSES if s != status])
            injected["status_mismatch"] += 1
        elif roll < 0.045:
            f_amount = round(amount + rng.choice([-1, 1]) * rng.uniform(50, 5_000), 2)
            injected["amount_mismatch"] += 1
        elif roll < 0.060:
            f_ts = ts + timedelta(days=rng.randint(1, 9))
            injected["date_mismatch"] += 1
        feed.append((rid, f_ts.strftime("%Y-%m-%d %H:%M"), f_status, f_amount))
        if rng.random() < 0.008:               # outside system sent the same record twice
            feed.append((rid, f_ts.strftime("%Y-%m-%d %H:%M"), f_status, f_amount))
            injected["duplicate_in_feed"] += 1

    for j in range(1, 13):                     # records only the outside system knows about
        feed.append((f"X{j:04d}", start.strftime("%Y-%m-%d %H:%M"), "application", 100_000.0))
        injected["missing_in_ledger"] += 1

    db_path.unlink(missing_ok=True)
    con = sqlite3.connect(db_path)
    con.executescript("""
        CREATE TABLE ledger (record_id TEXT PRIMARY KEY, event_ts TEXT, status TEXT, amount REAL);
        CREATE TABLE feed   (record_id TEXT, event_ts TEXT, status TEXT, amount REAL);
    """)
    con.executemany("INSERT INTO ledger VALUES (?,?,?,?)", ledger)
    con.executemany("INSERT INTO feed VALUES (?,?,?,?)", feed)
    con.commit()
    con.close()
    return injected


if __name__ == "__main__":
    out = Path(__file__).with_name("recon.db")
    print(build(out))
