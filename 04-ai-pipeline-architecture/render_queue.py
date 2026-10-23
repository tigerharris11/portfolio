"""Shared render queue: one job at a time, earliest publish date first, fails closed.

Three YouTube channels share one PC for video renders. Rendering two at once crashes the
machine; rendering in arrival order makes the video due tomorrow wait behind one due next
week. This queue fixes both, and treats "I can't tell if the machine is busy" as busy.
"""
from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable


@dataclass(order=True)
class RenderJob:
    publish_at: datetime
    enqueued_at: datetime
    job_id: str = field(compare=False)
    channel: str = field(compare=False)


class RenderQueue:
    def __init__(self, is_busy: Callable[[], bool]):
        self._heap: list[RenderJob] = []
        self._is_busy = is_busy
        self.running: RenderJob | None = None

    def enqueue(self, job: RenderJob) -> None:
        if any(j.job_id == job.job_id for j in self._heap) or (self.running and self.running.job_id == job.job_id):
            raise ValueError(f"{job.job_id} already queued")
        heapq.heappush(self._heap, job)

    def machine_free(self) -> bool:
        """Fail closed: if the busy check itself breaks, assume busy and start nothing."""
        try:
            return not self._is_busy()
        except Exception:
            return False

    def start_next(self) -> RenderJob | None:
        if self.running or not self._heap or not self.machine_free():
            return None
        self.running = heapq.heappop(self._heap)
        return self.running

    def finish(self, job_id: str) -> None:
        if not self.running or self.running.job_id != job_id:
            raise ValueError(f"{job_id} is not the running job")
        self.running = None

    def pending(self) -> list[str]:
        return [j.job_id for j in sorted(self._heap)]


if __name__ == "__main__":
    q = RenderQueue(is_busy=lambda: False)
    t = datetime(2026, 10, 23, 8)
    q.enqueue(RenderJob(datetime(2026, 10, 30), t, "gilt-ep12", "Gilt & Gallows"))
    q.enqueue(RenderJob(datetime(2026, 10, 24), t, "dh-ep27", "Dark History"))
    q.enqueue(RenderJob(datetime(2026, 10, 26), t, "space-ep09", "Space"))
    print("order:", q.pending())
    print("start:", q.start_next().job_id, "| second start while running:", q.start_next())
