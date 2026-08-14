---
id: 037
title: The repo-to-Drive export stopped and nothing said so
type: bug
class: admin
owner: claude-code
depends: 020
---

**Status** RUNNING

# 037 — done. The export never failed. It was never run.

**That is the whole finding, and it changes the fix.** `037` Part 0 asks whether a trigger
stopped firing or a copier started failing, and says the two are different bugs. It is the
first: `export-handoff.ps1` has no trigger and has never had one. It is invoked by hand, by
Claude Code, at the end of a task, and no task changed the tree between 2026-08-13 22:12 and
2026-08-14 13:56.

**Three of `037`'s factual premises are wrong**, and they are corrected in §1 before anything
else, because `038` is written against them. The bug is real, the fix stands, and the specific
file `037` says the design session cannot read has been on Drive since 2026-08-13 17:18.

---

## 1 — Part 0's four answers, before any fix

### 1. How is the export triggered?

**It is not. There is no trigger.** `schtasks /query /fo LIST` matched nothing for
`handoff|export|momentum|drive`. There is no hook, no `CronCreate` routine, no watcher, no
scheduled job. The mechanism is one sentence of prose in `CLAUDE.md`:

> **Run it at the end of every task, after the commit.**

That sentence is the entire trigger, and the same section says why no daemon was added: *"a
missed export is visible in `verify.ps1` section 5; a background process that fails quietly is
not."* **The reasoning was sound and the instrument was not strong enough** — see §4.

### 2. When did it last attempt to run, as distinct from succeed?

**They were the same event, and that was the defect.** Before this task nothing recorded an
attempt. Both manifests carry:

```
**exported** 2026-08-13T22:12:59+02:00
**HEAD** e625df38c6794889bfe0b10803e38e36860bfa1a Five streams cost nothing, and then everything stopped at 15:22
**working tree** DIRTY -- 1 uncommitted paths
```

That HEAD is commit `e625df3`, authored `2026-08-13 22:12:53 +0200` — six seconds before the
export. So the last run was a normal end-of-task export that worked. **There has been no
attempt since.**

**`037` says 20:12. The manifests say 22:12:59.** The 20:12 figure matches nothing on disk;
`9014098`, the commit before, is 19:32:31.

### 3. What was the failure?

**There was none.** The copier did not error, did not partially copy, and did not no-op
incorrectly. Its last run copied one file and reported `103 files (1 copied, 102 unchanged)`.
Run by hand at the start of this task against an unmodified script, it behaved correctly.

**Not a Google outage and not a credential expiry either** — Drive is mounted, the folders are
present, and the inbound sync delivered `037` itself at 13:30 today. No code defect was
invented to have something to fix; the defect fixed is the invisibility, which is what the task
identifies as the actual bug.

### 4. Did it report anything anywhere?

**No, and this is the mechanism of the failure.** The only artifact the export produced was
`MANIFEST-<leaf>.md` — written **inside each destination** and **only on success**. Three
different states therefore presented as the same unchanged file:

| what happened | what the mirror looked like |
|---|---|
| ran, copied nothing | manifest unchanged |
| never ran at all | manifest unchanged |
| ran and died mid-copy | manifest unchanged |

`verify.ps1` section 5 read that manifest and printed `exported at 2026-08-13T22:12:59+02:00`
with **no age and no comparison against the source**, so a reader had to know today's date, do
the subtraction, and care. **And `verify.ps1` runs as the last action of a task — the same
trigger the export was missing.** The one instrument that could have caught it was gated behind
the identical condition.

---

## 2 — What `037` gets wrong, stated first because `038` depends on it

**`037`'s `unblocks:` line does not hold.** All three premises were checked against disk at the
start of this task.

| `037` says | disk says |
|---|---|
| export *"last ran 2026-08-13 20:12"* | `2026-08-13T22:12:59+02:00`, both manifests |
| `christoph/done/` on Drive *"holds nothing past `c014`"* | it held `c013` **and** `c014` |
| `c013` is unreadable to the design session, so `038` is blocked | `c013` has been on Drive since 2026-08-13 17:18 |

`013-s010-check-against-your-charts.md` hashes **identically** in both places:

```
3b3f5fec114afa6488b8a01e5c551e98f103ea611bb2edb868971612fc21bb09  christoph/done/013-s010-check-against-your-charts.md
3b3f5fec114afa6488b8a01e5c551e98f103ea611bb2edb868971612fc21bb09  D:\claude-googledrive-sync\momentum-christoph-done\013-s010-check-against-your-charts.md
```

**`038` is not blocked and never was.** `c013`'s chart comparison is readable and was readable
when `037` was written.

**What was actually missing** — five files, all created after 22:12 on 2026-08-13:

- `christoph/done/015 for christoph attach qqq.md` (13,401 bytes, created 2026-08-14 09:11)
- `handoff/inbox/035-for-code-bug-pdl-and-atr14.md`
- `handoff/inbox/035a-for-code-adr-is-rth-atr-is-eth.md`
- `handoff/inbox/036-for-code-every-indicator-declares-its-session.md`
- `handoff/inbox/037-for-code-bug-drive-export-stopped.md`

**`036` is named in `037` as missing and it is an inbound file** — it arrived from the design
session through `tools/sync_from_drive.py` and was waiting to be echoed back out. Recorded as
**OBS-047**, a READING rather than an observation: the design session can only diagnose the
mirror from the mirror, which is not a thing the repository can fix.

---

## 3 — Part 1: the immediate break

There was no break to repair, so Part 1 reduced to **running it**. From `D:\Dev\momentum` at
`HEAD 6f273dd`:

```
momentum-code-handoff: 4 new - inbox\035-for-code-bug-pdl-and-atr14.md, inbox\035a-for-code-adr-is-rth-atr-is-eth.md, inbox\036-for-code-every-indicator-declares-its-session.md, inbox\037-for-code-bug-drive-export-stopped.md
  not exported (non-.md): A1-connector-from-scheduled-run.txt, accepted\.gitkeep
momentum-christoph-done: 1 new - 015 for christoph attach qqq.md
  not exported (non-.md): .gitkeep
HEAD 6f273dd02bc9eabe8b182500f9cc285841fef4e9 Merge 037: the export leaves a record of every attempt
working tree DIRTY -- 6 uncommitted paths
run record D:\Dev\momentum\export-run-record.md (last_success 2026-08-14T13:56:04+02:00)
```

**Five files moved.** `c015` is now on Drive; so is `037` itself.

### The export must not be run from a worktree, and `037` told me to work in one

`037` says *"Work in a worktree, not `D:\Dev\momentum`."* I did the code work in
`.claude/worktrees/037-drive-export` and **ran the export from the main checkout**, deliberately.

**A worktree checks out tracked content only, and all five missing files were untracked.** An
export from the worktree would have copied 118 files, silently skipped those five, and written
a manifest asserting `files 118` with a sha256 for each — **complete, well-formed, internally
consistent and wrong.** Nothing downstream could have caught it: the manifest *is* the
completeness claim.

Recorded as **OBS-045**. The narrow fix is a refusal keyed on the destination rather than on the
checkout, and it is not in `037`'s scope.

---

## 4 — Part 2: the structural fix

### 2a — `export-run-record.md`, at the repository root

**Written on every invocation: before the copy, and again after.** A run killed mid-copy leaves
`last_attempt` moved and `last_success` stale, which is the signature to look for.

```
last_attempt : 2026-08-14T13:56:03+02:00
last_success : 2026-08-14T13:56:04+02:00
outcome      : 5 new - momentum-code-handoff/inbox/035-…, …, momentum-christoph-done/015 for christoph attach qqq.md
head         : 6f273dd02bc9eabe8b182500f9cc285841fef4e9 Merge 037: the export leaves a record of every attempt
```

**Where it lives and why that location survives the failure.** The repository root is outside
`handoff/`, outside `christoph/done/` and outside `D:\claude-googledrive-sync`. It is therefore
**not exported** — it cannot be, since the export's sources are structurally derived and the
root is not one of them. *A run record that only existed in the destination could not report
that it failed to reach the destination.* It is the smoke alarm not wired to the burning wall.

**It is tracked, not gitignored.** Two reasons: `tests/test_export_run_record.py` needs a
subject on a fresh clone (2c makes an absent record red), and `git log -p export-run-record.md`
is then the attempt history for free. **The cost, stated rather than discovered later:** an
export run after a commit leaves the tree dirty until the next commit picks the record up. To
stop that degrading the manifest's `working tree` field into a permanent `DIRTY`, `git status`
is read **before** the first record write — so the field describes the source tree, and a record
left uncommitted by a *previous* run does still show up, correctly.

**ISO-8601 with an offset**, not the `yyyy-MM-dd HH:mm:ss` the task sketched. It matches the
manifest's `exported` stamp, and an offset-less time is ambiguous across the DST change in a
project whose session logic is US/Eastern while the machine runs CEST.

### 2b — `verify.ps1` reports the age, and something better than the age

Section 5 now **leads** with the run record, before the manifests, because the manifests cannot
answer the question it answers:

```
  drive export      last attempt 2026-08-14T13:56:03+02:00   (0h 04m ago)
                    last success 2026-08-14T13:56:04+02:00   (0h 04m ago)
                    outcome      5 new - momentum-code-handoff/inbox/035-…
```

**And a second line per destination that is not a clock:**

```
    newer than export  4 — inbox\035-…, inbox\036-…, inbox\037-…, done\037-…
```

**This is the part I would defend hardest.** *"Last success 15 hours ago"* is unalarming on a
Sunday and alarming on a Thursday, and a signal that cannot tell those apart is a signal that
gets ignored — `037` says so itself about time-based tests. *"Four source files are newer than
the last success"* means the same thing on both days: **four things the design session cannot
read.** It is a content signal, it needs no schedule, and it goes to zero exactly when the
problem is gone. Both `MISSING` and `UNPARSEABLE` are printed rather than skipped, and the
section still draws no verdict, consistent with the rest of the script.

### 2c — the test, and the red

`tests/test_export_run_record.py`, six tests. **Scoped positionally to exactly two paths** —
`export-run-record.md` and `export-handoff.ps1`. Nothing scans the tree for timestamp-shaped
strings; that self-reference trap fired repeatedly during this session's ledger edits and would
have matched the test's own docstring.

**Not time-based.** Nothing asserts how old `last_success` is.

Four are static — exists, both timestamps present and parseable, `outcome` and `head` present,
`outcome` is one line. **Two are behavioural, and they are the ones that matter**, because a
static check would pass forever against a copier that had stopped writing the file: the record
would simply go stale, which is indistinguishable from an export nobody ran — the original bug.
Both run the real copier as a subprocess against a temp destination and a temp record path, so
neither touches Drive.

**Seen red by removing the record**, in the main checkout:

```
FAILED tests/test_export_run_record.py::test_the_run_record_exists
FAILED tests/test_export_run_record.py::test_it_carries_both_timestamps_and_they_parse
FAILED tests/test_export_run_record.py::test_it_carries_an_outcome_and_a_head
FAILED tests/test_export_run_record.py::test_the_outcome_is_one_line
FAILED tests/test_adoption_log_complete.py::test_the_allowlist_does_not_rot
5 failed, 7 passed in 2.89s

E  AssertionError: export-run-record.md is missing. The export writes it on every invocation,
   success and failure alike -- so its absence means either the copier stopped recording or
   somebody deleted the one artifact that can report a sync that never ran.
```

The fifth is `test_the_allowlist_does_not_rot` catching the same absence from the other side,
which is the adoption gate working as designed.

With the record restored: `6 passed in 2.58s`.

### The bug I reintroduced inside the fix, found by running the refusal

**The first cut indented the record's four fields to render them as a markdown code block.**
`Read-LastSuccess` anchored on `^last_success`, which then never matched — so **every failed run
silently rewrote `last_success` to `never`**, destroying the one value the whole mechanism
exists to preserve. Output at the moment it was caught:

```
EXPORT FAILED - 0 new - destination unreachable: D:/no-such-drive-root
run record …\rec.md (last_success still never)      <-- should have been 13:42:19
```

**`037`'s own defect, reproduced inside `037`'s fix, and invisible to every static check.** It
was found by executing the refusal, not by reading the code. Both halves are now fixed: the
fields are written at column zero *and* both regexes tolerate leading whitespace. Either alone
would have done, which is the point.

### 2d — the trigger. I agree with the recommendation, with one correction

**Agreed: Claude Code runs the export as a final action alongside `verify.ps1` on any task that
adds to `handoff/done/`.** No second scheduler. That is what I did here.

**The correction is that this is not a change** — `CLAUDE.md` has said *"run it at the end of
every task, after the commit"* since v1.5. **The convention was already exactly 2d and it still
drifted fifteen hours.** So restating it buys nothing on its own, and the honest claim for this
task is narrower than 2d's wording suggests: **2b is the fix and 2d is the habit it makes
visible.** Adopting 2d without 2b would have produced the same fifteen hours next week.

The one thing that would make the trigger genuinely deterministic is putting the export inside
`verify.ps1`, and **that must not be done**: `verify.ps1` states facts and modifies nothing, and
a verification script with a side effect cannot be run to find out whether something happened.

---

## 5 — Part 3: which of the four lines the copier could emit

**Before** — measured, not read off the source:

| line | before |
|---|---|
| `N new · <names>` | **partly.** `momentum-code-handoff: 103 files (1 copied, 102 unchanged)` — a count, never the names |
| `0 new · up to date` | **no.** Identical sentence to the above with a different number. *"103 files (0 copied, 103 unchanged)"* and *"103 files (1 copied, 102 unchanged)"* differ by two characters |
| `0 new · source unreachable` | **not on stdout.** `throw "source missing: …"`, exit 1, stderr only, **stdout completely empty** |
| `0 new · destination unreachable` | **not on stdout, and only for the Drive root.** A missing *leaf* destination was silently created. Run against a missing root: exit 1, a red exception block on stderr, **stdout empty** |

**Two of the four were the same sentence, and the two failures printed nothing at all on
stdout — the success line was simply absent, which is the hardest kind of output to notice.
That alone explains fifteen silent hours.**

**Now** — all four, distinct, all on stdout, and all four write the run record:

```
momentum-code-handoff: 4 new - inbox\035-…, inbox\036-…, inbox\037-…
momentum-code-handoff: 0 new - up to date (103 files unchanged)
EXPORT FAILED - 0 new - source unreachable: D:\…\christoph\done (destination momentum-christoph-done)
EXPORT FAILED - 0 new - destination unreachable: D:/no-such-drive-root
```

Both failures exit `1`. Both were executed, not reasoned about — the source case by renaming
`christoph/done` inside the worktree and restoring it.

**The name list is capped at 12 and the remainder is counted out loud** — `… and 106 more`. The
first run against an empty destination copies 118 files and named all of them in a
12,000-character line. A silent truncation would read as *"that was everything"*, which is the
shape of failure this task exists to remove.

---

## 6 — Test results, verbatim

**Baseline in `D:\Dev\momentum` before any change:**

```
8 failed, 340 passed, 1 warning in 32.01s
```

**After, in `D:\Dev\momentum`:**

```
8 failed, 346 passed, 1 warning in 30.58s
```

**Same eight, six more passing** — the six in `tests/test_export_run_record.py`. Nothing that
was green went red. `verify.ps1` ran as the last action and its output is not pasted here, per
`037`'s instruction.

The eight pre-existing failures are unrelated to this task and were red before it started:
`test_handoff_state_declared`, `test_observations_ledger` (×2), `test_pytest_collection`,
`test_regime_prompt_invariants` (×2), `test_regime_snapshot_could_not_do`, `test_uat_has_a_file`.

**One of them is a finding.** `test_pytest_collection::test_every_directory_holding_tests_is_declared`
is red because of `.claude/worktrees/024-subagent-roster` and `.claude/worktrees/029-entry-point`
— **two worktrees left on disk by earlier tasks and never removed.** OBS-034 predicted this
breakage would be *"transient: removing the worktree clears it"*. Measured three days later it
is not transient, because nobody removed them. Recorded as **OBS-046**.

**I removed my own worktree and deliberately left theirs.** Deleting another session's working
checkout to make a test green is the move OBS-036 exists to warn about.

**Two of the eight gain one entry each from this task, and both are correct to.**

- `test_uat_has_a_file` now names `037-drive-export-stopped.md` alongside `017` and `020`,
  because this note declares a UAT (`c017`) and no file in `christoph/` declares slice `037`.
  **The fix is chat's**: `christoph/open/` is authored by the design session and Claude Code
  must never write there. Declaring `UAT | … | None` to clear it would be a lie — `037` does
  owe a UAT, and it is in its own exit table.
- `test_handoff_state_declared` now names `handoff/inbox/037-for-code-bug-drive-export-stopped.md`
  alongside `021`–`027` and `035`, because the arriving task file carries no `**Status**`
  header. **That file is chat's and I did not edit it.** The inbound copier is required to copy
  task files byte-identical, so repairing one on landing would put the tree and Drive out of
  sync on bytes — which is exactly what `026`'s immutability rule forbids.

---

## 7 — What I could not do

- **`tools/sync_from_drive.py` has the same defect and I did not fix it.** `037` says *"do not
  touch `026`… if the fix genuinely must be shared between them, say so and stop."* **It must,
  and this is the stop.** The inbound copier leaves **no record of any kind** — three
  well-distinguished stdout lines and nothing on disk — so it is *worse* off than the outbound
  one was, which at least stamped a manifest. **OBS-044.**
- **`CLAUDE.md`'s export section is now incomplete.** It describes the manifest and
  `verify.ps1` section 5 and says nothing about the run record. I did not bump it: the version
  ceremony is a decision, `037` did not ask, and a stale section is more honest than a version
  row nobody sanctioned. **It should be v1.7 and it is not.**
- **The design session still cannot see the run record.** It is not exported and by design never
  will be — putting it in the destination would defeat the property it exists for. So *"did the
  export run"* is answerable in the tree and not in Drive. **OBS-047**, second half.
- **No refusal was added for running the export outside the main checkout** (OBS-045), and no
  `New-Item` behaviour was changed for a missing *leaf* destination — that auto-creation is
  deliberate and documented in the script, and only the missing *root* is treated as
  `destination unreachable`.
- **The number collision in the inbox is unresolved and is not mine.** `tools/sync_from_drive.py`
  refused to copy `035-for-code-every-value-declares-its-session-basis.md` from Drive, because
  `035-for-code-bug-pdl-and-atr14.md` already holds `035` in the inbox. **Two different `035`s
  exist and one of them has never landed.** The copier reported it correctly and copied neither.

---

## 8 — Exit tests

| test | who | state |
|---|---|---|
| **Green** | Claude Code | **Done.** `verify.ps1` ran as the last action with 2c included, seen red first by removing the run record (§4, 2c) |
| **Refusal** | Claude Code | **Done.** Destination pointed at a path that does not exist ⇒ `destination unreachable` on stdout, exit `1`, run record still written with `last_success` carried forward. Covered by `test_an_unreachable_destination_still_writes_the_record` |
| **UAT** | Christoph | **`c017` — open `D:\claude-googledrive-sync\momentum-christoph-done` and confirm `013` is there.** It is, and it was before this task. **`015` is the file that arrived today** — please confirm that one too, since it is the actual evidence of the fix |

---

## Files

| path | change |
|---|---|
| `export-handoff.ps1` | run record on every invocation; four distinct outcomes; both refusals exit 1 and still record; `-DriveRootOverride` / `-RunRecordOverride` for the tests |
| `export-run-record.md` | **new, tracked.** Written by the copier, not by a person |
| `verify.ps1` | section 5 leads with the run record's age; per-destination count of source files newer than the last success |
| `tests/test_export_run_record.py` | **new.** Six tests, two behavioural, none time-based |
| `tests/test_adoption_log_complete.py` | two allowlist entries; the count is now 42 |
| `docs/observations/OBSERVATIONS.md` | OBS-044, OBS-045, OBS-046, OBS-047 |

---

## THIS NOTE NEEDS PASTING TO CHAT

**Writing it is not reporting it.** It lands in a repo the design session cannot read. It is on
Drive now — the export ran — but §2 corrects three premises `038` is being written against, and
that correction is worth carrying by hand rather than waiting for it to be noticed:

> **`038` is not blocked. `c013` is on Drive, byte-identical, and has been since 2026-08-13
> 17:18.** The export last ran at 22:12:59, not 20:12. What was missing was `c015` and four
> inbox files, and all five are there now.
