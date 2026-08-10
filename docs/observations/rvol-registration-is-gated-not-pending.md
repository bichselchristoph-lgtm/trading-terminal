---
recorded: 2026-08-09
recorded_by: Claude Code, during a staleness audit of handoff/README.md
status: OBSERVATION_VERIFIED_AND_GATED
review_trigger: volume_curve_transfer_tested_against_phase_3_data
review_trigger_kind: gate
review_trigger_note: >
  Doubly blocked. The gate needs phase-3 tick data to be testable, and phase 3
  is halted -- see handoff/phase-3-halted.md. Nothing here is actionable until
  BOTH the halt is lifted and the hypothesis is tested. Neither is a Claude
  Code decision.
---

# DO NOT REGISTER `rvol_vs_curve`. It is gated, not pending.

**Read the prohibition before the gap below.** The gap is real and it looks
exactly like a small piece of tidying that has been overlooked. It is not. The
order of these two sections is deliberate: a note that opened with "these
indicators are unregistered" would be actioned on a quiet afternoon by someone
being helpful, and that action breaches a pre-registration gate.

## The prohibition

`rvol_vs_curve` **must not be added to the registry as a scored entry.**

`harness/config/preregistration.yaml` (hypothesis `volume_curve_transfer`,
around line 959) carries `status: NOT_YET_TESTED` and blocks:

```
- any_report_of_rvol_vs_curve_as_a_measurement
- any_threshold_set_on_rvol_vs_curve
```

Registering it with `scored=True` puts it into the composite score. **That is
reporting it as a measurement.** The gate does not need to be mentioned by name
for it to be breached; it is breached by the registration itself.

Why the hypothesis is doubted, in one line: the volume curve it divides by is a
generic US-equity anchor set whose own source module called itself a
placeholder, calibrated on three mega-cap ETFs, and phase 3 runs on 1,706
mostly small- and mid-cap single names. Two hardcoded curves for the same
measure already existed in this workspace and they **cross** rather than
offset — a name reading 5.00 on one reads 5.45 or 4.25 on the other depending
on the clock. Until that is measured against real phase-3 data, `rvol_vs_curve`
may be an artefact of the prior rather than a measurement of participation, and
nothing may report it as the latter.

**`rvol_vs_trailing` is deliberately exempt.** It needs no shape prior at all,
which is precisely why the two exist as separately named functions rather than
as one function with a flag. The preregistration's own `if_it_fails` path names
`rvol_vs_trailing` as the measure that takes over if the curve fails.

## The gap

Verified 2026-08-09 by direct inspection:

- `core/indicators/rvol.py` defines `rvol_vs_curve` and `rvol_vs_trailing` with
  **neither `@signal` nor `REGISTRY.register`**.
- `core/indicators/magnitude.py` and `core/indicators/vwap.py` register theirs
  with `@signal`; `core/indicators/structural.py` uses `REGISTRY.register`.
  So the omission in `rvol.py` is genuinely an omission in shape, not a
  different registration style used consistently.
- `handoff/done/001-rvol-vs-trailing.md` is the task these came from.
  `handoff/README.md` previously described the remaining work as "registry
  conformance — the `@signal` declaration itself", with no mention of the gate.
  That sentence is what this observation exists to replace; it was removed on
  2026-08-09.

The accurate statement of the gap is therefore split:

| Function | State |
|---|---|
| `rvol_vs_curve` | unregistered, and **must stay** unregistered until the gate clears |
| `rvol_vs_trailing` | unregistered, and not gated — but see below before acting |

## What would settle it

For `rvol_vs_curve`: the test declared in `volume_curve_transfer` — compute the
empirical cumulative-volume fraction by time of day across phase-3 training
rows and compare against the registered curve, with the failure threshold
already declared before the data exists. That requires phase-3 tick data, and
**phase 3 is halted**.

For `rvol_vs_trailing`: nothing blocks its registration on
pre-registration grounds. But registering one half of a deliberately-paired
set, while its twin is held back by a gate, changes what the composite contains
without anyone deciding the composite should change. That is a decision, not a
choice — it belongs in `handoff/questions/` before it belongs in code.

## Why this is not filed as a task

Because the next reader's correct default action is **to leave it alone**, and
an inbox item communicates the opposite. An observation that produces no action
is the intended outcome here.
