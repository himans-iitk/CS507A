"""End-to-end pipeline: from the coded labels to the final results and the paper.

    python -m gapstudy.pipeline [--boot 1000] [--from STAGE] [--only STAGE ...] [--no-pdf] [--force]

Stages, in order (each one's output is the next one's input):

  check        inputs exist and agree: units, queue, codebook, complete pass-1 labels,
               detector scores for every queued agent unit, no AI draft ever shown on the
               blind reliability set
  freeze       coding/labels_v1.csv (+ sha256) from the pass-1 labels: the analysis dataset
  reliability  pass 1 vs pass 2 when a second coder's labels exist; otherwise "pending"
  detector     RQ3: tune on the pilot repos, evaluate on held-out repos (adds the LLM judge
               automatically when data/processed/llm/ has its outputs) -> detector/config.json
  analysis     RQ1, RQ2, sensitivity (incl. the docs/ check, which needs the tuned detector),
               corpus readability, label provenance
  paper        paper/numbers.tex, paper/tables/*.tex, paper/main.pdf
  summary      analysis/FINAL_RESULTS.md and analysis/pipeline_manifest.json

The annotation mode is detected, not configured: with only pass-1 labels the results are
single-annotator and the reliability stage reports "pending"; once pass-2 labels from a
different coder exist, the same command computes agreement and the paper switches to its
two-annotator text. Embedding and LLM scores are produced on a GPU by the Slurm jobs in
scripts/ and are reused here; TF-IDF scores are computed on the fly if missing.
Each stage's output goes to logs/pipeline/<stage>.log.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from gapstudy.github_client import PROJECT_ROOT

CODING = PROJECT_ROOT / "coding"
PROCESSED = PROJECT_ROOT / "data" / "processed"
ANALYSIS = PROJECT_ROOT / "analysis"
PAPER = PROJECT_ROOT / "paper"
LOGS = PROJECT_ROOT / "logs" / "pipeline"
STAGES = ("check", "freeze", "reliability", "detector", "analysis", "paper", "summary")

INPUTS = ["data/processed/units.csv", "coding/queue.csv", "coding/codebook.json", "coding/labels/pass1.jsonl",
          "coding/labels/pass2.jsonl", "coding/drafts.jsonl", "coding/coder_aliases.json"]
OUTPUTS = ["coding/labels_v1.csv", "analysis/phase5/reliability.json", "analysis/phase6/detector_results.csv",
           "detector/config.json", "analysis/phase7/results.md", "paper/numbers.tex", "paper/main.pdf",
           "analysis/FINAL_RESULTS.md"]


class StageError(RuntimeError):
    pass


def sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def run_module(stage: str, module: str, *args: str, cwd: Path = PROJECT_ROOT) -> str:
    """Run `python -m module args`, log its output, raise on failure."""
    LOGS.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run([sys.executable, "-m", module, *args], cwd=cwd, capture_output=True, text=True)
    out = proc.stdout + proc.stderr
    with open(LOGS / f"{stage}.log", "a") as log:
        log.write(f"$ python -m {module} {' '.join(args)}\n{out}\n")
    if proc.returncode:
        raise StageError(f"{module} failed (exit {proc.returncode}); last lines:\n" + "\n".join(out.splitlines()[-8:]))
    return out


# ---------------------------------------------------------------- stages

def stage_check(args) -> dict:
    from gapstudy.freeze import check
    from gapstudy.labels import LabelStore

    missing = [p for p in INPUTS[:4] if not (PROJECT_ROOT / p).exists()]
    if missing:
        raise StageError(f"missing inputs: {missing}")
    notes, warnings = [], []

    _, issues = check(CODING)
    if issues and not args.force:
        raise StageError("labels not ready to freeze: " + "; ".join(issues))
    warnings += [f"freeze issue (forced): {i}" for i in issues]

    queue = pd.read_csv(CODING / "queue.csv").drop_duplicates("unit_id")
    store = LabelStore(CODING)
    first = store.latest(1)
    rel = set(queue[queue.set == "reliability"].unit_id)
    shown = [u for u in rel if first.get(u, {}).get("draft_shown")]
    if shown:
        raise StageError(f"{len(shown)} reliability units were labelled with an AI draft visible; the blind set is compromised")

    from gapstudy.labels import aliases, annotator_type
    from gapstudy.reliability import agreement_kind
    alias = aliases(CODING)
    second = store.latest(2)
    if second:
        if any(r.get("draft_shown") for r in second.values()):
            raise StageError("pass-2 labels were made with an AI draft visible; the second coding is not blind")
        c1 = {alias.get(first[u].get("coder"), first[u].get("coder")) for u in second if u in first}
        c2 = {alias.get(r.get("coder"), r.get("coder")) for r in second.values()}
        kind = agreement_kind(c1, c2, CODING)
        mode = {"human-llm": "human annotator + LLM second annotator", "inter-rater": "two human annotators",
                "intra-rater": "one annotator, re-coded"}[kind]
        notes.append(f"pass 2: {len(second)} / {len(rel)} reliability units by {', '.join(sorted(c2))} ({mode})")
        unknown = sorted(c for c in c1 | c2 if annotator_type(c, CODING) == "unknown")
        if unknown:
            warnings.append(f"annotators not in coding/annotators.json (type unknown): {unknown}")
    else:
        mode = "single annotator"
        notes.append("pass 2: none yet; results are single-annotator and reliability is pending")

    scores_dir = PROCESSED / "scores"
    if not (scores_dir / "tfidf.csv").exists():
        run_module("check", "gapstudy.detector.score", "--matcher", "tfidf")
        notes.append("computed TF-IDF scores")
    agent_units = set(queue.unit_id)
    for path in sorted(scores_dir.glob("*.csv")):
        have = set(pd.read_csv(path, usecols=["unit_id"]).unit_id)
        gap = len(agent_units - have)
        (warnings if gap else notes).append(f"scores {path.stem}: " + (f"{gap} queued units missing" if gap else "complete"))
    llm = sorted((PROCESSED / "llm").glob("*.csv")) if (PROCESSED / "llm").exists() else []
    notes.append(f"LLM judge outputs: {len(llm)} file(s)" + ("" if llm else " -> RQ3 runs without the LLM stage"))
    return {"mode": mode, "notes": notes, "warnings": warnings}


def stage_freeze(args) -> dict:
    out = run_module("freeze", "gapstudy.freeze", *(["--force"] if args.force else []))
    return {"notes": [line.strip() for line in out.splitlines() if "froze" in line]}


def stage_reliability(args) -> dict:
    run_module("reliability", "gapstudy.reliability", "--boot", str(args.boot))
    status = json.loads((ANALYSIS / "phase5" / "reliability.json").read_text())
    if status["status"] == "pending":
        return {"notes": ["pending: no second-coder labels"], "reliability": status}
    return {"notes": [f"{status['kind']}: κ = {status['coverage_kappa']:.2f} on {status['units']} units"],
            "reliability": status}


def stage_detector(args) -> dict:
    run_module("detector", "gapstudy.detector.evaluate", "--boot", str(args.boot))
    r = pd.read_csv(ANALYSIS / "phase6" / "detector_results.csv")
    best = r.sort_values("dev_f1", ascending=False).iloc[0]
    return {"notes": [f"best on dev: {best.matcher} ({best.variant}); test F1 {best.f1:.2f}, AUC {best.auc:.2f}"]}


def stage_analysis(args) -> dict:
    run_module("analysis", "gapstudy.analysis.report", "--boot", str(args.boot))
    h = pd.read_csv(ANALYSIS / "phase7" / "rq1_headline.csv").set_index(["outcome", "scope"])
    return {"notes": [f"agent-only {h.loc[('agent_only', 'overall'), 'estimate']:.1%}, "
                      f"agent-only or partial {h.loc[('any_gap', 'overall'), 'estimate']:.1%} (post-stratified)"]}


def stage_paper(args) -> dict:
    notes = [run_module("paper", "gapstudy.paper_numbers").strip().splitlines()[-1]]
    notes.append(run_module("paper", "gapstudy.paper_tables").strip().splitlines()[-1])
    if not args.no_pdf:
        proc = subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "-silent", "main.tex"],
                              cwd=PAPER, capture_output=True, text=True)
        (LOGS / "paper.log").open("a").write(proc.stdout + proc.stderr)
        if proc.returncode:
            raise StageError("LaTeX build failed; see paper/main.log")
        tbd = (PAPER / "main.log").read_text(errors="ignore").count("undefined")
        notes.append("paper/main.pdf built" + (f" ({tbd} undefined references)" if tbd else ""))
    return {"notes": notes}


def stage_summary(args, results: dict) -> dict:
    from gapstudy.summary import write_final_results
    path = write_final_results(results.get("check", {}).get("mode", "unknown"))
    manifest = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "git_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT, capture_output=True,
                                     text=True).stdout.strip(),
        "git_dirty": bool(subprocess.run(["git", "status", "--porcelain"], cwd=PROJECT_ROOT, capture_output=True,
                                         text=True).stdout.strip()),
        "bootstrap_draws": args.boot,
        "stages": {k: {kk: vv for kk, vv in v.items() if kk != "reliability"} for k, v in results.items()},
        "inputs": {p: sha256(PROJECT_ROOT / p) for p in INPUTS}
                  | {f"data/processed/scores/{p.name}": sha256(p) for p in sorted((PROCESSED / "scores").glob("*.csv"))},
        "outputs": {p: sha256(PROJECT_ROOT / p) for p in OUTPUTS},
    }
    (ANALYSIS / "pipeline_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    return {"notes": [f"wrote {path.relative_to(PROJECT_ROOT)} and analysis/pipeline_manifest.json"]}


RUNNERS = {"check": stage_check, "freeze": stage_freeze, "reliability": stage_reliability,
           "detector": stage_detector, "analysis": stage_analysis, "paper": stage_paper}


def run(args) -> dict:
    stages = list(args.only) if args.only else list(STAGES[STAGES.index(args.from_stage):])
    if "check" not in stages:
        stages.insert(0, "check")  # never run on unchecked inputs
    results: dict[str, dict] = {}
    for stage in STAGES:
        if stage not in stages:
            continue
        t0 = time.time()
        print(f"▶ {stage}", flush=True)
        try:
            res = stage_summary(args, results) if stage == "summary" else RUNNERS[stage](args)
        except StageError as e:
            print(f"✗ {stage}: {e}", flush=True)
            results[stage] = {"status": "failed", "error": str(e), "seconds": round(time.time() - t0, 1)}
            raise SystemExit(1)
        res |= {"status": "ok", "seconds": round(time.time() - t0, 1)}
        results[stage] = res
        for n in res.get("notes", []):
            print(f"   {n}")
        for w in res.get("warnings", []):
            print(f"   ⚠ {w}")
        print(f"✓ {stage} ({res['seconds']}s)", flush=True)
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--boot", type=int, default=1000, help="bootstrap draws for all confidence intervals")
    ap.add_argument("--from", dest="from_stage", choices=STAGES, default="check")
    ap.add_argument("--only", nargs="+", choices=STAGES)
    ap.add_argument("--no-pdf", action="store_true", help="skip the LaTeX build")
    ap.add_argument("--force", action="store_true", help="freeze despite label issues (say so in the paper)")
    run(ap.parse_args())


if __name__ == "__main__":
    main()
