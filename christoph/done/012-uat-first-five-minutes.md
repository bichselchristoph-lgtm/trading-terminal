# 012 · UAT — the first five minutes of tape

**Path** `christoph/open/012-uat-first-five-minutes.md`
**State** OPEN · **Owner** Christoph only · **Blocks** 012's done-note
**Written** 2026-08-12 by the design session

> Fill in §2 before any count is computed or read. This file is the UAT artifact for 012; without it the exit table has a UAT with no file behind it.

---

## 1. Why the question changed

**Observation.** Claude Code asked for a pre-registered estimate of the *number of prints* in 09:30:00–09:35:00 ET. Christoph's answer: no basis for a point estimate in prints; he can read share volume for the first candle in TradingView, not print count.

**Observation.** The session total — **565,957 trades** — was already reported in chat before the estimate was requested.

**Inference (design session's, not established fact).** Two separate things went wrong with the original construction, and they pull in opposite directions:

1. **A point estimate in prints was unanswerable.** Print count is a quantity nobody has ever been shown a value for. Asking for one invites a fabricated number, and a fabricated pre-registration does not test intuition — it destroys the test while appearing to pass it. *"I cannot estimate this"* is a valid, recorded outcome, not a failure to complete UAT.
2. **The anchor is already set.** Because 565,957 is known, any magnitude estimate for five minutes is now contaminated. That door is closed and cannot be reopened.

**Recommendation, adopted below.** Re-ask the question as a **share of the session** rather than a count. That quantity is un-poisoned by the anchor, it is answerable from ordinary trading intuition, and the gap it measures — *how front-loaded is the tape?* — is the finding 012's UAT was actually after.

---

## 2. Pre-registration — fill in before reading anything computed

**A · What share of the session's 565,957 trades landed in 09:30:00–09:35:00 ET?**
Pick exactly one bracket:

- [x] under 1 %
- [ ] 1 – 3 %
- [ ] 3 – 6 %
- [ ] 6 – 12 %
- [] over 12 %

**B · Typical (median) print size in QQQ at the open, in shares.** One number:

`__Can't give a meaningul estimate other than looking it up which you can do better._____ shares`

**C · Optional, and read *before* filling A and B, or not at all.** TradingView consolidated volume of the 09:30 five-minute candle:

`__164.28k_____ shares`

**D · If any of the above cannot be answered, write "cannot estimate" and why.** That is a result, not a blank.
A free cross-check falls out. 164.28k shares over 09:30–09:35 on the capture's basis, divided by the capture's print count for the same window, gives an implied median print size — which is what §2B couldn't answer. If that lands near QQQ's known opening print size, both feeds are on the same basis. If it's off by a large factor, they aren't, and that's the finding. Worth adding to 012's done-note request, since Claude Code is computing that window anyway
---

Signed `___Chirstoh_________________` Date/time `___Aug 8, 2026 10:25 UTC+2_________________`

*Once signed, this file is closed to edits. Corrections go in the next document, not here.*

---

## 3. The basis trap in this UAT, stated before it bites

**C and the capture are not the same quantity.**

| | basis |
|---|---|
| TradingView 5-min volume | **consolidated tape** — every venue plus off-exchange prints |
| The capture | **single venue**, as configured for this run |

They share a name and answer different questions — the recurring pattern in §7 of the project instructions. Consequences, stated now so neither party rationalises them later:

- A print count derived as `C ÷ B` is a **consolidated** estimate. The capture produces a **venue** count. They may be compared only with both bases declared on the display.
- The capture's count is **expected to be the smaller number**, for structural reasons. If it comes out smaller, that is not evidence of loss.
- Off-exchange prints are the largest single gap between the two and are not a defect in the capture.

---

## 4. What follows, in order

**1 · This file, filled in and signed.** Christoph. Then point Claude Code at the path — it is not a new inbox task, it is the artifact 012 already owes.

**2 · Claude Code writes `handoff/done/012-*.md`.** It must carry, at minimum:
- the per-venue trade breakdown (this also discharges 008a's Test 5 at no extra cost)
- the 09:30–09:35 trade count **and** its share of 565,957, compared against §2A
- depth record accounting: 2,149,968 records, 1.83 GB, and what the retention position currently is
- what surprised the builder, and what it could not do

**3 · The paste.** 012 stays **RUNNING** until the done-note reaches the design session. Claude Code's own report of success is not confirmation. The design session then reads it and names every open issue → **REVIEWED**.

**4 · Two decisions 012 surfaced and does not answer.** Both are Christoph's; recommendations attached.

| Decision | Recommendation |
|---|---|
| **Retention for `records/tape/`** — 2 GB now sits under no policy. `.gitignore` protects the repo, not the disk. | Keep this session's raw JSONL **indefinitely and unconditionally**. It is not reproducible — that session cannot be re-recorded — and it is the substrate for Row 14. Write the retention rule for *future* captures **before** the multi-ticker run, not after it has produced 7 GB. |
| **Multi-ticker capture budget** — four tickers with L2 extrapolates to ≈ 7 GB/day from this run's observed rate. | Depth on **one** ticker, trades + quotes on the other three, for the first multi-ticker run. L2 across four names buys displayed-depth reliability (M2), which `BUILD-PLAN.md` already defers to slice 016. Paying 7 GB/day now for a component deferred by plan is premature cost — tenet 10. |

**5 · Handoff 013 — Row 14's order-flow basis.** The tape now exists, so the row that has blocked ratification on every card can finally be computed rather than declared unavailable. This is the next real task file. **It is not written yet, deliberately**: its construction depends on the per-venue breakdown from step 2, and writing it first would be guessing at the input.

**Unaffected and still open:** S009a (panel measurement defects) and the TotalView depth probe post TWS restart. Neither is blocked by any of the above; neither blocks it.

---

## 5. What is deliberately not in this file

No instruction to Claude Code. Nothing here is an inbox task. If Claude Code needs anything from this document, it is given the path and reads it.
