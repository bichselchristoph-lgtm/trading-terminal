---
id: 031
title: Does the tape session ledger survive to the next day?
type: decision
bug: B-069
blocks: RECORD-SPEC section 10, and what the ledger row claims
---

**Status** OPEN

# 031 — does the tape ledger persist across days?

## The question

**A level accumulates a ledger across every visit in a session. Does it reset at 09:30 with
everything else, or carry forward?**

## Why it changes what the row means, not just how long it lives

**Today:** *733.40 — 6 visits, 4.8M sh sold into it, not broken.* **A claim about one session.**

**Carried forward:** *733.40 — 19 visits over 4 days, 14M sh sold into it, not broken.* **A different
and much stronger claim** — a seller who has been working one price for four days is a different
object from one working it since 09:31.

## What makes it hard

**The coverage line has to carry days, not minutes.** *Watched 09:31–10:14, 48 min not watched*
becomes *watched 6 of 22 hours across 4 sessions* — **and with one tape slot, the gaps will dominate.**

**A ledger claiming four days of accumulation while having watched a quarter of it is absence
rendered as history.** That is the defect this whole design exists to avoid.

## My recommendation

**Reset at 09:30, same as everything else.**

**Not because multi-day is wrong — it is the more interesting claim — but because the coverage
problem gets worse the longer the window.** One tape slot means one symbol at a time, and a four-day
ledger on a name you watched for six hours would look authoritative and be mostly holes.

**Revisit when more than one symbol can carry tape.**

## To answer

Reset, or carry forward. Copy this file to `christoph/done/` with the date.
