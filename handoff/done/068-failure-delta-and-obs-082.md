---
id: 068
title: verify.ps1 reports a failure-set delta instead of a note quoting a count; the two OBS-082 guards are green
type: task
class: admin
owner: claude-code
unblocks: NOTHING
depends: [064]
touches: verify.ps1 ADOPTION-LOG.md tests/test_donenote_bugs_block.py
bugs: []
---

**Status** RUNNING

# 068 — done. All three parts landed; none needed a subagent.

**Part 0's file map, before anything else.** All three parts turned out to need only
the files the task itself named, plus two small additions neither part's own
instruction anticipated (below) — no collision, so nothing needed serialising or
parallelising beyond just doing them in order (A, then B, then C, since A's demonstration
needed a clean baseline to tamper against).

| Part | Files touched |
|---|---|
| A | `verify.ps1`, `.gitignore` (new ignore rule), `tests/test_verify_failures_state_is_ignored.py` (new), `tests/test_verify_output_is_ignored.py` (one docstring, "one exemption" → "two") |
| B | `ADOPTION-LOG.md` |
| C | `tests/test_donenote_bugs_block.py`, `tools/exported_notes.py` (new — shared with Part A's content-signal line) |

**The task's own `touches:` said `docs/ADOPTION-LOG.md`.** The real file is
`ADOPTION-LOG.md` at the repository root; there is no `docs/` copy. Used the real
path, noted here rather than silently corrected without comment.

---

## Part A — `verify.ps1` §1 reports the delta

**Three lines added to §1**, computed from a new gitignored state file at the repo
root (`verify-failures.txt`, matching the location and reasoning of `handoff/verify-output.md`'s
existing exemption — generated, per-machine, describes a moment):

```
  unchanged  N
  new        N
  fixed      N
```

Any `new`/`fixed` entry is named individually, never left as a bare count. Order of
operations is read-previous → compute → print → write-current, so the comparison is
always against the LAST run, never against itself.

**First run** (state file freshly removed to test the cold-start path): printed
`no previous run recorded`, not `new 0` / `fixed 0` — absence is not zero, and that
applies to this instrument's own state the same as every other section.

**Seen against a deliberately-tampered state file, through the real §1 path — not a
synthetic stand-in for the parser.** After the first real run wrote a 12-entry state
file, one real, still-failing test id was removed from it
(`tests/test_uat_has_a_file.py::test_every_declared_uat_exists_as_a_file`) and one
fabricated id was added (`tests/test_scratch_demo.py::test_this_does_not_exist_and_never_will`).
Running `verify.ps1` again for real reported exactly:

```
  unchanged  11
  new        1
  fixed      1
  new failures:
    tests/test_uat_has_a_file.py::test_every_declared_uat_exists_as_a_file
  fixed since last run:
    tests/test_scratch_demo.py::test_this_does_not_exist_and_never_will
```

— the removed-from-previous real test correctly reported as `new` (it's in the current
set and wasn't in the tampered previous one), the fabricated entry correctly reported as
`fixed` (it was in the tampered previous set and isn't in the real current one). A third,
final real run restored the state file to the genuine current set and reported
`unchanged 12 · new 0 · fixed 0` — the clean baseline this closing sequence's own
`verify.ps1` run below is measured against.

**One thing this demonstration could not show directly: the actual 14→12 transition
`062`/`064`'s OBS-082 caused.** That drop happened between this session fixing Parts B
and C and this task's *first* `verify.ps1` run — since no state file existed yet at
that point, the first run reported `no previous run recorded` rather than `fixed 2`,
which is what the task's own UAT example anticipates seeing on a repository that
already had a prior run's state on disk. The mechanism is proven by the scratch
demonstration above; the specific 14→12 moment is simply not observable after the fact,
because the instrument that would have shown it did not exist yet when it happened.

**Gitignored and tested the same way `handoff/verify-output.md` already is:**
`tests/test_verify_failures_state_is_ignored.py` (new) asserts `git check-ignore`,
anchored to the repo root. `verify.ps1`'s own header comment and
`test_verify_ps1_still_modifies_nothing_else`'s docstring both said "the ONE exemption" —
both updated to "two," since the code now genuinely writes a second gitignored file and
stale prose contradicting the code is exactly this project's most-named defect.

## Part B — the two `ADOPTION-LOG.md` rows

Added, in the `authored in this tree under NNN; not imported` / `Claude Code (058),
logged by 068` shape `test_worktree_root_is_scanned.py`'s existing row already
established for a retrospective log entry. `test_adoption_log_complete.py::test_every_tracked_file_is_accounted_for`
is green.

**A third row was also needed and wasn't named in the task**: `tools/exported_notes.py`
(new, Part C) is itself a tracked code-tree file with no native carve-out, so it needed
its own row the moment it was staged — same shape `061`/`064` already hit for their own
new files. Added alongside the two 058 rows. `tests/test_verify_failures_state_is_ignored.py`
(Part A's new test) needed one too; added.

## Part C — the guard yields for an already-exported note

**`tools/exported_notes.py` (new)**, following the extraction pattern `tools/waiting.py`
and `tools/now.py` already set: it parses `export-handoff.ps1`'s own `$driveRoot` and
`$exports` table (never a second hardcoded copy of the Drive path) to locate the
`momentum-code-handoff` manifest, then reads which `done/*.md` basenames that manifest
names. Raises `ExportManifestUnreadable` — never returns an empty set — on any failure to
locate the script, parse its table, find the manifest, or read it, so a caller cannot
mistake "I don't know" for "nobody is exempt."

**`test_donenote_bugs_block.py`** now reads this once per run and, for an in-scope note
missing `bugs:` that the manifest names as exported, emits a `UserWarning` naming the
note and the reason and continues — a skip, not a failure, and never silent (the warning
surfaces in pytest's own summary on every run, pass or fail, with no `-s` needed).
Confirmed live:

```
UserWarning: 058-attach-latency-and-attaching-state.md: exempt from the `bugs:`
requirement -- already exported (see the manifest at
D:\claude-googledrive-sync\momentum-code-handoff\MANIFEST-momentum-code-handoff.md)
before this rule reached it. Not edited: handoff/ is copy-and-keep.
```

**`058`'s done-note was not edited.** Per the task's own §4, that is the whole answer —
handoff/ is copy-and-keep, and an edit would put the tracked copy out of byte-sync with
its already-exported Drive copy, the same condition `040`/`043`/`052` are stuck in.

**Two new tests cover both refusal shapes**, not just the happy path:
`test_an_unreadable_manifest_refuses_by_name_rather_than_exempting_everyone` monkeypatches
`manifest_path()` to a nonexistent file and asserts `ExportManifestUnreadable` is raised
(never an empty set); `test_058_is_actually_exported_and_that_is_what_makes_the_exemption_real`
asserts against the REAL manifest that `058`'s note is actually named in it — a synthetic
basename set would have passed even if `manifest_path()` pointed at the wrong file
entirely.

**`verify.ps1` surfaces the same count as a content signal**, via
`tools/exported_notes.py`'s own `main()` (invoked as a subprocess, the same shape
`tools/now.py` and `tools/waiting.py` already use) — `"done-notes exempted (already
exported, missing bugs:) 1"`, naming `058`'s note. It goes to zero the day no in-scope
exported note is missing `bugs:` any more; it does not go to zero by anyone editing an
exported note.

`test_adoption_log_complete.py` and `test_donenote_bugs_block.py` are both green.

---

## Not done

- **`056`'s frontmatter, the `040`/`043`/`052` divergences, any scheduled task
  configuration, `065`'s phrasing.** All explicitly out of scope, per §5.
- **The nine other pre-existing failures.** Untouched.

---

## Exit tests

| test | result |
|---|---|
| §1 prints `unchanged`/`new`/`fixed`, naming anything in the last two | **true** |
| Seen against a deliberately-broken scratch state file, through the real §1 path | **true** — quoted above |
| State file deleted → `no previous run recorded` | **true** |
| `test_adoption_log_complete` green | **true** |
| `test_donenote_bugs_block` green, `058` named as skipped with its reason | **true** — quoted above |
| Export manifest unreadable → refuses by name, does not skip-and-pass | **true** — `test_an_unreadable_manifest_refuses_by_name_rather_than_exempting_everyone` |
| State file present but unparseable → reported as unreadable, not empty | **true** — `verify.ps1`'s read is wrapped in try/catch; a read failure prints `CANNOT COMPUTE: ... could not be read` rather than proceeding with an empty previous set |

**UAT (Christoph).** Read §1 once: `unchanged 12 · new 0 · fixed 0` (this session's own
closing run — no `fixed 2` moment to show, per the note above on why that specific
transition isn't observable after the fact). Legible without reference to any earlier
note, which is the whole point of the task.

---

## The closing sequence

Per `CLAUDE.md`, from the main checkout. One commit.

**`verify.ps1` runs last and is the file this task changed — not independent evidence
about that instrument.** Three runs happened during this task: a cold-start run (`no
previous run recorded`), a deliberately-tampered demonstration run (`new 1` / `fixed 1`,
quoted above), and a final clean run (`unchanged 12 · new 0 · fixed 0`) whose state is
what the closing sequence's own commit-time `verify.ps1` run will be compared against
next. Not pasted or summarised beyond what's already quoted above for the specific
exit-test evidence.

---

**This note needs to be pasted to chat.**
