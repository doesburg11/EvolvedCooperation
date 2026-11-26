"""Step 2 of PREREG_SCREEN.md: an evolving partner market, no learning.

N haploid agents with two inherited traits in [0, 1]: offer s and acceptance threshold a.
Non-overlapping generations of H rounds; every agent starts each generation unpaired.

Each round, in this order:
  1. Search: each unpaired agent succeeds with probability m = 1/T; successful searchers are paired
     uniformly at random among themselves (one uniformly chosen odd one out stays unpaired).
  2. Hunt: each pair catches a stag of value S = 1; the catcher (probability 1/2 each) keeps 1 - s_catcher,
     the partner receives s_catcher. Each unpaired agent receives h.
  3. Leave (choice arm only): the non-catcher leaves if s_catcher < its own a; both become unpaired.

Fitness = total income + 0.01 * mean income (uniform parents if everyone earned 0). Wright-Fisher
reproduction from the whole population; each trait mutates with probability mu by Normal(0, sigma),
clipped to [0, 1].
"""

import numpy as np
from numba import njit

N = 200
H = 100
G = 2000
MU = 0.01
SIGMA = 0.05
FLOOR = 0.01
WINDOW = 200  # outcome window: the last WINDOW generations

STARTS = ("exploiter", "fair", "random")


@njit(cache=True)
def _seed(seed):
    np.random.seed(seed)


@njit(cache=True)
def generation(s, a, m, h, rounds, choice, met, stats):
    """One generation of the market. Returns each agent's total income.

    stats (float64[9]) accumulates: 0 pair-rounds, 1 catches (one per pair-round), 2 sum of offers
    received, 3 sum of squared offers, 4 break-ups, 5 rematch delays summed (rounds unpaired before being
    paired again, counted only for agents that had a break-up this generation), 6 such rematches, 7 new
    pairs that reunite agents already paired earlier this generation, 8 new pairs.
    """
    n = s.shape[0]
    income = np.zeros(n)
    partner = -np.ones(n, dtype=np.int64)
    unpaired_since = np.zeros(n, dtype=np.int64)
    broke_before = np.zeros(n, dtype=np.bool_)
    met[:, :] = False
    succ = np.empty(n, dtype=np.int64)
    leavers = np.empty(n, dtype=np.int64)
    for r in range(rounds):
        # 1. search
        k = 0
        for i in range(n):
            if partner[i] < 0 and np.random.random() < m:
                succ[k] = i
                k += 1
        for i in range(k - 1, 0, -1):  # Fisher-Yates over the successful searchers
            j = np.random.randint(0, i + 1)
            t = succ[i]
            succ[i] = succ[j]
            succ[j] = t
        for p in range(0, k - 1, 2):  # the last one stays out if k is odd (uniform after the shuffle)
            i = succ[p]
            j = succ[p + 1]
            partner[i] = j
            partner[j] = i
            stats[8] += 1.0
            if met[i, j]:
                stats[7] += 1.0
            met[i, j] = True
            met[j, i] = True
            for x in (i, j):
                if broke_before[x]:
                    stats[5] += r - unpaired_since[x]
                    stats[6] += 1.0
        # 2. hunt (all payoffs first; break-ups are applied after every pair has been paid)
        nb = 0
        for i in range(n):
            j = partner[i]
            if j < 0:
                income[i] += h
            elif i < j:
                if np.random.random() < 0.5:
                    c, q = i, j
                else:
                    c, q = j, i
                offer = s[c]
                income[c] += 1.0 - offer
                income[q] += offer
                stats[0] += 1.0
                stats[1] += 1.0
                stats[2] += offer
                stats[3] += offer * offer
                if choice and offer < a[q]:  # the receiver decides (applied in step 3)
                    leavers[nb] = i
                    nb += 1
        # 3. leave
        for b in range(nb):
            i = leavers[b]
            j = partner[i]
            partner[i] = -1
            partner[j] = -1
            unpaired_since[i] = r + 1
            unpaired_since[j] = r + 1
            broke_before[i] = True
            broke_before[j] = True
            stats[4] += 1.0
    return income


@njit(cache=True)
def reproduce(s, a, income, mu, sigma, floor):
    n = s.shape[0]
    total = income.sum()
    if total <= 0.0:
        w = np.ones(n)
    else:
        w = income + floor * total / n
    cum = np.cumsum(w)
    cum /= cum[-1]
    ns = np.empty(n)
    na = np.empty(n)
    for k in range(n):
        p = np.searchsorted(cum, np.random.random(), side="right")
        if p >= n:
            p = n - 1
        ns[k] = s[p]
        na[k] = a[p]
        if np.random.random() < mu:
            ns[k] = min(1.0, max(0.0, ns[k] + sigma * np.random.standard_normal()))
        if np.random.random() < mu:
            na[k] = min(1.0, max(0.0, na[k] + sigma * np.random.standard_normal()))
    return ns, na


@njit(cache=True)
def _random_traits(n):
    return np.random.random(n), np.random.random(n)


def initial_traits(start, n=N):
    if start == "exploiter":
        return np.full(n, 0.05), np.zeros(n)
    if start == "fair":
        return np.full(n, 0.5), np.full(n, 0.45)
    if start == "random":
        return _random_traits(n)
    raise ValueError(f"unknown start {start!r}")


def run(T, h, start, choice, seed, n=N, rounds=H, gens=G, window=WINDOW, mu=MU, sigma=SIGMA):
    """One run. Returns (summary dict, per-generation mean s, per-generation mean a)."""
    if n % 2:
        raise ValueError("n must be even")
    window = min(window, gens)
    _seed(seed)
    s, a = initial_traits(start, n)
    m = 1.0 / T
    met = np.zeros((n, n), dtype=np.bool_)
    mean_s = np.empty(gens)
    mean_a = np.empty(gens)
    win = np.zeros(9)
    for g in range(gens):
        stats = np.zeros(9)
        income = generation(s, a, m, h, rounds, choice, met, stats)
        mean_s[g] = s.mean()
        mean_a[g] = a.mean()
        if g >= gens - window:
            win += stats
        s, a = reproduce(s, a, income, mu, sigma, FLOOR)
    catches = win[1]
    mean_off = win[2] / catches if catches else float("nan")
    summary = {
        "T": T, "h": h, "start": start, "arm": "choice" if choice else "no_choice", "seed": seed,
        "partner_share": float(mean_s[gens - window:].mean()),
        "mean_a": float(mean_a[gens - window:].mean()),
        "catch_weighted_share": mean_off,
        "catch_share_sd": float(np.sqrt(max(0.0, win[3] / catches - mean_off ** 2))) if catches else float("nan"),
        "frac_paired": float(2 * win[0] / (n * rounds * window)),
        "breakups_per_gen": float(win[4] / window),
        "rematch_delay": float(win[5] / win[6]) if win[6] else float("nan"),
        "reunion_share": float(win[7] / win[8]) if win[8] else float("nan"),
    }
    return summary, mean_s, mean_a
