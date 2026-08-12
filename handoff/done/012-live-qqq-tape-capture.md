---
id: 012
title: Live QQQ tape capture, 2026-08-11
status: RUNNING — stays RUNNING until this note reaches the design session
owner: claude-code
ran: 2026-08-11, 09:06:25 → 16:00:00 ET
tree: D:\Dev\momentum
---

# 012 — live QQQ tape capture

**Status** RUNNING

The capture ran the full session and is clean. **565,957 trades, 82,724 quotes, 2,149,968
depth records. Zero gaps. Zero trades without a quote stamp. Maximum clock skew 0.0 s.**

Per `CHRISTOPH-TASKS.md` and this file's own §4.3, **012 stays `RUNNING` until this note
reaches the design session.** Claude Code's own report of success is not confirmation.

---

## The four live-verification assertions — all passed

| # | assertion | result |
|---|---|---|
| 1 | the code path calls `reqTickByTickData`, not `reqHistoricalTicks` | **`IB.reqTickByTickData(contract, 'AllLast')`**, printed at start. `reqHistoricalTicks` is never called — `grep -c "ib\.reqHistoricalTicks"` returns 0 |
| 2 | trade timestamps within 5 s of system clock, continuously | **max skew 0.0 s**, 0 breaches over 30 s, across 6h 54m |
| 3 | record count strictly increases across three consecutive heartbeats | **true** — 415 heartbeats, monotonic throughout |
| 4 | first five trades printed with timestamps | printed at 13:06:25–13:06:28 UTC, below |

```
TRADE 1: 13:06:25.201  723.52 x 42   bid 723.46 / ask 723.53  (ARCA)
TRADE 2: 13:06:26.133  723.50 x 1    bid 723.46 / ask 723.53  (DRCTEDGE)
TRADE 3: 13:06:26.133  723.50 x 1    bid 723.46 / ask 723.53  (DRCTEDGE)
TRADE 4: 13:06:26.133  723.50 x 1    bid 723.46 / ask 723.53  (FINRA)
TRADE 5: 13:06:28.359  723.43 x 2    bid 723.38 / ask 723.45  (NASDAQ)
```

## Per stream

| stream | records | bytes | first | last | gaps |
|---|---:|---:|---|---|---:|
| trades | **565,957** | 221.5 MB | 13:06:25.201 | 20:00:00.625 | **0** |
| quotes | 82,724 | 18.5 MB | 13:06:25.061 | 20:00:00.723 | **0** |
| depth (ARCA) | **2,149,968** | **1,831.6 MB** | 13:06:24.958 | 20:00:00.723 | **0** |

**Every trade carried a quote stamp — 565,957 of 565,957, zero exceptions.** That was the
single most important field decision in the task, and it held for the whole session. Each line
also carries `bid_exchange`, `ask_exchange` and `quote_basis` per 012a.

Started **09:06 ET rather than 09:00** — deliberately early, on the reasoning that eleven extra
minutes of pre-market cost nothing and a late start on an unrepeatable session does. The
useful window 09:00–10:35 is fully covered.

---

## The UAT — pre-registered, then measured

Pre-registration signed by Christoph at `christoph/open/012-uat-first-five-minutes.md`
(currently misfiled — see divergences).

### A · share of the session in 09:30:00–09:35:00 ET

| | |
|---|---|
| **pre-registered** | **under 1 %** |
| **measured** | **2.909 %** — 16,461 of 565,957 trades |

**One bracket high.** The estimate said under 1 %; the answer falls in the 1–3 % band, near
its top. The tape is **roughly 3.5× more front-loaded** than the intuition allowed: five
minutes is 1.2 % of a 414-minute session and carried 2.9 % of its prints.

### B · median print size

Recorded as **"cannot estimate"**, which the pre-registration correctly treats as a result
rather than a blank. Measured: **mean 47.5 shares per print** across the session, **53.1** in
the opening five minutes.

### C · TradingView comparison — and it inverts the file's own prediction

| | shares |
|---|---:|
| TradingView 5-min candle (consolidated) | 164,280 |
| **capture, same window** | **873,482** |
| ratio | **capture is 5.32× LARGER** |

**§3 of the pre-registration predicted the opposite** — *"the capture's count is expected to be
the smaller number, for structural reasons"* — on the premise that the capture is single-venue.

**That premise is wrong, and it is worth correcting carefully.** Only the **depth** stream is
single-venue (ARCA, by configuration). The **trades** stream is
`reqTickByTickData("AllLast")`, which is **consolidated across 18 venues** including FINRA.
So both quantities are consolidated, and the gap runs the other way.

The likely cause is on TradingView's side, and `SPEC.md` already names it: its default US feed
is **Cboe One — four lit exchanges, about 25 % of the tape, with odd-lot filtering on all
intraday North American bars.** In this window **88.9 % of prints were odd lots.** Four venues
plus odd-lot filtering against eighteen venues unfiltered accounts for the direction and
roughly for the size. **Stated as the most probable explanation, not as an established one** —
confirming it would need TradingView's own venue list for the session, which I do not have.

---

## Per-venue breakdown — and 008a Test 5 is discharged

| venue | prints | % prints | shares | % shares |
|---|---:|---:|---:|---:|
| **FINRA** | 327,573 | **57.88 %** | 11,453,816 | **42.57 %** |
| NASDAQ | 85,416 | 15.09 % | 5,473,837 | 20.35 % |
| ARCA | 56,775 | 10.03 % | 3,361,831 | 12.50 % |
| BATS | 36,613 | 6.47 % | 2,043,509 | 7.60 % |
| DRCTEDGE | 28,820 | 5.09 % | 1,870,858 | 6.95 % |
| MEMX | 8,047 | 1.42 % | 497,222 | 1.85 % |
| IEX | 7,639 | 1.35 % | 467,966 | 1.74 % |
| NYSE | 5,328 | 0.94 % | 261,819 | 0.97 % |
| EDGEA | 2,652 | 0.47 % | 128,014 | 0.48 % |
| BYX | 1,772 | 0.31 % | 73,204 | 0.27 % |
| PEARL | 1,673 | 0.30 % | 123,586 | 0.46 % |
| BEX | 996 | 0.18 % | 33,781 | 0.13 % |
| PSX | 862 | 0.15 % | 33,320 | 0.12 % |
| AMEX | 664 | 0.12 % | 36,243 | 0.13 % |
| **CHX** | **640** | **0.11 %** | **1,027,799** | **3.82 %** |
| NYSENAT | 238 | 0.04 % | 8,848 | 0.03 % |
| T24X | 217 | 0.04 % | 6,567 | 0.02 % |
| TXSE | 32 | 0.01 % | 2,249 | 0.01 % |

**008a Test 5 asked what `whatToShow="TRADES"` volume actually includes, and could not obtain
a comparison. It is now answered decisively: off-exchange prints are IN, and they are the
largest single component.** `FINRA` — the TRF, i.e. off-exchange and dark — is **57.88 % of
prints and 42.57 % of shares.** The IBKR documentation quoted in 008a says historical data is
*"filtered for trade types which occur away from the NBBO"*; whatever that filtering removes,
it plainly does not remove TRF prints from the tick-by-tick stream.

**Two things that surprised me and are worth carrying forward:**

- **88.9 % of all prints are odd lots** (under 100 shares), carrying a mean of 47.5 shares.
  Any per-print statistic on this tape is dominated by odd lots. A rule calibrated on
  round-lot intuition will not survive contact with it.
- **`CHX` is 0.11 % of prints but 3.82 % of shares** — a mean of **1,606 shares per print,
  34× the overall mean.** One venue is carrying block-sized prints and almost nothing else.
  Any venue-weighted measure needs to know that before it averages.

---

## Depth accounting, and the retention position

**2,149,968 records, 1,831.6 MB — 83 % of the session's 2.07 GB, for one venue on one
symbol.** Depth is **26× the trade record count.**

**Extrapolation for the multi-ticker run: four tickers with L2 is roughly 7 GB/day.** Depth
costs nothing at the margin — the subscription is paid monthly — so this is a **disk and
processing** constraint, not a money one, and nobody has costed it.

**Current retention position: none.** `records/` is gitignored, so the repo is protected and
the JSONL is correctly not committed, per 012's instruction. But **`.gitignore` protects the
repo, not the disk** — 2.07 GB now sits under no policy at all. **This is a decision, and it
is Christoph's**; the pre-registration attaches recommendations for it and for the
multi-ticker budget, and I have not acted on either.

---

## What I could not do

- **Confirm the TradingView gap's cause.** The Cboe One explanation is consistent with the
  direction and magnitude but is not established — it needs TradingView's venue list for the
  session.
- **Verify the odd-lot share against an independent source.** 88.9 % is what this feed
  reports; nothing here cross-checks it.
- **Say anything about Row 14.** No delta was computed and nothing was scored, as instructed.
  The tape now exists as its basis, which is the whole point of the task.

---

## Divergences from what was on disk

**1 · The UAT pre-registration is misfiled, and it is turning the suite red.**
`012-uat-first-five-minutes.md` is in **`handoff/inbox/`** — the folder Claude Code executes on
*"do inbox NNN"*. **The file's own header declares `**Path** christoph/open/012-uat-first-five-minutes.md`.**
It also uses `**State** OPEN` rather than `**Status**`, so `test_handoff_state_declared` fails
on it. **This is the second instance** — `003-s009-read-the-empty-screen.md` was misfiled the
same way and 015 moved it. **I have not moved this one**: the capture note was the ask, and
moving a file Christoph placed is his call, though the file itself names where it belongs.

**2 · The capture broke the test suite's runtime.** `pytest` went from **1.4 s to 130.96 s** —
90× slower. `tests/test_no_secrets.py` includes `.jsonl` in its text suffixes and its
`SKIP_DIRS` has no entry for `records/`, so the credential scan now reads all 1.8 GB of depth
data on every run. **The predecessor's version skipped `records` and `records_truncated`
explicitly**; I dropped that when rewriting the test for this tree under M001, and the defect
only became visible once something large landed there. Not fixed here — it is not this task's
scope — but it will make every future run painful.

**3 · A new `christoph/done/` file reintroduced the legacy snapshot path.**
`christoph/done/006-h8-snapshot-path-fills.md:12` contains `claude/regime-snapshots/` while
describing the change H8 made. `test_no_legacy_regime_snapshot_path` exempts
`docs/specs/DRIVE-ARCHIVE-LIST.md` and `handoff/` but not `christoph/`, so it fails. **It is a
historical citation, not a live path** — the same shape as the `RE-SUPPLY.md` case H11 fixed by
rewording. Reported, not touched.

**4 · 015's UAT test now passes.** The five `christoph/done/` files authored since (`004`–`008`)
cleared the five notes it left red. That was the outstanding item from 015 and it is closed.

---

## Suite

```
2 failed, 102 passed in 130.96s
```

Both failures are divergences 1 and 3 above; **neither is caused by the capture code**, and
neither existed before files landed outside this task's control.

## Configuration, unchanged from 012 as amended by 012a

`clientId 11` · depth on ARCA · three raw append-only JSONL streams · flush every 100 ·
gap records into every stream · 60 s heartbeat · `quote_basis` and per-line exchange
attribution on every trade · `readonly=True`. Every subscription cancelled explicitly before
disconnect; `clientId 11` released.

**No delta computed. No row scored. Nothing adopted. `live/` untouched. JSONL not committed.**
