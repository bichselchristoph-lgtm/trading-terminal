---
task: 005
title: Regime context — Layer 0 / Layer 1 / Layer 2, hard vetoes, exposure grid
status: BLOCKED ON ONE ANSWER (see Blocking question) — everything else is READY
written: 2026-08-09
written_for: a clean session with no prior context
depends_on: 004 (done) only for the archive/provenance pattern, not for data
blocks: 006 (ranked watchlist header), sizing, reconciliation
---

# 005 — Regime context

Second build task of the trading-signal dashboard. 004 built the front door
(watchlist ingestion). This builds the thing that decides how much exposure the
day has earned before a single symbol is considered.

**You do not need any other context to do this task.** Read this file and the
source specs it cites. Do NOT go looking for the research/phase-3 work in this
repo — it is unrelated, it is HALTED by user instruction, and nothing in it
bears on this build. If a file points you there, report and stop. In
particular: `tests/test_incomplete_work.py` has 5 pre-existing failures that
belong to that halted work. Leave them failing. Do not fix them.

## Scope

Build the regime engine: Layer 0 (pre-market risk-on read), Layer 1 (index
regime), Layer 2 (own follow-through), the four hard vetoes, and the
Layer 0 × Layer 1 exposure grid.

**Not in scope:** the ranked watchlist panel (006), per-symbol anything, live
tape, sizing arithmetic, order staging. Build the constraint, not the trade.

## Source specs

| Doc | ID |
|---|---|
| Regime Read Template — Layer 0: Overnight / Pre-Market Risk-On Read | `1k8pWYW6mICMT8T_Too5nxf6E9qatCZpZD-q4CywAfCs` |
| Dashboard Spec — Amendment 1: Layer 0 Session Context | `1QQQXBKrmfqHYbpATv5G060hcWoDlmLQhDzYkE4WxzNo` |
| mockup-02-regime.html — what this looks like on screen | `17t3W8JjwBa9YpeLw6qiB45jW19hhwbWX` |
| mockup-05-live-context.html — the three live rows, and the NOT BUILT state | `1IHzDFLqVpe4Zhc9OKDt64R8jKFhSOk2R` |

Read mockup-README.md (`16gYlaRCd4paFnzVwrvSrAvJWflwBd1dh`) first. The mockups
are blueprints of a PowerShell terminal. There is no web app.

## Settled — do not reopen

| Decision | Detail |
|---|---|
| Layers only ever downgrade | Layer 0 can lower the Layer 1 dial, never raise it. Layer 2 overrides both, downward. A green index cannot lift an amber pre-market read. |
| Computed once, cached for the session | Layer 0 is computed at 08:00 ET and cached. Attaching a ticker at 16:20 SAST must NOT recompute it — the pre-open inputs no longer exist and a recompute silently produces a different, later, worse answer. |
| Session-level, not per-ticker | Layer 0 renders as a header above the ticker panel, never as a row inside it. A per-ticker row implies it varies by symbol. It does not. |
| Vetoes are a separate boolean array | Four hard vetoes, never folded into the score sum. Each caps the read at AMBER regardless of total. |
| Missing input is excluded, never zero | A not-computable input leaves both numerator and denominator. Scoring it 0 shifts the composite toward AMBER and looks like a measured neutral reading. |
| Score is a prediction and is unfitted | The +1/0/−1 weights and the GREEN/AMBER/RED thresholds were hand-assigned before any calibration existed. Renders labelled unfitted, and must not visually outrank a deterministic rule. |
| Vetoes and grid are rules, not predictions | They are risk preferences, legitimate without evidence, and render as rules. "Credit soft while futures green → cap at AMBER" is a preference. "Pre-open ≥ +6 predicts a trend day" is a claim, and is unsupported. |

## Blocking question — ask the user before writing scoring code

**The reduced-denominator arithmetic in Amendment 1 §A1.5 does not add up, and
it is the number that scales into position size.**

The source doc scores two separate cards:

- rows 1–11, pre-open, max +11 → GREEN ≥ +6 / AMBER +2..+5 / RED ≤ +1
- rows 12–14, after the first 30 minutes, max +3 → +2 or +3 ratifies, 0 or +1
  downgrades one step, ≤ −1 forces RED

Amendment 1 then says rows 10 and 13 are unavailable, so "the pre-open total is
out of 9 inputs, not 11."

That is wrong twice. Row 13 (TICK / ADD / RSP) is not a pre-open row — it is an
*opening* row, in the 12–14 card. Removing row 10 from an 11-row card leaves
**10**, not 9. And removing row 13 from the 3-row opening card leaves **2**,
which needs its own rescale: with max +2, "ratifies" now requires a perfect
score and "downgrade one step" catches everything else. The opening card
becomes a downgrade machine.

mockup-02 renders `6 / 9` and inherited the error. Do not implement 9.

**Three things need a decision, and they are the user's, not yours:**

1. Pre-open denominator with row 10 unavailable: 10, not 11 — confirm.
2. Opening denominator with row 13 unavailable: 2, not 3 — confirm, and decide
   whether a 2-row opening card should be allowed to force RED at all, or
   whether below some floor the ratification step is skipped entirely and the
   pre-open read stands.
3. The rescale rule itself. Proportional is the obvious candidate — GREEN at
   ≥ 6/11 of available points, AMBER at ≥ 2/11 — but "obvious" is not
   "decided", and this is the number that becomes half size or full size on a
   real morning.

Until answered: **the composite renders as NOT BUILT / refusal, exactly as
mockup-05 does.** A rendered AMBER looks operational. Build everything else.

## Structure — build the rules first

Amendment 1 §A1.7 splits this task for you, and the split is the point:

**Phase A — deterministic, ships immediately, needs no calibration:**
the four hard vetoes, the Layer 0 × Layer 1 exposure grid, the Layer 1 index
read, the exclusion arithmetic (which inputs are available, what the
denominator is, which rows are named as missing).

**Phase B — the composite score**, which renders unfitted, and which is
blocked on the question above.

Phase A is what actually constrains sizing. It is usable on its own and should
be complete and tested before Phase B is started.

## Where it lives

`core/regime.py`. Same reasoning as `core/watchlist.py`: the dependency rule
forbids `harness ↔ live` in both directions, and both sides legitimately want
to know which regime a given date was traded under. `core` is the only tree
both may import. Keep it stdlib-only if you can, so
`tests/test_import_boundaries.py::test_core_imports_nothing_from_the_repo_at_all`
keeps passing.

## Inputs — report before you build

The fourteen Layer 0 rows need cross-asset data (ES/NQ, Asia indices, AUD/JPY,
DAX/STOXX, VIX term structure, HYG, 10Y/DXY, gold/WTI, BTC) that this repo may
or may not have wired.

**First action: inventory what data sources actually exist in the tree and
report them.** Do not assume, do not invent a feed, and do not add a
dependency to reach one. The known state from Amendment 1 §A1.5:

| Row | Dependency | Status |
|---|---|---|
| 10 — gap breadth | Deepvue pre-market screener export | not wired |
| 13 — TICK-NYSE / ADD | IBKR REST availability never verified | unknown |

## Design notes — proposed, confirm before committing

These are my reading, not prior decisions.

**1. The regime read is hand-entered, on the same pattern as the watchlist.**
The system does not scan; the user exports Deepvue by hand. The same logic
applies here: the user already runs the Layer 0 template as a morning prompt
and produces a regime read. Ingest that rather than automating fourteen feeds
to build P1. A `RegimeInputs` structure where every row is explicitly
`available | unavailable(reason)`, populated from a dated file the user drops,
gets the whole engine working today and leaves a clean seam for automation
later. Rows 12/14 are the exception — per Amendment 1 §A1.4 they are the
per-ticker tape indicators called with SPY/QQQ as the symbol, so they come from
code once those exist, not from typing.

**2. Archive the regime read the way 004 archives watchlists.**
Same two-folder split, same provenance companion, same hard refusals. It costs
almost nothing on top of the ingestion module that already exists, and it earns
something specific: Amendment 1 §A1.6 wants ~1,250 session observations to
validate Layer 0, and a dated immutable record of every read is exactly that
sample accumulating for free from day one. Without it the validation starts
from zero on the day someone decides to run it.

**3. The exposure grid emits the source doc's vocabulary verbatim.**
The grid's cells are: full size + pyramiding allowed; full size, no adds before
10:00; starter size only; starter size, best setup only; starter size, tighten
stops; no new risk today; paper/cash; cash. mockup-02 renders the
GREEN×AMBER cell as "reduced", which is not one of them. Emit the cell text,
do not paraphrase it — a paraphrase is where a sizing instruction quietly
changes meaning.

**4. Layer 2 needs the trade log, and probably does not have one.**
Layer 2 is the user's own breakout follow-through rate over the last 20, per
playbook (Amendment 3 makes it per-playbook, not one undifferentiated rate).
Report whether a trade log with playbook attribution exists. If it does not,
Layer 2 renders `n/a — no trade history` with the reason, not a neutral GREEN,
and not a fabricated rate. Below the calibration floor it renders `unfitted`
and stays a hint, per mockup-02.

## Definition of done

- The four vetoes each have a test asserting they cap at AMBER regardless of
  the score total, and that they are tracked separately from the sum.
- The exposure grid has a test asserting **no** combination of Layer 0, Layer 1
  and Layer 2 states produces a cell above the Layer 1 row's own baseline.
  Downgrades-only is the safety property; assert it exhaustively over the grid,
  not by example.
- An unavailable row is excluded from numerator and denominator, the
  denominator is exposed, and the excluded rows are named. Test that a missing
  row never scores 0.
- Layer 0 computed once and cached: a second call within the same session
  returns the cached value. Test that a later call does not recompute, with a
  control proving the first call did compute.
- The composite renders NOT BUILT until the blocking question is answered.
  Test that no numeric composite is emitted while the rescale is unspecified.
- The three live rows (10, 12, 13) carry a last-updated stamp and are never
  folded into the frozen composite. Test both halves.
- Layer 2 with no trade history renders a reason, not a value.

## Two inconsistencies to report, not fix

**Row 14 cannot be both.** mockup-05 puts rows 1–9, 11, 14 in the frozen 08:00
composite. Row 14 is the first pullback, 10:00–10:30 ET. It cannot be frozen at
08:00. The source doc has it in the opening card. Report which the user wants;
do not pick.

**mockup-README indexes four sheets; the folder has five.** mockup-05 is not in
the table. The user has confirmed the README is stale and the row should be
added — that is handled in 006, not here.

## Tenets this leans on

1 (distrust the data — including our own scoring), 8 (fail loud, degrade
gracefully), 11 (a changed source lowers confidence, never discards).
