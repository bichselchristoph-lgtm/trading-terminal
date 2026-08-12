# 019 — QQQ tape capture, 2026-08-12, unattended

**Status** WRITTEN · **Date** 2026-08-12 · **Type** capture · **Tree** `D:\Dev\momentum`

> **Number not confirmed.** If `019` is taken, say so and this file is re-issued.
>
> **CHRISTOPH IS NOT AVAILABLE DURING THIS SESSION.** No question can be answered, no gate can be
> advanced, and no decision can be taken between the start of this task and the close. **If
> something needs a decision, do not guess — stop that thing, keep the capture running, and
> report it.** The capture is the deliverable; everything else is optional.

---

## The order of operations, and why

**1 · `018` part 1 first.** It reads `records/tape/` and the capture writes there. **It must
complete before the capture starts, or wait until after 16:00 ET.** It is a read of yesterday's
file and takes minutes.

**2 · Then this task.** Start as soon as part 1's read is done. **Pre-market is free and a late
start on an unrepeatable session is not** — `012` started 09:06 ET deliberately.

**3 · `018` parts 2–7 run during the session.** They touch the TUI and tests, open no TWS
connection, and write nothing to `records/`. `016` made the suite 2.4 s, so running it during a
capture is safe.

---

## Part 1 — before connecting

**Check free disk.** The capture needs roughly **2.5 GB**. Report free space as a number.

**If under 20 GB free: report it and continue.** The threshold is advice, not a block —
Christoph's rule. **If under 5 GB free, do not start**: an out-of-disk failure mid-session
produces a truncated file that looks like a capture and is not.

**Confirm TWS is up on 7496** and that no other client is holding `clientId 11`.

---

## Part 2 — the capture

**Identical configuration to `012` as amended by `012a`. Change nothing.**

| | |
|---|---|
| symbol | **QQQ** |
| `clientId` | **11** |
| streams | three — trades, quotes, depth |
| trades | `reqTickByTickData(contract, "AllLast")` |
| depth | **ARCA**, `numRows=10` |
| format | raw append-only JSONL, flush every 100 records |
| gap records | into every stream |
| heartbeat | 60 s |
| per-line | `quote_basis`, `bid_exchange`, `ask_exchange` |
| connection | `readonly=True` |
| run until | **16:00:00 ET** |

**Do not modify `tools/capture_tape.py`.** Not to add a field, not to fix the row-position
question `018` part 1 is investigating, not to improve anything. **A change to the capture tool
minutes before an unrepeatable session is the risk this project exists to avoid**, and matching
`012`'s configuration exactly is what makes the two sessions comparable at all.

**Do not add tickers.** A multi-ticker run has never been specified, its line-count budget is
undecided, and inventing one under time pressure is how a session gets lost.

### The four live-verification assertions, as in `012`

1. The code path calls `reqTickByTickData`, not `reqHistoricalTicks`.
2. Trade timestamps within 5 s of system clock, continuously.
3. Record count strictly increases across three consecutive heartbeats.
4. First five trades printed with timestamps.

**If any assertion fails, report it and keep capturing.** A flawed capture that is recorded and
labelled is worth more than no capture; a stopped capture cannot be restarted for this session.

---

## Part 3 — while it runs

**Do not touch `records/tape/` beyond writing the capture.** No reads of the live files, no
size checks that open them, no compression, nothing moved or renamed.

**Nothing is committed from `records/`, ever.**

If TWS disconnects: **reconnect and record a gap record.** That is what gap records are for.
Report every disconnection with its duration. **Do not silently resume.**

---

## Part 4 — at the close

Write `handoff/done/019-*.md` carrying, at minimum:

- **Per-stream counts, bytes, first and last timestamps, and gap count.**
- **The four assertions, each with its result.**
- **Any disconnection**, with duration and what the gap record says.
- **Free disk before and after**, as measured numbers.
- **A per-venue trade breakdown**, as `012` produced — it is free and it is the comparison that
  makes two sessions worth having.
- **How this session differs from `012`'s**, in counts and in venue mix. **State differences as
  observations. Do not explain them** — a same-instrument comparison across two days is exactly
  where a plausible reading becomes a premise.

**No delta computed. No row scored. Nothing fitted.**

---

## Do not

- Do not modify `tools/capture_tape.py`, or any capture configuration.
- Do not add symbols, venues, or streams.
- Do not delete, move, compress or rename anything in `records/`.
- Do not commit any JSONL.
- Do not write to `christoph/open/` or `christoph/done/`.
- Do not change any subscription or sign up for anything.
- **Do not stop the capture to fix something.** Report it and keep running.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | Capture runs to 16:00:00 ET. Four assertions reported with results. Counts and bytes stated. |
| **Refusal** | Claude Code | **A gap must be recorded as a gap, never as absence.** If no disconnection occurs, state that the gap-record path was not exercised — do not report an untested path as passing. |
| **UAT** | **None.** Machine-checkable, and Christoph is unavailable. |

## Done-note must state

- Everything in part 4.
- **Whether `018` part 1 completed before the capture started.** If it did not, say so — the
  read is then owed after 16:00 ET and `018` part 1 stays open.
- Anything in this task that was wrong on contact.
