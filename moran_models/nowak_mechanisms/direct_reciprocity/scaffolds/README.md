# Direct-Reciprocity Scaffolds

This directory contains experiments that test what can help direct reciprocity
start from rarity.

## Purpose

The main direct-reciprocity result is now clear:

- A single unassorted TFT mutant is weak in an ALLD population.
- A small reciprocal foothold can sometimes cross the basin boundary.
- A reciprocal majority is reliably maintained.

Scaffold experiments should test mechanisms that move a population from the
first case toward the second or third case while keeping direct reciprocity
explicitly present through repeated encounters and partner memory.

## Current Evidence

| Scaffold | Current status | Interpretation |
| --- | --- | --- |
| Small reciprocal foothold | Tested in `../well_mixed/` | Initial frequency helps, but success is stochastic. |
| Spatial clustering | Tested in `spatial_clustering/` | Works because direct reciprocity and network reciprocity act together. |
| Continuous spatial memory | Tested in `continuous_spatial_memory/` | Shows partner-memory help routing inside a local spatial kernel; not a pure well-mixed baseline. |
| Kin assortment | Tested separately in `../../kin_selection/` | Not yet tested as a direct-reciprocity scaffold. |
| Partner choice | Not tested | Candidate scaffold for a new experiment. |
| Reputation-based partner choice | Not tested | Candidate bridge between direct and indirect reciprocity. |

## Candidate Modules

Future modules should live under this directory and keep their own config file
as the source of truth.

| Candidate | Question |
| --- | --- |
| `kin_assorted_pairing/` | Can reciprocal strategies invade when same-lineage agents re-encounter each other more often? |
| `partner_choice/` | Can agents avoid defectors and preferentially keep reciprocal partners? |
| `reputation_partner_choice/` | Can observed behavior create enough assortment for direct reciprocity to start? |
| `group_seeded_pairs/` | Can group-level seeding create reciprocal footholds that direct reciprocity then maintains? |

Each scaffold should report the same three roles used by the main README:

- `single_tft_invader` or equivalent origin-from-rarity test
- small reciprocal foothold amplification test
- reciprocal-majority maintenance test

This keeps origin, amplification, and maintenance separate.
