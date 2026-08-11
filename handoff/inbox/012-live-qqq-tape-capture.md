# 012 — Live QQQ tape capture, 2026-08-11

**Status** RUNNING · **Date** 2026-08-11 · **Type** capture · **Window** 09:00 ET → close, today only

> **State header note.** `WRITTEN` is the only state the design session can assert from its own side. If this file is already in the inbox or already running, correct the header to `HANDED OFF` or `RUNNING` — see `docs/specs/HANDOFF-PROTOCOL.md`.
**Runs in** `D:\Dev\momentum`. Requires TWS running and logged in before 15:00 SAST.

> Read this cold. The session that wrote it cannot answer questions. **This task has a deadline that does not come back — today's session happens once.**

---

## Why

**Row 14 of the Layer 0 ratification card is defined in order-flow delta** — *"declining sell delta"*, *"expanding sell delta"* — and OHLCV cannot express it. On 2026-08-10 it scored `null` on the floor's first live firing, and it will score `null` every session until an order-flow source exists. The reduced-card floor therefore fires permanently and does not self-resolve.

**Tape data exists for QQQ.** This task captures it live so row 14 has a basis. It does **not** score row 14, adopt any module, or decide anything — it puts raw prints on disk before another session is lost.

**Multi-ticker capture is deliberately not in this task.** A second subscription set started alongside this one risks IBKR throttling or terminating the first, and today's session is unrepeatable. Multi-ticker runs tomorrow at the open, as task 013.

---

## Phase 0 — reads, now, before the market opens

No market data required. **Report all five before writing any capture code.**

**0a.** Read `live/tape/tape_reader.py` and `live/tape/rolling_flow.py` in `momentum-harness`. Report whether the reader emits a **signed delta series** or **raw prints needing aggregation**, and **what exact rule classifies a print as buy or sell** — at-ask/at-bid against the quote in force, tick rule, or something else. **Quote the code.** Do not adopt either file; this is a read.

**0b.** Report all tape data already on disk under `D:\Dev` — Databento or IBKR, any symbol. Paths, date ranges, format, row counts. **Download nothing.**

**0c.** Verify **from IBKR documentation or the API, not from memory**, the concurrent tick-by-tick subscription limit and this account's market data line count. Report how many lines today's capture will consume. This number decides what task 013 can attempt tomorrow.

**0d.** Confirm `ib_async` imports, the TWS API is enabled, and the port.

**0e.** Report whether `reqMktDepth` works on QQQ and **on which exchange** — SMART does not serve depth, so name the exchange that does — and whether this account holds the depth subscription. **If it does not, say so and skip L2 entirely. Do not sign up for anything.**

---

## Phase 1 — capture

`tools/capture_tape.py`. **Standalone. Imports nothing from `live/`.** This is not an adoption and must not become one by accident — `live/tape/` remains un-adopted and undecided.

`clientId 11`.

### Three streams

```
D:\Dev\momentum\records\tape\QQQ-2026-08-11-trades.jsonl   reqTickByTickData("AllLast")
D:\Dev\momentum\records\tape\QQQ-2026-08-11-quotes.jsonl   top of book, every change
D:\Dev\momentum\records\tape\QQQ-2026-08-11-depth.jsonl    reqMktDepth — only if 0e says yes
```

**Every trade line carries the bid and ask in force at that moment, plus the quote's own timestamp.** This is the single most important field decision in the task: it keeps trades classifiable even if the quote file is lost, and it records *which* quote the classification would use rather than leaving a later reader to guess.

### Rules

1. **CAPTURE RAW ONLY.** No buy/sell classification, no delta, no aggregation, no resampling. Derivation happens after the close, from the stored files, and **must be re-derivable differently later.** A capture that computes is a capture that cannot be recomputed under a different rule — and 0a exists precisely because the classification rule is not yet settled.
2. **Append-only**, flush every 100 records. A crash must not cost the session.
3. **On disconnect, write an explicit gap record** with start and end timestamps, then resume. **Never resume silently** — an unmarked gap is indistinguishable from a quiet market.
4. **Heartbeat every 60s**: per-stream counts, last timestamp, connection state.

### Live verification — a required gate, not a nicety

**Prove the stream is live before accepting the capture as running.** Report all four:

1. **The code path uses `reqTickByTickData`, not `reqHistoricalTicks`.** State which function is called.
2. **Trade timestamps stay within 5 seconds of system clock, continuously** — not checked once. If the gap ever exceeds 30s while the market is open, log it loudly.
3. **Record count strictly increases across three consecutive heartbeats.**
4. **Print the first five trades to stdout with timestamps** so Christoph can eyeball them against a live chart.

**If any of the four fails, stop and say so.** A historical replay that looks like a live session is the same failure shape as a 16:53 read that looks like an 05:00 read: identical artifact, different meaning, nothing downstream able to tell.

### Timing

Start **09:00 ET**. Run **to the close** if stable. Minimum useful window is 09:00–10:35 ET — row 12 needs 09:30–09:35, row 14 needs 10:00–10:30.

At the close: **cancel every subscription explicitly** — do not rely on disconnect to release them — disconnect, and confirm in TWS that `clientId 11` is released.

---

## Do not

- Do not adopt anything. `live/tape/` stays un-adopted and undecided.
- Do not compute delta, or score row 14.
- Do not commit the JSONL files. They are large and their retention is a separate decision.
- Do not start a second subscription set today under any circumstances.
- Do not modify `REGIME-PROMPT.md`, `SPEC.md`, or any spec.

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | All four live-verification assertions reported and passing within the first two minutes. `pytest` unchanged — this task adds a tool, not library code. |
| **Refusal** | Claude Code | Kill the TWS connection once during a quiet moment, deliberately, and confirm a gap record is written with both timestamps and that capture resumes. **A capture that cannot demonstrate its own gap handling has not demonstrated it.** |
| **UAT** | Christoph | Eyeball the first five printed trades against a live QQQ chart. **Before reading the counts, write down roughly how many prints you expect in the first five minutes.** The gap is the finding. |

## Done-note must state

- All five phase-0 answers, with 0a's classification rule quoted from the code.
- **The market data line count consumed today, against the account total** — this decides what task 013 can attempt tomorrow.
- **Whether depth was available on QQQ**, and on which exchange. Depth is the expensive line; four tickers with L2 tomorrow may exceed budget where four with trades and quotes will not. **[CORRECTED 2026-08-11 by 013c §5a: this premise is wrong. Christoph pays the full North America subscription set monthly, so depth costs nothing at the margin and does not scale with ticker count. The constraint is LINE COUNT, not money — 3 concurrent tick-by-tick subscriptions at the documented 0–399-line bracket.]**
- Per stream: record count, every gap with timestamps, first and last timestamp, file size.
- **Whether every trade carried a quote stamp**, and if any did not, how many and when.
- Anything about the capture that would make tomorrow's multi-ticker run behave differently.
