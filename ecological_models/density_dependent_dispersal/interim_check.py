"""Interim check for PREREG_KIN_TEST.md: reads only progress files (generation, elapsed seconds) and launch.json.

Usage: python -m ecological_models.density_dependent_dispersal.interim_check {V|M}
Prints, per stage: runs finished, runs in progress (min/max generation), runs not started, and the projected
finish of the stage (amendment A1): each running run finishes at its own measured speed (never before now);
runs not started are queued in launch order onto the earliest free worker, each taking G generations at the
mean speed measured in its arm (T and F share a code path, so either stands in for the other; otherwise the
slowest measured speed). Progress files older than the launch are an error. Stage M: whether the 8-hour rule is
breached (projected finish, or time already elapsed, beyond 8 h after launch).
"""

from __future__ import annotations

import heapq
import json
import os
import sys
import time

BUDGET_H = 8.0


def project(running, waiting_arms, workers, now, G):
    """running: dicts with arm, rate (s per generation), finish (epoch s); waiting_arms: arms of the runs not
    started, in launch order. Returns the projected epoch time at which the last run finishes."""
    mean = {}
    for r in running:
        mean.setdefault(r["arm"], []).append(r["rate"])
    mean = {a: sum(v) / len(v) for a, v in mean.items()}

    def rate(arm):
        if arm in mean:
            return mean[arm]
        other = {"T": "F", "F": "T"}.get(arm)
        return mean[other] if other in mean else max(mean.values())

    free = [max(r["finish"], now) for r in running] + [now] * max(0, workers - len(running))
    heapq.heapify(free)
    finish = max(free)
    for arm in waiting_arms:
        t = heapq.heappop(free) + rate(arm) * G
        finish = max(finish, t)
        heapq.heappush(free, t)
    return finish


def main(stage):
    from ecological_models.density_dependent_dispersal.run_test import G, jobs, stage_dir
    d = stage_dir(stage)
    launch = json.loads((d / "launch.json").read_text())
    now = time.time()
    done, running, waiting, stale = 0, [], [], []
    for j in jobs(stage):
        if (d / f"{j['name']}.npz").exists():
            done += 1
            continue
        p = d / f"{j['name']}.progress"
        try:
            fd = os.open(p, os.O_RDONLY)          # contents and timestamp from the same file
            try:
                mt = os.fstat(fd).st_mtime
                g, el = os.read(fd, 256).decode().split()
            finally:
                os.close(fd)
        except FileNotFoundError:
            if (d / f"{j['name']}.npz").exists():   # finished between the two checks
                done += 1
            else:
                waiting.append(j)
            continue
        g, el = int(g), float(el)
        if mt < launch["start"]:
            stale.append(j["name"])
            continue
        running.append(dict(name=j["name"], arm=j["arm"], g=g, el=el, age=now - mt, mt=mt))
    print(time.strftime("%H:%M"), f"stage {stage}: {done} done, {len(running)} running, {len(waiting)} not started")
    elapsed = (now - launch["start"]) / 3600
    reasons = []
    if stale:
        reasons.append(f"stale progress files from before this launch: {stale}")
    stalled = [r["name"] for r in running if r["age"] > 600]
    if stalled:
        reasons.append(f"no progress for > 10 min: {stalled}")
    if elapsed > BUDGET_H:
        reasons.append(f"{elapsed:.1f} h elapsed > {BUDGET_H:.0f} h")
    timed = [dict(r, rate=r["el"] / r["g"], finish=r["mt"] - r["el"] + r["el"] / r["g"] * G)
             for r in running if r["g"] > 0]
    if running:
        gs = [r["g"] for r in running]
        print(f"  generations {min(gs)}..{max(gs)}; oldest progress update {max(r['age'] for r in running):.0f} s ago")
    if timed:
        rates = {}
        for r in timed:
            rates.setdefault(r["arm"], []).append(r["rate"])
        print("  s per generation by arm:", {a: round(sum(v) / len(v), 3) for a, v in sorted(rates.items())})
        # runs still at generation 0 are treated as starting now
        waiting_arms = [r["arm"] for r in running if r["g"] == 0] + [j["arm"] for j in waiting]
        busy = len(timed)
        finish = project(timed, waiting_arms, max(launch["workers"], busy), now, G)
        hours = (finish - launch["start"]) / 3600
        print(f"  projected finish of the stage: {time.strftime('%H:%M', time.localtime(finish))}, "
              f"{hours:.1f} h after launch ({elapsed:.1f} h elapsed)")
        if hours > BUDGET_H:
            reasons.append(f"projected {hours:.1f} h > {BUDGET_H:.0f} h")
    elif waiting or running:
        print(f"  no timed progress yet ({elapsed:.2f} h elapsed)")
    if stage == "M":
        print("  VERDICT: STOP (" + "; ".join(reasons) + ")" if reasons else "  VERDICT: ok")


if __name__ == "__main__":
    main(sys.argv[1])
