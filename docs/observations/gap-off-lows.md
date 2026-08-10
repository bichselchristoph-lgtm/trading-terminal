---
recorded: 2026-08-07
status: OBSERVATION_UNVALIDATED
review_trigger: phase_3_gate_cleared
review_trigger_kind: gate
review_trigger_note: >
  Not a calendar date. This cannot be tested before the phase-3 sample exists,
  so a date would be theatre -- it would come due while the thing that decides
  it is still unavailable.
---

# OBSERVATION — Gap-Off-Lows: a candidate sub-population distinct from EP

Recorded 2026-08-07. Status: OBSERVATION, unvalidated. Read from charts by eye.
A hypothesis to be tested against the sample, **NOT a finding and NOT a
playbook**.

Review trigger: the phase-3 gate clearing. Not a calendar date — this cannot be
tested before then.

## The case that prompted it

MSFT daily. Long advance to ~550, rolling top through ~510-530, sustained
decline to ~355 with MAs crossing down and stacking bearishly, then an earnings
gap from ~430 to ~500 on visibly heavy volume, closing near the highs.

## Why it is not an EP as the playbook defines one

1. **No base.** The pre-gap consolidation is a few weeks of chop *within a
   downtrend*, after a ~35% decline. VCP and EP both want a constructive base
   preceded by a genuine uptrend. This is a bounce off lows.
2. **Immediate overhead supply.** ~510-530 is where the top formed and where
   trapped stock sits. Price at ~500 has perhaps 2-6% before reaching the
   heaviest resistance on the chart.
3. **MA stack still wrong.** The 200-day is flat-to-declining and price has just
   crossed it from below; it has not turned up. Qullamaggie EPs generally want
   the longer MAs already rising.

## What is constructive about it

Large gap, volume confirms, decisive clearing of the 200-day, close near the
highs. Real demand, not drift. The point is not that the pattern is bad — it is
that it is a DIFFERENT pattern, and forcing it through the EP playbook means
calibrating on a mixed population.

## The contrasting case

SNOW daily, same session. Base through April-May at ~140-160, an earnings gap in
early June clearing the whole MA stack, a tight consolidation at ~230-250
holding above a rising 10/20, then a steady advance to ~318. MAs properly
stacked and rising, 200-day turned up, RS above 1.0 and trending. At new highs —
no overhead supply. Extended (~318 against a 10-day near 290), which affects
sizing, not classification.

The pair is useful because the two charts differ on exactly the two variables
the hypothesis names: prior-trend direction, and presence of overhead supply.
Two charts is not evidence; it is the right pair to hold in mind when
classifying the sample.

## The hypothesis to register

"Big gap, no base, into overhead supply" may be a distinct sub-population with
its own excursion distribution — plausibly a sharp initial move that stalls into
the supply shelf.

Testable form: among gap candidates, does the presence of (a) a prior downtrend
rather than a base, and (b) overhead supply within N% of the entry, change the
forward excursion distribution over the playbook's declared horizon?

## What would decide it, and what will not

Will NOT decide it: more chart reading. This note exists because the eye and the
checklist can diverge here, and neither is calibrated.

WILL decide it: classifying the phase-3 sample rows on the two conditions and
comparing excursion distributions. Both are computable from bars already on
hand — prior-trend direction from the pre-gap window, overhead supply from prior
swing highs within a distance band. Neither needs ticks.

## Cross-references

- Tenet 3: this is an OBSERVATION. It does not become a claim until measured.
- Tenet 4: if tested, the hypothesis and its direction are registered in
  `config/preregistration.yaml` BEFORE the classification runs.
- Amdt 2: the universe already admits a separate playbook for a distinct
  population (liquid ETFs). Same mechanism applies if the distributions differ.
- Sample bound is CLOSED (commit d099a7b, 2,000 symbol-days). This is a new READ
  of the existing sample, not a reason to re-draw it.

> **Correction on ingestion, 2026-08-07.** The cross-reference above cites the
> **superseded** bound. Commit `d099a7b` registered phase-3 bound **v1** — 2,000
> symbol-days drawn from the whole population, seed 20260805, with ~2,048 held
> as a reserve. That was superseded by **v2** on 2026-08-06 because the holdout
> boundary was declared after it, leaving only 969 of those rows available for
> fitting. The bound now in force:
>
> ```
> training  2024-08-01..2025-07-31   1,943 rows, taken WHOLE, no sampling
> holdout   2025-08-01..2026-07-31   1,200 drawn of 2,105, seed 20260806
> ```
>
> The reserve concept is dissolved. **The observation's point is unaffected and
> arguably strengthened**: this is a new READ of an existing sample, not a
> reason to re-draw, and under v2 the training set is taken whole so there is no
> draw to reopen. Only the number and the commit reference were stale.

## Status

Not a playbook. Not a filter. Not a rule. An observation with a testable form
attached, parked until the phase-3 gate is cleared.
