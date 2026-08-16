<!--
DEV SPEC — authoritative for implementation.

This document is NOT the product specification. Product behaviour — what a panel
shows, what a number means, which basis a statistic takes, what refuses and how —
is owned by the product spec set:

  Google Drive folder: Trading Terminal
  https://drive.google.com/drive/folders/1rHQ9_46N2yhyKJg6Qd6iCnDTDx2Y8TCN

  Documents are referenced BY NAME, never by document link. The current version of
  each carries "- LATEST" in its title; superseded copies carry "- OLD" and live in
  Old spec versions/. Start at SPEC-INDEX, which names which spec owns which fact.

A dev spec is DERIVED FROM a product spec. The derivation runs one way only.
Where this document and a product spec disagree about product behaviour, the
product spec wins and this document is corrected. Where they disagree about
implementation, this document wins.

Ruled 2026-08-16. See PROCESS-SPEC section 8a. Bug row B-085.
-->

# Trading Terminal — Build Plan

> **STATUS** CURRENT · **date** 2026-08-10

**Version** 1.1 · **Date** 2026-08-09 · **Companion to** `SPEC.md`
**Method** Agile. Thin vertical slices. Core first, layers later.
**v1.1 changes:** Layer 0 leaves the terminal (v1.0's slices 016 and 019 deleted; LAYERS renumbered) · no verdict colour renders anywhere (§4.1) · **the terminal advises, it never blocks a trade or changes a size** (§4.2). Both are standing rules below.

> Context for own decision — not financial advice.

---

## 1. Working agreement

**Roles.** Claude Code builds in **`D:\Dev\momentum`**. Christoph is the sole user acceptance tester. Chat (this surface) does design and review and **cannot see the repo** — everything it needs must be written to a file. The handoff convention is **`docs/specs/HANDOFF-PROTOCOL.md`**, which is the authority: five states, copy-and-keep, and `handoff/accepted/`. This plan points at it rather than restating it — a convention described in two places diverges.

**Task files.** Each slice below becomes one `handoff/inbox/SNNN-*.md`. **Slices take the prefix `S`; handoff tasks keep bare numbers** — see the renumbering note in §2. On completion, Claude Code writes `handoff/done/SNNN-*.md` that is *readable cold*: name the files, quote the numbers, say what surprised you. "Done as specified" is not a handoff. See `docs/specs/HANDOFF-PROTOCOL.md` for the states and the copy-and-keep rule.

**One slice at a time.** A slice is not done until Christoph has run its UAT script and said so. No slice starts while the previous one is un-accepted.

**Every slice has three exit tests, not one:**

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | `pytest` passes, including the new behavioural tests |
| **Refusal** | Claude Code | A snapshot test proves the panel refuses correctly when its input is missing |
| **UAT** | Christoph | The named script below, on a real morning or replay |

**The refusal test is not optional and not a nice-to-have.** It is the mechanism that stops "a panel that renders a value with nothing behind it" from reappearing. Five previous times a correct warning sat in a file nobody read; a snapshot test is the version that fails.

**Two standing rules that constrain every panel** — `SPEC.md` §4.1 and §4.2, restated because a plan read slice-by-slice will otherwise violate them one panel at a time:

| Rule | What it forbids | Enforced by |
|---|---|---|
| **No verdict colour** (§4.1) | Colour may never say *good setup · risk-on · half size · bullish detector*. No letter grades, no state names, no detector polarity colouring | Snapshot tests; `_state_cell`'s polarity argument is **deleted, not conditioned** |
| **Surfaced, not refused** (§4.2) | The terminal does not block a trade and does not change a size — **with exactly one enumerated exception, the daily loss limit.** Every threshold is a **`Rule`** (the taxonomy's own kind: *state → bool + reason, an imposed constraint, nothing to fit*) carrying a required **`enforcement: warn \| block`** field, its measurement, threshold, source and timeframe | `enforcement` required, no default; the set of `block` rules must equal `HARD_BLOCKS`, asserted by test; `size_for()` cannot accept rules and does not import them; `stage()` has an enumerated, tested set of raise sites |

| **Every setting is declared, in config, once** (§4.4) | No threshold, window, `useRTH`, or **default in a function signature** lives in code. The defect is not a number in code — it is a number in *two* places, where the signature default wins silently the day the key is missing | Required with no default, `ConfigError` naming file and key; one `config/` directory, one loader; a test scans call sites for literals; `--dump-config` prints every effective value with its file, key and source |

**Colour is not removed — verdicts are.** The grammar is bound to the component kinds, not to mood (`SPEC.md` §4.1): **blue** = a declared parameter, or a value inside its declared band · **amber** = outside it, a rule failed with `enforcement: warn` · **green / red** = a **fitted** signal measured against its pre-registered expected outcome, held or failed · **dim + inverse badge** = the system refusing (absent · not built · warming · stale · frozen) · **red-inverse badge** = `[ STOPPED — DAILY LIMIT ]`, the one blocking rule.

**Green and red render nowhere until something is fitted, and a snapshot test asserts it** — no green and no red while the pre-registration file holds zero fitted entries. That makes §4.1 enforceable by palette rather than by discipline, and it means the first green ever shown on this terminal will mean a claim was pre-registered, measured against outcome, and held. `A+` and `RISK-OFF` do not render at all — the letter is not produced (§6.3), and green is not available to anything unfitted.

Refusals that survive because they are not trade permission: refusing to render a number it does not have · refusing a malformed watchlist into the archive · the two human gates · `SizingError` on arithmetic with no answer.

**`source` is a required field on every config value**, from a closed list: `christoph_preference` · `tradingview_convention` · `qullamaggie_faq_2021` · `orb_v3_tradebook` · `lore_uncredited` (renders `unfitted` wherever it appears) · `fitted@<version>` (changeable only by refitting) · and **`constraint:<source>`** for anything imposed rather than chosen.

**Constraints are prefixed by the authority that imposes them, and `note` is a required field** — empty or missing is a test failure. `constraint:ibkr` (15 s cooldown, 3 depth slots, ~100 data lines, ~60 requests/10 min, 1,000 ticks/request, `useRTH` defaulting to `True`, client-scoped `reqExecutions`) · `constraint:tws` (`transmit=False` cleared on restart, `permId` as the only stable identity) · `constraint:sec` (SSR at −10 %, PDT) · `constraint:exchange` (RTH hours, half-days, tick size) · `constraint:databento` (page sizes, schema availability).

**The prefix exists for portability: `grep 'constraint:ibkr' config/` is the broker-migration checklist, generated for free and always current.** `constraint:sec` and `constraint:exchange` survive a broker change; `constraint:ibkr` and `constraint:tws` do not, and some cease to exist rather than changing value. Each `note` says what the value would become elsewhere — *re-derive it, do not port it.* **Without this, a migration means rediscovering every assumption by hitting it in production.** `--dump-config --constraints` prints them grouped by prefix: the migration document, written by the system rather than from memory.

**Other standing rules that no slice may break.** `phase-3-halted.md` stays halted — no data purchases for it, no signal computation, no fitting, no holdout access. `tests/test_open_questions.py` goes red while any question is OPEN, and that is intended. `tws_order` stays a separate repo. `ib_async` only. Session logic is US/Eastern via `zoneinfo`. Thresholds are named, versioned parameters carrying their source string — never magic numbers.

**Scale.** Each slice is sized for **one to two Claude Code sessions**. If a slice looks bigger, it is two slices.

---

## 2. The shape of the plan

```
CORE — the minimum you use every morning
  008  Make live/ testable                         ← unblocks everything, clears 4 defects
  009  TUI frame + thin day record                 ← tiled, scrolling, refusal grammar
  010  Attach a symbol + the context block         ← IBKR on demand, no cache
  011  Sizing + risk + the two hard limits         ← the thing you touch on every trade
  ───────────────────────────────────────────────── CORE COMPLETE (4 slices)

NEXT — in this order, each a separate decision
  012  Tape: playbook binding + level machine       ← first after core
  013  Watchlist ingest + archive + ingest ledger
  014  Ranked watchlist + grader vector
  015  Execution pull + trade log + review
  016  Remaining tape components + extended hours
  017  Order staging                               ← hard-gated, written release
  018  Databento replay harness
  019  First calibration pass                      ← needs 100+ trades
  020  tws_order: CLOSE side + short rules

DEFERRED — no slice number, see §5
  ALL regime layers in the terminal                SPEC §3.2
  Exposure dial · grader letters · state name · detector colouring   SPEC §12.2-12.5
  Indicator-attached stop modes                    SPEC §12.6
  Several symbols attached at once                 SPEC §12.11
```

**Core is four slices.** After 011 you can attach any symbol, read its context from live IBKR data, price every stop mode, size from your account, and be stopped by your own daily and monthly limits. **That serves 100 % of trades, including the fast path where you decided elsewhere and came here only to size and send.**

**Tape is the first thing after core, and it is split rather than swallowed whole.** 012 ships the playbook binding, the level state machine, and the components needing **no baseline** — prints-at-price and replenishment, signed aggressive volume, print-size distribution. **The rest wait for 016**: tape speed against its own baseline (warms slowly), the sweep proxy (renders `unvalidated` until replay anyway), displayed-depth reliability (needs the 3-concurrent L2 budget), and the extended-hours read.

**Splitting it is what makes it promotable rather than a cliff.** As one block it was the largest slice in the plan and the one whose value is least established; as 012-then-016 the cheap, decision-changing half arrives immediately after core and the expensive half waits for evidence. **Nothing in 012 depends on 011**, so it can be pulled forward if the analytical path turns out to matter more than sizing on a given week.

**One thing core still deliberately omits**, because your scanners already do it: the ranked watchlist.

**Three earlier decisions move, and it is worth being explicit rather than quietly renumbering.**

| Decision | Then | Now | Why |
|---|---|---|---|
| Ingest ledger "in 009, do not wait" | core | **012, with ingestion** | The no-backfill argument only bites once watchlists are being dropped. With no ingest path there are no drops, so nothing is lost by moving it — and splitting the ledger from the ingest it records would be worse |
| Day-context capture "starts now" | core | **already running** | The scheduled task's `.yaml` snapshot (§`REGIME-PROMPT.md`) is capture, and it began this morning. The highest-value context — the pre-market read — is being logged today with no terminal involvement |
| Trade log as a prerequisite for the loss limits | blocking | **not blocking** | `reqPnL` returns day realised and unrealised P&L directly. **The hard limits work in core with no trade log at all** — monthly accumulates one number per session into the day record |

**Everything after 011 is a promotion decision, not a commitment.**

---

## 2a. How a slice actually runs

**Four steps, one loop, and you are the gate at step 3.**

### Step 1 — this session writes the task file

Design happens here, in chat. Output is one `handoff/inbox/NNN-name.md`, written *for a session that cannot ask questions*: file paths, function signatures, config keys, the exact defect being fixed and where it is documented, and the three exit tests.

**Getting it onto your machine.** If `D:\Dev\momentum\handoff\inbox` is a connected folder, this session writes it there directly. Otherwise it is delivered here and you save it. **Either way the task file is the whole handoff — this session cannot see the repo, so anything not written down does not exist.**

### Step 2 — Claude Code builds

You open Claude Code in `D:\Dev\momentum` and say *"do inbox S008"*. It reads the task file, builds, runs the suite, and writes `handoff/done/S008-name.md`.

**How many agents.** For most slices, **one session, no subagents.** The work is sequential and touches shared files, and parallel agents editing one module produce merge conflicts that cost more than the parallelism saves. **Fan out only where the work is genuinely independent**, which in this plan is three places:

| Slice | Fan out | Why it is safe |
|---|---|---|
| **008** | 3–4 agents, one per module, writing behavioural tests | Each writes its own new test file. No shared edits |
| **010** | 2 agents — indicator fetch/compute, and the panel that renders it | Clean interface between them: one produces values, one consumes |
| **015** | 4 agents, one per detector group | Already partitioned by group in the source |

Everywhere else, **one session is faster.** If a slice looks like it needs more, it is two slices.

**Size.** One to two Claude Code sessions per slice. A slice that has not landed after two sessions is mis-scoped — stop and split it rather than pushing through.

### Step 3 — you run the acceptance script

**A slice is not done until you have run its script and said so, and no slice starts while the previous one is un-accepted.** The scripts below are deliberately written so you commit to an answer *before* seeing the output where possible — that is the only way the comparison is honest.

**Read the `done/` note first.** It should be readable cold: what was built, what surprised the builder, what it could not do. *"Done as specified" is not a handoff* — if that is all it says, send it back.

### Step 4 — back here

You report what happened, this session reads the `done/` note, and writes the next task file. **Findings from a UAT script are worth more than the slice** — if the acceptance run disagrees with what the spec expected, that disagreement is the output, and the next task file starts by addressing it rather than moving on.

### What each side can and cannot see

| | Sees the repo | Sees the spec | Runs the code | Decides |
|---|---|---|---|---|
| **This session** (design) | **no** | yes | no | proposes |
| **Claude Code** (build) | yes | only what the task file quotes | yes | no |
| **You** | yes | yes | yes | **everything** |

**This asymmetry is deliberate and it is what the handoff convention exists to bridge.** It also means a convention that lives only in prose will be broken — which is why every rule in `SPEC.md` §4.1 and §4.2 has a test behind it rather than a paragraph.

---

## 3. Core slices

---

> **ORDERING DECISION, 2026-08-11 — `S009` runs before `S008`.** Recorded because it
> contradicts the standing rule that no slice starts while the previous one is un-accepted.
>
> `S008` makes `live/` testable: 16 imported files, zero collected behavioural tests, and
> **an adoption decision nobody has made.** `S009` needs none of it. Deferring the first
> visible panel behind an unmade decision about an imported tree is how Layer 0 stayed
> unbuilt while fully specified.
>
> **`S008` is not cancelled and not descoped, only reordered.** Its four defects remain
> owed: `condition_codes.yaml`, the session-defined-twice bug, the missing behavioural
> tests, and `regime_pull.py`.

### S008 — Make `live/` testable


**Why first.** Three things converge here, and one slice clears all of them. `live/` has **zero collected behavioural tests** across 16 modules, and two consolidation steps already shipped a broken `live/` that stayed green. `live/regime/regime_pull.py` **raises `NameError` on the first call** — Layer 1 is not runnable and import coverage cannot see it. And `preregistration.yaml → tws_order_separation` names `live_has_behavioural_coverage: met: false` as the precondition blocking any future order-staging work. **One slice clears all three.**

**Build.**
0. **Stand up `config/` and its loader** (`SPEC.md` §4.4) — one directory, one file per domain, **one loader that is the only code reading them.** Every key **required with no default**; a missing key raises `ConfigError` naming file and key and never falls back. Every value carries a `source` from the closed list, including **`ibkr_api_constraint`** for the values that are not choices. Ship `--dump-config`, printing every effective value with its file, key and source — **a setting that cannot be printed is a setting that is not in config.** Add the call-site literal scan as a test now, while there are few call sites to fix.
1. Fix `pytest.ini` so `live/tests/` is collected. Seven behavioural tests already exist there and have never run.
2. **Delete `live/regime/regime_pull.py`.** Layer 1 lives in the Claude scheduled task (`SPEC.md` §3.2), so the module has no consumer and its `NameError` is not worth fixing. **`git rm`, not a history rewrite** — the file stays fully recoverable in history, which is the record. **Name the last commit that contained it in the done-note**, so a future reader retrieves it in one command rather than going looking. *(No `core/regime.py` refactor either: the terminal computes no regime layer.)*
4. Behavioural tests for `engine.py`, `render.py`, `marketstate.py`, `detectors.py` — enough that a rename-plus-behaviour-change goes red. Minimum: a fixture session driven through `MarketState` producing known detector states.
5. **Rewrite `core/config/condition_codes.yaml`.** Its banner claims the delivery "carries no condition field at all… a vocabulary this codebase invented," and `handoff/inbox/condition-codes-config-is-unverified.md` is `PARTIALLY_CONSUMED` with the rewrite owed. The accurate statement: a direct venue feed has no condition column because the message *type* is the condition, and auction identification was discharged 133/133 without one. **Do not delete the banner — rewrite the file to say what it is**, and close the handoff note. A config that misleads the next reader is exactly what the convention exists to stop.
6. **Resolve the session-defined-twice defect** (`docs/observations/session-defined-twice.md`, marked `FIRST_BEHAVIOURAL_TEST`). `live/marketstate.py:336` builds its own `Session` from config strings with no holidays and treats half-days as full days, placing `rth_close` at 16:00 when the market shut at 13:00. Make it use `core/session.py`, and add the half-day test that would have caught it.

**Done when.** Full suite green except the deliberate reds (`test_open_questions.py`, `test_incomplete_work.py`). `live/` test count > 40. `regime_pull.py` either runs or is gone, with the reason in the done-note.

**Refusal test.** The half-day case from step 6: a session ending 13:00 must not place `rth_close` at 16:00. That is the defect the observation names and the one a behavioural test would have caught.

**Acceptance — Christoph.** Run the suite before and after. **Then break something on purpose** — rename a function in `marketstate.py` and change its behaviour — and confirm the suite goes red. If it stays green the slice did not do its job, and that is worth knowing before four more slices are built on it.

**Fan out: 3–4 agents**, one per module writing behavioural tests (`engine.py`, `render.py`, `marketstate.py`, `detectors.py`). Each writes its own new test file, so there are no shared edits. Everything else in this slice is one session.

**Not in this slice.** No TUI. No regime anything. No new indicators.

---

### S009 — The TUI frame, the refusal grammar, and a thin day record


**Why.** Build the frame and the vocabulary once, before any panel has content to argue about. This is where the render becomes snapshot-testable — the property the whole plan leans on — and where the **four-colour grammar** stops being prose.

**The day record lands here, thin.** `renderer(record)` must be a pure function from the first panel, or the property is retrofitted later at ten times the cost. Core needs only `schema_version · session_date · generated_at · attached[] · tickets[] · health · regime_snapshot{ref, frozen_at}` — plus **one number per session for the monthly P&L accumulator** (§011). Everything else in `SPEC.md` §2.2 arrives with the slice that produces it.

**Build.**
1. `live/tui/app.py` — Textual app, pinned version, **a tiled layout rather than switchable screens** (`SPEC.md` §3.0a): watchlist, attached symbol and tape across the top; sizing, risk and health along the bottom; **nothing hidden, nothing switched.** Ingest and Review are **episodic** — they open over the layout and close, because a panel used for thirty seconds pre-market has not earned permanent space on the best part of the screen. `Ctrl+Tab` rotates focus between panels and is **the entire navigation surface** — no screen keys, no drag-and-drop, no layout mode. **The terminal does not build window management; that is the OS's job** (`SPEC.md` §3.0a). `Ctrl+P` palette for the long tail.

**One property must not be traded away for a shortcut**: `renderer(record)` stays a pure function of the day record, with no panel reaching around it to compute anything itself. That is what keeps a future **read-only viewer process** — one owner holding the IBKR connection and the slot ledger, N viewers painting from the record in their own console windows, which Windows can then arrange freely — a small slice rather than a redesign. Not built now; just not foreclosed.
2. `live/tui/grammar.py` — the three-axis refusal vocabulary (`SPEC.md` §4) as typed values: `Freshness`, `Presence`, `Confidence`, and a `Cell` that renders them. **This is the only place a value becomes a string.**
3. Port `live/render.py`'s `Result` model into the grammar unchanged — `state: Optional[bool]`, `na_reason`, `degraded`, `degraded_reason`. It is already right; do not redesign it.
4. Panel chrome: box borders normalised to a fixed width, **provenance caption at the right-hand end of every top border**, ASCII-safe fallback theme when `SSH_CONNECTION` is set.
5. **Panels scroll independently, with pinned rows** (`SPEC.md` §3.0a). Risk and limit rows, the health bar, any failed rule and any active refusal are **sticky** — they hold position while the panel moves under them. A panel with content below the fold **says so**: `3–14 of 31` in the caption, `+7 more ↓` at the edge, because *"nothing more here"* and *"more below"* must not render identically. **`window too small` narrows to mean only that the pinned rows do not fit.** Scrolling is the sixth version of *a correct warning nobody was instructed to read* — a limit breach at row 19 of a 12-row viewport is indistinguishable from no breach.
5b. `pytest-textual-snapshot` wired, snapshots at **three widths — 80×24, 120×40 and 240×70** — a layout correct at 120 columns and broken at 240 fails silently on the machine actually used. **Scroll position is part of the snapshot**, and one test drives a failed rule into a panel scrolled to the bottom and asserts it is still visible via the pinned band. Without that test the pinning rule is prose. A too-small terminal renders a stated "window too small" state, never a silently clipped panel.
6. **`config/layout.yaml` — committed, and load-bearing** (`SPEC.md` §4.3). One line per component: `id`, `slot` (an ordinal, not a boolean), `visible`, and a **required `reason` on any change**. The renderer reads it; nothing else does. **Tenet 7 is enforced by test: a hidden component still computes and still writes to the day record** — otherwise only visible components accumulate evidence and the inference is circular. `git log config/layout.yaml` then becomes a free time series of revealed preference, compared against measured contribution in slice 018. **No auto-reordering, ever** — a system that both measures your preference and shapes it destroys the measurement.
7. **Health bar, permanently visible**: source states, last-seen ages, and the ticks-received-vs-frames-painted ratio.

**Done when.** The app boots on an empty day record and every surface renders entirely as refusals — no crashes, no blanks, no zeros. Snapshot suite green at both sizes.

**Refusal test.** *This slice is the refusal test.* The canonical snapshot is: empty record → every panel shows a named refusal. Any future change that turns one of those into `0.00` goes red.

**UAT — Christoph.** Run it with no data at all. **Read the empty screen and tell me whether every refusal is understandable without asking me what it means.** That is the acceptance criterion — not that it looks nice.

---

### S010 — Attach a symbol, and the context block

**Why here.** This is the first slice that puts a real number on screen, and it is the one that makes 011 possible — sizing needs ADR, and ADR comes from here. It is also where the *no local database* decision proves itself: if this slice needs a cache, the decision was wrong.

**Build.**
1. **`/` opens a symbol field** (`SPEC.md` §6b.1b). Type, enter, attached. Three origins recorded — `typed` · `scanner` · `watchlist` — even though only `typed` exists in core. **Contract qualification refuses ambiguity rather than picking the most liquid**: `tws_order` already does this with *"resolved to 2 contracts — ambiguous, refusing to guess."*
2. **Three IBKR requests per attach, and nothing else.** A daily-bar request (20–60 sessions → ADR%, ADR $, ATR₁₄, extension from the 10/20/50 SMA in ADR units, the level rail) · a 20-session intraday request (→ the RVOL curve) · **a today-from-the-open request (→ session VWAP and every other session-cumulative value).** **No nightly cache, no local store, no warm/cold path.**
2a. **No settle timer — render the sample instead** (`SPEC.md` §6b.1b). *n* seconds is the wrong unit: 30 s is thousands of prints on NVDA and four on a thin name at 11:40. Session-cumulatives need no warm-up (they arrive complete); tape baselines already warm on a **count** (`hold_baseline_min: 12`), which is correct; the only real settle is ~2 s for the subscription callback to populate, as `ibkr.py` already does after account requests. **Every value renders what it was computed over** — `VWAP 47.31 (tick-derived · 18.4M sh · 42 min · from 09:30:00)` — which answers the trust question per symbol, where a fixed timer cannot.
2c-bis. **VWAP is computed from one-minute bars — one basis, no alternative.** `Σ(Bar.WAP × volume) ÷ Σ(volume)`. **`reqHistoricalTicks` is not used for VWAP and the tick-derived variant is retired**: one basis means nothing to declare per row, nothing to substitute, nothing to disagree — better than two correct options with a label between them. `Bar.WAP` is the bar's own weighted average, so the approximation is small and **is now the number rather than a deviation from one.** Deletes: 1,000-tick pagination, boundary-second dedup, the tick pacing question, and the `tick budget exhausted` state.
2c-ter. **The five-slot limit governs T&S only.** `reqTickByTickData` is what the five concurrent slots limit; historical bar requests consume none, and `reqMktData` lines are a third budget (~100). **A symbol process rendering context, VWAP and the stop table needs no tick slot at all** — the slot is required only by the tape components in slice 012. **Five is the limit on how many symbols you can read the tape on simultaneously, not on how many windows you can have open.**
2c-quater. **`keepUpToDate=True` is the default; `cum_refresh_s: 120` is the fallback.** Measured in 008b (AMZN, 32.03 min, TWS 178): accepts `useRTH=False`, **515-bar payload anchored at exactly 04:00 which does not slide**, zero API errors, no drop, **~5 s update cadence (median 5.002) against the 120 s it replaces — 24× less stale on a stop level.** **No seam exists**, so the anticipated "one request then keepUpToDate from there" join cannot be got wrong.
2c-quinquies. **Build the REPLACE path, never an accumulate path.** The forming bar is **revised in place — 344 of 376 updates** — mutating `average`(WAP), `barCount`, `close`, `high`, `low`, `volume`; `open` correctly is not. **Both terms of `Σ(WAP × volume)` change on every update.** Measured cost of adding instead, over 33 bars: **VWAP off by only +0.214 ¢, volume overstated 5.94×** (4,730,374 against a true 796,911). **That asymmetry is the worst failure signature available — the number you would sanity-check stays plausible while the one you would not is six times wrong.** **And the exposure is RVOL, whose *numerator* is today's cumulative volume**: a quiet name at RVOL 0.8 renders 4.8, which reads as a stock in play. RVOL is a selection criterion, so the bug would put names in front of you that nothing was happening in. `streaming_bar_update_semantics: revise_in_place`, `source: constraint:ibkr` — under another broker, re-measure.
2c-sexies. **Test five concurrent `keepUpToDate` streams before removing the cadence.** 008b probed one stream in one process; IBKR limits *simultaneous open historical requests* separately from the rate budget. **The pacing conclusion holds for one symbol and is an inference for five** — and the failure would arrive on a morning with five names attached.
2d. **VWAP includes pre-market and the anchor is declared** (`SPEC.md` §6b.1b). Anchors at **04:00 ET or first print, whichever is later** — on a gapper that has done 2M shares before the open, the pre-market VWAP *is* where the level sits at 09:31, and an RTH-anchored one spends the first twenty minutes converging toward it, which is exactly the window the 1- and 5-min playbooks trade. **Render the anchor every time**: `VWAP 47.31 (tick-derived · pre-market incl. · from 04:00 · 18.4M sh)`, plus the pre-market share of volume so a level built on 40k shares is distinguishable from one built on 2M. **Most charting platforms default to RTH-only** — a TradingView VWAP and this one will disagree invisibly, and it lands in `|entry − stop|`.
2e. **`use_rth` is a per-indicator declaration, never a global switch.** Included: VWAP, cumulative volume, volume profile, cumulative delta. **Excluded: ADR% and the SMA stack** — and *structurally*, not by choice: both come off daily bars, and TradingView labels the toggle *"Extended Hours (Intraday only)"* while TC2000 (Kullamägi's platform) says *"extended hours data only appears on intraday charts"*. **The RTH convention exists because neither platform permits anything else** — do not expect a rationale. Opening range excluded by definition.
2g. **IBKR is the only data source. TradingView is not an input** — not a feed, not a cross-check, not an authority on any rendered number. It contributes **definitions only**. When the chart and the terminal disagree, **the terminal is right and the chart is the approximation**, for three structural reasons that are not defects: Cboe One is ~25 % of the tape against IBKR's consolidated view; TradingView accumulates `hlc3` per bar where this accumulates `price × size` per print; and TradingView odd-lot-filters every intraday North American bar. **Do not chase the difference and do not tune toward it.**
2h. **The two conventions adopted from TradingView, with Kullamägi's parameters — the settings are where these go wrong.** **`ADR%`** = `mean over 20 days of (high/low − 1) × 100`, excluding today, daily RTH bars — his own TC2000 formula, **not** TradingView's built-in ADR or screener ADR% (`(mean(H) − mean(L))/close` over 14, a different estimator). **`atr_d14`** = 14-period ATR on daily RTH bars, **RMA-smoothed — Wilder's, α = 1/14, not a simple mean of the last 14 true ranges**, which is the most common way this is implemented wrong. True Range uses the prior *close* including the gap, which is what makes ATR different from ADR at all. Both computed from IBKR bars with `useRTH=True`.
2f. **ATR is two numbers and neither may be called "ATR" unqualified.** ATR has no session logic — TradingView's docs give only `TR = max[(H−L), |H−C₋₁|, |L−C₋₁|]` smoothed by an RMA, one input, `Length`. It inherits whatever bars it is handed. So: **`atr_d14`** (daily, RTH-only unchangeably) is what the **3×ATR stop floor** and the 0.25-ATR tight-stop rule consume, and it is what every current mention of "ATR₁₄" means. **`atr_i14`** (intraday, ETH-dependent, needs `useRTH=False`) is available and consumed by nothing. Pre-market bars have small ranges but large gaps between them, so the two move differently in ways that depend on the name — which is precisely why substitution must be impossible. RVOL must simply match itself — today and the 20-session reference on the same basis. **`reqHistoricalData` and `reqHistoricalTicks` both default to `useRTH=True` and getting it wrong returns RTH-only data silently** — no error, just a different number. **A test asserts no fetch call site omits the parameter.**
2c. **Close the history/live splice, and test it.** Reconstructing then continuing live creates a seam that fails both ways: **overlap** double-counts prints and drags VWAP; **gap** loses them silently. A delay makes the gap *worse*. Order it: **subscribe live and buffer first, then fetch history with an explicit end timestamp, discard buffered ticks at or before it, dedupe on exchange timestamp + sequence.** **Test: reconstruct one session at two different attach times and require identical cumulative volume and VWAP to the cent.** If the seam cannot be verified, render `unavailable (splice unverified)` — a VWAP three cents wrong does not look broken, it looks like a VWAP, and it is a stop level.
2b. **There is no such thing as a late attach.** Session VWAP, cumulative volume, the volume profile and cumulative delta are **reconstructed from history, never accumulated from the live stream** — attaching at 10:12 gives the same numbers as attaching at 09:29. **The VWAP basis is declared and rendered**: `tick-derived` from `reqHistoricalTicks` (exact) or `bar-derived, 1-min` (an approximation, wrong inside any minute where price moved, and most wrong on the fast one-sided minutes that matter). Default tick-derived; **fall back to bar-derived only with the substitution stated** — `VWAP 47.28 (bar-derived — tick budget exhausted)`. **VWAP is a stop level, so the basis lands in the size.**
3. **Pacing is a display state, not an error.** IBKR paces ~60 historical requests per 10 minutes with a 15-second same-contract cooldown. Render `fetching dailies…`, then values, or `unavailable — pacing limit, retry in 42s`.
4. **The context block** of `SPEC.md` §6b.1a: ADR% (mean of `(high/low − 1) × 100`, **excluding today**, N=20 — Kullamägi convention, **not ATR**), ADR $, ADR used with its 20-cell bar and `OVER` past 100 %, **room left in both directions**, extension in ADR units, and the level rail (PDH/PDL, PMH/PML, ORH/ORL, session VWAP, 52-week, round numbers).
5. **Both RVOLs** (`SPEC.md` §8.4). `RVOL(t)` against a per-minute median curve rebuilt at attach; `RVOL_rel` against the sector ETF from `contractDetails`. **Render the sparkline, not only the scalar.** No sector ⇒ `unavailable (no sector mapping)`, **never 1.0**.
6. **One in-session memo, and it is not a database**: the sector ETF series, in memory, never written to disk, refetched after a restart. A test asserts nothing under the repo is written by this path.
7. **`warming` survives on exactly one thing** — tape baselines — and there are no tape components in core, so in practice nothing warms. Daily-derived values are **fetched or `unavailable (reason)`. There is no third state**, because there is no half-populated cache to produce one.

**Done when.** Attach three symbols in a row — one liquid large-cap, one thin small-cap, one with no sector mapping — and every field either shows a number you can check by hand or names why it cannot.

**Refusal test.** Kill the network mid-fetch: the panel renders `unavailable (reason)` per row, **never a partial ADR**. Attach the same symbol twice inside 15 seconds: the second renders the cooldown with its remaining seconds, never a silent drop. A symbol with no sector: `RVOL_rel` refuses by name.

**Acceptance — Christoph.** Attach a name you know well and **check ADR%, ATR and the RVOL reading against your own charts before looking at anything else.** They must agree to the cent and the decimal. **Then attach the same name twice — once pre-open and once at 10:15 — and confirm every value agrees.** They must, because nothing accumulates from the live stream. **Check the VWAP basis label in both** — `tick-derived` or `bar-derived`, never unlabelled.

**Not in this slice.** No sizing, no stop table, no order path, no tape components, no watchlist.

---

### S011 — Sizing, risk, and the two hard limits


**Why.** Turns a chosen name into a number, and it is the panel you touch on **every** trade — including the fast path where you decided in TradingView and came here only to size and send. **This is the last core slice; after it the terminal is useful every morning.** **No order staging** — that is 016 and it is gated behind a written release.

**The two hard limits work here with no trade log**, which is what makes this cut possible. `reqPnL` returns the day's realised and unrealised P&L directly. **Monthly accumulates one number per session into the day record** — and a session that never ran renders `month incomplete, n sessions missing`, never a quietly smaller total.

**Build.**
1. Surface **04, top half only**. Sizing panel from exactly two inputs: entry reference and invalidation. Trailing rules, targets and scale-outs change what happens after; **never the size.**
2. **Five stop modes** (`SPEC.md` §7b.2): VWAP · low of day · low of last closed candle · **low of current (forming) candle** · price override. Each mirrored for shorts, side taken from the declared side and never inferred. ATR-fraction, ADR-fraction and percent are **computed columns**, not modes — they read a distance, they do not choose a level.
2b. **`stop_offset: {mode: cents, value: 5}` applies to all five, and `mode` is required with no default.** No stop sits exactly at its level — that tick is the most likely single price to trade all session. **5 cents is what `tws_order`'s VWAP stop already defaults to**, so core ships one convention rather than a second. `mode` stays required because the unit is where this goes wrong: `5` could be 5c, 0.05 ATR (9c) or 5% of price ($2.50) on the same $50 name. Every row renders the basis — `LoD 48.12 − 5c = 48.07` — never a bare adjusted price, and **the offset is its own column** because it counts toward `|entry − stop|` and can push a tight setup over the stop-width ceiling.
2c. **The forming-candle mode renders `forming — updates until 09:36:00` with a countdown, and the size recomputes with it.** Staging against an unclosed bar records both the value and the fact that it was still forming.
3. **Wrong-side stop fails loudly and never silently sizes.** Long stop below, short above, sign follows the *declared* side. Side is declared, never inferred.
4. **Both stop rules, each bound to its entry timeframe** (`SPEC.md` §6.4 / §7b.2). **≤1×ADR for intraday-ORH entries** (EP: 1.5), **3×ATR floor for daily-close entries** — they were validated on different timeframes and the backtest that killed tight stops tested a daily-close screen. Each renders amber outside its ceiling: `stop 1.4 ADR · ceiling 1.0 (ORB v3, unfitted, intraday-ORH only)`. Neither refuses and neither resizes (§4.2). **What is a hard refusal is applying one across timeframes** — a labelling rule, not a trade block, and the record carries which timeframe the rule was validated against.
5. Comparison table sizes every stop mode at once, and shows which modes would sit inside the ceiling. **You pick.**
6. **Caps are shown, never applied**: aggregate open risk, sector/theme concentration, PDT count. Each renders current value, limit and headroom, and each is a `Rule` with `enforcement: warn`. There is no code path from any of them to the size.
7. **`config/risk.yaml` is created here — the single place these numbers are declared.** **`risk_pct_default`** — a percentage, **set so 1R ≈ $500 at current NLV** (0.40 % at $125k) · `risk_pct_cap: 2.00` · **`daily_loss_usd: 2000`** · **`monthly_loss_usd: 5000`** · `open_risk_cap_R` · `concentration_cap`. Each carries a source string; `risk_pct_default` is `source: christoph_preference`, not `fitted`. **Both loss limits are declared in US dollars** — unambiguous at the moment they bite, and they do not drift when `risk_pct` or the account changes. **R is rendered alongside, computed from dollars, never the reverse.** **NLV comes live from IBKR `reqAccountSummary`, never from config** — `tws_order` already raises `ConfigError`/*"Refusing to guess"* when no account resolves, and sizing refuses rather than using a remembered value. **Read once at session start and frozen, live value rendered beside it**: continuous re-reading would shrink your size as the day's losses accumulate, sizing two trades an hour apart against different accounts with no record of why. **Risk stays a percentage because it must compound with the account** — that is the function, not a drift to correct. **At ≈$500 risk the limits are four losing trades a day and ten a month — both rows render headroom in losses, not only dollars**, because `−$2,690` reads as a lot of room and `5.4 losses left` reads as what it is. **This also surfaces a scaling mismatch that would otherwise bite silently:** risk is a percentage and the limits are dollars, so if the account doubles, 1R doubles and the same $2,000 becomes *two* losses instead of four. The limits tighten in trade-count terms with nobody changing them — visible in the loss count, invisible in the dollars.
8. **The risk line renders in full, always, never collapsed into the size**: `RISK 0.50 % × NLV 124,300 = 1R $621 [edit] cap 2.00 %`. `[edit]` is the per-trade override, bounded by the cap, **and the value used is written into the pre-registration alongside the default it deviated from.** This is where discretion lives now that the dial is gone, and recording it is what eventually makes the dial testable (`SPEC.md` §12.2).
9. **Two loss rows, and they are the only hard blocks** (`SPEC.md` §4.2, §7b.1): `DAY used −$746 limit −$2,000 headroom −$1,254 (2.5 of 4 losses left)` and `MONTH used −$2,310 limit −$5,000 headroom −$2,690 (5.4 of 10 losses left)`, both rendered from the session's first trade, **red and blocking at breach**. `HARD_BLOCKS = frozenset({"daily_loss_breached", "monthly_loss_breached"})`, contents asserted by test. **The monthly limit fires far less often and matters more** — six ordinary red days never trip a daily limit once, and at $500 risk the month is ten losses however they arrive. **Daily auto-resets at the session boundary; monthly rolls on the calendar month. Neither ever blocks `SELL` or `CLOSE`** — blocking a flatten is the one way this exception could do real harm — and a test asserts it for both sides.
10. `stop_inside_noise` rule where the stop sits inside normal bar noise (default 0.25 ATR), `enforcement: warn`.
11. **Conviction multiplier absent from the code, not disabled by a flag.** Size is never scaled by unvalidated signal strength — and now, per §4.2, never scaled by anything except `risk_pct` and the stop distance.
12. **The structural test lands in this slice**, because this is the first slice where enforcement could exist: assert `size_for()`'s parameter list contains no rule type, assert the sizing module does not import the rules module at all, and assert the set of rules declaring `enforcement: block` equals `HARD_BLOCKS`. `SPEC.md` §4.2a.

**Done when.** Entry + invalidation produce a size, with every failed rule shown, every mode comparable, and **no rule anywhere in the arithmetic**.

**Refusal test.** Stop on the wrong side of entry → loud `SizingError`, no number emitted (arithmetic with no answer, not a judgement). Missing ATR → the ATR mode renders `unavailable`, the other three still size, and **the panel does not fall back to a mode you did not pick.** Plus the §4.2a test: a deliberately-added rule with `severity=top` failing on every mode changes **no** number on the panel — and the daily-loss block, the one exception, **changes no number either; it refuses to stage.**

**UAT — Christoph.** Size **five trades you are not going to take**, across four stop modes. Check every number against your own arithmetic. Then deliberately enter a wrong-side stop and confirm it refuses rather than producing a plausible number. **Then take a sixth with a 1.5 ADR stop and every rule failing, and confirm the terminal tells you all of them, clearly, in amber, and still gives you the size.** Finally, breach the daily limit on paper and confirm two things: it stops you opening, and it still lets you close.

---

---

## 4. After core — each a separate promotion decision

Each requires an explicit promotion decision. None starts automatically.

---

### S012 — The tape: playbook binding, the level machine, and the baseline-free components

**Why it is core.** This is the thing you open the terminal for on the analytical path. It is also the **most-built and least-tested** part of the system — a working book reconstruction, capability-driven degradation and replay support all exist, and an audit found the cluster is watching the wrong level for four of six playbooks. So this slice is not "build the tape engine." It is **bind it to the playbook, ship only what needs no baseline, and make every gap render as a reason.**

**Build.**
1. **`entry_construction` becomes a consumed field.** `trigger_level` and `trigger_side` **required, no default** — the same discipline as `lookback`, for the same reason. `detectors.py:501` currently reads `level = st.break_level4 if ... else st.or_high4`, hardcoding one playbook's level, long-only. **With no playbook bound the pane renders `no trigger level declared` and watches nothing.**
2. **`window_scale: range_fraction`.** Every detector window becomes a fraction of the playbook's own OR duration. `size_absorption.window_s: 20` is 33 % of a 1-min range and 6.7 % of a 5-min one; `level_claim.recent_s: 60` is *the entire* 1-min range.
3. **The attach sequence, in the order of `SPEC.md` §6b.1a-seq**: resolve contract → **check the tick slot and render its state before spending a historical request** → dispatch the three historical calls → open tick-by-tick → bind the playbook. **Step 4 never gates step 3**: a symbol with no free slot still delivers everything the sizing panel needs, and the pane says the tape is absent and why.
4. **The level state machine, with its basis on every state** (§6b.1a-seq). `untested · claimed · lost · reclaimed`, **bar-reconstructed before attach and tick-live after**, rendered as `claimed 09:41 (bar)` vs `(tick)` — the first says price held above, the second says the tape showed it being held, **and they are not the same claim.** Before the reconstruction window: `unknown before 04:00`, never `untested`.
5. **Three components only — the ones needing no baseline**: prints-at-price + replenishment (M1), signed aggressive volume with its band (M3), print-size distribution (M6). **M4 tape speed, E1 sweep proxy and M2 displayed depth wait for 016** — they need a warm baseline, replay validation, and the 3-slot L2 budget respectively.
6. **Warming starts at 09:25, because the 1-minute ORB fires at 09:31:00.** A baseline beginning at the open cannot be ready one minute later. `attach_warm_at` is a declared config value. **Render the projection, not just the count** — `warming 7/12 · ready ~09:29 at current rate` — because at 09:27 the question is *will it be ready in time*, and only the projection answers it. **Cold baseline renders `warming`, never FALSE.**
6b. **The pre-open baseline is a different population and is labelled** — `baseline: pre-open 09:25–09:30`. Prints in that window are thinner and wider-spread than RTH prints. **It cannot be seeded from history instead**: the baseline is compared against *live* prints, and IBKR historical is filtered where live is not (`SPEC.md` §6b.1b) — seeding it would compare two bases, the defect this project exists to catch. That is exactly why it needs the five minutes.
6c. **One symbol per process** (`SPEC.md` §6b.1c) — each process attaches exactly one ticker and holds exactly one tick subscription. **The slot ledger disappears**: *N* processes consume *N* slots, an invariant by construction rather than by coordination, and the whole "which five of eight" allocation screen is never built. Launch a process per name at 09:25; launching *is* the allocation. Crash isolation comes free, and Windows arranges the windows. **A symbol may be attached in at most one process** — lockfile keyed on symbol, because two processes racing one ticker produce a broker-side queue neither can explain.
6c-bis. **The pacing budget is per account, not per client ID — processes divide it, they do not multiply it.** This breaks the 30-second cumulative refresh as first specified: 5 processes × 2 requests/min = **100 per ten minutes against a budget of 60**, failing as pacing rejections that look like slow requests. **Fix by arithmetic, not coordination**: `requests_per_10min = processes × (600 / cum_refresh_s)`, and **default `cum_refresh_s: 120`** — 5 processes = 25/10min, leaving 35 for attaches (eleven, at three each). **The risk process refuses to launch the Nth symbol process when the arithmetic would exceed the budget, and says so with the numbers.** One check at launch, the only coordination the multi-process model needs. **Cost: VWAP is up to two minutes old, and its rate of change is highest in the first thirty minutes — exactly when the ORB playbooks trade** — so the as-of stamp is load-bearing on that row, not decoration. Adaptive cadence is the obvious refinement and is deliberately not built: it trades a fixed checkable budget for a variable one.
6d. **Risk, sizing and staging live in exactly one process, and symbol processes cannot perform them.** Not a preference: the loss limits are **session-wide**, and five processes each independently answering *"am I within the daily limit"* could each answer yes and collectively breach it — every one correct in isolation, **the single guarantee this terminal makes about stopping you void.** Enforced structurally (§4.2a): **the symbol process does not import the sizing or staging modules at all, asserted by test.** `HARD_BLOCKS` is evaluated in one place because only one place can. The risk process also renders the slot count (`4 of 5 tick slots held · CRDO NVDA AMD SMCI`) — a symbol process cannot know it and must not guess.
7. **Components render measurements, not verdicts** (§4.1): `M3 signed vol −412k (band ±180k)`. No TRUE/FALSE, no polarity colour — `_state_cell`'s polarity argument is **deleted, not conditioned**.
8. **Events append, they do not alert** (§6b.1a-seq). `10:14:32  47.30  reclaimed (tick) · 3rd test · held 41s` into an in-pane log, **pinned to its last three lines** so the pane scrolls without hiding what just happened. **No pop, no sound, no colour change** — an alert is a claim that the transition matters, and nothing has established that. The log is the raw material for the test that could one day justify one.
9. **Aggressor method on screen** — `lee_ready` or `tick_rule` — and delta renders with its ±13pp band **or not at all**.
10. **Slot model rendered**: 5 tick slots, **true count = nominal minus active price alarms**, exhaustion named with what to detach, 15-second cooldown showing its remaining seconds.

**Done when.** Attach a real symbol on `intraday_orb_1m`, then the same symbol on `intraday_orb_5m`, and confirm **the watched level and the detector windows both change.**

**Refusal test.** Snapshot six states: no playbook bound (`no trigger level declared`) · cold baseline at 09:31 (`warming 3/12`) · slot exhausted (named, with what to detach) · re-attach inside the cooldown (`queued · 11s`) · a level crossed before attach (`claimed 09:41 (bar)`, never bare) · feed killed mid-session (the pane **ages** rather than holding its last value).

**Acceptance — Christoph.** Attach a name you would actually have traded, through a real open, on the 1-min playbook. Then switch to the 5-min and confirm it is watching a different level with different windows. **Then the honest test: pick one component you believe in and one you do not, and watch both for a week.** Anything that never changes a decision is a deletion candidate, and finding that out is the point.

**Fan out: 2 agents** — one on the binding and level machine, one on the pane and its rendering. Clean interface between them.

**Not in this slice.** No M4, E1 or M2. No extended-hours read. No grader, no watchlist, no staging.

---

### S013 — Watchlist ingest, archive, and the ingest ledger


**Why.** `scanner_watchlists/` does not exist on disk, which means **no watchlist has ever successfully passed ingestion.** The door is built and tested; nothing has walked through it. And nothing downstream can be built until the day record exists, because every panel is a projection of one of its fields.

**Build.**
1. **Land inbox 007 first** (watchlist ingestion amendments): schema becomes symbol-only; column-absent and cell-empty must not print the same; `MissingProvenanceCompanion` stops firing (open question `scanner-provenance-requirement-dropped.md` decided it obsolete on 2026-08-09) but the companion is still archived when present. Refusal count drops from four to two. **Close the open question in the same commit** — set `status: RESOLVED`, add the `resolution:` line, move the file to `handoff/done/`. Deleting it does not clear it and must not be made to.
2. `core/day_record.py` — the schema in `SPEC.md` §2.2, versioned, with `write_day_record()` / `read_day_record()` and a JSON-schema test.
3. Wire ingest → day record: a successful drop populates `record.watchlist`.
3d. **The watchlist is capped at eight symbols** (`SPEC.md` §8.2b). `max_watchlist_symbols: 8`, `source: christoph_preference`. **A drop with more rows is refused and nothing enters the archive** — `WatchlistTooLarge: 12 symbols, cap 8` — a contract about the file, not a restriction on trading: `/` still attaches any symbol at any time. **This resolves the pacing problem rather than mitigating it**: 8 × 3 = 24 requests against 60/10min (~4 min) where 30 × 3 = 90 was 50 % over budget and ~15 min. It also moves `reqHistoricalTicks` for the shadow evaluation from ≈33 hours to **≈8.9 hours** — an overnight job with margin. Costs: population ② accumulates more slowly, and **selection pressure moves upstream to the scanner**, which now has to be right before the terminal sees the list.
4. **`scanner_watchlists/ingest_ledger.jsonl` — append-only, committed** (`SPEC.md` §8.2b). One row per accepted ingest: `(watchlist_date, version, content_key, ingested_at, symbols)`. **The watchlist is revised intra-day** — the Drive spec defines refresh scans at 09:35 / 09:50 / 10:15 ET — and `vN` gives an order, not a *when*, so a 09:40 trade cannot currently be attributed to the list that existed at 09:40. **Keep the filename-token ordering exactly as it is**: `sort_key` is `(date, version)` and never mtime, because a copy, restore or touch changes mtime without changing which universe the file describes, and there is already a test that sabotages mtime to prove it. Effectivity renders as a half-open interval: `v1 in force 08:14 → 09:47 · v2 from 09:47`.
4a. **Day-context capture starts here — decided.** `records/context/YYYY-MM-DD.jsonl`, append-only, one file per session. Every item carries **`source · as-of · capture method · seen-before-or-after-the-decision`**, and **nothing beyond that is schema'd** — a rigid schema chosen now will be wrong, whereas a timestamped append log of self-describing items cannot be, since re-interpretation is a read-side problem. The day record carries `context_captured: n items`, **and a session with zero renders as a gap rather than a quiet day** — the real failure mode is a store that silently stops being written to, not one with the wrong columns. Analysis stays gated behind a pre-registered question (`SPEC.md` §12.7).
4b. **Fix `read_archived`'s `ingested_at` in the same commit.** It currently regenerates the value as `datetime.now(EASTERN)` on every read, so an archived list reports the time you looked at it *as though it were the ingest time* — **well-formed and wrong, strictly worse than absent.** Persist the real value or return `None`.
4c. **Assert the ledger is tracked with `git check-ignore`.** `*.jsonl` matches at any depth and this exact filename was confirmed ignored before the negation block existed. **A silently untracked ledger looks present locally and is absent in history** — the worst available failure for an attribution record.
5. **Two absences must render differently**: `column absent from the export` vs `cell present but blank`. `BLANK_CELLS = {"", "-", "--", "n/a", ...}` → `None` and the row still ingests; a missing column is a schema fact about the whole file.

**Done when.** A real Deepvue export drops, ingests, archives, commits, and appears in `records/day/YYYY-MM-DD.json`. `scanner_watchlists/` exists and is tracked (the `.gitignore` un-ignore block is load-bearing — `test_watchlist_ingest.py` asserts it via `git check-ignore`).

**Refusal test.** Four scenarios each produce a distinct, named refusal and **leave no trace in the archive**: malformed filename · same-name-different-content · schema drift · unparseable cell in a present column.

**UAT — Christoph.** Export a real watchlist from Deepvue tomorrow morning. Drop it. Then **deliberately break it three ways** — rename it wrong, change one row and re-drop under the same name, delete a required column — and confirm each is refused by name and that `git log` shows only the good one.

---

### S014 — Ranked watchlist and grader vector


**Why.** The panel you will actually look at every morning. Depends on 009 (records). The D10 regime cap has nothing to consume until 013, so it renders `ABSENT — regime not built` and no cap applies — stated on the panel, never silently permissive.

**Build.**
1. **Land inbox 006** (ranked watchlist panel) on top of 007's contract. Its own key argument holds: *sorting by an unfitted score is a stronger claim than displaying one* — so the sort order carries the `unfitted` label, not just the score column.
2. `core/grader/` — the 13-dimension library of `SPEC.md` §6.2. **Ship the ten computable from OHLCV.** D8 (catalyst), D12 (float) and D13 (sector-relative) render `ABSENT — <missing source>`.
3. `config/playbooks/*.yaml` — the playbook config schema. **Ship two: `intraday_orb` and `intraday_flag`.** Both are fully gradeable from data on hand. `swing_ep` is **defined but renders `UNGRADEABLE — catalyst feed absent`**, because grading an EP on technicals alone produces a well-formed number answering a different question — and the EP is the one setup with published research behind it, so faking it is the most expensive possible shortcut.
4. **Grade emission is the vector and a rank — there is no letter** (§4.1). Per-dimension values, gate results, and the position within today's watchlist on this playbook's weighting. The band cuts (A+ ≥ 0.90 …) are **not implemented**, not implemented-and-hidden — six ladders in six files disagree about what those letters mean and three were set on synthetic tape. `SPEC.md` §12.4 holds them with a readmission criterion.
5. **Every threshold carries its source string** — `qullamaggie_faq_2021`, `zarattini_ssrn_4729284`, `christoph_15min_orb_tradebook_2024`, `lore_uncredited`. A grader whose numbers can't be traced to their origin can't be re-fitted.
6. **RVOL is exactly two measurements** (`SPEC.md` §8.4, settled). **RVOL-at-time** = cumulative volume open→`t` ÷ **median** cumulative volume open→`t` over 20 sessions. **`t` is any minute — 09:31 and 09:35 are just the minutes two playbooks gate on, not the definition.** So the denominator is a **curve**: the 20-session intraday series reduces at attach to one median value per minute (~390 for the regular session), and `RVOL(t)` is then a lookup and a division on every bar. **Render the shape as well as the number** — a sparkline across the session so far, because a bare `3.1×` cannot distinguish a violent first two minutes that has died from steady accumulation still building. Current value always carries its time: `RVOL 10:14 = 3.1×`. **Early readings are noisier** (at 09:31 the denominator is one minute across 20 sessions) — shown, not withheld, but not at equal weight. **RVOL-vs-sector** = the symbol's RVOL_t ÷ the sector ETF's RVOL_t, sector resolved from IBKR `contractDetails` — a ratio of ratios that divides out the common factor, so `3.1× · vs XLK 1.0×` ("everything tech is busy") is distinguishable from `3.1× · vs XLK 1.9×` ("this name specifically"). **Both render; neither replaces the other; they are never collapsed into one number.** No sector ⇒ `unavailable (no sector mapping)`, never 1.0. **This retires `rvol_vs_curve` and `volume_curve.yaml`** — a median over 20 real sessions needs no fitted curve, which removes the calibration question rather than answering it.

**Done when.** All ~30 names from a real watchlist render, ranked, nothing dropped, every grade carrying its vector and its absences.

**Refusal test.** A name with no intraday data available renders `UNGRADEABLE` naming the failing gate and its measurement — not rank 30, not grade F — **and stays selectable and attachable**, because `UNGRADEABLE` is a statement about the grader, not a refusal to let you trade it (§4.2). Names missing a weighted dimension rank in a separate `partial` block below the fully-measured ones, never interleaved. A watchlist where **no name passes the absolute gate** renders the ranking **and** `absolute_gate: FAIL — top RVOL 1.1 < 2.0` — because rank compositing manufactures a best candidate unconditionally, and that is the trap.

**UAT — Christoph.** For **ten mornings**: before opening the terminal, pick your top 3 by hand. Then open it and compare against the ranking. **Log both.** This is the beginning of the picks-vs-model measurement, and the ordering matters — picks are measured *against* the model, never fed *into* it as truth.

---

### S015 — Execution pull, trade log, and review


**Why.** **The highest-leverage missing artifact in the system.** No trade log exists, so Layer 2, grader calibration, the similarity prior and the scoring loop are all blocked on this one thing. It also closes the loop the project description asks for.

**Build.**
1. The three records of `SPEC.md` §8.1 — pre-registration (immutable, hash-sealed), order (keyed on `permId`), trade (derived, versioned).
2. **IBKR reconstruction that survives contact**: dedupe on the `execId` prefix keeping the highest suffix (corrections arrive as an extra callback with identical fields but incremented digits after the final period); treat commission-pending as a distinct state, never zero; `orderRef = plan_id` as the link between intent and fill.
3. Surface **06 Review**: R-distribution histogram (not just the mean), MAE conditioned on winners (the empirical answer to "is my stop too tight"), MFE-vs-realized efficiency, breakdowns by time-of-day / setup / regime-at-entry, and the **process × result 2×2 with the bad-process/good-result cell flagged loudest.**
3a. **The execution pull — build it, because none exists.** A repo-wide search for `reqExecutions`, `ExecutionFilter`, `execDetails`, `commissionReport`, `orderRef`, `permId`, `Flex` returns **zero hits in either repo**; `tws_order` reads open orders, positions and NLV and writes nothing on fill. **`reqExecutions` is client-scoped — and because you press Transmit by hand in TWS, most fills have no local `orderId` at all**, so a pull not configured for all-client visibility returns zero rows and looks like a quiet day. Believe the broker, not the log.
3b. **`core/watchlist.py` gains `for_date(d)`** — it does not exist; `latest_archived()` takes no date and always returns the newest. Short to write from existing parts. **Same-day `vN` is a real ambiguity**: a 09:35 trade scored against a `v2` published at 11:00 is the canonical defect, so **record the snapshot's `content_key` at stage time and reconcile against that exact file** — never `max(version)`. A date with no archived file renders `no watchlist ingested`, distinct from `symbol not on it`.
3c. **The population 2×2** (`SPEC.md` §8.2a) — watchlist membership × taken, as its own panel: follow-through · pass pile · improvisation. **Every statistic on this surface carries its population in the label, and a figure without one does not render.** A test asserts that no aggregate function can be called across two populations. Off-watchlist trades render most of the grader vector `ABSENT` — they are structurally less measurable, and the panel says so rather than letting an unequal-information comparison read as an equal one.
4. **Outcome vs result computed and displayed separately.** Only outcome feeds calibration.
5. **Adherence score**: five binaries → 0–5, **never weighted by P&L.**
6. **Every rule that failed is a field on the trade record** — id, measurement, threshold, source, and whether you proceeded. Surface 06 gains an **override-rate table per rule**. This is the whole evidentiary basis for §4.2: a rule overridden >80% of the time is mis-calibrated or should be deleted, and a rule that never fails is already deleted in practice. **Nothing else in this system can tell you which of your rules are real.**
7. **Expectancy never renders without a confidence interval, and any statistic on n < 100 renders `n = 43, not established`.**
8. Layer 2 now computes and its refusal on the regime surface (013) turns into a number with `n` and a Bayesian interval.
9. Backfill from IBKR Flex for whatever history exists.

**Done when.** A trade you actually took appears end to end: sealed plan → fills → derived trade → review panel. Layer 2 reports a rate with an n.

**Refusal test.** Fewer than the calibration floor of trades → Layer 2 renders `unfitted — n=7 below floor`, with the interval, and **nothing consumes it** — there is no dial left to consume it, which is the point. Rebuild a month of statistics from raw Flex data independently of the live path and **require the two to agree to the cent** — divergence means live capture is lossy.

**UAT — Christoph.** Pre-register **three real trades before entry** — thesis, entry, stop, target, invalidation phrased as a cue-response pair ("if it loses VWAP on volume, I exit"), all sealed before you click. Take them. Then check the review surface reconstructs them correctly, and that the adherence score matches your honest self-assessment. **If it flatters you, it is wrong.**

---

### S016 — The remaining tape components, and extended hours

**Why here.** This is the surface the terminal exists for on a live morning, and it is the most-built part of the system — a working book reconstruction, capability-driven degradation and replay support all exist. It is also the **least-tested**, and an audit found it is watching the wrong level for four of six playbooks. So this slice is not "build the tape engine." It is: **bind it to the playbook, collapse 22 detectors to 11, and make every capability gap render as a reason.** Contracts in **SPEC §5b, §6b** and **ORDER-FLOW-EVIDENCE.md §4.5**.

**012a — the binding must land first, or the pane gets built twice.**

0. **Two playbook fields, not one** (`SPEC.md` §5b.1a). **`playbook_attached`** is a *computation parameter* — required, no default, chosen at attach, selecting the trigger level, side, detector windows and baseline policy. **`playbook_traded`** is a *claim*, declared in the pre-registration at stage time and amendable afterwards. **They may disagree, and the disagreement is data**: `attached: orb_1m · traded: flag` is a countable event whose frequency says whether the attach step is working. **Re-binding is one keystroke, costs no slot and incurs no cooldown** — the subscription does not change, only the computation over it — and the pane **marks the re-bind point** rather than presenting one series computed two ways.
1. **`entry_construction` becomes a consumed field.** `trigger_level` and `trigger_side` are **required, no default** — the same discipline as `lookback` in `SignalSpec`, for the same reason. `detectors.py:501` currently reads `level = st.break_level4 if ... else st.or_high4`, hardcoding one playbook's level, long-only.
2. **`trigger_side: below` inverts the cluster.** One flag, not a mirrored detector set — it changes *which level is watched and which direction counts as through it*. **The polarity-colouring half of the existing machinery is deleted, not driven**: `_state_cell`'s colour-by-polarity with `BEAR` inverting is exactly the "green means bullish" that §4.1 removes, and `GroupScore`'s polarity constructor argument goes with it. What survives is the measurement and the direction it is measured in.
3. **`window_scale: range_fraction`.** Every detector window becomes a fraction of the playbook's own OR duration. `size_absorption.window_s: 20` is 33% of a 1-min range and 6.7% of a 5-min one; `level_claim.recent_s: 60` is *the entire* 1-min range.
4. **`baseline_policy: warm_or_refuse`.** `tape_reader` needs 12 completed holds before C1–C4 fire; on a 1-min ORB the trigger is at 09:31:00 and they will not exist. **Cold baseline renders `warming`, never FALSE.**
5. **Micro-range rule** (`enforcement: warn`) — ORB v3's `opening range < 2–3× spread` renders on the ticket with the range and the spread both shown. It does not refuse (§4.2).
6. **Ship three playbooks bound**: `intraday_orb_1m`, `intraday_orb_5m`, `intraday_flag`. The 1-min and 5-min pair is the test that the scaling actually transfers.

**012b — the level state machine (SPEC §6b.2a).**

One record per level per session, playbook-scoped: `tests[]` with prints-at-price, size consumed, replenished, outcome; `state ∈ untested | claimed | lost | reclaimed` with crossing timestamps; `test_count · holds · broke_at · held_after_break`. **The discriminant is prints, not size** — size vanishing without prints is a market maker repricing.

**012c — the pane.**

7. **Re-skin, don't rewrite.** `render.py`'s `Result` model is already correct — port it into the §4 grammar unchanged. What changes is the last five lines of `_write` and the fixed column constants.
8. **Ship 11 components, not 22.** M1–M6, E1–E2, G1–G2; R1 (spread) relocates to slice 013. Deleted: `BlockOrders`, `PassiveIceberg`, `ImmediateContinuation`.
9. **Detector rows render measurement, not verdict** (§4.1): `M3 signed vol −412k (band ±180k)`, `M1 14 prints at 41.20, 8.2k replenished` — no TRUE/FALSE colouring, no group verdict. Group scores render as a fraction over evaluable members with exclusions counted, uncoloured. Readmission per detector in `SPEC.md` §12.5, and it requires slice 017's replay to measure a hit rate.
10. **`Spoofing` → "Displayed Depth Reliability."** The manipulation claim renders **ABSENT with its reason**, not degraded — "degraded" implies a valid measurement at reduced confidence, and the quantity is unidentified.
11. **Capability derived from data, not from the class.** `DatabentoReplayFeed.capabilities` moves to an instance property counting distinct `publisher_id`.
11a. **Ad-hoc attach — `/` opens a symbol field** (`SPEC.md` §6b.1b). Three origins recorded: `watchlist` · `typed` · `scanner`. **Every indicator comes from IBKR on demand — there is no local database and no nightly cache.** ADR, ATR₁₄, extension, the level rail and both RVOLs are computed from `reqHistoricalData` at attach: **two requests per symbol** (one daily-bar, one 20-session intraday). An ad-hoc symbol and a watchlist symbol are then the *same* symbol — one code path, no warm/cold distinction, nothing to maintain nightly. **If a request fails the indicator renders `unavailable (reason)` and sizing refuses on that mode** — there is no half-populated cache to fall back on, which removes the likeliest route for a fabricated ADR to reach a position size. Render pacing state: `fetching dailies…` / `unavailable — pacing limit, retry in 42s`. **One in-session memo is allowed and is not a database**: the sector ETF series is identical for every name in that sector, held in memory, never written to disk, refetched after a restart. Contract qualification refuses ambiguity rather than picking the most liquid. **The ad-hoc symbol is written to the day record and never to `scanner_watchlists/`** — injecting it would silently redefine the sampling frame retroactively for every statistic already computed against it, the defect that retired `watchlist_builder`.
12. **Slot model rendered**: 5 tick slots, **true count = nominal minus active price alarms**, 3 concurrent L2, exhaustion named, 15-second cooldown queued with a reason.
13. **Backfill** playbook-driven, default 3 min, **anchored to confirmation**; failure attaches live and marks the window `unavailable`.
14. **Aggressor method on screen** — `lee_ready` or `tick_rule` — and delta renders with its ±13pp band or **not at all**.

**012d — extended hours (SPEC §6b.1b).** The prior after-hours reaction verdict — `bought | mixed | sold`, volume vs 50d, close-location in the AH range. It is the per-ticker version of Layer 0 row 11, which the spec calls the highest-signal input, and your disqualifier list already contains *"prior after-hours sold beats"* as a score override. **The rule exists; nothing computes it.** Pre-market structure grading and the non-S&P retail-print caveat land here too.

**Done when.** Attach a real symbol pre-open on `intraday_orb_1m`, then the same symbol on `intraday_orb_5m`, and confirm the detector windows and the watched level both change. Group scores compute over evaluable members only, exclusions counted. Behavioural tests cover M1, M3, E1, E2.

**Refusal test.** Snapshot six states: capability absent (N/A + reason, not FALSE) · cold baseline at 09:31 (`warming`) · no playbook attached (`no trigger level declared`) · micro-range (rule failed and rendered, ticket still stageable) · detached symbol (`STALE`) · sixth attach (slot exhaustion naming what to detach). Plus: kill the feed mid-session and confirm the pane ages rather than holding the last value.

**Acceptance — Christoph.** Attach a name you would actually have traded, through a real open, on the 1-min playbook. Then switch to the 5-min and confirm it is watching a different level with different windows. Then the honest test: **pick one component you believe in and one you don't, and watch both for a week.** Anything that never changes a decision is a deletion candidate, and finding that out is the point.

**Not in this slice.** No sizing, no staging, no grader calibration. E1's sweep proxy renders `unvalidated` until slice 017 runs it against the five-venue data.

---

### S017 — Order staging

**Hard-gated.** `preregistration.yaml → tws_order_separation` requires `live_has_behavioural_coverage: met: true`, which 008 and 012 deliver — but the gate is released by a person in writing, not by a passing test. **Do not build this slice until Christoph releases it.**

Then: surface 04 bottom half. Staged order as a record in **your** store with its own hash (TWS clears `transmit=False` orders on restart, so TWS cannot be the staging store). The eleven pre-send checks, each returning pass / **advise** / **stale**, never a silent default — freshness, echo integrity, `whatIf` (empty margin fields = `unavailable`, never "no impact"), notional caps, price collar, stop sanity with an explicit `triggerMethod`, duplicate guard, position/correlation state, daily risk state, **reconciliation state**, pre-registration completeness.

**One hard block, down from three (§4.2).** **Daily loss breached** blocks: staging refuses for the rest of the session and the row renders red. **Reconciliation unknown** and **pre-registration incomplete** become top-severity warn-rules — full weight, measurement shown, an explicit acknowledgement keystroke **written to the trade record**, refusing nothing. The ticket stages carrying every failed rule as a recorded field.

The keystroke is measurement, not friction: §7b.4 deletes any rule overridden >80% of the time, and that number only exists if the record distinguishes *shown* from *seen and proceeded anyway*. Without it every rule looks 100% overridden and nothing can ever be pruned.

**Two open decisions land in this slice** (`SPEC.md` §11): does the block **auto-reset at the session boundary or need an explicit re-arm** (§11.2), and it must cover **`BUY` and `SHORT` only, never `SELL` or `CLOSE`** (§11.3) — blocking a flatten after a bad morning is the one way this exception could do real harm. **Read §11.2 before building.**

**The structural test.** Enumerate every raise site in the staging path and fail the build if a new one appears. `stage(ticket, acknowledgements) -> StagedOrder` raises only on the four permitted refusals plus `HARD_BLOCKS`, whose contents are asserted by test. Adding a second member is then a visible one-line diff in a named constant — which is the only form in which §4.2 can be changed without anyone noticing.

`[ FROZEN ]` survives, narrowed: it fires only when the system does not know its own state — reconciliation unresolved, echo mismatch, connection lost mid-stage. Read-only, suggest-only manual flatten showing symbol/quantity/account. **It never had the power to stop you trading in TWS and still does not.** Re-arm via config edit plus restart, never a button.

---

### S018 — Databento replay harness

**No subscription (`SPEC.md` §7.2, revised).** Per-byte pulls of **traded tickers only**: `tbbo` for each traded symbol-day after the close, MBO only for the specific symbol-days where a book-dependent component is on trial. At ~20 trades a month that is a few dozen symbol-days — a fraction of the $199/mo Standard plan, and it lands in **the only sample where a detector's hit rate is measurable**, because it is the only sample with both the tape and the outcome. Call `get_cost` before every pull and log the delta against delivered bytes; `harness/spend.py`'s reserve-then-close ledger already maps.

**The base rate comes from bars, not from Databento** (`SPEC.md` §7.2). The ORB is mechanically defined — range high, range low, taken or not, forward excursion — so *"did it trigger and follow through"* is answerable over **every name on the archived watchlist** from IBKR minute bars pulled overnight, at zero cost. Add that pull as step 0 of this slice; the watchlist archive is the sampling frame and it is already in git, frozen before you chose.

**Four populations, never pooled** (`SPEC.md` §8.2a). Watchlist membership × taken: ① **follow-through** (on list, taken) · ② **the pass pile** (on list, not taken — shadow-evaluated) · ③ **improvisation** (off list, taken) · ④ the rest of the market, unobserved. **① vs ② separates watchlist quality from selection quality — two failures needing opposite responses that one pooled number cannot distinguish.** **③ vs ① answers whether preparation helps at all**, and it is trustworthy despite being the least prepared *because the trade record derives from broker fills, not memory* — every improvised trade is captured whether or not you would have mentioned it. Every figure renders its population: `on watchlist, n=612` · `on trades taken from watchlist, n=38` · `off-watchlist, n=9`. Databento buys the tape layer only, on the symbol-days where you also have the outcome.

**The pull is cost-gated and unattended** (`SPEC.md` §7.2). A **post-close scheduled job** — deliberately not a prompt on terminal exit, which is the worst moment to ask anyone anything. **The default is a flat two-tier rule: traded today → tick data; watchlist only → OHLC bars** at the playbook's timeframe. Predictable beats optimal — you can state it from memory, so you can predict the bill before the job runs, and a cost gate you cannot predict gets ignored. **The capability derivation below is an optimisation on top and may only make a pull cheaper, never dearer** — a traded symbol whose playbook selected no tape components downgrades to bars; nothing can upgrade a watchlist row to tick.

**Source: Databento only in this slice.** Where IBKR provides data free it is preferable, but **a source-decision layer is deferred** (`SPEC.md` §12.9) — two sources define sessions, timestamps and split adjustments differently, and a series stitched from both without declaring which segment came from where is the canonical defect in this project. One source first, then a layer testable against it, with parity as its acceptance test. Every stored symbol-day carries its source from day one so the later layer has something to decompose.

**Schema follows the playbook and is derived, not configured**: `schema = coarsest that satisfies ∪ requires over the playbook's selected components`. A flag breakout on the daily needs daily bars; a 5-min ORB needs minute bars; only tape components need `tbbo`; only book components need `mbo`. **A new config knob would be a second source of truth for what the existing `requires` declarations already answer**, and the two would drift. Pull the finest granularity required **once** and aggregate upward — never 1m and 5m separately. Consequence: **the pass pile is nearly free** (bars answer "did it trigger and follow through"), and where bars suffice IBKR may cover it at zero cost. A symbol-day stores the schema it was pulled at; running a `TAS` component against a bar-only pull renders **N/A with its reason** and the verdict inherits the weakest status (Tenet 3) — never a bar-derived verdict passing as tape-derived.

It builds `symbol_days = watchlist(today) ∪ traded(today) ∪ ad_hoc_attached(today)` — ad-hoc-but-not-traded rows take **bars, not tick**, since the only question about them is *"what did it do after I passed"* — **the union, because off-watchlist trades are absent from the watchlist and are exactly the ones that become unmeasurable forever if their tape is never pulled** — calls `metadata.get_cost`, and checks two thresholds from `config/data_budget.yaml`: `per_run_usd: 5.00` and `rolling_30d_usd: 50.00`. **A per-run threshold alone is not a budget** — $5/run is $100/month; auto-approval requires passing both. Under both: it pulls, and the terminal renders one line next morning (`31 symbol-days · $2.14 · MTD $18.60 of $50.00`) — silent means unattended, never invisible. Over either: it pulls nothing and stages a decision showing the estimate, **the five most expensive symbols** (a spike is usually one illiquid name's MBO day), and three options — pull all · pull traded-only · skip. The choice is recorded. Finally, reconcile `get_cost` against delivered bytes: **an overrun beyond `overrun_alert_pct` is a finding, not rounding** — the query shape is wrong, and it is wrong in every pull already made.

Historical `mbo` replay through `DBNStore.replay(callback)` into the same handler the live terminal uses. Gate on `ts_recv`, evaluate on `F_LAST`, treat `F_SNAPSHOT` as init, refuse on `F_MAYBE_BAD_BOOK`. **Parity test: run the same indicator over yesterday's live-captured stream and yesterday's historical pull and assert equality.** That converts "same code for backtest and live" from a vendor claim into a test that fails.

**Databento is the default for replay; IBKR is the default for live** (`SPEC.md` §6b.1b). Not a reversal of *"IBKR is the only input"* — that governs the live terminal, where the broker's view is correct because it is the venue your order meets. **Replay is a different job**, and choosing Databento deletes the ≈9-hour overnight pull, resumability across the daily IB Gateway restart, pacing contention with the live attach path, the undocumented tick-budget question and the 3-year tick limit — **none of which was buying anything but a saved fee that no longer applies** at ~8 symbol-days a session under the existing cost gate.

**The parity test changes purpose, and this is the part not to lose.** It was written to assert equality between live-captured and historical streams. **Equality is no longer expected**: IBKR historical is *"filtered for trade types which occur away from the NBBO"* while Databento delivers unfiltered MBO per venue, so **a component validated on Databento replay runs live on IBKR — different tape, different question.** The test becomes a **per-component measurement of divergence**, not a pass/fail. A component whose divergence is small relative to its effect size validates honestly; one whose divergence is the same order as its effect renders **`unvalidatable — source divergence exceeds effect`** rather than borrowing confidence from a test that did not apply to it. **Recording the divergence is the deliverable** — without it every replay-derived hit rate silently inherits an unmeasured error.

**This is also the only path by which a detector earns its colour back** (`SPEC.md` §12.5): hit rate against forward excursion, per detector, on a holdout. Nothing about §4.1 is reversible without this slice.

---

### S019 — First calibration pass

**Was the second half of v1.0's 019.** It never depended on Layer 0 and survives the deletion intact. Requires 100+ trades in the log and 60 sessions of Layer I logging. **Every result inherits 017's selection constraint — conditional on trades taken, never on setups available.**

Ships the **trials counter on screen**, the deflated Sharpe rather than the raw one, Platt scaling only, and reliability diagrams **with bin counts printed**. Its own pre-registration, its own declared holdout, predicted directions recorded before the holdout opens — **it must not reuse the QQQ tape holdout.**

This is the slice that adjudicates §12.2–12.5: grader letters, the Layer I state name, the exposure dial and detector colouring each have a stated readmission test, and this is where they are run. **Expect most of them to fail, and expect that to be the finding.**

---

### S020 — `tws_order`: the CLOSE side and the short rules

**Why it exists.** The Drive spec says **"four declared sides (side never inferred)."** `tws_order` implements three — `--side {buy,sell,short}` — and there is no `close`. `--cancel` cancels *orders*, which is a different operation from flattening a *position*.

**Build.** `--side close`, with direction **derived from the broker's reported position** — the one place inference is correct, and it must say so on screen. Refuse if no position exists (that is arithmetic with no answer, not a judgement). Then the five short-only items from SPEC §7b.1a, firing the moment SHORT is declared: **SSR active** and **no borrow/locate** as top-severity warn-rules with the fee shown — *not* blocks, because the SEC rule and the borrow desk already enforce them and a terminal that blocks them adds only the habit of blocking. Squeeze fuel, Phase-2-leader and gap-down-onto-support as ordinary warn-rules.

**Gated behind 016**, and behind the same written release. Nothing here touches the transmit wall.

**Acceptance.** Open a paper position, flatten it with `--side close`, and confirm the direction was read from the broker rather than declared. **Then attempt a short on an SSR name and confirm the terminal names SSR, shows the trigger price, and stages the ticket anyway** — the broker will reject the fill, and that rejection is the enforcement, arriving from the party that actually has the authority.

---

## 5. Not in this plan, deliberately

**Layer 0 in the terminal.** The fourteen-row card is produced by the scheduled cloud task and read as prose. The full model, the denominator arithmetic, and the mid-session-veto question are preserved in `SPEC.md` §12.1. **Promote when** three specific written mornings show the prose was ambiguous where a scored row would have resolved it — not when it would be nice to have the number.

**Everything §4.1 removed**, each with a readmission test in `SPEC.md` §12.2–12.5: the exposure dial · grader letter grades and their band cuts · the Layer I state name and desk action · detector polarity colouring. All four are adjudicated in slice 018 and none returns on judgement.

**Indicator-attached stop modes** — MA stops (9/20 EMA, 10/20/50 SMA), ATR bands, VWAP deviation bands, anchored VWAP, confirmed swings (`SPEC.md` §12.6). **Blocked on a real dependency, not on effort:** an MA is not a level until it has been tested, so an MA stop resolver must return the price *and* its claim state (`untested · claimed · lost · reclaimed`) or it renders an arbitrary nearby line as if it were a defended one. **Promote when** slice 012b's claim-state machine ships and the log holds 20+ structural stops that coincided with an MA. The price override covers the case manually meanwhile, and the record shows you chose it.

**The prioritisation pass** (`SPEC.md` §12.7) — one ranked table across *all* families at once: indicators, grader dimensions, stop modes, order-creation features, regime rows, detector components, backtesting. Ranked on: does anything downstream block on it · does it change a decision on a real morning · can it be built without fitting. **Its output is a reordering of §2 above, not a new document.** Run it when the inputs stop changing; until then this plan's order is provisional.

**Any enforcement beyond the one exception** (§12.8). No criterion is offered, because §4.2 is a standing architectural rule rather than a stage to grow out of. The daily loss limit is enforced — decided, on the Coval & Shumway evidence that the moment it fires is the moment judgement is measurably worst. **It is enumerated in `HARD_BLOCKS` precisely so that a second one cannot arrive quietly.** Any addition is a written reversal by Christoph and a one-line diff in a named constant.

**Phase 3 stays halted.** No data purchases for it, no signal computation, no fitting, no holdout access, and no making its failing tests pass. If a test points a future session here, the correct action is to report state and wait.

**The inference engine (P3) stays parked** until hundreds of trades exist — scoring loop, similarity prior, learned stop proposal, sentiment promotion.

**Not built at all:** dealer gamma, FINRA short volume, buyback blackout, HMM regime labels, order-book depth across the watchlist, unusual-options-activity feeds, a continuous 0–100 risk score, Streamlit, HTML as a running UI. Reasons in `SPEC.md` §10.

---

## 6. Housekeeping — do these regardless

Small, unblocked, and each removes a live footgun.

| # | Task | Why now |
|---|---|---|
| H1 | ~~Rotate the Databento API key.~~ **Done, 2026-08-10.** Remaining: **delete the cleartext key from `requirements.txt` and from the three allow-rules in `D:\Dev\.claude\settings.local.json`**, and read it from the environment as every other rule already does. | Rotation invalidated the exposed key, which was the only urgent step. **The old key remains in git history and that is now harmless** — rewriting history would be disruptive and cannot recall what was already fetched. **Removing the live one from the working tree stops the next commit re-exposing it.** |
| **H1b** | **Fix `test_no_secrets.py` so it would have caught this**, then confirm it fails against the pre-rotation key before it passes. | **A secrets test that passes while a live key sits in a committed file is worse than no test — it manufactures confidence.** It scans repo files and never sees `.claude/`; whether it saw `requirements.txt` and missed the pattern, or never scanned it, must be established rather than assumed. **Note the likely form: a key inside an `--extra-index-url https://user:key@…` line, which a naive `KEY=` or assignment-shaped matcher will not match.** Add `.claude/`, `requirements*.txt` and all dependency-manifest formats to the scan, and match on Databento's key shape (`db-` prefix) rather than on assignment syntax. |
| H2 | Delete `push_all.ps1` | Iterates every directory under `D:\Dev` and pushes each; four of those remotes are archived and read-only. Marked obsolete and harmful in `CLAUDE.md`. |
| H3 | Rewrite root `README.md` | Refers to `data/`, `signals/`, `config/` trees that no longer exist and quotes "435 tests" against ~2,500. It reads as the inventory and is not one. |
| H4 | `git add` the three inbox tasks and the open question | Currently **untracked**. Chat syncs `handoff/` — untracked files are not where the convention assumes they are. |
| H5 | Resolve or delete `live/_to_merge/` | Staged, gated on "step 7", enforced by `test_staging.py`. *"A directory that is harmless to ignore is one that gets ignored."* |
| H6 | Rewrite or retire `core/config/condition_codes.yaml` | Its own banner: the delivery carries no condition field at all, so these are "a vocabulary this codebase invented." Actively misleading. |
| H7 | Archive 32 redundant Drive docs | See `DRIVE-ARCHIVE-LIST.md`. |
| H8 | Freeze one filename convention for regime snapshots | Five conventions currently in use for the same artifact. |

---

## 7. What "done" looks like for core

### What core alone gives you — after slice 011

One tiled window. You have decided on a name, wherever that happened. You type `/` and the ticker.

- Two IBKR requests fetch everything: ADR%, ADR $, ADR used with room in both directions, ATR₁₄, extension from the 10/20/50 SMA in ADR units, the level rail, and both RVOLs with the curve drawn as a sparkline. **No cache, so a name you prepared for and a name you found ten seconds ago behave identically.**
- Anything that did not arrive says so by name. Nothing is estimated, nothing falls back.
- You pick a stop level. All five modes price at once with the 5-cent offset shown on every row, each with distance in dollars and in ADR, risk per share, and the resulting size.
- Rules that fail render amber with the measurement, the threshold, and where the threshold came from — **and not one of them changed a number.**
- `RISK 0.40 % × NLV (IBKR · frozen 08:12) = 1R $497`, with the day and month rows showing headroom **in losses, not only dollars.**
- If you have hit the daily or monthly limit, staging refuses in red — **and SELL and CLOSE still work.**
- You place it yourself, in TWS.

**Four slices. Nothing fitted, nothing predicted, nothing on screen with nothing behind it — and one thing that can stop you, which you set yourself.**

---

### And after the full plan

After 019, on a normal trading morning, in one terminal window:

- The watchlist you exported is ingested, verified, committed, and its age is shown.
- The overnight strip shows what moved while you slept — carry, credit, vol term structure, the dollar, oil, gold, crypto, Asia, Europe, ES and NQ — in reliability order, **each with its drift since the 05:00 cloud read**, so you see not just where things are but what changed since someone thought about them.
- Layer I gives you a 30-second institutional read: nine rows, each carrying its source and lag, marked PROVISIONAL. **No state name, no desk action, nothing sizing anything.** The state is being logged where you can't see it, on trial for 60 sessions.
- Layer 1 gives you the four-index regime, cross-checked against an independently-computed scheduled read.
- Layer 0 is the morning's cloud-task prose, linked with its as-of time. You read it. The terminal doesn't score it.
- Layer 2 reports your own follow-through with an n and an interval, or says it can't yet.
- Thirty names are ranked against a playbook, nothing dropped, every entry carrying its dimension vector and naming its absences. **No letters** — a rank within today's list, which is a claim about today's list and nothing more.
- You attach one and read its tape: book depth at the level, cumulative delta, speed, block activity, whether the level is being defended — with every detector the feed cannot support saying so by name, and every inferred reading dimmed and labelled unfitted.
- You attach one and read its tape as measurements — prints, replenishment, signed volume against its band, speed against its own baseline — **with no green and no red telling you what they mean.**
- You pick one. You size it from two inputs: `risk_pct × NLV` and the distance to your invalidation. Nothing in between. Every rule that failed is on screen in amber with its measurement, its threshold and where that threshold came from — **and not one of them changed a number.**
- One thing on the whole surface can stop you, and it is the daily loss limit. It has been visible since your first trade of the session, and it will still let you close.
- You place it yourself, in TWS.
- It reconciles against the broker, and the review surface separates what the setup did from what you did with it.

**Zero fitted predictions. Everything unvalidated visibly unvalidated. Nothing on screen that has nothing behind it. Nothing on screen that decides for you.**

The terminal's whole claim is now falsifiable in one sentence: *it shows you what is measurable, tells you which of your own rules it thinks you are breaking, and gets out of the way.* Whether its rules are worth reading is answered by the override-rate table in slice 015, from your own trades — which is the only place that answer was ever going to come from.
