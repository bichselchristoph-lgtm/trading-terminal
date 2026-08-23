---
id: 078
title: A failed warm() degrades to the sequential path in silence, and the fallback path is unguarded
type: task
class: product
story: S037
epic: 4
owner: claude-code
depends: none
touches: the attach path — the warm() call site and the per-role fallback reads
uat: c041
bugs:
  - id: B-130
    action: fix
  - id: B-133
    action: fix
---

**Status** WRITTEN

# 078 — surface the degrade, and guard the fallback

**This task does not make the attach faster. It makes the slow case legible.**
Say so in the done-note rather than letting a reader infer otherwise.

---

## 0. Is this task for you

**If `handoff/inbox/078-for-code-task-surface-the-silent-degrade.md` exists in
your tree and no file beginning `078-` exists in `handoff/done/`, this task is
for you. Otherwise stop reading and ignore this message.**

---

## 1. What was measured, not inferred

Task 075 ran twelve real attaches against live TWS and instrumented the wire.
**Every statement in this section is from that run, not from reading code.**

- `md.warm(c)` in `_context_block` is wrapped in a bare `try/except: pass`.
- **On 3 of the 6 AMZN-involving attaches it raised** `TimeoutError: no answer
  in 60s (request_timeout_s)`.
- On each of those three, **all five per-role reads then fell back to their own
  individual sequential live request** via `IBKRMarketData._bars` — the
  pre-058 shape, restored at runtime.
- The fallback added **70 to 83 seconds on top of the 60 already spent.** Total
  run times on those three: 143.2s, 143.4s, 130.6s.
- **Nothing on screen and nothing in any log said the fast path had failed.**
  The panel simply took longer.
- **`_bars` never consults `_PacingGuard`.** Confirmed by direct
  instrumentation. No pacing violation fired in the twelve runs, so this is
  latent rather than observed — record it that way.

Read `handoff/done/075-attach-still-slow-measured.md` before changing anything.
**Read the call sites yourself. Do not take this section as a substitute for
the read** — the design session has been wrong about a cause it inferred
rather than read, twice, and both times the note sounded exactly this certain.

---

## 2. What to change

**Two defects. B-130 and B-133.**

**B-130 — the failure must be surfaced.** A `warm()` that raises is a degraded
attach, and a degraded attach is a display state, not an error to swallow.
*Refusal is a display state you design, not an error you handle.*

**B-133 — every historical request passes the same guard, whichever path
issues it.** Whether that means routing the fallback through the guarded entry
or removing the fallback in favour of a guarded retry is yours: read both paths
and choose. **If removing it changes what renders, that is not yours — write a
question file instead.**

---

## 3. What you may NOT do, and why each one is here

**Do not invent a screen state.** `AttachResult.partial` already carries a
degraded-gather shape and the panel already renders `N of M rows unavailable`.
**Reuse that vocabulary.** No new token, no new colour, no new row.

The reason is positional rather than stylistic: **the most recent screen mockup
outranks every document (B-122)**, and there is no mockup for a pending or
degraded attach state. A state invented here would become the specification by
default. That has already happened once — a truncated row on a screenshot was
drawn into a mockup and the mockup then outranked the spec that had it right
(B-127). **If the existing vocabulary genuinely cannot express this, that is a
question file, not a judgement call.**

**Do not touch `request_timeout_s`.** It is wrong — it is set to roughly the
duration of the thing it bounds, which is B-132 — but it is a threshold, and
every threshold is Christoph's. **Raising it would make B-130 rarer without
making it visible, which is the failure this task exists to stop.**

**Do not touch the size or shape of any historical request.** The 20-session
1-minute pull is the whole attach cost (B-131) and reducing it is not this
task's. Not this task's.

**Do not restructure the attach into stages.** That is S038 and it is blocked
on a ruling and a mockup that do not exist yet.

**Do not commit any measurement harness.** 075's harness is scratch and stays
scratch. **Any scratch this task needs lives in `$env:TEMP`, never in the
repo.**

---

## 4. Exit tests

**Three, and the refusal test is not optional. Every one of them is seen red
against real pre-fix code before it is accepted green** — `git stash` the fix,
watch it fail, restore. A test that has only ever been green has not been
tested.

**Green.** Force `warm()` to raise and assert the attach reports the degraded
outcome in the record and on the rendered panel. **Assert the specific
wording, not that a substring appears somewhere in the body** — a loose
assertion passed on both the right output and the wrong one in 070, which is
B-126.

**Refusal.** `warm()` raises *and* a fallback request also fails. The affected
rows refuse with their reason, and **the refusal is distinguishable from a
successful read that returned nothing.** Those two states looking alike is the
defect one level up from the one being fixed.

**Guard.** A test that goes red when a historical request reaches the wire
without consulting `_PacingGuard`. **Assert the consultation, not the
absence of a violation** — no violation fired across twelve live runs with the
guard entirely absent, so absence of a violation proves nothing.

**UAT.** `christoph/open/041` — live, during market hours. Not yours to
perform and not yours to mark passed.

---

## 5. What the done-note must state

The two defects, what you read at each call site, which tests you saw red and
against what, and **the fact that attach duration is unchanged.**

If anything in section 1 does not match what you read in the tree, **say so
plainly and name which line was wrong.** That is more valuable than the fix.

`verify.ps1` runs as the last action. Do not paste or summarise its output.

**Anything that cannot proceed without a decision that is not yours goes into a
question file, and that session ends. It does not wait.**

---

## 6. The prompt

```
Do inbox 078
```
