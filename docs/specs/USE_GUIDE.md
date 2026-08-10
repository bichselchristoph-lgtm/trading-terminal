# momentum-harness — Use Guide

> **STATUS** HISTORICAL · **date** 2026-08-10
> Describes `momentum-harness` — its own title says so — including `signals/` and
> `data/` trees that commit `7987376` flattened away, and it links `../README.md` as
> "the working record", which is the README H3 finds describes a tree that does not
> exist. None of it is true of this tree. Kept as the record of how the harness was
> operated, never as setup instructions.

An intraday momentum signal harness for swing/momentum trading (Minervini SEPA
+ Qullamaggie EP). It exists to answer one question honestly: **do the signals
on my intraday checklist actually predict anything, and which ones?**

Three audiences, three sections. Read the one you need; the open issues at the
end are shared and marked with who owns each decision.

| | |
|---|---|
| [Product Owner](#for-the-product-owner) | What it's for, what it costs, what's decided, what needs deciding |
| [Architect](#for-the-architect) | Structure, invariants, guards, extension points |
| [Operator](#for-the-operator) | Setup, running it, reading output, what to do when it raises |
| [Open Issues](#open-issues) | Everything unresolved, by owner |

Companion documents: [README](../README.md) is the working record and carries
the full evidence trail. The [Signal Framework
Spec](https://docs.google.com/document/d/1epEGM3qvcLahZ6aOiV-7hZHH0Uc5xbdIhs-CNnYzMic/edit)
governs everything above the data layer.

---

## For the Product Owner

### What this delivers

A ten-signal intraday checklist, scored per session, with the scoring
**separated from the signals** so re-weighting is a config change rather than a
code change. Three layers feed one append-only daily record:

- **Layer 0** — pre-market cross-asset risk-on read
- **Layer 1** — daily index regime (IWM/SPY/QQQ/RSP)
- **Layer 2** — own breakout follow-through rate, which overrides both

The deliverable is not the score. It is **knowing which components of the score
are real**, measured against five years of unselected historical data rather
than against trades already taken.

### Why the discipline costs what it costs

The expensive-looking parts are there to prevent one specific failure: a
plausible number that is quietly wrong. Every guard in the system traces to a
case where the alternative produced clean-looking output and a false
conclusion. Three concrete examples from the build:

- A wrong condition-code guess would have made the auction comparison a
  no-op returning identical populations — reading as "auctions don't matter"
  rather than as "the code never ran".
- An extended-close print at 16:05 would have been folded into the 15:55 bar,
  where 200k extra shares look like a late-day surge, not a defect.
- A trailing baseline built from one data source and applied to another
  reintroduces a ~3× venue-coverage difference *inside* a ratio designed to
  eliminate it.

None of these would have failed loudly. All three now do.

### What is settled

| Decision | Status |
|---|---|
| Calibration data | Databento XNAS.ITCH trades, QQQ/SPY/IWM, 2021-08-05 → 2026-08-04, 1,254 sessions |
| Auction identification | Hybrid: NOII `imbalance` for type and window, size-and-side to locate the print, extended-close `ref_price` to confirm the close exactly |
| Holdout | **2025-08-05**, fixed date declared 2026-08-05 before any analysis, checked once |
| Weight sets | **Two**, fitted independently: `full` (all ten signals) and `live` (auction-independent only) |
| Auction availability | Declared per (source, instrument), never inferred |
| SPY/IWM auctions | Absent from this dataset — they are Arca-listed. ARCX purchase **deferred** pending the QQQ experiment |

### What the experiment decides commercially

The gap between the `full` and `live` weight-set scores measures **what the
auction decomposition is worth**. That number decides whether ARCX.PILLAR or a
consolidated feed is worth buying. If auctions turn out to be noise — a
reasonable prior for the close, which is largely mechanical rebalancing flow —
the SPY/IWM auction gap costs nothing and the purchase never happens.

This is deliberately sequenced so the experiment decides the spend, not the
other way round.

### Current state

Roughly the bottom third is built and tested; the analysis layer is not.

| Layer | State |
|---|---|
| Data (calendar, validation, bars, auctions) | **Done** — 551 tests |
| Calibration guards (holdout, provenance, eras, dependence) | **Done** |
| Signals | **Not started** — 5 structural exist elsewhere and need importing |
| Scoring, records, trade-log join | **Not started** — fully specified |

### What needs you

Six decisions are yours; see [Open Issues](#open-issues) for detail. The two
that gate everything else are **rotating the exposed API key** and **setting it
in the environment** so the remaining data checks can run.

---

## For the Architect

### Structure

```
data/          session calendar, validation, trades → bars, auction identification
harness/       calibration guards: holdout, provenance, eras, dependence
signals/       (not built) one function per signal, raw values only
layers/        (not built) Layer 0/1/2 regime inputs
config/        every threshold, capability, boundary and commitment — versioned
tools/         one-off verification scripts
```

Dependency direction is strictly downward: `harness` may import `data`;
`data` imports nothing from above it.

### The five design rules, and where each is enforced

| Rule | Enforcement |
|---|---|
| Signals return raw values, never scores | Convention; the registry (O-9) will carry `returns` so it is checkable |
| Thresholds are injected, never module constants | `SessionSpec`, `SessionHours`, `ConditionCodes`, `InstrumentCapabilities` are all dataclasses passed in |
| Volume signals are within-source ratios | `harness/provenance.py` — `Baseline` refuses to apply across sources |
| Validation fails loudly | `data/validate.py` — reports every problem, repairs nothing |
| Grouping across sessions is the harness's job | `validate_session` rejects a multi-session frame by default |

### The capability model

Capabilities are declared per **(source, instrument)** in
`config/instruments.yaml`, never inferred from whether anything turned up.
Inference would mean the "session yielded no auction" guard fires on SPY every
day, and weakening it to accommodate that would blind it on QQQ.

```
auction_identification:  databento_imbalance | size_and_side | none
auctions:                [open, close] | []
```

The distinction that matters is **`none` ≠ no auctions**. On a live IBKR feed
QQQ's crosses are genuinely in the consolidated tape — they exist but cannot be
told apart. That combination is the dangerous one, because `bars_ex_auction`
would still contain the cross while claiming not to. `auction_policy` of
`exclude` or `both` therefore raises there. SPY's vacuous case (no auctions at
all) stays permitted, since nothing is concealed.

### Auction lanes

`AuctionRole` has five members and two orthogonal predicates:

| role | `is_session_auction` | `belongs_in_rth_bars` |
|---|---|---|
| `OPEN` | yes | yes (exempt from the RTH clock filter) |
| `CLOSE` | yes | yes (forced into the final bar by role) |
| `HALT` | no | no (occurs during RTH; the clock is correct) |
| `INTRADAY` | no | no |
| `EXTENDED_CLOSE` | no | **no — and this one matters** |

`is_session_auction` gates the "this session had its auctions" guard. A halted
day carrying a resume cross but no opening cross must fail, not pass.

`belongs_in_rth_bars` gates the RTH exemption. Nasdaq's extended close fires at
16:05; had it inherited the exemption it would have been clamped into the grid
and dropped post-close volume into the 15:55 bar.

Extended-close prints stay in the `auctions` frame with `assigned_bar = NaT`.
Absent-from-record is what an identification *failure* looks like, and the two
must remain distinguishable.

### Guard inventory

Everything that raises, and why. None of these should be relaxed without
understanding the case it was built from.

| Guard | Raises when |
|---|---|
| `validate_session` | NaN, inf, duplicate/unsorted index, impossible OHLC, multi-session frame |
| Auction requirement | A declared auction never arrives |
| Auction contradiction | An *undeclared* auction does arrive |
| Decomposition | `exclude`/`both` requested where auctions exist but are unidentifiable |
| Single symbol | A trades frame holds more than one symbol |
| Calendar coverage | A date outside the declared range is queried |
| `seconds_into_rth` | Called on a non-trading day |
| `Baseline` | Built from fewer than 20 sessions, or applied across sources |
| `assert_single_source` | A population mixes sources |
| `assert_training_only` | Holdout dates reach a fitting path |
| `record_evaluation` | The holdout is evaluated twice, or without a pre-registration |
| Secret scanner | A credential pattern appears anywhere in the tree |

### The one frame that carries NaN

`bars_ex_auction` shares an index and columns with `bars`. Where a bar's only
print was the auction, the ex-auction row is **undefined, not absent**:
price columns NaN, additive columns 0.0, `has_trades` False.

Dropping those rows would leave the two populations different lengths, and an
include-vs-exclude comparison over unequal Ns fails silently. Consequence: this
frame cannot go through `validate_session` under the default spec, and scoring
must treat `has_trades == False` as N/A excluded from **both** numerator and
denominator.

### Feed semantics are not stationary

`config/eras.yaml` records dated boundaries where the *meaning* of a field
changes with no schema change. Two are known; assume a third.

- Extended-close auction type appears, early 2022
- `F_PUBLISHER_SPECIFIC` retired across 2025–2026

Both carry `established_by` provenance, because "inferred from presence/absence
in eight sampled pulls" and "stated in a venue change notice" are different
claims and the difference vanishes once only the dates survive.

`harness/eras.py::check_all(signal, dates, values)` reports a standardised
difference per boundary; ≥0.5 pooled SD is flagged material. Run it on every
signal. A signal that shifts hard across a boundary is measuring the feed
rather than the market.

### Extension points

**Adding a signal** — write a function taking one session frame plus injected
params, returning a scalar or a small frozen dataclass. Register it. Add a
threshold and a weight to config. No harness edit. Decorate with
`@requires_valid_session()` so a direct call gets the same guarantee as the
harness boundary.

**Adding a source** — add a block to `config/instruments.yaml` with its
`auction_identification` and per-instrument capabilities. The guards adapt; no
code change.

**Adding an auction type** — add an `AuctionRole` member and decide both
predicates deliberately. Getting `belongs_in_rth_bars` wrong is the extended
close bug again.

### Testing philosophy

551 tests. Two conventions worth preserving:

- **Tests assert the reason, not just the behaviour.** Failure messages name
  the case the guard was built from, so a future reader knows what they are
  breaking.
- **Checks prove they can fail.** `test_the_scanner_detects_a_planted_secret`
  and `test_the_scanner_actually_scans_something` exist because a green suite
  says nothing about whether a check would notice a regression — the same
  argument the `orb_validator` mutation harness makes in the sibling project.

---

## For the Operator

### Setup

There is **no `python` on PATH**. Use the venv directly:

```
C:\venvs\trading\Scripts\python.exe        # 3.12.7 — prefer this
py -3.12                                    # bare 3.12
```

It carries pandas 3.0.3, numpy 2.5.1, pytest 9.1.1, PyYAML, ib_async 2.1.0,
databento 0.82.0, zstandard, pyarrow.

**IBKR access is `ib_async`, always.** Never `ib_insync` — unmaintained, same
API. Its presence in the shared venv is for a sibling project, not a licence to
use it here.

### Credentials

Never in a file, never on a command line — a command line lands in process
listings, shell history, and Claude Code's own permission config. Set the
variable once:

```powershell
setx DATABENTO_API_KEY "..."
```

Then read it into the child process without echoing it:

```powershell
$env:DATABENTO_API_KEY = [Environment]::GetEnvironmentVariable('DATABENTO_API_KEY','User')
C:\venvs\trading\Scripts\python.exe tools\verify_imbalance.py --pull --date 2026-08-03
```

`tests/test_no_secrets.py` fails the suite if a credential reaches the tree.

### Running the tests

```bash
python -m pytest                                   # all 551
python -m pytest tests/test_bars.py -k auction     # one area
python -m pytest tests/test_no_secrets.py          # security only
```

### Building bars

```python
from data.session import bundled_calendar
from data.bars import bars_from_trades, ConditionCodes, InstrumentCapabilities

cal   = bundled_calendar()
codes = ConditionCodes.from_yaml("config/condition_codes.yaml")
caps  = InstrumentCapabilities.registry_from_yaml(
            "config/instruments.yaml")["databento_xnas_itch_trades"]["QQQ"]

out = bars_from_trades(trades, "5min", auction_policy="both",
                       codes=codes, calendar=cal, capabilities=caps)
```

`trades` must be **one session, one symbol**, tz-aware index, with `price` and
`size` (plus `side` for flow columns).

### Reading the output

| | |
|---|---|
| `out.bars` | OHLCV with auctions included |
| `out.bars_ex_auction` | same index and columns, auctions removed, NaN where undefined |
| `out.auctions` | one row per auction: `type, ts, price, size, assigned_bar` |
| `out.primary` | whichever the policy selects — **raises under `both`** |
| `out.metadata` | everything the daily record needs |

Metadata fields that matter operationally:

| field | why you care |
|---|---|
| `interval` | 1-min and 5-min are different populations; pooling them silently is the failure this prevents |
| `source` | live and historical records must never pool |
| `auction_comparison_meaningful` | False → signals 1 and 10 record NaN, not a number |
| `max_intra_rth_gap_seconds` | session continuity; QQQ median 14.2s, p99 32.9s |
| `first_rth_print_lag_seconds` | materially positive means a delayed open |
| `auction_evidence` | `exact` vs `corroborated` close confirmation, plus residuals |
| `trades_dropped_zero_size` | tally, not an error |

### The live ORB path

It splits, because the IBKR MCP connector cannot walk back — `get_price_history`
takes `period` *or* `step_count` and neither accepts an end date, so every
request anchors at now.

- **Today's bars** → MCP connector, one call, whole session including pre-market
- **Trailing baselines** → native IBKR API via `ib_async`, chunked requests
- **Then cache** — pull the 20-session baseline once and extend it daily with
  the session already fetched. After warm-up, history is never re-pulled and the
  baseline is built from exactly the bars the live signals see

During the first 20 sessions use `Baseline.warming(...)`. Ratio signals return
NaN with a stated reason rather than erroring, so the pipeline keeps running.

### When it raises — what it means

| Message contains | What happened | Do this |
|---|---|---|
| `no opening auction found` | Identification config wrong, or a partial session | Check the codes; do **not** weaken the guard to accommodate an instrument that has no auctions — declare its capabilities instead |
| `declares no open auction, but one was identified` | The declaration and the data disagree | One of them is wrong; reconcile before proceeding |
| `needs auctions to be identifiable` | `exclude`/`both` on a source that cannot decompose | Use `include`, and record the dependent signals as unavailable |
| `holds N symbols` | Trades frame not split by symbol | Split before calling |
| `is outside calendar` | Date beyond declared coverage | Extend the calendar deliberately; do not assume a normal session |
| `at least 20 [sessions]` | Baseline built too early | Use `Baseline.warming()` — never borrow the historical baseline |
| `venue-coverage` | Baseline and observation from different sources | Rebuild the baseline from the observation's source |
| `includes N date(s) inside the holdout` | Holdout data reached a fitting path | Filter to training range |
| `check once` | Second holdout evaluation | Deliberate? Pass `acknowledge_repeat=True` so it is on the record |
| `multi-session` | Frame spans more than one ET date | Group in the harness, not the signal |

A guard firing is information. The instinct to relax one is almost always
wrong — every guard here traces to a case where the permissive version produced
a plausible number.

---

## Open Issues

Numbered as in the [README](../README.md), which carries the full evidence.
Owner is who has to decide, not who types.

### Product Owner

| # | Issue | Why it needs you |
|---|---|---|
| **SEC-1** | **Rotate the exposed Databento key.** A key was pasted into chat and then persisted to disk. Removed from `.claude/settings.local.json`; it remains in Claude Code's transcript (26 occurrences), history, and file-history, none of which can be un-leaked. | Only you can revoke it, in the Databento console under your account. **Blocking and urgent.** |
| **O-15** | **ARCX.PILLAR purchase** — SPY/IWM auctions are absent from XNAS. Currently deferred. | The `full` vs `live` score gap is the number that decides this. Deliberately sequenced after the experiment. |
| **O-18b** | **Two weight sets** — registered, not yet fitted. | Confirm the live set is fitted independently, not the full model renormalised. |
| **O-17** | **Trade-log source** — IBKR flex export or maintained by hand. `setup_type` and `exit_reason` are the fields most often skipped and most needed. | Without them, aggregate R says nothing about which failure mode costs money. |
| **O-16** | Not a git repo yet. | `git init` when ready; `push_all.ps1` publishes privately by default. |

### Architect

| # | Issue | Decision needed |
|---|---|---|
| **O-4** | **Bar interval is not signal-neutral.** VWAP-break count and first-bar strength differ at 1-min vs 5-min. Interval is recorded; normalisation is not decided. A raw VWAP-break *count* is not scale-free across sessions of different length. | Decide before `magnitude.py`. |
| **O-6** | `bars_ex_auction` NaN handling is correct in `bars.py` but **unhandled downstream** — nothing consumes `has_trades` yet. | Registry must treat False as N/A excluded from both numerator and denominator. |
| **O-9** | **Signal registry** — fully specified in Spec §1, not built. | Mechanical; no analysis risk. Build first per Spec §7. |
| **O-14** | **Record schema** — tidy long, one row per (date, symbol, signal), with `raw_value` *and* `scored_value`. Spec §2 says "bars dropped from `bars_ex_auction`"; nothing is dropped any more. | Field should be `bars_undefined_ex_auction`. Spec predates the change. |
| **O-10** | **Layer 1 refactor.** `trading-scripts/regime_pull.py` connects to IBKR at import time, returns a verdict from the pull, has inline thresholds and no validation — violating rules 1, 2 and 4. | Split into `regime_facts(df, params)`, a thin fetcher, and a printer. Use `ib_async`. |
| **O-20** | **Era boundaries are bracketed, not exact.** ETC pinned to 2022-02-16…03-15; flag retirement only to 2025…2026. | One full-history `imbalance` pull settles the first exactly. |
| **O-21** | **Is `A.paired_qty` ever non-zero?** Zero on six sessions of 1,254. If ever non-zero there is an executed 16:05 print. | Code already handles it correctly; the scan confirms rather than changes behaviour. Prioritise quad-witching and rebalance dates. |

### Operator / blocked on data

| # | Issue | Unblocked by |
|---|---|---|
| **O-1** | `DATABENTO_API_KEY` not set in any scope. | `setx`, after rotation |
| **O-20/21** | Full-history `imbalance` pull — one `get_range` call covers all five years, making both checks exhaustive rather than sampled | The key |
| **O-7** | `signals/structural.py` + its 33 tests are **not present** in the repo | Dropping them in |
| **O-8** | `signals/magnitude.py` not started | O-4 first |
| **O-11** | Layer 0 pre-market read not started | — |
| **O-13** | `harness/score.py` not started | O-9 first |

### Resolved, recorded for provenance

`O-2` (trades condition path ruled out) · `O-2a` (QQQ-only auctions) ·
`O-2b` (heuristic validated at 99.92% against an independent daily series) ·
`O-2c`/`O-2d` (imbalance adopted; hybrid identification) · `O-3` (calendar
verified 50/50 holidays, 10/10 half days) · `O-5` (asymmetric auction
assignment) · `O-18`/`O-18a` (holdout declared and pre-registered) ·
`O-19` (live path declared) · `O-19a` (same-source baselines) ·
`O-19b` (ORB anchoring and zero-volume bars)

---

*This is a market-microstructure measurement tool. It reports what the tape and
the record say; it does not offer trading advice and it places no orders.*
