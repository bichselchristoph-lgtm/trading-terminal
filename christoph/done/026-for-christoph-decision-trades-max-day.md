---
id: 026
title: trades_max_day is 3 in one source and 5 in another
type: decision
bug: B-016
blocks: the sizing slice S011
---

**Status** OPEN

# 026 — `trades_max_day`

## The question

**Three, or five?**

The RISK mockup renders `trades 2/3`. Task `039` set `trades_max_day: 5`. **Both are in the tree and
neither cites the other.**

## What the cap is actually for

**It is the only limit that catches overtrading when the R limit does not.** Your own case: *"If I
close a good swing with 10Rs, two losing trades would vanish in R today"* — **gains buy no room
against the losses cap, but they do mask R, and the count cap is what covers that gap.**

**Four 0.25R losses never reach the R cap and are still four losing trades.**

## Which number is which

**Neither is fitted.** The 3 was drawn into a mockup as an illustration; the 5 was written into a
task. **Neither has a source string behind it, so this is a preference and preferences cannot be
wrong** — but it must be one number, in config, with `source: christoph_preference`.

## My recommendation

**Three.** It is the tighter of the two, it matches the mockup you reviewed, and **the cost of being
wrong is asymmetric**: too low costs you a trade you can take tomorrow, too high costs you a day you
should have stopped.

**Revisit it from the trade record after a month rather than from argument.**

## To answer

5 trades max per day.

One number. Copy this file to `christoph/done/` with it and the date.
