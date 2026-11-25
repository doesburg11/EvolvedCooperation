#!/usr/bin/env python3
"""Registered Stage 1 analysis (PREREGISTRATION_DRAFT.md, "What the paper claims, and the tests"; amendment A0).

Order: interim stop (if any) -> completeness -> validity -> H1, H2, H3 -> verdict. Each hypothesis uses the runs in
which its own measures are defined. Writes stage1_verdict.json next to the results.

  ~/simulation_results/altruistic_feeding/venv_050/bin/python analyze_stage1.py
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

import numpy as np
from scipy import stats

OUT = Path(os.path.expanduser("~/simulation_results/altruistic_feeding/stage1"))
LEVELS = [0.1, 0.5, 1.0]
SEEDS = list(range(10))
ALPHA = 0.01
MIN_ALIVE = 0.90
MAX_UNDEFINED = 0.10
DESIGN = {1: dict(steps=250_000, window=25_000), 0: dict(steps=100_000, window=10_000)}


def ok(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def load(feeding):
    rows, bad = [], []
    for lv in LEVELS:
        for s in SEEDS:
            p = OUT / f"result_move{lv}_seed{s}_feed{feeding}.json"
            try:
                r = json.loads(p.read_text())
            except (OSError, json.JSONDecodeError):
                bad.append((lv, s, feeding))
                continue
            d = DESIGN[feeding]
            if not (r.get("level") == lv and r.get("seed") == s and r.get("feeding") == feeding
                    and r.get("steps") == d["steps"] and r.get("window") == d["window"] and r.get("complete") is True):
                bad.append((lv, s, feeding))
                continue
            rows.append(r)
    return rows, bad


def validity(rows, keys):
    out = {}
    for lv in LEVELS:
        arm = [r for r in rows if r["level"] == lv]
        alive = sum(1 for r in arm if r.get("extinct_at") is None)
        undefined = sum(1 for r in arm if not all(ok(r.get(k)) for k in keys))
        out[str(lv)] = {"n": len(arm), "alive_to_end": alive, "undefined": undefined,
                        "valid": len(arm) == len(SEEDS) and alive >= MIN_ALIVE * len(arm)
                        and undefined <= MAX_UNDEFINED * len(arm)}
    return out


def ols_one_sided(x, y, greater=True):
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or np.ptp(x) == 0 or np.ptp(y) == 0:
        return {"slope": None, "p_one_sided": None, "n": len(x), "note": "degenerate (constant or too few points)"}
    res = stats.linregress(x, y)
    t = res.slope / res.stderr if res.stderr > 0 else float("inf") * np.sign(res.slope)
    df = len(x) - 2
    p = float(stats.t.sf(t, df) if greater else stats.t.cdf(t, df))
    return {"slope": float(res.slope), "stderr": float(res.stderr), "p_one_sided": p, "r": float(res.rvalue),
            "n": len(x)}


def seed_bootstrap(rows, xkey, yfun, n=2000, seed=0):
    """95% CI of the OLS slope, resampling whole seeds (all their levels together)."""
    rng = np.random.default_rng(seed)
    by_seed = {}
    for r in rows:
        by_seed.setdefault(r["seed"], []).append(r)
    seeds = sorted(by_seed)
    sl = []
    for _ in range(n):
        pick = rng.choice(seeds, len(seeds), replace=True)
        rr = [r for s in pick for r in by_seed[s]]
        x = np.array([r[xkey] for r in rr], float)
        y = np.array([yfun(r) for r in rr], float)
        if np.ptp(x) > 0:
            sl.append(np.polyfit(x, y, 1)[0])
    return [float(np.percentile(sl, 2.5)), float(np.percentile(sl, 97.5))] if sl else None


def spearman_one_sided(x, y, positive=True):
    if len(x) < 3 or np.ptp(np.asarray(y, float)) == 0:
        return {"rho": None, "p_one_sided": None, "n": len(x), "note": "degenerate"}
    rho, p2 = stats.spearmanr(x, y)
    p = p2 / 2 if (rho > 0) == positive else 1 - p2 / 2
    return {"rho": float(rho), "p_one_sided": float(p), "n": len(x)}


def endpoint(rows, key, lower_more=True):
    """Secondary: most hostile (0.1) against most benign (1.0), Mann-Whitney, one-sided."""
    a = [r[key] for r in rows if r["level"] == LEVELS[0] and ok(r.get(key))]
    b = [r[key] for r in rows if r["level"] == LEVELS[-1] and ok(r.get(key))]
    if not a or not b:
        return None
    alt = "greater" if lower_more else "less"
    return {"mean_hostile": float(np.mean(a)), "mean_benign": float(np.mean(b)),
            "p_one_sided": float(stats.mannwhitneyu(a, b, alternative=alt).pvalue)}


def met(res, positive_slope=True):
    if res.get("slope") is None:
        return False
    return res["p_one_sided"] < ALPHA and ((res["slope"] > 0) == positive_slope)


def main():
    verdict = {}
    ic = OUT / "interim_check.json"
    if ic.exists():
        verdict["interim_check"] = json.loads(ic.read_text())
        if verdict["interim_check"]["decision"].startswith("stop"):
            verdict["verdict"] = "not replicated (stopped at interim)"
            (OUT / "stage1_verdict.json").write_text(json.dumps(verdict, indent=1))
            print(json.dumps(verdict, indent=1))
            return
    en, bad_e = load(1)
    dis, bad_d = load(0)
    if bad_e or bad_d:
        verdict.update({"verdict": "incomplete", "missing_or_invalid": bad_e + bad_d})
        (OUT / "stage1_verdict.json").write_text(json.dumps(verdict, indent=1))
        print(json.dumps(verdict, indent=1))
        return
    mismatch = sum(r.get("feed_count_mismatch", 0) for r in en)
    val = {"enabled": validity(en, ["amount", "selectivity", "b_hat_pct"]), "disabled": validity(dis, ["ISR"]),
           "feed_count_mismatch_steps": mismatch}
    verdict["validity"] = val
    if mismatch or not all(a["valid"] for v in (val["enabled"], val["disabled"]) for a in v.values()):
        verdict["verdict"] = "not interpretable"
        (OUT / "stage1_verdict.json").write_text(json.dumps(verdict, indent=1))
        print(json.dumps(verdict, indent=1))
        return
    D = [r for r in dis if ok(r.get("ISR"))]
    Eb = [r for r in en if ok(r.get("b_hat_pct"))]
    h1_isr = spearman_one_sided([r["level"] for r in D], [r["ISR"] for r in D], positive=True)
    h1_b = spearman_one_sided([r["level"] for r in Eb], [r["b_hat_pct"] for r in Eb], positive=False)
    h1 = all(x.get("p_one_sided") is not None and x["p_one_sided"] < ALPHA for x in (h1_isr, h1_b))
    out = {}
    for name, key in (("H2", "amount"), ("H3", "selectivity")):
        E = [r for r in en if ok(r.get(key)) and ok(r.get("b_hat_pct"))]
        y = lambda r, k=key: math.log1p(r[k])   # noqa: E731
        on_b = ols_one_sided([r["b_hat_pct"] for r in E], [y(r) for r in E], greater=True)
        on_b["ci95_seed_bootstrap"] = seed_bootstrap(E, "b_hat_pct", y)
        El = [r for r in en if ok(r.get(key))]
        on_lv = ols_one_sided([r["level"] for r in El], [y(r) for r in El], greater=False)
        on_lv["ci95_seed_bootstrap"] = seed_bootstrap(El, "level", y)
        out[name] = {"on_b_hat": on_b, "on_level": on_lv, "met": met(on_b, positive_slope=True),
                     "endpoint_secondary": endpoint(en, key, lower_more=True)}
    h2, h3 = out["H2"]["met"], out["H3"]["met"]
    v = "replicated" if (h1 and h2 and h3) else ("partly" if h1 and (h2 or h3) else "not replicated")
    ES = [r for r in en if ok(r.get("selectivity")) and ok(r.get("amount"))]
    sens = {}
    for key in ("b_hat_pct_authors",):
        Ek = [r for r in en if ok(r.get(key))]
        sens[key + "_vs_level"] = spearman_one_sided([r["level"] for r in Ek], [r[key] for r in Ek], positive=False)
    sens["infant_feeds_per_capita_vs_level"] = ols_one_sided(
        [r["level"] for r in en if ok(r.get("mean_population"))],
        [math.log1p(r["feeds_to_infants"] / r["mean_population"]) for r in en if ok(r.get("mean_population"))],
        greater=False)
    per_level = {}
    for lv in LEVELS:
        d = {}
        for k in ("amount", "selectivity", "b_hat_pct", "b_hat_pct_authors", "stale_flag_share", "cap_share",
                  "run_cap_share", "mean_population"):
            vals = [r[k] for r in en if r["level"] == lv and ok(r.get(k))]
            d[k] = float(np.mean(vals)) if vals else None
        vals = [r["ISR"] for r in D if r["level"] == lv]
        d["ISR_disabled"] = float(np.mean(vals)) if vals else None
        d["run_cap_share_disabled"] = float(np.mean([r["run_cap_share"] for r in dis if r["level"] == lv
                                                      and ok(r.get("run_cap_share"))] or [float("nan")]))
        per_level[str(lv)] = d
    verdict.update({
        "H1": {"ISR_vs_level": h1_isr, "b_hat_vs_level": h1_b, "met": h1,
               "endpoint_secondary": {"ISR": endpoint(D, "ISR", lower_more=False),
                                      "b_hat": endpoint(Eb, "b_hat_pct", lower_more=True)}},
        **out, "verdict": v,
        "descriptive": {"table2_amount_on_selectivity": ols_one_sided([r["selectivity"] for r in ES],
                                                                      [r["amount"] for r in ES], greater=True),
                        "sensitivity_author_measures": sens, "per_level_means": per_level}})
    (OUT / "stage1_verdict.json").write_text(json.dumps(verdict, indent=1, default=str))
    print(json.dumps({k: verdict[k] for k in ("verdict", "H1", "H2", "H3")}, indent=1, default=str))


if __name__ == "__main__":
    main()
