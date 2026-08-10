---
id: 008a
title: IBKR data behaviour — verify what the documentation does not state
status: DONE
type: investigation
owner: claude-code
unblocks: [010-attach-and-context]
ran: 2026-08-10 05:42 ET (pre-market, outside RTH as the task required)
symbol: AMZN
---

# 008a — IBKR data behaviour verification

All five tests ran. **Four resolved outright; Test 5 resolved its units question and is
partially unrun on its comparison question**, for the reason in "What I could not do".

Two headline numbers, because they are why the task exists:

- **Test 1 — ADR% differs by `+1.1662` percentage points** between `useRTH=1` (2.6143) and
  `useRTH=0` (3.7805) over the identical 20 sessions. That is **+44.6% relative**. `useRTH`
  absolutely does affect daily bars, and `useRTH=1` is now mandatory for every daily-bar
  request.
- **Test 4 — reconstructing session VWAP from `Bar.WAP` instead of `hlc3` moves it by
  `0.773` cents** (275.6616 vs 275.6693 on 2026-08-03… see Test 4; sample session
  2026-08-07). Sub-cent. Either source is defensible; `WAP` is still the better choice and
  now for a measured reason rather than an assumed one.

Everything below is from one read-only session, **8 API requests total** against the task's
ceiling of ~12 and IBKR's 60-per-10-minutes limit.

The script is committed at **`tools/verify_ibkr_data.py`** so this is repeatable rather than
a transcript. It connects `readonly=True`, carries a hard 20-request budget that aborts
rather than pacing the shared connection, guards every request with a timeout, has a
`__main__` guard, and does not import `tws_order`.

---

## Test 1 — Does `useRTH` change a DAILY bar? **Yes. Emphatically.**

**What was run.** Two `reqHistoricalData` calls for AMZN, `30 D` of `1 day` `TRADES` bars,
changing only `useRTH`, then a bar-by-bar diff on `date, high, low, close, volume,
barCount, average`.

**The answer.** **All 29 shared dates differ.** Not a subset, not only gap days — every
single one. Volume differs on all 29 (extended-hours volume is a mean of **24.3%** of the
`useRTH=0` daily total, ranging 15.0%–38.9%), and `close` differs on all 29 because
`useRTH=0` reports the **20:00 post-market close, not the official 16:00 close**.

The extreme case is **2026-07-30**, an earnings session: the daily range goes from
**8.77 to 31.80 (+262.6%)** and the close from **235.50 to 258.00 (+9.55%)**. A stop sized
off that bar would be more than three times too wide, and a "close" of 258.00 is not a
number the exchange ever printed as a close.

**A trap found on the way.** The two requests **did not return the same date set**.
`useRTH=1` returned 2026-06-26 → 2026-08-07; `useRTH=0` returned 2026-06-29 → **2026-08-10**,
i.e. it emitted a **partial bar for the current day** (04:00–05:42, still in progress),
which pushed the oldest session out of the 30. So a `30 D` daily request is not a fixed
window across the flag. All ADR/ATR figures quoted here are recomputed over the **identical
20 sessions 2026-07-13 → 2026-08-07** to remove that confound. The raw mismatched-window run
gave `+1.0698` pp — the partial day, having a tiny range, was *deflating* the `useRTH=0`
figure. **The confound was hiding the problem, not creating it.**

ADR% here is `100 × (mean(high/low) − 1)` over 20 sessions.

| metric | `useRTH=1` | `useRTH=0` | difference |
|---|---:|---:|---:|
| **ADR%(20)** | **2.6143** | **3.7805** | **+1.1662 pp (+44.6%)** |
| ATR(14) | 9.9864 | 10.3386 | +0.3521 (+3.53%) |

Per-session, the 20 shared sessions:

| date | RTH range | ALL range | range +% | RTH volume | ALL volume | ext share |
|---|---:|---:|---:|---:|---:|---:|
| 2026-07-13 | 5.47 | 5.85 | 6.9% | 18,661,920 | 23,710,214 | 21.3% |
| 2026-07-14 | 4.76 | 5.12 | 7.6% | 16,008,430 | 21,212,519 | 24.5% |
| 2026-07-15 | 6.75 | 8.96 | 32.7% | 24,963,319 | 32,609,536 | 23.4% |
| 2026-07-16 | 10.09 | 10.30 | 2.1% | 23,199,229 | 30,277,567 | 23.4% |
| 2026-07-17 | 6.65 | 6.93 | 4.2% | 21,347,623 | 28,069,629 | 23.9% |
| 2026-07-20 | 4.89 | 6.18 | 26.4% | 16,910,915 | 23,479,872 | 28.0% |
| 2026-07-21 | 2.94 | 4.57 | 55.4% | 14,841,786 | 19,089,799 | 22.3% |
| 2026-07-22 | 6.00 | 9.49 | 58.2% | 16,447,019 | 24,036,638 | 31.6% |
| 2026-07-23 | 6.30 | 10.46 | 66.0% | 27,769,811 | 35,373,547 | 21.5% |
| 2026-07-24 | 3.61 | 4.16 | 15.2% | 20,060,202 | 24,352,738 | 17.6% |
| 2026-07-27 | 4.90 | 5.48 | 11.8% | 17,777,608 | 25,962,284 | 31.5% |
| 2026-07-28 | 5.01 | 6.13 | 22.4% | 19,939,392 | 26,846,206 | 25.7% |
| 2026-07-29 | 6.66 | 8.59 | 29.0% | 22,550,466 | 31,411,292 | 28.2% |
| **2026-07-30** | **8.77** | **31.80** | **262.6%** | 44,062,854 | 72,100,200 | 38.9% |
| 2026-07-31 | 11.22 | 14.45 | 28.8% | 77,993,050 | 93,288,827 | 16.4% |
| 2026-08-03 | 9.20 | 15.62 | 69.8% | 52,639,200 | 61,892,878 | 15.0% |
| 2026-08-04 | 5.25 | 8.68 | 65.3% | 36,849,608 | 46,029,651 | 19.9% |
| 2026-08-05 | 12.06 | 12.06 | 0.0% | 24,955,742 | 32,036,689 | 22.1% |
| 2026-08-06 | 4.42 | 4.42 | 0.0% | 14,434,349 | 20,224,911 | 28.6% |
| 2026-08-07 | 5.56 | 6.79 | 22.1% | 17,796,371 | 22,937,839 | 22.4% |

Note 2026-08-05 and 2026-08-06: **range identical, volume still +22% and +29%**. A
range-only check would have called those days "unaffected" and been wrong. That is exactly
how this would have been missed.

**Cross-check against local data.** `live/levels/AMZN.json` independently records
2026-08-03 `premarket_high = 278.58` against `prior_high = 273.23`. The `useRTH=0` bar for
2026-08-03 has `low = 271.58` versus the RTH `low = 278.00` — consistent with pre/post
prints leaking into the daily bar. The two sources agree.

**Verdict, per the interpretation fixed in advance:** any difference ⇒ **`useRTH=1` is
mandatory for every daily-bar request.**

---

## Test 2 — Does `useRTH=0` include the 20:00–03:50 overnight session? **No — it starts at 04:00.**

**What was run.** Today's `1 D` of `1 min` `TRADES` bars with `useRTH=False`, plus
`reqContractDetails`.

**The answer.** **Earliest bar = `2026-08-10 04:00:00-04:00`** (`datetime`, tz `US/Eastern`),
latest `05:42:00-04:00` — i.e. up to the moment of the call. 103 bars. This is the
**04:00 pre-market** case, not the 20:00-previous-evening case. The config anchor and the
API agree.

Contract details, verbatim:

```
timeZoneId   : US/Eastern
tradingHours : 20260810:0400-20260810:2000;20260811:0400-20260811:2000;
               20260812:0400-20260812:2000;20260813:0400-20260813:2000;
               20260814:0400-20260814:2000
liquidHours  : 20260810:0930-20260810:1600;20260811:0930-20260811:1600;
               20260812:0930-20260812:1600;20260813:0930-20260813:1600;
               20260814:0930-20260814:1600
```

`tradingHours` is `0400-2000` and the first `useRTH=0` bar is exactly `0400`. That is
**consistent with** `useRTH=0` returning `tradingHours`, which the documentation never
states — but it is one observation on one contract, not a proof, and it is recorded that way
deliberately so a future reader can check the inference rather than inherit it.

**The overnight session does not appear in `tradingHours` at all.** So for this contract,
routed `SMART` with `primaryExchange=NASDAQ`, the 20:00–03:50 session is simply not in
scope for historical bars. **This does not prove it is unreachable** — IBKR routes that
session differently, and a contract explicitly qualified to the overnight venue was not
tested. The timestamp filter therefore stays: it is currently belt-and-braces for
`SMART`, but it is the only thing that would hold if a differently-routed contract behaved
differently, and nothing here justifies removing it.

First and last bars are in the raw dump; the first five:

| timestamp | open | high | low | close | volume |
|---|---:|---:|---:|---:|---:|
| 2026-08-10 04:00:00-04:00 | 274.00 | 275.00 | 274.00 | 275.00 | 8,641 |
| 2026-08-10 04:01:00-04:00 | 274.53 | 275.02 | 274.48 | 274.57 | 3,687 |
| 2026-08-10 04:02:00-04:00 | 274.83 | 275.00 | 274.33 | 274.51 | 9,038 |
| 2026-08-10 04:03:00-04:00 | 274.45 | 274.45 | 274.31 | 274.31 | 1,919 |
| 2026-08-10 04:04:00-04:00 | 274.34 | 274.34 | 274.34 | 274.34 | 200 |

Note `04:06` has `volume = 0` with OHLC all equal — **zero-volume bars exist in the
pre-market series** and are carried forward at the last price. Anything averaging over
these must weight by volume or it will be pulled toward thin prints.

---

## Test 3 — Can one request return 20 sessions of 1-minute bars? **Yes, easily. The current doc table is right; the legacy table is wrong.**

**What was run.** `1 min` `TRADES` `useRTH=True` at `durationStr="20 D"`, then `"1 M"`.

**The answer.** Both succeeded. No errors, no pacing rejection.

| durationStr | result | bars | wall-clock | first | last | distinct dates | calendar span |
|---|---|---:|---:|---|---|---:|---:|
| `20 D` | **OK** | **7,800** | **2.4 s** | 2026-07-13 09:30 | 2026-08-07 15:59 | 20 | 26 days |
| `1 M` | **OK** | 8,580 | 8.8 s | 2026-07-09 09:30 | 2026-08-07 15:59 | 22 | 30 days |

`7,800 = 20 × 390` exactly, and `8,580 = 22 × 390` — full 09:30–15:59 sessions with no
missing minutes. **The RVOL 20-session curve is one request, not twenty.** The pacing
arithmetic in `SPEC.md` §6b.1b can be divided by twenty.

**The units question is settled: `durationStr` in `"D"` counts TRADING days, not calendar
days.** `"20 D"` returned exactly **20 distinct sessions spanning 26 calendar days** — the
extra 6 are weekends. `"1 M"` returned 22 sessions across 30 calendar days. Had `D` been
calendar days, `"20 D"` would have yielded roughly 14 sessions and the RVOL window would
have been silently 30% short.

---

## Test 4 — Is `Bar.WAP` populated, and does it look right? **Yes, on all 7,800 bars.**

**What was run.** The 7,800 bars from Test 3, checked for `average == 0` and for
`average` outside `[low, high]`, then 20 bars sampled from the most recent full session
(2026-08-07) — the ten thinnest and ten thickest traded minutes, which is what "spanning
quiet and active" has to mean if it is to be checkable.

**The answer.** **Zero bad bars.** `WAP == 0`: **0 of 7,800**. `WAP` outside `[low, high]`:
**0 of 7,800**. All 7,800 bars had `volume > 0`. The loud warning the task asked for is not
needed — but the check stays in the script, because a silently zero WAP would drag a
reconstructed VWAP toward zero and still look like a plausible price.

`|WAP − hlc3|` over the 390 traded bars of 2026-08-07: **mean 3.105¢, max 43.367¢.** The max
lands on the 09:30 opening minute (`WAP 273.2330` vs `hlc3 273.6667`, **−43.37¢**), which is
the expected place for it — `hlc3` weights an opening range's extremes equally with where
the volume actually traded, and `WAP` does not.

**Session VWAP for 2026-08-07, both ways:**

| source | session VWAP |
|---|---:|
| `Σ(WAP × vol) / Σ(vol)` | 275.6615724886832 |
| `Σ(hlc3 × vol) / Σ(vol)` | 275.6693033077736 |
| **difference** | **−0.773 cents** |

**The per-bar errors are large but they cancel at session level.** 3.1¢ mean per-bar
becomes 0.77¢ across the session. So the `WAP`-vs-`hlc3` choice is **not** materially
sizing a position on a normal session — but it is measured now rather than assumed, and
`WAP` remains correct on principle since `hlc3` demonstrably misprices the opening minute
by 43¢, which is exactly the bar an opening-range strategy cares most about.

Sample (10 quietest and 10 most active minutes, 2026-08-07):

| timestamp | open | high | low | close | volume | WAP | hlc3 | Δ¢ | barCount |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 12:37 | 276.0200 | 276.0500 | 275.9400 | 275.9800 | 5,871 | 275.9910 | 275.9900 | 0.10 | 38 |
| 14:52 | 274.2000 | 274.3400 | 274.1800 | 274.1800 | 5,880 | 274.2420 | 274.2333 | 0.87 | 46 |
| 12:42 | 275.8500 | 275.8500 | 275.7800 | 275.7900 | 6,370 | 275.8150 | 275.8067 | 0.83 | 32 |
| 13:37 | 274.2300 | 274.2400 | 274.1600 | 274.2000 | 6,988 | 274.1910 | 274.2000 | −0.90 | 35 |
| 12:47 | 275.9600 | 275.9600 | 275.8600 | 275.8700 | 7,062 | 275.8890 | 275.8967 | −0.77 | 49 |
| 13:09 | 274.9300 | 274.9700 | 274.8800 | 274.9200 | 7,947 | 274.9110 | 274.9233 | −1.23 | 54 |
| 14:57 | 274.1800 | 274.2400 | 274.1500 | 274.2200 | 8,074 | 274.1810 | 274.2033 | −2.23 | 48 |
| 13:12 | 275.0100 | 275.0500 | 274.9900 | 275.0400 | 8,431 | 275.0230 | 275.0267 | −0.37 | 52 |
| 13:45 | 274.3500 | 274.3800 | 274.2600 | 274.2700 | 8,544 | 274.3220 | 274.3033 | 1.87 | 45 |
| 12:03 | 277.1500 | 277.3400 | 277.1300 | 277.2600 | 8,601 | 277.2050 | 277.2433 | −3.83 | 66 |
| 09:45 | 276.5500 | 276.6300 | 275.6100 | 276.1600 | 198,596 | 276.2100 | 276.1333 | 7.67 | 820 |
| 15:41 | 274.2900 | 274.6000 | 274.0300 | 274.2500 | 209,223 | 274.3770 | 274.2933 | 8.37 | 604 |
| 09:31 | 273.8400 | 275.1700 | 273.5900 | 274.9600 | 209,734 | 274.5730 | 274.5733 | −0.03 | 1,003 |
| 09:37 | 276.9000 | 277.3500 | 276.6600 | 276.9600 | 210,146 | 276.9820 | 276.9900 | −0.80 | 1,111 |
| 09:34 | 276.3700 | 276.7300 | 275.9500 | 276.6800 | 222,770 | 276.4300 | 276.4533 | −2.33 | 1,175 |
| 09:32 | 274.9000 | 276.6500 | 274.8100 | 276.0700 | 263,336 | 275.8940 | 275.8433 | 5.07 | 1,180 |
| 15:58 | 274.8200 | 274.8700 | 274.7300 | 274.7500 | 264,732 | 274.8120 | 274.7833 | 2.87 | 1,673 |
| 09:35 | 276.6400 | 277.4300 | 276.4000 | 276.5000 | 279,091 | 276.9720 | 276.7767 | 19.53 | 1,340 |
| 15:59 | 274.7400 | 274.8200 | 274.3300 | 274.4500 | 722,563 | 274.6790 | 274.5333 | 14.57 | 4,417 |
| **09:30** | 272.8700 | 274.5400 | 272.7500 | 273.7100 | 731,941 | **273.2330** | 273.6667 | **−43.37** | 1,748 |

---

## Test 5 — What does `whatToShow="TRADES"` volume include? **Units resolved; the comparison is partially unrun.**

**Resolved: the volume field is in SHARES, not round lots.** This mattered enough to check
because IBKR has historically returned historical stock volume in hundreds. AMZN's
2026-07-31 daily bar reads **77,993,050**. Multiplied by 100 that would be 7.8 **billion**
shares in one session on a ~$270 stock — roughly $2.1 trillion of notional, which is
impossible. The raw field is shares. No multiplier is needed and one must not be applied.

| date | close | volume (shares) | barCount |
|---|---:|---:|---:|
| 2026-07-31 | 271.58 | 77,993,050 | 393,916 |
| 2026-08-03 | 284.02 | 52,639,200 | 276,818 |
| 2026-08-04 | 277.42 | 36,849,608 | 199,287 |
| 2026-08-05 | 272.65 | 24,955,742 | 135,782 |
| 2026-08-06 | 272.26 | 14,434,349 | 77,660 |
| 2026-08-07 | 274.48 | 17,796,371 | 87,691 |

**Not resolved: the ratio against a consolidated public source.** No full-session
independent figure was obtained — see "What I could not do".

**A partial, venue-limited comparison was possible** using the local Databento capture
`replay/AMZN-2026-08-03-open.json`, which overlaps IBKR's bars for **09:30–09:50 ET on
2026-08-03** (20 minutes). Summing MBO `action == "T"` messages over exactly that window:

| source | prints | shares |
|---|---:|---:|
| Databento capture (single publisher) | 54,739 | 5,764,415 |
| IBKR `TRADES` 1-min bars, same 20 minutes | 70,015 (barCount) | 15,668,759 |
| **ratio capture / IBKR** | **0.782** | **0.368** |

Per the task's instruction, **no attribution is offered for the gap** — the deliverable is
its size. But one asymmetry is worth flagging for whoever picks this up, because it is not
explained by venue coverage alone: the capture carries **78% of IBKR's print count but only
37% of its share volume**. Those two ratios should be far closer together if the only
difference were which venues each source sees. Something is differently *sized*, not just
differently *counted*. Also from the capture, in that window **70.1% of prints were odd lots
(<100 shares) but only 15.0% of shares** — so print counts and share counts genuinely
measure different things here, and `barCount` should not be used as a proxy for trade count
across sources.

**This does not answer Test 5's question** and must not be quoted as if it did. It is a
20-minute, single-publisher, single-session lower bound.

---

## Environment

| item | value |
|---|---|
| Application | **TWS, live**, `127.0.0.1:7496` |
| Server version | **178** |
| TWS time at connect | `2026-08-10 09:42:02 UTC` = **05:42 ET** |
| Session context | **pre-market, outside RTH**, as the task required |
| Connection | `readonly=True`, `clientId=77` (and `78` for the one follow-up request) |
| Accounts | 4 managed accounts visible; **IDs deliberately not recorded here** — not needed for any finding |
| Symbol | **AMZN** — `conId=3691937`, `SMART`, `primaryExchange=NASDAQ`, `NMS`, USD |
| Market data | Not enumerable via the API. All `TRADES` historical requests returned full data with **zero errors and zero pacing rejections**, so US equity historical entitlement is active. Depth/real-time entitlements were not exercised and are unknown. |
| Requests issued | **8** (7 in the main run + 1 follow-up); ceiling 20, IBKR limit 60/10 min |
| Script | `tools/verify_ibkr_data.py` |

Dates used: daily 2026-06-26 → 2026-08-10; minute 2026-07-09 → 2026-08-10.

---

## What I could not do

1. **Test 5's consolidated comparison — the main gap.** An independent full-session volume
   figure needs a public source (exchange site or broker front end), which is not reachable
   from the API and was not available in this session. **Recorded as unrun rather than
   guessed**, per the task. To close it, someone needs to read AMZN's official consolidated
   volume for one completed session and put it beside the table above. One number closes it.

2. **The local capture cannot substitute, for two reasons found by checking rather than
   assuming.** It spans `13:28:00Z → 13:50:50Z` — **22 minutes around the open, not a
   session** — so no daily total exists in it. And it is single-publisher, so it is not
   consolidated tape.

3. **The capture's venue is unverified, and that is a provenance defect worth its own
   fix.** The slice carries `publisher_id 2`, but `tools/make_replay_slice.py:72` sets
   `publisher_id = 2` as a *default* and then inherits whatever the source had, and **the
   slice never records which Databento dataset it came from**. So a capture sitting on disk
   cannot be traced to its venue without the original download. I have deliberately not
   named a venue anywhere above. This is a candidate for `docs/observations/`.

4. **The overnight session was not reached, only shown absent from `SMART`.** Confirming
   whether IBKR exposes 20:00–03:50 bars through a differently-routed contract would need
   another qualification and request. Not attempted — out of scope, and the finding that
   matters (the 04:00 anchor is correct for `SMART`) is settled.

5. **`useRTH=0` semantics are established on one contract, one day.** `tradingHours` starting
   at `0400` and the first bar landing at `0400` is one observation, not a proof.

6. **No behaviour of `live/` was exercised.** This task read the API directly. The standing
   caveat that `live/` has import coverage only is untouched by anything here.

---

## Test suite state

`C:\venvs\trading\Scripts\python.exe -m pytest`, verbatim:

```
8 failed, 2612 passed, 5 skipped, 1 warning in 12.76s
```

**No failure was introduced by this task**, and none of the three files added here
(`tools/verify_ibkr_data.py`, this note, the observation) appears in any failure. The
working tree carries no modified source file — only `requirements.txt`, which was already
modified before this session began. The eight break down as:

| count | test | cause |
|---:|---|---|
| 5 | `test_incomplete_work.py` | Pre-existing. `vwap_breaks` and `first_bar_strength` diverge from their checklist definitions; the test itself points at `HANDOFF: phase-3-halted`. Untouched here. |
| 1 | `test_open_questions.py::test_no_question_is_open` | Pre-existing and **intended red** — `handoff/questions/scanner-provenance-requirement-dropped.md` is `status: OPEN`. Per CLAUDE.md the suite refuses to go green while something is blocked on a person. |
| 2 | `test_no_secrets.py` | **Pre-existing, and serious — see below.** |

### The two secrets failures are a live credential, not a stale pattern

`tests/test_no_secrets.py` fails on **`requirements.txt:30`**, which in the working tree
contains a real `setx DATABENTO_API_KEY "db-…"` line and a `setx DATABENTO_USER` line.

What was established, without reproducing either value:

- **It is NOT in git history.** `git log -S` over `requirements.txt` returns nothing, and
  `HEAD:requirements.txt` at those lines is ordinary dependency content. The exposure is
  **working-tree only**, so history is clean and no rewrite is needed.
- **The working-tree file is also an older revision.** It reads `pandas>=2.0` /
  `numpy>=1.24` — the floors that commit `a976a2a` deliberately raised — and is 30 lines
  against HEAD's 42. Committing it as-is would silently revert that commit *and* publish the
  key permanently.

This was **not fixed in this task**: it is uncommitted user content, and discarding it is
not a call to make unasked. Two actions are needed by a person — **rotate the Databento key**
(it has been sitting in plaintext), and decide what `requirements.txt` should contain.

Note the guard worked exactly as designed. No question file was opened for this, because
`test_no_secrets.py` already holds the suite red on it, which is the stronger form of the
same thing.

---

## Proposed config entries

**Not written to `config/` in this task**, per the task's instruction — they land with slice
008's config loader so its rules apply from the first commit. Each `constraint:ibkr` note
says what the value becomes under a different broker, per `SPEC.md` §4.4.

```yaml
ibkr_daily_bars_use_rth:
  value: 1
  source: constraint:ibkr
  note: >
    Mandatory, not a preference. With useRTH=0 IBKR folds pre- and post-market prints into
    the daily bar: measured on AMZN over 20 sessions to 2026-08-07, ADR% went 2.6143 ->
    3.7805 (+1.1662pp, +44.6%) and one earnings session's range went 8.77 -> 31.80
    (+262.6%). ADR% and atr_d14 size positions, so useRTH=0 silently widens every stop.
    The daily 'close' under useRTH=0 is also the 20:00 post-market price, not the official
    16:00 close. Under a broker that only ever returns regular-session dailies this key
    becomes unnecessary rather than 0; under any broker with an equivalent flag it must be
    set to the regular-session-only value.

ibkr_daily_request_emits_partial_current_day:
  value: true
  source: constraint:ibkr
  note: >
    With useRTH=0, a "30 D" daily request includes an in-progress bar for today and drops
    the oldest session to stay at 30, so the window shifts depending on the flag and the
    time of day. Any fixed-window calculation must slice by date after the request rather
    than trusting the bar count. Under another broker, verify separately -- this is not a
    universal behaviour and assuming it either way is wrong.

session_vwap_anchor_et:
  value: "04:00"
  source: constraint:ibkr
  note: >
    Confirmed against the API, not merely assumed: reqContractDetails gives
    tradingHours 0400-2000 and liquidHours 0930-1600 for AMZN/SMART, and the first
    useRTH=0 1-minute bar on 2026-08-10 was exactly 04:00 ET. IBKR's 20:00-03:50 overnight
    session does NOT appear in tradingHours for this routing and did not appear in the
    bars. Keep the post-request timestamp filter regardless -- it is currently redundant
    for SMART but is the only defence if a differently-routed contract behaves otherwise.
    Under a broker whose extended session starts elsewhere, this becomes that time.

ibkr_duration_units:
  value: trading_days
  source: constraint:ibkr
  note: >
    durationStr "20 D" returned exactly 20 distinct sessions spanning 26 calendar days;
    "1 M" returned 22 sessions across 30 calendar days. D counts TRADING days. Had it been
    calendar days the 20-session RVOL window would have been ~14 sessions, i.e. 30% short,
    with no error raised. Under another broker this must be re-measured, not carried over.

ibkr_rvol_minute_history_single_request:
  value: true
  source: constraint:ibkr
  note: >
    One request returns 20 sessions of 1-minute bars: durationStr="20 D",
    barSizeSetting="1 min", whatToShow="TRADES", useRTH=1 gave 7,800 bars (= 20 x 390,
    no missing minutes) in 2.4s with no pacing rejection. "1 M" also succeeded (8,580 bars,
    8.8s). IBKR's legacy "Historical Data Limitations" table implying a 1-day cap for
    1-minute bars is WRONG; the current Max Duration Per Bar Size table is right. The RVOL
    curve costs 1 request, not 20 -- divide the SPEC 6b.1b pacing budget accordingly.

ibkr_historical_volume_units:
  value: shares
  source: constraint:ibkr
  note: >
    BarData.volume from reqHistoricalData is already in shares for US stocks -- do NOT
    apply the x100 round-lot multiplier that older IBKR API guidance implies. AMZN
    2026-07-31 reads 77,993,050; x100 would be 7.8bn shares (~$2.1tn notional) which is
    impossible. Verified by magnitude, not by documentation. Re-check per broker.

vwap_price_source:
  value: bar_wap
  source: measurement
  note: >
    Use Bar.WAP (ib_async BarData.average), not hlc3. Populated on all 7,800 bars sampled,
    never zero, never outside [low, high]. Per-bar |WAP - hlc3| averaged 3.105c (max
    43.367c, on the 09:30 opening minute) but session VWAP differed by only 0.773c
    (275.6616 vs 275.6693, 2026-08-07) -- the per-bar errors cancel. So this choice is not
    materially sizing a position on a normal session, but hlc3 misprices the opening minute
    by 43c, which is the bar an opening-range strategy cares most about.
```

---

## For whoever picks up 010

Three things from here change what you build:

1. **`useRTH=1` on every daily request** — this is the one that would have silently
   mis-sized positions, and a range-only sanity check would not have caught it (2026-08-05
   and 08-06 had identical ranges and 22–29% volume differences).
2. **The RVOL minute history is one request** — the pacing budget in `SPEC.md` §6b.1b is
   twenty times more generous than assumed.
3. **Slice by date, not by bar count.** `useRTH=0` shifts the window with the current
   partial day.

Test 5's consolidated-volume comparison is the one open item and needs a human with a
browser, not another API call.
