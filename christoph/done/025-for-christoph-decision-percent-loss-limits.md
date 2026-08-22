---
id: 025
title: The two percentage loss limits have no values
type: decision
bug: B-074
blocks: the safety layer — it cannot ship its percent limits
---

**Status** OPEN

# 025 — `daily_loss_pct` and `monthly_loss_pct`

## The question

**What are they, as numbers?**

Your own words in c015 §Risk 6: *"max loss in % and value"* — **both.** The dollar figures are set:
`daily_loss_usd: 1000`, `monthly_loss_usd: 5000`. **The percentages are empty and a missing key
refuses**, so the safety monitor cannot run its percent half at all.

## Why both exist rather than one

**The dollar limit stops tracking the account as it grows.** **The percentage is of NLV, and an NLV
that is itself misreported is not a backstop** — which is one of the three cases the safety layer
exists for.

**Whichever binds first, binds.** They are not redundant; they fail differently.

## What would make them consistent with what you already set

**$1,000 daily was your figure, described as *"approx. two losing trades"* at $500 risk each.**

**So the percentage should be whatever $1,000 is against the NLV you consider normal.** If that is
roughly $125,000, daily is **0.8%** and monthly **4.0%** — which is the pair currently drawn in the
RISK mockup as an illustration, **not as a decision.**

## My recommendation

**Set them from your own NLV, not from the mockup.** The mockup's numbers were invented to show the
row and have been sitting there looking decided — **that is B-054, and it is exactly how the VWAP
band survived.**

## To answer




`risk_pct_default_daily= 0.04%
`risk_pct_default_monthly= 0.02% 

#updated: in D:\Dev\momentum\christoph\done\014-for-christoph-account-parameters.md as well. 
Two numbers. Copy this file to `christoph/done/` with them and the date.
christoph aug 22, 2026