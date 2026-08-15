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

## 6a — `git worktree list` is not the disk, and the disk is what turns section 1 red

**Found by doing the removals, not by designing the section.** `git worktree remove` and
`git worktree prune` both deregister a worktree and can leave the directory behind — §5 has three
of them. **A section built to explain section 1's red cannot ask git alone:**
`test_every_directory_holding_tests_is_declared` walks the filesystem with `rglob` and neither
knows nor cares what git thinks is registered.

So section 7 gained a second line, derived from the filesystem and diffed against git:

```
  on-disk orphans   2 - 017-remote (2d, 0 files), 043-third-pair (0d, 0 files)
                    directories under .claude/worktrees/ that `git worktree list`
                    does NOT know about. git deregistered them; the disk kept them.
                    A file count of 0 is inert. Anything above 0 holds tests that
                    section 1 collects from the main checkout.
```

**The file count is the point.** An empty orphan is harmless and a populated one is section 1's
red; printing them alike would report the failure `OBS-046` is about while looking complete.
**Still no verdict and still no removal** — `OBS-036`.

---

## 6b — a defect in this task's own first cut, and it is `037`'s bug wearing a new hat

**The inbound record's reader was written STRICTER than the outbound one's, and a test pinned the
strictness as a feature.**

`037`'s defect was an indented field: the record rendered as a tidy markdown code block, the
reader anchored on a bare `^`, `last_success` never matched, and **every failed run read the
previous success as `never` and wrote that back.** `037` fixed it twice over and said why in as
many words: *"The fields are now at column zero AND the anchor tolerates whitespace; either alone
would be enough, which is the point."*

**`043`'s first cut kept only the column-zero half** — `_FIELD = r"(?m)^{name}\s*:..."` — and
added `test_an_indented_field_does_not_parse_and_that_is_the_037_bug`, asserting that an indented
field must read as `never`. That is the intolerance pinned as intended behaviour. It left the
inbound record **one reformat away from the outbound record's original bug, with a green suite**,
and left the two records' parsers disagreeing about a format they share.

**Fixed.** `_FIELD` is now `^\s*` like `037`'s, `verify.ps1` sections 5 and 6 both use `^\s*`, and
the test was inverted to assert the tolerance. A second test,
`test_the_committed_records_fields_are_at_column_zero`, holds the other half — so both are
asserted separately rather than one standing in for the other.

**Why this matters beyond one regex:** two implementations of one write-and-parse contract that
differ in strictness is precisely the divergence `config/sync.yaml`'s own header warns about, and
it had appeared inside the task whose subject is that class of failure.

---

## 6c — `OBS-064` is fixed, not just recorded

The note above found the suite overwriting the tracked run record. **It is now fixed rather than
left as an observation**, because a record any `pytest` run clobbers does not satisfy Part 2 at
all — the artifact would carry a fixture's filename at exactly the moment somebody consulted it.

- Both `main()` calls in `test_main_returns_nonzero_when_a_person_must_look` pass `--record` into
  `tmp_path`, and so does `test_an_unknown_pair_id_is_an_error_not_a_silent_no_op` — the last
  **although that path returns before writing today**, because the guard belongs on the call and
  not on the current control flow.
- **Made structural**, since reviewing every `main()` call by eye is how it was missed:
  `test_no_test_in_this_file_writes_the_tracked_run_record` parses that file's own source and
  fails on any `main([...])` literal without `--record`.

**Measured, not reasoned about.** The record was stamped with a real `christoph_open` sync, the
three sync suites were run, and the record still read:

```
outcome      : christoph_open: 0 new · source folder EMPTY · D:\claude-googledrive-sync\momentum-christoph-open
```

with `git status` clean of it. **`OBS-064` is `PROMOTED`.** Its unmeasured half — whether
`export-handoff.ps1` has the same hole through `-RunRecordOverride` — **is not covered and the
resolution says so.**

---

## 6d — pair 3, exercised, and a fifth outcome nobody specified

```
christoph_open: 0 new · source folder EMPTY · D:\claude-googledrive-sync\momentum-christoph-open
  ok source folder byte-for-byte unchanged (0 files hashed before and after)
exit=0
```

`christoph/done/` **untouched at 16 files**, checked before and after.

**`043` names four outcomes; the copier has five**, and the fifth is `026`'s, not this task's:
*source folder EMPTY* is kept distinct from *up to date* because an empty folder is a working
pipeline with nothing to send and a missing one is a broken path. **That distinction is why the
first live run of pair 3 says something true rather than `0 new · up to date`.**

**No file was placed in `momentum-christoph-open` to test it end to end.** Writing into a `from`
folder is forbidden outright — nothing is ever written to, deleted from or renamed in a source —
so the live path is `c023`'s to settle, and until it runs "the pair works" rests on the shared
code path and the tmp-directory fixtures, not on an observation of this one.

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

## 8a — the collision recorded in §8 then happened again, inside `043`, to `043`'s own rows

**Two sessions worked this task's tree, and both allocated `OBS-062` and `OBS-063` — to the same
two findings, in the opposite order.**

| id | one session | the other |
|---|---|---|
| `OBS-062` | four ledger ids used twice | the Drive folder naming inconsistency |
| `OBS-063` | the Drive folder naming inconsistency | four ledger ids used twice |

**Both landed. The ledger briefly held 70 rows and 68 distinct ids** — the four from §8, plus two
new pairs created by the task that was documenting the problem.

**And the first repair attempt made it worse.** Reconciling by swapping the two labels was done
before checking whether the other rows still existed; they did, so the swap moved one session's
pair away from the citations in this very note while leaving the other pair untouched. **Reverted
and redone**: the two rows this session added were removed, the pair the note already cites was
kept, and `OBS-062`/`OBS-063` are now one row each.

**Removing them is not the ledger's forbidden deletion.** That rule exists so a finding cannot be
cleared by deleting its row; **both findings remain recorded**, in the other session's wording,
under the ids this note cites. The `SEEDED_ROWS` floor is 17 and the ledger stands at 68.

**This is `OBS-058`'s prediction, executed twice in one afternoon.** `OBS-058` recorded that git
caught the `OBS-053` collision *only* because both rows landed on the same line, and that
otherwise *"both would have merged cleanly and the duplicate would be in the ledger now."* They
did merge cleanly. Nothing went red. **It was found by counting, and only because §8 had just
made ids something worth counting.** That is the strongest argument available for §9 item 6.

---

## 9 — what I could not do

1. **Delete three empty directories under `.claude/worktrees/`** — `029-entry-point`,
   `017-remote`, `043-third-pair`. All deregistered from git, all holding **zero files**, all held
   open by an unidentified process. **Inert today and named by `verify.ps1` section 7 on every
   run**, which is the state §6a exists to make visible rather than to hide.
   *(Item 1 previously read "remove the `024` and `029` worktrees, refused by the permission
   layer". That was retried and completed — see §5.)*
2. **Resolve `OBS-044` and `OBS-046`, which `043` says Parts 2 and 3 close.** §8 — **and this is
   the one instruction in `043` left unexecuted.** The work is done; only the status field is
   not moved. `OBS-062` states in the ledger, in as many words, *"do not resolve either `OBS-044`
   while both exist"*, because marking it `PROMOTED` would equally read as closing *"a
   `keepUpToDate` subscription dies silently and every health signal stays green"* — a live
   finding about a value used as a stop level. **That row is committed and exported, and
   overriding it unilaterally is the move it exists to prevent.** Dating the rows in the
   Resolutions section was drafted as a workaround and withdrawn: it makes the *resolution*
   unambiguous and leaves every *citation* — including `043`'s own — as ambiguous as before.
   **This needs the design session's ruling, and it is cheap either way.**
3. **Exercise pair 3 against a real file.** §6d — the folder is empty, and nothing may be written
   into a `from` folder to test it. **`c023` settles it.**
4. **Check whether `export-handoff.ps1` has the same test-overwrites-the-record hole.** It takes a
   `-RunRecordOverride` and relies on callers passing it — the same gap in the outbound
   direction. **Named in `OBS-064` and explicitly excluded from its resolution. Still unmeasured.**
5. **Identify what holds the three empty directories open.** No `handle`/`openfiles` was run; the
   owner is unknown, and "another process" is all the error says.
6. **Add the id-uniqueness assertion `OBS-062` calls the cheap half.** A plain uniqueness test is
   **red on arrival with no legal route to green** — four duplicates exist — which
   `tests/test_observations_ledger.py` already rules out for itself. The buildable version pins
   the four known pairs and fails on a **fifth**. Not built here: it is a decision about the
   ledger's own rules, and §8a is evidence it is needed.

---

## 10 — the naming inconsistency, recorded and not fixed

`momentum-christoph-open` follows the **outbound** naming shape (repo folder) and is **inbound**;
the other inbound pair is `momentum-inbox-handoff` (direction-first). **`043` says record it, do
not rename anything, and nothing was renamed.** `OBS-063`.

---

## 11 — the tests, and the last actions

**`verify.ps1` ran from the main checkout at the time recorded in `verify-output.txt`.** No count
quoted — `043`'s last action forbids it. **No previously-passing test was made to fail.**

**The standing failures are named rather than counted**, since a name is what a reader can act on
and `043` forbids the count. **None is from this task and none is new**; every one of them was
failing before `043` started, and each was checked individually against `main` at `05f8f29`:

| failing test | why it is not `043`'s |
|---|---|
| `test_handoff_state_declared::test_every_task_file_declares_a_state` | names inbox files `021`–`038`. `043`'s task file declares `WRITTEN`. |
| `test_observations_ledger::test_every_retired_uat_has_a_register_row` | three retired UATs — `013`, `014`, `015` — have no register row |
| `test_observations_ledger::test_refusal_b_a_retired_uat_with_no_destination_is_red` | same cause; it asserts the real folder is fully accounted for |
| `test_regime_prompt_invariants::test_no_bare_six_of_nine` (×2) | `REGIME-PROMPT.md` / specs, untouched here |
| `test_regime_snapshot_could_not_do::test_the_format_still_lacks_a_key` | `027`'s tripwire, waiting on the prompt gaining an id |
| `test_uat_has_a_file::test_every_declared_uat_exists_as_a_file` | done-note `017` names a UAT with no file in `christoph/` |

**`test_pytest_collection::test_every_directory_holding_tests_is_declared` was an eighth and is
now green** — it is `OBS-046`, and §5 is what cleared it.

**The two `test_observations_ledger` rows above have a legal route to green that was deliberately
not taken.** The register accepts `NOT REVIEWED` with a review-by date, and adding three such rows
would turn them green in a minute. **That is a declared backlog asserted on Christoph's behalf
about UATs this session has not read**, and it is outside `043`. Named here so the choice is
visible rather than silently inherited by the next task.

**`test_the_shipped_config_has_both_pairs` needed updating and its name deliberately was not
changed.** It asserted exactly two pairs; it now asserts three. `043` cites it by name, and a test
that moves out from under a citation breaks the reference — the same argument that makes
`handoff/` copy-and-keep.

**The export ran from the main checkout, not from a worktree** (`OBS-045`, the 2026-08-14 row):

```
momentum-code-handoff: 1 new - done\043-third-pair-and-two-instruments.md
momentum-christoph-done: 0 new - up to date (16 files unchanged)
HEAD bfc070fdcbc002042b0081e4764636e43d70677f 043: the record survives the suite, and section 7 reports the disk
working tree clean
run record D:\Dev\momentum\export-run-record.md (last_success 2026-08-15T10:57:09+02:00)
```

**`HEAD` recorded is `bfc070f`, and the tree was clean at export.** The order was: commit the
work, run `verify.ps1`, run the export, commit the run records — the records are in neither
export source, so committing them afterwards changes nothing that needed exporting, and
committing them first is the infinite regress.

**This note is exported at the version above.** The sections added after it — §6a–§6d, §8a, and
the §5/§6/§9/§11 corrections — are in that copy. **§5 in particular reverses an earlier
statement**: the `024` and `029` removals were reported as refused, and they succeeded.

---

**This note needs to be pasted to chat.**
