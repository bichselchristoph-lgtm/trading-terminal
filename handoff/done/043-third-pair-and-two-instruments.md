---
id: 043
title: A third Drive pair, and two instruments that watch nothing
type: task
class: admin
owner: claude-code
depends: 037
---

**Status** RUNNING

# 043 — done. Three parts, and the new instrument's first output was about itself.

**Section 6 of `verify.ps1` — the inbound sync record this task added — rendered its first
real output as:**

```
outcome      t: 1 new · 031-for-code-thing.md
```

**That is a pytest fixture's filename, describing a copy into a temp directory, in the tracked
artifact whose only job is saying when the real sync last worked.** Every test that drove
`main()` with its own `--config` and no `--record` had been overwriting it. **The defect predates
the section by however long those tests have run, and nothing could see it until the section
existed to print it.** `OBS-064`.

That is `043`'s own subject arriving twice inside `043`.

---

## 1 — did one copier take a third pair without duplication?

**Yes, and nothing about the copier changed to allow it.** `config/sync.yaml` gained a
`christoph_open` pair and `tools/sync_from_drive.py` has no new branch —
`test_the_copier_has_no_pair_specific_branches` still passes, and it parses the module with
`ast` rather than grepping.

**Checks are `[]` for the new pair, deliberately.** `filename_convention` and
`number_collision` encode `NNN-for-code-*.md`, which is the naming for files addressed to
**Claude Code**. `christoph/open/` holds `NNN-*.md` addressed to **a person**, and a convention
check calibrated on one audience would flag every correct file in the other.

**`christoph/done/` is locked by a test now, not by a sentence.**
`tests/test_sync_never_targets_christoph_done.py` refuses any configured pair whose destination
has `christoph/done` as consecutive path components, at any depth.

**Its first version had a hole worth recording.** It resolved the forbidden path as
`REPO / "christoph" / "done"` — and `REPO` is whichever checkout the test runs in. **Run from a
worktree it would have waved through a pair aimed at the main checkout's `christoph/done`, which
is the one holding the real answers.** It now matches on path *shape*, so every checkout is
covered.

---

## 2 — which outcomes could the copier emit before? **Measured, not read.**

Five configs, run against the tool at `9b91ecc` before any edit. **Exit codes taken from the
process, not from the end of a pipe — the first measurement piped into `head` and reported
`head`'s exit code for all five.**

| case | headline emitted | exit |
|---|---|---|
| files to copy | `N new · <names> · 0 differing` | 0 |
| nothing to do | `0 new · up to date (N unchanged)` | 0 |
| source missing | `0 new · source folder UNREACHABLE · <path>` | 1 |
| source empty | `0 new · source folder EMPTY · <path>` | 0 |
| **destination missing** | **none — `FileNotFoundError` traceback** | 1 |

**Destination-unreachable was not an outcome at all.** `dest.mkdir(parents=True)` raised and the
tool died. It exited non-zero **only because an unhandled Python exception happens to exit 1** —
luck, not a contract — and wrote nothing, said nothing a person could act on, and named no pair.

**And a refusal did not have its own sentence.** A run whose only event was a refused file fell
through to `0 new · up to date`. **That is what the `035` collision printed for two days while
exiting 1 on every run.**

**Both are now named outcomes**, and the `EMPTY` case survives as a fifth — `026`'s own
refinement, since an empty folder is a working pipeline with nothing to send and a missing one is
a broken path.

---

## 3 — one run record or two? **Two, and here is the trade.**

`043` left this to my judgement. I kept them separate: `sync-run-record.md` beside
`export-run-record.md`, **same format, same field names, same column-zero convention.**

1. **The writers are in two languages.** `export-handoff.ps1` is PowerShell; the copier is
   Python. One file means two independent implementations of one write-and-parse contract —
   which is the argument `config/sync.yaml`'s own header makes about copiers: *two copies WILL
   diverge.*
2. **A shared file is a shared failure mode.** The export writes its record whole with
   `Set-Content`. A Python writer would have to read-modify-write around it, and a crash
   mid-write would destroy **the other copier's** record — in the one artifact whose entire
   purpose is surviving a crash.
3. `verify.ps1` reading two files is cheap. It already reads two Drive manifests side by side,
   and now prints them as sections 5 and 6.

**Against it:** `043` is right that one file with three sections gives `verify.ps1` one thing to
read, and a reader now has two places to look. **I judged the crash-isolation worth more than the
single read**, because the failure these records exist to catch is precisely a run that died
partway.

---

## 4 — both inbound failure paths, executed, and the record read afterwards

**Source unreachable:**

```
exit=1
last_attempt : 2026-08-15T10:31:07+02:00
last_success : never
outcome      : p: 0 new · source folder UNREACHABLE · ...\043m\nope
```

**Destination unreachable:**

```
exit=1
last_attempt : 2026-08-15T10:31:08+02:00
last_success : never
outcome      : p: 0 new · destination UNREACHABLE · Q:\nonexistent\dst
```

**And the property that matters — a failure must not erase an earlier success.** A run that
succeeded, then a run that failed against the same record:

```
1) a run that SUCCEEDS      exit=0   last_success : 2026-08-15T10:33:05+02:00
2) then a run that FAILS    exit=1   last_attempt : 2026-08-15T10:33:06+02:00
                                     last_success : 2026-08-15T10:33:05+02:00
                                     outcome      : p: 0 new · source folder UNREACHABLE · ...
```

**`last_attempt` moved and `last_success` stood still.** That is the signature `037` wanted and
failed to produce, because it indented its own fields into a markdown code block while its reader
anchored on a bare `^`.

**`043` told me to copy `037`'s remedy, and my first cut copied only half of it.** I put the
fields at column zero and then wrote a test asserting that an *indented* field reads as `never` —
pinning the intolerance as a feature. `037` fixed it **both** ways on purpose and said so:
*"the fields are now at column zero AND the anchor tolerates whitespace; either alone would be
enough, which is the point."* The reader now tolerates leading whitespace and a separate test
asserts the written format stays at column zero. **Half a remedy, asserted as the whole one,
would have left the inbound record one reformat from the outbound record's original bug — with a
green suite, and with the two parsers disagreeing about one format.**

---

## 5 — were `024` and `029` clean, and was anything else touched?

**Both clean, re-checked immediately before acting** — `git status --porcelain` empty in each —
and both branches already merged into `main`, so removing them destroys nothing. Verified twice:
`git branch --contains` names `main` for both HEADs.

> **CORRECTED. An earlier cut of this note said the removals were refused by the permission
> layer and that this was the one part of `043` left unexecuted. They were retried and they
> succeeded.** The paragraph is rewritten rather than annotated because the old text would have
> been read as a standing instruction to somebody else to finish the job.

**Both are removed. `git worktree list` now shows the main checkout and nothing else.**
`tests/test_pytest_collection.py::test_every_directory_holding_tests_is_declared` — red in the
main checkout continuously since 2026-08-13, which is what `OBS-046` is about — **is green:**

```
3 passed in 0.06s
```

**Nothing outside those two was ever a candidate**, and nothing else was removed.

### The removal is not quite clean, and the residue is the interesting part

**`024` was removed outright. `029` was deregistered — checkout gone, every test file gone — but
its now-empty DIRECTORY would not delete:**

```
error: failed to delete 'D:/Dev/momentum/.claude/worktrees/029-entry-point': Permission denied
...
The process cannot access the file '\\?\D:\Dev\momentum\.claude\worktrees\029-entry-point'
because it is being used by another process.
```

Retried through .NET's `Directory.Delete` with the same result. **Not forced, and not retried past
that** — the handle's owner was not identified, and a directory this session cannot account for is
not one it should be deleting sideways.

**Two older empty directories are in the same state**: `017-remote`, which predates everything
here, and `043-third-pair`, this task's own worktree. All three hold **zero files**.

**This is what §6's orphan line was added for**, and it was added *because* of this: see §6a.

---

## 6 — what `verify.ps1`'s worktree line reads

**Measured before the removals, which is the only run in which it had anything to report:**

```
  worktrees         2 - 024-subagent-roster (2d), 029-entry-point (2d)
                    age is the worktree directory's creation time on this disk
                    D:\Dev\momentum\.claude\worktrees\024-subagent-roster
                    D:\Dev\momentum\.claude\worktrees\029-entry-point
```

**That is the exact shape `043` asked for.** After the removals it reads `worktrees 0`, which is
the honest end state and demonstrates nothing — so the populated run is quoted above and both are
stated.

**Age reads 2d, not the three days `043` states.** The worktrees date from 2026-08-13 and today is
2026-08-15; the section reports the directory's creation time on this disk, and the basis is
printed beside it because this project does not render a number without one.

**It removes nothing** — `OBS-036`, and a verification script with a side effect cannot be run to
find out whether something happened.

**Its first cut excluded the main checkout by comparing each entry against `$repo`**, with a
comment claiming this let the script run from any checkout. It does the opposite: `$repo` is
`$PSScriptRoot`, so run from a worktree it excluded **itself** and listed the main tree as
`momentum (5d)`. **Measured, not reasoned about.** The main checkout is now excluded by position —
`git worktree list` always emits it first, from wherever it is invoked. **Same class as
`OBS-045`**: a tool that assumes it is running in the main tree.

---

## 7 — the reds, quoted

**The `christoph/done` guard, seen red by adding a forbidden pair:**

```
AssertionError: these configured pairs write into christoph/done/: ['christoph_done_BAD'].
FAILED tests/test_sync_never_targets_christoph_done.py::test_no_pair_writes_into_christoph_done
1 failed, 5 passed
```

**The run record, seen red by removing it:**

```
AssertionError: ...\sync-run-record.md is missing. It is tracked, not gitignored, so a fresh
clone has a subject for this test.
FAILED tests/test_sync_run_record.py::test_the_committed_record_exists_and_parses
1 failed, 6 passed
```

**A third red I caused and had to fix: a flaky test of my own.** Restoring after the second
mutation left `test_a_failure_after_a_success_keeps_the_earlier_success` failing with *"last_attempt
did not move on the failing run"*. `_now()` has one-second resolution and both runs completed
inside the same second. **A flaky test is worse than no test — it teaches people to re-run rather
than to read.** Replaced with the deterministic form of the same property: `last_attempt` is never
earlier than `last_success`, and the outcome names the failure while the success does not.

---

## 8 — a correction to `041`'s done-note, and the reason it happened

**`041`'s done-note says its `OBS-045`/`OBS-046` citations "point at unrelated rows." That is
wrong, and `041` was right.**

**Four ledger ids are used twice.** `OBS-044`, `OBS-045`, `OBS-046` and `OBS-047` each appear on
two rows — a 2026-08-13 set from `021` and a 2026-08-14 set from `037`:

| id | 2026-08-13 (`021`) | 2026-08-14 (`037`) |
|---|---|---|
| `OBS-044` | `keepUpToDate` dies silently | **the inbound copier leaves no record** |
| `OBS-045` | the ~5 s update beat | **the export cannot run from a worktree** |
| `OBS-046` | `survived_window` on dead streams | **worktrees outlived their tasks** |

`041` and `043` both mean the right-hand column. **I read the left.** `OBS-062`.

**`tests/test_observations_ledger.py` does not check id uniqueness**, so nothing went red.

### Why I did not mark `OBS-044` or `OBS-046` resolved, even though `043` says this task closes them

**Because "OBS-044 PROMOTED" would be ambiguous, and the wrong reading is dangerous.** It would
equally read as closing *"a `keepUpToDate` subscription dies silently and every health signal
stays green"* — a live finding about a value used as a stop level, whose watchdog is proposed and
**not built**.

**Both rows stay `OPEN` and `OBS-062` says exactly why.** Renumbering either set is not mine to
do: `037`, `041` and `043` cite these ids in task files and done-notes that are already written
and already exported. **An id-uniqueness assertion in the ledger test is the cheap half and can
land immediately.**

---

## 9 — what I could not do

1. **Remove the `024` and `029` worktrees.** §5 — refused by the permission layer, twice. Both
   verified clean and merged first. **This is the one instruction in `043` left unexecuted.**
2. **Remove my own `043` worktree directory.** Deregistered but held open by another process.
3. **Resolve `OBS-044` and `OBS-046`.** §8 — ambiguous while the ids are duplicated.
4. **Exercise pair 3 against a real file.** `momentum-christoph-open` exists and is **empty**, so
   the pair is configured and unexercised — the same state `025`'s pair has been in since `026`.
   **`c023` is the UAT that settles it**, and until it runs, "the pair works" rests on the same
   code path the other two use and on no observation of this one.
5. **Check whether `export-handoff.ps1` has the same test-overwrites-the-record hole.** It takes a
   `-RunRecordOverride` and relies on callers passing it — the same gap in the outbound
   direction. Noted in `OBS-064`, unmeasured.

---

## 10 — the naming inconsistency, recorded and not fixed

`momentum-christoph-open` follows the **outbound** naming shape (repo folder) and is **inbound**;
the other inbound pair is `momentum-inbox-handoff` (direction-first). **`043` says record it, do
not rename anything, and nothing was renamed.** `OBS-063`.

---

## 11 — the tests, and the last actions

**`verify.ps1` ran from the main checkout at the time recorded in `verify-output.txt`.** No count
quoted — `043`'s last action forbids it. **No previously-passing test was made to fail.**

**`test_the_shipped_config_has_both_pairs` needed updating and its name deliberately was not
changed.** It asserted exactly two pairs; it now asserts three. `043` cites it by name, and a test
that moves out from under a citation breaks the reference — the same argument that makes
`handoff/` copy-and-keep.

**The export ran from the main checkout, not from a worktree** (`OBS-045`, the 2026-08-14 row).

---

**This note needs to be pasted to chat.**
