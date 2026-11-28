"""Rung 6a theory screen (no simulation), 2026-11-28: overlapping generations on rung 5c's met setting (p = 0.75).

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung6a_overlap.theory

Smallest ecological step: each generation a share r of the population is replaced (the replaced slots are filled by
rung 5a's fitness-weighted reproduction with mutation per offspring); the other 1 - r survive with their strategy.
Views still reset every generation (memory across generations is a later, separate step). Mean field:
x' = (1 - r) x + r * step_5a(x), where step_5a already includes mutation of offspring. r = 1 is rung 5c's C2 setting.
Same limits as before: the mean field ranks settings within itself and has not predicted simulated pass rates.
"""

from concurrent.futures import ProcessPoolExecutor

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a import theory as t5
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5c_partial_empathy import theory as t5c

P = 0.75
RS = (1.0, 0.5, 0.2)


def step_overlap(x, mu, r, shuffled=False):
    y = t5.step(x, mu, True, shuffled)
    return tuple((1 - r) * xi + r * yi for xi, yi in zip(x, y))


def run(x0, mu, gens, r, shuffled=False):
    x = tuple(x0)
    win = []
    g500 = None
    for g in range(1, gens + 1):
        x = step_overlap(x, mu, r, shuffled)
        if g == 500:
            g500 = x[0] + x[1]
        if g > gens - 500:
            win.append(x[0] + x[1])
    return g500, sum(win) / len(win), x


def cliff(r, lo=0.0002, hi=0.2, steps=9, gens=4000, bar=0.8):
    ok = lambda mu: run((0.0, 1.0, 0.0), mu, gens, r)[1] >= bar
    assert ok(lo) and not ok(hi)
    for _ in range(steps):
        mid = (lo * hi) ** 0.5
        lo, hi = (mid, hi) if ok(mid) else (lo, mid)
    return lo, hi


def screen(r):
    t5c.install(P)
    g5, w, x = run((0.1, 0.8, 0.1), 0.001, 2000, r)
    _, ws, _ = run((0.1, 0.8, 0.1), 0.001, 2000, r, shuffled=True)
    return r, g5, w, x, ws, cliff(r)


def main():
    t5c.install(P)
    a = run((0.1, 0.8, 0.1), 0.001, 50, 1.0)
    t5c.install(P)
    x = (0.1, 0.8, 0.1)
    for _ in range(50):
        x = t5.step(x, 0.001, True, False)
    assert max(abs(u - v) for u, v in zip(a[2], x)) < 1e-12        # r = 1 reproduces rung 5c's dynamics
    print("check: r = 1 reproduces rung 5c's (p 0.75) mean-field dynamics")
    with ProcessPoolExecutor(len(RS)) as ex:
        rows = list(ex.map(screen, RS))
    print("| Share replaced per generation r | Cooperators gen 500 / gens 1,501-2,000 (mu 0.001) | Final ALLC / DISC / ALLD"
          " | Shuffled (late) | Finite-time cliff mu (per offspring) |")
    print("| --- | --- | --- | --- | --- |")
    for r, g5, w, x, ws, (lo, hi) in rows:
        print(f"| {r:.1f} | {g5:.3f} / {w:.3f} | {x[0]:.3f} / {x[1]:.3f} / {x[2]:.3f} | {ws:.3f} | {lo:.5f}-{hi:.5f} |")


if __name__ == "__main__":
    main()
