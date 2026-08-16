---
id: 051
title: The basis audit — what every indicator declares, and what the code actually requests
type: task
class: product
version: 1.0
originates: ATTACHED-SPEC §3 · LEVELS-SPEC §1 · ARCHITECTURE-SPEC §3
closes: B-013 · B-049 · contributes to B-033
depends: none
unblocks: the ATR stop floor in TRADE-SPEC §6, which currently cannot be trusted
owner: claude-code
tree: D:\Dev\momentum
---

**Status** WRITTEN

# 051 — the basis audit

**Type: task. Class: product.** No panel work. **This decides whether numbers currently on screen are
computing what they claim to compute.**

> **Read this cold. The session that wrote it cannot answer questions.**

---

## Addressing

**If `handoff/inbox/051-for-code-task-the-basis-audit.md` exists in your tree and
`handoff/done/051-*.md` does not, this task is for you. Otherwise stop reading and ignore this
message.**

**Work in a worktree.** Remove it when the task completes. **Scratch in `$env:TEMP`, never the repo.**

---

## Why this exists

**Two documents state opposite bases for the same quantity.**

| Source | Says |
|---|---|
| Project instructions §8 | **`ATR14` is ETH** |
| `ATTACHED-SPEC` §3 | **`atr_d14` is daily, RTH-only unchangeably, and is what every mention of `ATR₁₄` means.** `atr_i14` is ETH and **is consumed by nothing** |

**Both cannot be true, and the ATR stop floor consumes it.**

**This may not be a documentation slip.** The 3× ATR floor prices a $46.83 stop — **4.0 ADR, ten
shares on a liquid name** — and that was attributed to "an ETH ATR" while the floor was calibrated
against RTH numbers. **If the code is fetching the intraday ETH variant where the spec means the daily
RTH one, the contradiction is the cause and not a description of it.**

**A rule that produces a ten-share position on a liquid name is a defect wearing a rule's clothes.**

---

## The principle this task applies

**The read is the implementation.**

**A basis declared in a spec, a docstring or a config comment is a claim. The basis that exists is the
one in the actual request.** A fixture cannot catch a mismatch between them, because a fixture is
internally consistent by construction — **it will happily produce a well-formed value that answers a
different question.**

**So this task does not read intentions. It reads call sites.**

---

## Part 1 — the audit table

**For every indicator the terminal computes, produce one row:**

| column | meaning |
|---|---|
| indicator | the name as it appears in code |
| **declared basis** | what the spec or config says it is |
| **requested basis** | **what the actual API call passes**, at the call site |
| `useRTH` | the literal value passed, or **ABSENT** |
| bar size / duration | as passed |
| **agree?** | yes / **no** / **undeclared** |

**Cover at minimum:** `ADR%` · `atr_d14` · `atr_i14` · session VWAP · `RVOL(t)` and its denominator ·
`RVOL_OR` · `RVOL_rel` · cumulative volume · every level in the twenty · the opening-range windows ·
the SMA and EMA series.

**`ABSENT` is the finding, not a blank.** `reqHistoricalData` and `reqHistoricalTicks` both default to
`useRTH=True` and **return RTH-only data silently — no error, just a different number.** A call site
that omits the parameter has chosen `True` without saying so.

**`undeclared` is also a finding.** An indicator whose basis is stated nowhere is not passing; it is
unexamined.

---

## Part 2 — the two known mismatches

**Confirm or refute each by measurement, not by argument.**

### 2a — the ATR the stop floor consumes (B-013)

**Trace it from the floor back to the fetch.** Report which variant it receives, on which basis, and
whether the name it is called by matches the name the spec uses.

**If the floor consumes an ETH ATR, that is the finding and it explains the ten-share stop.**
**If it consumes the daily RTH one, the floor is miscalibrated for a different reason and the project
instructions carry a wrong sentence.** Both are worth knowing and they are not the same repair.

### 2b — the RVOL numerator and denominator (B-049)

**The logged defect is pre-market entering the numerator and not the denominator**, which reads about
3× on an ordinary morning. **Confirm whether both sides are fetched on the same basis today.**

**Report the measured ratio on a real pre-market session**, so the size of the error is a number rather
than an adjective.

---

## Part 3 — the guards

**Three tests, each seen red before it is accepted green.**

1. **No fetch call site omits `useRTH`.** A scan, not a unit test — <b>the defect is the absence of an
   argument, so the test must look at call sites rather than at behaviour.</b>
2. **`atr_i14` has no consumer.** The spec says it is consumed by nothing; **a test asserts that,
   because "consumed by nothing" is exactly the kind of claim that silently stops being true.**
3. **Every bar request asserts the count it received.** IBKR returned 204 bars for a request of 205
   with no error and no flag — **a degraded supplier looks exactly like a quiet market** (B-033).

---

## What this task does NOT do

**Do not change a basis.** **Which basis is correct is a product decision and it is Christoph's.** This
task establishes what is actually happening; the ruling follows.

**Do not refit the ATR floor.** That needs the audit's answer first, and it is TRADE-SPEC §13 item 3.

**Do not touch the project instructions.** If they carry the wrong sentence, report it and it is
corrected at source.

---

## Constraints

**Pacing, budgets and the daily Gateway restart are ARCHITECTURE-SPEC §4** and are not restated here.
**The one that bites this task: the three budgets are separate and must not be conflated**, and a
pacing rejection looks like a slow request.

---

## Last action

**Run `verify.ps1`.** Do not paste or summarise. Do not quote a test count.
**Then run the export, from the main checkout** — not from a worktree.

---

## Exit tests

| test | who | what |
|---|---|---|
| **Green** | Claude Code | All three Part 3 guards **seen red first**, then green |
| **Refusal** | Claude Code | **An indicator whose basis cannot be determined renders `undeclared` in the table rather than being omitted.** An omitted row and a row with nothing to report must not look alike |
| **UAT** | Christoph | `c029` — read the audit table and rule on any row where declared and requested disagree |

---

## Report

1. **The full audit table.** Every indicator, every column, including `ABSENT` and `undeclared`.
2. **Which ATR the stop floor consumes**, traced from the floor to the fetch.
3. **The measured RVOL ratio on a real pre-market session.**
4. **Every row where declared and requested disagree**, listed separately so none is lost in the table.
5. **Whether the project instructions' §8 sentence is correct.**
6. **Bug rows to update:** B-013, B-049, and B-033 if the count assertion landed. **Report the row ids
   and the status each should move to — do not assume the sheet was updated.**
7. **What you could not do**, and why. Empty is suspicious.

---

## The question this task hands back to Christoph

**Where declared and requested disagree, which one is right?**

**A basis is a fact about what an indicator is, not a setting** — so the answer is not "make the config
match the code" or the reverse. **It is a ruling about what the number is supposed to mean, and it is
his.**
