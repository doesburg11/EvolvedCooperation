import numpy as np
import pytest

from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5a import model as old
from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5b import model as new


ARGS = (0.8, 0.5, 0.1, 0.02, 0.001, (0.1, 0.8, 0.1))


def test_no_gossip_exactly_replays_rung5a():
    before = old.run(*ARGS, old.TEST, 17, gens=5, n=60, every=5)
    replay = new.run(*ARGS, new.NO_GOSSIP, 17, gens=5, n=60, every=5)
    assert np.array_equal(before[0], replay[0])
    assert np.array_equal(before[1], replay[1])
    assert np.array_equal(before[2], replay[2][:old.NST])
    assert np.array_equal(before[3], replay[3][:old.NST])
    assert not replay[2][old.NST:old.NST + 3].any()


def test_gossip_has_eligible_attempts_and_accounting():
    n, gens = 40, 3
    _, _, stats, gen1 = new.run(*ARGS, new.TARGET_GOSSIP, 3, gens=gens, n=n, every=gens)
    s = stats + gen1
    attempts, changes, noops = s[28:31]
    assert attempts + 1e-9 >= changes + noops
    assert attempts <= gens * (n - 1) * (n - 2)
    assert changes + noops <= attempts
    assert attempts > 0


def test_sham_and_target_use_registered_copy_rate():
    n, gens = 50, 2
    _, _, target, target_g1 = new.run(*ARGS, new.TARGET_GOSSIP, 9, gens=gens, n=n, every=gens)
    _, _, sham, sham_g1 = new.run(*ARGS, new.SHAM_GOSSIP, 9, gens=gens, n=n, every=gens)
    eligible = gens * (n - 1) * (n - 2)
    for stats in (target + target_g1, sham + sham_g1):
        assert abs(stats[28] / eligible - new.Q_GOSSIP) < 0.04


def test_gossip_preserves_self_views_and_audits_every_update():
    n = 16
    views = np.ones((n, n), np.uint8)
    np.fill_diagonal(views, 0)
    stats = np.zeros(new.NST)
    new.gossip(views, new.TARGET_GOSSIP, np.uint64(19), stats)
    assert not np.diag(views).any()
    assert stats[28] == stats[29] + stats[30]


def test_gossip_accounting_detects_corruption():
    from ecological_models.nowak_mechanisms.indirect_reciprocity.ladder.rung5b import run
    counts = np.zeros((run.GENS + 1, 2), np.int32)
    counts[:, 0] = 100
    audit = np.zeros((run.GENS, 10), np.int32)
    audit[:, 1] = run.N
    audit[:, 9] = run.N * run.K
    row = dict(check_mismatch=0, sanity_violations=0, gossip_attempts=2, gossip_changes=2, gossip_noops=1,
               encounters=float(run.N * run.K * run.GENS), helps=0, observations=0, flips=0)
    with pytest.raises(ValueError, match="gossip accounting"):
        run.validate_one(row, counts, audit)
