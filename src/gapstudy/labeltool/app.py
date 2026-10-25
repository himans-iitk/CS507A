"""Local web tool for coding agent-file units against the human docs.

    python -m gapstudy.labeltool.app [--port 8507]

Prints a URL with an access token. Open it through VS Code's port forwarding
(Ports tab) or an SSH tunnel: ssh -L 8507:localhost:8507 <login node>.
The server binds to localhost only; the token keeps other users of a shared
login node out.
"""

from __future__ import annotations

import argparse
import json
import secrets
from pathlib import Path

import pandas as pd
from flask import Flask, abort, jsonify, request, send_file

from gapstudy.github_client import PROJECT_ROOT
from gapstudy.labels import CODING, LabelStore

PROCESSED = PROJECT_ROOT / "data" / "processed"
HERE = Path(__file__).resolve().parent
LABEL_FIELDS = ("categories", "coverage", "evidence", "need", "barriers", "flags", "notes", "seconds")
FORBIDDEN = """<!doctype html><title>Token needed</title>
<body style="font:15px/1.5 system-ui;max-width:640px;margin:40px auto;padding:0 16px">
<h2>Access token missing or wrong</h2>
<p>Open the tool with the full link printed in the terminal where you started it, including
<code>?token=...</code>. The token is also saved in <code>coding/.labeltool_token</code>.</p>
<p>After opening it once with the token, this browser remembers it.</p></body>"""


def persistent_token(coding_dir: Path) -> str:
    """One token per checkout, reused across restarts so saved links keep working."""
    path = Path(coding_dir) / ".labeltool_token"
    if not path.exists():
        path.write_text(secrets.token_urlsafe(16))
        path.chmod(0o600)
    return path.read_text().strip()


def create_app(coding_dir: Path = CODING, processed_dir: Path = PROCESSED, token: str | None = None) -> Flask:
    app = Flask(__name__)
    store = LabelStore(coding_dir)
    codebook = json.loads((coding_dir / "codebook.json").read_text())
    queue = pd.read_csv(coding_dir / "queue.csv")
    units = pd.read_csv(processed_dir / "units.csv").set_index("unit_id", drop=False)
    prelabel_path = coding_dir / "prelabels.csv"
    prelabels = (pd.read_csv(prelabel_path).set_index("unit_id").categories.map(json.loads).to_dict()
                 if prelabel_path.exists() else {})
    meta = queue.drop_duplicates("unit_id").set_index("unit_id")
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

    def coding_pass() -> int:
        p = int(request.args.get("pass", 1))
        if p not in (1, 2):
            abort(400)
        return p

    @app.get("/")
    def index():
        return send_file(HERE / "index.html")

    @app.get("/api/state")
    def state():
        p = coding_pass()
        ids = store.queue(p, queue)
        done = store.latest(p)
        todo = [u for u in ids if u not in done]
        pending, next_date = store.recode_pending(queue)
        by_set = {s: {"total": int(n), "done": int(sum(u in done for u in g.unit_id))}
                  for s, g in queue.groupby("set") for n in [len(g)]}
        return jsonify({
            "pass": p, "codebook": codebook, "queue": ids, "next": todo[0] if todo else None,
            "done": len([u for u in ids if u in done]), "total": len(ids), "by_set": by_set,
            "recode_waiting": pending, "recode_next_date": next_date,
        })

    @app.get("/api/unit/<path:unit_id>")
    def unit(unit_id):
        p = coding_pass()
        if unit_id not in meta.index:
            abort(404)
        u, m = units.loc[unit_id], meta.loc[unit_id]
        human = units[(units.repo == u.repo) & (units.doc != "agent")]
        return jsonify({
            "unit": {"unit_id": unit_id, "repo": u.repo, "tool": u.tool, "set": m.set, "kind": u.kind,
                     "heading_path": u.heading_path if isinstance(u.heading_path, str) else "",
                     "text": u.text, "words": int(u.words)},
            "human": [{"unit_id": h.unit_id, "doc": h.doc, "heading_path": h.heading_path if isinstance(h.heading_path, str) else "",
                       "text": h.text, "toc": bool(h.toc)} for h in human.itertuples()],
            "prelabel": prelabels.get(unit_id),
            "label": store.latest(p).get(unit_id),  # pass 2 never sees pass-1 labels
        })

    @app.post("/api/label")
    def save():
        p = coding_pass()
        body = request.get_json(force=True)
        if body.get("unit_id") not in meta.index:
            abort(404)
        if body.get("coverage") not in codebook["coverage"]:
            abort(400, "coverage required")
        record = {"unit_id": body["unit_id"], "codebook_version": codebook["version"],
                  **{k: body.get(k) for k in LABEL_FIELDS}}
        return jsonify(store.save(p, record))

    return app


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8507)
    args = ap.parse_args()
    app = create_app()
    print(f"\n  Open this link (it stays the same across restarts):\n"
          f"    http://localhost:{args.port}/?token={app.config['TOKEN']}\n"
          f"  Re-code pass (from mid-November):\n"
          f"    http://localhost:{args.port}/?pass=2&token={app.config['TOKEN']}\n")
    app.run(host="127.0.0.1", port=args.port, debug=False)


if __name__ == "__main__":
    main()
