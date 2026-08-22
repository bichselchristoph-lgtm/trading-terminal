---
id: 018
title: Check ATR14 and PDL against your own charts, and supply one missing pin
status: OPEN
type: EXTERNAL
owner: christoph
closes: 038's UAT row
---

**Status** OPEN

# c018 — do the two corrected numbers agree with your charts?

**`038` amended `SPEC.md` and changed what two rows compute. Nothing has checked the result against
the outside world.** Claude Code verified five of six fixture pins against externally-known values.
**The sixth is currently a constant asserted against itself**, which is worth exactly nothing —
that is the self-reference trap, and this task is what closes it.

**Three things. Ten minutes. Attach QQQ and open your TradingView daily.**

---

## 1 — `ATR14`, and it should now agree

**`ATR14` is ETH-derived, 04:00–20:00 ET, Wilder's RMA over 14 daily bars.**

**You trade with ETH charts enabled, so this is the one that should match.** Read ATR(14) off your
daily QQQ chart and compare.

| | |
|---|---|
| Terminal | `ATR14 $__.__` |
| TradingView daily, ETH | `___` |
| Agree to the cent? | |

**If it does not agree, the difference is the finding, not the number.** Record both, and note
whether TradingView's ATR is set to RMA — some templates default to SMA smoothing, which will
disagree by a few percent and is not a terminal defect.

---

## 2 — `PDL`, and it should NOT match your chart directly

**`PDL` is now the low of the prior *regular* session, 09:30–16:00 ET.**

**Your ETH chart will not show this directly.** If yesterday's low printed in pre-market or
after-hours, the chart's daily low and the terminal's `PDL` will differ — **and that is the ruling
working, not a bug.**

**To read the prior RTH low:** switch the chart to regular-hours-only, or drop to a 5-minute chart
and read the low between 09:30 and 16:00.

| | |
|---|---|
| Terminal `PDL` | `$___.__` |
| Prior RTH low from the chart | `___` |
| Prior *ETH* low, for comparison | `___` |
| Did the ETH low print outside 09:30–16:00? | yes / no |

**If the two lows are the same, this test proves less than it looks like.** Note that, and if you
can, repeat it on a day or a name where they differ — that is the case the ruling exists for.

---

## 3 — the missing pin: QQQ's prior regular-session low for 2026-08-12

**This is the one thing only you can supply, and it is the reason this task matters most.**

The regression fixture pins six QQQ values for 2026-08-13. **Five were checked against something
outside the code. The sixth — `PDL` — is a constant the test compares against itself.** A test that
asserts a number equals the number it was written from cannot fail for the right reason.

**Read the low of QQQ's regular session on Wednesday 2026-08-12, 09:30–16:00 ET, and write it
here:**

```
QQQ prior RTH low, 2026-08-12 09:30–16:00 ET   =   $______._____
```

**Read it from TWS rather than TradingView if you can** — TWS is the source the terminal draws from,
so a TWS-derived pin tests the terminal against its own supplier rather than against a third party's
interpretation of the same session.

**Note where you read it from.** A pin whose provenance is unrecorded is a pin nobody can re-check.

---

## What to do with this

Save your answers into `christoph/done/018-check-atr14-and-pdl.md` — **the filled-in file, not a
summary.** Then tell chat, and the pin goes into the next task file so the fixture stops asserting
a constant against itself.

**If any of the three cannot be done, say which and why.** An unanswered row is a result. **A row
filled in from memory is not** — this whole task exists because one value was never checked against
anything.

Christoph Aug 22, 2026. this is a duplicate. we already decided. ATR20 is ETH and PDL `PDL` is now the low of the prior *regular* session, 09:30–16:00 ET. Ruled as a decission by design. not tests needed.
018 adopt ATR20 as definition in all specs and tasks.