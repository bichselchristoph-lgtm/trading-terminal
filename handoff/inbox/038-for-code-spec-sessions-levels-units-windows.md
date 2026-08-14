---
id: 038
title: Sessions, levels, units and windows — amend SPEC in place
type: spec
class: admin
supersedes: 035, 035a, 036
unblocks: S011 and S013 — sizing and the stop table consume ATR, VWAP and the level rail, and cannot be built against three contradictory rulings
owner: claude-code
tree: D:\Dev\momentum
---

# 038 — a basis, a unit and a window are all definitions

**Type: spec. Class: admin.** No panel changes. `SPEC.md` gains four rulings and the tests that
hold them.

**`035`, `035a` and `036` are SUPERSEDED. Do not run them.** They will stay in
`handoff/inbox/` — copy-and-keep, nothing moves. **`036` was right about ATR, ADR, and about a
basis being a constant rather than a config key. It was wrong about `PDH`/`PDL`.** Part 1
explains why, because the reasoning is the durable part.

> **Read this cold. The session that wrote it cannot answer questions.**

---

## Addressing

**If `handoff/inbox/038-for-code-spec-sessions-levels-units-windows.md` exists in your tree and
`handoff/done/038-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

**Work in a worktree.** Remove it when the task completes.

**Run `037` first if it has not run** — the export is stale and the design session cannot read
your done-note otherwise.

---

## How to amend

**Edit `SPEC.md` on disk. Do not re-author it and do not accept a replacement from outside the
tree.** The design session has no bridge this session and has not read the live file. **If any
instruction below contradicts what is actually in `SPEC.md`, report the contradiction and stop on
that part** rather than overwriting.

**`SPEC.md:999`** currently asserts that daily bars are RTH-only, *"excluded, unchangeably — ETH
cannot alter a daily bar."* **That is factually wrong** — IBKR returns different daily bars for
`use_rth=True` and `False`, which is why any of this matters. Correct it.

---

## Part 1 — six windows, and a level carries its window

**Christoph's ruling, 2026-08-14.**

| Level | Window (ET) | |
|---|---|---|
| **PDC** | 16:00 closing auction | prior day close |
| **PDO** | 09:30 opening auction | prior day open |
| **PDH / PDL** | **09:30–16:00, prior day** | prior **regular** session extremes |
| **PMH / PML** | 04:00–09:30, today | pre-market extremes |
| **AMH / AML** | 16:00–20:00, prior day | post-market extremes |
| **ORH / ORL** | 09:30–09:35, today | opening range |

**Why `PDH`/`PDL` are RTH, and this is the part to record.** If they were ETH, then on any day
the extreme occurred after 16:00, **`PDL` *is* `AML`** — one number, two names, no way to tell
which you are looking at. A level that silently changes identity depending on when the extreme
occurred is the canonical defect of this project. **Confirmed on Christoph's own QQQ chart for
2026-08-13: the session low of 722.34 sits in the early pre-market, so an ETH `PDL` would have
been `PML` that day.**

**The distinction that makes the table consistent:**

- **ADR is a statistic** — mean of session ranges, no gap term. **RTH, definitionally.**
- **ATR is a statistic** — its true range spans the prior close, so the gap is the measurement.
  **ETH 04:00–20:00.**
- **PDH/PDL/PMH/PML/AMH/AML are not statistics. They are levels.** They exist because price
  traded there, in a named window, **and the window is part of the name.**

**ADR being RTH does not propagate to `PDL`; ATR being ETH does not either.** Different kinds of
object.

**Carried forward from `036`, unchanged:**

- **A basis is a constant declared beside the indicator's definition — never `config/`.** A
  setting is a choice; a basis is a fact about what the indicator is. **State in the code that
  `SPEC.md` §4.4 is exempt here and why**, or the next person moves it into config for
  consistency and the rule quietly becomes a preference.
- **VWAP, cumulative volume, RVOL: ETH, anchored 04:00.**
- **Every rendered value prints its basis or anchor.**

**Note for the future, not a build.** The SEC approved Nasdaq's 23/5 proposal on 2026-04-10
targeting December 2026, and NSCC plans 24×5 clearing from 2026-06-28. **Structure the taxonomy
so a seventh window can be added.** Record it in `OBSERVATIONS.md`; build nothing.

---

## Part 2 — every value renders its unit

**Christoph's ruling: all numbers need units. Always.**

```
$48.55 flag high · yours 10:11h ET      now $48.62   +$0.07 above
buyers 340k sh · sellers 95k sh · net +245k sh to buyers
ATR14 $15.61 · Wilder RMA n=14 · 04:00-20:00 ET
ADR used 78% of $1.29
money $4.2M/s · 6.1× 20d median at this time
```

| Kind | Rule |
|---|---|
| Prices, distances, dollar ranges | **`$` prefix** |
| Share counts | **`sh` suffix** |
| Ratios / multiples | **`×` suffix, and the baseline named** — `6.1×` alone is the `12.4M` complaint again |
| ADR distances | **both** — `+$0.25 · 0.19 ADR`. ADR is a dollar quantity used as a ratio |
| Percentages | **name the referent** — `78% of $1.29`, not bare `78%` |
| Times | **`HH:MMh` 24-hour, and `ET`** |

**`ET` is not optional.** Christoph is in Cape Town, the levels mean nothing except in exchange
time, and `034` lost four values to a UTC/ET slicing defect. **A bare clock time on this panel is
the same defect wearing a different hat.**

---

## Part 3 — a level has a state, not only a distance

**Distance says where it is. State says what happened to it.**

| State | Meaning |
|---|---|
| `untested` | Price has not reached it today |
| `gapped over` | **Price crossed it without trading through it** |
| `traded through` | Price crossed it with trades at the level |
| `reclaimed` | Crossed back from below to above |
| `lost` | Crossed back from above to below |

**`gapped over` is the strongest of these and the reason the row exists.** Nobody got the chance
to exit there, so positions taken before the gap are still held. **A level traded through on
volume is spent; a level jumped over is loaded.** `PDC` most of all — being above or below the
institutional print is a different day.

**This is arithmetic on levels already computed.** No tape, no volume profile.

### `clear for` — distance to the next claimed level

```
BREAKING  $48.55  flag high · yours 10:11h ET
  overhead   $48.80  ORH     +$0.25   0.19 ADR
             $49.60  PDH     +$1.05   0.81 ADR
  underfoot  $48.20  PML     −$0.35   0.27 ADR
  ▸ clear for 0.19 ADR
```

**One number: how far the move runs before it meets something.** 0.19 ADR clear is a muted
breakout; 1.2 ADR clear is a different trade at the same entry price. **Symmetric, because a
level just under a stop is a stop that gets run and then reverses.**

**This replaces `room up` / `room down` rather than joining them.** Those measure room in the ADR
*budget*; `clear for` measures room to the next obstacle. **Having both invites reading one as the
other**, which is the defect this document is mostly about.

**The lookahead cap is a threshold and renders `unfitted`** — suggested first three levels or
1.5 ADR, whichever comes first, but nothing is fitted until Christoph has watched it.

---

## Part 4 — a window is a definition, and there are two of them

**Record in `SPEC.md`. Build nothing — tape components are not in core.**

**A tape reading states its window, its step, and its band, or it has no defined meaning.**

**The rolling window — what is happening now.**
At each step, every trade whose **exchange timestamp** falls in `[now − W, now]`, classified
buyer- or seller-aggressive, summed per side. **Default `W = 60s`, stepped `5s`.**

**Why stepped.** A 10 Hz repaint cap solves CPU and not readability. **A number changing ten
times a second is unreadable even when it is cheap to draw** — that is Time & Sales in a smaller
box. A 60s window stepped at 5s is twelve stable readings of the same measurement.

- **The row states the step** — `60s window · stepped 5s`. It is up to 5s stale by construction
  and that must not be silent.
- **Counts step; events do not.** A sweep is discrete and its *arrival* is the thing you want
  immediately. Sweep arrivals are exempt from the step.
- **The step size is empirical and unfitted.** Answer it by replaying a captured session at 1s,
  5s and 10s. **Research, not a slice.**

**The anchored window — who has been winning, and for how long.**
Anchored at the moment price **first entered the band around a level**, and running until it
leaves.

```
at level since 09:52h ET · 19min · buyers 4.2M sh · sellers 4.1M sh · price +$0.02 · within ±0.02 ADR
```

**This is what absorption actually is.** Real absorption runs for many minutes; a 60s window is
exactly the wrong length to see it. **The rolling window says the level is under pressure now;
the anchored one says who has been winning.**

- **The band is stated and is ADR-based**, not cents — `±0.02 ADR` transfers between a $4 name
  and a $700 one; `±$0.03` does not.
- **Resets when price leaves the band beyond a threshold; re-anchors on return.** The reset
  threshold is unfitted.

**What neither window can see, and the panel must not imply otherwise:** anything before the
window opened; order *within* the window (340k buy then 95k sell renders identically to the
reverse); and, for the rolling window, whether the volume was at the level at all — **which is
precisely why the anchored window states its band.**

**Bars are not units of time.** A window expressed in bars declares its bar size **and** its
session, or it has no defined length — a 20-period MA spans three sessions on RTH bars and 1.25
on ETH. Prefer clock form. **Nothing currently rendered is exposed to this**; record it and build
nothing.

---

## Part 5 — the tests

1. **The basis constant matches the request actually issued** — not that the constant exists.
   Seen red with one inverted.
2. **`adr` and `atr_d14` must request different flags.** A configuration where both read alike
   passes trivially — `OBS-037`'s shape, in the test written to prevent it.
3. **Every rendered context row's detail names a basis or an anchor.** Seen red by removing one.
4. **Every rendered numeric carries a unit** per Part 2. **Scope this positionally to the render
   layer** — a repo-wide search for bare numbers will match its own fixtures. Self-reference trap,
   five times in one session.
5. **A regression fixture pinning 2026-08-13 QQQ**, from bar fixtures, no network:
   `PDH $727.25 · ORH $726.02 · ORL $724.03 · PMH $725.46 · PML $722.80`, **`PDL` on the RTH
   basis**, and **`ATR14` ETH-derived**, which Christoph's TWS reads at ≈$15.6.

**`PDL $717.37` must NOT be pinned.** `036` would have baked it in. It is the ETH low and
therefore, under Part 1, the `AML` — **the first externally-checked values this project has, and
one of them would have been wrong on arrival.**

**`ADR%` and `ADR $` are deliberately absent from the fixture.** TWS has no native ADR; anything
it shows comes from a different computation over a different bar set. **It is not a check and
must not be recorded as one.** Say so in the note so the omission does not read as an oversight.

---

## Part 6 — three rows that do not reconcile

**Carried from `036`. Report on each; do not guess.**

1. **The ADR trio closes arithmetically and anchors to nothing identifiable.** `ADR used 67.00`,
   `room up 3.90`, `room down 19.76`, `ADR $ 11.83`: 67% of 11.83 = 7.93; 7.93 + 3.90 = 11.83;
   11.83 + 7.93 = 19.76. But 733.14 − 7.93 = 725.21, which is neither 722.80 nor 724.03.
   **Name the anchor, or name it unidentified.**
2. **`round 47.00 · ±11.83 of 733.14`.** Nothing near 47 is a round level for a 733 instrument.
   **State what the row computes and whether the label matches.**
3. **`ADR used` and `round` render two decimals** where `SPEC.md` §4.0a requires one for
   non-monetary values.

**Also report, before fixing anything: one table, one row per indicator, stating what each
daily-bar request currently passes for `use_rth`.** The present state is the finding.

**And: RVOL's denominator is a per-minute curve median-ed across 20 sessions. It is
clock-anchored and safe only if every session in the lookback used the same anchor. Verify and
say so.** A misaligned curve makes RVOL wrong in a way that looks like a quiet market.

---

## Not in scope

**`OBS-042`, the unreachable rail** — fourteen of twenty-six rows still cannot be seen from the
running program. That is `S012`, and the scope decision of 2026-08-14 shrinks it considerably:
`ext 10/20/50`, `52wH/52wL`, `RVOL`, `RVOL_rel` and `round` **leave the panel entirely** —
TradingView owns charting and indicators.

**No tape components.** Part 4 is specification only.

**No panel layout changes.**

---

## Last action

**Run `verify.ps1`.** Do not paste or summarise. Do not quote a test count.

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | `verify.ps1` ran with all five tests; 1–4 seen red first |
| **Refusal** | Claude Code | A row whose basis constant is missing renders `unavailable (no basis declared)`, never an unlabelled number |
| **UAT** | Christoph | `c018` — attach QQQ and check `PDL` and `ATR14` against the TradingView **ETH** daily chart. `ATR14` must agree; **`PDL` must equal the prior RTH low, which the ETH chart will not show directly** — read it from the regular session. |

---

## Report

In `handoff/done/038-sessions-levels-units-windows.md`:

1. The pre-fix `use_rth` table, all indicators.
2. Before-and-after values with bases.
3. The four reds, quoted.
4. Part 6's three answers plus the RVOL anchor finding.
5. **Any contradiction between this file and what `SPEC.md` actually says**, and where you stopped.
6. **Anything else requesting bars without a declared basis.** Look — this task exists because
   nobody had.
7. **What you could not do**, and why. Empty is suspicious.
8. `verify.ps1` run at `<time>`.
