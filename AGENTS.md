# EvolvedCooperation Agent Instructions

These instructions apply when working in this repository.

## Environment

- Use the project-local Python environment by default:
  - `./.conda/bin/python`
- Prefer running scripts and checks from repo root:
  - `/home/doesburg/Projects/EvolvedCooperation`

## Parameters

- Don't use CLI style parameters
- Use and define parameters inside script

## Configuration Policy

- Use the config file as the single source of truth where practical.
- Avoid runtime overrides, fallback paths, alias layers, and backward-compatibility shims unless explicitly requested.
- Do not add optional `config=...`-style override parameters to runtime functions unless there is a strong reason and the user asks for it.
- Prefer failing fast over silently falling back to alternative behavior.
- When simplifying code, remove unnecessary override or fallback mechanisms instead of preserving them for convenience.

## Cross-Repo Mapping

- This repository (`EvolvedCooperation`) contains the canonical Python implementations for the website models.
- The website `https://humanbehaviorpatterns.org/` is built from the sibling `human-cooperation-site` repo and serves as the documentation/presentation layer for these models.
- Required 1-to-1 mapping:
  - `ecological_models/spatial_altruism/` in this repo <-> the `spatial_altruism` page/section in `human-cooperation-site`
  - `ecological_models/cooperative_hunting/` in this repo <-> the `cooperative_hunting` page/section in `human-cooperation-site`
  - `ecological_models/spatial_prisoners_dilemma/` in this repo <-> the `spatial-prisoners-dilemma` page/section in `human-cooperation-site`
  - `ecological_models/retained_benefit/` in this repo <-> the `retained-benefit` page/section in `human-cooperation-site`
- When modifying a mapped Python module here, check whether the corresponding website description must be updated there.
- When modifying the website description there, preserve fidelity to the Python implementation here.

## Maintenance Notes

### Website-Backed Modules

- `Spatial Altruism` -> `ecological_models/spatial_altruism/altruism_model.py`
- `Cooperative Hunting` -> `ecological_models/cooperative_hunting/cooperative_hunting.py`
- `Spatial Prisoner's Dilemma` -> `ecological_models/spatial_prisoners_dilemma/spatial_prisoners_dilemma.py`
- `Retained Benefit` -> `ecological_models/retained_benefit/retained_benefit_model.py`

### Website Landing Page Note

- On 2026-04-06, the repo-level website root was turned into a multi-demo landing page.
- Stepwise impact:
  - `docs/index.html` now acts as a landing page that lists the available replay demos instead of embedding one specific simulation.
  - The cooperative-hunting browser replay now lives at `docs/cooperative-hunting/index.html`.
  - The spatial-altruism browser replay continues to live at `docs/spatial-altruism/index.html`.
  - The retained-benefit browser replay now also lives at `docs/retained-benefit/index.html`.
  - README links now point directly to each demo route instead of assuming the root site always hosts one specific replay.

### Landing Page Feedback Loop Note

- On 2026-04-10, the landing page gained a conceptual display that clarifies the eco-evolutionary feedback loop around learning and plasticity.
- Stepwise impact:
  - `docs/index.html` now includes a full-width `Why the feedback loop matters` section beneath the demo cards.
  - The new display presents the loop as a four-step sequence: evolution shapes learning capacities, learning reshapes ecological structure, ecological structure reshapes selection gradients, and plasticity closes the loop.
  - The landing page now also contrasts unstable and stable environments so the selection logic behind higher versus lower plasticity is visible at a glance.
  - `docs/style.css` now includes responsive home-page styles for that explanatory display while staying in the existing card-based visual system.

### GitHub Pages Deployment Note

- On 2026-04-06, the repo gained an explicit GitHub Pages deployment workflow for the interactive viewers.
- Stepwise impact:
  - `.github/workflows/deploy-pages.yml` now publishes the repo-level `docs/` site on pushes to `main`.
  - `docs/index.html` now labels the demo entry points as `Open Interactive Viewer` so the viewer routes are explicit.
  - The public routes now include `docs/cooperative-hunting/index.html`, `docs/spatial-altruism/index.html`, and `docs/retained-benefit/index.html`; the workflow only changes how those pages are deployed.
  - If the repository Pages setting is not already using `GitHub Actions`, switch it there so this workflow becomes the active publisher.

### Cooperative Hunting Rename Note

- On 2026-04-06, the package directory for the predator-prey-grass model was renamed from `predpreygrass_cooperative_hunting/` to `ecological_models/cooperative_hunting/`.
- Stepwise impact:
  - The Python package now lives at `ecological_models/cooperative_hunting/`.
  - Module entrypoints now use `./.conda/bin/python -m ecological_models.cooperative_hunting...` from the repo root.
  - Internal asset paths moved from `assets/predprey_cooperative_hunting/` to `assets/cooperative_hunting/`.
  - Utility output paths now write to `ecological_models/cooperative_hunting/images/`.
  - The package rename initially affected the Python/package layer; the public viewer route was renamed separately on 2026-04-07.

### Public Viewer Rename Note

- On 2026-04-07, the cooperative-hunting browser viewer and website slug were renamed from `predator-prey-cooperative-hunting` to `cooperative-hunting`.
- Stepwise impact:
  - The repo-level replay page moved from `docs/predator-prey-cooperative-hunting/index.html` to `docs/cooperative-hunting/index.html`.
  - GitHub Pages links now point to `/cooperative-hunting/`.
  - The `humanbehaviorpatterns.org` page and replay paths now use `/evolved-cooperation/cooperative-hunting/`.
  - The public viewer title and landing-page label now read `Cooperative Hunting`, while the descriptive copy still explains that it is a predator-prey-grass ecology.

### Spatial Prisoner's Dilemma Addition Note

- On 2026-04-17, `ecological_models/spatial_prisoners_dilemma/` was added as a new experimental module in this repository.
- Stepwise impact:
  - The repo now contains a dedicated spatial Prisoner's Dilemma package rather than only a future experiment note.
  - The new module follows the same package-run convention as the newer models: edit the config file, then run it from the repo root with `python -m`.
  - The implementation keeps the external model's central mechanism family: local pairwise PD interactions, fallback movement, local reproduction, inheritance, mutation, death, and a hard population cap.
  - The default world size is reduced so the model remains practical as a pure Python CPU simulation in this repo.
  - The package is canonical on the Python side now and has a matching `human-cooperation-site` page and replay route.

### Spatial Prisoner's Dilemma Website Replay Note

- On 2026-04-18, `ecological_models/spatial_prisoners_dilemma/` gained a frozen website-demo config and replay export pipeline.
- Stepwise impact:
  - `ecological_models/spatial_prisoners_dilemma/config/spatial_prisoners_dilemma_website_demo_config.py` now freezes the public site run.
  - `ecological_models/spatial_prisoners_dilemma/utils/export_github_pages_demo.py` now exports a sampled static replay bundle under `docs/data/spatial-prisoners-dilemma-demo/`.
  - The sibling `human-cooperation-site` repo now has a matching page and replay route at `/evolved-cooperation/spatial-prisoners-dilemma/`.
  - Cross-repo fidelity for this module now includes both the explanatory docs page and the sampled browser replay data bundle.

### Nowak Mechanisms Directory Note

- On 2026-04-27, the five explicit Nowak mechanism Moran wrappers moved under `moran_models/nowak_mechanisms/`.
- Stepwise impact:
  - `moran_models/nowak_mechanisms/direct_reciprocity/`, `moran_models/nowak_mechanisms/group_selection/`, `moran_models/nowak_mechanisms/indirect_reciprocity/`, `moran_models/nowak_mechanisms/kin_selection/`, and `moran_models/nowak_mechanisms/network_reciprocity/` now hold the five wrapper packages.
  - Their module entrypoints now use `./.conda/bin/python -m moran_models.nowak_mechanisms.<mechanism>...`.
  - Their logs and sweep outputs now write under `moran_models/nowak_mechanisms/<mechanism>/`.
  - `moran_models/interaction_kernel/` remains the shared engine and comparison layer.

## Communication Style

- Keep answers concise and technical.
- When the response is substantive (not a one-line factual reply), end with
  `1-3` concrete next-step suggestions as a numbered list.
- When comparing implementations, emphasize meaningful mechanism differences and
  avoid listing trivial incidental differences.
- If a meaninful chance in the code has been made, give a detailed and stepwise update in the accompanied README.md
- If asked to explain something, not only give formulas, but also explain every variable in detail.

## Validation Expectations

- After code edits, run minimal relevant validation where possible (for example
  syntax check and a short smoke run) using `./.conda/bin/python`.
- Report what was run and what could not be run.
