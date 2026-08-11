---
id: 013b
title: Do you agree with the state table? — read-only reconciliation
status: DONE
owner: claude-code
ran: 2026-08-11
tree: D:\Dev\momentum
written: retrospectively under 013c §4b — 013b's task file forbade writing this file
---

# 013b — state reconciliation

**Status** DONE

> **This note was written after the fact, under `013c` §4b.** `013b`'s own task file said
> *"report in chat, write nothing including no done-note"* — an instruction that removed a
> contradiction by removing the artifact, and **is why two of the four notes lost on
> 2026-08-11 were lost.** Nothing below was re-derived by re-running anything.

---

## Per-row: two disagreements, two agreements

| task | design session | repo showed | verdict |
|---|---|---|---|
| `012` | RUNNING | header `RUNNING`; tool present; `records/tape/` **0 files**; capture not yet started | **label agreed, but see the limit below** |
| `012a` | RUNNING | header `DONE`; done-note at `handoff/done/012a-preopen-correction.md` | **DISAGREE — finished** |
| `013` | RUNNING | header `RUNNING`; **done-note exists**; status line `BLOCKED ON ONE DECISION` | **DISAGREE — blocked, not running** |
| `013a` | DONE | header still `WRITTEN`; no done-note file, by design | **repo stale; the design session was right** |

### The limit, reported rather than resolved

**`HANDED OFF` and `RUNNING` are indistinguishable on disk.** A task file in `handoff/inbox/`
with no artifact beside it looks identical whether nobody has opened it or a session is
mid-execution.

For `012` that gap was live: the capture had not started, so *"RUNNING"* was true only if it
meant *"a session has picked this up"* and false if it meant *"the capture is live"*. **The
repo could not tell which.** That is an observation about the schema, not a claim about 012.

*(Settled afterwards by `013c` §2b: `RUNNING` means picked up and not yet reported. A
scheduled window inside a task does not create a sixth state, so `012` was correctly
`RUNNING`.)*

## What 013 actually did — complete-but-unreported, and blocked

**Its done-note existed and the design session had not received it.** The table was holding a
stale `RUNNING`.

Everything was **staged but in no commit**, verified against `HEAD` rather than the index:

```
handoff/done/013-adopt-handoff-protocol.md   NOT in HEAD (staged only)
docs/specs/HANDOFF-PROTOCOL.md               NOT in HEAD (staged only)
tests/test_handoff_state_declared.py         NOT in HEAD (staged only)
```

### A correction to my own method, recorded because it nearly produced a wrong answer

My first check used **`git ls-files`**, which reads the **index** and therefore counts staged
files as present. It reported `1` for a file that was in no commit, and I labelled that output
"in HEAD". **`git cat-file -e HEAD:<path>`** is the check that actually answers the question.
HEAD was `aa8bb43`.

`013`'s real state was neither RUNNING nor DONE: Phase 1 complete, Phase 2 test written,
11 of 30 files backfilled, blocked on the evidence-hash collision, two tests red.

## What the table omitted — 21 items

**9 inbox files:** `005`, `006`, `007`, `008a`, `008b`, **`013b` itself**,
`condition-codes-config-is-unverified.md`, `H9 — Commit the specs into the repo.md`,
`separation-guard-inactive-on-official-venues.md`

**12 done-notes:** `001`, `002`, `003`, `004` ×2, `004a`, `005`, `008a`, `008b`,
`handoff-readme-stale-two-sources-of-truth.md`, `noii-supersedes-clock-anchor.md`,
`repo-cannot-run-its-own-tests-from-clean-clone.md`

## Headers contradicting reality — four

| file | header said | repo showed |
|---|---|---|
| `inbox/013a-…md` | `WRITTEN` | complete |
| `inbox/013-…md` | `RUNNING` | done-note exists, `BLOCKED ON ONE DECISION` |
| `inbox/H8-…md` | **`OPEN`** | not one of the five states; done-note exists |
| `inbox/M001-…md` | **`OPEN`** | not one of the five states; done-note exists |

`H8` and `M001` were the two `OPEN` headers `013` deliberately left — carried evidence, inside
the collision. **The backfill introduced no fabricated state**; every value it wrote was backed
by a done-note on disk. The contradictions were files it could not touch, plus `013a`/`013`
moving on after their headers were set.

## Capture untouched

`records/tape/` existed and held **0 files**. `git status records/` → 0 entries (gitignored).
`tools/capture_tape.py` unmodified since 012a. TWS up on 7496.

## Observations versus inferences

**Observations** — file existence, header text, `git cat-file -e HEAD:`, `git status` hashes,
the 0-file capture directory, HEAD `aa8bb43`.

**Inferences, labelled as such** — that `012a` "is finished" (a done-note exists and its
header says DONE; whether Christoph considers it closed is his to say); that `013` is
"blocked rather than running" (from its own status line, which I wrote); that
`HANDED OFF`/`RUNNING` are indistinguishable on disk (reasoning about the schema, not a
measurement).

**One inference declined:** whether `012` should read `RUNNING` or `HANDED OFF`. That depended
on what RUNNING meant, which was a definition question for `HANDOFF-PROTOCOL.md` and not
something the repo could settle. `013c` §2b has since settled it.

## Proof the tree was unchanged

```
baseline (before 013b) : d945cf15b9252068be04f0bbf847c34b0dd56a96
current  (after)       : d945cf15b9252068be04f0bbf847c34b0dd56a96
UNCHANGED: True     28 entries
```

*(That baseline differs from 013a's only because 013b's own task file had arrived in the
inbox between the two reads — 27 → 28 entries.)*
