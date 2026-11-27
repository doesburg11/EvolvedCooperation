import numpy as np
import pytest

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a import run as r5
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a_nomut import run as nm


def test_settings_applied_and_restored():
    before = (r5.B_, r5.E, r5.Q, r5.SEEDS, r5.CONDITIONS, r5.DATA)
    with nm.configured() as mod:
        js = mod.jobs()
        assert len(js) == 200 and {j[1] for j in js} == {"test", "shuffled"}
        assert sorted({j[2] for j in js}) == list(range(3300, 3400))
        assert mod.CONDITIONS["main"][0] == 0.0 and (mod.B_, mod.E, mod.Q, mod.O, mod.A) == (3.0, 0.1, 0.8, 0.5, 0.02)
        assert mod.DATA == nm.DATA != before[5]
    assert (r5.B_, r5.E, r5.Q, r5.SEEDS, r5.CONDITIONS, r5.DATA) == before


def test_seeds_disjoint():
    earlier = set(range(0, 20)) | set(range(1000, 1100)) | set(range(2000, 2100)) | set(range(3000, 3300))
    assert not (set(nm.SEEDS) & earlier)


def test_short_run_has_no_mutants_and_validates(tmp_path):
    extra = dict(DATA=tmp_path, GENS=6, N=40, G_END=2, WIN=(3, 6), SEEDS=(3300, 3301))
    (tmp_path / "heartbeats").mkdir()
    (tmp_path / "runs").mkdir()
    with nm.configured(extra) as mod:
        outs = [mod.run_one(j) for j in mod.jobs()]
        rows = [o[0] for o in outs]
        keys = [(r["condition"], r["arm"], r["seed"]) for r in rows]
        mod.validate(rows, dict(zip(keys, [o[1] for o in outs])), dict(zip(keys, [o[2] for o in outs])))
    r2, c2, a2 = nm.load_runs(tmp_path)
    assert len(r2) == 4 and nm.mutation_free(r2, a2) and all(r["mu"] == 0.0 for r in r2)
    k = next(iter(a2))
    bad = np.array(a2[k]); bad[0, 3] = 1; a2[k] = bad
    assert not nm.mutation_free(r2, a2)


def test_extinction_and_disc():
    rows = [{"condition": "main", "arm": a, "seed": s} for a in ("test", "shuffled") for s in (1, 2)]
    counts = {}
    for a in ("test", "shuffled"):
        c1 = np.zeros((11, 2), dtype=np.int16); c1[:4, 0] = 5; c1[:, 1] = 20       # ALLD extinct at gen 4
        c2 = np.zeros((11, 2), dtype=np.int16); c2[:, 0] = 5; c2[:, 1] = 20        # never extinct
        counts[("main", a, 1)], counts[("main", a, 2)] = c1, c2
    out, per = nm.extinction_and_disc(rows, counts, n=100, g_end=5, win=(6, 10))
    t = out["test"]
    assert (t["alld_extinct_runs"], t["alld_extinct_gen_median"], t["alld_reappeared_runs"]) == (1, 4.0, 0)
    assert t["mean_disc_g500"] == pytest.approx((0.80 + 0.75) / 2)
    assert per[0]["alld_extinct_gen"] == 4 and per[1]["alld_extinct_gen"] is None
    counts[("main", "test", 1)][7, 0] = 1                                          # reappearance is flagged
    assert nm.extinction_and_disc(rows, counts, 100, 5, (6, 10))[0]["test"]["alld_reappeared_runs"] == 1


def _worker_view():
    from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a import run as m
    return m.CONDITIONS["main"][0], m.SEEDS[0], str(m.DATA)


def test_fork_workers_inherit_settings():
    from concurrent.futures import ProcessPoolExecutor
    with nm.configured():
        with ProcessPoolExecutor(2) as ex:
            got = ex.submit(_worker_view).result()
    assert got == (0.0, 3300, str(nm.DATA))


@pytest.mark.parametrize("col", range(3, 9))
def test_mutation_check_every_column(col):
    rows = [{"condition": "main", "arm": "test", "seed": 1, "mutants_total": 0, "mutants_max_gen": 0}]
    au = np.zeros((5, 10), dtype=np.int32)
    assert nm.mutation_free(rows, {("main", "test", 1): au})
    au[2, col] = 1
    assert not nm.mutation_free(rows, {("main", "test", 1): au})
    au[2, col] = 0
    rows[0]["mutants_total"] = 1
    assert not nm.mutation_free(rows, {("main", "test", 1): au})
