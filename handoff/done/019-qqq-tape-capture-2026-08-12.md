---
id: 019
title: QQQ tape capture, 2026-08-12, unattended
status: RUNNING — stays RUNNING until this note reaches the design session
owner: claude-code
ran: 2026-08-12, 09:07:31 → 16:00:00 ET
tree: D:\Dev\momentum
---

# 019 — live QQQ tape capture, 2026-08-12

**Status** RUNNING

**`019` was free** — nothing numbered 018 or 019 existed when I checked at 09:06 ET. No re-issue.

The capture ran the full session and is clean. **511,211 trades, 81,773 quotes, 2,174,143 depth
records. Zero gaps. Zero trades without a quote stamp. Maximum clock skew 0.0 s. Zero
disconnections.**

> **This note has to be pasted into chat.** Writing it is not reporting it.

---

## Part 1 — before connecting

| check | result |
|---|---|
| **Free disk** | **226.6 GB** of 476.9 GB. Far over the 20 GB advisory; the 5 GB block never in play |
| **TWS** | up on **7496**. 7497, 4001, 4002 closed |
| **`clientId 11`** | **free** — the capture claimed it on the first attempt |

**Configuration is 012-as-amended-by-012a, unmodified.** I read `tools/capture_tape.py`'s
argument parser rather than assuming, and **every value the task specifies is already the
default** — `clientId 11`, QQQ, `--until 16:00`, `numRows=10`, ARCA-first depth probe,
`readonly=True`. So the invocation passed **only `--port 7496`**. Nothing was edited and no
flag overrode a default.

```
connected 127.0.0.1:7496 clientId=11 server=178
contract: Stock(conId=320227571, symbol='QQQ', exchange='SMART', primaryExchange='NASDAQ', ...)
0e depth on QQQ: YES via ARCA
capturing until 16:00 ET
```

---

## The four live-verification assertions — all passed

| # | assertion | result |
|---|---|---|
| 1 | calls `reqTickByTickData`, not `reqHistoricalTicks` | **`IB.reqTickByTickData(contract, 'AllLast')`**, printed at start |
| 2 | trade timestamps within 5 s of system clock, continuously | **max skew 0.0 s**, **0 breaches over 30 s**, across 6 h 52 m |
| 3 | record count strictly increases across three consecutive heartbeats | **`"monotonic_increase_across_3_heartbeats": true`** — 413 heartbeats |
| 4 | first five trades printed with timestamps | printed at 13:07:31–13:07:32 UTC, below |

```
  TRADE 1: 2026-08-12T13:07:31.594882+00:00  725.65 x 5.0   bid 725.63 / ask 725.66  (FINRA)
  TRADE 2: 2026-08-12T13:07:31.594882+00:00  725.63 x 10.0  bid 725.63 / ask 725.66  (ARCA)
  TRADE 3: 2026-08-12T13:07:32.552567+00:00  725.63 x 40.0  bid 725.62 / ask 725.65  (NASDAQ)
  TRADE 4: 2026-08-12T13:07:32.552567+00:00  725.63 x 5.0   bid 725.62 / ask 725.65  (ARCA)
  TRADE 5: 2026-08-12T13:07:32.552567+00:00  725.63 x 2.0   bid 725.62 / ask 725.65  (ARCA)
```

---

## Per stream

| stream | records | bytes | first | last | gaps |
|---|---:|---:|---|---|---:|
| trades | **511,211** | 190.7 MB | 13:07:31.594882 | 20:00:00.033669 | **0** |
| quotes | 81,773 | 17.4 MB | 13:07:31.324206 | 19:59:59.889160 | **0** |
| depth (ARCA) | **2,174,143** | **1,767.1 MB** | 13:07:34.230970 | 20:00:00.033669 | **0** |

**Every trade carried a quote stamp — 511,211 of 511,211, zero exceptions.**

Started **09:07:31 ET**. `012` started 09:06:25 ET, so **the two sessions begin 66 seconds
apart** — a closer match than either task asked for, and it makes the comparison below worth
more than it would otherwise be.

---

## Disconnections: NONE. And the gap-record path was therefore NOT exercised.

**Zero disconnections. `"gaps": []`.** Every one of the 413 heartbeats reported
`connected=True`.

The log contains exactly one `!!!! DISCONNECTED` line, at **`2026-08-12T20:00:00.075187+00:00`**
— which is **0.042 s after the final record was written** and is the deliberate shutdown, not a
drop. `clientId 11` was released cleanly.

**The Refusal exit test requires this stated rather than reported as passing:**

> **The gap-record path was not exercised in this session.** No disconnection occurred, so
> nothing was written by it and nothing about it was tested here. **It is an untested path, and
> reporting it as passing would be reporting a path that never ran.**

---

## Per-venue breakdown

| venue | prints | % prints | shares | % shares | sh/print |
|---|---:|---:|---:|---:|---:|
| **FINRA** | 310,267 | **60.69 %** | 11,128,260 | **42.98 %** | 36 |
| NASDAQ | 69,945 | 13.68 % | 4,254,681 | 16.43 % | 61 |
| ARCA | 51,858 | 10.14 % | 3,065,754 | 11.84 % | 59 |
| BATS | 28,650 | 5.60 % | 1,615,103 | 6.24 % | 56 |
| DRCTEDGE | 19,900 | 3.89 % | 1,309,501 | 5.06 % | 66 |
| MEMX | 9,184 | 1.80 % | 522,841 | 2.02 % | 57 |
| IEX | 5,594 | 1.09 % | 348,255 | 1.34 % | 62 |
| NYSE | 5,068 | 0.99 % | 213,106 | 0.82 % | 42 |
| EDGEA | 2,878 | 0.56 % | 123,875 | 0.48 % | 43 |
| PEARL | 2,017 | 0.39 % | 130,814 | 0.51 % | 65 |
| BYX | 1,705 | 0.33 % | 92,428 | 0.36 % | 54 |
| PSX | 1,029 | 0.20 % | 41,442 | 0.16 % | 40 |
| AMEX | 851 | 0.17 % | 54,341 | 0.21 % | 64 |
| BEX | 788 | 0.15 % | 32,905 | 0.13 % | 42 |
| **CHX** | **750** | **0.15 %** | **2,933,825** | **11.33 %** | **3,912** |
| T24X | 463 | 0.09 % | 14,786 | 0.06 % | 32 |
| NYSENAT | 217 | 0.04 % | 9,258 | 0.04 % | 43 |
| TXSE | 47 | 0.01 % | 2,549 | 0.01 % | 54 |

**Total: 25,893,724 shares across 511,211 prints. 458,051 odd lots — 89.6 %. Mean 50.7
shares per print.**

---

## How this session differs from `012`'s — stated as observations only

**No explanation is offered for any of these.** A same-instrument comparison across two days is
exactly where a plausible reading becomes a premise, and `012` already produced one reading
this project had to be careful with.

| | `012` (2026-08-11) | `019` (2026-08-12) | difference |
|---|---:|---:|---|
| trades | 565,957 | **511,211** | **−54,746 (−9.7 %)** |
| quotes | 82,724 | 81,773 | −951 (−1.1 %) |
| depth records | 2,149,968 | **2,174,143** | **+24,175 (+1.1 %)** |
| total shares | 26,904,469 | 25,893,724 | −1,010,745 (−3.8 %) |
| mean print size | 47.5 sh | **50.7 sh** | **+6.7 %** |
| odd-lot share | 88.9 % | 89.6 % | +0.7 pp |
| trades bytes | 221.5 MB | 190.7 MB | −30.8 MB |
| depth bytes | 1,831.6 MB | 1,767.1 MB | −64.5 MB |

**Fewer trades, slightly more depth records.** The two streams moved in opposite directions.

### Venue mix

| venue | `012` prints | `019` prints | `012` shares | `019` shares |
|---|---:|---:|---:|---:|
| FINRA | 57.88 % | **60.69 %** | 42.57 % | 42.98 % |
| NASDAQ | 15.09 % | 13.68 % | 20.35 % | 16.43 % |
| ARCA | 10.03 % | 10.14 % | 12.50 % | 11.84 % |
| **CHX** | **0.11 %** | **0.15 %** | **3.82 %** | **11.33 %** |

**The largest single change is CHX.** Its share of prints barely moved — 640 to 750 — while its
share of *volume* went from **3.82 % to 11.33 %**, and its mean print size from **1,606 to
3,912 shares, 77× the session mean of 50.7.** In absolute terms, 2,933,825 shares against
1,027,799, on 110 more prints.

**NASDAQ's share of volume fell from 20.35 % to 16.43 %** while its share of prints fell less.

**Both are single-session observations on one instrument.** `012`'s note already recorded CHX
as *"one venue carrying block-sized prints and almost nothing else"* and asked whether it holds
across sessions. **Two sessions is not an answer to that**, and the direction of the change is
not evidence of a cause. It is `OBS-003` in the ledger with a review-by date.

---

## Disk

| | |
|---|---|
| **free before** | **226.6 GB** |
| **free after** | **224.7 GB** |
| **consumed** | **1.9 GB** — matching the 2,071,128,428 bytes of the three streams |

`records/tape/` now holds **3.86 GB across 10 files**, two sessions.

**Retention is `CLAUDE.md` v1.4: kept indefinitely until Christoph says otherwise.** No policy
for future captures is decided, and a multi-ticker run multiplies this — `012` measured
~7 GB/day for four tickers with L2, and nobody has costed the disk.

---

## Part 3 compliance

**Nothing in `records/` was read, moved, renamed, compressed or deleted while the capture ran.**
The per-venue breakdown above was computed **after 16:00:00 ET**, from a completed file, as
part 4 requires. **No JSONL is committed** — `records/` is gitignored and stays so.

---

## Exit tests

| Test | Result |
|---|---|
| **Green** | **Capture ran to 16:00:00 ET.** Four assertions reported with results above. Counts and bytes stated |
| **Refusal** | **The gap-record path was NOT exercised** — zero disconnections. Stated as untested rather than reported as passing |
| **UAT** | None. Machine-checkable, and Christoph was unavailable |

---

## Was `018` part 1 done before the capture started?

**No, and it could not have been.**

At 09:06 ET **there was no `018` in the inbox at all.** It was placed at 16:31 CEST — hours
after the capture began writing to `records/tape/` at 09:07:31 ET. So part 1's ordering
constraint was already violated before the file that states it existed.

**Christoph's instruction resolved it: part 1 runs after 16:00 ET.** It has now been done, and
is reported separately in `handoff/done/018-part-1-depth-ordering.md` — **a new note, because
`018`'s own done-note is already in `handoff/accepted/` and amending it would break the
byte-identity `013d` established and `018` protects.**

---

## Anything that was wrong on contact

**1 · `018` did not exist when the ordering rule required it to run first.** Above.

**2 · `019` arrived as a paste, not a file.** There was no `handoff/inbox/019-*.md` when the
capture started. I did not create one — inbox files are chat's to author — and Christoph placed
it during the session. Committed unmodified.

**3 · The task's "roughly 2.5 GB" estimate was high.** The session consumed **1.9 GB**, close to
`012`'s 2.07 GB. Not a defect; recorded because the 5 GB hard floor is calibrated against that
figure and a future multi-ticker run will not be.

**4 · Nothing else.** The configuration matched `012` exactly, the assertions all held, and no
decision was needed at any point — which is what the task was designed to achieve while
Christoph was unavailable.

---

**Paste this into chat. `019` stays `RUNNING` until it lands there.**
