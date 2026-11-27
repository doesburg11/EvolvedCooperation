"""Independent plain-Python reference for rung 5b's empathetic assessment, for scripted tests (no shared code with the
model). views[(w, t)] is observer w's view of target t (True = good); all good at the start.

Empathetic simple standing: an observer w sets its view of donor d to good if d helped, otherwise good iff d's own
(pre-act) view of the recipient r is bad; then flips it if w is flipped. The donor decides from its own view of r
(shuffled arm: of z). Disagreement counters use the observer's own pre-act view of r.
"""


class EmpatheticViews:
    def __init__(self, n):
        self.n = n
        self.views = {(w, t): True for w in range(n) for t in range(n) if w != t}
        self.counts = {"consult_disc": 0, "consult_good": 0, "helps": 0, "observations": 0, "flips": 0,
                       "intent_refusals": 0, "intent_refusal_obs": 0, "intent_refusal_obs_recgood": 0,
                       "shuffled_refusal_obs": 0, "shuffled_refusal_obs_recgood": 0,
                       "exec_fail": 0, "allc_intends": 0, "disc_turns": 0}

    def decide(self, strategy, donor, recipient, consulted, failed, shuffled_target=None):
        c = self.counts
        self._refusal = False
        self._shuffled = shuffled_target is not None
        if strategy == "ALLC":
            intends = True
            c["allc_intends"] += 1
        elif strategy == "ALLD":
            intends = False
        else:
            c["disc_turns"] += 1
            if not consulted:
                intends = True
            else:
                c["consult_disc"] += 1
                target = recipient if shuffled_target is None else shuffled_target
                intends = self.views[(donor, target)]
                c["consult_good"] += intends
                if not intends:
                    c["intent_refusals"] += 1
                    self._refusal = True
        failed = intends and failed
        c["exec_fail"] += failed
        helped = intends and not failed
        c["helps"] += helped
        return intends, helped

    def assess(self, donor, recipient, helped, observers, flipped):
        donor_view_good = self.views[(donor, recipient)]
        own_before = {w: self.views[(w, recipient)] for w in observers}
        c = self.counts
        c["observations"] += len(observers)
        c["flips"] += len(set(flipped) & set(observers))
        if getattr(self, "_refusal", False):
            key = "shuffled_refusal_obs" if self._shuffled else "intent_refusal_obs"
            c[key] += len(observers)
            c[key + "_recgood"] += sum(own_before[w] for w in observers)
        for w in observers:
            assert w not in (donor, recipient)
            good = helped or not donor_view_good
            if w in flipped:
                good = not good
            self.views[(w, donor)] = good
