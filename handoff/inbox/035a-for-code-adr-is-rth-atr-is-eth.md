---
id: 035a
title: ADR is RTH, ATR is ETH — read before running 035
type: product
owner: claude-code
depends: 035
---

**Status** WRITTEN

**If `handoff/inbox/035-for-code-every-value-declares-its-session-basis.md` exists in your tree
and has NOT yet been run, this is for you. If `handoff/done/035-*.md` already exists, this
arrived too late — say so and treat it as a correction to apply, not a precondition.**

# 035a — Correcting 035's config block before it lands

**`035` §Part 2 shows `adr: false` and `atr_d14: false` — both extended hours. `adr` is
wrong.** The design session inferred both from `SPEC.md` without checking the definitions
against each other.

**Christoph's ruling, 2026-08-13, and it is definitional rather than a preference:**

| | Measures | Gap term | Basis |
|---|---|---|---|
| **ADR** — Average **Day** Range | mean of each session's own `High − Low` | **none** | **RTH, 09:30–16:00** |
| **ATR** — Average **True** Range | mean of `max(H−L, \|H−Cprev\|, \|Cprev−L\|)` | **yes, spans the prior close** | **ETH, 04:00–20:00** |

**ADR deliberately excludes gaps** — that is what distinguishes it from ATR — so it measures the
range of the session actually traded. **ATR deliberately includes the move across the close**,
so it must be computed on the bar series whose close-to-close relationship is the real one.

```yaml
# config/indicators.yaml — supersedes 035 Part 2 for these two rows
use_rth:
  adr:      true      # Average DAY Range: session high-low only, no gap term.
                      # RTH by definition, not by preference. Will NOT match a
                      # TWS ADR computed over 04:00-20:00 bars, and that is correct.
  atr_d14:  false     # Average TRUE Range: the true range spans the prior close,
                      # so the gap is part of the measurement. ETH.
```

**Every other row in `035` Part 2 is unchanged**, including `prior_day: false` — **PDH and PDL
stay extended hours.** A level is a level because price traded there; 717.37 traded.

---

## What this changes downstream in `035`

**Part 0's table.** `ATR14` at `13.14` is still wrong and still becomes ≈15.61. **`ADR%` was
never shown to be wrong** — it was never externally checked and now, on RTH, it is not expected
to match anything TWS displays.

**Part 3, and this is now the point of the whole task.** ADR and ATR are both labelled
volatility and are computed on different sessions **on purpose**. **Rendering the basis is no
longer a nicety — without it the panel shows two numbers a reader will naturally compare and
must not.**

```
    ADR%      1.63  · 20 sessions, excl. today · 09:30-16:00
    ADR $     11.83  · 20 sessions, excl. today · 09:30-16:00
    ATR14     15.61  · Wilder RMA, n=14 · 04:00-20:00
```

**Part 5's fixture.** Pin `ATR14` on the ETH basis — Christoph's TWS daily ATR(14) reads ≈15.6
and is a real external check. **Do not pin `ADR%` or `ADR $`**: TWS has no native ADR, anything
it shows comes from a different computation over a different bar set, and recording it as
verification would be a check that never happened.

**One test gains a case.** The `use_rth` assertion must prove `adr` and `atr_d14` request
**different** flags. **A config where both are the same value passes trivially** — that is the
inward form of `OBS-037`, and it is the exact defect this correction exists to prevent.

---

## Done when

- `config/indicators.yaml` carries `adr: true`, `atr_d14: false`, each with its note.
- The two rows render their bases and the bases differ on screen.
- A test fails if `adr` and `atr_d14` are configured alike.

---

**No separate done-note.** Fold this into `035`'s, with a line saying `035a` corrected the ADR
basis before `035` ran — or, if `035` had already run, what had to be changed after the fact.
