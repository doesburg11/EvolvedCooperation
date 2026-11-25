"""Interim check for PREREG_KIN_TEST.md: reads only progress files (generation, elapsed seconds) and launch.json.

Usage: python -m ecological_models.density_dependent_dispersal.interim_check {V|M}
Prints, per stage: runs finished, runs in progress (min/max generation), runs not started, projected finish
(launch + slowest run's projected total), and whether the 6-hour rule (Stage M) is breached.
"""

from __future__ import annotations

import json
import sys
import time

from ecological_models.density_dependent_dispersal.run_test import G, jobs, stage_dir

stage = sys.argv[1]
d = stage_dir(stage)
launch = json.loads((d / "launch.json").read_text())
now = time.time()
done, running, waiting, proj = 0, [], 0, []
for j in jobs(stage):
    if (d / f"{j['name']}.npz").exists():
        done += 1
        continue
    p = d / f"{j['name']}.progress"
    if not p.exists():
        waiting += 1
        continue
    g, el = p.read_text().split()
    g, el = int(g), float(el)
    age = now - p.stat().st_mtime
    running.append((j["name"], g, el, age))
    proj.append(p.stat().st_mtime - el + el / g * G)
print(time.strftime("%H:%M"), f"stage {stage}: {done} done, {len(running)} running, {waiting} not started")
if running:
    gs = [r[1] for r in running]
    print(f"  generations {min(gs)}..{max(gs)}; oldest progress update {max(r[3] for r in running):.0f} s ago")
    finish = max(proj)
    hours = (finish - launch["start"]) / 3600
    if waiting:
        hours *= 2   # a second wave would follow the first
    print(f"  projected finish of the running wave: {time.strftime('%H:%M', time.localtime(finish))}; "
          f"stage projected at {hours:.1f} h after launch" + (" (two waves)" if waiting else ""))
    if stage == "M":
        print("  6-hour rule:", "BREACHED" if hours > 6 else "ok")
    stalled = [r[0] for r in running if r[3] > 600]
    if stalled:
        print("  STALLED (no progress for > 10 min):", stalled)
