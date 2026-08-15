---
id: 039
title: Risk, trade classification and the lock — amended in SPEC, arithmetic in core
type: spec
class: admin
owner: claude-code
depends: 038
---

**Status** RUNNING

# 039 — done. 1R is a fixed dollar figure, and a rounding error was firing a limit.

**`SPEC.md` §7b.1 argued *for* percentage-of-NLV sizing, at length and well** — *"a fixed dollar
risk would be the defect"*, *"drift is the entire function"*. Christoph reversed it on
2026-08-14. **The argument is struck, not deleted**, under a banner naming which half is
current.

**The thing worth reading first is §4.** A trade that made nothing and lost nothing classified
as a **Loser** — the one class that feeds `losses_max_day`, `losses_max_month` and both R-lost
caps — because `10.00 − 9.95` is not `0.05` in binary floating point. **A limit firing on a
rounding error.** Found by the boundary test on its first run.

---

## 1 — what §7b.1 said before, verbatim, and what it says now

**Before** (`SPEC.md` §7b.1, heading *"Risk comes from the account, not the chart"*):

```
1R  = risk_pct × NetLiquidation          risk_pct default 0.50%, cap 2.00%
```

> **Risk is declared as a percentage of NLV, and NLV is read live from IBKR — never
> configured.** … **The percentage is the declaration precisely because it must move with the
> account.** Position size compounds as the account grows and contracts as it shrinks,
> automatically, with nothing to re-tune. **A fixed dollar risk would be the defect** — the same
> $500 on a doubled account is a steadily smaller position in real terms, and on a halved one it
> is twice the exposure. **Drift here is not a problem to warn about; drift is the entire
> function.**

**After** — heading now `### 7b.1 ~~Risk comes from the account, not the chart~~ Risk comes
from config, not from the account`:

```
1R  = risk_usd_per_trade                 declared in config/risk.yaml. Does not move with NLV.
```

**Everything from *"Where `risk_pct` lives"* downward is kept and marked superseded.** The
reversal is not a claim that the struck text was wrong about drift — it is right that drift
happens and right that it compounds. **The disagreement is about whether drift should be a side
effect of marking to market or an explicit decision**, and `c015` §Risk 3 wants it keyed to
*sequences of days won and lost*, from a rules engine that is a later version and not core.
That framing is now in the spec, because the next reader will otherwise see two confident
paragraphs contradicting each other with no account of why.

**Four new subsections**, inserted before §7b.2 so nothing renumbers:

| § | What |
|---|---|
| **7b.1b** | Every closed trade is exactly one of four things |
| **7b.1c** | Five limits, and every one of them is a loss limit |
| **7b.1d** | The lock — staging only — and paper as a launch flag |
| **7b.1e** | The dollar safety limit is a bug detector |
| **7b.1f** | The TRADE panel's content and the six record fields |

---

## 2 — can `tws_order` take absolute risk without modification? **No.**

**It cannot, and the required change is small, well-bounded, and not made here** — `039` says
report only, and `tws_order` is a separate repository by standing decision.

`tws_order/tws_order/sizing.py`:

```python
def compute_sizing(risk_pct: float, net_liquidation: float,
                   entry_price: float, stop_price: float) -> SizingResult:
    risk_dollars = (risk_pct / 100.0) * net_liquidation
```

**`risk_pct` and `net_liquidation` are both required positional parameters and the dollar figure
is derived inside.** There is no argument, config key or code path that accepts an absolute
figure. Exactly what is required:

| # | File | Change |
|---|---|---|
| 1 | `tws_order/tws_order/sizing.py` | A second entry point taking `risk_dollars` directly — **or** make `compute_sizing` accept one of `risk_pct`+`net_liquidation` or `risk_dollars`, and raise when neither or both are given. **Never default one from the other** |
| 2 | `tws_order/tws_order/cli.py:32` | `--risk-usd` beside `--risk-pct`, **mutually exclusive, neither defaulted.** Today `--risk-pct` falls back to `merged["risk"]["risk_pct"]` (0.5), so an unspecified risk silently becomes half a percent |
| 3 | `tws_order/tws_order/config.py:219` | `clamp_risk_pct` has no absolute counterpart. A `risk_usd` needs its own floor/ceiling or an explicit decision that it has none — **the percentage path's cap warns rather than clamping, and whatever is chosen must match that behaviour or the two modes fail differently** |
| 4 | `tws_order/tws_order/config.py:337-342` | The resolution block reads `risk_pct` unconditionally into `ResolvedConfig`. Two mutually-exclusive modes need a discriminated field, not a second optional one |
| 5 | `tws_order/tests/test_sizing.py` | Seven existing cases all pass `risk_pct=`. **They must keep passing unchanged** — that behaviour is correct and tested and `039` says explicitly it must not be deleted |

**The NLV path must survive.** `039` Part 1 is explicit, and the reason is in its own text: *the
terminal must not compute share counts independently — two sizing implementations that disagree
is worse than either being wrong.* **`momentum` computes no share counts in this task and none
are built.**

---

## 3 — which of Part 6's record fields already exist

**None. There is no trade record type in this tree at all.**

| Field | Exists |
|---|---|
| `stop_at_entry` | **no** — now a field on `core.risk.classify.ClosedTrade`, which is an input type, not a persisted record |
| `avg_fill` · `avg_exit` | **no** — same |
| `commissions` | **no** — same |
| `class` | **no** — `TradeClass` exists as a type; nothing stores it |
| `session_date` | **no** |
| `ema9` · `ema21` at entry | **no, and nothing computes an EMA anywhere in the tree** |

`core/risk/classify.py` defines the shape the record must eventually carry, and **nothing
persists.** `039` Part 6 says *build only what is trivial*; persistence is not.

**`ema9`/`ema21` are held open as `OBS-055`**, and the reason is sharper than "not built": **an
EMA at a past instant cannot be reconstructed from daily bars later.** A record written without
them cannot be repaired retrospectively, which makes them expensive-to-defer in exactly the way
`stop_at_entry` is — and unlike every other field in the table, **they have no screen presence
at all**, so nothing will ever surface them as missing.

---

## 4 — the defect: a limit firing on a rounding error

**Found on the first run of `test_each_class_at_and_around_its_boundary`, before any of this
was wired to anything.**

`039` Part 2 closes the break-even band at its edges: `−0.05R ≤ R_closed ≤ +0.05R`. A $10.00
fill with a $9.00 stop exiting at $9.95 is exactly `−0.05R`. In binary floating point:

```
>>> (9.95 - 10.0) / (10.0 - 9.0)
-0.050000000000000710
```

**Which is outside the band.** The naive comparison classified it `L`.

**`L` is the only class that counts against anything** — `losses_max_day`, `losses_max_month`,
`r_max_loss_day`, `r_max_loss_month`. So a scratch that made no money and lost none consumed a
loss against the day's cap, and −0.05R accumulated toward the R limit. **The same arithmetic at
the upper edge misfiles a scratch as `P`, which costs nothing, and at the winner floor flips `W`
to `P`, which costs a record field.** Only the lower edge touches a limit, and the lower edge is
the one a scratch lands on.

Fixed with `_EDGE = 1e-9`, widening each comparison so an on-the-edge value resolves to the
**more conservative** class — `BE` rather than `L`, `W` rather than `P`. 1e-9 is far below any
real R (1R is hundreds of dollars, so a nanoR is a fraction of a cent) and far above the ~1e-16
relative error of the arithmetic producing it.

**The instance is fixed. The class is open as `OBS-054`** — every `>=`/`<=` against a configured
threshold on a value derived by subtraction or division has this shape, and nobody has swept
them. Named candidates: the tight-stop rule (`0.25 ATR`), the `≤ 1.0 ADR` stop ceiling, `038`'s
`±0.02ADR` anchored-window band, and §7b.4's `80%` override-rate prune.

**What made it findable was parametrising the exact edges rather than values either side of
them.** A test written with `9.90` and `10.10` would have been green and useless.

---

## 5 — the two reds, quoted

`039` asks for the classification and sum tests seen red first. Broken deliberately in the
worktree — the refusal defaulted to break even, and `Counters`' invariant disabled:

```
E       AssertionError: assert <TradeClass.BREAK_EVEN: 'BE'> is None
E        +  where <TradeClass.BREAK_EVEN: 'BE'> = Classified(r_closed=0.0, trade_class=<TradeClass.BREAK_EVEN: 'BE'>, unavailable=None).trade_class
E       Failed: DID NOT RAISE ValueError
E       assert 2 == 1
E        +  where 2 = Counters(trades=2, winners=1, partials=0, break_evens=1, losers=0, unclassifiable=0).trades
FAILED core/tests/test_trade_classification.py::test_a_trade_with_no_entry_stop_is_unavailable_and_never_break_even
FAILED core/tests/test_trade_classification.py::test_the_sum_can_actually_fail
FAILED core/tests/test_trade_classification.py::test_an_unclassifiable_trade_is_counted_and_is_outside_trades
3 failed, 25 passed in 0.21s
```

Restored: **35 passed.** The red was demonstrated in the worktree, never by mutating the shared
tree — `OBS-036`.

**And the boundary red, which was not staged**, quoted because a defect found by accident is
worth more than one demonstrated on purpose:

```
E       AssertionError: assert <TradeClass.PARTIAL: 'P'> is <TradeClass.BREAK_EVEN: 'BE'>
E        +  where <TradeClass.PARTIAL: 'P'> = Classified(r_closed=0.05000000000000071, ...)
FAILED core/tests/test_trade_classification.py::test_each_class_at_and_around_its_boundary[10.05-TradeClass.BREAK_EVEN]
FAILED core/tests/test_trade_classification.py::test_each_class_at_and_around_its_boundary[9.95-TradeClass.BREAK_EVEN]
3 failed, 31 passed in 0.26s
```

---

## 6 — does anything in the tree still reference a winners cap or a gain-based stop?

**No. Searched and clean.**

```
grep -rniE "winners_max|r_gain_stop|gain-based stop|winners cap" --include=*.py --include=*.md --include=*.yaml .
(no matches outside handoff/inbox/039 itself)
```

Consistent with `039`'s own claim that neither v1.0 nor v1.1 reached the tree. **A test now
holds it that way** — `test_no_cap_on_winning_trades_or_on_gains` refuses five key names in
`config/risk.yaml` and carries the reason, so the next person to add one reads *why* before
doing it rather than after.

---

## 7 — contradictions between `039` and `SPEC.md`, and where I stopped

**One internal contradiction in `039` itself, and I did not stop — I generalised, and it
reduces exactly to what was asked.**

Part 2 states `R_closed = (avg_exit − avg_fill) ÷ (avg_fill − stop_at_entry)` **and** requires
classification net of commissions. **The per-share form has nowhere to put a commission.** The
implementation computes the dollar form:

```
net P&L = (avg_exit − avg_fill) × quantity − commissions
risk    = |(avg_fill − stop_at_entry) × quantity|
R       = net P&L ÷ risk
```

`test_zero_commission_reduces_to_the_formula_039_states` pins the two together at every point
where they must agree. **Signed `quantity` makes it side-agnostic with no branch**, and the
absolute value on the denominator is load-bearing — without it a short's risk is negative and
every short classifies as its own mirror image, which has its own test.

**No contradiction with `SPEC.md`.** §7b.1's percentage model is superseded rather than
contradicted, which is what `039` Part 1 asks for. The `daily_loss_usd` / `monthly_loss_usd`
keys `039` Part 4 says *"already exist in `SPEC.md` §7b.1 as hard blocks"* — **they do**, in the
`HARD_BLOCKS` frozenset, and Part 4 records their purpose without changing them.

**One judgment call, recorded rather than asked.** `039` Part 2 requires `trades = W + P + L +
BE` and Part 3 makes `trades_max_day` a limit on `trades`. **A trade with no `stop_at_entry`
therefore counts toward no limit at all** — the two requirements cannot both read the same
number. I implemented `039` exactly as written and surfaced the consequence (`Counters.
unclassifiable`, `Counters.closed_total`, a test naming it, and `OBS-056`) rather than quietly
redefining `trades`, **because redefining it would make the asserted invariant false and no test
would say so.** Which number `trades_max_day` reads is a ruling, not a choice.

---

## 8 — what I could not do

- **`tws_order` is unchanged.** §2 says exactly what it needs. `039` forbids the change here and
  I did not make it.
- **Nothing is persisted, nothing is enforced, nothing renders.** `039` builds no panel and no
  limit enforcement, so `config/risk.yaml` **has no reader** — `risk_usd_per_trade: 500` is the
  number every position size will come from and no code path reaches it. `OBS-057`.
  `tests/test_risk_config_matches_core.py` is a stand-in reader for the three values that *do*
  have a code counterpart; it deliberately does not pin the seven limit values, because
  asserting them against a second copy of the same literals would be a test of nothing.
- **`ema9`/`ema21` are not computed.** `OBS-055`.
- **The threshold sweep `OBS-054` asks for is not done.** One module's edges are fixed.
- **The `0.05R` / `1.00R` thresholds are unfitted and ship that way**, as `039` Part 5 directs.
  They gate nothing.
- **`c019` has no file in `christoph/`.** `039`'s exit table names it; `christoph/open/` is
  authored by the design session and Claude Code must never write there. This will show up in
  `test_uat_has_a_file` alongside `017`, `020` and `037`.

---

## 9 — two things about the task queue that are not `039`

**`038` was already done when I was asked to run it.** Another session merged it this morning
(`da486e3` … `79e95f4`). **`038`'s own addressing gate disqualified me** — *"if
`handoff/done/038-*.md` does not [exist], this task is for you"* — and it does, so I did not
touch it. The gate worked exactly as designed and this is the first time it has fired.

**`038` v1.1 existed in Drive and differed from the merged v1.0.** `tools/sync_from_drive.py`
refused to overwrite and reported both hashes. I was about to raise it as a question;
**`042-for-code-spec-four-deltas.md` arrived first and is the answer** — the design session
trashed the Drive copy and reissued the four deltas as a new task. **The pipeline handled this
correctly end to end and nobody had to remember anything**, which is worth recording because
every mechanism involved was built in the last three days.

---

## 10 — test results, verbatim

**After the merge, in `D:\Dev\momentum`:**

```
8 failed, 414 passed, 1 warning in 37.60s
```

**422 collected, of which 35 are this task's** — `pytest --collect-only` on the two new files.
So the tree stood at **387 collected, 8 failed, 379 passed** before `039`, and stands at 422 / 8
/ 414 after. **The failure count did not move.**

*(That before-figure is arithmetic on two measurements taken here — 422 total and 35 mine — not
a suite run at `79e95f4`. Stated that way deliberately: an earlier draft of this note asserted
"8 failed, 406 passed" as an observed baseline and it was neither observed nor right. Quoting a
count you did not run is the defect this project names most often, and it very nearly went into
the note that says so.)*

`verify.ps1` ran as the last action and its output is not pasted, per `039`'s instruction.

**The same eight pre-existing failures, and no new ones.** `test_handoff_state_declared`,
`test_observations_ledger` (×2), `test_pytest_collection`, `test_regime_prompt_invariants` (×2),
`test_regime_snapshot_could_not_do`, `test_uat_has_a_file`.

**One of the eight gains an entry from this task and it is correct to** —
`test_uat_has_a_file` now names `039` because this note declares `c019` and no file in
`christoph/` declares slice `039`. Declaring `UAT | … | None` to clear it would be a lie.

**`test_pytest_collection` is still red for `.claude/worktrees/024-subagent-roster` and
`029-entry-point`** — `OBS-046`, two worktrees left on disk since 2026-08-13. **I removed mine
and left theirs**; deleting another session's checkout to make a test green is what `OBS-036`
warns about.

---

## 11 — the ledger, and an id collision inside it

Five rows: **`OBS-054`** (the float boundary class), **`OBS-055`** (`ema9`/`ema21`),
**`OBS-056`** (an unclassifiable trade counts toward no limit), **`OBS-057`**
(`config/risk.yaml` has no reader), **`OBS-058`** (see below).

**They were written as `OBS-053`–`OBS-056` and renumbered during the merge**, because another
session had committed its own `OBS-053` in the meantime. **Git caught it only because both rows
landed on the same line of the same file.** Had the other session appended a blank line first,
both would have merged cleanly and the ledger would now hold two `OBS-053`s with every later
citation ambiguous.

**`tests/test_observations_ledger.py` validates schema, status and `review-by` and never checks
that ids are unique** — the one property a register of record most needs. That is five lines and
**I did not write it**: adding a ledger test inside a slice about risk is how a task acquires
work nobody scoped. `OBS-058` holds it, and `031` is the general fix.

Two forward references in `SPEC.md` §7b.1b and §7b.1f were renumbered with the rows.

---

## Files

| path | change |
|---|---|
| `docs/specs/SPEC.md` | §7b.1 reversed under a supersession banner, struck not deleted; §7b.1b–§7b.1f new |
| `config/risk.yaml` | **new.** 1R as a fixed dollar figure; the five limits; the classification thresholds |
| `core/risk/classify.py` | **new.** `R_closed` net of commissions, the four classes, `Counters` that refuse to exist unless they sum, `r_lost` separate from `r_net` |
| `core/risk/__init__.py` | **new**, empty, matching `core/indicators/` |
| `core/tests/test_trade_classification.py` | **new.** 35 tests |
| `tests/test_risk_config_matches_core.py` | **new.** The drift pin between the yaml and `core` |
| `tests/test_adoption_log_complete.py` | five allowlist entries; the count is now 47 |
| `docs/observations/OBSERVATIONS.md` | `OBS-054` … `OBS-058` |

---

## Exit tests

| test | who | state |
|---|---|---|
| **Green** | Claude Code | **Done.** `verify.ps1` ran with the classification and sum tests; both seen red first (§5) |
| **Refusal** | Claude Code | **Done.** A trade with no `stop_at_entry` classifies `unavailable (no entry stop recorded)`, never break even — `test_a_trade_with_no_entry_stop_is_unavailable_and_never_break_even`, and a second case covers stop-equals-fill for the same reason |
| **UAT** | Christoph | **`c019` is not performable yet and `039` knows it** — set `trades_max_day: 1`, take one paper trade, confirm TRADE empties with the reason and the config key. **No TRADE panel exists, no limit is enforced, and nothing reads `config/risk.yaml`.** This UAT belongs to `S011` |

---

## THIS NOTE NEEDS PASTING TO CHAT

**Writing it is not reporting it.** Three things the design session cannot get any other way:

> **1.** A rounding error was classifying scratches as losses and consuming the day's loss cap
> (§4). Fixed here; the class is unswept.
> **2.** `tws_order` cannot take absolute risk without the five changes in §2, and `039` forbade
> making them.
> **3.** `c019` cannot be performed — there is no TRADE panel and no enforcement. `039` Part 5
> says "no panel work in this task", so the UAT it declares is one slice ahead of itself.
