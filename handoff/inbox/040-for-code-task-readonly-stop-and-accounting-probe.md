---
id: 040
title: Can the terminal see a stop moved by hand in TWS
type: task
class: product
version: 1.1
unblocks: 039 — the R accounting cannot be trusted while a stop moved outside the terminal is invisible, and the dollar safety net is currently the only thing watching for it
owner: claude-code
tree: D:\Dev\momentum
---

**Status** WRITTEN

# 040 — read-only probe: stop orders, executions, and commissions

**Type: task. Class: product** — it determines whether a number Christoph sizes from is complete.

**This task places no orders. It reads.** Nothing it writes touches the broker.

**Christoph must be present** — three steps require him to act in TWS. Part 4 lists them. **Ask
before each one and wait.** He has said he is available Friday; **do not start Part 4 without him.**

**v1.1 adds the `**Status**` line above. No other change.**

> **Read this cold. The session that wrote it cannot answer questions.**

---

## Addressing

**If `handoff/inbox/040-for-code-task-readonly-stop-and-accounting-probe.md` exists in your tree and
`handoff/done/040-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

**Work in a worktree.** Remove it when the task completes — `OBS-046`. Do not remove another
session's.

---

## Why

**`039` defines every closed trade by `R_closed = (avg_exit − avg_fill) ÷ (avg_fill −
stop_at_entry)`, net of commissions.** Two inputs to that are currently assumed rather than
established:

1. **A stop Christoph moves by hand in TWS.** If the terminal cannot see it, a stop widened 10×
   produces a 10R loss the R counter records as 1R. The dollar safety net catches it *afterwards*,
   which is a backstop, not accounting.
2. **Commissions.** Classification is net. If commission reports do not arrive, the
   winner/break-even boundary moves and nobody finds out.

**IBKR's TWS API Settings dialog exposes a `Master API client ID`.** Its tooltip states that the
master client receives all orders and trades **including those placed by other API clients**, and
that **only that client receives commission reports for all executions**. It contrasts this with
`clientId 0`, which *"receives orders placed through the Trader Workstation GUI but not orders
placed by other API clients."*

**What the tooltip does not say is whether the master client ALSO receives GUI orders.** That is the
whole question. **Establish it by observation. Do not reason it out.**

---

## Standing constraints

- **Read-only API is currently enabled in TWS and stays enabled.** Every call in this task is a
  read. **If any step appears to require order placement, stop and report.**
- **Only `tws_order` places orders**, and this is not `tws_order`.
- **`ib_async` only. Never `ib_insync`.**
- **Do not change TWS settings yourself.** Christoph changes them; you observe.
- **Only one client may hold the master ID.** If `tws_order` or another session holds it, say so and
  stop.

---

## Part 1 — record the present state before changing anything

**The present state is the finding.**

Report, from the code as it stands:

1. **What client id does the terminal connect with?** The literal value and where it comes from.
2. **Does it call `reqAutoOpenOrders(True)`?** `SPEC.md` §7a specifies `clientId 0` with
   `reqAutoOpenOrders(True)`. **Report whether that is what the code does** — do not assume the spec
   describes the implementation.
3. **Does anything subscribe to `execDetails`, `commissionReport`, `openOrder` or `orderStatus`
   today?** Name the call sites, or state that there are none.
4. **Is any of it reachable from the running app**, or does it exist only as a library? *(Four
   instances of a green suite over an unreachable feature are already recorded.)*

---

## Part 2 — the baseline probe, current settings

**Write a standalone read-only script** — `tools/probe_orders.py`, outside the app — that:

- connects with the terminal's current client id
- calls `reqAutoOpenOrders(True)`
- subscribes to `openOrder`, `orderStatus`, `execDetails`, `commissionReport`
- calls `reqOpenOrders()` and `reqExecutions()` once at start
- **logs every callback with a wall-clock timestamp**, verbatim, to `probe-output.txt`

**It runs for a bounded time and exits.** No panels, no rendering, no state.

**Run it, with Christoph doing nothing.** Report what arrives — existing open orders, existing
executions, or silence. **Silence here is a result, not a failure.**

---

## Part 3 — the master ID

**Ask Christoph to set `Master API client ID` in TWS** (Configuration → API → Settings) to a value
you name, and restart TWS if it requires one.

**Then run the same probe connecting with that id**, unchanged in every other respect.

**Compare against Part 2 and report the difference.**

---

## Part 4 — the three things only Christoph can do

**Ask before each. Wait. Do not batch them.**

**4a — a stop moved in the GUI.** Christoph has an open position with a stop. He moves it in TWS by
hand.
> **The question: does `openOrder` or `orderStatus` fire, and does it carry the new stop price?**

**If yes, the largest hole in the R accounting is closable and `039`'s dollar safety net stops being
the only thing watching it. If no, it is a permanent blind spot and must be recorded as one.**

**4b — an execution.** If Christoph takes or exits a trade during the session, capture `execDetails`
and `commissionReport` for it.
> **The questions: does a commission report arrive at all; does it carry `commission`, `realizedPNL`,
> and the `execId` that ties it to the fill; how long after the execution.**

**If Christoph does not trade, say so and mark 4b unanswered. Do not simulate it.**

**4c — a cancelled order.** Christoph cancels an order in the GUI.
> **The question: does the terminal see the cancellation, or does it keep a stop it believes is
> live?** *A stop the terminal thinks exists and does not is worse than no stop at all — it makes
> `stop_at_entry` describe a protection that is not there.*

---

## Part 5 — the two accounting questions

From what Parts 2–4 produced, answer:

**5a — Can `stop_at_entry` be captured automatically?** `039` requires it as an immutable field. If
the terminal sees the stop leg at the moment the bracket is placed, it can. **If not, say plainly
that it must be recorded by the terminal at stage time from its own selection**, which is weaker,
because a stop Christoph places directly in TWS then has no entry value at all.

**5b — Is `commissions: net` achievable?** If commission reports do not arrive, `039`'s
classification is defined against data the terminal does not have. **Say so.** Do not propose a
fallback in this task — that is a decision, and decisions are Christoph's.

---

## Part 6 — one thing worth building if it is trivial

**`CONNECTION` currently renders `read-only` because that is how it was configured.** It should
render the **actual** state, read from the connection.

**Read-only will be switched off when order staging lands** (slice 017), and a session where the box
was not re-checked would otherwise surprise Christoph at `ctrl+enter` rather than on the panel.

**If this is more than a small change, report what it needs and build nothing.**

---

## Not in scope

**No order placement, ever.** No changes to `tws_order`. No panel work beyond Part 6. No trade record
fields — that is `039`. No changes to TWS settings by you.

---

## Last action

**Run `verify.ps1`.** Do not paste or summarise. Do not quote a test count.
**Then run the export**, from the main checkout — not from a worktree (`OBS-045`).

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | `verify.ps1` ran. The probe is a tool, not a library — **assert it is not imported by the app** |
| **Refusal** | Claude Code | With TWS unreachable, the probe reports `unavailable (reason)` and exits non-zero. **It never reports "no orders found"** — absence of connection and absence of orders must not read alike |
| **UAT** | Christoph | `c020` — perform 4a, 4b and 4c, and confirm the probe log shows what he did |

---

## Report

In `handoff/done/040-readonly-stop-and-accounting-probe.md`:

1. **Part 1's four answers**, before any change.
2. Baseline probe output — what arrived, what did not.
3. Master-ID probe output, and the difference.
4. **4a: does a GUI stop move reach the API? Quote the callback.**
5. **4b: does a commission report arrive, with what fields, and how late?** Or that it was unanswered.
6. **4c: is a GUI cancellation visible?**
7. **5a and 5b, answered plainly.**
8. Whether Part 6 was built or deferred.
9. **What you could not do**, and why. Empty is suspicious.

**Do not recommend a design in this report.** State what the broker does. **The decisions that follow
are Christoph's.**
