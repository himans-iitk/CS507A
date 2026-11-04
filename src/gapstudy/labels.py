"""Append-only label store for manual coding.

Every save appends one JSON line to coding/labels/pass{1,2}.jsonl, so the full
history is kept; the latest record per unit wins. Pass 1 is the verification of
AI drafts (pilot and main sets) and the first blind labelling of the reliability
set. Pass 2 is the second blind labelling of the reliability set by a different
person, for inter-rater agreement.
"""

from __future__ import annotations

import json
import random
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from gapstudy.github_client import PROJECT_ROOT

CODING = PROJECT_ROOT / "coding"
SECOND_CODER_SEED = 507


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

    def queue(self, coding_pass: int, queue: pd.DataFrame, coder: str | None = None) -> list[str]:
        """Unit ids to code in this pass, in order.

        Pass 2 offers reliability units that someone other than ``coder`` labelled in
        pass 1, in a fixed shuffled order, so no one labels the same unit twice."""
        if coding_pass == 1:
            return list(queue.unit_id)
        first = self.latest(1)
        ids = [u for u in queue[queue.set == "reliability"].unit_id
               if u in first and first[u].get("coder") != coder]
        random.Random(SECOND_CODER_SEED).shuffle(ids)
        return ids

    def second_coder_status(self, queue: pd.DataFrame, coder: str | None) -> dict[str, int]:
        """Reliability units not yet available to ``coder`` in pass 2, and why."""
        first = self.latest(1)
        rel = queue[queue.set == "reliability"].unit_id
        return {"no_first_label": int(sum(u not in first for u in rel)),
                "own_first_label": int(sum(u in first and first[u].get("coder") == coder for u in rel))}

    def to_frame(self, coding_pass: int) -> pd.DataFrame:
        return pd.DataFrame(self.latest(coding_pass).values())
