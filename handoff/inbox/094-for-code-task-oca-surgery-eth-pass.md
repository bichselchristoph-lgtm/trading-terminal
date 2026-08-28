---
task: 094
class: admin
unblocks: the unattended-exit order construction (product, unnumbered — TRADE spec change follows from 094+095 together)
depends: none
touches: nothing in the tree — measurements only, scratch in $env:TEMP
---

# 094 — for code — task — OCA group surgery, ETH pass

**If `handoff/inbox/094-*.md` exists in your tree and `handoff/done/094-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

**Session gate: this pass runs OUTSIDE regular trading hours.** If the current time in ET is within 09:30–16:00, stop and record that the gate failed — this pass is ETH-only; task 095 is the RTH pass. Record the ET time at start and whether it fell in pre-market (04:00–09:30) or after-hours (16:00–20:00).

## 093 is superseded

Task 093 was superseded before any run. **If a `093-*.md` file sits in `handoff/inbox/` with no done-note, do not execute it** — its full scope is split into 094 (this file, ETH) and 095 (RTH). State in this task's done-note whether a local 093 file was found, so the retraction is on the record rather than assumed.

## Why

SECURITY-BRIEF §5.3 concluded no IBKR construction keeps a protective stop and a working exit mutually exclusive unattended. External evidence says a **new** order can join a live order's `ocaGroup` at creation, and with **both legs GTC** nothing session-close-cancels — measured nowhere yet in this project. This pass additionally answers a question the RTH pass cannot: **whether group surgery — join, modify, cancel-cascade — works outside the session at all, and whether the cascade fires immediately or queues.** A queued cascade means a window with one leg dead and one alive: exactly the state the construction exists to prevent, and the unattended design depends on knowing whether that window exists.

## Hard constraints

- **Paper account only, verified by both signals before the first order**: account id prefix `DU`/`DF`/`DI` **and** port 7497. Either failing → stop, place nothing, record what was read.
- All orders **1 share**, on the test instrument named in task 062. Price references come from the **previous RTH close** (live NBBO may be absent in ETH — record which reference was actually used): sell stop at ~50% of it, sell limits at ~200% of it. Intent is that nothing fills; if something fills, flatten and record it as an observation.
- **End state: flat, zero open orders**, confirmed by a fresh read after cleanup, not by the absence of an error.
- Scratch in `$env:TEMP`, never the repo.
- Observations verbatim, with **ET timestamps on every order-state transition** — immediate-vs-queued is the finding, so timing is data. Inference labelled as inference. A read returning nothing is recorded as exactly that.

## Measurements

**M1-E — sole-member group accepted in ETH.** GTC sell STP, explicit `ocaGroup` `M094-A`, `ocaType=3`. Observe: accepted/rejected/queued, order status received, `ocaGroup` echoed on openOrder.

**M2-E — join-later and cascade timing.** With M1-E working, place a new GTC sell LMT, same group `M094-A`, `ocaType=3`. Observe both orders' `ocaGroup` fields. Then cancel one leg and observe the sibling **with timestamps**: does its cancel arrive within seconds, or does anything suggest it waits for the session? Leave enough observation time (≥60s) before concluding, and record how long was waited.

**M3-E — modify outside RTH.** Fresh group `M094-B`, same two shapes. Modify the limit leg's price (still non-marketable). Observe: modification accepted or queued; stop leg untouched; both orders still carry `M094-B`. Clean up by cancel; confirm the cascade removed both; confirm zero open orders.

**M4 — GTC auto-expiry visibility** (session-independent; lives in this pass so 095 stays lean). IBKR auto-cancels GTC orders at the end of the calendar quarter following placement, on corporate actions, and after 90 days without login. Determine what, if anything, `ib_async` exposes on a working GTC order that carries or implies that expiry date — openOrder fields, order state, anything on the wire. If nothing carries it, the absence is the finding. Do not infer a field that was not read.

## Exit

- Done-note carries M1-E–M4 observations verbatim with ET timestamps, observation and inference separated, plus the ET start time, the session it fell in, and whether a local 093 file was found and skipped.
- Done-note states the end-state check: flat, zero open orders, by fresh read.
- `verify.ps1` ran; the note states that it ran and when, and quotes no test count.
- No spec is edited by this task — the spec change is the design session's, after 094 and 095 are both read.
