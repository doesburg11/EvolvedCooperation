# Retained Benefit Model

This package adds a more abstract fourth cooperation model to
`EvolvedCooperation`. The point is not to model one special case such as
altruism, reciprocity, or hunting. The point is to test a more general claim:

> cooperation evolves when enough of the benefit created by cooperation flows
> back to cooperators, or to copies of the cooperative rule, to outweigh the
> private cost.

This module therefore treats **benefit routing** as the main variable.

## Why This Module Exists

The other three website-facing modules are useful, but each of them bundles the
cooperation problem into one particular mechanism family:

- `spatial_altruism/` focuses on local altruist benefit, private cost, and
  lattice replacement under void pressure and disturbance
- `spatial_prisoners_dilemma/` focuses on repeated local reciprocity and
  strategy competition
- `cooperative_hunting/` focuses on ecological synergy in predator group hunts

Those models are strong mechanism studies. They are not ideal if the question
is:

> what is the most general condition under which cooperation can spread at all?

This module is an attempt to answer that more directly by stripping away most
special-case story structure and centering one abstract question:

> how much of the value created by cooperation is retained by cooperators or
> their copies, rather than leaking to free-riders?

## What I Just Added Here

This module was created specifically to do a better job than the existing three
models at probing a near-universal cooperation rule.

Concretely, I added:

1. A new package, `retained_benefit/`, with a normal repo-style module entry
   point at `retained_benefit_model.py`.
2. A config-backed runtime in
   `config/retained_benefit_config.py`, so the active config file is the normal
   source of truth just like the newer modules elsewhere in the repo.
3. A synchronous lattice simulation in which every site carries:
   - one inherited cooperation trait `h in [0, 1]`
   - one inherited lineage label
4. A benefit-routing rule that splits cooperative output into:
   - an **open** share that is distributed across the whole local neighborhood
   - a **retained** share that is distributed only among local agents carrying
     the same lineage as the producer
5. A local replacement rule where every site copies one local parent with
   probability proportional to fitness, so successful local lineages and trait
   values can spread spatially.
6. Mutation on the cooperation trait, so the model can evolve continuously
   rather than only switching between fixed discrete strategies.
7. A live Pygame grid viewer in `retained_benefit_pygame_ui.py`, so the model
   can be inspected step by step as a spatial field rather than only through
   summary logs.
8. JSON logging plus a small Matplotlib summary utility, so the model is usable
   both as a live viewer and for headless experiments.

In other words: I kept **inheritance**, **local interaction**, **cost**, and
**selection**, but removed most of the mechanism-specific story of the other
models. That makes this a cleaner test of the statement:

> no cooperation without feedback

## Core Representation

Each lattice site is always occupied by one agent. Each agent carries:

- `h`: a continuous cooperation trait in `[0, 1]`
- `lineage_id`: an inherited lineage label copied under local reproduction

Interpretation:

- higher `h` means the agent creates more cooperative value
- higher `h` also means the agent pays a larger private cost
- `lineage_id` is not meant as a full biological kin model; it is an abstract
  stand-in for “copies of the same rule” or “the same inherited local cluster”

So this module studies the evolution of cooperation under **local copying plus
benefit retention**, not under learning, planning, contracts, or explicit game
memory.

## Benefit Routing Rule

At each step, an agent with cooperation trait `h_i` creates:

<p>B_i = b * h_i</p>

where:

- `b` is `cooperation_benefit`

That output is split into two parts:

<p>B_i^retained = r * B_i</p>
<p>B_i^open = (1 - r) * B_i</p>

where:

- `r` is `retained_benefit_fraction`

Distribution rule:

- the **open** component is shared equally across the full local neighborhood
- the **retained** component is shared only across same-lineage recipients in
  that local neighborhood

Private cost:

<p>C_i = c * h_i</p>

where:

- `c` is `cooperation_cost`

Fitness:

<p>W_i = w_0 + received_open_i + received_retained_i - C_i</p>

where:

- `w_0` is `base_fitness`

This is the whole conceptual point of the module: the key variable is not
“altruism versus selfishness” or “tit-for-tat versus defect,” but **how much of
cooperation’s return is protected from leakage**.

## One Step Of Simulation

The update order is:

1. Each agent produces cooperative value according to its `h`.
2. That value is split into open versus retained components.
3. Open benefit is spread across the full local neighborhood.
4. Retained benefit is spread only to same-lineage recipients in the same local
   neighborhood.
5. Each agent pays the private cooperation cost.
6. Fitness is computed from baseline fitness plus received benefits minus cost.
7. Every site chooses a parent from its local neighborhood with probability
   proportional to local fitness.
8. The chosen parent’s lineage is copied to the next grid.
9. The chosen parent’s cooperation trait is copied with optional Gaussian
   mutation.

So turnover is implemented as a **local replacement lottery** rather than as
explicit death plus birth plus movement.

## Why This Is More General Than The Other Three

This model is not more realistic than the other three. It is more **abstract**.
That is deliberate.

Why it is more suitable for a near-universal cooperation statement:

1. It does not depend on one special ecological story such as predator-prey
   hunting.
2. It does not depend on one special strategic story such as repeated
   Prisoner’s Dilemma memory.
3. It does not depend on one special disturbance story such as void pressure or
   culling, although local spatial clustering still matters.
4. It makes the central question explicit in one parameter:
   `retained_benefit_fraction`.
5. It therefore lets you test a candidate near-law directly:

   cooperation rises when the retained share of cooperative benefit becomes
   large enough relative to its private cost.

In shorthand:

> the more benefit leaks to everybody, the harder cooperation is to sustain  
> the more benefit is routed back to cooperators or their copies, the easier it
> is to sustain

## What To Vary

The most important parameters are:

- `retained_benefit_fraction`
  Main abstraction knob. Higher values mean more cooperative value is protected
  from leakage to unrelated local recipients.
- `cooperation_benefit`
  Scales how much value a unit of cooperation creates.
- `cooperation_cost`
  Scales how much private burden cooperation imposes on the producer.
- `mutation_rate` and `mutation_stddev`
  Control how quickly the cooperation trait can explore the trait space.
- `initial_lineage_block_size`
  Controls how patchy the initial local lineage structure is.

If you want a fast conceptual experiment, start by sweeping:

1. `retained_benefit_fraction`
2. `cooperation_benefit`
3. `cooperation_cost`

That gives the cleanest map of where cooperation collapses, coexists, or rises.

## Package Contents

- `retained_benefit_model.py`
  Main runtime, local benefit routing logic, replacement step, logging, and CLI
  entry point.
- `retained_benefit_pygame_ui.py`
  Live Pygame viewer for the lattice. It can display either cooperation
  intensity or inherited lineage structure.
- `config/retained_benefit_config.py`
  Active runtime configuration and normal source of truth for the run.
- `utils/matplot_plotting.py`
  Matplotlib summary figure for completed runs.

## Quick Start

Run from the repository root:

```bash
./.conda/bin/python -m retained_benefit.retained_benefit_model
```

For the live grid viewer:

```bash
./.conda/bin/python -m retained_benefit.retained_benefit_pygame_ui
```

Normal workflow:

1. Edit `config/retained_benefit_config.py`.
2. Run either the headless model or the Pygame viewer from the repo root.
3. Inspect the terminal summaries, live grid, and optional JSON log.

Viewer controls:

- `Space`: play/pause
- `S` or `Right Arrow`: single step
- `R`: reset
- `V`: toggle between cooperation view and lineage view
- `C`: force cooperation view
- `L`: force lineage view
- `+` / `-`: change playback speed

Default output path:

```text
retained_benefit/data/latest_run.json
```

## What The Default Run Should Be Read As

The default config is not meant as a final scientific claim. It is a clean
demonstration baseline.

Interpret it as:

- a test of whether continuous cooperation can rise under one explicit benefit
  routing rule
- a first probe of how much retained feedback is needed before cooperation is
  no longer swamped by free-rider leakage
- a bridge model between the more specialized modules in this repo

It should not be read as:

- a full kin-selection model
- a full human cooperation model
- a realistic ecology
- a universal proof

## Relation To The Other Modules

- relative to `spatial_altruism/`, this model keeps local inheritance and
  spatial selection but replaces altruist-versus-selfish patch states with a
  continuous cooperation trait and an explicit routing split
- relative to `spatial_prisoners_dilemma/`, this model removes reciprocity
  memory and discrete strategy families so the benefit-feedback structure is
  more exposed
- relative to `cooperative_hunting/`, this model removes prey, grass, and hunt
  coalition mechanics so cooperative synergy is reduced to an abstract routing
  problem

So this module is best understood as a **generalization attempt**, not a
replacement for the richer models.

## Limitations

Important limits:

- lineage is only a simple inherited label, not full kin structure
- there is no movement
- there is no learning, planning, or memory
- there are no explicit empty sites
- replacement is fully synchronous and stylized
- retained benefit is routed by lineage identity, which is only one possible
  abstraction of “copies of the cooperative rule”

That means this module is useful for studying a compact abstract question about
cooperation, but not for claiming realism by itself.
