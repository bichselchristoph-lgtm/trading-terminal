---
id: 082
title: Does concurrent dispatch cost the fast requests time — batched against concurrent, measured
type: task
class: admin
unblocks: NOTHING
story: none
owner: claude-code
depends: none
touches: nothing — no production file is edited by this task
bugs:
  - id: B-138
    action: measure
---

**Status** WRITTEN

# 082 — batched against concurrent, on the wire

**Measure. Do not fix.** Nothing in the repo changes. If the numbers point at
an obvious improvement, **write it in the done-note and do not build it.**

**`unblocks: NOTHING` is honest rather than modest.** No product task is
waiting on this. It exists because B-138 is a number that could undercut a
drawing Christoph has already signed off, and nobody knows whether it is real.

---

## 0. Is this task for you

**If `handoff/inbox/082-for-code-task-batched-vs-concurrent.md` exists in your
tree and no file beginning `082-` exists in `handoff/done/`, this task is for
you. Otherwise stop reading and ignore this message.**

---

## 1. The question, and only this question

**Does dispatching the three historical roles concurrently make each of them
slower than dispatching them as one batch?**

Two measurements exist and they disagree by more than an order of magnitude on
one role:

| | `rth_dailies` | Shape | When |
|---|---|---|---|
| **Task 075** | **0.7–1.9s, all twelve runs** | five roles through one `asyncio.gather` | Sunday 2026-08-23, ~11:36 ET, **market closed** |
| **Task 080** | **21.11s QQQ · 3.94s AMZN** | three roles as independent concurrent workers | Sunday 2026-08-23, 14:53 ET, **market closed** |

**Both ran against live TWS with the market shut, so market hours are already
excluded as the difference** — that was checked against the artifacts, not
argued. **What remains untested is the dispatch shape**, plus cold-connection
and single-run variance.

**This is why the run can happen today.** A closed-market run is the directly
comparable one. Do not wait for a regular session.

---

## 2. The harness

**Standalone. Outside the terminal entirely** — no Textual, no TUI, no panel,
no worker threads, no `app.py`. **It does not have to live within the
terminal's constraints and should not try to.** A plain async script that opens
one IBKR connection and issues requests is the whole of it.

**It lives in `$env:TEMP`. It is not committed. It is scratch, exactly as
075's was.**

**`client_id=82`** — never `7`, `75`, `80`, `121` or `11`.

**Import the repo's own request-building code if that is the cheap path**, so
the requests are byte-identical in duration, bar size and `use_rth` to what the
terminal actually issues. **Reimplementing the request shapes by hand would
measure a different thing than the one in question.** Reading them and calling
them is fine; editing them is not.

---

## 3. What to run

**Three arms, same three roles each time** — `rth_dailies`, `sessions`,
`sector_sessions`, with the shapes the terminal uses today:

- **A — batched.** All three in one `asyncio.gather`. This is 075's shape.
- **B — concurrent.** Three independent dispatches, all in flight at once. This
  is 080's shape.
- **C — sequential.** One at a time, each awaited before the next starts.

**C is not a candidate design. It is the control** — without it, a difference
between A and B cannot be told apart from the connection simply being slow that
minute.

**Both symbols, QQQ and AMZN**, because 075 and 080 both used them and the two
behave very differently.

**Interleave the arms — A, B, C, A, B, C — never all of one arm and then all
of the next.** Ordering effects and connection warm-up would otherwise land
entirely on whichever arm went first, which is exactly how a real difference
and an artefact become indistinguishable.

**Six rounds if pacing allows, fewer if it does not.** IBKR's historical
request budget is finite and **`_PacingGuard` exists for a reason: if the guard
would be exceeded, stop and report the shorter run rather than working around
it.** A measurement that trips a pacing violation has changed the thing it was
measuring.

---

## 4. What to record

**Per request, per arm, per round, per symbol. Never averaged, never pooled.**
075's discipline: every run's raw timing appears individually.

- **Wall time for each of the three roles, separately.** The whole question is
  about one role's own duration, not the total.
- **Total wall time for the arm**, which is a different number and may move the
  opposite way — concurrency can make each request slower and the batch faster.
- **Bars received against bars requested**, per B-033.
- **Round index**, so a cold first round is visible rather than averaged away.
- **Whether `_PacingGuard` fired, and when.**
- **Any timeout**, with which role and at what bound.

**AMZN's `sessions` pull hit `request_timeout_s` at 60s during 080's run.
Expect it again. Record it as a data point. Do not change the bound** — it is a
threshold and every threshold is Christoph's, B-132.

---

## 5. What you may NOT do

**Do not edit any production file.** Not one. `touches:` is empty and it means
it.

**Do not change any request's duration, bar size or `use_rth`.**

**Do not change `request_timeout_s`, or any pacing setting, or any config.**

**Do not commit the harness.**

**Do not fix anything you find.** If arm A is plainly better, say so with the
numbers and stop. **A measure-only task that fixes something has made its own
measurement unrepeatable.**

---

## 6. Exit condition

**There are no Green, Refusal or UAT tests for this task, and that is
deliberate rather than an omission.** No production code changes, so there is
no behaviour to pin and nothing to see red first. **The exit condition is the
numbers in the done-note.**

`verify.ps1` still runs as the last action, because the tree is being reasoned
about even though it is not being changed. Do not paste or summarise it.

---

## 7. What the done-note must state

**Every round's raw numbers, individually.** Then, and separately from them:

**Does arm B make individual requests slower than arm A?** Yes, no, or the
data cannot tell — **and the third answer is a perfectly good one.** Six rounds
on one connection on one closed Sunday is not a distribution, and the note
should say what it cannot support as clearly as what it can.

**Whether the 21.11s figure reproduced at all.** If it never appears again,
that is the finding, and it points at variance rather than at design.

**Whether total time and per-request time move in the same direction.** If
concurrency makes each request slower but the whole set faster, the panel's
promise about *which rows land in two seconds* is wrong while the split itself
is still right — those are different conclusions with different fixes.

**Anything that contradicts §1 of this file.** Name the line.

**Anything that cannot proceed without a decision that is not yours goes into a
question file, and that session ends. It does not wait.**

---

## 8. The prompt

```
Do inbox 082
```
