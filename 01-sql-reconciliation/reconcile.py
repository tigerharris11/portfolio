"""Run reconcile.sql against the synthetic database and write a Markdown exception report.

    python reconcile.py            # builds recon.db, prints the summary, writes report.md
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

from generate_data import build

HERE = Path(__file__).parent


def load_queries(path: Path) -> dict[str, str]:
    """Split a .sql file on '-- name: <query>' markers."""
    queries, name, buf = {}, None, []
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"--\s*name:\s*(\w+)", line)
        if m:
            if name:
                queries[name] = "\n".join(buf).strip()
            name, buf = m.group(1), []
        elif name:
            buf.append(line)
    if name:
        queries[name] = "\n".join(buf).strip()
    return queries


def run(db_path: Path = HERE / "recon.db") -> dict[str, pd.DataFrame]:
    injected = build(db_path)
    con = sqlite3.connect(db_path)
    results = {name: pd.read_sql_query(sql, con) for name, sql in load_queries(HERE / "reconcile.sql").items()}
    con.close()
    results["injected"] = pd.DataFrame(sorted(injected.items()), columns=["exception_type", "injected"])
    return results


def md_table(df: pd.DataFrame) -> str:
    """Markdown table without extra dependencies."""
    cols = [str(c) for c in df.columns]
    rows = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    rows += ["| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(rows)


def write_report(results: dict[str, pd.DataFrame], out: Path = HERE / "report.md") -> None:
    summary = results["exception_summary"].merge(results["injected"], on="exception_type", how="outer")
    summary["check"] = (summary["records"] == summary["injected"]).map({True: "match", False: "CHECK"})
    mismatches = results["field_mismatches"]
    lines = [
        "# Reconciliation report (synthetic data)",
        "",
        "## Row counts",
        md_table(results["completeness"]),
        "",
        "## Exceptions found vs. defects injected",
        md_table(summary),
        "",
        "## Largest amount differences",
        mismatches[mismatches["field"] == "amount"]
        .reindex(mismatches["amount_diff"].abs().sort_values(ascending=False).index)
        .head(10)[["record_id", "ledger_amount", "feed_amount", "amount_diff"]]
        .dropna()
        .pipe(md_table),
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    res = run()
    write_report(res)
    print(res["exception_summary"].merge(res["injected"], on="exception_type").to_string(index=False))
