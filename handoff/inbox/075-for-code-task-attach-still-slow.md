---
task: 075
class: product
story: S037
epic: 4
depends: none
touches: the attach path, instrumentation only in Part 0
---

# 075 — a symbol switch takes over twenty seconds. Measure before touching anything

**If `handoff/inbox/075-for-code-task-attach-still-slow.md` exists in your tree and `handoff/done/075-*.md` does not, this task is for you. Otherwise stop reading and ignore this message.**

---

## 0. What was observed

**Christoph, 2026-08-23, on the running terminal: switching from QQQ to AMZN takes more than twenty seconds.**

**058's target was a second or two. The measured pre-058 figure was 13.7 seconds. So the switch is slower than the defect 058 was written to fix.**

**That is the whole observation. No cause is named here.**

---

## 1. The rule this task exists to obey

**058 optimised without measuring, because the measurement was blocked and honestly reported as owed — B-114, Part 5.** Five requests became four, seven sequential round trips became one gathered call, **and nobody has ever timed the result.**

**So this task measures and does not fix.** **Do not open the optimisation until Part 0 says where the time goes.** A second round of optimising an unmeasured path would be the same mistake with more confidence behind it.

**If the fix is obvious and one line, still do not apply it in this task.** Report it. **The measurement is the deliverable.**

---

## 2. Part 0 — instrument the attach path and time it live

**TWS must be up.** If it is not, **stop and say so** — B-114 has been owed for a day because a number was refused rather than fabricated, and that was the right call both times.

**Instrument, at minimum, from keypress to the single paint:**

| Segment | What it covers |
|---|---|
| **keypress → `_begin_attach` returns** | the synchronous clear and first render |
| **`_begin_attach` → worker starts** | Textual's worker dispatch |
| **contract resolution** | `reqContractDetails` for the new symbol |
| **`warm()` total** | the gathered call, wall clock |
| **each request inside the gather** | dispatch time and return time, per role |
| **any per-role fallback request** | §3 — these are the ones that should not be happening |
| **`_finish_attach` → paint** | the atomic swap and rerender |

**Run it at least three times per symbol, on QQQ and AMZN, and report every run rather than a mean.** **A mean over three runs hides the one that took forty seconds, and that one is the finding.**

**Time a first attach and a switch separately.** **13.7s was measured on a first attach. Nobody has ever timed a switch**, so it is not established that this is a regression rather than a case that was always slow.

**Scratch goes in `$env:TEMP`, never the repo.**

---

## 3. The first thing to look at, and it is readable in 058's own note

**`_context_block` calls `md.warm(c)` wrapped in `try/except: pass`.** Each per-role read then checks a `_warm` cache and **falls back to its own single live request if warming did not populate it.**

**So if `warm()` raises for any reason, every request runs sequentially again — the exact pre-058 behaviour — and nothing anywhere says so.** 058's note records that every existing fixture implements `warm()` as a no-op and **exercises the fallback path**, which means the fast path may have less test coverage than the slow one.

**Establish, by measurement rather than by reading:**

1. **Does `warm()` complete, or does it raise?** If it raises, what is the exception.
2. **Are the per-role fallback requests firing?** Count them on the wire.
3. **How many historical requests does one switch actually make?** 058 claims four for the underlying, six with a sector ETF. **Count them.**

**Whatever the timing turns out to be, the silent fallback is a defect on its own terms** — *fail loud, degrade graceful*, and this degrades silently. **A fast path that is dead leaves no trace at all.** Raise it as a row regardless of whether it explains the twenty seconds.

---

## 4. Other things worth timing, none of them accusations

- **The 1Y daily request.** Part 1 replaced a 60-day request with a one-year one and reported the count dropping five to four. **A count is not a duration** — one heavier request can cost more than two light ones.
- **The pacing guard.** It refuses at five requests per key in two seconds. **Report whether it fires, and whether a refusal is being retried rather than surfaced.**
- **The 15-second same-contract cooldown.** It should not apply to a different symbol. **Confirm it does not.**
- **The event loop created per worker thread.** `_attach_worker` calls `asyncio.new_event_loop()` on each run. **Report the cost; it is probably negligible and that is worth establishing rather than assuming.**
- **Whether the old subscription is released before the new one opens**, and what that costs. One symbol, one subscription is now the ruling.

---

## 5. Not in this task

- **Any optimisation.** §1.
- **Any change to what renders.** `071` owns the panel.
- **The LEVELS rail.** `074`.
- **Row descriptors.** `073`.
- **`B-076`**, the ATR multiplier. Christoph's.

---

## 6. Exit tests

**Green.**
- **Every run's timing is in the done-note, individually.** Not a mean.
- **First attach and switch are timed separately**, on two symbols.
- **The per-segment breakdown names where the time went.**
- **The request count on the wire is reported**, and whether any fallback fired.
- **`warm()`'s outcome is reported** — completed, or raised and with what.

**Refusal.**
- **TWS unreachable ⇒ stop, and report that nothing was measured.** **No estimate, no extrapolation from request counts.** A count collapsed from five to four says nothing about wall clock, and treating it as though it does is how twenty seconds went unnoticed for a day.
- **If the instrumentation itself changes the timing materially, say so** and report both.

**UAT (Christoph).** None. **The number is the deliverable, and he supplied the observation that started it.**

---

## 7. The closing sequence

Per `CLAUDE.md`, from the main checkout. One commit.

**The instrumentation may be committed if it is permanent and useful — a per-attach duration is a thing the terminal could reasonably always know.** **If it is scaffolding, it goes in `$env:TEMP` and does not enter the tree.** Say which and why.

**The done-note carries the numbers and no conclusions beyond what they support.**

---

**This note needs to be pasted to chat.**
