---
id: 033
title: Ten sessions of auction imbalance, by hand — the cheap test that decides a whole line of work
type: decision
bug: B-061
supersedes: c016, allocated and never written to christoph/open/
blocks: whether any auction work is ever specified
---

**Status** OPEN

# 033 — read the auction by hand, ten sessions

## What this asks of you

**Three names. Two minutes a day. Ten sessions. No code.**

Before the open, read the auction imbalance for each. Write down the number, the side, and what the
first fifteen minutes did. **Nothing else.**

## Why it is worth two minutes

**It decides whether an entire component is ever built.** If the imbalance predicts nothing on your
names, **this ends here and no slice is written — and that is a good outcome that cost twenty
minutes total.**

**It is the one stage this project has never done in the right order.** Every other component was
specified first and tested against reality afterwards, if at all.

## Why it cannot be answered from data instead

**The auction is not in the tape corpus.** And the question is not *does imbalance predict* in
general — it is *does it predict on the names you actually trade, in the window you actually trade
them.* **Ten of your own sessions answers that; a backtest on someone else's universe does not.**

## A note on the number

**This was allocated as `c016` and the file was never written.** It has been cited in the bug sheet
for days as though it existed. **`c016`, `c017`, `c020` and `c022` are all allocated with no file in
either folder** — a separate finding, raised as its own row.

## To answer

**Ten rows of notes**, or *"tried it, predicts nothing, drop the auction."* Copy this file to
`christoph/done/` with your notes and the date.

**A negative result closes the question permanently and is worth as much as a positive one.**
I do have auction imbalance data available. Rather than me testing, I defer to research:

Short answer: not directionally, no. The published evidence says opening-auction imbalance is mostly absorbed into the opening print itself, and whatever residual signal remains points to reversal, not continuation — the opposite of what an ORB entry needs. Its useful content is magnitude, not direction.

The reasoning, briefly:

The imbalance is public before it's tradable. Nasdaq disseminates NOII from 9:28, NYSE imbalances from 7:30/8:00. By 9:30 the auction price has already cleared against it — you're trading the residual, not the information.
The residual is retail-flow reversal. Brown (2025) finds publicly observable retail order flow at the open predicts short-term reversals, and sizes the transfer at ~$16bn to wholesalers. A momentum trader buying the ORB high on a big buy imbalance is on the wrong side of that.
Closing-auction imbalance is the one with documented directional predictability — different animal, different mechanism (index/MOC flow with a known deadline).
Pre-auction imbalance is strongly mean-reverting in the indicative-price dynamics work, so late imbalance readings are noisy as a level.

What does separate ORB winners from losers in the literature is relative volume / gap / "stock in play" selection — which is a screening variable. That's where imbalance would earn a place in the terminal: imbalance_shares / ADV as a participation measure feeding the watchlist sort, never as a direction arrow. That also keeps it inside the no-verdict-colour rule — it's a magnitude, and it has an obvious refusal state (no imbalance feed, or unpaired-only, renders nothing).

Want me to spec it that way for a LEVELS/TAPE open question row, or dig into whether IBKR even exposes NOII/NYSE imbalance through the API you have? (I suspect it doesn't cleanly — that's the real gate.)

Sources: The Quote Not Taken — Brown, SSRN · Dynamical regularities of US equities opening and closing auctions · Predicting US stock returns using closing auction imbalance data (Imperial) · Nasdaq Opening and Closing Crosses · Assessing the profitability of intraday ORB strategies