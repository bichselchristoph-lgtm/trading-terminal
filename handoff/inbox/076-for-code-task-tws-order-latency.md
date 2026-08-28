---
task: 076
class: product
story: S031
epic: 7
repo: D:\Dev\tws_order
depends: none
touches: instrumentation only, in tws_order
---

# 076 — how long tws_order actually takes, and how much of it can be measured at all

**If `handoff/inbox/076-for-code-task-tws-order-latency.md` exists in your tree and `handoff/done/076-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. Where the number came from, and why it is not accepted

**A figure of about five seconds for tws_order to issue an order is in circulation and was used to argue an attach-time target.** **Nobody has produced the measurement.**

**Christoph ruled 2026-08-23: measure and triage, do not raise a row yet.** So this task produces a number and a breakdown. **It does not fix anything and it does not conclude anything the numbers do not support.**

**And the target it was used to justify is withdrawn.** Attach stays at *a second or two* — Christoph's own words in c015 §2, reconfirmed 2026-08-23. **One component's latency is not another component's budget.**

---

## 1. Runs in the other repo, alongside 075

**All work is in `D:\Dev\tws_order`. Nothing in `D:\Dev\momentum` changes** except the done-note.

**Disjoint from `075` by construction — different repo, different index.** If one session runs both, they can go as parallel subagents. **They still commit separately, to their own repos.**

---

## 2. The constraint that shapes this task

**Read-Only API is on in TWS, and it blocks order placement entirely — including `transmit=False` staging.** B-022, and Christoph ruled it stays on: it is a security control and only he removes it.

**So the segment from `placeOrder` to TWS acknowledging cannot be measured today, by anyone, without him turning it off.**

**Do not ask him to turn it off. Do not turn it off. Do not route around it.**

**Measure everything up to that boundary**, report the total, and **state plainly which segment remains unmeasured and what it would take to measure it.** That statement is a deliverable, not an apology — **if the answer turns out to be that most of the five seconds is already visible on this side of the boundary, the Read-Only question never needs asking.**

---

## 3. Part 0 — the breakdown

**Instrument, from process start to the last action before `placeOrder`:**

| Segment | What it covers |
|---|---|
| **process start → config loaded** | interpreter start, imports, config read |
| **connect** | `connectAsync` to TWS, including any handshake |
| **account snapshot** | whatever tws_order reads to size — NLV, cash, margin |
| **contract resolution** | `reqContractDetails` for the symbol |
| **sizing arithmetic** | the share-count computation itself |
| **everything else up to the boundary** | named individually if it is more than a few ms |
| **unmeasured** | `placeOrder` onward — blocked by Read-Only |

**Run it at least five times on a liquid symbol and report every run, not a mean.** **A mean hides the run that took twelve seconds, and that run is the finding.**

**Report a cold run and a warm run separately if the process is not started fresh each time.** Interpreter start and imports are real cost the first time and free afterwards, and conflating them produces a number that describes neither.

**Scratch in `$env:TEMP`, never the repo.**

---

## 4. The two things most worth knowing

**Is it dominated by one segment?** A single 4-second connect and a five-way split across 1 second each are the same total and completely different problems. **Say which it is.**

**Does it reconnect every invocation?** tws_order is a command-line tool, so each run may pay a full connection. **If connect is the bulk of it, the question is whether the connection can be held rather than whether it can be made faster** — and that is a design question for the design session, not a fix for this task.

---

## 5. Not in this task

- **Any optimisation.** §0.
- **Turning Read-Only off, or asking for it.** §2.
- **Raising a bug row.** Christoph ruled: measure and triage first.
- **`--risk-usd`.** That is `066`.
- **The attach path.** That is `075`.

---

## 6. Exit tests

**Green.**
- **Every run's timing in the done-note, individually, cold and warm distinguished.**
- **The per-segment breakdown, with the dominant segment named.**
- **The unmeasured segment stated explicitly**, with what it would take to measure it.
- **Whether a connection is established per invocation.**

**Refusal.**
- **TWS unreachable ⇒ stop and report that nothing was measured.** **No estimate, no extrapolation.** The circulating five-second figure is exactly what an unmeasured number becomes once it is repeated.
- **If instrumentation materially changes the timing, say so and report both.**

**UAT (Christoph).** None. **The numbers are the deliverable.**

---

## 7. The closing sequence, and it is not the usual one

**`tws_order` is in no Drive sync pair and has no export.**

1. **Commit and push in `D:\Dev\tws_order`** — instrumentation only if it is permanent and useful; scratch otherwise, and say which.
2. **From the `momentum` main checkout, run `verify.ps1`** — §10 captures tws_order's HEAD and raw suite output, which is how this becomes visible to the design session at all.
3. **Write the done-note in `momentum`'s `handoff/done/`**, naming the tws_order commit hash.
4. **`export-handoff.ps1`, then push `momentum`.**

---

**This note needs to be pasted to chat.**
