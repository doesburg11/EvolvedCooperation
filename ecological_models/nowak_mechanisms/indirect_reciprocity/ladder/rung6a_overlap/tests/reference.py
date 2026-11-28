"""Independent plain-Python reference for rung 5c's partial-empathy assessment (no shared code with the model).
views[(w, t)] is observer w's view of target t (True = good). An empathetic observer judges an unhelped act by the
donor's pre-act view of the recipient, the others by their own; then flips."""


class PartialEmpathyViews:
    def __init__(self, n):
        self.n = n
        self.views = {(w, t): True for w in range(n) for t in range(n) if w != t}
        self.counts = {"consult_disc": 0, "consult_good": 0, "helps": 0, "observations": 0, "flips": 0,
                       "intent_refusals": 0, "intent_refusal_obs": 0, "intent_refusal_obs_recgood": 0,
                       "shuffled_refusal_obs": 0, "shuffled_refusal_obs_recgood": 0, "exec_fail": 0,
                       "allc_intends": 0, "disc_turns": 0, "empathetic_obs": 0}
        self._refusal = False
        self._shuffled = False

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

    def assess(self, donor, recipient, helped, observers, flipped, empathetic):
        donor_view = self.views[(donor, recipient)]
        own = {w: self.views[(w, recipient)] for w in observers}
        c = self.counts
        c["observations"] += len(observers)
        c["flips"] += len(set(flipped) & set(observers))
        c["empathetic_obs"] += len(set(empathetic) & set(observers))
        if self._refusal:
            key = "shuffled_refusal_obs" if self._shuffled else "intent_refusal_obs"
            c[key] += len(observers)
            c[key + "_recgood"] += sum(own[w] for w in observers)
        for w in observers:
            assert w not in (donor, recipient)
            used = donor_view if w in empathetic else own[w]
            good = helped or not used
            if w in flipped:
                good = not good
            self.views[(w, donor)] = good
