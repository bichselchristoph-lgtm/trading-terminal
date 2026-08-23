---
id: 080
title: Attach becomes two stages and the panel becomes live
type: task
class: product
story: S038
epic: 4
owner: claude-code
supersedes: 079
depends: none
touches: the attach path, the ATTACHED panel render, the record
mockup: ATTACHED mockup — the context block and its states v1.4
uat: c043
bugs:
  - id: B-134
    action: fix
  - id: B-114
    action: close
---

**Status** WRITTEN

# 080 — attach in two stages, and four rows that keep moving

**This supersedes 079, which must not be run.** 079 carried a Part 1 that task
078 has already delivered — B-130 and B-133, both fixed and pushed at 7e59fa2.
**079 was written before 078 ran and is wrong about the state of the tree, not
about the design.** Everything else in it is carried forward here unchanged.

**Read `handoff/done/078-surface-the-silent-degrade.md` first.** You are
building on top of it, not around it.

---

## 0. Is this task for you

**If `handoff/inbox/080-for-code-task-two-stage-attach.md` exists in your tree
and no file beginning `080-` exists in `handoff/done/`, this task is for you.
Otherwise stop reading and ignore this message.**

---

## 1. What is authoritative here

**The mockup, `ATTACHED mockup — the context block and its states v1.4`, in the
Trading Terminal Mockups folder.** Signed off by Christoph 2026-08-23. Its §0
is a twenty-line list of the rulings it carries. **Read it before writing
anything.**

The last screen mockup outranks any spec it contradicts on what renders — and
**ATTACHED-SPEC, UI-SPEC and RECORD-SPEC have not caught up yet.** Where they
disagree with the mockup, the mockup wins and **the disagreement is reported,
not resolved by you.**

**The mockup owns what renders. The spec owns meaning, bases, arithmetic and
refusal reasons.**

---

## 2. Part 0 — read and report before you change anything

**Three reads. Report each as what you read, not what you infer.**

1. **Does the current build refresh any panel value after attach?** `SPEC.md`
   specifies `keepUpToDate=True` as the default with a 120-second cadence as
   fallback. **That is what the spec says. Nobody has looked at the code.**
2. **What 078 left behind.** Its surfaced-degrade path and its `_PacingGuard`
   consultation both have to survive this task. **Name the tests that would go
   red if they did not.**
3. **Whether dispatching stage 1 and stage 2 in parallel costs materially more
   to build and to test than doing stage 1 first.** Christoph ruled parallel
   **conditional on the cost being roughly equal** — so this is your call, and
   the done-note states which you built and why.

**If any of these contradicts this task file, say so and name the line.** That
is worth more than the fix.

---

## 3. Part 1 — two stages

**Stage 1 is contract resolution plus the price stream.** Nothing else.
Measured floor: `reqContractDetails` ran 0.23–0.25s across all twelve runs of
task 075 with no meaningful variance.

**Stage 2 is the three historical requests.** Dispatched in parallel with stage
1 the moment the contract resolves — subject to Part 0 item 3.

**Stage 1 alone must be enough to submit an order. A stage-2 failure never
blocks the order path, for any reason.** This is the point of the whole task;
if anything you build makes the order path wait on history, it is wrong.

**Attaching a different symbol cancels every data stream of the current one.**

---

## 4. Part 2 — the rows

Per the mockup. **Five rows: symbol, `Last $`, `ADR% used`, `RVOL`, `VWAP`.**

- **`Last $` is the last trade, off the stream.** It is never `pending`.
- **`RVOL` renders `0.86x own · 1.4x vs XLC`** — own-history reading first,
  both bases labelled. **`avg` and `rel` are retired as labels.**
- **`cum` comes off the panel and stays in the system.** It is the numerator;
  deleting the computation deletes both readings with it. **The check is that
  the text is absent from what renders, not that the field is absent from the
  record** — the opposite of B-028's treatment of `ADR$`, deliberately.
- **Rows land independently as they arrive.** No shared paint. Measured:
  `ADR% used` and `VWAP` at 0.7–1.9s, `RVOL` at 15 to over 60s.
- **A pending row says `pending`. Every pending row says it. No summary count.**
- **One reading refusing never blanks the other** — B-117. With no sector
  mapping the row reads `0.86x own · unavailable (no sector mapping)`, never
  `1.0x`.

---

## 5. Part 3 — freshness

**The age renders always, in the header. Amber only past 20 seconds. A bare
header means the freshness age is not being computed** — that is the broken
state, it must be reachable and distinguishable, and it is B-134.

**Amber is the single exception to the no-verdict-colour rule** and it is
bounded positionally, not by intent: **a test asserts that amber renders only
where a freshness age has crossed its threshold, and nowhere else.** Write that
test. Without it the exception is a convention, and a convention is how a
one-off becomes a palette.

**Amber is per reading.** Two streams, two independent ages: a stale sector
stream ambers `1.4x vs XLC` alone and leaves `0.86x own` clean. **The header
carries the older of the two**, so it is never more optimistic than the worst
reading on the panel.

**20 seconds is unfitted** — one 32-minute session of one symbol, task 008b:
median 5.002s, max 14.477s. It renders as unfitted wherever provenance shows.

---

## 6. Part 4 — measurements

**Recorded, never rendered on this panel. HEALTH renders them.**

Per stream, symbol and sector **separately, never pooled**: update count,
last-update age, inter-update gap distribution. Per request: wall time, and
**bars received against bars requested** — B-033, where IBKR returned 204 for a
request of 205 with no error and no flag. Per stage: keypress to paint.

**The trap this exists for: a degraded supplier looks exactly like a quiet
market.** A sector stream at 40s because IBKR is throttling and one at 40s
because XLC is quiet produce identical numbers. **Cadence alone cannot separate
them.** Nothing you write may imply a certainty the measurement does not have.

---

## 7. What you may NOT do

**Do not touch `request_timeout_s`.** It is wrong — set to roughly the duration
it bounds, B-132 — but it is a threshold and every threshold is Christoph's.

**Do not change the size or shape of any historical request.** B-131 is not
this task's.

**Do not add anything to the ATTACHED panel.** Five rows and the header. The
measurements go to the record.

**Do not weaken or delete anything 078 built.** If a test of 078's has to
change shape to survive, **say so explicitly in the done-note and say why** —
silently rewriting a guard is how a fix becomes a regression nobody sees.

**Do not commit a measurement harness.** 075's harness is scratch and stays
scratch. **Any scratch this task needs lives in `$env:TEMP`, never in the
repo.**

---

## 8. Exit tests

**Green, Refusal, Colour and UAT. Every test seen red against real pre-fix code
before it is accepted green** — `git stash` the change, watch it fail, restore.

**Green.** Stage 1 renders a symbol and a price with the history still in
flight. Rows land independently. The freshness age advances. `RVOL` renders
both labelled readings in the ruled order. **Assert the specific wording, not
that a substring appears somewhere in the body** — a loose assertion passed on
both the right and the wrong output in 070, which is B-126.

**Refusal.** Four states, each distinguishable from the other three: `pending`,
`unavailable` with its reason, stale-amber, and the bare-header broken state.
**A stale value and a current one must not render alike, and a pending row and
a refused row must not render alike.**

**Colour.** A test that goes red when amber renders anywhere other than a
freshness age past its threshold.

**Fixture.** 078 found that the shared fixture always leaves PMH and PML
refused, which would have masked its own signal behind an ordinary refusal.
**Check that no test you write is reading a state the fixture guarantees rather
than a state your change produces.**

**UAT.** `christoph/open/043`. Not yours to perform or to mark.

---

## 9. What this reverses, and must be stated in the done-note

**B-095** closed by design that there is no per-cell pending state. **B-096**
ruled progressive fill out, not deferred. **S037 criterion 3** requires one
paint with no row filling independently. **All three are reversed by the signed
mockup**, on the measurement that progressive fill buys the difference between
two rows at two seconds and one row at fifteen to sixty — not the four seconds
B-096 assumed.

**Not reversed: old values still drop together the instant a new symbol is
attached.** That is B-116 and it is untouched. Rows filling in as they arrive
is a different thing from stale values lingering.

---

## 10. What the done-note must state

Which of Part 0's three reads matched this file and which did not. Which
dispatch shape you built and why. Which tests you saw red and against what.
Whether anything of 078's changed shape. **And the measured keypress-to-paint
for stage 1**, which is what closes B-114.

`verify.ps1` runs as the last action. Do not paste or summarise its output.

**Anything that cannot proceed without a decision that is not yours goes into a
question file, and that session ends. It does not wait.**

---

## 11. The prompt

```
Do inbox 080
```
