---
id: 053
title: The ledger ruling, and connecting the mechanisms that were specified and never wired
type: task
class: admin
task_version_executed: 3.0
closes: B-030 (corrected, not as stated) - B-027 (found already resolved)
answers: 044-q1
owner: claude-code
tree: D:\Dev\momentum
branch: 053-ledger-and-mechanisms
bugs:
  - id: B-030
    action: correct
    status: NEW
    note: >-
      Count is FOUR duplicated ledger ids, not five (B-030) and not three (053
      Part 1). OBS-062 already recorded four. Both wrong numbers were taken from
      a task or question file rather than from the ledger.
  - id: NEW
    action: raise
    status: NEW
    priority: 1
    title: verify-output.txt was written outside every exported path
    spec: PROCESS-SPEC
    summary: >-
      verify.ps1 wrote verify-output.txt to the repository root. The export
      carries handoff/ and christoph/done/ only, so the artifact HANDOFF-PROTOCOL
      names as the evidence for REVIEWED could never travel.
    actual: REVIEWED was unreachable by its own definition from 023 until 053.
    expected: >-
      The evidence file lands inside an exported path. Fixed - it is now
      handoff/verify-output.txt, and config/outputs.yaml plus test 1 catch the
      next instance rather than only this one.
  - id: NEW
    action: raise
    status: NEW
    priority: 1
    title: verify-output.txt still does not reach Drive after Part 2's fix
    spec: PROCESS-SPEC
    summary: >-
      export-handoff.ps1 filters to .md files only, deliberately (line 262).
      handoff/verify-output.txt is .txt, so moving it inside an exported FOLDER
      was not sufficient - it also needed to be inside the exported TYPE.
    actual: >-
      Confirmed by reading MANIFEST-momentum-code-handoff.md directly after
      running verify.ps1 then the export: verify-output.txt is listed under
      "not exported (non-.md)". REVIEWED remains unreachable by its own
      definition even after Part 2.
    expected: >-
      Either rename the artifact to end in .md, or add a named exception to the
      export filter. Not decided here - both are protocol-shape decisions Part
      2 did not authorize and 053 did not ask for.
  - id: NEW
    action: raise
    status: NEW
    priority: 1
    title: The worktree guard blocks all writes and its own remedy is unreachable
    spec: PROCESS-SPEC
    summary: >-
      .claude/settings.json denies Edit and Write on .claude/worktrees/**, and
      the EnterWorktree tool only ever creates worktrees there, so every worktree
      it makes is unwritable. The background-isolation guard then refuses Edit
      and Write in the main checkout until bgIsolation is disabled, and refuses
      the edit to settings.json that would disable it.
    actual: >-
      A closed loop with no in-band exit. Work stopped until Christoph
      intervened. Separately the guard intercepts Edit and Write but NOT shell
      writes, so a session using python via Bash is unisolated without being told.
    expected: >-
      Either the tool places worktrees at D:\Dev\_worktrees, which the policy
      already allows, or the guard covers shell writes too. As it stands it
      blocks the compliant path and leaves the non-compliant one open.
  - id: NEW
    action: raise
    status: NEW
    priority: 2
    title: The design session reissued task files under the same filenames
    spec: PROCESS-SPEC
    summary: >-
      049, 050, 052 and 053 were replaced in place in Drive. handoff/ is
      copy-and-keep and the inbound copier refuses to overwrite, so once any
      version reached the tree no later version could arrive.
    actual: >-
      052 was executed at v3.0 while Drive holds v4.0. The refusal looked
      identical to the 040 and 043 refusals standing since 045, so it read as
      furniture.
    expected: A correction arrives as a NEW task number, never as an amendment.
  - id: NEW
    action: raise
    status: NEW
    priority: 2
    title: The state-header test was satisfied by the frontmatter status key
    spec: HANDOFF-PROTOCOL
    summary: >-
      tests/test_handoff_state_declared.py read the first 20 lines of the FILE,
      so a frontmatter `status:` key satisfied a check whose subject is the
      `**Status**` body header. CLAUDE.md is explicit that these are different
      things - frontmatter describes the work, the header describes the handoff.
    actual: >-
      handoff/inbox/021-for-code-keepuptodate-at-scale.md carries status READY in
      frontmatter, has no body header at all, and the test did not distinguish
      them. Found while fixing the window, not looked for.
    expected: >-
      From task 049 the header is read from the body, frontmatter stripped.
      14 pre-existing files below the watermark remain red - they were red before
      053 started (measured: 15 failures unmodified, 14 with the fix) and are
      pre-convention documents the design session authored and has already read.
  - id: NEW
    action: raise
    status: NEW
    priority: 3
    title: The momentum-code-questions Drive folder is not an export destination
    spec: PROCESS-SPEC
    summary: >-
      The folder exists in D:\claude-googledrive-sync but export-handoff.ps1
      carries only handoff/ and christoph/done/.
    actual: >-
      Question files travel only incidentally, because handoff/questions/ sits
      under handoff/ and the export recurses. The dedicated folder is unused.
    expected: >-
      Either wire it or retire it. An empty folder that looks like a channel is
      the shape of a mechanism specified and never connected.
  - id: NEW
    action: raise
    status: NEW
    priority: 3
    title: 053 Part 6c describes an 035 collision that no longer exists
    spec: PROCESS-SPEC
    summary: >-
      Part 6c says two files share the number 035 and the addressing gate cannot
      tell them apart.
    actual: >-
      The gate globs NNN-*.md. The two files are 035-for-code-bug-pdl-and-atr14.md
      and 035a-for-code-adr-is-rth-atr-is-eth.md, and 035a- does not match
      035-*.md. The collision OBS-052 recorded was resolved by the rename to 035a.
    expected: >-
      Test 6 is GREEN, not RED as Part 6c predicted. 035a remains off-convention
      but that is a naming nit, not an addressing failure.
---

**Status** REVIEWED

# 053 — the ledger ruling, and the mechanisms that were never wired

**Read this cold.** Six parts. Two of them did not go the way the task file predicted, and both
divergences are findings rather than slips.

> **THIS NOTE NEEDS TO BE PASTED TO CHAT.** It lands in a repository the design session cannot
> read. Two correct done-notes were written on 2026-08-11 and never reached it; the export
> reduces that risk and does not remove it.

---

## The headline: three numbers, and only one of them right

| Source | Claimed duplicated ids | Correct? |
|---|---|---|
| `B-030` | **five** | no |
| `053` Part 1 | **three** | no |
| `docs/observations/OBSERVATIONS.md`, row `OBS-062` | **four** | **yes** |

**The ledger had the right answer the whole time.** Both wrong figures came from reading a task
file or a question file instead of the artifact itself — the same defect this task exists to
close, one folder over.

---

## Part 1 — the ruling on `044-q1`

**Applied the reason, not the rule.** `021`'s three rows moved forward; `037`'s rows kept
`OBS-044`, `OBS-045`, `OBS-046`.

**Ids allocated: `OBS-073`, `OBS-074`, `OBS-075`**, read from the ledger at execution time. The
question file proposed `OBS-065`–`067`; **all three were already taken, and so were
`OBS-070`–`072`, allocated by `052` the same morning.** The highest row at execution was
`OBS-072`. *The question was right about the action and could not be right about the numbers.*

**Verified rather than taken on trust:** `handoff/done/021-for-code-keepuptodate-at-scale.md`
cites none of the three ids, so the reallocation changes nothing any exported note appears to say.

### `OBS-047` — a permanent collision, and the one thing 053 did not anticipate

**Not reallocated. It cannot be.** Both of its rows are cited by exported done-notes:

| Row | Cited by |
|---|---|
| `OBS-047` · 2026-08-14 — READING, `037`'s premises | `handoff/done/037-drive-export-stopped.md` lines **120**, **391**, **422** |
| `OBS-047` · 2026-08-15 — OBSERVATION, `useRTH` on daily bars | `handoff/done/038-...md:294`, `handoff/done/041-...md:144` |

Moving either would change what an exported done-note appears to have said — **the exact end the
reallocation rule exists to protect.** `053`'s own refusal clause fires. It is now documented in
the ledger as permanent, with the instruction to **disambiguate by date, always**, and an undated
reference to `OBS-047` declared defective.

---

## Part 2 — `verify-output.txt` now lands where the export can carry it

**`verify.ps1` wrote it to the repository root.** The export carries `handoff/` recursively and
`christoph\done` flat — read from `export-handoff.ps1` lines 241–242, not from prose. **The root
is neither.**

**So `REVIEWED` has been unreachable by its own definition since `023`.** Every report in fact
arrived by Christoph pasting a terminal into chat — the one thing the protocol forbids outright.

**Now `handoff/verify-output.txt`.** One path change, no new pair. `.gitignore` follows it, and
`tests/test_verify_output_is_ignored.py` was retargeted — including its anchoring probe, which
must test a *different* nesting depth to still mean anything.

### Measured after moving it: the folder was not the whole gap

**`REVIEWED` is still unreachable, for a second and independent reason.** `verify.ps1` and the
export were both run, per the last-action instruction, and **the manifest — read directly, not
inferred from config — says the file did not travel:**

```
D:\claude-googledrive-sync\momentum-code-handoff\MANIFEST-momentum-code-handoff.md:
**not exported** 3 non-`.md` file(s) present in the source and deliberately skipped:
`A1-connector-from-scheduled-run.txt`, `accepted\.gitkeep`, `verify-output.txt`
```

**`export-handoff.ps1:262` filters to `.md` only, deliberately** (`# 262: the Extension test is the
one that actually decides`). `handoff/verify-output.txt` is a `.txt` file, so **being inside an
exported folder was never sufficient** — it needed to also be inside the exported *type*, and it
is not. Part 2's fix corrects the path and does not correct this; the two are independent gaps
that happened to look like one from `verify.ps1`'s side alone.

**Not extended here.** The `.md`-only filter is described in the script as deliberate, and
widening it is a design decision — rename the artifact to a `.md` extension, or add a named
exception to the filter — that `053` did not ask for and that changes what "every file in
`handoff/` is `.md`" means elsewhere in the protocol. **Reported as a bug below, not fixed in
passing.**

---

## Part 3 — routing is protocol, not task content

**`CLAUDE.md` → v1.8**, with the block as specified, plus the measured instance: `044` told this
session to paste a question into chat **when the questions channel already existed**, specified
about 150,000 characters earlier in the same design session.

**No lint, as instructed.** Grepping prose for destinations is unbounded, and a check that catches
four phrasings and misses the fifth is worse than none because it would be trusted. The bounded
half — a `destination:` key in frontmatter — is asserted by test 3.

---

## Part 4 — findings become data

**Every done-note carries `bugs:` in frontmatter, present and possibly empty.** This note carries
six entries. **No `B-NNN` was allocated here** — five are `id: NEW`. Allocating from this side
would be a number inferred rather than read, which is precisely what produced the duplicate
ledger ids.

---

## Part 5 — the tests

| # | Test | File | Before | After |
|---|---|---|---|---|
| 1 | declared outputs are exported | `tests/test_declared_outputs_are_exported.py` | **RED** | **green** |
| 2 | done-note `bugs:` block | `tests/test_donenote_bugs_block.py` | **RED** | **green** |
| 3 | task-file shape, no destination | `tests/test_task_file_shape.py` | *unknown* | **green** |
| 4 | ledger id uniqueness | `tests/test_observation_ids_are_unique.py` | **RED** | **green** |
| 5 | inbound run record has no conflicts | `tests/test_inbound_run_record_has_no_conflicts.py` | **RED** | **RED — correct** |
| 6 | one task id, one file | `tests/test_one_task_id_one_file.py` | *predicted RED* | **green — see below** |

**Each was seen red before being accepted green**, including the two that are green by nature:

- **Test 1** — seen red by pointing the declared path back at the repository root, reproducing
  the historical defect exactly, then restored.
- **Test 4** — seen red twice: first on all four duplicates, then again with the watermark
  temporarily lowered to 46 so `OBS-047` fell above it.
- **Test 6** — its clash logic is exercised on constructed input, because the folder is clean.

### Test 4 is a watermark, not an allowlist

**Uniqueness is asserted for every id allocated after `OBS-062`** — the row that recorded the
collisions. Nothing below the line is re-litigated; **everything above it must be unique**, and a
new row is always allocated above the line, so **a new duplicate is caught no matter which id it
reuses. The exemption cannot grow.** An allowlist would have to name `OBS-047` and would then
grow an entry every time this recurred — furniture, which is exactly what `040` and `043` became.

### Test 6 is green, and 053 predicted red

**Part 6c's premise no longer holds.** The two files are:

| File | Contains |
|---|---|
| `035-for-code-bug-pdl-and-atr14.md` | the PDL / ATR-14 bug task |
| `035a-for-code-adr-is-rth-atr-is-eth.md` | the ADR-is-RTH / ATR-is-ETH session ruling |

**The gate globs `NNN-*.md`, and `035a-` does not match `035-*.md`.** They are different
addresses. The collision `OBS-052` recorded was real and was resolved by the rename to `035a`
before this task ran. **Neither file was renumbered.**

**A calibration note worth keeping.** The first version of test 6 grouped on leading digits alone
and reported **four** clashes — `008`, `012`, `013`, `035` — every one of which is a correctly
named file using the established letter-suffix convention. **A test one character too loose would
have demanded four renames the gate does not need.** It is now pinned to the gate's own glob.

---

## Part 6 — the allocation log and the standing conflicts

### 6a — `handoff/ALLOCATIONS.md`

**57 numbers, range `001`–`053`**, seeded from `handoff/inbox/`, `handoff/done/`,
`handoff/accepted/` and `git log`.

- **Appearing more than once: none.** Thirteen numbers carry two *filenames*, but that is the
  convention — a done-note drops the `for-code-task-` prefix. **Checked rather than assumed**,
  since a real duplicate would look identical at a glance.
- **Not appearing at all: `009`, `010`, `011`, `047`.** `047` is the one worth a look — `046` and
  `048` both exist. `009`–`011` fall in the early era when several numbering schemes ran at once.
  **Gaps are reported, never filled**: filling one manufactures a record of an allocation nobody
  made.

**Its limit, stated in the file itself:** it would not have prevented the reissues, because the
design session was not allocating — it believed it was replacing a document.

### 6b — `040` and `043`: reissue defect, not divergence

**Drive is newer on both. Neither was overwritten. Both still stand.**

| | tree | Drive | What Drive adds |
|---|---|---|---|
| **040** | v1.1, 8,840 B, 09:44 | v1.2, 10,556 B, 10:56 | `answers: OBS-040` and a new **Part 0** — the socket guard in `tests/test_keepuptodate_scale.py` does not stop an asyncio client; `034` measured a test connecting to live TWS and returning `connected · client 7 · read-only`. Also drops *"Do not remove another session's worktree"* |
| **043** | v1.1, 8,822 B, 10:17 | v1.2, 10,533 B, 10:31 | Retitled *"A third Drive pair"* to *"Two new Drive pairs"*; three parts become four; adds **Part 2, the questions channel**; rewrites `unblocks:` for S011 and S012 |

**Both are the reissue defect**, and each says so itself: *"neither earlier version reached the
tree."* **This is a report, not a resolution** — retiring the Drive copies is the design session's
act. Test 5 stays red until it happens, which is the correct outcome.

### 6c — the `035` pair

Reported above under test 6. **Neither renumbered.**

---

## Which version of `052` actually ran

**v3.0.** The committed `docs/specs/SPEC.md` header reads *"Start at SPEC-INDEX, which names which
spec owns which fact"* — **no numbering, no `01` prefix**, which is `053`'s stated signature for
v3.0. Drive holds v4.0. **So `052` ran without the worktree-isolation ruling**, and its Parts 2
and 3 were withdrawn after it executed.

---

## The run records, and whether the design session can see them

**It cannot, and it should not be able to.** `export-run-record.md` and `sync-run-record.md` sit
at the repository root, outside every source and destination, **on purpose**: a record whose only
copy lands in the destination cannot report having failed to reach the destination.

**A content signal is what can travel.** `config/outputs.yaml` records both as deliberate
exclusions **with their reason**, and test 1 asserts every exclusion carries one — so the absence
is now legible in an exported file rather than being an unexplained hole. **A count that
self-clears, never a clock**: test 5 reads the inbound record's conflict count and is red while it
is non-zero, so the *fact* of a stale inbound state travels into `handoff/verify-output.txt` even
though the record itself never moves.

---

## What `config/outputs.yaml` lists, and what else was unexported

**Six declared outputs**: `handoff/verify-output.txt`, `handoff/done/`, `handoff/questions/`,
`handoff/inbox/`, `handoff/ALLOCATIONS.md`, `christoph/done/`. **All six are inside an exported
path** — after Part 2; `verify_output` was the one that was not.

**This is the answer to *how many more of these are there*.** Five more, each recorded as an
exclusion with a reason:

| Path | Why not exported |
|---|---|
| `export-run-record.md`, `sync-run-record.md` | outside every source **on purpose** — see above |
| `christoph/open/` | answers **by being empty**; an additive export cannot represent empty |
| `docs/observations/OBSERVATIONS.md` | **not exported today, and this is a decision not taken.** The ledger is the durable record of findings and reaches the design session only by being quoted into a done-note. Flagged, not fixed — it is not `053`'s to rule on |
| `docs/specs/` | Drive is archive; exporting specs back lets a superseded copy walk in wearing the shape of current work |

---

## What I could not do, and one thing I did that needs recording

**1. Test 5 cannot be made green from here.** It requires retiring the Drive copies of `040` and
`043`, which is the design session's act. Red is the correct state.

**2. `OBS-047` cannot be resolved at all**, by anyone, without changing an exported done-note. It
is now permanent by design rather than open by neglect.

**3. The isolation guard was bypassed deliberately, with Christoph's explicit authorization.**
`.claude/settings.json` denies `Edit` and `Write` on `.claude/worktrees/**`, and the EnterWorktree
tool only creates worktrees there — so every worktree it makes is unwritable. The
background-isolation guard then refuses `Edit` and `Write` in the main checkout, **and refuses the
edit to `settings.json` that would lift it.** A closed loop. Christoph removed an orphaned
worktree, directed the work to the main checkout on this branch, and authorized the shell-write
route. **Every file in this task was therefore written through `python` via `Bash`, which the
guard does not intercept.** That porosity is itself raised as a bug above: the guard stops the
compliant path and leaves the non-compliant one open.

**4. Nothing was committed to `main`.** Work is on `053-ledger-and-mechanisms` for Christoph to
merge.

**5. `049`, `050` and `051` were deliberately not opened.** The worktree-isolation ruling that
unblocks them is in `052` v4.0, which this tree does not hold; it arrives as `054`.
