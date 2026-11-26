"""Rung 5a theory screen (no simulation), 2026-11-26: private assessment, on rung 4b (q = 0.8, mutation mu).

    ./.conda/bin/python -m ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a.theory

Change from rung 4b, only this: there is no public record. Every individual keeps its own view (good/bad) of every
other. When a donor acts, each other individual observes the act independently with probability o and assesses it by
simple standing using ITS OWN view of the recipient (helping is good; refusing is good only if the observer sees the
recipient as bad); assessment flips with probability a per observation, as before. A discriminator consults its own
view of the recipient.

Mean field (independent-views approximation): g_X = share of observers that view a type-X individual as good. The
donor's view and an observer's view of the same recipient are treated as independent, each good with probability
g_Y. Then the probability that an observed act of a type-X donor earns a good view (before flips) is, averaged over
recipient types Y (shares x_Y):
    DISC (test):     1 - sum_Y x_Y g_Y [ e ((1 - q) + q g_Y) + q (1 - g_Y) ]
    DISC (shuffled): 1 - sum_Y x_Y g_Y [ e ((1 - q) + q (1 - bbar)) + q bbar ]       (donor uses its view of a random
                                                                                    other individual; bbar = sum x (1-g))
    ALLC:            1 - e sum_Y x_Y g_Y            ALLD: 1 - sum_Y x_Y g_Y      (as with public records)
With a public record the observer's and the donor's views coincide and the DISC (test) term q (1 - g_Y) g_Y vanishes:
this is the screen's only difference from rung 4b. Independence sets the covariance between the donor's and the
observer's views to zero: positive covariance (plausible, since views come from the same acts) would make the screen
overstate the disagreement penalty, negative covariance understate it; the screen also ignores the dispersion of views
about an individual, observer-specific tendencies and links between views and reproduction. So it is not a proven
bound in either direction, and says nothing directly about stochastic maintenance.
Records reset at birth; within a generation views evolve as in rungs 3a-4b: g += o (P' - g) per donor round.
Payoffs as rung 4a/4b (a DISC helps a type-Y recipient with probability (1 - e)((1 - q) + q g_Y)).
"""

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rebase import theory as rb

Q, B, C, S = 0.8, 3.0, 1.0, 0.1
O, E, A = 0.5, 0.1, 0.02
K, STEPS = 10, 400


def records(x, private=True, shuffled=False, q=Q, o=O, e=E, a=A, k=K, steps=STEPS):
    xc, xd, xa = x
    g = [1.0, 1.0, 1.0]
    acc = [0.0, 0.0, 0.0]
    du = 1.0 / steps
    for _ in range(k):
        g0 = list(g)
        for _ in range(steps):
            good_mass = xc * g[0] + xd * g[1] + xa * g[2]          # sum_Y x_Y g_Y
            bbar = 1.0 - good_mass
            pc = 1 - e * good_mass
            pa = 1 - good_mass
            if shuffled:
                h_i = (1 - q) + q * (1 - bbar)
                if private:
                    pd = 1 - good_mass * (e * h_i + q * bbar)
                else:
                    pd = 1 - (1 - (1 - e) * h_i) * (1 - bbar)
            elif private:
                pd = 1 - sum(xy * gy * (e * ((1 - q) + q * gy) + q * (1 - gy))
                             for xy, gy in zip(x, g))
            else:
                pd = 1 - e * good_mass                              # public record (rung 4b)
            ps = [(1 - a) * p + a * (1 - p) for p in (pc, pd, pa)]
            for i in range(3):
                g[i] += o * (ps[i] - g0[i]) * du
                acc[i] += g[i] * du
    return [v / k for v in acc]


def payoffs(x, private=True, shuffled=False):
    gs = records(x, private, shuffled)
    bbar = sum(xi * (1 - gi) for xi, gi in zip(x, gs))
    hc = [(1 - E)] * 3
    if shuffled:
        hd = [(1 - E) * ((1 - Q) + Q * (1 - bbar))] * 3
    else:
        hd = [(1 - E) * ((1 - Q) + Q * gy) for gy in gs]
    h = (hc, hd, [0.0] * 3)
    return [B * sum(x[d] * h[d][me] for d in range(3)) - C * sum(x[r] * h[me][r] for r in range(3))
            for me in range(3)], gs


def step(x, mu, private=True, shuffled=False):
    pis, _ = payoffs(x, private, shuffled)
    f = [1 + S * p for p in pis]
    tot = sum(xi * fi for xi, fi in zip(x, f))
    y = [xi * fi / tot for xi, fi in zip(x, f)]
    return tuple((1 - mu) * y[i] + mu / 2 * (1 - y[i]) for i in range(3))


def run(x0, mu, gens, private=True, shuffled=False):
    x = tuple(x0)
    win = []
    g500 = None
    for g in range(1, gens + 1):
        x = step(x, mu, private, shuffled)
        if g == 500:
            g500 = x[0] + x[1]
        if g > gens - 500:
            win.append(x[0] + x[1])
    return g500, sum(win) / len(win), x


def boundary_two(private=True, mu=0.0):
    """Smallest DISC share (DISC vs ALLD only) at which DISC out-earns ALLD (large-N payoffs)."""
    lo, hi = 0.0, 1.0
    if payoffs((0.0, 0.999, 0.001), private)[0][1] <= payoffs((0.0, 0.999, 0.001), private)[0][2]:
        return None
    for _ in range(30):
        mid = (lo + hi) / 2
        pis, _ = payoffs((0.0, mid, 1 - mid), private)
        lo, hi = (lo, mid) if pis[1] > pis[2] else (mid, hi)
    return hi


def finite_time_threshold(lo=0.001, hi=0.002, steps=5, gens=4000, bar=0.8):
    """Bisection on mu for mean cooperators >= bar over the last 500 of `gens` generations from an all-DISC start.
    A finite-time threshold, not the equilibrium fold (Codex: the cooperative fixed point persists up to about
    mu = 0.00128)."""
    rows = []
    for _ in range(steps):
        mid = (lo + hi) / 2
        _, win, _ = run((0.0, 1.0, 0.0), mid, gens)
        rows.append((mid, win))
        lo, hi = (mid, hi) if win >= bar else (lo, mid)
    return lo, hi, rows


def main():
    print("check: public records reproduce rung 4b's screen at mu 0.001 (0.988 / 0.988):",
          tuple(round(v, 4) for v in run((0.1, 0.8, 0.1), 0.001, 2000, private=False)[:2]))
    print(f"two-strategy boundary (DISC vs ALLD): public {boundary_two(False):.3f}, private {boundary_two(True):.3f}")
    gp = records((0.0, 0.9, 0.1), True)
    gq = records((0.0, 0.9, 0.1), False)
    print(f"views at 90% DISC: public DISC/ALLD good {gq[1]:.3f}/{gq[2]:.3f}; private {gp[1]:.3f}/{gp[2]:.3f}")
    for mu in (0.0, 0.001, 0.002):
        for name, x0 in (("main 10/80/10", (0.1, 0.8, 0.1)), ("all-DISC", (0.0, 1.0, 0.0))):
            g500, win, xf = run(x0, mu, 2000)
            print(f"private, mu {mu}, {name}: cooperators gen 500 {g500:.4f}, window 1501-2000 {win:.4f}, "
                  f"final C/D/A {tuple(round(v, 4) for v in xf)}")
    g500, win, xf = run((0.1, 0.8, 0.1), 0.001, 2000, private=True, shuffled=True)
    print(f"private, shuffled, mu 0.001: cooperators gen 500 {g500:.4f}, window {win:.4f}")
    lo, hi, rows = finite_time_threshold()
    for mid, w in rows:
        print(f"private bisection mu {mid:.6f}: all-DISC start, window gens 3501-4000 cooperators {w:.4f}")
    print(f"private finite-time threshold: between mu {lo:.6f} and {hi:.6f}")


if __name__ == "__main__":
    main()
