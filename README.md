# Tiger Harris: data, operations and AI automation portfolio

Operations and data analyst in Chicago. Five years in mortgage lending, reviewing financial files
and clearing discrepancies against hard deadlines. In 2026 I started building the tools myself:
a reconciliation-heavy trading-data platform, an AI follow-up assistant for my own past clients, and a
daily AI video pipeline that now runs three YouTube channels. I also launched PayoutTax, a live tax tool for funded traders.

My production code is private because it touches client contact data, financial accounts or API keys.
**This repo rebuilds the core of each project on synthetic data so you can run it, read it, and
check it.** Every project runs with plain Python, and a test suite runs on every push.

[![tests](https://github.com/tigerharris11/portfolio/actions/workflows/tests.yml/badge.svg)](https://github.com/tigerharris11/portfolio/actions/workflows/tests.yml)

## Projects

| # | Project | What it shows | Skills |
|---|---|---|---|
| 01 | [SQL reconciliation and anomaly triage](01-sql-reconciliation) | Finds every disagreement between two sources, classifies it, and checks itself against a known answer | SQL, CTEs, joins, pandas, data quality |
| 02 | [Follow-up cadence engine](02-follow-up-engine) | The core of an AI assistant I built to stay in touch with my own past clients: drafts only, a person approves every send, sensitive fields dropped by code | Python, rules engines, human-in-the-loop, data minimization |
| 03 | [Data job audit](03-data-job-audit) | Catches jobs that "succeed" but write nothing, go stale, or shrink | Python, monitoring, root-cause analysis |
| 04 | [AI video pipeline architecture](04-ai-pipeline-architecture) | Multi-agent pipeline with a critique loop, rule checks and a human approval gate; shared render queue | AI orchestration, LLM APIs, system design |
| 05 | [Claude skills and the tune loop](05-claude-skills) | 80 agent skills across 9 project areas, and the loop that turns every correction into a written rule | Prompt and agent design, Claude Code, process improvement |

## Live product

**[PayoutTax](https://payouttax.com)**: a tax set-aside tracker for US traders paid by prop firms. Their payouts arrive
on a 1099-NEC with nothing withheld, stacked on top of a day-job salary, and most don't know what to save or when
quarterly payments are due. I found the gap (people searching for it, no trader-side tool), then designed, built and
launched it (code is private).

- Free calculator: federal tax at the bracket the day job sets, self-employment tax with the Social Security wage
  base, state estimates, safe-harbor minimums and the "add $X per paycheck to your W-4" alternative
- Accounts by emailed sign-in link (no passwords), payout and expense logs, and a dashboard on the same engine
- Built on Cloudflare Workers + D1; tax figures checked against IRS primary sources; 55 automated tests
- Security by default: hashed one-time tokens, CSRF checks, rate limits, a bot check, and full account deletion
- SEO guides with IRS sources, structured data, and a marketing plan for short-form video

## Numbers from the real (private) work

| | |
|---|---|
| Webhook events ingested into SQL | 67,479 from 87 strategies |
| Records reconciled against a second source | 31,239, with 1,138 exceptions each traced to a cause |
| Scheduled jobs audited | 10, of which 5 were failing silently |
| Loan records combined into one tracking view (Cardinal Financial) | 472+ from 18+ sources |
| Follow-up assistant | built in 2 days with 39 message templates; human approval on every send |
| AI video channels | 3 channels, 150,000+ views, 1,400+ credited archival images |
| Claude skills | 80 across 9 project areas |

## Skills and tools

| Area | Tools |
|---|---|
| Data | SQL (SQLite / Cloudflare D1, DuckDB), Python (pandas), Excel (pivot tables, lookups), JSON, CSV |
| Automation and AI | Claude, Claude Code, agent skills, MCP connectors, LLM APIs, text-to-speech APIs, scheduled jobs, webhooks |
| Engineering practice | Git, GitHub Actions, unit testing, written runbooks and investigation notes |
| Business systems | Salesforce, Encompass, Octane CRM, HubSpot (user), Microsoft 365 |
| Finance and lending | Residential mortgage origination through funding, condition clearing, reconciliation, compliance hand-offs |
| Media | Remotion (React video), FFmpeg, YouTube Data API, TradingView Pine Script |

## Run everything

```bash
pip install -r requirements.txt
python 01-sql-reconciliation/reconcile.py
python 02-follow-up-engine/engine.py
python 03-data-job-audit/audit.py
python 04-ai-pipeline-architecture/render_queue.py
python -m unittest discover -s tests -v
```

## Contact

[LinkedIn](https://www.linkedin.com/in/tiger-harris-8a45b3b4) · [YouTube: Dark History Files](https://www.youtube.com/@DarkHistoryFiles_HQ) · Chicago, IL · open to operations, analyst and AI-automation roles

*All data in this repository is synthetic. No client, customer or account data is included.*
