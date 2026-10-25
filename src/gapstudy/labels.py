"""Append-only label store for manual coding.

Every save appends one JSON line to coding/labels/pass{1,2}.jsonl, so the full
history is kept; the latest record per unit wins. Pass 2 is the blind re-code
of the reliability set and only offers units whose pass-1 label is old enough.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from gapstudy.github_client import PROJECT_ROOT

CODING = PROJECT_ROOT / "coding"
RECODE_DELAY = timedelta(days=14)
RECODE_SEED = 507


class LabelStore:
    def __init__(self, coding_dir: Path = CODING):
        self.dir = Path(coding_dir)
        (self.dir / "labels").mkdir(parents=True, exist_ok=True)

    def path(self, coding_pass: int) -> Path:
        return self.dir / "labels" / f"pass{coding_pass}.jsonl"

    def records(self, coding_pass: int) -> list[dict]:
        p = self.path(coding_pass)
        if not p.exists():
            return []
        return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]

    def latest(self, coding_pass: int) -> dict[str, dict]:
        out = {}
        for r in self.records(coding_pass):
            out[r["unit_id"]] = r
        return out

    def save(self, coding_pass: int, record: dict, now: datetime | None = None) -> dict:
        record = {**record, "pass": coding_pass,
                  "saved_at": (now or datetime.now(timezone.utc)).isoformat(timespec="seconds")}
        with self.path(coding_pass).open("a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    def queue(self, coding_pass: int, queue: pd.DataFrame, now: datetime | None = None) -> list[str]:
        """Unit ids to code in this pass, in order."""
        if coding_pass == 1:
            return list(queue.unit_id)
        now = now or datetime.now(timezone.utc)
        first = self.latest(1)
        ids = [u for u in queue[queue.set == "reliability"].unit_id
               if u in first and now - datetime.fromisoformat(first[u]["saved_at"]) >= RECODE_DELAY]
        random.Random(RECODE_SEED).shuffle(ids)
        return ids

    def recode_pending(self, queue: pd.DataFrame, now: datetime | None = None) -> tuple[int, str | None]:
        """Reliability units labelled in pass 1 but not yet old enough, and when the next becomes eligible."""
        now = now or datetime.now(timezone.utc)
        first = self.latest(1)
        waiting = [datetime.fromisoformat(first[u]["saved_at"]) + RECODE_DELAY
                   for u in queue[queue.set == "reliability"].unit_id
                   if u in first and datetime.fromisoformat(first[u]["saved_at"]) + RECODE_DELAY > now]
        return len(waiting), (min(waiting).date().isoformat() if waiting else None)

    def to_frame(self, coding_pass: int) -> pd.DataFrame:
        return pd.DataFrame(self.latest(coding_pass).values())
