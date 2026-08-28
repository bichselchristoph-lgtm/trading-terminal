---
task: 095
class: admin
unblocks: the unattended-exit order construction and the precaution-reject display state (product, unnumbered — TRADE spec change follows from 094+095 together)
depends: none for M1-R–M3-R; M5 additionally requires c050 Part B confirmed on the paper TWS — if unconfirmed, skip M5 and say so
touches: nothing in the tree — measurements only, scratch in $env:TEMP
---

# 095 — for code — task — OCA group surgery and the TWS ceiling, RTH pass

**If `handoff/inbox/095-*.md` exists in your tree and `handoff/done/095-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

**Session gate: this pass runs INSIDE regular trading hours.** If the current time in ET is not within 09:30–16:00 on a trading day, stop and record that the gate failed — this pass is RTH-only; task 094 is the ETH pass. Record the ET time at start.

## Context

Task 093 was superseded before any run and split into 094 (ETH) and 095 (this file). The two passes measure the same group mechanics in both sessions so the unattended-exit spec can state where repairs are possible, not assume it. If a `093-*.md` sits in `handoff/inbox/` with no done-note, do not execute it.

## Hard constraints

- **Paper account only, verified by both signals before the first order**: account id prefix `DU`/`DF`/`DI` **and** port 7497. Either failing → stop, place nothing, record what was read.
- All orders **1 share**, on the test instrument named in task 062, priced off live NBBO not to execute: sell stop at ~50% of market, sell limits at ~200% of market. If something fills anyway, flatten and record it as an observation.
- **End state: flat, zero open orders**, confirmed by a fresh read after cleanup, not by the absence of an error.
- Scratch in `$env:TEMP`, never the repo.
- Observations verbatim with ET timestamps; inference labelled as inference; a read returning nothing recorded as exactly that.

## Measurements

**M1-R — sole-member group.** GTC sell STP, explicit `ocaGroup` `M095-A`, `ocaType=3`. Observe: accepted or rejected; `ocaGroup` echoed on openOrder.

**M2-R — join-later, proven by cascade.** With M1-R working, place a new GTC sell LMT, same group `M095-A`, `ocaType=3`. Observe both orders' `ocaGroup` fields. Cancel one leg; observe the sibling with timestamps. The cascade (§5.1) is the proof of linkage — no fill needed.

**M3-R — modify does not cascade.** Fresh group `M095-B`, same two shapes. Modify the limit leg's price (still non-marketable). Observe: stop leg survives; group intact; both orders still carry `M095-B`. Clean up by cancel; confirm zero open orders.

**M5 — the ceiling rejects (only if c050 Part B is confirmed on the paper TWS; otherwise skip and state the skip).** With "Bypass Order Precautions for API Orders" unchecked and Stocks precautionary limits set, place one order deliberately exceeding the Total Value Limit (still non-marketable). Observe verbatim: error code and text (documentation suggests error 451 — hypothesis, not fact), and whether the order is rejected outright or held untransmitted. Additionally observe whether the ~200% sell limits used in M2-R/M3-R drew a percentage-constraint reaction — that collision is data for the exit-order shapes. Clean up anything left working.

## Exit

- Done-note carries M1-R–M3-R and M5 observations verbatim, observation and inference separated, M5's skip stated plainly if skipped.
- Done-note states the end-state check: flat, zero open orders, by fresh read.
- `verify.ps1` ran; the note states that it ran and when, and quotes no test count.
- No spec is edited by this task — the spec change is the design session's, after 094 and 095 are both read.
