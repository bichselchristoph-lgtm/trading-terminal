---
id: 030
title: The safety monitor — four linked decisions, none taken
type: decision
bug: B-072
blocks: the safety slice, which cannot be written until all four are ruled
---

**Status** OPEN

# 030 — how the safety monitor runs

**Four questions. They are one decision because each answer constrains the others.**

## 1 — Its own IBKR connection, and on which client id

**It must not read the terminal's counters** — if the terminal's R accounting is what broke, a limit
computed from it inherits the defect and reports comfortably that all is well.

**So it needs its own connection to the same account.** Two connections is a real constraint, not a
detail. **And the master client id is the only one receiving commission reports for all executions,
which makes it an input to classification** — task `040` establishes that by observation.

## 2 — How it runs, given the terminal must not start it

**If the terminal started it, its absence would become invisible exactly when the terminal fails to
start it** — and the monitor exists for the case where the terminal is the thing that is broken.

**Scheduled task, Windows service, or you launch it beside the terminal.**

## 3 — How often

**Every N minutes, or on every execution.** Cheap either way; the cost is pacing budget and a second
connection held open.

## 4 — Does a mid-session breach lock immediately, or at the next trade?

**Immediately is louder and can interrupt you mid-position.** **At the next trade is gentler and lets
one more trade through after the limit was already breached.**

## My recommendation

**Scheduled task, every 5 minutes, locks immediately, own client id — not the master.**

**Immediately, because the lock blocks staging only.** It never disconnects, never touches an open
position, and never blocks a `SELL` or `CLOSE`. **So "interrupting you" means refusing a new trade,
which is the entire point.**

## To answer

Four answers. Copy this file to `christoph/done/` with them and the date.
