# Relatedness With Nowak's Five Mechanisms

This note maps the current `EvolvedCooperation` models onto Martin Nowak's
five canonical mechanisms for the evolution of cooperation, then places the
repo's broader feedback framing beside mechanisms that are not captured cleanly
by the five-part taxonomy.

Nowak's five mechanisms are:

1. **Kin selection**: cooperation is favored when help is directed toward
   genetic relatives strongly enough that indirect genetic benefits outweigh
   private costs.
2. **Direct reciprocity**: cooperation is favored when repeated encounters let
   agents condition behavior on a partner's previous actions.
3. **Indirect reciprocity**: cooperation is favored when agents use reputation,
   observation, or social information about third-party behavior.
4. **Network reciprocity**: cooperation is favored when population structure
   makes cooperators interact with other cooperators more often than random
   mixing would allow.
5. **Group selection**: cooperation is favored when more cooperative groups
   outcompete less cooperative groups strongly enough to overcome within-group
   exploitation.

The five mechanisms are a useful compact framework, but they are not an
exhaustive list of every route to cooperation. They are best treated as a
canonical evolutionary game theory taxonomy, not as a complete ontology.

## Model Mapping

| Model | Primary Nowak mechanism | Secondary or adjacent mechanisms | Not implemented |
| --- | --- | --- | --- |
| `ecological_models/spatial_altruism/` | Network reciprocity | Group-selection-adjacent spatial patch effects | Direct reciprocity, indirect reciprocity, explicit kin selection |
| `ecological_models/spatial_prisoners_dilemma/` | Direct reciprocity and network reciprocity | Local assortment through lattice position | Indirect reciprocity, explicit kin selection, explicit group reproduction |
| `ecological_models/cooperative_hunting/` | Not a clean single Nowak mechanism | Network reciprocity, byproduct mutualism, partner-like ecological feedback, group-benefit effects | Reputation-based indirect reciprocity, explicit kin selection |
| `ecological_models/retained_benefit/` | Generalized assortment and feedback, not a clean single Nowak mechanism | Kin-selection-like lineage routing, network reciprocity through local neighborhoods | Memory-based direct reciprocity, reputation-based indirect reciprocity |
| `moran_models/interaction_kernel/` | General interaction-kernel engine, not a clean single Nowak mechanism | Can instantiate kin-weighted routing, network-local routing, mixed help-harm effects, and retained-feedback-like special cases | Mechanism-specific memory, reputation, and partner-tracking rules unless added as kernels or wrappers |

The five explicit Moran wrapper implementations for Nowak's canonical
mechanisms live under `moran_models/nowak_mechanisms/`. The shared reusable
engine and comparison utilities remain in `moran_models/interaction_kernel/`.

## Spatial Altruism

`ecological_models/spatial_altruism/` is the repo's clearest example of **network reciprocity**.
The model places altruist, selfish, and empty sites on a lattice. Altruists pay
a private cost and distribute benefit through a local five-site von Neumann
neighborhood. Replacement is also local: the next occupant of a site is drawn
from local altruist, selfish, and void lottery weights.

The key cooperation-preserving structure is spatial assortment. Altruists can
benefit nearby altruists, and local clusters can resist immediate invasion
better than isolated altruists in a well-mixed population.

The model is only **group-selection-adjacent**. Local neighborhoods can behave
like small competing patches, especially under disturbance and recolonization,
but the implementation does not define explicit groups with group-level birth,
death, fission, or migration.

It does not implement:

- **direct reciprocity**, because sites do not remember partners or condition
  future behavior on previous interaction history
- **indirect reciprocity**, because there is no reputation or observation of
  third-party behavior
- **explicit kin selection**, because there is no relatedness coefficient,
  pedigree, lineage identity, or kin recognition

## Spatial Prisoner's Dilemma

`ecological_models/spatial_prisoners_dilemma/` combines **direct reciprocity** and **network
reciprocity** more strongly than `ecological_models/spatial_altruism/`.

It is direct-reciprocity-like because agents carry inherited strategies for
pairwise Prisoner's Dilemma interactions, including conditional same-vs-other
response rules. The model is local and repeated over time, so strategy success
depends on interaction outcomes and future demographic consequences.

It is also network-reciprocity-like because agents interact only with local
Moore-neighborhood neighbors on a grid. Cooperators or conditional reciprocators
can benefit from local spatial assortment rather than facing a fully mixed
population.

It does not implement indirect reciprocity, because agents do not use global
reputation or third-party observation. It also does not implement explicit kin
selection, even though local reproduction can create local genetic or strategic
assortment.

## Cooperative Hunting

`ecological_models/cooperative_hunting/` does not map cleanly to one of Nowak's five mechanisms.
It is primarily an ecological synergy model: predators can invest in hunting,
and costly investment can pay when coordinated hunting creates enough prey
capture benefit.

The closest Nowak-adjacent mechanisms are:

- **network reciprocity**, because hunting opportunities and ecological effects
  are spatially local
- **group-selection-adjacent effects**, because groups of hunters can create a
  collective benefit that isolated non-hunters cannot create
- **byproduct mutualism**, because helping in a hunt can directly increase the
  helper's own expected food return when the hunt succeeds
- **partner-like ecological feedback**, because cooperative hunters can support
  local ecological conditions that feed back into future survival and
  reproduction

The active model is not a pure direct reciprocity model. Predators do not track
specific partners and repay past help. It is also not an indirect reciprocity
model, because there is no reputation system.

## Retained Benefit

`ecological_models/retained_benefit/` was added to test a broader condition:

> cooperation evolves when enough of the benefit created by cooperation flows
> back to cooperators, or to copies of the cooperative rule, to outweigh the
> private cost.

This is broader than any single Nowak mechanism. The module abstracts away from
specific stories such as altruism, repeated reciprocity, reputation, and
cooperative hunting. Its central variable is **benefit routing**.

The model is related to several mechanisms:

- **kin-selection-like routing**, because retained benefit can be directed
  toward same-lineage recipients
- **network reciprocity**, because open benefit and replacement operate through
  local neighborhoods
- **assortment**, because cooperation succeeds only when cooperators or their
  copies receive enough of the created benefit
- **ecological or demographic feedback**, because local replacement converts
  current benefit routing into future trait composition

It is not direct reciprocity in the strict Nowak sense, because agents do not
remember individual partners and condition future help on past help. It is not
indirect reciprocity, because there is no reputation or social scoring.

## Interaction Kernel

`moran_models/interaction_kernel/` is the repo's more general abstraction layer. It separates
trait-dependent production, positive and negative effect routing, fitness score
formation, local selection, and inheritance. That makes it the broadest current
kernel-style abstraction in this repo.

Its conceptual role is to isolate the common interaction chain:

1. A trait produces positive effects, negative effects, or both.
2. Explicit kernels route those effects to recipients.
3. Received positive effects, received negative effects, and private costs form
   a fitness or selection score.
4. Local selection and inheritance convert the routed effects into future trait
   and lineage composition.

This can express retained-feedback-like cases, but it can also express broader
mechanism families. For example, a kin-weighted positive kernel creates a
kin-selection-like return path, a uniform local kernel creates a
network-reciprocity-like spatial return path, and a negative kernel can model
harm, punishment, suppression, or other costly interaction channels.

The module is still not a full implementation of every Nowak mechanism by
itself. Direct reciprocity would require partner memory and history-conditioned
behavior. Indirect reciprocity would require reputation, observation, or social
scoring. Partner choice would require endogenous interaction partner selection.
Those can be added as mechanism-specific kernels, state variables, or wrappers
around the core engine.

## Mechanisms Beyond Nowak's Five

Important cooperation mechanisms and refinements outside the strict five-part
Nowak list include:

- **Partner choice**: agents preferentially interact with cooperative or
  productive partners and abandon poor partners.
- **Partner control**: agents alter partner incentives through sanctions,
  punishment, exclusion, or enforcement.
- **Rewarding and incentives**: cooperators receive additional benefits that
  change the payoff balance.
- **Policing**: third parties suppress selfish behavior or stabilize collective
  rules.
- **Byproduct mutualism**: an action benefits others because it directly
  benefits the actor at the same time.
- **Pseudoreciprocity or invested benefits**: an actor benefits another because
  a more productive partner later improves the actor's own payoff.
- **Greenbeard effects**: a recognizable trait marks cooperators and directs
  help toward others carrying the same marker.
- **Niche construction and ecological feedback**: cooperative behavior changes
  the environment, and the changed environment feeds back on selection.
- **Institutional enforcement**: norms, rules, monitoring, and punishment
  stabilize cooperation at social scales.
- **General assortment**: cooperators interact with cooperators more often than
  random mixing predicts, whether caused by kinship, space, partner choice,
  tags, ecology, or institutions.

These mechanisms can overlap. For example, local reproduction can create both
network reciprocity and kin-like assortment. Cooperative hunting can combine
byproduct mutualism, local assortment, and ecological feedback. Retained benefit
can be interpreted as a deliberately abstract version of the same deeper
condition: cooperation needs a feedback path from the value it creates back to
cooperators or to copies of the cooperative rule.

## Repo-Level Summary

The current repo is best understood through the broader feedback framing:

1. Cooperation must vary across agents, sites, or lineages.
2. Cooperative acts must create enough value to matter.
3. Some mechanism must prevent all of that value from leaking randomly to
   defectors.
4. Reproduction, survival, or replacement must convert protected value into
   future cooperative representation.
5. The protected benefit must be large enough to outweigh the private cost.

Nowak's five mechanisms describe several classic ways to satisfy those
conditions. The repo's `ecological_models/retained_benefit/` model and broader
`moran_models/interaction_kernel/` engine make the more general condition explicit:
cooperation spreads only when the model contains enough feedback from
cooperative value creation back to cooperators, relatives, partners, groups, or
copies of the cooperative rule.
