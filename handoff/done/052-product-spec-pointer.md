---
id: 052
title: The product-spec pointer, the document-link audit, and the mockup-citation sweep
type: done-note
class: admin
task: handoff/inbox/052-for-code-task-product-spec-pointer.md
task-version: 3.0
closes: B-085
date: 2026-08-16
owner: claude-code
tree: D:\Dev\momentum
---

**Status** RUNNING

# 052 — done-note

**The one-line summary: Part 1 landed and broke two guards; Parts 2 and 3 changed nothing, and
that is the finding rather than an absence of one.**

Three files gained the ruling comment. **Zero document links were rewritten and zero mockup
citations were rewritten** — every hit in the tree is either inside a record, or names a
first-generation mockup that `052` itself says to report rather than patch. **A sweep that
touches nothing is the outcome the task's own exclusions produce, and the inventory below is
the deliverable.**

---

## 1 — Which files received the header comment

| File | Comment added | Why |
|---|---|---|
| `docs/specs/SPEC.md` | **yes** | Named by the task |
| `docs/specs/BUILD-PLAN.md` | **yes** | Named by the task; exists at the stated path |
| `docs/specs/RE-SUPPLY.md` | **yes** | Named by the task; exists at the stated path |
| `docs/specs/REGIME-PROMPT.md` | **no** | Forbidden by the task — an instruction to a scheduled run |
| `docs/specs/HANDOFF-PROTOCOL.md` | **no** | Forbidden by the task — protocol |
| `docs/specs/CHRISTOPH-TASKS.md` | **no** | Not named. Companion to `HANDOFF-PROTOCOL.md`; protocol, by the same reasoning |
| `docs/specs/DRIVE-ARCHIVE-LIST.md` | **no** | Not named. See §6 — its classification is itself unsettled |
| `docs/specs/USE_GUIDE.md` | **no** | Not named. `STATUS HISTORICAL`, and describes `momentum-harness` |
| `docs/specs/REPO_CONSOLIDATION_PLAN.md` | **no** | Not named. `STATUS HISTORICAL` — a record of an executed plan |
| `docs/specs/layer0-amendment-2-frozen-vs-live.md` | **no** | Not named. `STATUS SUPERSEDED` by `SPEC.md` §5.1. See §6 |
| `docs/specs/mockups/mockup-README.md` | **no** | Not named. `STATUS HISTORICAL` |

**The comment is byte-identical in all three**, exactly as written in the task, including the
one permitted folder link.

**Both files the task asked about exist:**
`docs/specs/BUILD-PLAN.md` (98,750 bytes) and `docs/specs/RE-SUPPLY.md` (5,989 bytes).

---

## 1a — The collision, which is the substantive part of this task

**The 21-line comment turned two green guards red, and the exit tests said to treat that as a
coupling finding. It is one, and it was fixable.**

```
FAILED tests/test_resupplied_docs_are_repaired.py::test_invariant_1_every_spec_still_declares_a_status
FAILED tests/test_spec_pointers.py::test_every_spec_declares_status
```

**Both read the first ten RAW lines of every `.md` under `docs/specs/` looking for a
`**STATUS**` header.** The comment is 21 lines plus a blank, so in all three files the header
moved from line 3 to line 24.

**The comment renders as nothing.** The STATUS header is still the first thing a reader sees.
The guards were measuring the wrong thing — file position, where they meant reading position —
and the header comment is simply the first input that made the difference visible.

**Fixed by teaching the window to skip a LEADING HTML comment block, not by raising ten to
forty.** `test_spec_pointers.head()` now owns that rule; `test_resupplied_docs_are_repaired.py`
loads it **by path**, matching the `_path_module()` idiom already in that file, so the
definition of *how far in the header may be* exists once.

**The loophole this could have become is pinned by a test.** `test_the_head_window_skips_only_comments`
asserts three cases, and the third is the one that matters: **a STATUS header buried under 21
lines of prose is still red.** Only a comment — invisible when rendered — is skipped. A
document arriving with no STATUS at all fails exactly as it did before.

**A third test uses the same window** and was not red only because no spec is currently
`SUPERSEDED` in a way that reached it: `test_every_superseded_spec_names_a_resolving_by`. It was
moved to the shared helper too, so it does not go red the first time a superseded spec gains a
comment.

### RE-SUPPLY.md gains invariant 5, and this was not asked for

**Added deliberately. The ruling is invisible when rendered, which makes it the tree-side repair
most certain to be silently dropped.** An author re-supplying `SPEC.md` from the design session
is looking at rendered text; the comment is not there to see; the file comes back well-formed,
the gate compares bytes and passes it, and the document has quietly un-ruled itself. **Nothing
in the tree would have noticed.**

So: `docs/specs/RE-SUPPLY.md` invariant 5, and
`test_invariant_5_dev_specs_keep_the_product_spec_ruling`, which asserts the ruling's first line
is present in all three files and names re-supply as the cause when it is not.

**This is the exact failure mode `RE-SUPPLY.md` was written for, applied to the newest repair.**

---

## 2 — Every document link found

**51 hits across 4 files.** Patterns: `docs.google.com/document`, `docs.google.com/spreadsheets`,
`drive.google.com/file`. Scope: `handoff/`, `christoph/`, `docs/`, `claude/`, `CLAUDE.md`.

| File | Links | Lines | Rewritten | Why |
|---|---|---|---|---|
| `docs/specs/DRIVE-ARCHIVE-LIST.md` | **45** | 20–39, 49–54, 74, 78, 82, 84, 86 | **no** | See below — this is the whole of §2's finding |
| `docs/specs/USE_GUIDE.md` | 1 | 26 | **no** | `STATUS HISTORICAL`. Describes `momentum-harness`, and its own banner says *"None of it is true of this tree"*. A record |
| `docs/observations/OBSERVATIONS.md` | 2 | 123 | **no** | Excluded by the task. Also not URLs — they are the two grep patterns, quoted inside the row this task added |
| `handoff/inbox/052-…-product-spec-pointer.md` | 3 | 103–105 | **no** | The task's own grep patterns |

**`CLAUDE.md`: zero. `claude/NOW.md`: zero. `christoph/`: zero. `handoff/done/`,
`handoff/accepted/`: zero.**
**No live instruction outside `DRIVE-ARCHIVE-LIST.md` carries a document link at all.**

### Why `DRIVE-ARCHIVE-LIST.md` was left alone — a judgment, recorded as **OBS-072**

**By the letter of the task it qualifies**: it is under `docs/specs/*`, and its own header says
*"Read as instruction, not record."* **By the reason given for the rule it does not**, on two
counts:

1. **Its links are archive TARGETS, not references to authority.** The rule's rationale is that
   a link dies on revision and may resolve to a superseded document. **That is the property this
   file exploits** — it exists to point at 32 specific superseded documents so they can be moved
   into `_archive`. A link resolving to a superseded document is the success condition here.
2. **Name-plus-folder cannot express what it says.** Two rows name the same document —
   `Failed-Bounce Rollover Short Playbook`, at 2,812 and 6,460 bytes — and the file id is the
   only thing that distinguishes them. Rewriting to names collapses them into one row that
   archives the wrong file.

**Recorded rather than decided.** The genuinely open question is prior to the rule: its 32 moves
were never made and `H7` still owns them, so **whether the file is instruction or history is
undecided** — and that ambiguity, not the links, is the finding.

---

## 3 — Every mockup citation found

**94 citations across 17 files** (excluding the five mockup sheets themselves, which the task
forbids touching, and `052`'s own mapping table).

**None was rewritten. Not one citation in this tree names a second-generation mockup.**
`mockup-09` through `mockup-17` — the whole of the rename table — appear nowhere except in the
task file. **Every hit is `mockup-01` … `mockup-08` or `mockup-README`: first generation, which
`052` says to report rather than patch.**

### Live instructions (no done-note, or `STATUS CURRENT`) — reported, not patched

| File | Lines | Citations |
|---|---|---|
| `docs/specs/SPEC.md` | 146–150, 213–216, 1633, 1953, 2023, 2668 | `mockup-01`…`08` |
| `docs/specs/REGIME-PROMPT.md` | 141 | `mockup-02` |
| `handoff/inbox/006-ranked-watchlist-panel.md` | 28, 38, 40, 57, 129, 130, 133 | `mockup-03`, `05`, `README` |
| `handoff/inbox/007-watchlist-ingestion-amendments.md` | 29, 59, 136, 138 | `mockup-01`, `03`, `README` |

> **`SPEC.md` line numbers are POST-CHANGE** — the header comment shifted everything down by 22.

### Records — excluded by the task, listed for completeness

`handoff/done/003`, `004-watchlist-ingestion-spec`, `005`, `H8`, `H9`, `H10`, `H11`;
`handoff/inbox/005`, `030`, `H10`, `H11` (all four have done-notes);
`docs/specs/mockups/mockup-README.md` (`STATUS HISTORICAL`); `docs/observations/OBSERVATIONS.md`;
`christoph/done/015 for christoph attach qqq.md` (the word "mockup", not a citation).

**`CLAUDE.md` line 228 names `docs/specs/mockups/` and "the five screen mockups".** That is a
directory path and an accurate count of what is on disk, not a numbered citation. Left as is.

---

## 4 — Staleness findings: live instructions on first-generation mockups

**Two, and both are recorded in the ledger.**

### OBS-070 — `SPEC.md` cites three mockups that exist nowhere

`docs/specs/mockups/` holds exactly five sheets, `mockup-01` through `mockup-05`, plus
`mockup-README.md`. **`SPEC.md` cites `mockup-06`, `mockup-07` and `mockup-08` as though they
were sheets in that folder. They are not in the tree, and they are not in Drive under those
numbers either.**

**And the numbers collide across generations.** `052`'s table maps `mockup-08` to
`TAPE mockup — twelve tape states`. `SPEC.md` line 216 cites `mockup-08` for the **hotkey and
palette table**. Applying the rename mechanically would have pointed a hotkey section at a tape
mockup — **a wrong pointer that looks like a repair**, which is precisely why `052` says report,
not rename.

### OBS-071 — `006` and `007` are open tasks built on retired sheets

**Neither has a done-note.** Every neighbour from `004` to `008b` does, so by the addressability
rule both are still open work — and `NOW.md` will keep reporting them.

`006` tells the builder to read `mockup-README.md` first and cites `mockup-03` five times. `007`
orders a re-draw of `mockup-01-ingest.html`. **The inbox has since reached `052`.**

**The question for Christoph is not about mockups: are `006` and `007` still owed, or were they
overtaken?** Nothing in the tree distinguishes an abandoned task from a pending one.

---

## 5 — Classification findings in `docs/specs/`

**Four files are neither dev spec nor protocol.** Reported, not moved — `052` forbids
restructuring that folder, and retiring it was discussed and rejected.

| File | STATUS | What it actually is |
|---|---|---|
| `USE_GUIDE.md` | HISTORICAL | An operating guide for `momentum-harness`. Its own banner: *"None of it is true of this tree."* |
| `REPO_CONSOLIDATION_PLAN.md` | HISTORICAL | A record of an executed plan. Kept as the definition of "step 7" |
| `DRIVE-ARCHIVE-LIST.md` | CURRENT | An archive manifest with 32 unexecuted moves. **Header says instruction; content is an audit.** See OBS-072 |
| `layer0-amendment-2-frozen-vs-live.md` | SUPERSEDED | **A product-spec amendment, in the tree.** See below |

### The one worth a second look

**`layer0-amendment-2-frozen-vs-live.md` is a product spec sitting in the tree**, which is the
thing `052` says not to create: *"Do not copy any product spec into the tree. A second copy is a
second authority."*

**It is not a violation of this task** — it was adopted 2026-08-10 under H9, long before the
2026-08-16 ruling, and it is `STATUS SUPERSEDED` by `SPEC.md` §5.1. **But it is exactly the
shape the new rule forbids**, and if Layer 0 is ever revived from §12.1 it becomes a live second
authority. **Flagged, not touched** — deciding it is product work.

---

## 6 — B-085

**Row `B-085` → `CLOSED BY DESIGN`.**

**I did not update the sheet and cannot verify it was updated.** The bug register is not in this
tree — no `B-0` row exists anywhere under `handoff/`, `docs/` or `claude/`. Whoever holds it must
set the status; **treat this line as a request, not a record.**

---

## 7 — Test results, verbatim

**Baseline, main checkout, before any change:**

```
8 failed, 486 passed, 1 warning in 39.93s
```

**After, main checkout:**

```
8 failed, 488 passed, 1 warning in 41.12s
```

**Same eight failures, identically named. Two more passing — the two tests this task added.
Delta from 052: zero red, plus two green.**

The eight, unchanged and none of them this task's:

```
tests/test_handoff_state_declared.py::test_every_task_file_declares_a_state
tests/test_observation_ids_are_unique.py::test_every_observation_id_is_allocated_once
tests/test_observations_ledger.py::test_every_retired_uat_has_a_register_row
tests/test_observations_ledger.py::test_refusal_b_a_retired_uat_with_no_destination_is_red
tests/test_regime_prompt_invariants.py::test_no_bare_six_of_nine
tests/test_regime_prompt_invariants.py::test_no_bare_six_of_nine_anywhere_in_specs
tests/test_regime_snapshot_could_not_do.py::test_the_format_still_lacks_a_key
tests/test_uat_has_a_file.py::test_every_declared_uat_exists_as_a_file
```

**Two of these are documented as expected red** — the duplicate ledger ids (`OBS-044`–`047`,
held open by `handoff/questions/044-duplicate-ledger-ids.md`) and `6 of 9`, which `RE-SUPPLY.md`
says must be fixed at source in `REGIME-PROMPT.md` v1.9 and **not** tree-side.

**`test_every_task_file_declares_a_state` names ten inbox files with no `**Status**` header** —
`021`–`027`, `035`, `037`, `038`. **Not caused by this task**; `052`'s own file declares
`**Status** WRITTEN` and is not in the list. It predates the run and is unowned.

**The worktree run is not comparable and is recorded so nobody re-derives it.** A detached
worktree reports four extra failures — `test_evidence_carry_intact` ×2,
`test_the_destination_paths_are_inside_the_repo`, `test_claude_md_pointers_resolve` — because
gitignored and untracked files are absent from it. **12 failed / 483 passed there, at zero delta
from its own 12 / 481 baseline.**

### Refusal test

**Not applicable, and stated explicitly rather than invented.** No rendering path is touched.
This task adds an HTML comment to three markdown documents and widens a test's read window;
nothing in `live/`, `core/` or the TUI is reached, and there is no refusal to exercise.

---

## 8 — What I could not do

1. **`B-085` could not be updated.** The bug register is outside this tree. §6.
2. **`DRIVE-ARCHIVE-LIST.md`'s 45 links were not rewritten.** A judgment against the letter of
   the task, with the reasoning above and a ledger row. **If the ruling is that the rule admits
   no exception, this is a one-command follow-up** — but the two same-named playbook rows will
   become indistinguishable and the manifest stops working.
3. **No mockup citation was rewritten, because none could be.** The rename table covers
   `mockup-08` through `mockup-17`; the tree cites `mockup-01` through `mockup-08` in
   first-generation numbering. **The single overlap, `mockup-08`, means different things in the
   two generations.**
4. **`SPEC.md` was not reconciled against the product spec set.** Explicitly out of scope.
   **OBS-070 is the first concrete instance of what that reconciliation will find**, and it is
   larger than a rename: the mockup index in §3.1 no longer describes anything that exists.
5. **Not verified: that the product spec set is reachable, that `SPEC-INDEX` exists, or that the
   folder link in the header comment resolves.** The comment was transcribed as given. **The tree
   now asserts the existence of documents nobody in this session could open.**

---

## Ledger rows added

| id | type | what |
|---|---|---|
| **OBS-070** | OBSERVATION | `SPEC.md` cites six mockups by number; three name nothing that exists, and `mockup-08` collides across generations |
| **OBS-071** | OBSERVATION | `handoff/inbox/006` and `007` have no done-note and instruct against retired first-generation sheets |
| **OBS-072** | READING | The no-document-link rule has one file where applying it destroys the file's function, and that file's own classification is unsettled |

All three `OPEN`, `review-by 2026-11-16` — three months, matching the ledger's stated convention.

---

## Files changed

```
docs/specs/SPEC.md                          +22   header comment
docs/specs/BUILD-PLAN.md                    +22   header comment
docs/specs/RE-SUPPLY.md                     +22   header comment, +14  invariant 5
tests/test_spec_pointers.py                 +75   head() helper, its test, two call sites
tests/test_resupplied_docs_are_repaired.py  +61   _pointers_module(), invariant 5 test
docs/observations/OBSERVATIONS.md           +3    OBS-070, OBS-071, OBS-072
```

**Worktree:** `%TEMP%\wt-052`, branch `task-052`, fast-forwarded into `main` and removed.
**Scratch:** `$env:TEMP` only. Nothing was written inside the repository.

---

## >>> THIS NOTE MUST BE PASTED TO CHAT <<<

**It lands in a repo the design session cannot see.** On 2026-08-11 two correct done-notes were
written and never reached it. **Three items here need a person:**

1. **`B-085` → `CLOSED BY DESIGN`** — someone must set it in the register.
2. **`006` and `007`: still owed, or overtaken?** OBS-071.
3. **Does the no-document-link rule carve out archive manifests?** OBS-072.
