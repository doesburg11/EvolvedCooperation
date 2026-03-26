#!/usr/bin/env python3
"""
Resume the configured mutual-survival tuner until all candidates are completed.

No CLI is used. Adjust the config block below if needed.
"""

from __future__ import annotations

import os
import sys
from dataclasses import replace


if __package__:
    from . import tune_mutual_survival as tuner
else:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    import predpreygrass_public_goods.tune_mutual_survival as tuner


# ============================================================
# RESUME HELPER CONFIG (edit here)
# ============================================================

FORCE_WORKERS = 1
MAX_PASSES_OVERRIDE = 24


def main() -> None:
    cfg = tuner.load_config()
    cfg = replace(
        cfg,
        resume=True,
        workers=FORCE_WORKERS if FORCE_WORKERS is not None else cfg.workers,
        run_until_complete=True,
        max_resume_passes=MAX_PASSES_OVERRIDE,
    )
    tuner.validate_ranking_mode(cfg.ranking_mode)
    tuner.validate_param_grid(cfg.param_grid)
    results = tuner.run_search_until_complete(cfg)
    csv_out, summary_out = tuner.finalize_results(results, cfg)
    print(f"Final outputs: csv={csv_out} summary={summary_out}")
    tuner.print_top_results(results, cfg)


if __name__ == "__main__":
    main()
