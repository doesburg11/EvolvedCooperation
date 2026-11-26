# Indirect reciprocity threshold model: discriminators against defectors (`q > c/b`)

**Status (2026-11-26):** pre-registration written and committed before any model code or run, at the user's request
(fourth minimal threshold model). No Codex review.
**Result: reproduced** (direction in all far cells, size in 12/12 cells, rare discriminator declines in 12/12).
Details in [`RESULTS.md`](RESULTS.md).

## Question

In a well-mixed population playing one-shot donation games, do discriminators (who help only those not known to
be defectors) resist invasion by Always-Defect exactly when the probability `q` of knowing a recipient's reputation
exceeds `c/b` (Nowak 2006), and does a rare discriminator fail to spread for every `q` below about 0.98?

## Model (Nowak 2006, the simplest form of indirect reciprocity)

- **Population.** `N` = 1,000, well mixed, two strategies: discriminator (DISC) and Always-Defect (ALLD); haploid, no
  mutation, non-overlapping generations.
- **Encounters.** Every ordered pair meets once per generation, the first as donor and the second as recipient, so
  every individual is donor once to everyone and recipient once from everyone. Helping costs the donor `c` and gives
  the recipient `b`.
- **Reputation.** An individual's reputation is good if it helps and bad if it does not: DISC are good, ALLD bad. In
  each encounter, a DISC donor knows the recipient's reputation with probability `q` (independently per encounter);
  it helps a recipient known to be bad only if it does not know, and always helps a good recipient. ALLD never helps.
  So DISC-DISC pairs help each other every time; a DISC donor helps an ALLD recipient with probability `1 − q`.
- **Fitness and reproduction.** As in `direct_reciprocity_tft/`: `f = 1 + s·π̄`, `π̄` = payoff over all encounters
  divided by `N − 1`, `s` = 0.1; Wright-Fisher, next-generation ALLD binomial with the ALLD share of total fitness.

## Theory

With `n` ALLD: `π̄_ALLD = b·(1 − q)(N − n)/(N − 1)` and `π̄_DISC = [(b − c)(N − n − 1) − c(1 − q)·n]/(N − 1)`.
ALLD does better exactly when `q < q*(n)` with

**`q*(n) = 1 − (b − c)(N − n − 1)/(b(N − n) + c·n)`** → **`c/b`** as `N → ∞`, `n/N → 0`.

This is the same expression as `w*` in `direct_reciprocity_tft/`: in Nowak's (2006) simplest forms, the probability of
another round (`w`) and of knowing a reputation (`q`) enter the payoff comparison in the same way, so the two
thresholds coincide. The mechanisms differ (a defector is punished by the partner it exploited, or by others who
know its reputation), and so does the randomness: here each DISC-ALLD encounter is a coin flip with probability
`1 − q`, and DISC-DISC payoffs are fixed. With `n` = 10: `q*` = 0.3362 (`b` = 3) and 0.5030 (`b` = 2). A rare DISC
(`m` = 10) does better only if `q > 1 − (m − 1)(b − c)/(b·m + c(N − m))`: 0.9824 (`b` = 3), 0.9911 (`b` = 2).

**One-generation prediction:** as in `direct_reciprocity_tft/`, from the expected payoffs.

## Cells, runs, Stage 0, tests (all fixed now)

The same as in `direct_reciprocity_tft/README.md`, with `q` in place of `w` and DISC in place of TFT:

| Series | `b` | `c` | `q*` (`n` = 10) | `q` |
| --- | --- | --- | --- | --- |
| B3 | 3 | 1 | 0.3362 | 0.15, 0.25, 0.30, 0.375, 0.45, 0.55 |
| B2 | 2 | 1 | 0.5030 | 0.30, 0.40, 0.45, 0.55, 0.60, 0.70 |

- Far cells (`|q − q*|` ≥ 0.05): B3 0.15, 0.25, 0.45, 0.55; B2 0.30, 0.40, 0.45, 0.60, 0.70.
- Runs: 20,000 one-generation runs per cell from 10 ALLD (seed `110,000,000 + 100,003·i + j`) and from 10 DISC
  (seed `130,000,000 + 100,003·i + j`); 40 runs of 100 generations from 10 ALLD (seed `150,000,000 + 1,009·i + j`).
- Stage 0: tests (closed-form payoffs equal encounter-by-encounter play on a small population; the mean number of
  helped ALLD recipients matches `1 − q`; payoffs equal at `q*`; share and absorbing-state checks; same seed, same
  run) and a timing benchmark with the 5-hour rule.
- **D1** (direction, far cells, 99% t-interval of mean `Δx` for rare ALLD on the predicted side), **D2** (predicted
  change inside the 99% interval in at least 10 of 12 cells), **D3** (rare DISC: 99% interval of mean `Δx` below 0 in
  all 12 cells). **Verdict: reproduced** if all three hold.

## Predictions (mine, before any code)

D1: 95%. D2: 85%. D3: 99%. (The direct-reciprocity run with the same numbers was seen before this was written:
D1, D2 11/12 and D3 held there.)

## Limits

The reputation rule is the simplest one ("bad" = ALLD, known with probability `q`), with no errors, no
second-order assessment and no cost of observation. It shows the threshold in the form Nowak states, and that a rare
discriminator cannot get started below `q` ≈ 0.98; the site's `well_mixed_binary/` model and the stricter
assessment rules in the literature (Ohtsuki and Iwasa 2004) go beyond it.

## References

- Nowak, M. A. (2006). Five rules for the evolution of cooperation. *Science*, 314(5805), 1560-1563.
- Nowak, M. A., and Sigmund, K. (1998). Evolution of indirect reciprocity by image scoring. *Nature*, 393, 573-577.
- Ohtsuki, H., and Iwasa, Y. (2004). How should we define goodness? Reputation dynamics in indirect reciprocity.
  *Journal of Theoretical Biology*, 231, 107-120.
