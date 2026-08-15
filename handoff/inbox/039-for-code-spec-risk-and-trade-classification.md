---
id: 039
title: Risk, trade classification and the lock — amend SPEC in place
type: spec
class: admin
version: 1.2
unblocks: S011 — sizing and the TRADE panel cannot be built while risk is defined as a percentage of NLV in SPEC and a fixed dollar figure in Christoph's ruling
owner: claude-code
tree: D:\Dev\momentum
---

**Status** WRITTEN

# 039 — risk is a fixed dollar figure, and every limit is a loss limit

**Type: spec. Class: admin.** No panel changes. `SPEC.md` §7b.1 is corrected and four new
definitions land.

**v1.2 adds the `**Status**` line above.** v1.1 removed the cap on winning trades that v1.0
carried — Part 3 records why. **Neither earlier version reached the tree.**

**Run `038` first** — it settles the session bases these definitions sit on.

> **Read this cold. The session that wrote it cannot answer questions.**

---

## Addressing

**If `handoff/inbox/039-for-code-spec-risk-and-trade-classification.md` exists in your tree and
`handoff/done/039-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

**Work in a worktree.** Remove it when the task completes — `OBS-046`. Do not remove another
session's.

---

## How to amend

**Edit `SPEC.md` on disk. Do not re-author it.** The design session has no bridge and has not read
the live file. **If any instruction below contradicts what `SPEC.md` actually says, report the
contradiction and stop on that part.**

---

## Part 1 — risk comes from config, not from the account

**`SPEC.md` §7b.1 currently reads `1R = risk_pct × NetLiquidation`, with NLV read live and never
configured. That is superseded.** Christoph's ruling, 2026-08-14, stated twice:

> **`1R` is a fixed dollar amount declared in config. It does not move with NLV.**

**Rationale, recorded because it is not obvious.** A risk figure that tracks the account grows
position size on a good run and shrinks it on a bad one, automatically and invisibly. Christoph
wants that behaviour to come later from an explicit rules engine keyed to *sequences of days won
and lost* — not from a number that drifts every time the account marks to market. **c015 §Risk 3:
"Risk should not change daily. It should change after N days won, and get reduced when Y days lost
in sequence."** That engine is a **requirement for a later version, not core.**

```yaml
# config/risk.yaml
risk_usd_per_trade:   500      # THE declaration. 1R. Does not move with NLV.
```

**`risk_pct_default` and `risk_pct_cap` are removed from the sizing path.** If a percentage-of-NLV
sanity check is retained anywhere, it warns and never sizes.

### The consequence for `tws_order`

**`tws_order/sizing.py` enforces NLV-based sizing today** — `1R = risk_pct × NetLiquidation`, with
`risk_pct <= 0` a hard `ConfigError` and the account never guessed. That behaviour is correct and
tested and **must not be deleted.**

**`tws_order` needs an absolute-risk mode alongside it** — `--risk-usd` beside `--risk-pct`,
mutually exclusive, neither defaulted. **The terminal must not compute share counts
independently.** Two sizing implementations that disagree is worse than either being wrong.

**`tws_order` is a separate repo by standing decision.** Report what the change requires; **do not
make it inside this task.** If it cannot be done without touching that repo, say so and stop.

---

## Part 2 — every closed trade is exactly one of four things

**New. Nothing in `SPEC.md` classifies a closed trade today.**

```
R_closed = (avg_exit − avg_fill) ÷ (avg_fill − stop_at_entry)
```

| Class | Condition | Counts against a limit |
|---|---|---|
| **Winner** `W` | `R_closed ≥ +1.0R` | **no** |
| **Partial** `P` | `+0.05R < R_closed < +1.0R` | **no** |
| **Break even** `BE` | `−0.05R ≤ R_closed ≤ +0.05R` | **no** |
| **Loser** `L` | `R_closed < −0.05R` | `losses` cap |

**All four count toward `trades`. Only `L` counts toward anything else.**

```yaml
breakeven_band_r:  0.05      # ± this many R around zero is break even
winner_min_r:      1.00      # at least this many R to count as a winner
commissions:       net       # classification is net of commissions
```

**Three things about this that are load-bearing:**

**The denominator is `stop_at_entry` and it is frozen.** Christoph moves stops up during a trade.
Using the *live* stop makes a trailed winner divide by nearly zero, and makes a trailed loser read
as a full −1R when a quarter was lost. **`stop_at_entry` is an immutable field on the trade record**
and it is the only denominator. Every later stop is management, not risk.

**The band is in R, never in percent of price.** An earlier draft used 1% of entry price. On QQQ at
$733 that is $7.33 per share — **on a 480-share position, $3,518, seven times 1R, classified as
break even.** `0.05R` bounds it at $25.

**Classification is net of commissions.** A $25 gross scratch that cost $2 to trade is a small loss.
Gross-versus-net is an unstated basis, which is this project's recurring defect.

**`W`, `P` and `BE` exist as record fields, not as limits.** They are what makes the reconciliation
question answerable later — *am I cutting winners short?* A month of `P` values clustered near
+0.6R says something specific. Folded into `W`, it would be invisible.

### The test that must exist

**`trades = W + P + L + BE`, asserted.** A counter set that does not sum is a defect that would
otherwise sit unnoticed for weeks. **Seen red by miscounting one class deliberately.**

---

## Part 3 — five limits, and every one of them is a loss limit

| # | Limit | Config key | Window |
|---|---|---|---|
| 1 | Total trades | `trades_max_day` | day |
| 2 | Losing trades | `losses_max_day` · `losses_max_month` | day · month |
| 3 | R lost | `r_max_loss_day` · `r_max_loss_month` | day · month |
| 4 | Dollar safety | `daily_loss_usd` · `monthly_loss_usd` | day · month |

**Reaching any one empties the TRADE panel with the reason and the config key that set it.**

### Two rulings that shaped this list

**There is no cap on winning trades, and none on gains.** v1.0 of this file carried
`winners_max_day: 2` from c015 §Risk 3, and a later draft proposed replacing it with a gain-based
stop, `r_gain_stop_day`. **Both are removed.**

> **Christoph, 2026-08-14: "Some trades run 1:15, especially wins, and closing this trade first
> thing on open might lock me out of a good day."**

**A count cap cannot tell a 15R morning from a lucky scratch — one 15R winner is `1W`, and a second
ordinary trade reaches `2/2`. A gain cap fails the same way from the other side: +15R by 09:35 would
stop trading for the day.** A rule intended to prevent giving back profit would instead fire on the
best morning of the quarter.

**`trades_max_day` still catches overtrading on a good day**, so the case is not unprotected — it is
simply not protected by a rule that cannot distinguish a good day from a busy one.

**Whether Christoph is cutting winners short is a reconciliation question, not a terminal one.** A
month of closed trades carrying `R_closed` and `stop_at_entry` answers it directly. **The rule
cannot be set before the data exists, and once it exists the answer may be that no rule is wanted.**

**Consequence, stated plainly: every remaining limit stops Christoph when it is going badly and
never when it is going well.** That is the whole of the risk model and it fits in one sentence,
which is the test for whether it belongs in core.

**The daily and monthly R limits count losses only, never net.** A +10R swing closing today must not
buy back two losing trades and defer the cap. **Losses accumulate; gains buy no room.** Render net R
alongside as information, with no ceiling:

```
R lost   −1.5R of −2.0R today · −3.5R of −6.0R month
R net    +8.5R today          ← information only, no limit
```

**This also removes any need for the terminal to know whether a trade was intraday or swing.** A
swing position may be open for weeks; because its eventual gain masks nothing, the distinction never
enters the arithmetic.

### One trade is one round trip

**A trade opens when the position leaves zero and closes when it returns to zero.**

**Partial exits are position changes that do not reach zero and are therefore not trades.** This
requires no side logic and no short-versus-sell classification — **the sign of the position carries
the direction**, and IBKR reports position quantity without the terminal having to interpret it.

**The terminal does not close positions.** This definition exists so that counting is unambiguous,
not so that the terminal acts.

### The lock

**The lock blocks staging and nothing else.** No disconnect. No account change. No interference with
an open position. **Every other panel renders normally** — ATTACHED, LEVELS, TAPE, WATCHING,
CONNECTION.

**c015 carries two earlier readings — §Risk 3 "terminal freezes and exits with error" and §Risk 7
"other functionality will disconnect". Both are superseded** by Christoph's ruling of 2026-08-14 and
this is the record of that.

**Reset is 09:30h ET, not midnight.** A trade at 20:00h belongs to the day that is ending.

### The lock outlives the process

**Trades, classification counts, R and dollar totals persist to disk, keyed to the session date.**
Otherwise closing a window clears the limit.

**Open positions are read from the broker, never from disk.** The count is remembered; the position
is read. **When the two disagree, the broker wins and the disagreement is surfaced** — Christoph can
take a trade directly in TWS and the terminal must not silently under-count.

### Paper is a launch flag

**`--paper` at launch. There is no runtime switch, deliberately** — so no order can reach an account
other than the one on screen when the terminal started.

**Relaunching without the flag shows a locked live account and still renders live data** — open
positions, tape, levels, watchlist. **The lock is on staging, not on data.**

**`PAPER` renders on every panel border and on the submit line.** A single corner label is a label
that stops being seen. **Paper keeps its own counters** against the same config limits.

---

## Part 4 — the dollar safety limit is a bug detector

**`daily_loss_usd` and `monthly_loss_usd` already exist in `SPEC.md` §7b.1 as hard blocks. Their
purpose is now recorded, because it is not what it looks like.**

**It is not a second risk rule.** Limits 1–3 already govern trading. **The dollar limit catches the
cases where the R arithmetic above it is no longer true:**

1. **Christoph moves a stop in TWS and the terminal never sees it.** A stop moved 10× wider produces
   a 10R loss the R counter records as 1R.
2. **A fill lands badly on a volatile name** and 1R is really 1.3R.
3. **A defect** — in the terminal, the OS, the network or the broker. *Something that should not
   happen, happening anyway.*

**If it fires, the finding is that the R accounting is wrong, not that Christoph traded badly.** **A
safety net that only catches anticipated errors is not a net.**

**Task `040` establishes whether case 1 is closable.** Do not assume either answer here.

---

## Part 5 — the panel

**Specification of content, not layout. No panel work in this task.**

```
account  LIVE *1234
open     2R · 384 sh
trades   3/5 today  ·  1W 1P 1L 0BE
losses   1/2 today · 4/12 month
R lost   −1.0R of −2.0R today · −3.5R of −6.0R month
R net    +8.5R today
safety   −$180 of −$2,000 today · −$3,110 of −$5,000 month
risk     $500 per trade (config)
```

**Every limit renders its ceiling.** A number with no ceiling on screen cannot tell you how close you
are until it stops you. **`R net` has no ceiling because it has no limit** — and that difference must
be visible, not inferred.

**Dollars appear on the `safety` row and the `risk` row only.** c015 §Risk 2: *"Seeing dollars made
and lost encourages overtrading and/or revenge trading."* **Dollar P&L is recorded for data
collection and never rendered.**

**`open 2R · 384 sh`** — two open positions totalling 384 shares.

### One open question, to be reported not decided

**`0.05R` and `1.0R` are unfitted thresholds.** They no longer gate anything — no limit depends on
them — so they are classification only. **Ship the values, render them `unfitted`, and answer them
from the record.** Tenet 6: thresholds do not transfer.

---

## Part 6 — the new record fields

**Report what exists and what is missing. Build only what is trivial.**

| Field | Why |
|---|---|
| `stop_at_entry` | **Immutable. The R denominator.** Expensive to add later |
| `avg_fill` · `avg_exit` | Classification inputs |
| `commissions` | Classification is net |
| `class` | `W` · `P` · `L` · `BE`, derived and stored |
| `session_date` | The key the daily counters reset on |
| `ema9` · `ema21` at entry | **c015 §5b: "new requirement for trade data collection".** Never rendered |

**`ema9` and `ema21` are the one requirement here with no screen presence at all**, which is exactly
the kind that gets lost. **Record it in `docs/observations/OBSERVATIONS.md` if it is not built in
this task.**

---

## Not in scope

No panel work. No `tws_order` changes — report only. No rules engine. No slippage or fill-time
measurement (c015 marks it future). **No order staging** — that is slice 017 and hard-gated on
Christoph's written release. **No reconciliation module** — that follows core.

---

## Last action

**Run `verify.ps1`.** Do not paste or summarise. Do not quote a test count.
**Then run the export**, from the main checkout — not from a worktree (`OBS-045`).

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | `verify.ps1` ran with the classification and sum tests; both seen red first |
| **Refusal** | Claude Code | A trade with no `stop_at_entry` classifies as `unavailable (no entry stop recorded)` — **never as break even** |
| **UAT** | Christoph | `c019` — set `trades_max_day: 1` in config, take one paper trade, confirm TRADE empties with the reason and the config key, and that every other panel still renders |

---

## Report

1. What `SPEC.md` §7b.1 said before, verbatim, and what it says now.
2. Whether `tws_order` can take absolute risk without modification — and if not, exactly what is required.
3. Which of Part 6's fields already exist.
4. **Whether anything in the tree still references a winners cap or a gain-based stop.** v1.0 of this file specified one; it must not survive anywhere.
5. The two reds, quoted.
6. **Any contradiction between this file and `SPEC.md`**, and where you stopped.
7. **What you could not do**, and why. Empty is suspicious.
