---
id: 014
title: The two account numbers only you can supply
status: OPEN
type: EXTERNAL
owner: christoph
blocks: [S011-sizing-risk-and-limits]
---

# 014 — The two account numbers only you can supply

**Everything else about sizing is decided.** The mechanism is specified, the limits are set
in dollars, and the rules are written. **Two values remain, and neither can be inferred from
anything in the repo.**

---

## 1. Your NetLiquidation, so `risk_pct_default` can be set

**Risk is declared as a percentage of NLV, deliberately** — position size must compound as
the account grows and contract as it shrinks, with nothing to re-tune. A fixed dollar risk
would be the defect.

**But the starting percentage has to land near $500 of risk per trade**, which needs your
actual account value:

| NLV | `risk_pct_default` for ≈ $500 |
|---|---|
| $100,000 | 0.50 % |
| $125,000 | **0.40 %** |
| $150,000 | 0.33 % |
| $200,000 | 0.25 % |

**$124,300 has been used throughout the spec as an illustration and is not your number.**

**Once set it does not need revisiting as the account moves** — that is the whole point of
declaring a percentage. **NLV itself is read live from IBKR at session start and is never
configured**, so this is the only place the account size enters by hand.

**What I need:** your NLV to the nearest thousand, or the percentage directly if you would
rather not state the balance. Either settles it.

The percentage is 0.02%. 

---

## 2. Confirm the two loss limits against your own history

**Decided and recorded: `daily_loss_usd: 2000`, `monthly_loss_usd: 5000`.** Both are hard
blocks — **the only two things in the entire terminal that stop you.**

**One consequence is worth seeing before it fires, because it is not obvious from the
dollars.** At roughly $500 of risk per trade:

- **$2,000/day is four losing trades.**
- **$5,000/month is ten** — and **two and a half full stop-out days.**

change daily_loss_usd to 1000. Approx. two loosing trades.

**So the monthly limit binds well before any slow bleed reaches it.** Two bad days and part
of a third ends the month. That may be exactly the discipline you want; it is not the
relationship most people picture when they write those two numbers down.

reduced daily_loss_usd to half. 

**Both rows therefore render headroom in losses as well as dollars** — `5.4 of 10 losses
left` rather than only `−$2,690`, because the second reads as a lot of room and the first
reads as what it is.

yes

**What I need:** either *"confirmed"*, or replacement numbers. **If you have your own trade
history to pick from, use it** — these two are exempted from the no-unfounded-numbers rule
only because the alternative is no limit at all, and that exemption is worth spending as
little as possible.
change daily_loss_usd to 1000. Approx. two loosing trades.

---

## Also, when you have a morning to spare

**`handoff/inbox/021-for-code-keepuptodate-at-scale.md` must be started by 09:25 ET** and
held to 16:05. It closes all three of 008b's open deviations in one run and answers the one
question none of them could separately: **whether the ~5 s update cadence survives five
concurrent streams on one account, or whether 5.002 s was a single-stream artifact.**

done

**That number decides whether `keep_up_to_date` stays the default for a five-symbol console.**
It blocks nothing today — `cum_refresh_s: 120` is a working fallback — but it should be
answered before five symbols are ever attached at once, because that is the morning the
failure would arrive.

**It is read-only, holds no tick slots, and will not interfere with trading** — but it will
be running, so choose a morning where you do not mind that.

---

## Return

Answers here, in this file, moved to `christoph/done/` when complete. **Two numbers and a
date is the whole deliverable.**
