#!/usr/bin/env python3
"""Stage 0 viability pilot (no hypothesis test): do populations survive under the reconstructed paper configuration?

Paper configuration (run_feeding.PAPER_OVERRIDES), the three Stage 1 infant-move levels, feeding enabled and disabled,
seeds 100-103 (not Stage 1 seeds), 10,000 steps, window = final 2,000. Reports extinction and population size.

  ~/simulation_results/altruistic_feeding/venv_050/bin/python run_viability_pilot.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENERGY = os.environ.get("AF_ENERGY", "paper")
OUT = Path(os.path.expanduser("~/simulation_results/altruistic_feeding/viability_pilot" + ("" if ENERGY == "paper" else "_" + ENERGY)))
LEVELS, SEEDS, FEEDING = [0.1, 0.5, 1.0], [100, 101, 102, 103], [1, 0]
STEPS, WINDOW, WORKERS = 10_000, 2_000, 4


def one(job):
    lv, s, f = job
    cmd = [sys.executable, str(HERE / "run_feeding.py"), "--level", str(lv), "--seed", str(s), "--feeding", str(f),
           "--steps", str(STEPS), "--window", str(WINDOW), "--out", str(OUT), "--energy", ENERGY]
    with open(OUT / "logs" / f"move{lv}_seed{s}_feed{f}.log", "w") as fh:
        subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT)
    p = OUT / f"result_move{lv}_seed{s}_feed{f}.json"
    return json.loads(p.read_text()) if p.exists() else {"level": lv, "seed": s, "feeding": f, "failed": True}


def main():
    (OUT / "logs").mkdir(parents=True, exist_ok=True)
    jobs = [(lv, s, f) for f in FEEDING for s in SEEDS for lv in LEVELS]
    with ThreadPoolExecutor(WORKERS) as ex:
        rows = list(ex.map(one, jobs))
    summary = [{k: r.get(k) for k in ("level", "seed", "feeding", "failed", "extinct_at", "mean_population",
                                      "run_cap_share", "feeds", "amount", "ISR", "wall_seconds")} for r in rows]
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
    for r in summary:
        print(r, flush=True)
    for f in FEEDING:
        for lv in LEVELS:
            arm = [r for r in summary if r["feeding"] == f and r["level"] == lv]
            alive = sum(1 for r in arm if not r.get("failed") and r["extinct_at"] is None)
            print(f"feeding={f} level={lv}: alive {alive}/{len(arm)}", flush=True)


if __name__ == "__main__":
    main()
