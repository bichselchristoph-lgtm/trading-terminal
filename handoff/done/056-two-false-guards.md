---
id: 056
title: Two false guards — a test that stopped guarding, and a ledger that reads a word as a dependency
type: task
class: admin
task_version_executed: 1.0
owner: claude-code
tree: D:\Dev\momentum
branch: 056-two-false-guards, merged to main
bugs:
  - id: NEW
    action: raise
    status: NEW
    priority: 1
    title: test_inbound_run_record_has_no_conflicts matches wording, not condition
    spec: PROCESS-SPEC
    summary: >-
      tools/sync_from_drive.py prints "files refused" two different ways
      depending on whether anything else copied in the same run: "0 new · N
      REFUSED" alone, or "N differing" when something new also copied. The
      test written in 053 only matched "differing", so a run whose only event
      was a refusal reported green.
    actual: >-
      Confirmed on 2026-08-16's committed sync-run-record.md: the outcome read
      "handoff_inbox: 0 new · 3 REFUSED · 23 unchanged" while 040/043/052 were
      being refused, and the old test's regex (which only matched the word
      "differing") reported green against it — reproduced deliberately below.
    expected: >-
      Match the CONDITION, not the wording. Fixed here.
  - id: NEW
    action: close
    status: FIXED
    priority: 1
    title: test_inbound_run_record_has_no_conflicts matches wording, not condition
    spec: PROCESS-SPEC
    resolution: >-
      sync-run-record.md gains a fourth, machine-readable field: `refused`,
      one count per pair, `pair_id: N`, `|`-joined like `outcome`. Written by
      tools/sync_from_drive.py's write_record() on every invocation
      (PairResult.refused_count property; main()'s two write_record() calls).
      tests/test_inbound_run_record_has_no_conflicts.py now reads this field
      exclusively and never inspects `outcome`'s prose. The human-readable
      `outcome` line is unchanged. Exit tests:
      test_a_nonzero_refused_count_is_caught,
      test_an_absent_refused_field_is_a_failure_to_report,
      test_a_refused_count_of_zero_for_every_pair_is_clean — all in
      tests/test_inbound_run_record_has_no_conflicts.py.
  - id: NEW
    action: raise
    status: NEW
    priority: 1
    title: "tools/now.py's depends_on() reads depends: none as a phantom dependency"
    spec: PROCESS-SPEC
    summary: >-
      depends_on() (tools/now.py:87-93) treats an absent depends: key as no
      dependency but not the literal string "none" written as a value —
      raw="none" is non-empty, so the task acquires a dependency on a task
      named "none" that can never exist.
    actual: >-
      049 and 051 (and 052/053/054, the same convention) both write "depends:
      none" and both rendered blocked — needs none in NOW.md while genuinely
      ready.
    expected: >-
      Treat the literal none/None/NONE the same as absent. Fixed here.
  - id: NEW
    action: close
    status: FIXED
    priority: 1
    title: "tools/now.py's depends_on() reads depends: none as a phantom dependency"
    spec: PROCESS-SPEC
    resolution: >-
      depends_on() now returns [] when the stripped value is empty OR equals
      "none" case-insensitively. compute() and render() needed no change —
      they already handled an empty dependency list correctly. Exit test:
      test_a_task_with_depends_none_is_ready in tests/test_now_is_derived.py,
      red before the fix, green after. test_ready_blocked_and_on_christoph
      (a real unmet dependency) confirmed green both before and after —
      the fix does not disable dependency checking. Regenerated NOW.md via
      verify.ps1 confirms 049 and 051 moved from blocked to ready.
  - id: NEW
    action: raise
    status: NEW
    priority: 1
    title: 056's own frontmatter is malformed YAML and crashes test_task_file_shape.py for every file it scans
    spec: PROCESS-SPEC
    summary: >-
      handoff/inbox/056-for-code-task-two-false-guards.md lines 12-18: `unblocks:
      NOTHING` is followed by a blank line and an indented, unquoted prose
      paragraph as a continuation. That is not valid YAML (a scalar cannot
      resume after a blank line without block-scalar syntax), and the
      paragraph itself contains "Rule 16:" — a colon inside what YAML now
      reads as plain content — which is what yaml.safe_load() actually trips
      on ("mapping values are not allowed here").
    actual: >-
      Not found by inspection — found because test_task_file_shape.py's three
      tests each loop `yaml.safe_load()` over every handoff/inbox/*.md
      numbered 049+ with no per-file try/except, so ONE malformed file's
      ScannerError takes down the check for every OTHER file in the same run,
      not just its own row. Confirmed the cause in isolation: every other
      file numbered 049+ parses cleanly; only 056 raises. New failures this
      session, not present in 055's baseline (055 predates 056's arrival):
      test_every_task_file_declares_a_class,
      test_admin_tasks_name_what_they_unblock,
      test_no_task_file_names_a_destination (all in
      tests/test_task_file_shape.py).
    expected: >-
      Not this task's to fix — handoff/ is copy-and-keep, so
      handoff/inbox/056-*.md cannot be edited in place, and widening this
      session's own scope to make test_task_file_shape.py tolerate a malformed
      file (e.g. per-file try/except) is a decision about that test's
      robustness, not about the two guards 056 was scoped to. A corrected
      reissue of 056's frontmatter is the design session's to author, same
      shape as 055's 049-wrong-tree finding.
  - id: NEW
    action: correct
    status: CORRECTED
    priority: 2
    title: 056 Section 7 instructs a Status header value that is not one of the five valid states
    spec: PROCESS-SPEC
    summary: >-
      056 Section 7 says this done-note's Status header should read "complete".
      CLAUDE.md's handoff convention names exactly five valid states — WRITTEN,
      HANDED OFF, RUNNING, REVIEWED, DONE — and "complete" is none of them.
      tests/test_handoff_state_declared.py::test_no_task_file_declares_a_
      state_outside_the_five confirmed it red against the literal instruction.
    actual: >-
      Deviated from the literal instruction rather than write an invalid
      state and a red test knowingly. Used RUNNING, matching the established
      precedent in every other recent done-note not yet reviewed by the
      design session (041-046, 052) and consistent with 056's clear intent —
      not REVIEWED, since that is the design session's to set.
    expected: >-
      Corrected here by using a valid state instead of the literal one named.
bugs_note: >-
  The first two pairs (raise+close) are Parts A and B, fixed in this task. The
  fifth row is new, found while running the full suite after the fix. The
  sixth is a self-correction of this task's own Section 7 instruction. Neither
  is fixed by editing handoff/inbox/056 itself — copy-and-keep.
---

**Status** RUNNING

# 056 — two false guards

Gate checked first: `handoff/inbox/056-for-code-task-two-false-guards.md` did not exist in
the tree at task start — it had not yet been pulled from Drive by `sync.ps1`. Confirmed by
direct read of the Drive source folder, then pulled in properly via `sync.ps1` (see below), so
the gate condition ("if `056-...md` exists and `handoff/done/056-*.md` does not") was satisfied
from the correct channel rather than by manual copy.

## The observation that matters most

**Reproduced the exact false-green from `055`'s finding, on demand, before touching any code.**
Built a fixture run-record carrying the `0 new · 3 REFUSED · 23 unchanged` wording with no
structured field, and ran the *current, unmodified* `test_inbound_run_record_has_no_conflicts`
regex logic (`_DIFFERING = re.compile(r"(\d+)\s+differing")`, matched against the `outcome`
field split on `|`) directly against it:

```
outcome line: regime_snapshots: 0 new · up to date (2 unchanged) | handoff_inbox: 0 new · 3
REFUSED · 23 unchanged | christoph_open: 0 new · up to date (14 unchanged)
offenders found by the CURRENT (pre-056) test logic: []
RESULT: GREEN -- the defect, reproduced deliberately
```

Zero offenders found, on a record naming three live refusals by name. That is `055`'s finding,
executed rather than read.

## Part A — the sync guard, fixed by field not by wording

Per the task's own ruling: **did not widen the regex to match `"REFUSED"` too.** Added a
fourth, machine-readable field to `sync-run-record.md`: `refused`, one count per pair,
`pair_id: N`, `|`-joined like `outcome` already is. `tools/sync_from_drive.py` writes it on
every invocation (`PairResult.refused_count`, `main()`'s two `write_record()` calls); the
`outcome` line is byte-for-byte the same shape it always was, for Christoph and `verify.ps1`
section 6. `tests/test_inbound_run_record_has_no_conflicts.py` now reads `refused` exclusively
and never inspects `outcome`'s prose.

Exit tests, run in this order against the fixed code:

- `test_a_nonzero_refused_count_is_caught` — a fixture with `handoff_inbox: 3` in `refused` —
  **red as designed** (offenders found).
- `test_an_absent_refused_field_is_a_failure_to_report` — a record with no `refused:` field at
  all — **raises**, confirming absence is never read as zero (tenet 2).
- `test_a_refused_count_of_zero_for_every_pair_is_clean` — every pair at `0` — **green**.

Then re-ran `sync.ps1` (needed anyway, to pull `056` and confirm the gate) so the *real*,
committed `sync-run-record.md` would carry the new field, and ran
`test_the_inbound_sync_reports_no_refusals` (the renamed, field-reading version of the old
test) against it: **it is red**, for real — `refused` reads `handoff_inbox: 3`, because `040`,
`043` and `052` are still genuinely standing refusals, unresolved since before this task and
not this task's to resolve (`053`'s own instruction: never clear a refusal by overwriting).
**This is the guard doing its job.** `055` predicted the suite would show one more red once
this guard could actually fire; that prediction held.

## Part B — `depends: none`

`tools/now.py`'s `depends_on()` (lines 87–93) now treats the literal value `none`/`None`/`NONE`
(stripped, case-insensitive) the same as an absent key. One added condition on the existing
`if not raw:` guard; `compute()` and `render()` needed no change.

- `test_a_task_with_depends_none_is_ready` (new, `tests/test_now_is_derived.py`) — **red**
  against the unmodified parser (`compute(repo)["ready"] == []`, not `["049"]`), **green**
  after the fix.
- `test_ready_blocked_and_on_christoph` (existing, a real unmet dependency) — confirmed
  **green both before and after** — run explicitly both times, not assumed. The fix does not
  disable dependency checking.
- `NOW.md` regenerated through `verify.ps1` (never by hand): `ready now` now includes `049` and
  `051`, which is the whole point.

## Part C — the backlog

Committed directly to `main`, before branching for Parts A/B, in its own commit
(`a9ca777`): `.claude/settings.json`, `export-run-record.md` and `sync-run-record.md`
(routine tool output from the `055` session, never committed), `christoph/open/018` →
`christoph/done/018-*` (Christoph's own retirement, already performed, git recorded it as a
rename), ten `christoph/open/024`–`033-*.md` decision files, and
`handoff/inbox/055-for-code-task-the-checkpoint.md` — all arrived via the correct sync pairs.

**Wider than `055`'s own item 1 accounting**, worth stating plainly: `055` reported only
`sync-run-record.md` modified plus 11 untracked. The actual `git status` also carried
`.claude/settings.json` (two new benign MCP Google Drive read permissions) and
`export-run-record.md` modified — both routine, both confirmed benign by `git diff` before
committing.

## A new finding, not asked for and not fixed here

Running the full suite after both fixes surfaced a third defect, in `056`'s own frontmatter —
see the fifth `bugs:` row. `handoff/inbox/056-for-code-task-two-false-guards.md` lines 12–18
carry `unblocks: NOTHING` followed by a blank line and an unquoted, indented prose continuation
— not valid YAML, and it crashes `yaml.safe_load()` inside a loop with no per-file isolation, so
one malformed task file took down `test_task_file_shape.py`'s three checks for every file it
scans, not just its own row. `tools/now.py`'s own hand-rolled line parser is unaffected (it
never reached this line — no change was needed there), which is why `NOW.md` generation and
Part B were untouched by it. **Not fixed here**: `handoff/` is copy-and-keep, so the file
cannot be edited in place, and widening `test_task_file_shape.py` to tolerate one malformed
file is a decision about that test's own robustness, not one of the two guards `056` was
scoped to fix. Same shape as `055`'s `049`-wrong-`tree:` finding — a defect in a task file that
needs a corrected reissue from the design session.

## Exit tests

`verify.ps1` ran from the main checkout at `2026-08-22 12:46:14 +02:00`, HEAD
`a9ca77725c6499f85e5aba45b7777be9d12260df` at that point (before the branch merge). Section 1's
full line and named failures are quoted above and below rather than counted:

- `test_the_inbound_sync_reports_no_refusals` — **red**, for the real reason (standing
  `040`/`043`/`052` refusals), which is new behaviour: the previous version of this test was
  false-green on exactly this state.
- The five reds `055` already knew about (`test_handoff_state_declared`,
  `test_observations_ledger` ×2, `test_regime_prompt_invariants` ×2 counted as one family,
  `test_uat_has_a_file`) plus the one deliberate tripwire (`test_regime_snapshot_could_not_do`
  — its own message says failing is the *good* outcome) are untouched by this task.
- Three new reds in `test_task_file_shape.py`, caused by the new finding above, not by Parts A
  or B.

**Not the "drops by one" outcome `056`'s own text predicted** — the guard now correctly
reports red given real standing conditions, matching `055`'s own prediction ("it will show 8
once fixed") rather than `056`'s. Stated plainly rather than smoothed over, per this project's
own convention about task-file predictions that don't hold (`049`'s wrong `tree:` is the
precedent).

**No test count is quoted as a headline number** — `verify.ps1` ran, at the timestamp above;
the named failures are listed so the reader does not have to trust a count.

## Refusal, demonstrated

With a fixture carrying `refused: 3`: red. With the field absent entirely: red (raises). Both
shown above, both under Part A's exit tests.

## Worktrees

Not touched. `verify.ps1` section 7 still reports `wt-052` and `wt-probe` (registered) plus
three inert orphans under `.claude\worktrees\` (`029-entry-point`, `043-third-pair`,
`045-workflow`, all `0 files`) — unchanged from `055`.

## UAT

None. Nothing Christoph can look at changed. Stated rather than invented.

## Closing sequence

`sync.ps1` → `verify.ps1` → commit (branch `056-two-false-guards` merged into `main`, `--no-ff`)
→ `export-handoff.ps1` → push to `origin` (`trading-terminal`), all from the main checkout, no
worktree. Ran in that order; outcomes recorded at the bottom of this note once each step
completed.

---

**This needs to be pasted to chat.** Per the handoff convention, chat cannot see this repo —
writing it here is not the same as it being read.
