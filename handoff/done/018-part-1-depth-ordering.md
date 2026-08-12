---
id: 018-part-1
title: Is the ARCA depth capture reconstructable?
status: RUNNING — stays RUNNING until this note reaches the design session
owner: claude-code
ran: 2026-08-12, 16:05 ET
tree: D:\Dev\momentum
---

# 018 part 1 — the depth-ordering question, answered

**Status** RUNNING

**Why this is a separate note.** `018`'s done-note is already in `handoff/accepted/`, and
`013d` established that an acceptance copy is byte-identical to its done-note — verified by
hash. **Amending `handoff/done/018-depth-ordering-and-uat-findings.md` would break that**, and
`018`'s own *Do not* list protects it. `HANDOFF-PROTOCOL.md` rule 6 says a task found wanting
after the fact is reopened as a new file rather than silently amended; the same logic covers a
part deliberately deferred.

**Part 1 ran after 16:00 ET**, once `019`'s capture had closed. `records/` was **read only** —
nothing written, moved, renamed, compressed or deleted.

---

## The short answer

**YES — the ordering is reconstructable, and the book is intact.**

**But the file does not say so anywhere, and a consumer reading it the obvious way gets the
wrong best bid 99.9 % of the time.**

---

## 1 · The fields each depth record carries, quoted from the code

`tools/capture_tape.py:231-242`:

```python
    def _depth_update(self, t) -> None:
        if not self.depth:
            return
        bids = getattr(t, "domBids", None)
        asks = getattr(t, "domAsks", None)
        if not bids and not asks:
            return
        self.depth.write({
            "ts": iso(now_utc()),
            "bids": [{"price": l.price, "size": l.size, "mm": l.marketMaker} for l in (bids or [])],
            "asks": [{"price": l.price, "size": l.size, "mm": l.marketMaker} for l in (asks or [])],
        })
```

**Three fields: `ts`, `bids`, `asks`.** Each level carries `price`, `size`, `mm`.

**There is no `position` key.** The row position is **not written as a field.**

**But nothing sorts, reorders, normalises or filters.** The comprehension iterates `domBids`
and `domAsks` **in their own order**, so the array index *is* the DOM row position, preserved
exactly. `getattr` with a `None` default and the `or []` guard mean a one-sided book is written
as a one-sided book rather than being padded or dropped.

---

## 2 · A verbatim sample from the capture

`records/tape/QQQ-2026-08-12-depth.jsonl`, first three lines:

```
{"_record": "START", "wall_utc": "2026-08-12T13:07:31.087584+00:00", "symbol": "QQQ", "client_id": 11, "depth_exchange": "ARCA", "provenance": {...}}

{"ts": "2026-08-12T13:07:34.230970+00:00", "bids": [{"price": 725.6, "size": 81.0, "mm": ""}], "asks": []}

{"ts": "2026-08-12T13:07:34.230970+00:00", "bids": [{"price": 725.6, "size": 81.0, "mm": ""}, {"price": 725.58, "size": 40.0, "mm": ""}], "asks": []}
```

**The book builds up level by level from empty**, which is what a fresh `reqMktDepth`
subscription looks like. `mm` is empty on every ARCA row.

---

## 3 · Is ordering reconstructable? **YES — with the reasoning shown**

**The array index is the DOM position.** IBKR delivers positional rows that mutate in place;
the writer preserves list order; therefore `bids[i]` in the file is `domBids[i]` at that
instant. **Nothing is lost.**

**What is NOT true is that the array is price-ordered.** Measured over the first 20,000
snapshots of the session:

```
snapshots checked      : 19,999
bids NOT price-sorted  : 19,970  (99.9%)
asks NOT price-sorted  : 19,946  (99.7%)
```

A concrete one, at `2026-08-12T13:07:34.511274+00:00`:

```
bids: [725.60, 725.58, 725.55, 725.54, 725.40, 725.16, 725.00, 724.88, 724.80, 725.55]
                                                                              ^^^^^^^
                                                            index 9, and it beats indexes 4-8
```

**`domBids[0]` is not the best bid**, and the highest-priced level sits at index 9. Note also
that `725.55` appears at **both index 2 and index 9** — duplicate prices across rows are normal
for a positional book and are not a defect.

**This confirms `S009a`'s live probe rather than contradicting it.** That probe saw the best bid
at index 6 and was recorded as an observation with an unestablished cause. **The cause is now
established: positional rows, exactly as inferred, and it is the normal case rather than an
anomaly** — 99.9 % of snapshots, not a rare event.

---

## 4 · What is lost — precisely

**No question about the book's contents can no longer be answered.** Price, size, market maker
and row position are all present for every level of every snapshot. The book at any instant is
fully reconstructable, and so is its evolution.

**What is lost is self-description, and that is a real cost:**

**The file nowhere states that the array index is a row position rather than a price rank.**
There is no schema line, no `position` key, and no field name carrying the semantics. A
consumer who opens this file and reads `bids[0]` as the best bid — which is the obvious reading,
and the one every price-sorted book format invites — **will be wrong on 99.9 % of snapshots**,
and wrong in a way that produces a plausible number rather than an error.

**That is the failure signature this project keeps naming.** A wrong best-bid is not obviously
wrong: it is one tick off, it moves like a real quote, and it would pass every sanity check
short of comparing against a second source.

**The concrete exposure.** `019` and `012` together hold **4,324,111 ARCA depth records** across
two unrepeatable sessions. Any future consumer — the level machine in `S012`, the order-flow
work behind Row 14 — inherits this. **Nothing in the capture, the done-notes or the tree warned
about it until now.**

---

## What I did NOT do

**Nothing was fixed and `tools/capture_tape.py` was not touched.** Part 1's instruction is
explicit: *this part establishes what is true; what follows from it is a decision that needs the
answer first, and inventing a repair before the diagnosis is the pattern this project keeps
paying for.*

**For the record, and as a statement of options rather than a recommendation to act:** adding a
`"position": i` key would make future files self-describing but would not touch the two sessions
already captured; a documented schema note would cover both. **Which — or neither — is
Christoph's call.**

**The two existing sessions need no re-capture.** That is the substantive good news: the data is
complete and correct, and only its reading is at risk.

---

## Ledger

Recorded as **OBS-017** in `docs/observations/OBSERVATIONS.md`, status `OPEN`, citing this note.
It is deliberately **not** `PROMOTED`: the diagnosis is settled, the decision that follows from
it is not.

---

**Paste this into chat. It stays `RUNNING` until it lands there.**
