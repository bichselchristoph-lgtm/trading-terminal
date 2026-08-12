# S010 — attach a symbol, and the context block

**Status** WRITTEN · **Date** 2026-08-12 · **Type** build slice · **Tree** `D:\Dev\momentum`

> **Number not confirmed.** Build slices are `SNNN`, handoff tasks are bare numbers, and they
> have collided three times. **If `S010` is taken, say so and this file is re-issued.**
>
> **THE `019` CAPTURE IS RUNNING UNTIL 16:00 ET. DO NOT OPEN A TWS CONNECTION BEFORE IT CLOSES.**
> Build and test everything against fixtures today. **Part 6 — the live attach — runs after
> 16:00 ET and not before.** A second client during an unrepeatable session is not worth the
> hour it saves.

---

## Why this slice

**This is the first thing in the project that puts a real number on screen**, and it is what
makes sizing possible — sizing needs ADR, and ADR comes from here.

**It is also where the no-local-database decision proves itself.** `BUILD-PLAN.md` §010 states
it plainly: *if this slice needs a cache, the decision was wrong.* Build it so that it does not.

---

## Part 0 — one contradiction in `BUILD-PLAN.md` §010, resolved before you start

**The plan says two incompatible things about VWAP.**

Item **2c-bis** says: *"VWAP is computed from one-minute bars — one basis, no alternative.
`Σ(Bar.WAP × volume) ÷ Σ(volume)`. `reqHistoricalTicks` is not used for VWAP and the
tick-derived variant is retired."*

Item **2** (later in the same section) says: *"Default tick-derived; fall back to bar-derived
only with the substitution stated — `VWAP 47.28 (bar-derived — tick budget exhausted)`."*

**Build 2c-bis. It is the amendment and it supersedes.** One basis means nothing to declare per
row, nothing to substitute, nothing to disagree. **It also deletes the `tick budget exhausted`
state, the 1,000-tick pagination and the boundary-second dedup** — do not build any of them.

**The label still renders**, because every value must say what it was computed over. It reads
`bar-derived` always, and never as a fallback or a degradation.

**Report this in the done-note as a `BUILD-PLAN.md` defect.** Do not edit `BUILD-PLAN.md` —
that is an adopted spec and the amendment route is separate. **A spec that says two things is
worse than one that says the wrong thing**, because a reader cannot tell which is current.

---

## Part 1 — attach

**`/` opens a symbol field.** Type, enter, attached.

**Three origins are recorded — `typed` · `scanner` · `watchlist` — even though only `typed`
exists.** The other two arrive in later slices; recording the field now means the day record
does not change shape when they do.

**Contract qualification refuses ambiguity rather than picking the most liquid.** `tws_order`
already does this and its wording is the model: *"resolved to 2 contracts — ambiguous, refusing
to guess."* **Render the candidates and ask.** Picking the most liquid is a well-formed value
answering a different question, and it would be silently right most of the time — which is
what makes it dangerous.

### The attach sequence — five steps, three of which can fail independently

| # | Step | Blocking? | On failure |
|---|---|---|---|
| 1 | Resolve the contract | **Yes** | Ambiguous ⇒ render candidates, ask. **Never guess** |
| 2 | Check the tick slot | No | Exhausted ⇒ render **now**, before the fetches, naming what to detach. Cooldown ⇒ `queued · 11s` |
| 3 | Dispatch three historical requests | No | Per-row `unavailable (reason)`. The others still render |
| 4 | Open the tick-by-tick subscription | No | **Attach succeeds.** The pane says the tape is absent and why |
| 5 | Bind the playbook | No | `no trigger level declared` |

**Step 2 before step 3 is deliberate**, and the reason belongs in a comment: with no slot you
should learn that in the first frame, not after three historical requests have been spent
against a 60-per-10-minutes budget on a symbol you are about to detach.

**Step 4 does not gate step 3, and this ordering is the point of the whole slice.** A symbol
with no free tick slot still gives you ADR, ATR, extension, the level rail, both RVOLs and
session VWAP — **everything sizing will need.**

---

## Part 2 — three IBKR requests per attach, and nothing else

1. **A daily-bar request**, 20–60 sessions → ADR%, ADR $, ATR₁₄, extension from the 10/20/50
   SMA in ADR units, the level rail.
2. **A 20-session intraday request** → the RVOL curve.
3. **A today-from-the-open request** → session VWAP and every session-cumulative value.

**No nightly cache. No local store. No warm path, no cold path.**

**A test must assert that nothing under the repo is written by this path.** Not a convention —
a test. The one in-session memo (the sector ETF series) lives in memory, is never written to
disk, and is refetched after a restart.

**The five-slot limit governs `reqTickByTickData` only.** Historical bar requests consume none;
`reqMktData` lines are a third budget (~100). **Do not conflate the three.**

**Pacing is a display state, not an error.** ~60 historical requests per 10 minutes, 15-second
same-contract cooldown. Render `fetching dailies…`, then values, or
`unavailable — pacing limit, retry in 42s`.

### No settle timer — render the sample instead

*n* seconds is the wrong unit: 30 s is thousands of prints on a liquid name and four on a thin
one at 11:40. **Every value renders what it was computed over:**

```
VWAP 47.31 (bar-derived · 18.4M sh · 42 min · from 09:30:00)
```

That answers the trust question per symbol, where a fixed timer cannot. The only real settle is
~2 s for the subscription callback to populate, as `ibkr.py` already does after account
requests.

---

## Part 3 — the context block

Per `SPEC.md` §6b.1a:

- **ADR%** — mean of `(high/low − 1) × 100`, **excluding today**, N=20. **Kullamägi convention,
  not ATR.** They are different quantities and must never share a label.
- **ADR $**
- **ADR used**, with its 20-cell bar, and `OVER` past 100 %
- **Room left in both directions**
- **Extension in ADR units** from the 10/20/50 SMA
- **The level rail** — PDH/PDL, PMH/PML, ORH/ORL, session VWAP, 52-week, round numbers

**Both RVOLs** (`SPEC.md` §8.4):

- `RVOL(t)` against a per-minute median curve rebuilt at attach
- `RVOL_rel` against the sector ETF from `contractDetails`
- **Render the sparkline, not only the scalar.**
- **No sector mapping ⇒ `unavailable (no sector mapping)`. Never `1.0`.** A neutral-looking
  number for a missing input is the defect this project exists to prevent.

**`warming` survives on exactly one thing — tape baselines — and there are no tape components in
core.** So in practice nothing warms. **Daily-derived values are fetched or `unavailable
(reason)`. There is no third state**, because there is no half-populated cache to produce one.

---

## Part 4 — the seam, and when a value must refuse

**Assert the seam in a test:** reconstruct a session at two different attach times and require
identical cumulative volume and VWAP **to the cent.** A double-count or a gap shows up
immediately and nothing else will surface it.

**If the seam cannot be closed for a symbol, the value renders `unavailable (splice unverified)`
rather than a number that is quietly a little wrong.** A VWAP off by three cents does not look
broken — it looks like a VWAP — and it is a stop level, so it becomes position size.

**Backfill on attach:** playbook-driven, **default 3 minutes, anchored to confirmation**, not to
the fill and not to the session open. **Never backfill the whole session.** Tape older than the
window is discarded, not reconstructed. Backfill failure degrades gracefully — the slot still
attaches live and the missing pre-attach window reads `unavailable`, never zero.

**Where an indicator needs the open and attach is later than open + window**, serve from the
nightly baseline or read `N/A`. **Never silently zero.**

---

## Part 5 — what this slice must not become

**No sizing. No stop table. No order path. No tape components. No watchlist.**

`SPEC.md` §6b.1c requires that a symbol process **cannot size, stage, or evaluate a limit**, and
that this is enforced structurally rather than by discipline — the symbol process does not
import the sizing or staging modules at all.

**Those modules do not exist yet, so the test cannot be written today.** **Record it as owed by
`S011`** rather than writing a test that passes because its subject is absent — that is a
vacuous pass, and this project has a fixture proving how easily one happens.

---

## Part 6 — the live attach. **After 16:00 ET only.**

**Do not open a TWS connection before the `019` capture has closed and written its done-note.**

Then attach three symbols in a row:

1. **One liquid large-cap**
2. **One thin small-cap**
3. **One with no sector mapping**

**Every field must either show a number that can be checked by hand, or name why it cannot.**

Report all three attaches in full — every field, every refusal, with its reason string verbatim.

---

## Do not

- **Do not open a TWS connection before 16:00 ET.** The capture is unrepeatable.
- Do not modify `tools/capture_tape.py` or anything in `records/`.
- Do not edit `SPEC.md`, `BUILD-PLAN.md`, `REGIME-PROMPT.md` or `HANDOFF-PROTOCOL.md`. **Report
  part 0's contradiction; do not fix it in the file.**
- Do not write to `christoph/open/` or `christoph/done/`.
- Do not build a cache, a local store, or any persistence for fetched values.
- Do not add a settle timer.
- Do not render `1.0` for a missing RVOL, or `0` for anything absent.
- **Do not use colour for a verdict.** No green anywhere.
- Do not adopt `live/render.py`, `live/detectors.py`, `live/marketstate.py` or `live/feeds.py`.
  **`feeds.py` still imports `ib_insync`.** If a cascade appears, stop and re-author, as `S009`
  did.
- Do not weaken a test to make it pass. **Report and stop.**

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | Full suite, count before and after as measured numbers. **Plus the no-disk-write assertion and the two-attach-times seam test.** |
| **Refusal A** | Claude Code | Kill the network mid-fetch: **per-row `unavailable (reason)`, never a partial ADR.** |
| **Refusal B** | Claude Code | Attach the same symbol twice inside 15 s: the second renders the cooldown with its remaining seconds. **Never a silent drop.** |
| **Refusal C** | Claude Code | A symbol with no sector mapping: `RVOL_rel` refuses **by name**. Assert the string is not `1.0` and not blank. |
| **Refusal D** | Claude Code | An ambiguous ticker: candidates render, nothing is chosen. **Assert no contract was qualified.** |
| **UAT** | Christoph | **Attach a name you know well and check ADR%, ATR and the RVOL reading against your own charts before looking at anything else. They must agree to the cent and the decimal.** Then attach the same name twice — once pre-open, once mid-session — and confirm every value agrees, because nothing accumulates from the live stream. **Check the VWAP label carries its basis and its sample in both.** Write the record to `christoph/open/`. |

## Done-note must state

- **Part 0's contradiction**, and confirmation that 2c-bis was built.
- **The three live attaches in full**, with every refusal string verbatim.
- The seam test's two attach times and whether the values matched **to the cent.**
- Which `SPEC.md` §4 refusal terms this slice made reachable, and which remain constants with no
  producer.
- **The `S011`-owed structural import test**, recorded rather than written.
- The commit split, one line each.
- **Anything in this task that was wrong on contact.** Every task this week has had divergences
  and every one of them mattered.
