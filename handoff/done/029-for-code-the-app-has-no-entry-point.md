# 029 — done — the app can be started, and the test that proves it was seen red first

**Status** RUNNING · **Date** 2026-08-13 · **Type** correction · **Tree** `D:\Dev\momentum`

---

## 0. Where this work is, and it is NOT on `main`

**Everything below is committed on the branch `worktree-029-entry-point`, in the git worktree
`D:\Dev\momentum\.claude\worktrees\029-entry-point`.** This session runs as a background job and
is required to isolate before editing; edits to the shared checkout are refused, not discouraged.

**Nothing has been merged and nothing has been pushed.** `CLAUDE.md` forbids pushing this tree
because the remote is unsettled, and merging is Christoph's call. Until it is merged the entry
point does not exist in `D:\Dev\momentum` — **so the `013` UAT cannot be run yet.** That is the
one thing in this note that needs an action before anything else here is true. See §7.

---

## 1. The diagnosis was exactly right, and the file confirms it

`029` inferred that `live/tui/app.py` defined `MomentumApp` and never ran it. Confirmed:
`class MomentumApp(App)` at line 424, no `main()`, no `.run()` call, no
`if __name__ == "__main__"`, and no `live/tui/__main__.py`. Nothing was broken. **Nothing was
ever built to start.**

## 2. The exact commands that now work

Both, as required — `-m live.tui` is the form worth having and `-m live.tui.app` is the one in
Christoph's shell history:

```
C:\venvs\trading\Scripts\python.exe -m live.tui
C:\venvs\trading\Scripts\python.exe -m live.tui.app
```

| File | What it holds |
|---|---|
| `live/tui/app.py` | **`main()`** — loads `Layout.load()`, constructs `MomentumApp`, calls `.run()` — plus `if __name__ == "__main__": raise SystemExit(main())` |
| `live/tui/__main__.py` | Two lines: `from .app import main`, `raise SystemExit(main())` |

**The launcher is not a second place where configuration lives.** All of the behaviour is in
`main()`; `__main__.py` only calls it. **No setting acquires a default there** (`SPEC.md` §4.4) —
there is no argument parsing, no flags, and no fallback values.

**`main()` loads the layout explicitly rather than letting `MomentumApp.__init__` default it.**
Two reasons, both recorded in its docstring: a launcher is the classic place a default appears,
and loading before `.run()` means a malformed `config/layout.yaml` raises on a terminal that
still works rather than one mid-teardown of the alternate screen buffer.

### What it renders on a 209 × 54 terminal

Captured from the real command, not from a pilot — the SVG Textual writes at
`TEXTUAL_SCREENSHOT`, converted back to text:

```
+- WATCHLIST ------------------ no ingest today ++- ATTACHED ------------ not attached ++- TAPE ---------- no source +
  — (no watchlist ingested today)                 — (nothing attached)                  — (no tape subscription in this slice)
  1 of 1 · end                                    1 of 1 · end                          1 of 1 · end

+- SIZING --------------------- not transmitted ++- RISK ------------- not transmitted ++- HEALTH --- updates · none yet +
  1R        — (no account snapshot)               day P&L   — (no trades today)          sources     — (no feed connected)
  shares    — (no entry, no stop)                 open R    — (no positions)             last seen   — (nothing seen)
                                                                                         frames/ticks — (no ticks received)
  risk      — (no account snapshot)               daily limit — (no account snapshot)    regime       (no file for today)

+- PIPELINE ------------------------------------------------------------------------------ 1 of 12 built +
   1 ingest      [ NOT BUILT · S013 ]
   2 regime      -> HEALTH panel
```

*(Columns are compressed above to fit this note; the real frame is 209 wide. Seven panels, all
present.)*

**One thing worth naming: the borders came out ASCII — `+-` rather than `┌─`.** That is
`ascii_safe()` doing its job for the capture environment's output encoding, which is the wider
trigger **OBS-007** already records as disagreeing with `SPEC.md` §4d's `SSH_CONNECTION`. **It is
not a new defect and it is not evidence about what Christoph's PowerShell will render** — his
console may well take the box characters. Flagged so the screenshot above is not read as the
promised appearance.

## 3. The launch test, red then green

`live/tests/test_launches_as_a_program.py` — **three tests, all subprocess.**

**An import-and-assert-it-exists test was explicitly not written**, per `029`: it would pass
against an entry point that raises on its first line. **And `returncode == 0` is not the
assertion either — exit 0 IS the bug.** What is asserted is that the process *reached the point
of rendering*, evidenced by an SVG of the screen containing all seven panel titles. The
assertions are ordered so the missing screen is named before the exit code.

### Red, against the pre-fix `app.py` — quoted verbatim

```
FAILED live/tests/test_launches_as_a_program.py::test_the_command_reaches_the_point_of_rendering[live.tui]
FAILED live/tests/test_launches_as_a_program.py::test_the_command_reaches_the_point_of_rendering[live.tui.app]
FAILED live/tests/test_launches_as_a_program.py::test_it_starts_with_no_broker_and_says_why_each_panel_is_empty
3 failed in 3.32s
```

```
E   AssertionError: python -m live.tui.app produced no rendered screen.
      exit code : 0   <- 0 here is the DEFECT, not the pass
      stdout    : ''
      stderr    : ''
    The module was imported and the process ended without the app ever running. That is 029: no entry point.
```

```
E   AssertionError: python -m live.tui produced no rendered screen with no broker present.
      exit code : 1   <- 0 here is the DEFECT, not the pass
      stderr    : "C:\\venvs\\trading\\Scripts\\python.exe: No module named live.tui.__main__; 'live.tui' is a package and cannot be directly executed"
```

**The two commands failed differently and that is the useful part.** `-m live.tui.app` exited
**0 in total silence** — byte-for-byte Christoph's UAT. `-m live.tui` exited **1 with a real
message**. Only one of those two failure modes is detectable by a human running the command, and
the app shipped with the undetectable one.

### Green, after

```
live\tests\test_launches_as_a_program.py ...                             [100%]
3 passed in 7.32s
```

### The mechanism, and one trap in it

Textual **8.2.8**. The driver is selected by environment —
`TEXTUAL_DRIVER=textual.drivers.headless_driver:HeadlessDriver` via `App.get_driver_class` — **so
the launcher needs no test-only flag.** `TEXTUAL_SCREENSHOT=1` uses Textual's own `App._ready`
hook: it saves the SVG and calls `exit()`, which is both the evidence and the reason the test
terminates. `COLUMNS`/`LINES` size the headless driver at 209 × 54.

**`TEXTUAL_SCREENSHOT=0` does not work on this version and fails invisibly.** `timer.py` divides
by the interval, raises `ZeroDivisionError` inside a task nobody retrieves, and the app never
exits — the run hangs to its timeout with no error. Cost me one 120-second timeout to find. The
value is `1`, deliberately, and the docstring says why.

## 4. Does it start with TWS absent? Yes, and it says why each panel is empty

**There is no broker in this environment and the app never asks for one.** It boots on
`empty_record()` and every panel states its own reason: *(no feed connected)*, *(no account
snapshot)*, *(no watchlist ingested today)*, *(no tape subscription in this slice)*, *(nothing
seen)*, *(no ticks received)*, *(no file for today)*. `SPEC.md` §4.2 — **surfaced, not refused.**

`test_it_starts_with_no_broker_and_says_why_each_panel_is_empty` pins three of those strings, so
a future launcher that exits when TWS is absent — *a refusal the user cannot read*, the same
defect one line later — goes red.

## 5. The suite

**`279 passed, 6 failed`** in the worktree. **None of the six is caused by this task**, and each
was traced rather than assumed:

| Failure | Cause | Mine? |
|---|---|---|
| `test_evidence_carry_intact::test_every_carried_file_is_present` | `records/` is gitignored, so it exists only in `D:\Dev\momentum` and not in any worktree. 149 parquet files reported missing | **No — worktree artifact** |
| `test_evidence_carry_intact::test_no_carried_file_has_been_modified` | `docs/observations/session-defined-twice.md` — CRLF vs LF. **OBS-033**, below | **No — and it is a real finding** |
| `test_spec_pointers::test_claude_md_pointers_resolve` | Six `records/` and `records/tape/` pointers in `CLAUDE.md`, same absent folder | **No — worktree artifact** |
| `test_sync_from_drive::test_the_destination_paths_are_inside_the_repo` | `config/sync.yaml` names absolute destinations under `D:\Dev\momentum`, which is not inside the worktree | **No — worktree artifact** |
| `test_handoff_state_declared::test_every_task_file_declares_a_state` | Inbox `021`–`027` carry `status: READY` frontmatter, not a `**Status**` header. **This is OBS-031** | **No — pre-existing** |
| `test_uat_has_a_file::test_every_declared_uat_exists_as_a_file` | `020`'s done-note names a UAT that no file in `christoph/` declares | **No — pre-existing** |

**029 itself does not add a seventh.** The synced task file carries `**Status** WRITTEN` and is
not among the offenders in the state-header failure — I checked the list rather than assuming.

**The four worktree artifacts all go away on merge into `D:\Dev\momentum`.** They are red for
*where the tests ran*, not for what changed.

**Two new `BOOTSTRAP_ALLOWLIST` entries**, `live/tui/__main__.py` and
`live/tests/test_launches_as_a_program.py`, taking the count to **33**. Both authored here —
**OBS-008 stands**, and this is the fourth task in a row to add to a list that is supposed to
hold exceptions.

### A red I caused and removed, worth one paragraph

**My first draft of the OBS-034 row quoted the legacy regime-snapshot path literally, and
`test_no_legacy_regime_snapshot_path` went red on the ledger row describing the problem.** It
was caught by a `verify.ps1` run reporting **7 failed** where my own `pytest` run minutes earlier
had said 6 — the discrepancy was the whole signal. The row now names the string instead of
spelling it. **Recorded because a re-measure caught a number I would otherwise have carried
forward, which is `028` §4's failure avoided rather than repeated.**

## 6. Ledger — three rows, not one

`029` asked for one row. **Two more findings surfaced while diagnosing the suite, and
`CLAUDE.md` requires a row for a finding a done-note names.** Neither is acted on.

| Row | What |
|---|---|
| **OBS-032** | **The suite tests `live/` as a library; the UAT tests it as a program.** Third green suite over a broken `live/`. `029`'s own words. **The general rule — every slice adding a user-facing command needs a launch test — is NOT enforced**, and `029` forbids generalising beyond this one command, so the row carries the gap |
| **OBS-033** | **One carried evidence file's recorded hash can never be reproduced by a checkout.** `session-defined-twice.md` is recorded at `77ef9f79…` (CRLF, 3,012 bytes, 64 CRLF pairs — the copy in `D:\Dev\momentum`), while `.gitattributes` pins `eol=lf` and git writes `b90faf85…` (2,948 bytes). **Red in any fresh clone, green only in the one working copy that predates the attribute.** The other 178 rows match. **Not repaired** — re-recording the hash would make an evidence ledger agree with a file normalised *after* it was carried |
| **OBS-034** | **A worktree under `.claude/worktrees/` turns two tests red in the main checkout**, because both walk the filesystem and a worktree is a second full copy of the repo. **Not fixed** — both tests carry an explicit *do not add a prefix to an exemption list* warning, and one derives its exemption rather than listing it. Transient: it clears when the worktree is removed |

All three `OPEN`, review-by **2026-11-13**.

## 7. What I could not do

**1. I could not merge, and until someone does, none of this is in `D:\Dev\momentum`.** The
entry point exists on `worktree-029-entry-point` only. `python -m live.tui` in the main checkout
still does nothing. **The `013` UAT is blocked on the merge, not on the code.**

**2. I did not run `export-handoff.ps1`, and this is a deviation from `CLAUDE.md`.** Run from the
worktree it would write a manifest recording a `HEAD` that exists **only on a temporary branch
that is deleted with the worktree** — an unresolvable hash, in a mirror that is additive and
deletes nothing, ever. A wrong HEAD there is permanent. **Run it from `D:\Dev\momentum` after
merging** and it records the right commit:

```powershell
cd D:\Dev\momentum
.\export-handoff.ps1
```

**3. I did not run the app interactively.** A real TUI in this session would block until killed;
every observation about rendering above comes from the headless driver at 209 × 54. **What a
real PowerShell console does with the box-drawing characters is untested here** — see §2.

**4. I did not verify the fix against the main checkout's suite**, for the reason in OBS-034: my
own worktree pollutes that run. The main-checkout baseline I did take showed **6 failed, 276
passed**, of which two — `test_pytest_collection` and `test_regime_snapshot_path` — were caused
by the worktree's mere existence and will clear when it is removed.

**5. I did not resolve the `026` conflict the sync reported** (§8). Not mine to resolve.

**6. `christoph/done/014-for-christoph-account-parameters.md` is untracked in the main
checkout** and has no row in the UAT review register, so `test_observations_ledger` has two
failures there that are invisible from the worktree. **Committing it and giving it a register
row is Christoph's**, and it is a live red in his tree right now.

## 8. The inbox sync, and a conflict it reported

`029` arrived through `026`'s copier — run with the `handoff_inbox` pair redirected at this
worktree, everything else verbatim from `config/sync.yaml`:

```
handoff_inbox: 1 new · 029-for-code-the-app-has-no-entry-point.md · 1 differing
  !! DIFFERS, NOT OVERWRITTEN: 026-for-code-inbox-sync-from-drive.md
       source 2b4b07346453fc8b152b99e868a9b4c9adab10ece8dd0c061906e68b88ae9049
       repo   c7257a6f4600e179fb2e1953dddcd75b31c97c1635a6568b970ebe215d00fbe6
  ok source folder byte-for-byte unchanged (4 files hashed before and after)
```

**The `026` conflict is pre-existing and the copier did exactly the right thing** — the repo copy
is untouched. It needs a person, and it is the mechanism working rather than a fault.

## 9. `verify.ps1`

Run at **2026-08-13 16:11:12 +02:00**, from the worktree. Its section 1 reads
`6 failed, 279 passed, 1 warning in 16.29s` — the six accounted for in §5. **Output not quoted, per HANDOFF-PROTOCOL
v1.2** — it is in `verify-output.txt` at the worktree root, which is gitignored.

---

## THIS NOTE MUST BE PASTED TO CHAT

**The design session cannot see this repo, and `export-handoff.ps1` has not run for the reason in
§7.** Nothing else carries it. On 2026-08-11 two correct done-notes were written and never
reached the design session, which held a stale `RUNNING` for both — **and this one is worse than
that case, because the work is on an unmerged branch that a session cleanup could delete.**

**The two actions, in order: merge `worktree-029-entry-point`, then run `export-handoff.ps1` from
`D:\Dev\momentum`.** The `013` UAT can be run after the first one.
