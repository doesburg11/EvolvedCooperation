# Group selection threshold model: Traulsen and Nowak (2006) multilevel selection (`b/c > 1 + n/m`) — DRAFT

**Status (2026-11-26): DRAFT, not a pre-registration yet. No code, no runs.** The model's payoff convention inside a
group could not be confirmed from the paper's text in this session (the full text could not be retrieved), so the
cells, tests and theory values below are not fixed. To be completed after reading the paper's model section and
Supporting Text (Eq. 24).

## What is established (from the paper's abstract, Fig. 2 caption and fixation formulas)

- A population of `m` groups; individuals interact within their group in an evolutionary game whose payoff is
  fitness; reproduction is driven by individual fitness. When a group reaches its maximum size `n`, with probability
  `q` it splits in two (members randomly divided) and another group is eliminated; with probability `1 − q` a random
  individual of that group is eliminated. The number of groups stays `m`; the population lies between `m` and `m·n`.
- Weak selection, rare splitting: within-group fixation of one cooperator `ρ_C ≈ (1/n)[1 + (b − cn − c)w/2]`;
  fixation of one cooperator group among `m − 1` defector groups `ρ_C ≈ (1/m)[1 + (b − c)(m − 1)w/2]`. Their product
  exceeds `1/(n·m)` when **`b/c > 1 + n/m`**.
- Finite `m`: simulations at `q` = 10⁻³ and `w` = 0.1 agree with **`b/c > 1 + n/(m − 2)`** (Supporting Text, Eq. 24);
  at `q` = 1 the critical `b/c` is lower.

## Open before this can be pre-registered

1. **Payoff convention.** Whether a member's payoff is summed or averaged over its group mates, and whether the game
   is the donation game (`C` pays `c`, each other member gains `b`) or a payoff matrix applied per pair. With summed
   payoffs, `n` = 10 and `w` = 0.1, a lone cooperator's fitness `1 − w + w·π` would reach 0, which suggests averaged
   payoffs; this must be checked, because the within-group formula above depends on it.
2. **Reproduction step.** Whether the reproducing individual is drawn from the whole population in proportion to
   fitness (as "driven by individual fitness" suggests) and its offspring joins the parent's group.
3. **Which threshold to test.** `1 + n/(m − 2)` (finite `m`, the paper's own simulations) as the primary value, with
   `1 + n/m` as the large-`m` approximation, mirroring the finite-`N` test in `network_reciprocity_lattice/`.
4. **Feasibility.** Fixation with `q` = 10⁻³ is slow (a cooperator group must win about `m` splits, each taking on the
   order of `1/q` full-group events); Stage 0 must benchmark it with a kill rule before any registered run.

## Planned design (to be fixed in the pre-registration)

Fixation probability of a single cooperator among defectors, `ρ_C·n·m` against 1, in cells on both sides of the
finite-`m` threshold for two `(n, m)` combinations, with a direction test in far cells and a location test with
cells close to the threshold, as in `network_reciprocity_lattice/`.

## References

- Traulsen, A., and Nowak, M. A. (2006). Evolution of cooperation by multilevel selection. *Proceedings of the
  National Academy of Sciences*, 103(29), 10952-10955. https://doi.org/10.1073/pnas.0602530103
