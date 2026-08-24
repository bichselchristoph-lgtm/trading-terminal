---
id: 086
title: Twelve guards have been red long enough to stop being read — list every offender, fix nothing
type: task
class: admin
unblocks: NOTHING
story: none
owner: claude-code
depends: none
touches: nothing — no file is edited by this task
---

**Status** WRITTEN

# 086 — what is actually failing, named file by file

**List. Do not fix.** Not one file is edited by this task, including files that
are obviously wrong.

**`unblocks: NOTHING` is honest.** No product task waits on this. It exists
because **twelve tests have reported `unchanged 12` on every run for days**, and
a test that is permanently red has stopped carrying information — the same
defect as one that is permanently green.

---

## 0. Is this task for you

**If `handoff/inbox/086-for-code-task-triage-the-twelve.md` exists in your tree
and no file beginning `086-` exists in `handoff/done/`, this task is for you.
Otherwise stop reading and ignore this message.**

---

## 1. The twelve

```
tests/test_export_scope_is_derived.py::test_destination_contains_nothing_outside_its_source[1]
tests/test_handoff_state_declared.py::test_every_task_file_declares_a_state
tests/test_inbound_run_record_has_no_conflicts.py::test_the_inbound_sync_reports_no_refusals
tests/test_observations_ledger.py::test_every_retired_uat_has_a_register_row
tests/test_observations_ledger.py::test_refusal_b_a_retired_uat_with_no_destination_is_red
tests/test_regime_prompt_invariants.py::test_no_bare_six_of_nine
tests/test_regime_prompt_invariants.py::test_no_bare_six_of_nine_anywhere_in_specs
tests/test_regime_snapshot_could_not_do.py::test_the_format_still_lacks_a_key
tests/test_task_file_shape.py::test_every_task_file_declares_a_class
tests/test_task_file_shape.py::test_admin_tasks_name_what_they_unblock
tests/test_task_file_shape.py::test_no_task_file_names_a_destination
tests/test_uat_has_a_file.py::test_every_declared_uat_exists_as_a_file
```

---

## 2. What to produce, per test

**For each of the twelve, in the done-note:**

1. **What it asserts**, in one sentence, read from the test rather than from
   its name. **A test's name is a claim about the test, not a reading of it** —
   `test_the_format_still_lacks_a_key` in particular reads as though red is its
   intended state, and that needs confirming or denying by reading the body.
2. **Every file that fails it, listed by path.** Not a count. **A count cannot
   be acted on and cannot be checked.**
3. **Which of three buckets it falls in:**

| Bucket | Meaning |
|---|---|
| **Fixable** | A real defect in a file that can be edited. Name the file and what is wrong |
| **Frozen** | The offender is in `handoff/`, which is copy-and-keep. **The file cannot be edited and the test can never go green as written** |
| **Wrong test** | The assertion no longer matches a ruling. Name the ruling |

**The third bucket is the one that matters.** A guard whose premise has been
overtaken keeps a real signal permanently red, and everything behind it stops
being read. **083 already found one of these** — `test_session_basis.py`
asserted `intraday_sessions` fixes its basis *because no caller has a choice*,
which 083's own ruling made false.

---

## 3. Four specific things to check, because each is already suspected

**`test_every_declared_uat_exists_as_a_file`.** Two files in `christoph/open/`
both begin `043-`. One is a stale copy that reached the tree before it was
withdrawn from Drive. **Report both paths. Do not delete either** — deletion is
Christoph's alone, by mechanism, and this task has no delete.

**`test_the_inbound_sync_reports_no_refusals`.** The inbound run record shows
`3 differing` and a last success fifteen hours behind its last attempt.
**Name the three differing files.** That is B-101 and B-108 and neither has ever
had the files named.

**The `test_task_file_shape` trio.** Report whether the offenders are current
task files or historical ones. **If they are historical and frozen, say so
plainly** — it means the guard can never be green and is therefore a permanent
red that hides new breakage behind it.

**`test_every_retired_uat_has_a_register_row`.** Christoph retired several UATs
today. Report whether the register is behind, or the test is.

---

## 4. One thing that is not on the list, and belongs in the same note

**`NOW.md` reports `h084` as done. Task 084's own done-note reports
`Status RUNNING`** and states that its live measurement was not taken because
TWS was unreachable.

**Read how `NOW.md` derives `done`.** If it is *a file exists in
`handoff/done/`* rather than *that file says DONE*, then **a task that
correctly reported itself unfinished is being counted as finished, and the owed
measurement is now flagged nowhere.**

**Report what you read. Do not change `NOW.md` or `verify.ps1`.**

---

## 5. What you may NOT do

**Do not edit any file to satisfy any test.** Not one, however obvious.

**Do not delete anything.**

**Do not change `verify.ps1`, `NOW.md`, or any test.**

**Do not mark anything DONE that is not.**

**Any scratch lives in `$env:TEMP`.**

---

## 6. Exit condition

**No Green, Refusal or UAT tests, deliberately: no production code changes and
no behaviour to pin.** The exit condition is the list in the done-note.

**The suite must still report `unchanged 12, new 0, fixed 0` afterwards.** If it
does not, this task changed something it should not have.

`verify.ps1` runs as the last action. Do not paste or summarise it.

---

## 7. The prompt

```
Do inbox 086
```
