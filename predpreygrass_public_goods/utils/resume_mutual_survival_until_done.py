#!/usr/bin/env python3
"""
Resume the configured mutual-survival tuner until all candidates are completed.

No CLI is used. Adjust the config block below if needed.

Run from the repo root with:
  ./.conda/bin/python -m predpreygrass_public_goods.utils.resume_mutual_survival_until_done
"""

from __future__ import annotations

from dataclasses import replace


if not __package__:
    raise SystemExit(
        "Run this module from the repo root with "
        "'./.conda/bin/python -m predpreygrass_public_goods.utils.resume_mutual_survival_until_done'."
    )

from . import tune_mutual_survival as tuner


# ============================================================
# Resume helper config (edit here)
# ============================================================

force_workers = 1
max_passes_override = 24


def main() -> None:
    cfg = tuner.load_config()
    cfg = replace(
        cfg,
        resume=True,
        workers=force_workers if force_workers is not None else cfg.workers,
        run_until_complete=True,
        max_resume_passes=max_passes_override,
    )
    tuner.validate_ranking_mode(cfg.ranking_mode)
    tuner.validate_param_grid(cfg.param_grid)
    results = tuner.run_search_until_complete(cfg)
    csv_out, summary_out = tuner.finalize_results(results, cfg)
    print(f"Final outputs: csv={csv_out} summary={summary_out}")
    tuner.print_top_results(results, cfg)


if __name__ == "__main__":
    main()
