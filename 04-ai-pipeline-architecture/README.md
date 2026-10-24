# AI video pipeline: architecture

A daily, mostly unattended pipeline that researches, scripts, narrates, edits, renders and
packages documentary videos, then **stops for human approval** before anything is published.
It started as one YouTube channel in May 2026 and now runs three; the channels have passed
**150,000 views** ([Dark History Files on YouTube](https://www.youtube.com/@DarkHistoryFiles_HQ)). The production code is private (it holds API keys and licensed assets).
This folder documents the design and includes one component rebuilt in the open:
[`render_queue.py`](render_queue.py).

## Flow

```mermaid
flowchart LR
    A[Topic pick<br/>relevance to post date] --> B[Research agent<br/>multiple models, sources logged]
    B --> C[Script agent]
    C --> D[Critic pass<br/>facts, weak sections, gaps]
    D -->|rewrite| C
    D --> E[Narration<br/>text-to-speech]
    E --> F[Scene build<br/>archival images, each credited]
    F --> G[Pre-publish checks<br/>written rules, fail = stop]
    G --> H[Render queue<br/>shared by 3 channels]
    H --> I{Human approval}
    I -->|approve| J[Schedule upload]
    I -->|reject| C
```

## Design decisions

| Decision | Why |
|---|---|
| Human approval gate before publish | The pipeline drafts; a person decides. Nothing goes live on autopilot. |
| Self-critique loop before narration | Fixing a script is cheap; re-rendering a video is not. |
| Written rules enforced by a check that **fails** the build | A weak click-rate turned into 7 thumbnail rules; a rule that isn't checked isn't a rule. |
| Every image carries a source credit file | 1,400+ archival images, each credited. Licensing is part of the pipeline, not an afterthought. |
| One shared render queue, earliest publish date first | Three channels on one PC: no collisions, and the video due soonest renders first. |
| Busy check fails closed | If the queue can't tell whether the machine is free, it waits. |
| Failures become instructions | Each owner correction is logged as an issue and turned into an updated skill instruction (see [`../05-claude-skills`](../05-claude-skills)). |

## Tools

Python · Claude / Claude Code · multiple LLM APIs · text-to-speech API · Remotion (React video) ·
FFmpeg · YouTube Data API · Git · scheduled tasks
