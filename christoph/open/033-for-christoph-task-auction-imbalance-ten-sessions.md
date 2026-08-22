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
