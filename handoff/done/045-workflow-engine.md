---
id: 045
title: The workflow engine — trigger, dependencies, and who may decide
type: task
class: admin
owner: claude-code
---

**Status** RUNNING

# 045 — done. The four UAT files landed on the first run.

**All five parts complete.** The one thing not done is registering the scheduled task itself,
which writes outside the repository and is Christoph's — `tools/register-sync-task.ps1` is
written and one line away.

---

## 1 — the exact invocation, and whether it needed a wrapper

**It did not need one, and it got one anyway.**

```powershell
C:\venvs\trading\Scripts\python.exe D:\Dev\momentum\tools\sync_from_drive.py
```

**Measured, because 045 says a tool needing a specific working directory or an activated
environment is itself a finding:**

| | |
|---|---|
| working directory | **irrelevant.** Run from `C:\` it behaves identically — the script derives the repo from `__file__`, not from `cwd` |
| activated environment | **not needed.** The venv interpreter is named in full |
| arguments | **none required.** `--pair <id>` narrows it, `--dry-run` copies nothing |

**So the defect was never that the command was hard. It was that nobody had written it down.**

**The wrapper is `sync.ps1`, at the repository root, beside `verify.ps1`** — one word, because
045 is right that Christoph should not have to remember a shape. It passes the copier's exit code
straight through: **a wrapper that swallowed it would turn every refusal into a silent success**,
which is the failure this whole chain exists against.

---

## 2 — did the four waiting UAT files land?

**Yes, on the first run, before any of the rest of this was built.**

```
=== BEFORE ===   christoph/open/ :  .gitkeep
=== Drive    ===  018-for-christoph-task-check-atr14-and-pdl.md
                  019-for-christoph-task-lock-and-limits.md
                  021-for-christoph-task-52-week-basis.md
                  023-for-christoph-task-third-drive-pair.md

christoph_open: 4 new · 018-…, 019-…, 021-…, 023-… · 0 differing
  ok source folder byte-for-byte unchanged (4 files hashed before and after)
exit=0

=== AFTER  ===   all four in christoph/open/
```

**`043`'s pair 3 works end to end**, and this is the first time it has carried anything.

---

## 3 — `CLAUDE.md`: what it said, what it says, and what Christoph must do

**Before: nothing.** The file had no mention of the inbound sync at all — not the command, not
the script, not the pairs. That is the whole of the finding.

**Now v1.7**, with two new sections:

- **`sync.ps1`**, as a copy-pasteable line, in *Running things* — the section he already reads.
- **`claude/NOW.md`**, what it is and that a hand edit does not survive.
- **A new top-level section, *Who may decide*** — Part 4's rule, in full, with its four
  guardrails and its stated risk.

`037` flagged this bump as owed and correctly declined to take it unasked. `045` asks.

**What Christoph must do, in one line:**

```powershell
# right-click PowerShell → Run as Administrator, then:
D:\Dev\momentum\tools\register-sync-task.ps1
```

**I did not register it.** Creating a Windows Scheduled Task writes to the machine, outside the
repository. **That is a system change and system changes are his** — and 045 anticipates it
("Christoph creates or approves the scheduled task if Windows requires it").

**The task, as written:** every 15 minutes, **inbound only**, `-MultipleInstances IgnoreNew`,
10-minute execution cap, logging to `sync-scheduled.log`, and deliberately **not** elevated — it
copies between two folders this user already owns, and a job running elevated for no reason is a
standing offer to whatever it executes.

**Why this overturns `037`, stated because it is a reversal.** `037` ruled out a daemon: *a missed
export is visible in `verify.ps1`; a background process that fails quietly is not.* **The
objection was to silence.** `043` gave the inbound copier a run record, so a scheduled run that
dies now leaves `last_attempt` moved and `last_success` stale — the exact signature — and section
6 prints both. **The reasoning was sound and its premise is gone.** The export stays unscheduled;
`037` settled that separately and a scheduled export would race a session mid-commit.

---

## 4 — did `verify.ps1` already report the inbound record's age?

**Yes. `043` did not leave that half undone.** Section 6 already rendered `last attempt`,
`last success` and `outcome`, each with an age. Part 5's work was the *other* half — the count.

---

## 5 — what `waiting in Drive` read on the first run

**Zero — and the honest version of that answer is that I unblocked the backlog before the
instrument existed.**

Part 1 says *run it and confirm the four files land*, so I did, and only then built the counter.
**Its first reading is therefore `0`, and that is a true reading of a state I had already
fixed.**

**What it would have read is not a guess: it is a measurement I made by hand, above.** Four files
in `momentum-christoph-open`, one `.gitkeep` in `christoph/open/`. **`waiting in Drive 4`.**

**A gap worth naming: `waiting` counts files ABSENT from the destination, not files that
DIFFER.** `040` and `043` currently differ between Drive and the tree — both are v1.2 in Drive
against v1.1 here — and they contribute **zero** to this count. They are not waiting; they are
refused, and the copier says so on every run and exits non-zero. **Two different problems, two
different instruments, and neither reads as the other.**

---

## 6 — what `NOW.md` reads now

```
ready now    006 007 025 031 033 040 044
blocked      —
running      —
on christoph 018 019 021 023
superseded   035->036 035a->036 036->038
done         001 002 003 004 004a 005 008a 008b 012 012a 013 013a 013b 013c 013d
             014 015 016 017 018 019 020 021 022 023 024 026 027 028 029 030 032
             034 037 038 039 041 042 043 044 045
admin:product this stretch   7:2
```

**`superseded` is not in 045's list of categories and I added it.** Without it `035`, `035a` and
`036` render as **ready now** — an invitation to run them. **A session did exactly that this
morning**, read `035`, found two files under one number saying opposite things about `PDL`, and
stopped only because the ambiguity happened to be visible. **A status board saying `ready` is a
stronger signal than that ambiguity was.** It is derived from `supersedes:`, which is already in
the frontmatter, so it costs no new convention.

**`running` is always `—` and cannot be otherwise.** It is the one line that is not derivable: a
session in flight leaves nothing in the tree that says so, and a stored flag is exactly the state
this file refuses to keep. Said in the file itself rather than left to look like a bug.

**`NOW.md` is gitignored**, like `verify-output.txt`. Tracked, it would dirty the tree on every
verify run — section 2 would report it forever — and three sessions regenerating it would collide
on a file whose entire content is recomputable.

---

## 7 — the four reds, quoted

**1. The run record removed.**

```
AssertionError: …\sync-run-record.md is missing. It is tracked, not gitignored, so a fresh
clone has a subject for this test.
```

**2. A file waiting that the count misses** — `missing` forced to empty:

```
AssertionError: assert 0 == 1     (tests/test_waiting_in_drive.py:46)
AssertionError: assert 0 == 1     (tests/test_waiting_in_drive.py:58)
```

**3. A hand edit surviving a run** — the write skipped with `if not out.exists()`:

```
AssertionError: a hand edit survived a run. NOW.md is derived and nothing in it is stored —
a file that keeps an edit is a status board that can be made to lie while still looking
generated.
```

**4. A two-task cycle** — `find_cycle` disabled:

```
Failed: DID NOT RAISE CycleError     (test_a_two_task_cycle_is_refused_and_named)
Failed: DID NOT RAISE CycleError     (test_a_longer_cycle_is_also_found)
```

### Red 3 produced **nothing** on the first attempt, and that was a finding about my test

The mutation ran and the suite stayed green. **The test called `render(compute(repo))` and wrote
the result itself** — so it asserted only that the *renderer* does not emit `HAND EDIT`, and never
reached the code deciding whether to write at all.

**A test that cannot see the defect it is named after is worse than no test**, because the name
says the defect is covered. It now goes through `main()`, and the same mutation fails it.

**This is the second time in two tasks that seeing red found a blind test rather than a blind
implementation.** It is the strongest argument in 045's own instructions.

---

## 8 — what I could not do

1. **Register the scheduled task.** §3 — machine-level, Christoph's. The script is written and
   tested for syntax; **it has never been executed**, so its behaviour under Task Scheduler is
   unverified. That is a real gap and `c025` is where it shows.
2. **Confirm concurrent invocation against a *real* scheduled run.** `045` asks whether the
   copier's behaviour holds when a scheduled run collides with a hand run. **I tested two
   back-to-back runs over one source and destination** — byte-identical is a no-op, and the second
   changed nothing. **That is sequential, not concurrent**, and true simultaneity would need the
   task registered.
3. **Read a non-zero `waiting in Drive` through the instrument itself.** §5.
4. **Retro-fit `depends:`.** 045 forbids it, so `NOW.md`'s `blocked` line is empty — every task
   in the tree predates the field. **The line is untested against live data** and only against
   fixtures.

---

## 9 — one thing I changed that 045 did not ask for

**`verify.ps1` used the name `$tmp` for two unrelated things** — a temp *script* path in section 4
and a datetime scratch in section 5. `tests/test_verify_output_is_ignored.py` asserts that every
`Remove-Item` targets a temp path, and the datetime `$tmp` read as a violation of a rule it was
never part of.

**I renamed the datetime one.** The alternative was loosening the guard, and the guard is right:
one name for two meanings, in a script whose own test inspects it by name, is a trap that fires
later.

**And that test's assertion moved from a count to a shape.** It read `code.count("Remove-Item")
== 1`. A count is wrong twice over: it blocks a legitimate second temp cleanup — which 045
required — **and it would happily permit a single `Remove-Item` pointed at a repo path.**

---

## 10 — a defect I introduced and caught between two verify runs

**Two consecutive `verify.ps1` runs disagreed — 9 failed, then 8 — and the difference was
`test_spec_pointers`.**

`CLAUDE.md` v1.7 named `claude/NOW.md` as a backticked path. That test resolves every
backticked repo-relative token, **NOW.md is gitignored, and it does not exist until the generator
has run once.** So the first verify run was red, its own NOW.md section then created the file,
and the second run was green.

**On a fresh clone it would be red until somebody ran `verify.ps1`** — a pointer to an artefact
that is not guaranteed to exist.

**Fixed by not backticking a generated path**, in both places it appeared. The generator,
`tools/now.py`, is tracked and real and is what the file now points at. **Confirmed against the
fresh-clone case by deleting NOW.md and re-running: green with it absent and green with it
present.**

**It would have been invisible in a single run**, which is the argument for reading an
instrument's output twice when you have just changed the instrument.

---

## 11 — the tests

**`verify.ps1` ran from the main checkout at the time in `verify-output.txt`.** No count quoted.
**The inbound sync ran first, then `verify.ps1`, then the export**, in 045's order, from the main
checkout.

**No previously-passing test was made to fail.** The one red that remains from `044` —
`test_observation_ids_are_unique` — is unchanged and still awaiting its ruling.

---

**This note needs to be pasted to chat.**
