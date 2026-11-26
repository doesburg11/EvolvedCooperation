#!/usr/bin/env python3
"""Self-routing diagnostic for the shared Moran engine.

Pre-registration: moran_models/nowak_mechanisms/SELF_ROUTING_DIAGNOSTIC.md

Reruns the 2026-05-08 emergence baseline comparison with two arms per seed:
  self   -- routing as in the original (producer included in its own routing neighbourhood)
  noself -- producer removed from its own routing neighbourhood only; replacement neighbourhood unchanged

Set MODE below ("check": Stage 0 checks only; "run": Stage 0 checks, then the registered run), then run from repo root:
  ./.conda/bin/python -m moran_models.interaction_kernel.utils.self_routing_diagnostic
"""

from __future__ import annotations

import csv
import sys
import time
from datetime import datetime
from pathlib import Path
from statistics import fmean
from typing import Any

import numpy as np

from moran_models.nowak_mechanisms.group_selection.config.group_selection_config import config as group_cfg
from moran_models.nowak_mechanisms.group_selection.group_selection_model import GroupSelectionModel
from moran_models.nowak_mechanisms.indirect_reciprocity.config.indirect_reciprocity_config import config as indirect_cfg
from moran_models.nowak_mechanisms.indirect_reciprocity.indirect_reciprocity_model import IndirectReciprocityModel
from moran_models.nowak_mechanisms.kin_selection.config.kin_selection_config import config as kin_cfg
from moran_models.nowak_mechanisms.kin_selection.kin_selection_model import KinSelectionModel
from moran_models.nowak_mechanisms.network_reciprocity.config.network_reciprocity_config import (
    config as network_cfg,
)
from moran_models.nowak_mechanisms.network_reciprocity.network_reciprocity_model import NetworkReciprocityModel

MODELS: dict[str, tuple[dict[str, Any], type]] = {
    "indirect_reciprocity": (indirect_cfg, IndirectReciprocityModel),
    "network_reciprocity": (network_cfg, NetworkReciprocityModel),
    "group_selection": (group_cfg, GroupSelectionModel),
    "kin_selection": (kin_cfg, KinSelectionModel),
}
ARMS = ("self", "noself")

MODE = "run"  # "check": Stage 0 checks only; "run": Stage 0 checks, then the registered run

BENEFIT_SCALES = [0.8, 1.0, 1.2]
COST_SCALES = [0.10, 0.20, 0.30]
MAIN_CELLS = [(b, c) for b in BENEFIT_SCALES for c in COST_SCALES]
HIGH_CELLS = [(1.6, 0.20), (2.4, 0.20), (3.2, 0.20), (4.8, 0.20)]  # descriptive
SEEDS = list(range(8))
SIMULATION_STEPS = 250

SUCCESS_FINAL_TRAIT = 0.50
SUCCESS_MIN_GAIN = 0.05
CELL_OF_INTEREST_GAIN = 0.05
VERDICT_SHARE = 0.75

# Fixed in the pre-registration from the stored 2026-05-08 summary (original mean gain >= +0.05).
CELLS_OF_INTEREST: dict[str, list[tuple[float, float]]] = {
    "indirect_reciprocity": list(MAIN_CELLS),
    "network_reciprocity": [(0.8, 0.1), (1.0, 0.1), (1.2, 0.1), (1.2, 0.2)],
    "group_selection": [(0.8, 0.1), (1.0, 0.1), (1.2, 0.1), (1.2, 0.2)],
    "kin_selection": [cell for cell in MAIN_CELLS if cell != (0.8, 0.3)],
}

DATA_DIR = Path("moran_models/interaction_kernel/data")
REFERENCE_REPLICATES = DATA_DIR / "compare_emergence_baselines_20260508_134242_replicates.csv"
REFERENCE_SUMMARY = DATA_DIR / "compare_emergence_baselines_20260508_134242_summary.csv"


def make_cfg(base_cfg: dict[str, Any], benefit: float, cost: float, seed: int, steps: int) -> dict[str, Any]:
    """Same overrides as compare_emergence_baselines._run_single."""
    cfg = dict(base_cfg)
    cfg.update(
        {
            "B_plus_scale": float(benefit),
            "C_scale": float(cost),
            "random_seed": int(seed),
            "simulation_steps": int(steps),
            "summary_interval_steps": int(steps),
            "write_log": False,
        }
    )
    return cfg


def build_model(mechanism: str, benefit: float, cost: float, seed: int, arm: str, steps: int = SIMULATION_STEPS):
    """Build a wrapper model; in the noself arm remove self from the routing mask only."""
    if arm not in ARMS:
        raise ValueError(f"unknown arm: {arm}")
    base_cfg, model_cls = MODELS[mechanism]
    model = model_cls(make_cfg(base_cfg, benefit, cost, seed, steps))
    if arm == "noself":
        routing_mask = model.neighbor_mask.copy()
        np.fill_diagonal(routing_mask, False)
        model.neighbor_mask = routing_mask  # used for kernels only; replacement uses model.neighbor_indices
    return model


def positive_kernel(model) -> np.ndarray:
    """Positive kernel for the model's current state, without touching its state."""
    extra = {key: values.copy() for key, values in model.extra_state.items()}
    return model.mechanism.build_positive_kernel(model.neighbor_mask, model.lineage.copy(), extra, model.cfg)


def mean_self_share(model) -> float:
    return float(np.mean(np.diag(positive_kernel(model))))


def run_single(mechanism: str, benefit: float, cost: float, seed: int, arm: str) -> dict[str, Any]:
    model = build_model(mechanism, benefit, cost, seed, arm)
    share_start = mean_self_share(model)
    payload = model.run()
    share_end = mean_self_share(model)
    initial = float(payload["history"][0]["mean_trait"])
    final = float(payload["final_mean_trait"])
    gain = final - initial
    return {
        "mechanism": mechanism,
        "arm": arm,
        "benefit_scale": float(benefit),
        "cost_scale": float(cost),
        "seed": int(seed),
        "initial_mean_trait": initial,
        "final_mean_trait": final,
        "trait_gain": gain,
        "emergence_success": int(final >= SUCCESS_FINAL_TRAIT and gain >= SUCCESS_MIN_GAIN),
        "self_share_start": share_start,
        "self_share_end": share_end,
    }


# --------------------------------------------------------------------------------------------- checks


def _reference_final(mechanism: str, benefit: float, cost: float, seed: int) -> float:
    with REFERENCE_REPLICATES.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if (
                row["mechanism"] == mechanism
                and float(row["benefit_scale"]) == benefit
                and float(row["cost_scale"]) == cost
                and int(row["seed"]) == seed
            ):
                return float(row["final_mean_trait"])
    raise KeyError((mechanism, benefit, cost, seed))


def _cells_of_interest_from_reference() -> dict[str, list[tuple[float, float]]]:
    cells: dict[str, list[tuple[float, float]]] = {m: [] for m in MODELS}
    with REFERENCE_SUMMARY.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if float(row["mean_trait_gain"]) >= CELL_OF_INTEREST_GAIN:
                cells[row["mechanism"]].append((float(row["benefit_scale"]), float(row["cost_scale"])))
    return cells


def run_checks() -> bool:
    results: list[tuple[str, bool, str]] = []

    from_reference = _cells_of_interest_from_reference()
    same = all(sorted(from_reference[m]) == sorted(CELLS_OF_INTEREST[m]) for m in MODELS)
    results.append(("cells of interest match the stored summary", same, ""))

    for mechanism in MODELS:
        m_self = build_model(mechanism, 1.0, 0.2, 0, "self")
        m_noself = build_model(mechanism, 1.0, 0.2, 0, "noself")

        diag_off = not np.any(np.diag(m_noself.neighbor_mask))
        off_diag = ~np.eye(m_self.neighbor_mask.shape[0], dtype=bool)
        off_equal = bool(np.array_equal(m_self.neighbor_mask[off_diag], m_noself.neighbor_mask[off_diag]))
        repl_equal = all(np.array_equal(a, b) for a, b in zip(m_self.neighbor_indices, m_noself.neighbor_indices))
        results.append((f"{mechanism}: 1 routing mask (diagonal off, rest equal, replacement equal)",
                        diag_off and off_equal and repl_equal, ""))

        kernel = positive_kernel(m_noself)
        diag_zero = float(np.max(np.abs(np.diag(kernel)))) == 0.0
        rows_one = float(np.max(np.abs(kernel.sum(axis=1) - 1.0))) <= 1e-12
        results.append((f"{mechanism}: 2 noself kernel (diagonal 0, rows sum to 1)", diag_zero and rows_one,
                        f"self share in self arm at start = {mean_self_share(m_self):.4f}"))

        t0 = time.process_time()
        final = float(m_self.run()["final_mean_trait"])
        cpu = time.process_time() - t0
        ref = _reference_final(mechanism, 1.0, 0.2, 0)
        results.append((f"{mechanism}: 3 self arm reproduces 2026-05-08 (B=1.0, C=0.2, seed 0)",
                        abs(final - ref) <= 1e-12, f"|diff| = {abs(final - ref):.2e}, {cpu:.1f} s CPU per run"))

        # Check 4 (amendment A1): the manipulation acts, and only on routing.
        f_self = build_model(mechanism, 1.0, 0.2, 0, "self")
        f_noself = build_model(mechanism, 1.0, 0.2, 0, "noself")
        k_self = positive_kernel(f_self)
        k_expected = k_self.copy()
        np.fill_diagonal(k_expected, 0.0)
        k_expected = k_expected / k_expected.sum(axis=1, keepdims=True)
        kernel_ok = bool(np.allclose(positive_kernel(f_noself), k_expected, rtol=0.0, atol=1e-12))
        same_start = bool(np.array_equal(f_self.h, f_noself.h) and np.array_equal(f_self.lineage, f_noself.lineage))
        cost_ok = bool(np.array_equal(
            f_self.mechanism.compute_private_cost(f_self.h, f_self.extra_state, f_self.cfg),
            f_noself.mechanism.compute_private_cost(f_noself.h, f_noself.extra_state, f_noself.cfg),
        ))
        traj = {}
        for arm, model in (("self", f_self), ("noself", f_noself)):
            traj[arm] = [model.step()["mean_trait"] for _ in range(20)]
        differs = traj["self"] != traj["noself"]
        results.append((f"{mechanism}: 4 noself kernel = self kernel without diagonal, renormalised; same start and "
                        "cost; trajectories differ at B=1, C=0.2", kernel_ok and same_start and cost_ok and differs,
                        f"mean trait after 20 steps: self {traj['self'][-1]:.3f}, noself {traj['noself'][-1]:.3f}"))

    ok = all(passed for _, passed, _ in results)
    for name, passed, note in results:
        print(f"[{'PASS' if passed else 'FAIL'}] {name}" + (f"  ({note})" if note else ""))
    print("Stage 0:", "PASSED" if ok else "FAILED -> stop and report; no registered run")
    return ok


# --------------------------------------------------------------------------------------------- analysis


def summarise(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple, list[dict[str, Any]]] = {}
    for row in rows:
        by_key.setdefault((row["mechanism"], row["arm"], row["benefit_scale"], row["cost_scale"]), []).append(row)
    out = []
    for mechanism in MODELS:
        for benefit, cost in MAIN_CELLS + HIGH_CELLS:
            cell = {arm: sorted(by_key.get((mechanism, arm, benefit, cost), []), key=lambda r: r["seed"])
                    for arm in ARMS}
            for arm in ARMS:
                if [r["seed"] for r in cell[arm]] != SEEDS:
                    raise RuntimeError(f"incomplete cell {mechanism} B={benefit} C={cost} arm={arm}")
            paired = [n["final_mean_trait"] - s["final_mean_trait"] for s, n in zip(cell["self"], cell["noself"])]
            entry = {"mechanism": mechanism, "benefit_scale": benefit, "cost_scale": cost,
                     "cell_type": "main" if (benefit, cost) in MAIN_CELLS else "high_descriptive",
                     "of_interest": int((benefit, cost) in CELLS_OF_INTEREST[mechanism])}
            for arm in ARMS:
                rs = cell[arm]
                entry[f"{arm}_mean_initial"] = fmean(r["initial_mean_trait"] for r in rs)
                entry[f"{arm}_mean_final"] = fmean(r["final_mean_trait"] for r in rs)
                entry[f"{arm}_mean_gain"] = fmean(r["trait_gain"] for r in rs)
                entry[f"{arm}_successes"] = sum(r["emergence_success"] for r in rs)
            entry["self_share_start_self_arm"] = fmean(r["self_share_start"] for r in cell["self"])
            entry["self_share_end_self_arm"] = fmean(r["self_share_end"] for r in cell["self"])
            entry["paired_mean_diff_noself_minus_self"] = fmean(paired)
            entry["seeds_noself_lower"] = sum(d < 0 for d in paired)
            out.append(entry)
    return out


def classify(summary: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    verdicts = {}
    for mechanism in MODELS:
        cells = [e for e in summary if e["mechanism"] == mechanism and e["of_interest"]]
        n = len(cells)
        if n != len(CELLS_OF_INTEREST[mechanism]):
            raise RuntimeError(f"{mechanism}: {n} cells of interest found, expected {len(CELLS_OF_INTEREST[mechanism])}")
        half = len(SEEDS) // 2
        dependent = sum(e["noself_successes"] == 0 and e["noself_mean_gain"] < CELL_OF_INTEREST_GAIN for e in cells)
        surviving = sum(e["noself_successes"] >= half and e["noself_mean_gain"] >= CELL_OF_INTEREST_GAIN for e in cells)
        if n and dependent >= VERDICT_SHARE * n:
            verdict = "self-benefit-dependent"
        elif n and surviving >= VERDICT_SHARE * n:
            verdict = "survives without self-routing"
        else:
            verdict = "mixed"
        verdicts[mechanism] = {"cells_of_interest": n, "dependent": dependent, "surviving": surviving,
                               "mixed": n - dependent - surviving, "verdict": verdict}
    return verdicts


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def run_registered() -> None:
    if not run_checks():
        sys.exit(1)
    jobs = [(m, b, c, s, a) for m in MODELS for (b, c) in MAIN_CELLS + HIGH_CELLS for s in SEEDS for a in ARMS]
    rows = []
    t0 = time.time()
    for i, (mechanism, benefit, cost, seed, arm) in enumerate(jobs, 1):
        rows.append(run_single(mechanism, benefit, cost, seed, arm))
        if i % 50 == 0 or i == len(jobs):
            print(f"[self_routing_diagnostic] {i}/{len(jobs)} runs, {time.time() - t0:.0f} s")

    # Amendment A1: every main-cell self-arm replicate must reproduce the stored 2026-05-08 run.
    reference = {}
    with REFERENCE_REPLICATES.open(encoding="utf-8") as f:
        for ref in csv.DictReader(f):
            key = (ref["mechanism"], float(ref["benefit_scale"]), float(ref["cost_scale"]), int(ref["seed"]))
            reference[key] = float(ref["final_mean_trait"])
    diffs = [abs(r["final_mean_trait"] - reference[(r["mechanism"], r["benefit_scale"], r["cost_scale"], r["seed"])])
             for r in rows if r["arm"] == "self" and (r["benefit_scale"], r["cost_scale"]) in MAIN_CELLS]
    max_diff = max(diffs)
    print(f"[self_routing_diagnostic] self arm vs 2026-05-08: {len(diffs)} replicates, max |diff| = {max_diff:.2e}")
    if len(diffs) != len(MODELS) * len(MAIN_CELLS) * len(SEEDS) or max_diff > 1e-12:
        raise RuntimeError("self arm does not reproduce the stored 2026-05-08 replicates; no verdict")

    summary = summarise(rows)
    verdicts = classify(summary)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    rep_path = DATA_DIR / f"self_routing_diagnostic_{stamp}_replicates.csv"
    sum_path = DATA_DIR / f"self_routing_diagnostic_{stamp}_summary.csv"
    txt_path = DATA_DIR / f"self_routing_diagnostic_{stamp}_verdicts.txt"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _write_csv(rep_path, rows)
    _write_csv(sum_path, summary)
    with txt_path.open("w", encoding="utf-8") as f:
        f.write("Self-routing diagnostic (pre-registration SELF_ROUTING_DIAGNOSTIC.md)\n")
        f.write(f"replicates: {rep_path}\nsummary: {sum_path}\nwall time: {time.time() - t0:.0f} s\n")
        f.write(f"self arm vs 2026-05-08: {len(diffs)} replicates, max |diff| = {max_diff:.2e}\n\n")
        for mechanism, v in verdicts.items():
            f.write(f"{mechanism:>22s}: {v['verdict']}  (cells of interest {v['cells_of_interest']}: "
                    f"dependent {v['dependent']}, surviving {v['surviving']}, mixed {v['mixed']})\n")
    print(txt_path.read_text(encoding="utf-8"))


def main() -> None:
    if MODE == "check":
        sys.exit(0 if run_checks() else 1)
    if MODE == "run":
        run_registered()
        return
    raise ValueError(f"MODE must be 'check' or 'run', got {MODE!r}")


if __name__ == "__main__":
    main()
