"""TFT against ALLD in a well-mixed Wright-Fisher population (pre-registration: README.md).

Every pair plays one repeated donation game per generation with a geometric number of rounds (another round with
probability w). Only TFT-TFT pairs depend on the number of rounds: they earn (b - c) * L each. TFT against ALLD: -c
and b in round 1, nothing after. ALLD against ALLD: 0. Fitness 1 + s * (payoff / (N - 1)); the number of ALLD in the
next generation is binomial(N, ALLD share of total fitness).
"""

from __future__ import annotations

import numpy as np
from numba import njit


def w_star(n_alld: int, N: int, b: float, c: float) -> float:
    """w at which ALLD and TFT have equal expected payoff with n_alld ALLD (README, Theory)."""
    return 1.0 - (b - c) * (N - n_alld - 1) / (b * (N - n_alld) + c * n_alld)


def w_star_tft_rare(m_tft: int, N: int, b: float, c: float) -> float:
    return 1.0 - (m_tft - 1) * (b - c) / (b * m_tft + c * (N - m_tft))


def expected_payoffs(n_alld: int, N: int, b: float, c: float, w: float) -> tuple[float, float]:
    n_tft = N - n_alld
    pi_alld = b * n_tft / (N - 1)
    pi_tft = ((b - c) * (n_tft - 1) / (1 - w) - c * n_alld) / (N - 1)
    return pi_alld, pi_tft


def predicted_change(n_alld: int, N: int, b: float, c: float, w: float, s: float) -> float:
    """Expected one-generation change in ALLD frequency from expected payoffs."""
    x = n_alld / N
    pa, pt = expected_payoffs(n_alld, N, b, c, w)
    fa, ft = 1 + s * pa, 1 + s * pt
    return x * fa / (x * fa + (1 - x) * ft) - x


@njit(cache=False)
def tft_round_sums(m, w):
    """For m TFT players, each one's total number of rounds over its TFT partners (one draw per pair)."""
    sums = np.zeros(m)
    p = 1.0 - w
    for i in range(m):
        for j in range(i + 1, m):
            rounds = np.random.geometric(p)
            sums[i] += rounds
            sums[j] += rounds
    return sums


@njit(cache=False)
def alld_share(n_alld, N, b, c, w, s):
    """ALLD share of total fitness for one generation's realised games."""
    n_tft = N - n_alld
    f_alld = n_alld * (1.0 + s * b * n_tft / (N - 1))
    sums = tft_round_sums(n_tft, w)
    f_tft = 0.0
    for i in range(n_tft):
        f_tft += 1.0 + s * ((b - c) * sums[i] - c * n_alld) / (N - 1)
    return f_alld / (f_alld + f_tft)


@njit(cache=False)
def generation(n_alld, N, b, c, w, s):
    if n_alld == 0 or n_alld == N:
        return n_alld
    return np.random.binomial(N, alld_share(n_alld, N, b, c, w, s))


@njit(cache=False)
def one_generation_changes(n_alld0, N, b, c, w, s, seed0, runs):
    """ALLD frequency change after one generation, one value per run (seeds seed0 .. seed0 + runs - 1)."""
    out = np.empty(runs)
    for r in range(runs):
        np.random.seed(seed0 + r)
        out[r] = generation(n_alld0, N, b, c, w, s) / N - n_alld0 / N
    return out


@njit(cache=False)
def trajectory_finals(n_alld0, N, b, c, w, s, seed0, runs, generations):
    out = np.empty(runs)
    for r in range(runs):
        np.random.seed(seed0 + r)
        n = n_alld0
        for _ in range(generations):
            n = generation(n, N, b, c, w, s)
        out[r] = n / N
    return out
