---
id: 032
title: Does a gapped-over level mean untradeable, or more live?
type: decision
bug: B-080
blocks: LEVELS-SPEC section 8.4, and the colour treatment in 8.3
---

**Status** OPEN

# 032 — what does `gapped over` mean to you?

## The question

**Price jumped the level without ever trading at it. Is that a level you avoid, or one you watch more
closely?**

## Why the terminal cannot answer it

**The distinction it already makes is mechanical and settled:** a level jumped over is **loaded** —
nothing was resolved there; a level traded through with volume is **spent**.

**But loaded cuts both ways and only a playbook decides which.** No dataset says whether you take
trades at untested levels, and **fitting it would be the terminal deciding what you trade.**

## The two readings

**More live.** Nobody defended it and nobody paid to break it. **The fight has not happened yet**, so
the level is intact and the first test of it is the real one.

**Untradeable.** A gap means the market repriced without an argument at that price. **There is no
evidence anyone cares about that number**, and a level nobody contested may not be a level at all.

## What it changes on screen

**The colour treatment for `gapped over` versus `clear for`** — the two must be distinguishable, and
**colour marks kind or relation, never importance**, so the answer cannot be *"gapped over is more
important."* It has to be a kind.

## My recommendation

**Rule it only if a playbook depends on it.** If none does, **record it as deliberately unsettled**
rather than picking one — an unfitted preference written into a spec is a threshold pretending to be
a definition.

## To answer

A reading, or *"not settled and no playbook needs it."* Copy this file to `christoph/done/` with the
date.
