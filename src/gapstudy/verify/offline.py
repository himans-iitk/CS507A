"""Offline verify page: one HTML file anyone can open, no cluster or server needed.

    python -m gapstudy.verify.offline export [--set main]   # -> coding/verify_offline_<set>.html
    python -m gapstudy.verify.offline merge marks.jsonl [...] # add downloaded marks to pass1.jsonl

The HTML embeds the agent units, Claude's drafts and each repo's README/CONTRIBUTING
sections. Marks are kept in the browser (localStorage) and exported with the
"Download my marks" button as JSON lines, which `merge` validates and appends to
coding/labels/pass1.jsonl exactly as the online page would. The blind
reliability set is never exported.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from gapstudy.drafting import load_drafts
from gapstudy.labels import CODING, LabelStore
from gapstudy.labeltool.app import PROCESSED
from gapstudy.verify.app import HERE, SETS, verdict_record

SHIM = r"""
<script>
(function(){
  const D = JSON.parse(document.getElementById("vdata").textContent);
  const KEY = "verify-marks-" + D.exported_at;
  let marks = {};
  try { marks = JSON.parse(localStorage.getItem(KEY) || "{}"); } catch(e) {}
  const persist = () => { try { localStorage.setItem(KEY, JSON.stringify(marks)); } catch(e) { alert("Your browser blocked saving. Download your marks now so nothing is lost."); } };
  const isDone = u => !!marks[u] || !!D.previous[u];
  const ok = x => Promise.resolve(JSON.parse(JSON.stringify(x)));
  window.OFFLINE = {
    sets: Object.keys(D.sets),
    count: () => Object.keys(marks).length,
    onChange: null,
    api(path, opts) {
      const url = new URL(path, "http://x/");
      if (url.pathname === "/api/list") {
        const ids = D.sets[url.searchParams.get("set")] || [];
        const counts = {};
        for (const [s, l] of Object.entries(D.sets)) counts[s] = {total: l.length, done: l.filter(isDone).length};
        return ok({ids, done: ids.filter(isDone), counts});
      }
      if (url.pathname.startsWith("/api/unit/")) {
        const id = decodeURIComponent(url.pathname.slice("/api/unit/".length));
        const u = D.units[id];
        const m = marks[id];
        return ok({...u, unit_id: id, human: D.human[u.repo] || [],
                   previous: m ? {coder: m.name, verdict: m.verdict, coverage: m.coverage} : (D.previous[id] || null)});
      }
      if (url.pathname === "/api/verify") {
        const b = JSON.parse(opts.body);
        marks[b.unit_id] = {...b, marked_at: new Date().toISOString()};
        persist(); if (this.onChange) this.onChange();
        return ok({saved: true});
      }
      return Promise.reject(new Error("unknown " + path));
    },
    download(name) {
      const lines = Object.values(marks).map(m => JSON.stringify(m)).join("\n") + "\n";
      const a = document.createElement("a");
      a.href = URL.createObjectURL(new Blob([lines], {type: "application/json"}));
      const who = (name || "verifier").replace(/[^A-Za-z0-9_-]+/g, "_");
      a.download = `verify_marks_${who}_${new Date().toISOString().slice(0,10)}.jsonl`;
      document.body.appendChild(a); a.click(); a.remove();
    },
  };
})();
</script>
"""


def build_data(coding_dir: Path, processed_dir: Path, sets: list[str]) -> dict:
    queue = pd.read_csv(coding_dir / "queue.csv").drop_duplicates("unit_id")
    units = pd.read_csv(processed_dir / "units.csv").set_index("unit_id", drop=False)
    drafts = load_drafts(coding_dir)
    done = LabelStore(coding_dir).latest(1)
    text = lambda v: v if isinstance(v, str) else ""  # noqa: E731
    data = {"exported_at": pd.Timestamp.now("UTC").strftime("%Y%m%dT%H%M%S"), "sets": {}, "units": {},
            "human": {}, "previous": {}}
    for s in sets:
        ids = [u for u in queue[queue.set == s].unit_id if u in drafts]
        data["sets"][s] = ids
        for uid in ids:
            u, d = units.loc[uid], drafts[uid]
            data["units"][uid] = {"repo": u.repo, "tool": u.tool, "heading": text(u.heading_path), "text": u.text,
                                  "draft": {"coverage": d["coverage"], "rationale": d.get("rationale", ""),
                                            "evidence": d.get("evidence") or [], "flags": d.get("flags") or []}}
            if uid in done:
                p = done[uid]
                data["previous"][uid] = {"coder": p.get("coder"), "verdict": p.get("verdict"), "coverage": p.get("coverage")}
    repos = {v["repo"] for v in data["units"].values()}
    human = units[units.repo.isin(repos) & (units.doc != "agent")]
    for h in human.itertuples():
        data["human"].setdefault(h.repo, []).append(
            {"id": h.unit_id, "doc": h.doc, "heading": text(h.heading_path), "text": h.text})
    return data


def export(sets: list[str], out: Path, coding_dir: Path = CODING, processed_dir: Path = PROCESSED) -> Path:
    data = build_data(coding_dir, processed_dir, sets)
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = (HERE / "page.html").read_text()
    inject = f'<script type="application/json" id="vdata">{blob}</script>\n{SHIM}\n<script>'
    page = page.replace("<script>", inject, 1).replace("<title>Check Claude's Answers</title>",
                                                       "<title>Check Claude's Answers (offline)</title>")
    out.write_text(page)
    return out


def merge(paths: list[Path], coding_dir: Path = CODING) -> dict[str, int]:
    """Append downloaded marks to pass1.jsonl; re-merging the same file is a no-op."""
    store = LabelStore(coding_dir)
    drafts = load_drafts(coding_dir)
    queue = pd.read_csv(coding_dir / "queue.csv").drop_duplicates("unit_id").set_index("unit_id")["set"]
    version = json.loads((coding_dir / "codebook.json").read_text())["version"]
    seen = {(r["unit_id"], r.get("coder"), r.get("marked_at")) for r in store.records(1) if r.get("marked_at")}
    stats = {"added": 0, "already": 0, "rejected": 0}
    for path in paths:
        for line in Path(path).read_text().splitlines():
            if not line.strip():
                continue
            m = json.loads(line)
            uid, name = m.get("unit_id"), (m.get("name") or "").strip()[:40]
            if uid not in drafts or queue.get(uid) not in SETS or not name:
                stats["rejected"] += 1
                continue
            if (uid, name, m.get("marked_at")) in seen:
                stats["already"] += 1
                continue
            try:
                rec = verdict_record(drafts[uid], uid, m.get("verdict"), m.get("coverage"), name,
                                     (m.get("note") or "")[:2000], m.get("seconds"), version)
            except ValueError:
                stats["rejected"] += 1
                continue
            if m.get("verdict") not in ("correct", "wrong"):
                stats["rejected"] += 1
                continue
            rec.update(tool="verify-offline", marked_at=m.get("marked_at"))
            store.save(1, rec)
            seen.add((uid, name, m.get("marked_at")))
            stats["added"] += 1
    return stats


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("export")
    e.add_argument("--set", choices=SETS, action="append")
    e.add_argument("--out", type=Path)
    m = sub.add_parser("merge")
    m.add_argument("files", nargs="+", type=Path)
    args = ap.parse_args()
    if args.cmd == "export":
        sets = args.set or ["main"]
        out = args.out or CODING / f"verify_offline_{'_'.join(sets)}.html"
        export(sets, out)
        print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB) - send this one file to each verifier")
    else:
        print(merge(args.files))


if __name__ == "__main__":
    main()
