"""RQ1: how much agent-file knowledge is absent from README and CONTRIBUTING?

Primary estimate: the share of a repo's knowledge units that are agent-only,
averaged over repos (each repo counts once), per agent and overall. The sample
has equal numbers per agent, so the overall figure is post-stratified to each
agent's share of the eligible frame. 95% CIs: bootstrap resampling repos within
each agent. Unit-level questions (which categories are agent-only) use a
logistic GEE clustered by repo; a plain chi-square is reported only as descriptive.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

from gapstudy.analysis.data import KNOWLEDGE, TOOLS

OUTCOMES = {"agent_only": ["agent_only"], "partial": ["partial"], "shared": ["shared"],
            "any_gap": ["agent_only", "partial"]}


def repo_table(df: pd.DataFrame) -> pd.DataFrame:
    """Per repo: knowledge units and the share of each coverage outcome."""
    k = df[df.coverage.isin(KNOWLEDGE)]
    out = k.groupby(["repo", "tool"]).size().rename("units").to_frame()
    for name, labels in OUTCOMES.items():
        out[name] = k.assign(x=k.coverage.isin(labels)).groupby(["repo", "tool"]).x.mean()
    directed = df.assign(x=df.coverage.eq("agent_directed")).groupby(["repo", "tool"]).x.mean()
    out["agent_directed_share"] = directed.reindex(out.index).fillna(0)
    return out.reset_index()


def estimate(repos: pd.DataFrame, shares: dict[str, float], col: str) -> dict[str, float]:
    per_tool = repos.groupby("tool")[col].mean()
    present = [t for t in TOOLS if t in per_tool]
    w = np.array([shares.get(t, 0) for t in present])
    overall = float(np.dot(per_tool[present], w / w.sum())) if w.sum() else float("nan")
    return {"overall": overall, **per_tool.to_dict()}


def bootstrap(repos: pd.DataFrame, shares: dict[str, float], col: str, n: int, seed: int = 507) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    groups = {t: g for t, g in repos.groupby("tool")}
    draws = []
    for _ in range(n):
        sample = pd.concat([g.iloc[rng.integers(0, len(g), len(g))] for g in groups.values()])
        draws.append(estimate(sample, shares, col))
    return pd.DataFrame(draws)


def headline(df: pd.DataFrame, shares: dict[str, float], n_boot: int = 1000) -> pd.DataFrame:
    """Rows: outcome; columns: overall and per agent as 'est [lo, hi]' numbers."""
    repos = repo_table(df)
    rows = []
    for col in list(OUTCOMES) + ["agent_directed_share"]:
        est = estimate(repos, shares, col)
        boot = bootstrap(repos, shares, col, n_boot) if n_boot else None
        for scope, value in est.items():
            lo, hi = ((boot[scope].quantile(0.025), boot[scope].quantile(0.975)) if boot is not None
                      else (np.nan, np.nan))
            rows.append({"outcome": col, "scope": scope, "estimate": value, "lo": lo, "hi": hi,
                         "repos": int((repos.tool == scope).sum()) if scope != "overall" else len(repos)})
    return pd.DataFrame(rows)


def unit_level(df: pd.DataFrame) -> dict[str, float]:
    """Pooled share over all knowledge units, weighted for the per-repo cap."""
    k = df[df.coverage.isin(KNOWLEDGE)]
    w = k.weight.fillna(1)
    return {name: float(np.average(k.coverage.isin(labels), weights=w)) for name, labels in OUTCOMES.items()}


def by_category(df: pd.DataFrame, category_names: dict[str, str]) -> pd.DataFrame:
    """Agent-only share among knowledge units containing each category (weighted)."""
    k = df[df.coverage.isin(KNOWLEDGE)]
    rows = []
    for key, name in category_names.items():
        has = k[k.categories.map(lambda c: key in c)]
        if len(has):
            rows.append({"category": name, "units": len(has), "repos": has.repo.nunique(),
                         "agent_only": float(np.average(has.coverage == "agent_only", weights=has.weight.fillna(1))),
                         "any_gap": float(np.average(has.coverage.isin(["agent_only", "partial"]), weights=has.weight.fillna(1)))})
    return pd.DataFrame(rows).sort_values("agent_only", ascending=False)


def gee(df: pd.DataFrame, category_keys: list[str], min_units: int = 15) -> pd.DataFrame:
    """Logistic GEE: agent-only ~ categories + agent, clustered by repo (exchangeable).

    Categories are multi-label dummies; those with fewer than ``min_units`` units, no
    outcome variation, or no information beyond the columns already in the model
    (perfect collinearity) are dropped (reported in the 'dropped' attribute)."""
    import statsmodels.api as sm

    k = df[df.coverage.isin(KNOWLEDGE)].reset_index(drop=True)
    y = (k.coverage == "agent_only").astype(float)
    X = pd.DataFrame({"const": 1.0}, index=k.index)
    for t in TOOLS[1:]:  # CLAUDE.md is the reference agent
        X[f"agent:{t}"] = (k.tool == t).astype(float)
    dropped = []
    dummies = {key: k.categories.map(lambda c: key in c).astype(float) for key in category_keys}
    for key in sorted(dummies, key=lambda c: -dummies[c].sum()):  # most frequent first
        x = dummies[key]
        if x.sum() < min_units or y[x == 1].nunique() < 2:
            dropped.append(key)
            continue
        trial = X.assign(**{f"cat:{key}": x})
        if np.linalg.matrix_rank(trial.to_numpy()) == trial.shape[1]:
            X = trial
        else:
            dropped.append(key)
    model = sm.GEE(y, X, groups=k.repo, family=sm.families.Binomial(),
                   cov_struct=sm.cov_struct.Exchangeable(), weights=k.weight.fillna(1))
    fit = model.fit()
    ci = fit.conf_int()
    out = pd.DataFrame({"odds_ratio": np.exp(fit.params), "lo": np.exp(ci[0]), "hi": np.exp(ci[1]),
                        "p": fit.pvalues}).drop(index="const")
    out.attrs["dropped"] = dropped
    out.attrs["n_units"], out.attrs["n_repos"] = len(k), k.repo.nunique()
    return out


def chi_square_descriptive(df: pd.DataFrame) -> dict:
    """Agent x coverage at unit level. Ignores clustering, so descriptive only."""
    k = df[df.coverage.isin(KNOWLEDGE)]
    table = pd.crosstab(k.tool, k.coverage)
    chi2, p, dof, _ = chi2_contingency(table)
    return {"table": table, "chi2": chi2, "p": p, "dof": dof}
