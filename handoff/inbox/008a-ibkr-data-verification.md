---
id: 008a
title: IBKR data behaviour — verify what the documentation does not state
status: READY
blocks: [010-attach-and-context]
type: investigation
owner: claude-code
---

# 008a — IBKR data behaviour verification

**This is an investigation, not a build slice.** No production code ships from it. The
deliverable is a findings note and, where a question resolves, one or two config values
with a `source:` and a `note:`.

**Why it exists.** Six facts that `SPEC.md` §6b.1b depends on are **not stated in IBKR's
documentation**. Two of them change a number that sizes a position. They were researched
against the official TWS API docs and confirmed absent, not overlooked — so the only way
to close them is to ask the API directly.

**Run it outside regular trading hours** where the test permits. Pacing is shared with
everything else on the connection (`SPEC.md` §6b.1b), and a pacing rejection looks like a
slow request rather than an error.

---

## Standing constraints — do not break these

- **Read-only. `readonly=True` on the connection.** This task requests historical data and
  contract details. It must not import from `tws_order`, must not place, modify or cancel
  anything, and must not call `reqExecutions`.
- **`ib_async` only.** Never `ib_insync`.
- **Guard every synchronous request with a timeout.** `ib_async`'s `RequestTimeout`
  defaults to `0`, which means wait forever. `tws_order/ibkr.py` already does this with
  `_guard_timeout()` at 20 s — use the same shape.
- **Guard the module against import-time connection.** `preregistration.yaml` records a
  prior incident where a module opened a socket to live TWS port 7496 at import with no
  `__main__` guard, and a test collector walking the tree opened a live session.
- **Total requests must stay under 60 in any ten minutes.** The whole task needs roughly
  a dozen. Do not loop.

---

## Test 1 — Does `useRTH` change a DAILY bar?

**The question.** `SPEC.md` computes ADR% and `atr_d14` from daily bars, and both feed the
stop-width rules, and therefore the position size. IBKR documents `useRTH` as *"whether (1)
or not (0) to retrieve data generated only within Regular Trading Hours"* — with **no
bar-size carve-out**. A plain reading says it applies to daily bars too, which would mean
`useRTH=0` returns dailies whose high, low and volume include extended hours. **No IBKR
page confirms or denies this.**

**Method.**

1. Pick a symbol with a **large, known pre-market gap** in the last 30 sessions — one where
   the pre-market high or low clearly exceeded the regular session's. A gapper from your
   own recent watchlist is ideal because you can eyeball the answer.
2. Request the same series twice, changing only `useRTH`:

```python
common = dict(endDateTime="", durationStr="30 D", barSizeSetting="1 day",
              whatToShow="TRADES", formatDate=1)
rth   = ib.reqHistoricalData(contract, useRTH=True,  **common)
all_h = ib.reqHistoricalData(contract, useRTH=False, **common)
```

3. Diff bar by bar on `date`, `high`, `low`, `close`, `volume`, `barCount`, `average`.

**Record.** For every date where they differ: both highs, both lows, both volumes, and the
absolute and percentage difference. **Then compute ADR% both ways over the same 20 sessions
and state the difference in ADR% points** — that number is the answer's actual consequence,
and it is what a reader six months from now will want.

**Interpretation, decided in advance so the result cannot be rationalised:**

- **Identical across all 30 days** ⇒ `useRTH` does not affect daily bars. Record it as a
  `constraint:ibkr` with a note. ADR and ATR are safe either way.
- **Any difference** ⇒ `useRTH=1` is **mandatory** for every daily-bar request, and the
  config key gets a note saying why in one sentence a stranger would understand.

---

## Test 2 — Does `useRTH=0` include the 20:00–03:50 overnight session?

**The question.** IBKR now runs a US overnight equity session, 20:00–03:50 ET. `SPEC.md`
anchors session VWAP at **04:00 or the first print**. If overnight prints fall inside a
`useRTH=0` request, a naive "today from the open" pull would anchor VWAP at **20:00 the
previous evening** — and VWAP is a stop level.

**This is already defended against** (the anchor is declared in config and returned bars
are filtered by timestamp), but the behaviour must be *known*, not merely guarded.

**Method.**

1. Take a liquid US equity that trades overnight — one of the larger names, since coverage
   is not universal.
2. Request today's 1-minute bars with `useRTH=False`:

```python
bars = ib.reqHistoricalData(contract, endDateTime="", durationStr="1 D",
                            barSizeSetting="1 min", whatToShow="TRADES",
                            useRTH=False, formatDate=1)
```

3. **Print the first ten and last ten bar timestamps.** Note the earliest.

**Record.** The earliest timestamp, in ET, with the date. Also request
`reqContractDetails` and record `tradingHours`, `liquidHours` and `timeZoneId` verbatim —
the documentation links `liquidHours` to *"regular trading hours"* but **never states that
`useRTH=0` returns exactly `tradingHours`**, so capturing both lets a future reader check
the inference rather than inherit it.

**Interpretation:**

- Earliest ≈ **04:00** ⇒ pre-market only, and the config anchor agrees with the API.
- Earliest ≈ **20:00 previous day** ⇒ the overnight session is included. The timestamp
  filter is not belt-and-braces, it is **load-bearing**, and the note must say so.
- **Anything else** ⇒ record it exactly and do not round it into one of the two expected
  answers.

---

## Test 3 — Can one request return 20 sessions of 1-minute bars?

**The question.** IBKR's two documentation pages disagree. The current *Max Duration Per
Bar Size* table gives `1 min → max 365 D`; the legacy *Historical Data Limitations* table
maps `1 W` duration to *"3 mins - 1 week"*, implying 1-minute bars cap at one day. **Both
cannot be right.** The RVOL curve needs 20 sessions of 1-minute bars, and whether that is
one request or twenty changes the pacing arithmetic by a factor of twenty.

**Method.** Request `durationStr="20 D"`, `barSizeSetting="1 min"`, `whatToShow="TRADES"`,
`useRTH=True`. Then try `"1 M"`.

**Record.** Whether each succeeds, the bar count returned, the first and last timestamps,
and the wall-clock duration of the call. If it errors, **the exact error code and message**.

**Also settle the units question.** `durationStr` in `"D"` — does IBKR count *calendar* or
*trading* days? Compare the number of distinct dates returned by `"20 D"` against a
calendar span covering a weekend. Undocumented, and it silently changes the RVOL window.

---

## Test 4 — Is `Bar.WAP` populated, and does it look right?

**The question.** `SPEC.md` reconstructs session VWAP as `Σ(WAP × volume) / Σ(volume)`
rather than from `hlc3`, because `Bar.WAP` is documented as *"the bar's Weighted Average
Price (only available for TRADES)"*. **Its formula is not published.**

**Method.** From Test 3's 1-minute bars, for twenty bars spanning quiet and active periods,
record `open, high, low, close, volume, average (WAP), barCount`. Check that `WAP` sits
within `[low, high]` and compare it against `hlc3` for the same bar.

**Record.** The mean and max absolute difference between `WAP` and `hlc3`, in cents.
**Then compute session VWAP both ways over one full session and report the difference in
cents** — that is the number that lands in `|entry − stop|`, and it is the whole reason
this test exists.

**If `WAP` is zero, absent or outside `[low, high]` on any bar, say so loudly.** A silently
zero WAP would drag a reconstructed VWAP toward zero and look like a plausible number.

---

## Test 5 — What does `whatToShow="TRADES"` volume actually include?

**The question.** IBKR states historical data is *"filtered for trade types which occur
away from the NBBO such as combo legs, block trades, and derivative trades"* and that
*"the daily volume from the (unfiltered) real time data functionality will generally be
larger than the (filtered) historical volume."* **Odd lots and off-exchange/TRF prints are
not named**, and the RVOL denominator depends on which are in.

**Method.** For one liquid symbol on one completed session, compare the daily bar's
`volume` against the same day's volume from a public source (the exchange's own site, or
your broker's front end). Note both, and the ratio.

**Record.** Both numbers and the ratio. **Do not attempt to attribute the difference to a
cause** — the deliverable is the size of the gap, so a later reader knows whether it is
1 % or 30 %. That is enough to decide whether RVOL can be compared across sources at all.

---

## Deliverable

**`handoff/done/008a-ibkr-data-verification.md`**, readable cold. It must contain:

1. **One paragraph per test: the question, what was run, and the answer** — with the
   actual numbers, not a summary of them. Quote the ADR% difference from Test 1 and the
   VWAP cents difference from Test 4 explicitly; those two are why this task exists.
2. **The raw comparison tables**, small enough to read inline.
3. **Environment**: TWS or Gateway, version, account type, market-data subscriptions
   active, date and time each test ran, and the symbols used.
4. **What you could not do**, and why. An empty section here is suspicious.
5. **Proposed config entries** — key, value, `source:`, `note:` — for anything that
   resolved. Constraints get `source: constraint:ibkr` and a note saying **what the value
   would become under a different broker** (`SPEC.md` §4.4).

**Do not write the config values into `config/` in this task.** Propose them in the note;
they land with slice 008's config loader, so the loader's rules apply to them from the
first commit rather than being retrofitted.

**If a test cannot be run** — no subscription, no overnight coverage, symbol unavailable —
**record it as unrun with the reason.** An unrun test is a known gap. A guessed answer is a
well-formed value that answers a different question, and it will size a position.
