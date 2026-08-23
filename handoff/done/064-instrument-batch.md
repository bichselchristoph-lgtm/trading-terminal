---
id: 064
title: Four instruments, four disjoint files, one commit — three landed, two of five sub-items refused for cause
type: task
class: admin
owner: claude-code
unblocks: NOTHING
depends: none
touches: verify.ps1 sync.ps1 export-handoff.ps1 tests/test_task_file_shape.py
bugs: []
---

**Status** RUNNING

# 064 — done. Parts A, C, D landed; Part B found nothing in its own file to fix.

**Four subagents ran in parallel, each scoped to exactly one file, and were told explicitly to
refuse rather than write outside it.** That refusal mechanism fired for real, twice — not as a
hypothetical the task described, but as the actual outcome for A3 and all of B. Both refusals are
reported below with the exact fix each would need, per the task's own instruction not to route
around a scope boundary.

`handoff/done/063-quiet-tree-reverify.md` (Part 0) was written separately, closing `063` without
retroactively claiming a `verify.ps1` run. This note does not repeat it.

---

## Part A — `verify.ps1`

**A1 — DONE.** The BOM hypothesis was tested empirically, not assumed. The subagent copied
`verify.ps1` to two scratch files under `$env:TEMP`, parsed both with
`[System.Management.Automation.Language.Parser]::ParseFile` under the real, live
`powershell.exe` 5.1.26100.9168 on this machine: the no-BOM copy produced **5 parse errors**
(first: `The string is missing the terminator: "` at line 827); the BOM copy produced **0**.
Cross-checked under `pwsh` 7.6.4: both variants parse with 0 errors either way, so the BOM does
not affect `pwsh` compatibility. A UTF-8 BOM was applied to the real `verify.ps1`
(41663 → 41666 bytes, confirmed by `git diff --stat`: 1 line changed, no content difference).
Post-edit, both `powershell.exe` 5.1 and `pwsh` 7 parse it with 0 errors. The subagent did not
run the script end-to-end at any point — parser-level validation only, per instruction, since a
full run would have collided with the other three parts' concurrent edits.

**A2 — DONE, report-only, no scheduled task exists.** Queried the live Windows Task Scheduler
two independent ways — `Get-ScheduledTask` (216 tasks total) and `schtasks /query /fo LIST /v`
(295 tasks) — filtering for anything naming `momentum` in its name, Execute, Arguments, or
WorkingDirectory. **Zero matches, either way.** `tools/register-sync-task.ps1`'s
`momentum-inbound-sync` task (which the script would register with `Execute 'powershell.exe'`
running `sync.ps1`) is **not currently registered on this machine** — the script describes what
running it would produce, not a live fact. **This means the 15-minute scheduled sync this
project's documentation and several done-notes (including `063`'s own analysis) assume is
running was not actually running on this machine at the time this was checked.** No scheduled
task was created or changed — this was report-only, as instructed.

**A3 — REFUSED, as the task anticipated.** Confirmed by reading `tools/now.py`: the
`admin:product this stretch {admin}:{product}` line is computed and rendered entirely inside
`tools/now.py`'s `render()` and its state dict; `verify.ps1`'s own NOW section only invokes that
script as a subprocess and reprints the block it wrote. Grepping both files for `unblocks` found
zero matches anywhere — the `unblocks:`-keyed "admin task naming a product task" count and the
"days since last product task" derivation do not exist yet in any form. Implementing the
four-line format would require adding this to `tools/now.py`'s state computation (and very
likely `tests/test_now_is_derived.py`), both outside `verify.ps1`. The subagent explicitly
declined to work around this by re-deriving the counts a second time inside `verify.ps1` by
parsing `NOW.md`'s existing one-line output — that would be a second implementation of logic
that belongs in one place, the exact failure `sync.ps1`'s own header warns against elsewhere in
this repo. **`claude/NOW.md` still renders the single `admin:product this stretch N:M` line, not
four.** The UAT instruction in `064` §7 ("read the four `NOW.md` numbers") cannot be carried out
as written until a future task implements A3 in `tools/now.py`.

## Part B — `sync.ps1`

**No edit was made to `sync.ps1`.** The subagent confirmed by reading it that it is a ~70-line
pure pass-through wrapper with no business logic of its own — it locates the venv Python
interpreter, builds an argv list, invokes `tools/sync_from_drive.py`, and passes its exit code
through. All three sub-items' actual logic lives in `tools/sync_from_drive.py`, a file outside
this part's scope, and the wrapper's own header comment ("IT WRAPS, IT DOES NOT REIMPLEMENT")
was treated as binding rather than worked around.

**B1 — REFUSED.** Confirmed in `tools/sync_from_drive.py`: `main()` computes
`success = previous_success if blocked else attempt`, and `PairResult.blocked` is `True`
whenever any pair has a differing file, a collision, or an unreachable source/destination —
which has been continuously true since `040`/`043`/`052` started differing on 2026-08-15. A
designed refusal is not a run failure, so gating `last_success` on `blocked` has saturated the
one signal that would report a genuinely broken sync channel for over a week. **The record
already carries a separate, machine-readable `refused` count per pair** (added under a prior
task, `056` — the "split the two facts" half of B1 is already done); what remains broken is
specifically that `success` should advance on any completed run, refusals included. The fix is
one expression in `tools/sync_from_drive.py`'s `main()`, outside `sync.ps1`. Not applied.

**B2 — DONE, pure report, no files touched.** For the three differing `handoff_inbox` files —
comparing `D:\claude-googledrive-sync\momentum-inbox-handoff` against the tracked repo copies —
the subagent reported per-file timestamps, line-diff counts, and first-differing lines (full
detail in its transcript; not restated here since this note does not resolve any of the three,
matching the task's own instruction to report and stop). No file was overwritten and no winner
was picked.

**B3 — REFUSED for the mechanism; DONE for the reportable half.** Confirmed in
`tools/sync_from_drive.py`'s `sync_pair()`: it only checks whether a same-named file already
exists in the pair's destination folder before copying from Drive — it has no concept of a
sibling `christoph/done/` folder, so a retired file (copied to `done/`, then deleted from
`open/`) is indistinguishable, to the copier, from one never delivered, and Drive's still-present
original gets copied back in. The fix needs a new, generically-applied `checks:` value (e.g.
`retired_in_sibling_done`) in `sync_pair()` plus an entry in `config/sync.yaml`'s `christoph_open`
pair — both outside `sync.ps1`. Not implemented. The reportable half (current basenames present
in both `christoph/open/` and `christoph/done/` right now) found four candidates; two —
`032-for-christoph-decision-gapped-over.md` and
`034-for-christoph-decision-the-rolling-window-unit.md` — are confirmed resurrections by git history
(034's own commit message: *"034 template reappeared (OBS-077 pattern)"*); the other two —
`035` and `036` — are ambiguous from a single snapshot (could equally be Christoph's
copy-verify-retire caught mid-cycle) and reported as such rather than asserted as bugs. **This
whole finding corroborates `OBS-077` (already OPEN, review-by 2026-11-22) rather than adding a
new one.**

## Part C — `export-handoff.ps1`

**DONE.** Self-contained, no wrapper problem. Added `$headForManifest` and `$dirtySection`,
both derived from the existing `$dirty` array (never re-derived independently, so they cannot
disagree with `$treeState`, which uses the same array). When clean, both reduce to exactly the
pre-existing output (`$headForManifest` equals `$head`; `$dirtySection` is empty) — verified by
direct evaluation of the conditional with `$dirty = @()`, confirming byte-identical output to
before the change in the clean case. When dirty, the `**HEAD**` line itself now carries the
count (`$head + N uncommitted paths (listed below)`) and a new `**uncommitted paths** (N)`
section lists every path by name, immediately before `**files**`.

**Verified against a real export run**, not a synthetic one — the tree was already naturally
dirty (10 paths, from this task's own concurrent subagents and other unrelated activity) at the
moment the subagent ran `export-handoff.ps1` for real, against the actual Drive destinations.
The resulting manifest at
`D:\claude-googledrive-sync\momentum-code-handoff\MANIFEST-momentum-code-handoff.md` reads:

```
**HEAD** 5205af397e978851a2d75ec84f9c644abecc8ba4 063: precondition failed — tree was dirty before this session touched it + 10 uncommitted paths (listed below)
**working tree** DIRTY -- 10 uncommitted paths
**uncommitted paths** (10)
- `M christoph/done/032-for-christoph-decision-gapped-over.md`
- `M christoph/done/035-for-christoph-task-claude-permissions-and-databento-history.md`
- `M docs/observations/OBSERVATIONS.md`
- `M export-handoff.ps1`
- `M sync-run-record.md`
- `M verify.ps1`
- `?? christoph/done/037-for-christoph-task-second-checkout-and-its-deny.md`
- `?? handoff/done/063-quiet-tree-reverify.md`
- `?? handoff/inbox/063-for-code-task-quiet-tree-reverify.md`
- `?? handoff/inbox/064-for-code-task-instrument-batch.md`
**files** 159 (2 copied, 157 unchanged)
```

The count (10) matches the listed items exactly, and `export-run-record.md` is correctly absent
(the pre-existing carve-out for the export's own run-record file still applies). No test in this
repo asserts the exact prior wording of `**HEAD**`/`**working tree**`, and `verify.ps1`'s own
manifest-reading regex (`(?m)^\*\*HEAD\*\*\s+(.+?)\s*$`) captures to end-of-line, so this change
needed no corresponding edit there.

## Part D — `tests/test_task_file_shape.py`

**DONE.** Factored the three affected tests' shared per-file frontmatter parse into
`_load_frontmatter(p, problems)`, which catches `yaml.YAMLError` and records a named violation
(`"{filename}: frontmatter is not valid YAML ({error}) -- cannot check ..."`) instead of letting
the exception abort the loop; also converts the "no frontmatter" case from an aborting `assert`
into the same accumulate-and-continue shape. Each of the three tests now collects every
violation across every file in one pass and asserts once at the end, joining all messages.

**Seen aborting, before the fix**: `tests/test_task_file_shape.py -v` showed a bare
`yaml.scanner.ScannerError` traceback on `056`, not a violation list. **Seen reporting two
violations from two scratch files in one run, after the fix**: a new test,
`test_malformed_frontmatter_is_a_named_violation_not_an_abort`, builds two files under
`tmp_path` — one reproducing `056`'s unquoted-colon shape, one syntactically valid but carrying
`class: nonsense` — and asserts both surface together from a single call. Confirmed independently
by re-running the whole file directly (not just trusting the subagent's report): 6 tests, 3
pass, 3 fail — and the 3 failures are now clean `AssertionError`s naming files, not tracebacks.

**Newly-surfaced real violations against the live `handoff/inbox/`** (previously invisible
because the loop aborted at `056`; the task's own estimate of "twelve" files unchecked was high —
the guard's fix only exposes the tail sorting after `056`, i.e. `057`–`064`, of which two fail):

1. `056-for-code-task-two-false-guards.md` — invalid YAML (`Rule 16: this counts in the...`,
   unquoted colon). Already tracked as `OBS-080`; not fixed here, per that observation's own
   ruling.
2. `062-for-code-task-tws-order-test-instrument.md` — **newly discovered by this fix**: its
   frontmatter block is inside a fenced markdown code block rather than the `---`-delimited
   block every other task file uses, so `_FM` never matches it at all and it is treated as
   having no frontmatter. Not fixed here — `062` is another task's already-merged file, and
   `handoff/` is copy-and-keep.

`057`–`061`, `063`, `064` all parse and pass all three checks.

---

## An unrelated regression found by the full-suite run, not fixed, logged as OBS-082

Running the full suite (not the targeted per-part runs above) surfaced two failures beyond the
known-12 baseline: `test_adoption_log_complete.py::test_every_tracked_file_is_accounted_for` and
`test_donenote_bugs_block.py::test_every_done_note_in_scope_carries_a_bugs_block`. Both trace to
task `058` (already merged at commit `02d4083`, before this task started): two new files under
`live/tests/` (`test_attaching_state.py`, `test_pacing_guard.py`) with no `ADOPTION-LOG.md` row,
and `handoff/done/058-attach-latency-and-attaching-state.md` with no `bugs:` frontmatter key.
**Not caused by any of this task's four parts** — confirmed by checking each part's actual diff
before writing this note. Logged as `OBS-082`, not fixed — `058`'s files are another task's
already-merged work, the same reasoning `061` §6 already applied to its own new files, and
`064`'s scope is the four named files, not a general sweep.

## `docs/observations/OBSERVATIONS.md`'s working-tree diff was not entirely this task's

Before this task's own `OBS-082` edit, `OBSERVATIONS.md` already carried an uncommitted update
from task `058`/`062` (promoting `OBS-041` and `OBS-079` to reflect `058`'s merged fix, and
adding `OBS-081`, `062`'s own finding about concurrent-session collision) — none of it written
by this session, all of it complete and consistent with already-merged code, none of it
in-progress work at risk of being lost. Rather than leaving that dangling indefinitely, this
task's commit includes it alongside its own `OBS-082` addition, since splitting one file's
working-tree diff into "whose part" by hand is not something `git add` can do and the content is
finished, not contested. Flagged here rather than silently folded in.

---

## Full-suite comparison to the known-12 baseline

Before this task (per `061`/`062`'s recorded baseline): 12 failed, of which 3 were
`test_task_file_shape.py`'s abort-shaped failures. After this task's four parts plus the
`OBS-082` addition: the same 9 non-`test_task_file_shape.py` pre-existing failures, the same 3
`test_task_file_shape.py` tests still fail — now for the correct, named reason instead of an
abort — plus the 2 new-but-pre-existing `058`-caused failures named above (not this task's).
**14 failed, 545 passed** overall; **no test that was passing before this task is failing now.**

---

## Exit tests

| test | result |
|---|---|
| Each of A–D lands or refuses with a stated reason; a refusal does not block the others | **true** — A3 and all of B refused; A1/A2/C/D landed; one commit contains everything that landed |
| D seen reporting two violations from two scratch files in one run, having first been seen red as a single abort | **true** — confirmed independently, not just on the subagent's word |
| B's run record shows a `refused` count separate from `last_success`, demonstrated against the current three | **already true before this task** — `refused` already exists per-pair in the record (task `056`); the remaining bug (`last_success` gating) was investigated and refused, not fixed |
| C's manifest names the dirty paths individually — verified by exporting from a deliberately dirty tree | **true** — real export run, quoted above |
| A1 states what was observed, not what was assumed | **true** — empirical parser test, real `powershell.exe` 5.1, before applying the fix |
| `handoff/done/063-*.md` exists | **true** — written separately, this task's Part 0 |

**Refusal exit test** ("a subagent that would need to write outside its one file stops and says
which file and why") fired for real on A3 and B1/B3, each stating the exact file and mechanism
needed. **A1 with no confirmed cause would have been a pass too** — not needed here, since the
BOM hypothesis was confirmed.

**UAT (Christoph).** §7 asks to read the four `NOW.md` numbers, specifically the second one.
**This cannot be done as written** — A3 was refused, so `claude/NOW.md` still renders the single
`admin:product this stretch N:M` line. A future task implementing A3 in `tools/now.py` is a
precondition for this UAT.

---

## The closing sequence

**Parent session only, after all four parts reported.** Per `CLAUDE.md`, from the main checkout.
One commit contains everything that landed: Part 0's `063` closure, Parts A/C/D's edits, and the
`OBS-082` addition (with the caveat above about `OBSERVATIONS.md`'s pre-existing content riding
along).

- **`sync.ps1` was not run by this task** (matching `063`'s own instruction: it changes the tree,
  which would defeat comparability — though this task's subject is different files, the
  instruction was followed for consistency and because Part B was mid-investigation of exactly
  that tool).
- **`verify.ps1` runs last and is the version this task just modified** (Part A's BOM fix). A run
  of it here is not independent evidence about `verify.ps1` itself — it confirms the suite and
  the tree, not that the BOM fix works under Windows PowerShell 5.1, which was already confirmed
  directly against the live 5.1 parser in Part A.
- **`export-handoff.ps1` runs after the commit**, so its manifest HEAD is that commit.
- **Pushed to `origin` (`trading-terminal`).**

---

**This note needs to be pasted to chat**, alongside `handoff/done/063-quiet-tree-reverify.md`.
