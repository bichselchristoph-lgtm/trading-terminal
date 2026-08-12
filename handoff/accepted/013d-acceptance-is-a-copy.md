---
id: 013d
title: Correct §2e — acceptance is a copy, not an authored document
status: DONE
owner: claude-code
ran: 2026-08-11
tree: D:\Dev\momentum
---

# 013d — acceptance is a copy

**Status** DONE

```
BEFORE : 99 passed, 0 failed
AFTER  : 99 passed, 0 failed
```

One amendment, one file, no test added and none broken. **All four accepted files are
byte-identical to their done-note counterparts.**

---

## §2e as it now reads

> **`handoff/accepted/NNN-*.md`** — the record that both parties agreed nothing further is
> owed: no open follow-ups, no unresolved issues.
>
> **Acceptance is a COPY, not an authored document.**
>
> - When both parties agree, **`handoff/done/NNN-*.md` is copied to
>   `handoff/accepted/NNN-*.md`**, byte-identical. **The presence of the copy is the
>   acceptance.** Nothing is authored.
> - **Christoph performs the copy.** He is the only party who can, and it requires nothing
>   from the design session beyond agreement.
> - **The five states do not change.** `accepted/` is what `DONE` leaves on disk. Until this
>   existed `DONE` lived only in conversation, which is how four done-notes went unreceived on
>   2026-08-11.
> - **Copy-and-keep applies here too.** Nothing moves. **Three copies coexist**: the task
>   file, the done-note, and the acceptance record.
> - **Claude Code never writes to `handoff/accepted/`**, and never infers acceptance from a
>   note it wrote itself.
> - **New work discovered during acceptance does not live here.** It goes into the task file
>   for the work it implies. **`handoff/accepted/` records that agreement happened; it is not
>   a place where anything is first written down.**
>
> Nothing is backfilled into it. No past task has an acceptance record, and inventing one
> would assert an agreement that was never made.
>
> **Why this replaced an authored record, on the day it was adopted.** The first version of
> this rule said the design session authors the acceptance record and Christoph saves it. It
> was exercised once — on `013`, `013a`, `013b` and `013c`, immediately after adoption — and
> failed twice:
>
> 1. **It makes closure depend on a party that cannot see the repo.** A task could not be
>    accepted unless the design session was available to write a file about it. A copy needs
>    nobody.
> 2. **Nobody reads `handoff/accepted/`.** An authored record puts new information somewhere
>    it will never be opened — the same failure this project names most often, *a correct
>    warning sitting in a file nobody was instructed to read.* Anything genuinely new belongs
>    in the task file for the work it implies, where someone must read it to do the job.
>
> The design session authored four acceptance records; Christoph discarded them and copied
> the four done-notes instead. **The copy rule is what the four files in `handoff/accepted/`
> actually are** — verified byte-identical to their `handoff/done/` counterparts on
> 2026-08-11.

**Edited in place.** The file was not re-authored and no replacement was accepted from outside
the tree. The three bullets that were already correct — the five states unchanged,
copy-and-keep, and Claude Code never writing there — carried across untouched; only the
authoring bullet was replaced, and the copy mechanics and the reason were added around it.

---

## Byte-identity — the Refusal test

All four, sha256 of accepted versus done:

| file | accepted | done | identical |
|---|---|---|---|
| `013-adopt-handoff-protocol.md` | `9e43e5a955…` | `9e43e5a955…` | **yes** |
| `013a-handoff-tree-inventory.md` | `e78607a71a…` | `e78607a71a…` | **yes** |
| `013b-state-reconciliation.md` | `542831383e…` | `542831383e…` | **yes** |
| `013c-resolution-d-protocol-and-trees.md` | `2b93d3536f…` | `2b93d3536f…` | **yes** |

**ALL FOUR BYTE-IDENTICAL.** The copy rule is not merely now written down — it is what
already happened, and the hashes prove it rather than the prose asserting it.

Re-checked after the amendment landed: still identical, and `git status handoff/accepted/`
shows four `A` entries and **no `M`** — nothing in that folder was altered.

---

## Divergences from what was on disk

**Two, both premise drift rather than defects.**

1. **The Green exit test expects "unchanged from `013c`'s 71 passed, 0 failed".** The tree is
   at **99 passed, 0 failed**. `S009` ran between `013c` and this task and added 28 tests —
   the TUI frame, the refusal grammar and the snapshot suite. The *spirit* of the test is met
   exactly: **99 before, 99 after, nothing added, nothing broken.** The figure is simply from
   before the slice landed.

2. **`handoff/accepted/` was empty when `013c` finished, and its four files arrived
   afterwards.** `013c` created the tree with a `.gitkeep` and explicitly backfilled nothing,
   as instructed. The four copies are timestamped **13:32–13:37 local**, after `013c`
   completed at 13:31 — so this task's premise that *"the tree now shows"* the copy rule was
   **true when written but not when `013c` reported.** Worth stating so the sequence is
   readable later: the rule was exercised in the gap between the two tasks, and this
   amendment is the record catching up with what was done.

**None of the four accepted files is tracked in any commit yet** — they are staged along with
everything else from `013c` and `S009`.

---

## Prohibitions honoured

`HANDOFF-PROTOCOL.md` edited in place, not re-authored, no external replacement accepted.
`SPEC.md`, `BUILD-PLAN.md`, `REGIME-PROMPT.md` and `CHRISTOPH-TASKS.md` untouched. No state
added, removed or redefined — the five are exactly as they were. **Nothing in
`handoff/accepted/` modified.** No file recorded in `EVIDENCE-CARRY.md` modified. `records/`,
the capture and everything `S009` built left alone.

**Not committed.** `momentum-harness` untouched at `1afcecf`.
