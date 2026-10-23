# Data job audit: "it ran" is not "it's right"

A scheduled job can exit successfully and still write nothing, write half its normal output, or
quietly stop running. This audit checks each job against what it is **supposed** to produce.

**Skills:** Python · data quality · monitoring design · root-cause investigation · written reporting

## Run it

```bash
python audit.py
```

| Check | Flags when |
|---|---|
| MISSING | no output has ever been written |
| STALE | output is older than the job's cadence plus a grace period |
| EMPTY | the run "succeeded" but wrote 0 rows |
| SHRANK | output fell far below its recent normal |

## The real version

On my own trading-data platform, 10 scheduled jobs fed the reports I relied on. Nothing was
visibly broken and nobody asked me to look. Auditing each job against its expected output found
**5 of 10 failing silently, 4 of them stale for 3 to 23 days**. I traced the five to a shared root
cause and wrote it up as an investigation note. The synthetic manifest here reproduces that shape
so the checks can be run and tested in public.
