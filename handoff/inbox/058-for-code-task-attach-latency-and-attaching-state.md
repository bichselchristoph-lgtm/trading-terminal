---
task: 058
class: product
depends: none
touches: live/attach/attach.py, live/attach/ibkr.py, config/ibkr.yaml, live/render.py
---

# 058 — Attach latency, and the ATTACHING display state

**If `handoff/inbox/058-for-code-task-attach-latency-and-attaching-state.md` exists in your tree and `handoff/done/058-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. What this is, and what ruled it

`OBS-041` measured a live QQQ attach at **13.7 s wall clock, blocking the Textual UI thread for the whole of it**. `OBS-079` (your own investigation, 2026-08-22) established the cause: **up to seven sequential, blocking round-trips**, none of them concurrent, plus a per-connect account/order/position sync nobody needs.

**Christoph ruled the remedy on 2026-08-22.** It is a product decision under CLAUDE.md's product/admin line and it is now made:

> **Worker plus grouped concurrency. Atomic swap. No progressive fill.**

**The three things that ruling settles, and they are the point of this task:**

1. **The freeze and the latency are separate problems and both get fixed.** A Textual worker fixes the freeze and changes latency by zero. Concurrent dispatch fixes latency and changes the freeze by zero.
2. **There is no per-cell pending state.** A cell is *fetched* or it is *`unavailable (reason)`*. `BUILD-PLAN` slice 010 §7 already says this and §3 contradicts it with `fetching dailies…`. §7 wins. `fetching dailies…` is retired as a cell state.
3. **The attach state is one screen-level state, not twenty-three cell states.** Values land together or not at all.

**Explicitly not in scope, and refusing to build it is correct:** progressive fill — panels filling in as each request returns. It was `B-008`'s stated Expected and that expectation is **retired by this ruling**. It buys roughly four seconds and costs a new display state, a completion signal, and a weakened colour rule. Revisit only if the measured result in Part 5 still feels wrong in use.

**Derivation note, stated rather than hidden.** Per project instructions §1a a dev spec derives from a product spec, one way only. This file states the ruling **ahead of** `UI` and `ATTACHED` carrying it; those revisions land in the same session. **If they disagree with this file about product behaviour, they win and this file was wrong.**

---

## 1. Part 1 — collapse the redundant daily request, first

**Do this before Part 2, because it is what makes Part 2 safe.**

`daily_bars()` and `year_high_low()` both request **RTH daily bars** for the same contract at two different durations — 60D and 1Y — as two separate round trips. Nothing downstream needs the 60-session window specifically.

**Build:** one 1Y RTH daily fetch, sliced locally for the 60-session consumers. `_daily_cache`'s keying changes; make the key carry the window that was *served*, not the window that was *requested*, or a 60D lookup will miss against a 1Y entry.

**Why first.** It takes the underlying's historical request count from **five to four**, and four is what puts Part 2 under IBKR's pacing limit **by construction rather than by stagger**.

---

## 2. Part 2 — concurrent dispatch on the existing broker loop

**Build:** dispatch the independent historical requests via `asyncio.gather` over `reqHistoricalDataAsync` coroutines **on the existing `ibkr-broker` loop**. Not a second thread.

`live/tests/test_attach_is_reachable_by_key.py::test_the_thread_bridge_carries_a_real_async_client` pins `set(ib.threads) == {"ibkr-broker"}`. **Concurrent coroutines on one loop satisfy that** — it forbids a second OS thread, not concurrency within the one loop. **Do not weaken that test.**

**The pacing constraint, and it is real.** IBKR's own documented limit: **six or more historical requests for the same Contract, Exchange and Tick Type within two seconds is a violation.** This is a *separate* rule from the identical-request-within-15s cooldown `attach.py` already enforces as `COOLDOWN_S`.

After Part 1 the underlying carries **four** historical requests, so a single `gather` sits under the limit with one to spare. The sector ETF's two requests are **a different contract** and do not count against the underlying's window.

**Build the guard, do not rely on the arithmetic staying true.** A test asserts that **no more than five historical requests are issued for one `(contract, exchange, tickType)` inside any two-second window**, and it must be seen **red** — add a fifth-and-sixth request in a fixture, watch it fail, remove it, watch it pass. A guard nobody has seen fail is `B-035` again.

**Contract qualification stays sequential** — `reqContractDetails` must return before anything can be requested for the contract.

---

## 3. Part 3 — the ATTACHING state, and the atomic swap

**This is the product half and it is not optional.**

**On attach, in this order:**

1. **Every value dependent on the outgoing symbol is dropped immediately.** Not left on screen, not greyed. `ATTACHED` §6b.5 already rules that a detached symbol renders `STALE` — *"the old symbol's last values are still true; they are just no longer now."* **A value from the previous symbol sitting under a new symbol's header is the §7 archetype: a well-formed value answering a different question.**
2. **One screen-level `ATTACHING {SYMBOL}` state** renders while the requests are in flight. Dim-inverse badge, per `SPEC.md` §4 — **the system is refusing to claim anything yet, it is not failing.** Not amber: amber means *read this and decide*, and there is nothing to decide.
3. **When the gather completes, every value lands in one paint.**

**Partial failure must not look like success.** If some requests return and others do not, the completed screen carries per-row `unavailable (reason)` **and** a screen-level statement that the attach completed with refusals. **Four values and two refusals must not be indistinguishable from a complete attach of an illiquid name.** Tenet 3 — status inherits from the weakest — has to be *rendered*, not merely true.

**Every bar request asserts the count it received** (`B-033`). A short response is a refusal with its reason, never a silently short array.

**Do not touch the violet link colour in this task.** With an atomic swap the *every linked token has a partner on screen* invariant holds at all times, which is precisely why the swap was chosen. If you find a path where it does not hold, **write a question file rather than weakening the invariant.**

---

## 4. Part 4 — `StartupFetch(0)` on connect, gated on a version check

`ibkr_tape_tools`' `test_conn.py:19-43` connects with `StartupFetch(0)`, which tells `ib_async` to skip its default post-connect account/order/position sync. `momentum`'s `connect()` (`live/attach/ibkr.py:544-551`) pays for that sync unconditionally, on every attach, for a read-only market-data client that does not use it.

**Check the installed `ib_async` version exposes it before using it.** If it does not, **do not shim it** — record the version and move on. This part is worth a second or two, not a workaround.

---

## 5. Part 5 — measure it, and say where the scratch lives

**Report wall-clock attach time before and after**, same symbol, same time of day, three attaches each, on a **liquid large-cap** and on a **thin name**. Report the slowest single request too — after Part 2 that is the floor, and it is expected to be the 20-session minute-bar fetch (`config/ibkr.yaml` calls it *"by far the largest of the four"*).

**Scratch goes in `$env:TEMP`. Never the repo.**

**Do not quote a test count in the done-note.** State that `verify.ps1` ran, and when.

---

## 6. Exit tests

**Green.**
- Attach a liquid large-cap, a thin small-cap, and a name with no sector mapping. Every field is a number that can be checked by hand or a named refusal.
- The one-loop thread test still passes, unmodified.
- The pacing guard passes, **and was seen red first**.
- The collapsed daily fetch serves both the 60-session and 1Y consumers, and `_daily_cache` does not miss on the narrower window.

**Refusal.**
- **Kill the network mid-attach.** The screen renders a completed attach carrying named refusals — **never a half-filled screen presented as complete, and never a partial ADR.**
- **Attach the same symbol twice inside 15 s.** The cooldown renders with its remaining seconds. Never a silent drop.
- **A symbol with no sector mapping.** `RVOL_rel` refuses by name. Never `1.0`.
- **The UI stays responsive throughout every one of the above.** Key input is accepted while the attach is in flight.

**UAT — Christoph.**
- Attach three names in a row and **read the screen during the attach.** The question is not whether it is fast. It is whether, at any moment, **the screen could be mistaken for a completed attach when it is not** — and whether the previous symbol's numbers ever appear under the new symbol's header.
- Then attach with TWS disconnected and confirm the refusal says what is missing without needing the design session to explain it.

---

## 7. Not in this task

- **No progressive fill.** Ruled out above.
- **No RVOL basis work.** `B-049` and `B-050` are `051`'s and are not touched here.
- **No change to `COOLDOWN_S`.**
- **No sector-ETF deferral.** `OBS-079`'s secondary note — that a mapped sector doubles two requests and `RVOL_rel` does not gate the way ADR/ATR do — is a separate decision, not this task's.

---

## 8. Closing

**The closing sequence, from the main checkout: sync, work, verify, export, push.** `verify.ps1` runs as the last action and **is not pasted or summarised.**

Anything that cannot proceed without a decision that is not yours goes in `handoff/questions/`, and that session ends rather than waits.
