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
  - `spatial_altruism/` in this repo <-> the `spatial_altruism` page/section in `human-cooperation-site`
  - `cooperative_hunting/` in this repo <-> the `cooperative_hunting` page/section in `human-cooperation-site`
- When modifying either Python module here, check whether the corresponding website description must be updated there.
- When modifying the website description there, preserve fidelity to the Python implementation here.

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
