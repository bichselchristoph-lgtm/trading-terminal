---
recorded: 2026-08-07
status: OBSERVATION_RESOLVED_IN_PART
review_trigger: consolidation_step_8
review_trigger_kind: gate
review_trigger_note: >
  Step 8 folds in ibkr_tape_tools, which carries two of the four sites. The
  decision on vwap_breaks (below) is owed BEFORE the phase-3 fit, not before
  step 8, and is flagged separately because it changes a registered indicator.
---

# OBSERVATION — VWAP has no single definition, and one of ours is chosen at runtime

## What was found

Four sites computed something called VWAP. Reading the bodies -- not the
signatures -- showed they were not four attempts at one measure:

| site | form | price input | shape |
|---|---|---|---|
| `core/indicators/magnitude.py:40` `_session_vwap` | series | **switches at runtime** | running cumulative |
| `orb_tools/flag_monitor.py:133` | scalar | `(H+L+C)/3` always | one number |
| `ibkr_tape_tools/tape_reader.py:1652` | property | per-print notional | running |
| `ibkr_tape_tools/tape_reader_v2.py:1238` | property | per-print notional | **byte-identical to the above** |

So: two definitions, one duplicated copy, and one function that is on both
sides of the line.

## The live defect

```python
if "vwap" in bars.columns:
    px = bars["vwap"]          # per-print, exact
else:
    px = (high + low + close) / 3.0    # bar-level approximation
```

`vwap_breaks` -- a registered indicator, one of the ten under test, measured
auction-dependent at 67.3% -- picks its price series by **whether the frame
happens to carry a column**. Production bars have it; hand-built fixtures do
not. So the test suite exercises a different computation from the one that
runs on real data, and neither the call site nor the recorded value says which.

## Why "pick the right one" was the wrong response

IBKR's own VWAP study takes an **anchor**, a smoothing type and a length, set
per chart. Their API serves no indicator at all -- there is no `reqVwap`, and
the only computed quantities are historical/implied volatility and a per-bar
`average`. There was never a canonical definition available to adopt, and
session VWAP is simply the member of the family anchored at the session open.

The parameters none of the four declared:

- **price input** -- per-print notional (exact) vs `(H+L+C)/3` (approximation
  whose error grows with bar range; on a trending bar the true VWAP sits toward
  the end of the range and the typical price at its middle)
- **anchor** -- all four silently meant session open
- **shape** -- running series vs one scalar
- **smoothing / length** -- IBKR offers them; none of ours has them

## What was done

`core/indicators/vwap.py` makes both parameters **required, with no defaults**,
and returns a `VwapSeries` carrying them -- so two series are not comparable
unless the parameters match, the same shape as `Rvol.basis`. A `TRADE_NOTIONAL`
request against a frame with no per-print column **raises rather than falling
back**, because the fallback returns a different measurement under the same
name.

## What is still owed, and is NOT done here

`vwap_breaks` still calls `_session_vwap` and still switches at runtime.
Changing it means changing a **registered** indicator's definition, which is a
`signal_version` bump (v1 -> v2) so stored values do not pool across
definitions. That is a pre-registration decision and belongs to the user, not
to a refactor. Flagged rather than taken.

The question to settle: which price source should `vwap_breaks` declare? The
honest default is `TRADE_NOTIONAL` on production bars, with fixtures rebuilt to
carry the column -- but that changes measured values for an indicator already
in the pre-registration.

## What would decide it

Compare crossing counts for the same sessions under both price sources. If they
agree within noise, the switch was harmless and the bump is bookkeeping. If they
diverge, every `vwap_breaks` value computed so far is a mixture of two measures
and the phase-1 result depends on which frames carried the column. Computable
from bars already on hand; needs no ticks and no spend.
