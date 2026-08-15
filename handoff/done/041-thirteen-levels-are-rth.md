---
id: 041
title: The thirteen unruled levels are RTH — OBS-051 narrowed, not closed
type: spec
class: admin
owner: claude-code
depends: 038
---

**Status** RUNNING

# 041 — done. Thirteen levels ruled RTH, and eleven of them do not exist yet.

**The single most important thing in this note: of the thirteen levels `041` rules, only
`52wH` and `52wL` are built.** `HOD`, `LOD`, `PWH`, `PWL`, `PWO`, `PWC`, `MoMH`, `MoML`, `MoMO`,
`MoMC` and `ATH` have no computation, no request and no row anywhere in the tree.

**And both that do exist already requested RTH.** So **no rendered value changed.** What changed
is that the flag is now a *decision* with a recorded reason instead of an inheritance —
which is exactly what `041` says it is for: *"they kept whatever basis they happened to have,
which is not a decision."*

**This is a real outcome, not a disappointing one.** But a reader who expects a number to have
moved should stop expecting it.

---

## 1 — what basis each of the thirteen used before this task

**The present state was the finding, so it is recorded before anything else.**

| Level | Before `041` | How |
|---|---|---|
| `52wH` `52wL` | **RTH** (`use_rth=True`) | via `YEAR_BASIS`, whose own `why` read *"UNRULED by 038. Carried unchanged from the pre-038 behaviour."* |
| `HOD` `LOD` | **no basis — not built** | no computation exists |
| `PWH` `PWL` `PWO` `PWC` | **no basis — not built** | no computation exists |
| `MoMH` `MoML` `MoMO` `MoMC` | **no basis — not built** | no computation exists |
| `ATH` | **no basis — not built** | no computation exists |

`RAIL_ORDER` is `PDH · PDL · PMH · PML · ORH · ORL · 52wH · 52wL · round`, and `level_rail`
returns exactly those plus `VWAP`. **Eleven of thirteen is the honest count.**

---

## 2 — do any of the thirteen share a request with something `038` settled?

**No, and this is asserted rather than eyeballed.**

`52wH`/`52wL` come from `year_high_low`, which calls `_bars` **directly** with its own
`1 Y` / `1 day` request. **It does not go through `_context_block`'s `dailies_on()` memo**, which
is the only place in the tree where two indicators can end up sharing one flag. So ruling the
thirteen cannot move `ADR`, `ATR14`, `PDH` or `PDL`.

`test_the_thirteen_do_not_share_a_request_with_anything_038_settled` pins it by asserting
`year_high_low` issues exactly `["1 Y"]` and never a `60 D`. **If it is ever refactored onto the
shared daily request, that test goes red** — which is the point, because at that moment `038`'s
ruling and `041`'s would be carried by one boolean and neither could move without the other.

**Nothing in the tree suggests the ruling reaches further than the thirteen.** `PDH`/`PDL`/`PMH`/
`PML`/`ORH`/`ORL`, `ADR`, `ATR14`, `VWAP`, `RVOL` and cumulative volume are untouched, and the
suite proves it: the `038` regression fixture still passes unchanged.

---

## 3 — the red, quoted

**`041` asks for one inversion. I ran two**, because the thirteen split into levels that have a
request and levels that do not, and only one of those two halves can be caught on the wire.

**Inverting `PRIOR_WEEK_BASIS` — a group with no request:**

```
AssertionError: PWH PWL PWO PWC must be RTH (041). It declares use_rth=False, which breaks the
composition chain: 038 made PDH RTH, so a week, month or year computed on extended hours would
be higher than every day inside it.
FAILED tests/test_session_basis.py::test_the_thirteen_levels_are_ruled_rth[PWH-PWL-PWO-PWC]
1 failed, 14 passed
```

**Inverting `LONG_BASIS` — the one group that does issue a request:**

```
AssertionError: 52wH 52wL ATH must be RTH (041). It declares use_rth=False, which breaks the
composition chain: 038 made PDH RTH, so a week, month or year computed on extended hours would
be higher than every day inside it.
AssertionError: the 52-week request issued [False]; LONG_BASIS declares use_rth=False and 041
rules it True.
FAILED tests/test_session_basis.py::test_the_thirteen_levels_are_ruled_rth[52wH-52wL-ATH]
FAILED tests/test_session_basis.py::test_a_long_range_request_carries_the_ruled_basis
2 failed, 13 passed
```

**Two failures for one inversion, and the second is the one that matters** — it proves the flag
reached `reqHistoricalData`, which is what `041` asked for. **The first eleven levels can only
ever produce the first kind.** Stated plainly so nobody later reads the parameterised test as
stronger evidence than it is.

**`041`'s instruction not to scan for the string `use_rth` was already satisfied by `038`** —
that test parses `ibkr.py` with `ast` and inspects keyword arguments, because a text scan matches
the module's own docstring warning about the thing.

---

## 4 — the composition property: could not assert, and here is exactly why

**`041` asks: is `PWH` the maximum of its week's `PDH`s in the fixture?**

**There is no `PWH`, and there is no week.** The composition chain the ruling rests on —
day → week → month → year — **exists as an argument and not as code.** No fixture can demonstrate
it because nothing computes the middle two links.

**What can be said, and is:** the chain's *bases* now agree, so when the levels are built the
property is available to be asserted rather than needing a re-ruling. `PDH` RTH, week RTH, month
RTH, long RTH. **That is the whole of what `041` could deliver, and it is worth having** — the
alternative was building the levels first and discovering the mismatch afterwards.

**This is the test to write on the day `PWH` lands**, and it should be written that day: assert
`PWH == max(PDH for each day in the week)` on a fixture spanning a week that contains a
post-16:00 extreme. **On ETH bases that assertion fails; on the ruled bases it holds.** That is
the ruling made falsifiable, and right now it is not.

---

## 5 — two things in `041` that do not match the tree

**Neither changes the ruling. Both are reported because `041` asks for contradictions.**

**1. `ext 10/20/50` have not left the panel.** `041` argues that `OBS-051`'s original reasoning is
void because *"`ext` no longer exists"* — it having left under the scope decision of 2026-08-14.
**They are still in `CONTEXT_ORDER`, still computed by `extension_in_adr`, still rendered.** The
scope decision is a decision; `S012` has not been built.

**So `OBS-051`'s argument still stands** — `ADR $` is RTH under `038`, so an ETH SMA would divide
across two bases — **and it points the same way `041` does.** The conclusion survives; the stated
reason for it was wrong. Recorded in the `OBS-051` resolution so the next reader does not
re-derive it.

**2. `041`'s `OBS-045` and `OBS-046` references point at unrelated rows.** It cites `OBS-046` for
"remove your worktree" and `OBS-045` for "export from the main checkout". In the ledger,
**`OBS-045` is the `keepUpToDate` 5-second cadence finding and `OBS-046` is the
`survived_window` instrumentation defect** — both from `021`. Neither is about worktrees or
exports. **I followed the instructions, which are correct on their own terms**; only the
citations are wrong. Likely an off-by-a-few against the ledger as it stood before `038` added
`OBS-047`–`052`.

---

## 6 — what landed

| file | what |
|---|---|
| `core/indicators/context.py` | `TODAY_BASIS`, `PRIOR_WEEK_BASIS`, `PRIOR_MONTH_BASIS`, `LONG_BASIS` — each with its own `why`. `SMA_BASIS`'s comment rewritten to record that `041` left it unruled deliberately |
| `live/attach/ibkr.py` | `year_high_low` takes `LONG_BASIS`; the comment no longer says "UNRULED" |
| `tests/test_session_basis.py` | `038`'s test 1 **extended, not duplicated**, as `041` requires: the thirteen parameterised by group, the long-range request checked on the wire, and the no-shared-request assertion |
| `docs/specs/SPEC.md` | §4.4a.1 gains the thirteen, the composition argument, the unchanged list, and the accepted TradingView divergence |
| `docs/observations/OBSERVATIONS.md` | `OBS-051` → `PROMOTED` with its resolution; **`OBS-053`** added |

**`YEAR_BASIS` is renamed `LONG_BASIS`**, because `ATH` is not a year and the old name would have
been wrong for a third of what it now serves.

**A rename bug worth recording, because the suite caught what review did not.** The rename hit two
call sites in `level_rail` and my first pass replaced only the first — `52wH` moved and `52wL`
raised `NameError` on every attach. **39 tests went red.** It was invisible in the diff and
obvious in the run. `tests/test_session_basis.py` alone stayed green throughout, because it never
calls `level_rail`: **a targeted test passing is not evidence that a rename landed.**

---

## 7 — the tests, and the exit tests

**`verify.ps1` ran at 2026-08-15 10:05:58 +02:00 from `D:\Dev\momentum`.** No count quoted —
`041`'s last action forbids it and the design session reads `verify-output.txt` directly.

**No previously-passing test was made to fail.** Six tests added.

**Exit test — the refusal still holds for the thirteen.** `041` asks me to confirm a level whose
basis constant is missing still renders `— (no basis declared)` rather than an unlabelled number.
It does: `test_a_value_with_no_basis_refuses_rather_than_rendering_bare` passes unchanged, and it
exercises a `Unit.DOLLAR` value with `basis=None`, which is exactly the shape a level takes.
**Unchanged from `038`, confirmed rather than assumed.**

**The worktree is removed.** `git worktree remove` refused with a lock and the directory had to be
deleted directly, then pruned — noted only because a half-removed worktree turns
`test_pytest_collection` red and looks like somebody else's mess.

**`test_pytest_collection` is still red on `024` and `029`'s stale worktrees**, and now also on
**`worktree-039-risk`, which another session created and is presumably still using.** I did not
touch any of the three. **The `039` worktree is live work, not debris** — do not clean it up on
the strength of that red test.

---

## 8 — what I could not do

1. **Assert the composition property.** §4 — the levels do not exist.
2. **Check eleven of the thirteen on the wire.** §3 — no request to inspect.
3. **Rule the SMA stack.** `041` forbids it: *ruling a value nothing reads is admin.* `OBS-051`
   is narrowed to it rather than closed, and `SMA_BASIS.why` now carries the condition — it must
   be ruled **before anything consumes it**.
4. **Verify the divergence `OBS-053` predicts.** It needs a name whose 52-week extreme printed
   outside regular hours, a live connection and an ETH chart. **That is `c021`, and it is
   Christoph's.** On QQQ the two agree today, so QQQ cannot demonstrate it.

---

## 9 — for Christoph

**`c021`** — read `52wH` for one name whose extreme printed outside regular hours and confirm the
terminal and your ETH chart disagree **in the expected direction**. **A disagreement is the ruling
working.** `OBS-053` exists so that a future session finding that disagreement does not "fix" it.

**Still open from `038`:** the prior regular-session low for QQQ on 8/12, which turns the sixth
fixture pin from a fixture constant into an externally-checked value.

---

**This note needs to be pasted to chat.**
