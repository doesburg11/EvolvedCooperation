# External reference code (untracked)

Third-party code kept next to the repo for reference. Everything in this folder except this file is
gitignored, and pytest does not collect it (see `pyproject.toml`).

| Folder | What it is | Used by |
| --- | --- | --- |
| `hammond-axelrod-ethnocentrism/` | NetLogo Ethnocentrism model and Hammond & Axelrod's original Java code, unmodified | `ecological_models/ethnocentrism/` (reference for the port) |
| `viscosity-promotes-altruism/` | Clone of [jkanwal/viscosity-promotes-altruism](https://github.com/jkanwal/viscosity-promotes-altruism): code for Kanwal & Gardner, *Viscosity promotes altruism under density-dependent dispersal* (own `.git`) | reference for `ecological_models/spatial_altruism/` |
| `EcoEvoJax/` | Clone of [flowersteam/EcoEvoJax](https://github.com/flowersteam/EcoEvoJax): eco-evolutionary neuroevolution in large multi-agent environments (own `.git`, about 600 MB) | reference only; not imported |

Moved here from inside the package tree on 2026-11-22, because pytest collected EcoEvoJax's tests and failed.
