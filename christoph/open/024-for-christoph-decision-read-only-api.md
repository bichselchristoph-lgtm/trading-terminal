---
id: 024
title: Read-Only API is on in TWS, and it blocks phase 1 entirely
type: decision
bug: B-022
blocks: every staging slice, and therefore phase 1
---

**Status** OPEN

# 024 — Read-Only API

## The question

**Read-Only API is checked in TWS. Do you turn it off?**

## Why it needs you and not me

**It is a security control.** Every rule in this project puts those on you unconditionally — not as a
gate I ask you to click through, but because **it is the one class of decision the design session
should not be able to take.**

## What it costs either way

**On:** the terminal cannot place an order at all, including `transmit=False` staging. **Phase 1
does not exist.** The terminal is a monitor, permanently.

**Off:** staging works. **And the API can place live orders** — the terminal is designed never to,
`tws_order` is the only thing that does, and *"nothing transmitted from here"* is on the panel. **But
the control that made that structurally impossible is gone, and what remains is design plus
discipline.**

## My recommendation

**Off, when you are ready to start phase 1 — and not before.**

There is no reason to remove the control while nothing stages. **The gates that replace it are real:
`transmit=False` on all three legs, and you pressing transmit in TWS.** But they are software, and
this is not.

## To answer

Copy this file to `christoph/done/`, add your ruling and the date at the bottom.
