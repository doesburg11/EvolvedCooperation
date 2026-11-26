"""Independent plain-Python reference for rung 5a's private assessment (README.md, "Rung 5a"), for scripted tests.

views[(w, t)] is observer w's view of target t (True = good); all good at the start.
"""


class PrivateViews:
    def __init__(self, n):
        self.n = n
        self.views = {(w, t): True for w in range(n) for t in range(n) if w != t}
        self.counts = {"consult_disc": 0, "consult_good": 0, "helps": 0, "observations": 0, "flips": 0,
                       "intent_refusals": 0, "intent_refusal_obs": 0, "intent_refusal_obs_recgood": 0,
                       "exec_fail": 0, "allc_intends": 0, "disc_turns": 0}

    def decide(self, strategy, donor, recipient, consulted, failed, shuffled_target=None):
        """Returns (intends, helped). strategy in {'ALLC', 'DISC', 'ALLD'}."""
        c = self.counts
        self._refusal = False
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

    def assess(self, donor, recipient, helped, observers, flipped, image=False):
        before = {w: self.views[(w, recipient)] for w in observers}
        c = self.counts
        c["observations"] += len(observers)
        c["flips"] += len(set(flipped) & set(observers))
        if getattr(self, "_refusal", False):
            c["intent_refusal_obs"] += len(observers)
            c["intent_refusal_obs_recgood"] += sum(before[w] for w in observers)
        for w in observers:
            assert w not in (donor, recipient)
            good = helped if image else (helped or not before[w])
            if w in flipped:
                good = not good
            self.views[(w, donor)] = good
