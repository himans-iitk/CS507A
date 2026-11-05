"""A simple page to check Claude's draft answers, one unit at a time.

    python -m gapstudy.verify.app [--port 8508]

For each agent-file section the page shows Claude's answer to one question
("Is this also in the README/CONTRIBUTING?") and asks: right or wrong?
A verdict is saved to coding/labels/pass1.jsonl (the same file the full
labelling tool uses), with the draft copied and the coverage replaced when
the verifier says it is wrong. The blind reliability set is never shown here.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from flask import Flask, abort, jsonify, request, send_file

from gapstudy.drafting import load_drafts
from gapstudy.labels import CODING, LabelStore
from gapstudy.labeltool.app import FORBIDDEN, PROCESSED, changed_fields, persistent_token

HERE = Path(__file__).resolve().parent
SETS = ("pilot", "main")
COVERAGES = ("agent_only", "partial", "shared", "agent_directed")


def verdict_record(draft: dict, unit_id: str, verdict: str, coverage: str | None,
                   name: str, note: str, seconds: int | None, version: str) -> dict:
    """Turn a right/wrong verdict into a full pass-1 label built from the draft."""
    label = {k: draft.get(k) for k in ("categories", "coverage", "evidence", "need", "barriers", "flags")}
    label["flags"] = list(label["flags"] or [])
    needs_detail = False
    if verdict == "wrong":
        if coverage not in COVERAGES or coverage == draft["coverage"]:
            raise ValueError("pick a different answer")
        label["coverage"] = coverage
        if coverage in ("shared", "agent_directed"):
            label["need"], label["barriers"] = None, []
        if coverage in ("agent_only", "agent_directed"):
            label["evidence"] = []
        if coverage in ("agent_only", "partial") and not label["need"]:
            needs_detail = True  # need/barriers to be filled in later
        if coverage in ("partial", "shared") and not label["evidence"]:
            needs_detail = True  # evidence passage to be added later
    changes = changed_fields(draft, label)
    return {"unit_id": unit_id, "codebook_version": version, "coder": name, **label,
            "notes": note, "seconds": seconds, "tool": "verify", "verdict": verdict,
            "needs_detail": needs_detail, "draft_shown": True, "drafter": draft.get("drafter"),
            "changed_fields": changes, "accepted_draft": not changes}


def create_app(coding_dir: Path = CODING, processed_dir: Path = PROCESSED, token: str | None = None) -> Flask:
    app = Flask(__name__)
    store = LabelStore(coding_dir)
    queue = pd.read_csv(coding_dir / "queue.csv")
    queue = queue[queue.set.isin(SETS)].drop_duplicates("unit_id")
    units = pd.read_csv(processed_dir / "units.csv").set_index("unit_id", drop=False)
    drafts = load_drafts(coding_dir)
    version = __import__("json").loads((coding_dir / "codebook.json").read_text())["version"]
    token = token or persistent_token(coding_dir)
    app.config["TOKEN"] = token

    @app.before_request
    def check_token():
        given = request.args.get("token") or request.cookies.get("token") or request.headers.get("X-Token")
        if given != token:
            return FORBIDDEN, 403

    @app.after_request
    def remember_token(resp):
        if request.args.get("token") == token:
            resp.set_cookie("token", token, httponly=True, samesite="Lax", max_age=60 * 60 * 24 * 90)
        return resp

    def text(v) -> str:
        return v if isinstance(v, str) else ""

    @app.get("/")
    def index():
        return send_file(HERE / "page.html")

    @app.get("/api/list")
    def listing():
        which = request.args.get("set", "pilot")
        if which not in SETS:
            abort(400)
        ids = [u for u in queue[queue.set == which].unit_id if u in drafts]
        done = store.latest(1)
        counts = {s: {"total": int(sum(u in drafts for u in g.unit_id)),
                      "done": int(sum(u in done for u in g.unit_id))}
                  for s, g in queue.groupby("set")}
        return jsonify({"ids": ids, "done": [u for u in ids if u in done], "counts": counts})

    @app.get("/api/unit/<path:unit_id>")
    def unit(unit_id):
        if unit_id not in drafts or unit_id not in set(queue.unit_id):
            abort(404)
        u, d = units.loc[unit_id], drafts[unit_id]
        human = units[(units.repo == u.repo) & (units.doc != "agent")]
        prev = store.latest(1).get(unit_id)
        return jsonify({
            "unit_id": unit_id, "repo": u.repo, "tool": u.tool,
            "heading": text(u.heading_path), "text": u.text,
            "draft": {"coverage": d["coverage"], "rationale": d.get("rationale", ""),
                      "evidence": d.get("evidence") or [], "flags": d.get("flags") or []},
            "human": [{"id": h.unit_id, "doc": h.doc, "heading": text(h.heading_path), "text": h.text}
                      for h in human.itertuples()],
            "previous": None if not prev else {"coder": prev.get("coder"), "verdict": prev.get("verdict"),
                                                "coverage": prev.get("coverage")},
        })

    @app.post("/api/verify")
    def verify():
        body = request.get_json(force=True)
        unit_id = body.get("unit_id")
        name = (body.get("name") or "").strip()[:40]
        if unit_id not in drafts or unit_id not in set(queue.unit_id):
            abort(404)
        if not name:
            abort(400, "name required")
        if body.get("verdict") not in ("correct", "wrong"):
            abort(400, "verdict required")
        try:
            record = verdict_record(drafts[unit_id], unit_id, body["verdict"], body.get("coverage"),
                                    name, (body.get("note") or "")[:2000], body.get("seconds"), version)
        except ValueError as e:
            abort(400, str(e))
        return jsonify(store.save(1, record))

    return app


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8508)
    args = ap.parse_args()
    app = create_app()
    print(f"\n  Open this link in your browser:\n"
          f"    http://localhost:{args.port}/?token={app.config['TOKEN']}\n")
    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()
