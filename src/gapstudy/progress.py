"""Coding progress against the schedule in coding/README.md.

    python -m gapstudy.progress
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd

from gapstudy.labels import CODING, LabelStore

# set -> (start, due); pass 2 is the blind re-code of the reliability set
SCHEDULE = {
    "pilot": (date(2026, 10, 27), date(2026, 11, 1)),
    "reliability": (date(2026, 11, 2), date(2026, 11, 4)),
    "main": (date(2026, 11, 4), date(2026, 11, 14)),
    "re-code": (date(2026, 11, 16), date(2026, 11, 19)),
}


def summary(coding_dir: Path, today: date) -> pd.DataFrame:
    queue = pd.read_csv(coding_dir / "queue.csv")
    store = LabelStore(coding_dir)
    done1, done2 = store.latest(1), store.latest(2)
    rows = []
    for name, (start, due) in SCHEDULE.items():
        ids = queue[queue.set == ("reliability" if name == "re-code" else name)].unit_id
        if ids.empty:
            continue
        done = sum(u in (done2 if name == "re-code" else done1) for u in ids)
        days_left = (due - today).days + 1
        if done == len(ids):
            status = "done"
        elif today < start:
            status = f"starts {start:%b %d}"
        elif days_left <= 0:
            status = f"overdue since {due:%b %d}"
        else:
            status = f"{-(-(len(ids) - done) // days_left)} units/day to finish by {due:%b %d}"
        rows.append({"step": name, "done": done, "total": len(ids), "%": round(100 * done / len(ids)), "status": status})
    return pd.DataFrame(rows).set_index("step")


def main() -> None:
    print(summary(CODING, date.today()).to_markdown())


if __name__ == "__main__":
    main()
