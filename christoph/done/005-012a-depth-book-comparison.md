**Status** REVIEWED — answered by events, awaiting Christoph's confirmation
**Type** UAT · **Date** 2026-08-11 · **For** Christoph
**Task** 012a
**Done-note** `handoff/done/012a-preopen-correction.md`

# 005 — The two depth books that never existed

---

## What it asked

Compare the ARCA book against the `ISLAND` book, if depth moved to `ISLAND`.

## Why it cannot be performed

**Depth never moved.** `ISLAND` and `NASDAQ` both returned code 10089 naming the same feed, `NASDAQ.NMS/DEEP` — one route, not two. Depth stayed on ARCA.

So there are no two books to compare. **The UAT was written against a hypothesis that the probe disproved**, and the design session wrote the hypothesis.

## What was observed instead

ARCA, same session, two times:

| time | dimensions |
|---|---|
| 04:38 ET | 4 × 3 |
| 05:07 ET | 9 × 9 |

**That is the book filling out pre-market, not a venue difference.** It is also where the design session misread `240` — the top-level share *size* — as book dimensions, and wrote `240×240` into a task file as a comparison target that never existed.

## What is actually owed

**Nothing to perform.** Confirm you agree this is closed, and it moves to `christoph/done/`.

**One thing is genuinely open and it is not this**: why an account holding TotalView receives 10089 *for API* on `NASDAQ.NMS/DEEP`. That is `christoph/open/001`, and it matters only if you want QQQ's primary book for a later capture.
