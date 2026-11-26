import numpy as np
import pytest

from ecological_models.partner_choice_fairness import analyze, market


def _gen(s, a, m, h, rounds, choice, seed=0, q=0.0):
    market._seed(seed)
    n = len(s)
    met = np.zeros((n, n), dtype=np.bool_)
    stats = np.zeros(10)
    inc = market.generation(np.asarray(s, float), np.asarray(a, float), m, h, rounds, choice, met, stats, q)
    return inc, stats


def test_income_conserved_per_pair_round():
    n, rounds, h = 20, 50, 0.3
    s = np.random.default_rng(1).random(n)
    inc, st = _gen(s, np.zeros(n), 0.3, h, rounds, True)
    unpaired_rounds = n * rounds - 2 * st[0]
    assert inc.sum() == pytest.approx(st[0] * 1.0 + unpaired_rounds * h)
    assert st[0] == st[1]


def test_T1_even_population_all_paired_and_no_choice_never_breaks():
    n = 10
    inc, st = _gen(np.full(n, 0.0), np.full(n, 1.0), 1.0, 0.0, 30, False)
    assert st[0] == n // 2 * 30  # all paired every round
    assert st[4] == 0
    assert st[8] == n // 2


def test_receiver_leaves_when_offer_below_threshold():
    # offer 0.1 everywhere, threshold 0.2: every pair breaks after its first hunt
    n = 10
    inc, st = _gen(np.full(n, 0.1), np.full(n, 0.2), 1.0, 0.0, 5, True)
    assert st[4] == st[1]
    # offers at threshold are accepted (strict <)
    inc, st = _gen(np.full(n, 0.2), np.full(n, 0.2), 1.0, 0.0, 5, True)
    assert st[4] == 0


def test_reunion_with_two_agents():
    inc, st = _gen(np.full(2, 0.1), np.full(2, 0.5), 1.0, 0.0, 10, True)
    # pair forms, breaks, re-forms every round: all but the first new pair are reunions
    assert st[8] == 10 and st[7] == 9
    assert st[6] == 18 and st[5] == 0  # immediate rematch, both agents counted


def test_catcher_split():
    inc, st = _gen(np.array([0.3, 0.3]), np.zeros(2), 1.0, 0.0, 1, True)
    assert sorted(inc) == pytest.approx([0.3, 0.7])


def test_reproduce_zero_income_uniform_and_clip():
    market._seed(3)
    s = np.linspace(0, 1, 200)
    ns, na = market.reproduce(s, s.copy(), np.zeros(200), 1.0, 5.0, 0.01)
    assert ns.min() >= 0 and ns.max() <= 1 and na.min() >= 0 and na.max() <= 1


def test_reproduce_follows_income():
    market._seed(4)
    s = np.array([0.0] * 100 + [1.0] * 100)
    inc = np.array([0.0] * 100 + [10.0] * 100)
    ns, _ = market.reproduce(s, s.copy(), inc, 0.0, 0.05, 0.01)
    # floor share for zero-income agents: 100*0.01*mean / total = 0.01*... ~ 0.5% of draws
    assert (ns == 1.0).mean() > 0.97


def test_initial_traits():
    s, a = market.initial_traits("exploiter")
    assert (s == 0.05).all() and (a == 0).all()
    s, a = market.initial_traits("fair")
    assert (s == 0.5).all() and (a == 0.45).all()
    with pytest.raises(ValueError):
        market.initial_traits("x")


def test_no_choice_offers_fall():
    summ, ms, _ = market.run(1, 0.0, "fair", False, 0, gens=300, window=50)
    assert ms[-1] < ms[0] - 0.1


def test_x_star_prefix_rule():
    c = {("choice", "exploiter", 0.0, T): [0.5] * k + [0.1] * (20 - k)
         for T, k in zip(analyze.TS, (20, 16, 10, 20, 20))}
    assert analyze.x_star(c, "exploiter", 0.0) == 0.05
    c[("choice", "exploiter", 0.0, 1)] = [0.1] * 20
    assert analyze.x_star(c, "exploiter", 0.0) is None


def test_breakup_with_hare_income_is_conserved():
    # Codex P1: a break-up must not also pay the higher-id member h in the same round
    inc, st = _gen(np.array([0.1, 0.1]), np.array([0.2, 0.2]), 1.0, 0.3, 1, True)
    assert inc.sum() == pytest.approx(1.0)
    n, rounds, h = 30, 40, 0.3
    rng = np.random.default_rng(7)
    inc, st = _gen(rng.random(n), rng.random(n), 0.4, h, rounds, True)
    assert st[4] > 0
    assert inc.sum() == pytest.approx(st[0] + (n * rounds - 2 * st[0]) * h)


def test_receiver_threshold_not_catcher_controls_leaving():
    # agent 0 offers 0.1 and accepts anything; agent 1 offers 0.7 and needs 0.5
    breaks_when_0_catches = 0
    for seed in range(200):
        inc, st = _gen(np.array([0.1, 0.7]), np.array([0.0, 0.5]), 1.0, 0.0, 1, True, seed=seed)
        caught_by_0 = inc[0] == pytest.approx(0.9)
        assert st[4] == (1 if caught_by_0 else 0)
        breaks_when_0_catches += caught_by_0
    assert 60 < breaks_when_0_catches < 140  # catcher drawn with probability 1/2


def test_window_is_last_generations():
    summ, ms, _ = market.run(5, 0.1, "random", True, 2, gens=50, window=10)
    assert summ["partner_share"] == pytest.approx(ms[40:].mean())


def _rows(share=0.1, gens=2000, drop=False, dup=False):
    rows = []
    for arm in analyze.ARMS:
        for st in analyze.STARTS:
            for h in analyze.HS:
                for T in analyze.TS:
                    for seed in analyze.SEEDS:
                        rows.append({"arm": arm, "start": st, "h": h, "T": T, "seed": 0 if dup else seed,
                                     "gens": gens, "partner_share": share})
    return rows[:-1] if drop else rows


def test_check_rejects_bad_datasets():
    assert analyze.check(_rows()) == []
    assert analyze.check(_rows(drop=True))
    assert analyze.check(_rows(dup=True))
    assert analyze.check(_rows(gens=30))
    assert analyze.check(_rows(share=float("nan")))


def test_verdict_precedence():
    rows = _rows(share=0.1)
    c = analyze.cells(rows)
    assert analyze.verdict(c) == "KILL"
    for k in list(c):
        if k[0] == "choice" and k[1] == "fair":
            c[k] = [0.5] * 20
    assert analyze.verdict(c) == "MARGINAL"
    for k in list(c):
        if k[0] == "choice" and k[1] == "exploiter":
            c[k] = [0.5] * 20
    assert analyze.verdict(c) == "PASS"
    c[("no_choice", "fair", 0.0, 1)] = [0.3] * 20
    assert analyze.verdict(c) == "V1 FAILED: inspection pending"
    assert analyze.verdict(c, v1_final=True) == "INVALID"


# --- reputation step (PREREG_REPUTATION.md) ---

def test_refusal_needs_known_reputation_and_q():
    # agent 0 stingy (s=0), agent 1 fair and choosy (a=0.45); T=1
    s, a = np.array([0.0, 0.5]), np.array([0.0, 0.45])
    # q=1: the first pair always forms (reputations unknown); once 0 has caught, 1 leaves and every later
    # candidate pair is refused, so exactly one pair ever forms and refusals fill the remaining rounds
    for seed in range(50):
        inc, st = _gen(s, a, 1.0, 0.0, 20, True, seed=seed, q=1.0)
        assert st[8] == 1
        assert st[8] + st[9] == st[0] - (st[0] - 1) + st[9]  # one spell
        assert st[9] == 20 - st[0]
    # no-choice: q ignored inside generation() too
    i1, s1 = _gen(s, a, 1.0, 0.0, 20, False, seed=2, q=1.0)
    i0, s0 = _gen(s, a, 1.0, 0.0, 20, False, seed=2, q=0.0)
    assert np.array_equal(i1, i0) and s1[9] == 0
    inc, st = _gen(s, a, 1.0, 0.0, 20, True, seed=1, q=0.0)
    assert st[9] == 0


def test_refused_stingy_agent_earns_h_after_being_known():
    s, a = np.array([0.0, 0.5]), np.array([0.0, 0.45])
    inc, st = _gen(s, a, 1.0, 0.3, 200, True, seed=3, q=1.0)
    # after its first catch, agent 0 is always refused: at most a few paired rounds, then h every round
    assert st[0] < 20
    assert st[9] > 150
    assert inc.sum() == pytest.approx(st[0] + (2 * 200 - 2 * st[0]) * 0.3)


def test_q_zero_reproduces_earlier_screen_exactly():
    from pathlib import Path
    d = Path(market.__file__).resolve().parent / "data" / "screen_traj.npz"
    if not d.exists():
        pytest.skip("baseline data not present")
    old = np.load(d)
    for T, h, st, seed in ((5, 0.1, "fair", 3), (1, 0.0, "random", 7)):
        _, ms, ma = market.run(T, h, st, True, seed, q=0.0)
        assert np.array_equal(ms.astype(np.float32), old[f"{T}_{h}_{st}_choice_{seed}_s"])
        assert np.array_equal(ma.astype(np.float32), old[f"{T}_{h}_{st}_choice_{seed}_a"])


def test_no_choice_ignores_q():
    a1 = market.run(5, 0.1, "random", False, 4, gens=40, window=10, q=1.0)
    a2 = market.run(5, 0.1, "random", False, 4, gens=40, window=10, q=0.0)
    assert np.array_equal(a1[1], a2[1]) and a1[0]["q"] == 0.0


def test_reputation_q_star_suffix_rule():
    from ecological_models.partner_choice_fairness import analyze_reputation as ar
    def rows(k):
        return [{"partner_share": 0.5}] * k + [{"partner_share": 0.1}] * (20 - k)
    c = {("choice", q, "exploiter", 0.0, 5): rows(k) for q, k in zip(ar.QS, (0, 20, 10, 16, 20))}
    assert ar.q_star(c, "exploiter", 0.0, 5) == 0.75
    c[("choice", 1.0, "exploiter", 0.0, 5)] = rows(15)
    assert ar.q_star(c, "exploiter", 0.0, 5) is None
