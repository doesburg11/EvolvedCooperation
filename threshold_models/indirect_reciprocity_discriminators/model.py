"""Discriminators against ALLD in a well-mixed Wright-Fisher population (pre-registration: README.md).

Every ordered pair meets once per generation (donor, recipient). A discriminator (DISC) helps a DISC recipient
always and an ALLD recipient only when it does not know its reputation (probability 1 - q, drawn per encounter).
ALLD never helps. Helping costs c and gives b. Fitness 1 + s * (payoff / (N - 1)); the number of ALLD in the next
generation is binomial(N, ALLD share of total fitness).
"""

from __future__ import annotations

from numba import njit
import numpy as np


def q_star(n_alld: int, N: int, b: float, c: float) -> float:
    """q at which ALLD and DISC have equal expected payoff with n_alld ALLD (README, Theory)."""
    return 1.0 - (b - c) * (N - n_alld - 1) / (b * (N - n_alld) + c * n_alld)


def expected_payoffs(n_alld: int, N: int, b: float, c: float, q: float) -> tuple[float, float]:
    n_disc = N - n_alld
    pi_alld = b * (1 - q) * n_disc / (N - 1)
    pi_disc = ((b - c) * (n_disc - 1) - c * (1 - q) * n_alld) / (N - 1)
    return pi_alld, pi_disc


def predicted_change(n_alld: int, N: int, b: float, c: float, q: float, s: float) -> float:
    x = n_alld / N
    pa, pd = expected_payoffs(n_alld, N, b, c, q)
    fa, fd = 1 + s * pa, 1 + s * pd
    return x * fa / (x * fa + (1 - x) * fd) - x


@njit(cache=False)
def helped_matrix_counts(n_disc, n_alld, q):
    """For each DISC, how many ALLD it helped; for each ALLD, how many DISC helped it (one draw per encounter)."""
    given = np.zeros(n_disc)
    received = np.zeros(n_alld)
    for i in range(n_disc):
        for j in range(n_alld):
            if np.random.random() >= q:  # reputation not known -> help
                given[i] += 1
                received[j] += 1
    return given, received


@njit(cache=False)
def alld_share(n_alld, N, b, c, q, s):
    n_disc = N - n_alld
    given, received = helped_matrix_counts(n_disc, n_alld, q)
    f_alld = 0.0
    for j in range(n_alld):
        f_alld += 1.0 + s * b * received[j] / (N - 1)
    f_disc = 0.0
    for i in range(n_disc):
        f_disc += 1.0 + s * ((b - c) * (n_disc - 1) - c * given[i]) / (N - 1)
    return f_alld / (f_alld + f_disc)


@njit(cache=False)
def generation(n_alld, N, b, c, q, s):
    if n_alld == 0 or n_alld == N:
        return n_alld
    return np.random.binomial(N, alld_share(n_alld, N, b, c, q, s))


@njit(cache=False)
def one_generation_changes(n_alld0, N, b, c, q, s, seed0, runs):
    out = np.empty(runs)
    for r in range(runs):
        np.random.seed(seed0 + r)
        out[r] = generation(n_alld0, N, b, c, q, s) / N - n_alld0 / N
    return out


@njit(cache=False)
def trajectory_finals(n_alld0, N, b, c, q, s, seed0, runs, generations):
    out = np.empty(runs)
    for r in range(runs):
        np.random.seed(seed0 + r)
        n = n_alld0
        for _ in range(generations):
            n = generation(n, N, b, c, q, s)
        out[r] = n / N
    return out
