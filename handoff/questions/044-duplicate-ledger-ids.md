---
id: 044-q1
title: Which set of duplicate ledger ids gets reallocated — the rule or the reason?
status: ANSWERED
answered_by: 053
answered_on: 2026-08-16
raised_by: claude-code
task: 044
---

**Status** DONE

> ## ANSWERED by `053` Part 1, 2026-08-16
>
> **Apply the reason, not the rule. `021`'s three rows moved forward; `037`'s rows keep
> `OBS-044`, `OBS-045` and `OBS-046`.**
>
> `044`'s rule -- *the earlier allocation keeps the number* -- was only ever a means to the end
> **do not change what an exported done-note appears to have said**, and it was written under a
> false belief about which set came first. **When a means and its end separate, the end is the
> durable half.** The arithmetic settles it: the letter would have retargeted twenty citations
> across nine exported files; the reason breaks nothing, because `021`'s done-note cites none of
> the three. That was verified in the tree, not assumed.
>
> **Stopping was correct.** `044`'s own clause -- *if any reallocation would change what an
> exported done-note appears to have said, stop and report* -- is triggered by the literal
> reading. That is the clause working, not the task failing.
>
> **The ids actually allocated: `OBS-073`, `OBS-074`, `OBS-075`**, read from the ledger at
> execution time. **Not `OBS-065`-`067` as this file proposed** -- those were free when this
> question was written two days ago and were taken by the time it was answered, as were
> `OBS-070`-`072`. *The question was right about the action and could not be right about the
> numbers.*
>
> **And the count was wrong in both directions.** `B-030` said five, `053` said three; **the
> ledger holds four**, and `OBS-062` had already recorded that. The fourth, **`OBS-047`, is a
> PERMANENT collision and was not reallocated**: both of its rows are cited by exported
> done-notes, so moving either breaks the very end the ruling exists to protect. It is
> documented in `docs/observations/OBSERVATIONS.md` and disambiguated by date.

# `044` Part 3's rule and its reason point in opposite directions

**`044` Part 3 rests on a premise that git contradicts, and the two readings that
follow lead to opposite actions. I did not reallocate anything.**

---

## What `044` says

> **The earlier allocation keeps the number. The later one is reallocated forward.**
>
> **Why that way round.** `037` allocated `044`–`047` first, and `041` and `043` cite them in
> done-notes **already exported to Drive**. `handoff/` is copy-and-keep — those files cannot be
> edited without putting the tree and Drive out of sync on bytes. **Moving the earlier findings
> would break three documents; moving the later ones breaks none.**

---

## What is actually true

**`021`'s rows were allocated first, not `037`'s.** Established from git, which is `044`'s own
suggested method — *"use the ledger's own ordering, or the commit that introduced each row."*

| commit | when | which rows |
|---|---|---|
| `e625df3` | 2026-08-13 22:12 | **`021`'s** — `keepUpToDate` dies silently · the ~5 s beat · `survived_window` |
| `eba938d` | 2026-08-14 14:01 | **`037`'s** — inbound copier has no record · export cannot run from a worktree · worktrees outlived their tasks |

`git merge-base --is-ancestor e625df3 eba938d` succeeds. **`021` is first by commit and by the
dates on the rows themselves.**

**And it is `037`'s meanings that everything cites**, which is the reverse of what `044` assumed:

| id | files under `handoff/` citing it | which meaning they intend |
|---|---|---|
| `OBS-044` | 3 | the inbound copier |
| `OBS-045` | 8 | export cannot run from a worktree |
| `OBS-046` | 9 | worktrees outlived their tasks |

**`021`'s done-note cites none of the three.**

---

## The fork

**Apply the rule as written** — earlier keeps the number, so `021` keeps `044`–`046` and **`037`'s
rows move**. This silently retargets **nine files under `handoff/`**, several already exported to
Drive, so that every existing citation of `OBS-046` now resolves to *"a probe reported
`survived_window: true`"* instead of *"worktrees outlived their tasks"*.

**Apply the reason as written** — protect the exported citations, so **`021`'s rows move** and
`037`'s keep their numbers. This breaks no citation at all. **It contradicts the rule's letter**,
because `044` believed `037` was first and it was not.

---

## Why I stopped rather than choosing

**`044` closes Part 3 with an unconditional clause that covers exactly this:**

> **If any reallocation would change what an exported done-note appears to have said, stop and
> report instead.**

The literal rule does precisely that, to nine files. **So the instruction to stop is the
instruction that applies**, and `044` also says *do not guess, and do not use "which one seems
more important"*.

**My reading, offered as a recommendation and not acted on:** the reason is the durable half. It
names a concrete harm — a citation that silently changes meaning — while the rule's "earlier
keeps the number" was a means to that end, chosen under a false belief about which set was
earlier. **Moving `021`'s three rows forward to `OBS-065`–`067` breaks nothing and leaves every
exported document correct.** But that is a ruling, not a deduction, and it is yours.

---

## Two other corrections to `044` Part 3

**1. There are three duplicated ids, not five.** `044` names `OBS-044`, `045`, `046`, `047` and
`053`. Measured today, **`047` and `053` are unique** — whatever duplicated them has already been
resolved, or they were counted at a moment the ledger no longer reflects.

**2. `tests/test_observation_ids_are_unique.py` is RED and is meant to be.** It names this
question in its failure message. **It is deliberately not `xfail`** — that would remove it from
the failure count, which is the cheap route to green that the ledger convention exists to
forbid.

---

**This question needs to be pasted to chat, and it blocks nothing else in `044`** — Parts 1, 2
and 4 are complete.
