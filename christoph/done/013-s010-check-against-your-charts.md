# 013 · UAT — check it against your own charts

**Slice** S010
**Status** RUNNING · **Owner** Christoph only · **Blocks** S010 reaching DONE
**Written** 2026-08-12 by the design session

> **Run this during market hours.** Part B needs one attach before the open and one mid-session,
> so it spans a morning. Nothing else in it works properly on a closed market.

---

## 1. Why this one is different

**Every UAT so far asked whether you could read the screen. This one asks whether the terminal
is right.**

It is the first slice that claims to know something — ADR, ATR, extension, RVOL, VWAP. **A wrong
number here becomes a stop level, and a stop level becomes position size.**

**Read the numbers against your own charts before you look at anything else.** Not after forming
an impression of the screen. The order matters, because a plausible number is easy to accept
once you have decided the panel looks fine.

### One thing found on the live run that you should specifically re-check

The 20-session RVOL curve and today's minutes were being fetched on **different session bases** —
one including pre-market, one not. **Two sides of one ratio measured differently.**

It refused rather than rendering, and Claude Code says plainly that **the refusal was luck**: a
minute earlier it would have produced a plausible number instead. **Fixtures could not catch it,
because a fixture is internally consistent by construction and the defect was in which real
request each side made.**

It is fixed. **Check RVOL hardest.**

---

## 2. What to do

```powershell
cd D:\Dev\momentum
C:\venvs\trading\Scripts\python.exe -m live.tui.app
```

**A · Attach a name you know well.** One you have looked at often enough to know its range.

**Before reading the panel, have your own chart open.** Then compare, field by field.

**B · Attach the same name twice** — once before the open, once mid-session.

**Nothing in this slice accumulates from the live stream**, so every value must agree between
the two. **If any value drifts, something is accumulating that should not be.**

---

## 3. Record your answer here

**A · ADR% — does it agree with your chart?**

| | |
|---|---|
| your chart | `________` |
| the terminal | `________` |

- [ ] agree
- [ ] disagree

**Note:** ADR% is the mean of `(high/low − 1) × 100` over 20 sessions, **excluding today** — the
Kullamägi convention. **It is not ATR.** If your chart shows ATR, that is a different quantity
and the two are not expected to match.

**B · ATR₁₄ — does it agree?**

| | |
|---|---|
| your chart | `________` |
| the terminal | `________` |

- [ ] agree
- [ ] disagree

**Note:** Wilder's smoothing, not a plain mean of the last 14 true ranges. Most charting
packages use Wilder's; if yours offers a choice, check which is selected.

**C · RVOL — does it agree?**

| | |
|---|---|
| your chart | `________` |
| the terminal | `________` |

- [ ] agree
- [ ] disagree
- [ ] it refused — reason it gave: `________________________`

**D · Attached twice, before the open and mid-session. Did every value agree?**

- [ ] yes
- [ ] no — which drifted: `________________________________`

**E · Does the VWAP label carry its basis and its sample?**
It should read something like `VWAP 47.31 (bar-derived · 18.4M sh · 42 min · from 09:30:00)` —
**a bare number is a defect**, and so is a label saying `tick-derived`, which no longer exists.

- [ ] yes
- [ ] no — it showed: `________________________________`

**F · Attach a symbol with no sector mapping.** `RVOL_rel` must name why it cannot compute.

- [ ] it refused by name
- [ ] it showed a number — which: `________`

**G · Anything that looked plausible and turned out to be wrong.** This is the answer worth most:


Can't attach. It isn't there.

live/tui/app.py imports day_record, grammar and layout — it never imports live.attach. It has one key binding (Ctrl+Tab, focus), zero action_ methods and no command provider. The ATTACHED panel only renders record.attached; nothing in the running app can put a symbol into it.

The module-level docstring says "Ctrl+P is the palette for the long tail" — that mechanism doesn't exist in the code. Ctrl+P opens Textual's built-in palette with theme and quit in it.

This is 029 one level up. attach() exists, works, and has 18 KB of tests; the TUI has no path to it. Green suite, unreachable feature — the third time this shape has shipped.

So the 013 UAT is unperformable, not failing. Record it that way in the file: you cannot check a context block against your charts because you cannot produce one.

terminal did not start after running C:\venvs\trading\Scripts\python.exe -m live.tui.app___________________
It returned to prompt ___PS D:\Dev\momentum> C:\venvs\trading\Scripts\python.exe -m live.tui.app
PS D:\Dev\momentum> C:\venvs\trading\Scripts\python.exe -m live.tui.app
PS D:\Dev\momentum>______________`

---

Signed `____Christoph____________` Date/time `__August 13, 2026______________`

*Once signed, copy this file to `christoph/done/`, verify it is byte-identical, then remove it
from `christoph/open/`.*

---

## 4. What this UAT does not cover

**No sizing, no stop table, no order path.** Those are `S011` and later.

**Refusal B — the 15-second same-symbol cooldown — was not exercised live**, because seven
minutes elapsed between attaches and the cooldown had legitimately expired. Covered by fixture
only. **If you happen to attach the same symbol twice within fifteen seconds, note in G what it
did.**

**The depth-ordering finding is not a screen question** and is recorded separately.
