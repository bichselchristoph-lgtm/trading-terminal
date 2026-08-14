---
id: 036
title: Every indicator declares its session basis — supersedes 035 and 035a
type: product
owner: claude-code
supersedes: 035, 035a
depends: 034
---

**Status** WRITTEN

**If `handoff/inbox/036-for-code-every-indicator-declares-its-session.md` exists in your tree,
this is for you. If it does not, stop reading and ignore this message.**

**`035` and `035a` are SUPERSEDED. Do not run them.** They will arrive in `handoff/inbox/` and
stay there — `handoff/` is copy-and-keep and nothing moves — but this file replaces both. **If
either has already produced a done-note, say so and treat this as the correction to apply.**

---

# 036 — A basis is a definition, not a setting

**Christoph performed `013` on 2026-08-13 — the first UAT this project has completed.** Six
values matched his TWS charts. Two did not, and both are inputs to position size.

---

## Part 0 — The evidence

Compared against **IBKR's own daily bars in TWS**, same source, same instrument. The chart
tooltip states its basis outright: `8/12 (04:00:00-20:00:00) EST`.

| Row | Terminal | IBKR chart | |
|---|---|---|---|
| ORH / ORL | 726.02 / 724.03 | 726.02 / 724.03 | **exact** — `034`'s timezone fix confirmed |
| PDH | 727.25 | 727.25 | match |
| PML | 722.80 | 722.80 | match |
| 52wH | 748.65 | 748.65 | match |
| **PDL** | **722.92** | **717.37** | **−5.55** |
| **ATR14** | **13.14** | **≈15.6** | **−16 %** |

**Observation:** two values disagree, both in the direction an RTH-only computation predicts.
**Inference:** daily-bar requests pass `use_rth=True` where the definitions require otherwise.
PDH agrees anyway because 8/12's high fell inside the regular session; PDL cannot, because the
717.37 low did not.

**Why this outranks the unreachable rail (`OBS-042`).** ATR feeds stop distance; stop distance
feeds size. **A 16 % error in ATR is a 16 % error in every share count**, arriving as a
well-formed number with no flag.

---

## Part 1 — Report before fixing

**One table, one row per indicator, stating what each daily-bar request currently passes for
`use_rth`.** The present state is the finding; do not fix and then describe the fix.

---

## Part 2 — The bases, and they are definitional

**Christoph's ruling, 2026-08-13.** These follow from what each indicator *is*, not from
preference:

| Indicator | Basis | Why |
|---|---|---|
| **ADR%, ADR $** | **RTH 09:30–16:00** | Average **Day** Range is the mean of each session's own `High − Low`. **It has no gap term — that is what distinguishes it from ATR.** So it measures the session actually traded. |
| **ATR14 (`atr_d14`)** | **ETH 04:00–20:00** | Average **True** Range is `max(H−L, \|H−Cprev\|, \|Cprev−L\|)`. **The gap across the close is part of the measurement**, so it is computed on the series whose close-to-close relationship is the real one. |
| **PDH / PDL** | **ETH** | A level is a level because price traded there. 717.37 traded. |
| **PMH / PML, ORH / ORL** | clock-defined | The windows are wall-clock. State which bars they slice. |
| **VWAP, cumulative volume, RVOL** | **ETH, anchored 04:00** | Settled previously; `008b` measured that liquid names do have pre-market volume. |
| **SMA stack** | **ETH** | Daily closes; the ETH close is the one the other daily values use. |

**ADR and ATR are both labelled volatility and are computed on different sessions on purpose.
That is the whole reason Part 3 exists.**

---

## Part 3 — The basis is declared in code, beside the definition. **Not a config setting.**

**This is the correction that supersedes `035`.** `035` put `use_rth` into
`config/indicators.yaml`. **Do not.**

**A setting is a choice. A basis is a fact about what the indicator is.** ADR is RTH by
definition; a config key implies it could sensibly be otherwise and invites someone to flip it
in a hurry. **Christoph's ruling: this is not a user setting in the terminal, now or in this
slice.**

So each indicator carries its basis as a **constant declared beside its own definition**, and
the value that reaches the request comes from that constant — never from a literal at the call
site, never from config.

**`SPEC.md` §4.4 says every setting lives in `config/`, once. State plainly in the code that a
session basis is exempt because it is not a setting** — otherwise the next person moves it into
config for consistency and the rule quietly becomes a preference. **An exemption that is not
written down is an exemption that gets undone.**

---

## Part 4 — Every rendered value prints its basis

```
    ADR%      1.63  · 20 sessions, excl. today · 09:30-16:00
    ADR $     11.83  · 20 sessions, excl. today · 09:30-16:00
    ATR14     15.61  · Wilder RMA, n=14 · 04:00-20:00
    PDH       727.25  · prior session · 04:00-20:00
    PDL       717.37  · prior session · 04:00-20:00
    VWAP      730.68  · bar-derived · 566 min · 04:00 anchor
```

**Without this the panel shows two volatility numbers four rows apart, on different sessions,
and a reader compares them.** It took a UAT and four chart screenshots to settle what one field
in the detail column answers permanently.

**A value that carries its basis can be compared with something. A value that does not can only
be argued about.**

---

## Part 5 — The window rule, agreed 2026-08-13

**A bar is not a unit of time unless the session is declared.** A 20-period MA on hourly
candles spans **three sessions** on RTH bars and **1.25 sessions** on ETH bars — same label,
same number, 2.5× the lookback, and no chart would ever disagree with another because both make
the substitution silently.

**The rule:**

- **A window expressed in bars declares its bar size AND its session**, or it has no defined
  length.
- **A window expressed in clock time declares its anchor.**
- **Prefer the clock form wherever the quantity is really about time.**

**Nothing currently rendered is exposed to this** — every existing value is either a daily-bar
count, where one bar is one session regardless of setting, or clock-anchored. **Record the rule
in `docs/observations/OBSERVATIONS.md` and do not build machinery for it.** It becomes live when
something intraday and bar-counted is first built.

**One thing to check rather than assume:** RVOL's denominator is a per-minute curve median-ed
across 20 sessions. It is clock-anchored and therefore safe **only if every session in the
lookback used the same anchor**. **Verify that and say so.** A misaligned curve makes RVOL wrong
in a way that looks like a quiet market.

---

## Part 6 — Three rows that do not reconcile

**Report on each. Do not guess.**

1. **The ADR trio closes arithmetically and anchors to nothing identifiable.** `ADR used 67.00`,
   `room up 3.90`, `room down 19.76`, `ADR $ 11.83`: 67 % of 11.83 = 7.93; 7.93 + 3.90 = 11.83;
   11.83 + 7.93 = 19.76. But 733.14 − 7.93 = 725.21, which is neither 722.80 nor 724.03.
   **Name the anchor, or name it as unidentified.**
2. **`round 47.00 · ±11.83 of 733.14`.** Nothing near 47 is a round level for a 733 instrument.
   **State what the row computes and whether the label matches.**
3. **`ADR used` and `round` render two decimals** where `SPEC.md` §4.0a requires one digit for
   non-monetary values.

---

## Part 7 — The tests

1. **The basis constant matches the request actually issued** — not that the constant exists.
   Seen red with one inverted.
2. **`adr` and `atr_d14` must request different flags.** A configuration where both read alike
   passes trivially — that is `OBS-037`'s shape in the test written to prevent this.
3. **Every rendered context row's detail names a basis or an anchor.** Seen red by removing one.
4. **A regression fixture pinning 2026-08-13 QQQ** from bar fixtures, no network:
   `PDH 727.25 · PDL 717.37 · ORH 726.02 · ORL 724.03 · PMH 725.46 · PML 722.80`, and
   **`ATR14` on the ETH basis**, which Christoph's TWS ATR(14) reads at ≈15.6.
   **These are the first externally-checked values this project has.**

**`ADR%` and `ADR $` are deliberately absent from that fixture.** TWS has no native ADR; any
figure it shows comes from a different computation over a different bar set. **It is not a check
and must not be recorded as one.** Say so in the done-note so the omission does not read as an
oversight.

---

## Not in scope

**`OBS-042`, the unreachable rail** — fourteen of twenty-six rows still cannot be seen from the
running program. Next task, not this one.

---

## Done when

- The pre-fix table is reported.
- `PDL` reads `717.37`; `ATR14` is ETH-derived; `ADR` is RTH-derived.
- No `use_rth` key exists in `config/`, and the code says why.
- Every rendered row names its basis or anchor.
- Part 6's three rows are explained or named unexplained.
- All four tests exist, the first three seen red first.
- RVOL's anchor consistency is verified and stated.

---

## Deliverable

`handoff/done/036-for-code-every-indicator-declares-its-session.md`:

1. The before-and-after table, all rows, with bases.
2. The three reds, quoted.
3. Part 6's three answers.
4. The RVOL anchor finding.
5. **Anything else requesting bars without a declared basis.** Look — this task exists because
   nobody had.
6. **What you could not do**, and why. Empty is suspicious.
7. `verify.ps1` run at `<time>`. Do not quote its output.

---

**Work in a worktree, not the shared checkout. Remove it when the task completes.**
