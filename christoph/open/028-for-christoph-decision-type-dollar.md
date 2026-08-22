---
id: 028
title: Type$ — you asked how it would work, and the answer is still a proposal
type: decision
bug: B-075
blocks: the TRADE panel's sixth stop target
---

**Status** OPEN

# 028 — how `Type$` works

## The question

**Your own open, verbatim: *"Type$ (type stop price, how will this work)."***

**The design session proposed an interaction and you have never confirmed it.** It is in TRADE-SPEC
§5 and it is labelled a proposal, not a decision.

## The proposal

```
▸ Type$   731._                —           —
  select the row, type digits, enter commits · esc cancels
  no $0.05 offset applied — you typed the stop you want

— after enter —
▸ Type$   $731.20         $731.20      257 sh
```

**Select with the arrows like any other target, type, enter commits, escape cancels.**

## The two decisions inside it

**No offset.** Every other target is pushed five cents past its level, because no stop should sit
exactly on the price most likely to trade. **A typed stop is the stop you meant** — but that means
`Type$` behaves differently from every row above it, and the panel says so on the line.

**Wrong-side stops refuse loudly rather than vanishing.** A `HOD` above price is removed from the
list; **a typed stop above price stays and refuses**, because you entered it deliberately and removing
it would look like the keystroke was lost.

## My recommendation

**Confirm as proposed, or correct the two decisions above.** They are the parts that will feel wrong
in use if they are wrong.

## To answer

Confirm, or say what changes. Copy this file to `christoph/done/` with the date.
