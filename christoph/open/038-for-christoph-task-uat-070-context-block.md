---
id: 038
title: UAT for 070 — the context block against the mockup
type: uat
owner: christoph
task: 070
story: S034 S035 S037
---

# 038 — UAT for 070: does the panel say what you ruled?

**For Christoph. Twenty minutes, market hours, one symbol you know well.**

**This is the only thing that closes 070.** The snapshot fixtures prove the panel matches the drawing. **They cannot prove the drawing was right, and they cannot prove `ADR% used` is the correct number.**

---

## Before you start

**Open the mockup beside the terminal:** `ATTACHED mockup — the context block and its states`, in the Drive `Mockups/` folder.

**Have your own chart open too.** Part C needs it.

```powershell
cd D:\Dev\momentum
C:\venvs\trading\Scripts\python.exe -m live.tui.app
```

---

## A · The landed panel — four rows and no more

**Attach a name you know. Read the context block against §1 of the mockup.**

**Expected, exactly:**

```
  ADR% used   64%  ▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░
  RVOL        rel 1.4x · avg 0.86x · cum 18.1M sh
  VWAP        $730.68 · +$2.46
              from 04:00 · 18.4M sh · pre-mkt 2.1M of 18.4M
```

- [ ] **Four rows, and the ADR row reads `ADR% used`**
- [ ] **No ATR row anywhere in this panel**
- [ ] **No `ADR$`, no `ADR%avail`, no room up, no room down**
- [ ] Something else is there — name it: `____________________`

**If an ATR row is present, that is the finding**, and it settles a contradiction two documents have been carrying. Note it and carry on.

---

## B · Is the number right?

**This is the part a test cannot do.**

`ADR% used` is the share of a typical day's range that today has already consumed.

| | |
|---|---|
| today's high | `________` |
| today's low | `________` |
| today's range | `________` |
| the terminal's `ADR% used` | `________` |

**Rough check:** today's range divided by roughly `ADR20% × price`. On a quiet morning it should read low; by mid-afternoon on a trending day, high.

- [ ] **It agrees with what the day has actually done**
- [ ] **It does not** — what it showed: `________` · what you expected: `________`

**Does the row say what it was computed over?** `ADR20` is RTH, 09:30–16:00 ET.

- [ ] **Yes, and the basis tail is legible to the end of the line**
- [ ] **The tail is cut off** — that is B-005 / B-011 and it matters here, because **the one row you need to verify a basis is the row the renderer cuts**

---

## C · Above 100%

**On a name having a bigger day than usual, the number should pass 100 and keep going. The bar stops at full.**

**A big mover will do this by early afternoon.** If nothing is running today, skip and say so.

- [ ] **Above 100% renders, bar full**
- [ ] **It capped at 100%** — a silently capped number answers a different question
- [ ] **No name did enough today to test it**

---

## D · The four other states

**Against §3–§6 of the mockup.**

**Attaching.** Attach a symbol and watch.

- [ ] **Old values vanish at once, one badge, everything lands in one paint**
- [ ] **Rows filled in one at a time** — that is the design that was ruled out

**Nothing attached.** Start fresh, do not attach.

- [ ] **Reads `not attached`, not `0 of 4`**

**Cooldown.** Attach the same symbol twice inside fifteen seconds.

- [ ] **Reads `queued · 11s`**
- [ ] **Nothing visible happened** — a silent drop is the defect

**Partial.** Only if it happens naturally — do not force it.

- [ ] **Saw `N of M rows unavailable`**
- [ ] Did not occur today

---

## E · The one answer worth most

**Anything that looked plausible and turned out to be wrong.** This is where c015 produced the richest requirement in the project.

```
____________________________________________________________
____________________________________________________________
```

---

## Verdict

- [ ] **Accepted.** The panel matches the mockup and `ADR% used` agrees with the day.
- [ ] **Not accepted** — details above.

**If accepted:** 070 reaches REVIEWED, and S034, S035 and S037 each clear Definition of Done condition 4.

**If not accepted:** the finding re-enters at ideation as a row, and the mockup is corrected before the code is.

Signed `____________________` Date `____________________`

*Copy to `christoph/done/` with your answers and the date.*
