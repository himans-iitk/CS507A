"""Phase 6 / RQ3: tune detector thresholds on the pilot repos, evaluate on the rest.

    python -m gapstudy.detector.evaluate [--boot 1000]

Reads coding/labels_v1.csv (or, before the freeze, the latest pass-1 labels,
marked provisional) and every data/processed/scores/*.csv. Agent-directed units
are excluded (they carry no project knowledge). Per matcher and score variant:
  - binary: agent-only if score < t           (t tuned for F1 on dev)
  - 3-class: agent-only < t1 <= partial < t2 <= shared   (tuned for macro-F1 on dev)
  - ROC-AUC for agent-only (threshold-free)
  - evidence retrieval: gold covering section in the top 1 / top 5
Writes analysis/phase6/detector_results.md, analysis/phase6/errors.md and
detector/config.json (the best matcher on dev, used by gapcheck).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_recall_fscore_support, roc_auc_score

from gapstudy.github_client import PROJECT_ROOT
from gapstudy.labels import CODING, LabelStore

PROCESSED = PROJECT_ROOT / "data" / "processed"
RESULTS = PROJECT_ROOT / "analysis" / "phase6"
CONFIG = PROJECT_ROOT / "detector" / "config.json"
CLASSES = ["agent_only", "partial", "shared"]
ITEM_TAUS = np.round(np.arange(0.3, 0.95, 0.05), 2)


def load_labels(coding_dir: Path = CODING) -> tuple[pd.DataFrame, bool]:
    frozen = coding_dir / "labels_v1.csv"
    if frozen.exists():
        df = pd.read_csv(frozen)
        df["evidence"] = df.evidence.map(json.loads)
        return df, False
    df = LabelStore(coding_dir).to_frame(1)
    if df.empty:
        return df, True
    queue = pd.read_csv(coding_dir / "queue.csv")
    return df.merge(queue[["unit_id", "repo", "tool", "set", "weight"]], on="unit_id"), True


def variants(scores: pd.DataFrame) -> dict[str, pd.Series]:
    """Score variants; higher = more covered."""
    out = {"unit_max": scores.unit_max, "item_mean": scores.item_mean}
    item_max = scores.item_max.map(json.loads)
    for tau in ITEM_TAUS:
        out[f"item_cov@{tau}"] = item_max.map(lambda xs: float(np.mean([x >= tau for x in xs])) if xs else 0.0)
    return out


def tune_binary(score: np.ndarray, y: np.ndarray) -> float:
    """Threshold t maximising F1 for agent-only (predict agent-only if score < t).

    Candidates are midpoints between neighbouring scores; among tied optima the middle
    one is taken, so the threshold sits in the gap rather than at its edge.
    """
    u = np.unique(score)
    cands = np.concatenate([[u[0] - 1e-6], (u[:-1] + u[1:]) / 2, [u[-1] + 1e-6]])
    f1s = np.array([f1_score(y, score < t, zero_division=0) for t in cands])
    best = np.flatnonzero(np.isclose(f1s, f1s.max()))
    return float(cands[best[len(best) // 2]])


def predict3(score: np.ndarray, t1: float, t2: float) -> np.ndarray:
    return np.where(score < t1, "agent_only", np.where(score < t2, "partial", "shared"))


def tune_three(score: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    cands = np.quantile(score, np.linspace(0, 1, 41))
    best, arg = -1.0, (cands[0], cands[-1])
    for i, t1 in enumerate(cands):
        for t2 in cands[i:]:
            f = f1_score(y, predict3(score, t1, t2), labels=CLASSES, average="macro", zero_division=0)
            if f > best:
                best, arg = f, (float(t1), float(t2))
    return arg


def binary_metrics(y: np.ndarray, pred: np.ndarray, score: np.ndarray) -> dict:
    p, r, f, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    auc = roc_auc_score(y, -score) if 0 < y.sum() < len(y) else float("nan")
    return {"precision": p, "recall": r, "f1": f, "auc": auc}


def bootstrap_ci(df: pd.DataFrame, fn, n: int, seed: int = 507) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    groups = [g for _, g in df.groupby("repo")]
    vals = []
    for _ in range(n):
        sample = pd.concat([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        vals.append(fn(sample))
    return float(np.nanquantile(vals, 0.025)), float(np.nanquantile(vals, 0.975))


def retrieval(df: pd.DataFrame) -> dict:
    has = df[df.coverage.isin(["partial", "shared"]) & df.evidence.map(bool)]
    if has.empty:
        return {"n": 0, "hit@1": float("nan"), "hit@5": float("nan")}
    ranked = has.top.map(lambda t: [u for u, _ in json.loads(t)])
    hit = lambda k: np.mean([bool(set(r[:k]) & set(e)) for r, e in zip(ranked, has.evidence)])
    return {"n": len(has), "hit@1": hit(1), "hit@5": hit(5)}


def evaluate_matcher(scores: pd.DataFrame, labels: pd.DataFrame, n_boot: int) -> tuple[dict, pd.DataFrame]:
    df = labels.merge(scores, on="unit_id")
    df = df[df.coverage.isin(CLASSES)].reset_index(drop=True)
    dev, test = df[df.set == "pilot"], df[df.set != "pilot"]
    if dev.empty or test.empty or dev.coverage.nunique() < 2:
        return {}, df
    vs = variants(df)
    y = (df.coverage == "agent_only").to_numpy()
    is_dev = (df.set == "pilot").to_numpy()

    # choose the score variant on dev only
    best = None
    for name, s in vs.items():
        s = s.to_numpy()
        t = tune_binary(s[is_dev], y[is_dev])
        f = f1_score(y[is_dev], s[is_dev] < t, zero_division=0)
        if best is None or f > best[1]:
            best = (name, f, t)
    variant, dev_f1, t = best
    s = vs[variant].to_numpy()
    t1, t2 = tune_three(s[is_dev], df.coverage.to_numpy()[is_dev])

    df["score"], df["pred_binary"], df["pred3"] = s, s < t, predict3(s, t1, t2)
    test = df[~is_dev]
    yt = (test.coverage == "agent_only").to_numpy()
    res = {
        "variant": variant, "threshold": t, "t1": t1, "t2": t2, "dev_f1": dev_f1,
        "n_dev": int(is_dev.sum()), "n_test": len(test),
        **binary_metrics(yt, test.pred_binary.to_numpy(), test.score.to_numpy()),
        "macro_f1": f1_score(test.coverage, test.pred3, labels=CLASSES, average="macro", zero_division=0),
        **{f"retrieval_{k}": v for k, v in retrieval(test).items()},
    }
    res["f1_ci"] = bootstrap_ci(test, lambda d: f1_score(d.coverage == "agent_only", d.pred_binary, zero_division=0), n_boot)
    res["auc_ci"] = bootstrap_ci(test, lambda d: roc_auc_score(d.coverage == "agent_only", -d.score)
                                 if d.coverage.eq("agent_only").nunique() == 2 else np.nan, n_boot)
    return res, df


def evaluate_llm(df: pd.DataFrame, res: dict, llm: pd.DataFrame, n_boot: int) -> list[dict]:
    """Rows for 'LLM alone' and 'matcher + LLM on borderline scores' (band tuned on dev).

    ``df`` is the per-unit frame from evaluate_matcher (score, predictions, labels)."""
    df = df.merge(llm[["unit_id", "llm_coverage"]], on="unit_id", how="left")
    df["llm_coverage"] = df.llm_coverage.fillna(df.pred3)  # unparsable answer: fall back to the matcher
    is_dev = (df.set == "pilot").to_numpy()
    y = (df.coverage == "agent_only").to_numpy()
    t, t1, t2 = res["threshold"], res["t1"], res["t2"]
    llm_bin = (df.llm_coverage == "agent_only").to_numpy()

    def combine(w):
        near_t = np.abs(df.score - t) <= w
        near_3 = (np.abs(df.score - t1) <= w) | (np.abs(df.score - t2) <= w)
        binary = np.where(near_t, llm_bin, df.pred_binary)
        three = np.where(near_3, df.llm_coverage, df.pred3)
        return binary, three, near_t

    widths = np.round(np.arange(0, 0.31, 0.02), 2)
    dev_f1 = [f1_score(y[is_dev], combine(w)[0][is_dev], zero_division=0) for w in widths]
    w = float(widths[int(np.argmax(dev_f1))])
    out = []
    for label, binary, three, share in (
        ("alone", llm_bin, df.llm_coverage.to_numpy(), np.ones(len(df), bool)),
        (f"borderline ±{w}", *combine(w)),
    ):
        d = df.assign(pred_binary=binary, pred3=three)[~is_dev]
        p, r, f, _ = precision_recall_fscore_support(d.coverage == "agent_only", d.pred_binary, average="binary", zero_division=0)
        out.append({"mode": label, "precision": p, "recall": r, "f1": f,
                    "f1_ci": bootstrap_ci(d, lambda x: f1_score(x.coverage == "agent_only", x.pred_binary, zero_division=0), n_boot),
                    "macro_f1": f1_score(d.coverage, d.pred3, labels=CLASSES, average="macro", zero_division=0),
                    "llm_share": float(np.mean(share[~is_dev]))})
    return out


def fmt_ci(ci) -> str:
    return "" if np.isnan(ci[0]) else f" [{ci[0]:.2f}, {ci[1]:.2f}]"


def errors_md(df: pd.DataFrame, units: pd.DataFrame, matcher: str, k: int = 15) -> str:
    test = df[df.set != "pilot"].merge(units[["unit_id", "heading_path", "text"]], on="unit_id")
    lines = [f"# Error analysis — {matcher} (test set)", ""]
    groups = {
        "False agent-only (labelled covered, scored low)": test[test.pred_binary & (test.coverage != "agent_only")].sort_values("score"),
        "Missed agent-only (labelled agent-only, scored high)": test[~test.pred_binary & (test.coverage == "agent_only")].sort_values("score", ascending=False),
    }
    for title, g in groups.items():
        lines += [f"## {title}: {len(g)}", ""]
        for r in g.head(k).itertuples():
            head = r.heading_path if isinstance(r.heading_path, str) else "(no heading)"
            lines += [f"- **{r.unit_id}** ({r.coverage}, score {r.score:.3f}) · {head}",
                      f"  > {r.text[:300].replace(chr(10), ' ')}"]
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--boot", type=int, default=1000)
    args = ap.parse_args()
    labels, provisional = load_labels()
    RESULTS.mkdir(parents=True, exist_ok=True)
    header = ["# RQ3 — Gap detector results", ""]
    if provisional:
        header += ["**Provisional:** computed from unfrozen pass-1 labels.", ""]
    if labels.empty:
        (RESULTS / "detector_results.md").write_text("\n".join(header + ["No labels yet."]) + "\n")
        print("No labels yet — nothing to evaluate.")
        return

    units = pd.read_csv(PROCESSED / "units.csv")
    rows, llm_rows, best = [], [], None
    for path in sorted((PROCESSED / "scores").glob("*.csv")):
        scores = pd.read_csv(path)
        name = scores.matcher.iloc[0]
        res, df = evaluate_matcher(scores, labels, args.boot)
        if not res:
            continue
        rows.append({"matcher": name, **res})
        if best is None or res["dev_f1"] > best[1]["dev_f1"]:
            best = (name, res, df)
        for llm_path in sorted((PROCESSED / "llm").glob(f"*__{path.stem}.csv")):
            llm = pd.read_csv(llm_path)
            for r in evaluate_llm(df, res, llm, args.boot):
                llm_rows.append({"matcher": f"{name} + {llm.model.iloc[0]}", **r})
    if not rows:
        print("Not enough labels on both the pilot (dev) and the other sets (test) yet.")
        return

    lines = header + [f"Dev = pilot repos (n = {rows[0]['n_dev']} units); test = reliability + main "
                      f"(n = {rows[0]['n_test']}). Agent-directed units excluded. 95% CIs: repo bootstrap.", "",
                      "| Matcher | Score (chosen on dev) | Precision | Recall | F1 agent-only | ROC-AUC | Macro-F1 (3 class) | Gold section in top 1 / top 5 |",
                      "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['matcher']} | {r['variant']} | {r['precision']:.2f} | {r['recall']:.2f} | "
                     f"{r['f1']:.2f}{fmt_ci(r['f1_ci'])} | {r['auc']:.2f}{fmt_ci(r['auc_ci'])} | {r['macro_f1']:.2f} | "
                     f"{r['retrieval_hit@1']:.2f} / {r['retrieval_hit@5']:.2f} (n = {r['retrieval_n']}) |")
    if llm_rows:
        lines += ["", "## With the LLM judge", "",
                  "The LLM sees the agent unit and the matcher's top-5 human sections. *Alone*: its answer for "
                  "every unit. *Borderline*: only for units whose score lies within the band (tuned on dev) "
                  "around the matcher's thresholds.", "",
                  "| Matcher + LLM | Mode | Units sent to LLM | Precision | Recall | F1 agent-only | Macro-F1 (3 class) |",
                  "|---|---|---|---|---|---|---|"]
        for r in llm_rows:
            lines.append(f"| {r['matcher']} | {r['mode']} | {r['llm_share']:.0%} | {r['precision']:.2f} | "
                         f"{r['recall']:.2f} | {r['f1']:.2f}{fmt_ci(r['f1_ci'])} | {r['macro_f1']:.2f} |")
    (RESULTS / "detector_results.md").write_text("\n".join(lines) + "\n")

    name, res, df = best
    (RESULTS / "errors.md").write_text(errors_md(df, units, name))
    CONFIG.parent.mkdir(exist_ok=True)
    CONFIG.write_text(json.dumps({"matcher": name, "variant": res["variant"], "threshold": res["threshold"],
                                  "t1": res["t1"], "t2": res["t2"], "provisional": provisional}, indent=2))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
