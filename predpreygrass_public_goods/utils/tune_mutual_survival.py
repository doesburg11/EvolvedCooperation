#!/usr/bin/env python3
"""
Automatic mutual-survival tuner for the predator-prey cooperation model.

No CLI is used. Edit the configuration block below, then run the script.

Goal:
- search a parameter grid around the current defaults,
- rank candidates by predator-prey coexistence across multiple seeds,
- save a full CSV plus a short top-results summary,
- checkpoint progress after each batch so long searches can resume.
"""

from __future__ import annotations

import contextlib
import csv
import io
import itertools
import math
import os
import statistics as stats
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Dict, Iterable, List


if __package__:
    from .. import emerging_cooperation as eco
else:
    repo_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    import predpreygrass_public_goods.emerging_cooperation as eco


Scalar = bool | int | float


# ============================================================
# TUNER CONFIG (edit here)
# ============================================================

param_grid: Dict[str, List[Scalar]] = {
    "pred_init": [60, 65, 70],
    "prey_init": [550, 575],
    "pred_repro_prob": [0.04, 0.045],
    "prey_repro_prob": [0.070, 0.072],
    "p0": [0.54, 0.56],
    "birth_thresh_pred": [4.8],
    "metab_pred": [0.055],
    "pred_energy_init": [1.4],
    "prey_birth_split": [0.40, 0.42],
    "prey_move_prob": [0.30],
}

steps = 1000
seed_start = 0
seed_count = 8
workers = 8
batch_size = 12
resume = True
run_until_complete = True
max_resume_passes = 12

out_dir = "./predpreygrass_public_goods/images"
name_prefix = "mutual_survival_tuning"
top_k = 12
ranking_mode = "prey_collapse_penalty"


@dataclass(frozen=True)
class TuningConfig:
    param_grid: Dict[str, List[Scalar]]
    steps: int
    seed_start: int
    seed_count: int
    workers: int
    batch_size: int
    resume: bool
    out_dir: str
    name_prefix: str
    top_k: int
    ranking_mode: str
    run_until_complete: bool
    max_resume_passes: int


@dataclass(frozen=True)
class CandidateResult:
    params: Dict[str, Scalar]
    success_count: int
    success_rate: float
    prey_extinction_count: int
    pred_extinction_count: int
    mean_final_preds: float
    mean_final_preys: float
    mean_min_preds: float
    mean_min_preys: float
    mean_extinction_step: float
    mean_final_preds_success: float
    mean_final_preys_success: float
    mean_group_hunt_effort_success: float


def load_config() -> TuningConfig:
    return TuningConfig(
        param_grid=param_grid,
        steps=steps,
        seed_start=seed_start,
        seed_count=seed_count,
        workers=workers,
        batch_size=batch_size,
        resume=resume,
        out_dir=out_dir,
        name_prefix=name_prefix,
        top_k=top_k,
        ranking_mode=ranking_mode,
        run_until_complete=run_until_complete,
        max_resume_passes=max_resume_passes,
    )


def validate_ranking_mode(ranking_mode: str) -> None:
    if ranking_mode not in {"coexistence", "prey_collapse_penalty"}:
        raise ValueError(
            "ranking_mode must be 'coexistence' or 'prey_collapse_penalty'"
        )


def validate_param_grid(param_grid: Dict[str, List[Scalar]]) -> None:
    if not param_grid:
        raise ValueError("param_grid must not be empty")

    for param_name, values in param_grid.items():
        if param_name not in eco.CFG:
            raise ValueError(f"Unknown parameter '{param_name}' in emerging_cooperation.py")
        if not values:
            raise ValueError(f"Parameter '{param_name}' has an empty candidate list")
        current_value = eco.CFG[param_name]
        if not isinstance(current_value, (bool, int, float)):
            raise TypeError(
                f"Parameter '{param_name}' has unsupported type {type(current_value).__name__}; "
                "supported types are bool, int, and float."
            )


def parameter_product(param_grid: Dict[str, List[Scalar]]) -> Iterable[Dict[str, Scalar]]:
    names = list(param_grid.keys())
    for values in itertools.product(*(param_grid[name] for name in names)):
        yield dict(zip(names, values))


def total_candidate_count(cfg: TuningConfig) -> int:
    total = 1
    for values in cfg.param_grid.values():
        total *= len(values)
    return total


def mean_or_nan(values: List[float]) -> float:
    return stats.mean(values) if values else float("nan")


def parse_float(text: str) -> float:
    return float(text) if text.lower() != "nan" else float("nan")


def cast_scalar_from_string(reference: Scalar, raw: str) -> Scalar:
    if isinstance(reference, bool):
        return bool(int(raw))
    if isinstance(reference, int) and not isinstance(reference, bool):
        return int(float(raw))
    return float(raw)


def normalize_checkpoint_row(row: Dict[str, str]) -> Dict[str, str]:
    return {
        key.strip().lower(): value
        for key, value in row.items()
        if key is not None
    }


def require_checkpoint_field(row: Dict[str, str], field_name: str) -> str:
    if field_name not in row:
        raise KeyError(
            f"Checkpoint is missing required field '{field_name}'. "
            f"Available fields: {sorted(row)}"
        )
    return row[field_name]


def chunked(values: List[Dict[str, Scalar]], batch_size: int) -> Iterable[List[Dict[str, Scalar]]]:
    for start in range(0, len(values), batch_size):
        yield values[start:start + batch_size]


def candidate_key(params: Dict[str, Scalar], param_names: List[str]) -> tuple[Scalar, ...]:
    return tuple(params[name] for name in param_names)


def candidate_sort_key(result: CandidateResult, ranking_mode: str) -> tuple[float, ...]:
    validate_ranking_mode(ranking_mode)
    success_prey = result.mean_final_preys_success
    if math.isnan(success_prey):
        success_prey = -1.0
    extinction_step = result.mean_extinction_step
    if math.isnan(extinction_step):
        extinction_step = float("inf")
    evaluated_runs = max(
        1,
        result.success_count
        + result.prey_extinction_count
        + result.pred_extinction_count,
    )
    prey_survival_rate = 1.0 - result.prey_extinction_count / evaluated_runs
    mean_final_prey = result.mean_final_preys
    if math.isnan(mean_final_prey):
        mean_final_prey = -1.0
    if ranking_mode == "coexistence":
        return (
            result.success_rate,
            result.mean_min_preys,
            success_prey,
            extinction_step,
        )
    if ranking_mode == "prey_collapse_penalty":
        return (
            result.success_rate,
            prey_survival_rate,
            result.mean_min_preys,
            mean_final_prey,
            success_prey,
            extinction_step,
        )
    raise ValueError(f"Unknown ranking mode '{ranking_mode}'")


def checkpoint_paths(cfg: TuningConfig) -> tuple[str, str]:
    stem = os.path.join(
        cfg.out_dir,
        f"{cfg.name_prefix}_{cfg.ranking_mode}_steps{cfg.steps}_checkpoint",
    )
    return stem + ".csv", stem + "_top.txt"


def legacy_checkpoint_paths(cfg: TuningConfig) -> tuple[str, str]:
    stem = os.path.join(cfg.out_dir, f"{cfg.name_prefix}_{cfg.ranking_mode}_checkpoint")
    return stem + ".csv", stem + "_top.txt"


def make_output_paths(cfg: TuningConfig) -> tuple[str, str]:
    os.makedirs(cfg.out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%h%M%S")
    stem = f"{cfg.name_prefix}_{cfg.ranking_mode}_steps{cfg.steps}_{stamp}"
    return (
        os.path.join(cfg.out_dir, f"{stem}.csv"),
        os.path.join(cfg.out_dir, f"{stem}_top.txt"),
    )


def write_text_atomic(outfile: str, text: str) -> None:
    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)
    temp_out = outfile + ".tmp"
    with open(temp_out, "w", encoding="utf-8") as file_obj:
        file_obj.write(text)
    os.replace(temp_out, outfile)


def save_csv(results: List[CandidateResult], outfile: str, param_names: List[str]) -> None:
    os.makedirs(os.path.dirname(outfile) or ".", exist_ok=True)
    temp_out = outfile + ".tmp"
    with open(temp_out, "w", newline="", encoding="utf-8") as file_obj:
        writer = csv.writer(file_obj)
        writer.writerow(
            [
                *param_names,
                "success_count",
                "success_rate",
                "prey_extinction_count",
                "pred_extinction_count",
                "mean_final_preds",
                "mean_final_preys",
                "mean_min_preds",
                "mean_min_preys",
                "mean_extinction_step",
                "mean_final_preds_success",
                "mean_final_preys_success",
                "mean_group_hunt_effort_success",
            ]
        )
        for result in results:
            writer.writerow(
                [
                    *(result.params[name] for name in param_names),
                    result.success_count,
                    f"{result.success_rate:.4f}",
                    result.prey_extinction_count,
                    result.pred_extinction_count,
                    f"{result.mean_final_preds:.4f}",
                    f"{result.mean_final_preys:.4f}",
                    f"{result.mean_min_preds:.4f}",
                    f"{result.mean_min_preys:.4f}",
                    "nan" if math.isnan(result.mean_extinction_step) else f"{result.mean_extinction_step:.4f}",
                    "nan" if math.isnan(result.mean_final_preds_success) else f"{result.mean_final_preds_success:.4f}",
                    "nan" if math.isnan(result.mean_final_preys_success) else f"{result.mean_final_preys_success:.4f}",
                    (
                        "nan"
                        if math.isnan(result.mean_group_hunt_effort_success)
                        else f"{result.mean_group_hunt_effort_success:.4f}"
                    ),
                ]
            )
    os.replace(temp_out, outfile)
    print(f"Saved CSV to {outfile}")


def save_top_summary(
    results: List[CandidateResult],
    outfile: str,
    cfg: TuningConfig,
    title: str,
    completed_candidates: int,
    total_candidates: int,
) -> None:
    top_results = results[: cfg.top_k]
    lines: List[str] = []
    lines.append(f"{title}\n")
    lines.append(f"completed_candidates={completed_candidates}/{total_candidates}\n")
    lines.append(f"steps={cfg.steps}\n")
    lines.append(f"seed_start={cfg.seed_start}\n")
    lines.append(f"seed_count={cfg.seed_count}\n")
    lines.append(f"workers={cfg.workers}\n")
    lines.append(f"batch_size={cfg.batch_size}\n")
    lines.append(f"resume={cfg.resume}\n")
    lines.append(f"ranking_mode={cfg.ranking_mode}\n")
    lines.append(f"ranked_candidates={len(results)}\n\n")

    for rank, result in enumerate(top_results, start=1):
        lines.append(f"#{rank}\n")
        lines.append(f"params={result.params}\n")
        lines.append(f"success={result.success_count}/{cfg.seed_count} ({result.success_rate:.3f})\n")
        lines.append(
            f"prey_extinction_count={result.prey_extinction_count} "
            f"pred_extinction_count={result.pred_extinction_count}\n"
        )
        lines.append(
            f"mean_final_preds={result.mean_final_preds:.2f} "
            f"mean_final_preys={result.mean_final_preys:.2f}\n"
        )
        lines.append(
            f"mean_min_preds={result.mean_min_preds:.2f} "
            f"mean_min_preys={result.mean_min_preys:.2f}\n"
        )
        lines.append(
            "mean_extinction_step="
            + ("nan" if math.isnan(result.mean_extinction_step) else f"{result.mean_extinction_step:.2f}")
            + "\n"
        )
        lines.append(
            "mean_final_success="
            + (
                "(nan, nan)"
                if math.isnan(result.mean_final_preds_success) or math.isnan(result.mean_final_preys_success)
                else f"({result.mean_final_preds_success:.2f}, {result.mean_final_preys_success:.2f})"
            )
            + "\n"
        )
        lines.append(
            "mean_group_hunt_effort_success="
            + (
                "nan"
                if math.isnan(result.mean_group_hunt_effort_success)
                else f"{result.mean_group_hunt_effort_success:.3f}"
            )
            + "\n\n"
        )

    write_text_atomic(outfile, "".join(lines))
    print(f"Saved top summary to {outfile}")


def load_checkpoint_results(cfg: TuningConfig) -> List[CandidateResult]:
    checkpoint_csv, _ = checkpoint_paths(cfg)
    if not cfg.resume:
        return []
    if not os.path.exists(checkpoint_csv):
        if cfg.steps == 500:
            legacy_checkpoint_csv, _ = legacy_checkpoint_paths(cfg)
            if os.path.exists(legacy_checkpoint_csv):
                checkpoint_csv = legacy_checkpoint_csv
            else:
                return []
        else:
            return []

    param_names = list(cfg.param_grid.keys())
    param_refs = {name: eco.CFG[name] for name in param_names}
    results: List[CandidateResult] = []
    with open(checkpoint_csv, newline="", encoding="utf-8") as file_obj:
        reader = csv.DictReader(file_obj)
        for row in reader:
            normalized_row = normalize_checkpoint_row(row)
            params = {
                name: cast_scalar_from_string(
                    param_refs[name],
                    require_checkpoint_field(normalized_row, name),
                )
                for name in param_names
            }
            results.append(
                CandidateResult(
                    params=params,
                    success_count=int(require_checkpoint_field(normalized_row, "success_count")),
                    success_rate=float(require_checkpoint_field(normalized_row, "success_rate")),
                    prey_extinction_count=int(
                        require_checkpoint_field(normalized_row, "prey_extinction_count")
                    ),
                    pred_extinction_count=int(
                        require_checkpoint_field(normalized_row, "pred_extinction_count")
                    ),
                    mean_final_preds=parse_float(
                        require_checkpoint_field(normalized_row, "mean_final_preds")
                    ),
                    mean_final_preys=parse_float(
                        require_checkpoint_field(normalized_row, "mean_final_preys")
                    ),
                    mean_min_preds=parse_float(
                        require_checkpoint_field(normalized_row, "mean_min_preds")
                    ),
                    mean_min_preys=parse_float(
                        require_checkpoint_field(normalized_row, "mean_min_preys")
                    ),
                    mean_extinction_step=parse_float(
                        require_checkpoint_field(normalized_row, "mean_extinction_step")
                    ),
                    mean_final_preds_success=parse_float(
                        require_checkpoint_field(normalized_row, "mean_final_preds_success")
                    ),
                    mean_final_preys_success=parse_float(
                        require_checkpoint_field(normalized_row, "mean_final_preys_success")
                    ),
                    mean_group_hunt_effort_success=parse_float(
                        require_checkpoint_field(
                            normalized_row,
                            "mean_group_hunt_effort_success",
                        )
                    ),
                )
            )
    return results


def completed_candidate_count(cfg: TuningConfig) -> int:
    return len(load_checkpoint_results(cfg))


def _evaluate_candidate(candidate: Dict[str, Scalar], steps: int, seed_start: int, seed_count: int) -> CandidateResult:
    config = dict(eco.CFG)
    config.update(candidate)
    config["live_render_pygame"] = False
    config["animate"] = False
    config["plot_macro_energy_flows"] = False
    config["restart_on_extinction"] = False
    config["steps"] = steps

    success_count = 0
    prey_extinction_count = 0
    pred_extinction_count = 0
    final_preds: List[float] = []
    final_preys: List[float] = []
    min_preds: List[float] = []
    min_preys: List[float] = []
    extinction_steps: List[float] = []
    success_final_preds: List[float] = []
    success_final_preys: List[float] = []
    success_group_hunt_effort: List[float] = []

    for seed in range(seed_start, seed_start + seed_count):
        with contextlib.redirect_stdout(io.StringIO()):
            (
                pred_hist,
                prey_hist,
                mean_coop_hist,
                var_coop_hist,
                successful_group_hunt_mean_effort_hist,
                preds_snaps,
                preys_snaps,
                preds_final,
                success,
                extinction_step,
            ) = eco.run_sim(seed_override=seed, config=config)

        final_pred = float(pred_hist[-1])
        final_prey = float(prey_hist[-1])
        final_preds.append(final_pred)
        final_preys.append(final_prey)
        min_preds.append(float(min(pred_hist)))
        min_preys.append(float(min(prey_hist)))

        if success:
            success_count += 1
            success_final_preds.append(final_pred)
            success_final_preys.append(final_prey)
            finite_effort = [
                v for v in successful_group_hunt_mean_effort_hist if not math.isnan(v)
            ]
            success_group_hunt_effort.append(mean_or_nan(finite_effort))
        else:
            if final_prey <= 0.0:
                prey_extinction_count += 1
            if final_pred <= 0.0:
                pred_extinction_count += 1
            if extinction_step is not None:
                extinction_steps.append(float(extinction_step))

    return CandidateResult(
        params=dict(candidate),
        success_count=success_count,
        success_rate=success_count / seed_count,
        prey_extinction_count=prey_extinction_count,
        pred_extinction_count=pred_extinction_count,
        mean_final_preds=mean_or_nan(final_preds),
        mean_final_preys=mean_or_nan(final_preys),
        mean_min_preds=mean_or_nan(min_preds),
        mean_min_preys=mean_or_nan(min_preys),
        mean_extinction_step=mean_or_nan(extinction_steps),
        mean_final_preds_success=mean_or_nan(success_final_preds),
        mean_final_preys_success=mean_or_nan(success_final_preys),
        mean_group_hunt_effort_success=mean_or_nan(success_group_hunt_effort),
    )


def run_search(cfg: TuningConfig) -> List[CandidateResult]:
    candidates = list(parameter_product(cfg.param_grid))
    param_names = list(cfg.param_grid.keys())
    completed_results = load_checkpoint_results(cfg)
    completed_map = {
        candidate_key(result.params, param_names): result
        for result in completed_results
    }
    pending = [
        candidate for candidate in candidates
        if candidate_key(candidate, param_names) not in completed_map
    ]

    print(
        f"Evaluating {len(candidates)} candidates | steps={cfg.steps} | "
        f"seeds={cfg.seed_start}-{cfg.seed_start + cfg.seed_count - 1}"
    )
    if completed_map:
        print(f"Resuming from checkpoint with {len(completed_map)} completed candidates")

    results: List[CandidateResult] = list(completed_map.values())
    completed = len(results)
    checkpoint_csv, checkpoint_summary = checkpoint_paths(cfg)

    for batch in chunked(pending, max(1, cfg.batch_size)):
        batch_results: List[CandidateResult] = []
        if cfg.workers == 1 or len(batch) == 1:
            for candidate in batch:
                batch_results.append(_evaluate_candidate(candidate, cfg.steps, cfg.seed_start, cfg.seed_count))
        else:
            with ProcessPoolExecutor(max_workers=min(cfg.workers, len(batch))) as executor:
                futures = [
                    executor.submit(_evaluate_candidate, candidate, cfg.steps, cfg.seed_start, cfg.seed_count)
                    for candidate in batch
                ]
                for future in as_completed(futures):
                    batch_results.append(future.result())

        for result in batch_results:
            completed += 1
            completed_map[candidate_key(result.params, param_names)] = result
            print(
                f"[{completed:>3}/{len(candidates)}] success={result.success_count}/{cfg.seed_count} "
                f"prey_ext={result.prey_extinction_count} params={result.params}"
            )

        results = sorted(
            completed_map.values(),
            key=lambda r: candidate_sort_key(r, cfg.ranking_mode),
            reverse=True,
        )
        save_csv(results, checkpoint_csv, param_names)
        save_top_summary(
            results,
            checkpoint_summary,
            cfg,
            title="Mutual-survival tuning checkpoint",
            completed_candidates=completed,
            total_candidates=len(candidates),
        )

    results.sort(key=lambda r: candidate_sort_key(r, cfg.ranking_mode), reverse=True)
    return results


def run_search_until_complete(cfg: TuningConfig) -> List[CandidateResult]:
    total = total_candidate_count(cfg)
    current_cfg = cfg
    results: List[CandidateResult] = []
    for pass_idx in range(1, cfg.max_resume_passes + 1):
        if pass_idx > 1 and not current_cfg.resume:
            current_cfg = replace(current_cfg, resume=True)
        results = run_search(current_cfg)
        completed = len(results)
        print(f"Resume pass {pass_idx}/{cfg.max_resume_passes}: completed {completed}/{total}")
        if completed >= total:
            return results
        current_cfg = replace(current_cfg, resume=True)
    raise RuntimeError(
        f"Tuning did not finish after {cfg.max_resume_passes} passes "
        f"({len(results)}/{total} candidates completed)."
    )


def finalize_results(results: List[CandidateResult], cfg: TuningConfig) -> tuple[str, str]:
    param_names = list(cfg.param_grid.keys())
    csv_out, summary_out = make_output_paths(cfg)
    save_csv(results, csv_out, param_names)
    save_top_summary(
        results,
        summary_out,
        cfg,
        title="Mutual-survival tuning summary",
        completed_candidates=len(results),
        total_candidates=len(results),
    )
    return csv_out, summary_out


def print_top_results(results: List[CandidateResult], cfg: TuningConfig) -> None:
    print("\nTop mutual-survival candidates:")
    for rank, result in enumerate(results[: cfg.top_k], start=1):
        print(
            f"#{rank:>2} success={result.success_count}/{cfg.seed_count} "
            f"prey_ext={result.prey_extinction_count} "
            f"hunt_effort={result.mean_group_hunt_effort_success:.3f} "
            f"mean_min_prey={result.mean_min_preys:.2f} params={result.params}"
        )


def main() -> None:
    cfg = load_config()
    validate_ranking_mode(cfg.ranking_mode)
    validate_param_grid(cfg.param_grid)
    if cfg.run_until_complete:
        results = run_search_until_complete(cfg)
    else:
        results = run_search(cfg)
    csv_out, summary_out = finalize_results(results, cfg)
    print(f"Final outputs: csv={csv_out} summary={summary_out}")
    print_top_results(results, cfg)


if __name__ == "__main__":
    main()
