---
id: 019
title: Does the lock actually stop you, and leave everything else alone
status: OPEN
type: EXTERNAL
owner: christoph
closes: 039's UAT row
---

**Status** OPEN

# c019 — set the limit to 1, take one trade, watch it lock

**`039` says a limit empties the TRADE panel and touches nothing else.** That is the whole risk
model, and nothing has confirmed it against a running terminal.

**Paper account. One trade. Five minutes.**

---

## Setup

In `config/risk.yaml`:

```yaml
trades_max_day:  1        # temporarily — restore afterwards
```

**Launch with the paper flag:** `.\momentum --paper`

**Before anything else, confirm the mode is unmistakable.** `PAPER` should be on every panel border
and on the submit line — not one label in a corner.

| | |
|---|---|
| `PAPER` on every panel border? | yes / no |
| `PAPER` on the submit line? | yes / no |
| RISK shows `account PAPER *____`? | yes / no |

---

## Before the trade

| | |
|---|---|
| `trades` reads | `0/1 today` |
| Every limit shows a ceiling? | yes / no |
| `R net` shows **no** ceiling? | yes / no |

**`R net` having no ceiling is deliberate — it has no limit.** If it renders one, that is a defect.

---

## Take one paper trade, then close it

Any name, any stop. **It only has to open and close.**

---

## After

| | |
|---|---|
| TRADE panel is empty? | yes / no |
| Does it name the **reason**? | |
| Does it name the **config key**? | |
| Class recorded — `W` `P` `L` or `BE`? | |
| `trades` reads | `1/1 today` |

**Now check what did NOT change** — this is the important half:

| Panel | Still rendering normally? |
|---|---|
| ATTACHED | yes / no |
| LEVELS | yes / no |
| TAPE | yes / no |
| WATCHING | yes / no |
| CONNECTION | yes / no |

**Anything that stopped rendering is a defect.** The lock is on staging, not on data.

---

## Restart while locked

Close the terminal. Relaunch with `--paper`.

| | |
|---|---|
| Banner says LOCKED? | yes / no |
| `trades` still reads `1/1`? | yes / no |
| Open positions still shown? | yes / no |

**If the count reset to `0/1`, the lock does not survive a restart** and closing a window clears the
limit. **That is the single most important line in this UAT.**

---

## Afterwards

**Restore `trades_max_day` to its real value.** Note what you restored it to.

Save into `christoph/done/019-lock-and-limits.md` — the filled-in file. Then tell chat.

**If anything could not be checked, say which and why.** An unchecked row is a result; a row filled
in from expectation is not.
