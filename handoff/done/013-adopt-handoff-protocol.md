---
id: 013
title: Adopt HANDOFF-PROTOCOL and enforce task-file state headers
status: BLOCKED ON ONE DECISION — Phase 1 complete, Phase 2 test written, backfill 11 of 30
owner: claude-code
ran: 2026-08-11
tree: D:\Dev\momentum
---

# 013 — HANDOFF-PROTOCOL adopted; the backfill hit a rule collision

**Status** RUNNING

```
BEFORE : 65 passed, 0 failed
AFTER  : 67 passed, 2 failed
```

**The two failures are `test_handoff_state_declared` itself, and they are correct.** 19 task
files have no state header, and **every one of the 19 is hash-verified carried evidence**
that M001 §4 forbids modifying. Zero non-evidence files are missing a header.

I did not weaken the test, and I did not edit the evidence. **The collision is a decision,
not a repair, and it is below.**

---

## Four divergences between 013 and what was on disk

Before anything else, because two of them changed what I did:

1. **The files were not in `D:\Dev\_adopt\`.** Both were in `handoff/inbox/` — untracked.
   Adopting from there would have bypassed the drop folder entirely, and `handoff/` is
   gate-exempt, so nothing would have stopped it. Moved to `_adopt\` and run through the gate
   properly.
2. **The companion was named `HANDOFF-PROTOCOL.provenance.md`**; the gate looks for
   `<candidate-filename>.provenance.md`, i.e. `HANDOFF-PROTOCOL.md.provenance.md`. Renamed.
   **The design session and the gate use different companion-naming conventions** — worth
   aligning at the source rather than renaming every time.
3. **The companion carried none of the four fields the gate parses.** It had `**origin:**`
   bolded, and no `source`, `reason` or `depends` at all, so refusal 1 would have fired on
   what is otherwise the best-written companion yet. I derived the four fields **from the
   supplied prose** and preserved every word of it underneath, under a heading saying so.
   Nothing was invented.
4. **"The 8 pre-existing failures stay at 8" does not describe this tree.** `D:\Dev\momentum`
   was at **0 failures, 65 passed** before this task. The figure of 8 was
   `momentum-harness`'s count before H11 restored `requirements.txt` — it is now 6 there.
   **There are no pre-existing failures to name in this repo**, so that exit test is
   vacuous as written.

---

## Phase 1 — adopted

### The `ADOPTION-LOG.md` row as written

```
| 2026-08-11 | `docs/specs/HANDOFF-PROTOCOL.md` | `authored in the design session of
2026-08-11; not imported, not derived from momentum-harness, not carried from Drive` |
authored | first written statement of the handoff convention, which has run unwritten for
the whole project and has already produced one task treated as finished on a report the
design session could not see | `n/a (not a code tree)` | Christoph |
```

A **create**, not a supersede — `--supersede` was not passed. `origin: authored`, so refusal
4 did not apply. Dry-run first: `PASSES all four refusals`.

### One repair on landing

The file arrived with **`**Status** CURRENT`** and `docs/specs/` requires **`**STATUS**`**, so
`test_every_spec_declares_status` failed on adoption. This is precisely the RE-SUPPLY case
H11 built for, and the fix is its rule: **re-apply, do not re-author.** Added
`> **STATUS** CURRENT · **date** 2026-08-11` as the first non-heading block; the author's own
metadata block is untouched beneath it.

**This is not the document being wrong.** It defines `**Status**` as the *task-file*
convention at its own line 69, and that is correct for `handoff/`. The two conventions are
different questions — a document's lifecycle versus a task's handoff state — and a file that
is both a spec and the definition of the task convention needs both headers. Worth knowing
before someone "fixes" the duplication.

---

## Phase 2 — the test

`tests/test_handoff_state_declared.py`.

### The matching rule, quoted from the test

```python
#: **Header region only — the first 20 lines.** A task file that discusses these
#: words in prose must not accidentally satisfy the test. This is a positional
#: rule rather than an exclusion list, for the same reason the `6 of 9`
#: normalisation ended up positional: a list of things to ignore grows until it
#: is a hiding place, and a rule about WHERE the claim must appear does not.
HEADER_LINES = 20

STATUS_RE = re.compile(r"\*\*Status\*\*[:\s]*([A-Za-z][A-Za-z ]*?)\s*(?:·|\||$)", re.M)
```

The capture is deliberately greedy to the end of the state token, so `IN PROGRESS` is
reported **whole** rather than matching `IN` and reporting something the file does not say.
`test_the_header_region_rule_is_positional_not_lexical` proves a state declared past line 20
is not accepted — the protocol document itself is the natural counter-example, since it
tabulates all five states in prose.

### Both refusal messages, verbatim

**Refusal A — no state header:**

```
AssertionError: these task files declare no handoff state in their first 20 lines:
    handoff/inbox/zz-temp-a.md

Add a header line, e.g. `**Status** RUNNING`. One of: WRITTEN · HANDED OFF · RUNNING · REVIEWED · DONE
Christoph holds the state — if it is not known, ask rather than assume. See docs/specs/HANDOFF-PROTOCOL.md.
```

**Refusal B — invalid state:**

```
AssertionError: these task files declare a state outside the five:
    handoff/inbox/zz-temp-b.md: declares 'IN PROGRESS'

The five states are: WRITTEN · HANDED OFF · RUNNING · REVIEWED · DONE
This is not a missing header — the file says something, and what it says is not a state.
Do not add a sixth state; see docs/specs/HANDOFF-PROTOCOL.md.
```

Two distinct messages for two distinct defects, as required. Both temp files deleted.

Empty directories pass: `task_files()` skips a directory that is absent or empty rather than
treating emptiness as failure.

---

## The collision — and it is the reason this task is not green

**`handoff/**` is carried evidence.** M001 §4 carried 21 task files byte-identical, recorded
their sha256 in `EVIDENCE-CARRY.md`, and `.gitattributes` marks `handoff/**` as `-text` so
git cannot even normalise their line endings. `tests/test_evidence_carry_intact.py` fails if
any byte changes.

**013 instructs me to add a header line to those files.** Those two rules cannot both hold.

**I found this the hard way.** My first backfill used `write_text()`, which normalised
CRLF→LF and **rewrote all 30 files** — `git diff --numstat` showed whole-file replacements,
not `+2` lines, and `test_evidence_carry_intact` caught it immediately with the recorded and
current hashes side by side. Restored with `git checkout -- handoff/`; nothing was lost. The
second pass operates on bytes and preserves line endings exactly, and the diffs are `+2/-0`.

**That accident is the argument.** §4's rule is not fussiness: an automated reformat of
evidence is exactly the failure it exists to catch, and it caught it within one test run.

### What I did instead

Backfilled **only the 11 files authored in this tree**, where no conflict exists:

| file | was | now |
|---|---|---|
| `handoff/inbox/012-live-qqq-tape-capture.md` | WRITTEN | **RUNNING** |
| `handoff/inbox/013-adopt-handoff-protocol.md` | WRITTEN | **RUNNING** |
| `handoff/inbox/H10-…`, `H11-…` | **OPEN** *(invalid)* | DONE |
| `handoff/done/005, H8-and-corrections, H9-commit-the-specs, H9a, H10, H11, M001` | (none) | DONE |

**19 carried files are untouched and remain headerless**, which is why the suite is red.

### The three resolutions, and my recommendation

| # | option | cost |
|---|---|---|
| **A** | Backfill all 19 and **re-record their hashes** in `EVIDENCE-CARRY.md` with a dated note saying 013 added a state header and nothing else | the manifest becomes a record of *reasoned* change rather than *no* change |
| **B** | Scope the test to natively-authored files only | **weakens the test — 013 forbids this**, and it would exempt exactly the files most likely to go stale |
| **C** | Leave them headerless permanently | a permanently red suite, which trains everyone to ignore it |

**I recommend A.** The manifest's job is to make change *visible and reasoned*, not to forbid
it — a single-purpose, dated, documented modification preserves the property that matters.
But H11 criticised me, correctly, for making a gate change under task pressure, and this is
the same shape: **the session that wants the exemption should not be the one that grants it.**
So I stopped.

**A is roughly ten minutes** once you say so.

---

## Backfill states — and which were inferred

**Known, from repo evidence:**

- `handoff/done/*` → `DONE`, per 013's instruction.
- Inbox copies with a matching done-note → `DONE` (H10, H11 — both had declared the invalid
  state `OPEN`).
- `013` → `RUNNING`; I am executing it.

**Inferred, flagged as 013 requires:**

- **`012` → `RUNNING`.** 013 says write `RUNNING` if the state is unknown and say so. Stating
  it precisely: **012 is part-run.** Phase 0's five answers are complete, `tools/capture_tape.py`
  is written and verified, and the capture itself has **not started** — the window opens at
  09:00 ET and it is currently ~05:00 ET. If "RUNNING" should mean the capture is live, 012 is
  not there yet and the honest value is `HANDED OFF`.

**Not assigned, and this is a category question rather than a state question:**

- `handoff/inbox/condition-codes-config-is-unverified.md`
- `handoff/inbox/separation-guard-inactive-on-official-venues.md`

Neither is a task file in the `NNN-`/`H` series. They read as parked observations or open
questions, and `CLAUDE.md` gives those `docs/observations/` and `handoff/questions/`. Forcing
a handoff state onto them asserts they are tasks, which may be false. **They are also carried
evidence**, so they are inside the collision regardless.

---

## The 8 pre-existing failures, by name

**There are none.** The tree was `65 passed, 0 failed` before this task. For the record, the
failures that *do* exist elsewhere are `momentum-harness`'s six — five phase-3-gated
`test_incomplete_work` cases and one intended-red open question — and that repo is untouched
at `1afcecf`.

The two failures now present are both `tests/test_handoff_state_declared.py`, both caused by
the collision above, and both will clear the moment resolution A is authorised.

---

## Prohibitions honoured

Nothing in `records/`, no tape file, nothing touching 012's capture. **No TWS connection
opened by this task.** `SPEC.md`, `REGIME-PROMPT.md` and `BUILD-PLAN.md` untouched. No gates,
states or rules added beyond the five. The test was not weakened.

One thing I fixed that belongs to 012: **`tools/capture_tape.py` had no allowlist entry**, and
since `tools/` is a code tree with no native-prefix carve-out, the gate flagged it. It
surfaced on this task's full-suite run rather than 012's, which only ran the tool.

## Left open

| # | item | owner |
|---|---|---|
| 1 | **The evidence-vs-header collision** — resolution A, B or C. Two tests stay red until then. | Christoph |
| 2 | **`012`'s state** — `RUNNING` or `HANDED OFF`, depending on what RUNNING means for a part-run task. | Christoph |
| 3 | **The two non-task files in the inbox** — are they tasks at all, or misfiled observations? | Christoph |
| 4 | **Companion naming**: design session uses `X.provenance.md`, the gate expects `X.md.provenance.md`. | design session |
| 5 | **UAT** — read rule 4 and confirm it matches what you meant by shared judgment. | Christoph |

**Not committed.** `momentum-harness` untouched at `1afcecf`. Neither repo pushed.
