# Partner Choice and Fair Sharing

A theory screen asking whether **the option to leave a partner can make the catcher of a shared hunt offer
a fair split** (the biological-market account of human fairness: André & Baumard 2011; Debove, André &
Baumard 2015). It comes before any PredPreyGrass module in which hunters learn how to split a catch.

Status (2026-11-26): **screen run, registered verdict KILL** (`RESULTS_SCREEN.md`). With inherited offers and
acceptance thresholds and anonymous random rematching, no choice-arm cell of the registered grid reached the
fairness criterion, from any start including the fair one (no-choice control valid). Descriptively, thresholds
declined before offers when search took time, and with instant rematching offers fell despite constant
break-ups; these readings were not tested. Line
closed by the registered hard stop. Next candidate mechanism: reputation (information about partners before
pairing). Pre-registration: `PREREG_SCREEN.md`.

Run: `./.conda/bin/python -m ecological_models.partner_choice_fairness.run_screen`, then `... .analyze`.

- Step 1: closed form for the least a catcher can offer and keep its partner (done, in the pre-registration).
- Step 2: a small evolving market (inherited offer and acceptance threshold, no learning) over a grid of
  search costs, against a no-choice control. This alone sets the verdict.
- Step 3: descriptive measurements from existing `deer_stag_hunt` checkpoints: do the same hunters meet
  again often enough for partner choice to matter?
