---
id: 016
title: The verification harness, three record-keeping defects, and a ledger for findings
status: RUNNING — stays RUNNING until this note reaches the design session
owner: claude-code
ran: 2026-08-12, 11:50 → 14:10 ET
tree: D:\Dev\momentum
---

# 016 — verify.ps1, three defects, and the ledger

**Status** RUNNING

**All eight parts are done except part 7, which Christoph ruled out mid-task.** The tree is
**clean** and the suite is **144 passed, 0 failed**. Both failures 016 was written to clear are
cleared, and no new one was introduced.

> **This note has to be pasted into chat.** Writing it is not reporting it.

---

## `verify.ps1` — first run, verbatim

Run **after** everything below had landed and been committed, so it describes the tree this
note describes.

```
verify.ps1  --  D:\Dev\momentum
run at 2026-08-12 14:06:45 +02:00

========================================================================
  1. SUITE — the pytest summary line, verbatim
========================================================================
============================= 144 passed in 2.44s =============================

========================================================================
  2. GIT STATUS — every uncommitted path
========================================================================
(clean — no uncommitted paths)

========================================================================
  3. HEAD — the commit this output describes
========================================================================
  e9dd8d1f89d7ee49210b5988e6263eb9b3747ffb Record Christoph's christoph/ and accepted/ files, unmodified

========================================================================
  4. EVIDENCE — sha256 recomputed from EVIDENCE-CARRY.md
========================================================================
  179 rows checked, 0 mismatches, 0 missing

------------------------------------------------------------------------
verify.ps1 runtime: 5.0s
  of which pytest: 3.8s

verify.ps1 states four facts and draws no conclusion from them.
The reading belongs to the design session.
```

**The 100-second warning did not fire, and that is itself the answer to part 2.** The suite is
2.44 s. The warning path exists and is written; it has never been seen firing, which is stated
here rather than left to be assumed tested.

The re-hash is an **independent reimplementation** and does not import
`test_evidence_carry_intact` — 014's reasoning, that a bug in the test would otherwise mask a
real drift and both would agree.

---

## Part 2 — `test_no_secrets` runtime, measured

| | |
|---|---|
| **before** | **`9 passed in 126.13s`** |
| **after** | **`10 passed in 0.25s`** |

**505× faster**, and the extra test is the guard below.

`records` and `records_truncated` are back in `SKIP_DIRS`, as the predecessor had them. **This
narrows WHERE, never WHAT** — the suffix list is untouched, `.jsonl` is still scanned
everywhere else, and there is no size cap and no sampling.

`test_the_records_skip_narrows_where_and_not_what` asserts both: that `.jsonl` is still a text
suffix, and that no `st_size` / `MAX_BYTES` / `islice` / slice-on-read appears in the file
walk. **A cap would silently stop scanning a large file that IS tracked, and would look
identical to a clean run.**

**A defect I introduced and caught.** The first version of that guard searched the whole module
for its banned words and **failed on its own list of them** — the fourth self-reference trap in
this project. Fixed by checking `inspect.getsource(candidate_files)` instead of the file: look
only where a cap could actually be applied. **This is the fourth time the fix has been
positional rather than an exclusion**, and the pattern is now reliable enough to reach for
first.

---

## Part 3 — the discriminator, and why it is this one

**Chosen: STRUCTURAL, with a two-property derivation.** A `.md` file is a record when it

1. **declares one of the five handoff states in its first 20 lines**, or
2. **is recorded in `EVIDENCE-CARRY.md`** — Resolution D reused, not re-invented.

Plus **one explicitly named exception**, `docs/specs/DRIVE-ARCHIVE-LIST.md`.

### Why not a bare date header

It was the obvious structural candidate and it is **wrong, for a reason worth recording**:
`SPEC.md`, `BUILD-PLAN.md` and `REGIME-PROMPT.md` all carry dated headers — **and all three
named a `claude/`-rooted directory before H8.** A date rule would have exempted precisely the
three files where a reintroduced live pointer would matter. **`CURRENT` is deliberately not one
of the five states**, which is what makes the state rule discriminate where a date rule cannot.

### Why `EVIDENCE-CARRY.md` had to be the second property

Two carried predecessor task files contain the legacy path and predate the five-state
vocabulary entirely: `handoff/inbox/H8-regime-snapshot-path.md` says `**Status** OPEN`, and
`handoff/inbox/H9 — Commit the specs into the repo.md` has no header at all. **They may not be
edited** — carried evidence is byte-identical or it is not evidence. Without property 2 the
derivation would have demanded exactly the edit the carry rule forbids.

### Why `DRIVE-ARCHIVE-LIST.md` stays a named exception

It is a **`STATUS CURRENT` spec that inventories history**. Any rule broad enough to reach it
reaches every other live spec. **Naming one file is honest; widening the rule to swallow it
would not be.**

### The guards

| guard | what it refuses |
|---|---|
| **1** | Any exempted path that is not `.md`. **This is what makes the derivation safe** — a live pointer lives in code or config |
| **2** | A file with neither property. Four fixtures: no header, `CURRENT`, `OPEN`, and a state declared *below* the header region — the positional rule, so a document cannot exempt itself by discussing handoff states |
| **3** | `SPEC.md`, `BUILD-PLAN.md`, `REGIME-PROMPT.md` being exempt, by name. The three that carried the wrong path |

Plus `test_the_derivation_actually_exempts_the_case_it_was_built_for`, which asserts
`christoph/done/006` is exempt **and** that the tree name is not hardcoded in the deciding
function — so it cannot pass for the wrong reason.

**That test also hit the self-reference trap** — its own hardcode check contained the string it
forbids. Fixed the same way: check `inspect.getsource(is_a_record)`, not the module.

### The derivation's known limit, stated rather than discovered

**A `.md` carrying a genuine five-state header can shelter a live pointer.** Refusal C proved
it (below). This is inherent: the property being tested is *is this a record*, and a document
declaring `DONE` **is** a record by the rule.

Why it is accepted rather than patched: **nothing reads a path out of a done-note.** A legacy
path in prose is not a live pointer in the operative sense, and guard 1 keeps the exemption out
of every place where it would be. **The derivation cannot tell the two apart and does not
pretend to.**

---

## Part 4 — `CLAUDE.md` v1.2, and two more versions

**v1.2** — line 159 named a subfolder with a trailing slash and no parent, prose shorthand for
`christoph/done/`. One word. **Recorded as its own version because rule 9 has no size
threshold**: a version that skips small fixes stops being a reliable identity for the file. The
row says what it was — a broken pointer introduced by the v1.1 re-supply, not a content change.

**Edited in place. No replacement was accepted from outside the tree.**

**Other bare-folder shorthand: exactly one instance, the one the test flagged.** Grepped for
`open`, `done`, `accepted`, `inbox`, `questions` written with a trailing slash and no parent.

**The history row reintroduced the defect twice while recording it.** First by quoting the
broken token in backticks; then, after that was fixed, by *enumerating four more* — `open/`,
`accepted/`, `inbox/`, `questions/` — which the pointer test read as four new unresolvable
paths. **A version-history row recording a broken pointer is the most likely place to
re-create one**, and it is now worded without trailing slashes, with that reason stated in the
row itself.

**There is an existing `OBSOLETE_MARKERS` mechanism that would have swallowed all of this** —
a line containing "no longer" or "obsolete" is skipped. **I did not use it.** Wording a line to
satisfy a test is the reflex this project exists to resist, even when the mechanism was built
for that case.

**v1.3 and v1.4** are parts 5a and 6, each its own version and row, per the instruction not to
batch.

---

## Part 5 — the ledger

### 5a — the convention carried forward

`momentum-harness/CLAUDE.md`'s observations section is now re-stated in the active tree's
`CLAUDE.md` as **v1.3**. **Read from the archive; the archive was not modified.**

The task's framing is exactly right and worth keeping: the convention *"sits beneath a banner
declaring that everything below it is not current guidance — the project's most-named failure
applied to the machinery for handling the project's failures."*

### 5b — `docs/observations/OBSERVATIONS.md`

**Thirteen rows.** All twelve seeded from the table in 016 §5b, **plus nothing else** — no row
was re-derived, re-measured or improved, and every row cites its producing source.

`kind` marks **OBSERVATION** or **READING**. Two are readings:

- **OBS-005** — Cboe One plus odd-lot filtering as the cause of the 5.32× gap. **Recorded
  separately from OBS-004, the measurement**, on purpose: the magnitude stands whether or not
  the explanation does.
- **OBS-013** — the 209-column reading.

### The one row I changed, and why it is not "improving a finding"

**OBS-013 entered the ledger marked *"a reading, unverified"* — and `S009a` had measured it
that same morning.** 209 × 54, from `$Host.UI.RawUI.WindowSize`, giving 67 columns per tile
against `BOX_WIDTH = 71`. The reading was correct.

It is recorded **`PROMOTED`, with a `resolution:`** naming where it went: it became
`live/tests/test_tui_measured_against_its_tile.py`'s primary snapshot width and the
`test_no_line_ever_exceeds_the_width_it_was_given` invariant.

**This is the ledger's exit route being used, not a finding being edited.** Carrying it as
`OPEN — unverified` would have been recording something already known to be false, which is
the failure mode the ledger exists to stop, pointed at itself. **The row keeps its original
kind visibly struck through**, so the fact that a design-session inference turned out to be
right is findable later.

### 5c — the trigger

`tests/test_observations_ledger.py`, 11 tests. **Red while any row is `OPEN` past its
`review-by` date — red for being *ignored*, not for being open.** A test that fires the moment
a finding is recorded teaches people not to record findings.

- **Missing or malformed `review-by` is red.** Five malformed forms are asserted to parse as
  `None` rather than being tolerated. **Unknown is never read as answered.**
- **Deleting a row does not clear it.** `SEEDED_ROWS = 13` is a **floor**; rows may be added,
  never removed. The docstring names why: `test_open_questions.py` once keyed on a folder being
  non-empty, which made deletion the cheapest route to green on a mechanism whose purpose was
  holding things open.
- `PROMOTED`/`DROPPED` **require** a `resolution:` block, or the status is an off switch with
  no record behind it.
- Dates are **US/Eastern via `zoneinfo`**, like every other date decision here.

### The `review-by` interval: 2026-11-12, three months

**Proposed and defended:**

1. **Almost every row is blocked on a slice that has not been built.** OBS-001–005 are tape
   questions `S012`/`S016` answer as a side effect; OBS-006 needs a `BUILD-PLAN` revision;
   OBS-009–010 need `S008`. `BUILD-PLAN.md` §1 sizes a slice at one to two sessions and core
   alone is four slices. **A review date falling before the work that would settle these turns
   the ledger into a recurring interruption, and a test that cries wolf gets made green rather
   than read.**
2. **It must be shorter than the memory of why the row exists.** Three months is inside this
   project's own git history, so a reviewer can still reconstruct context.
3. **It is a floor, not a schedule.** Any row can be resolved the day its slice lands.

**All rows share one date deliberately.** Staggering would be a guess dressed as precision.

### 5d — where rows come from

Written into `CLAUDE.md` v1.3: **rows are added at done-note review**, and *"a done-note that
names a finding with no ledger row has not finished reporting it."*

---

## Part 6 — retention, recorded

`CLAUDE.md` **v1.4**. `records/tape/` is kept **indefinitely until Christoph says otherwise**,
with the reason: the 2026-08-11 QQQ session cannot be re-recorded and is Row 14's basis, and a
threshold whose basis file is gone has no source string.

**v1.1 said *"no retention rule exists yet"*, which reads as a gap somebody might helpfully
close.** It is now a decision.

**And it says explicitly that no policy for FUTURE captures is decided** — with `012`'s ~7 GB/day
figure for four tickers — *"Do not read the rule above as 'keep everything forever.'"* That
absence is stated rather than left to be inferred, which is what part 6 asked for.

---

## Part 7 — NOT DONE. Christoph ruled the instruction wrong.

**016 part 7 told this session to fix headers across `christoph/open/` and `christoph/done/`.
That collides with two governing documents**, and I raised it before doing any of it:

- `CLAUDE.md`'s handoff table: `christoph/open/` — ***"Never write here."*** `christoph/done/` —
  written by ***"Christoph only."***
- `HANDOFF-PROTOCOL.md`: ***"Christoph performs all three steps. No Claude writes to, or removes
  from, either `christoph/` folder."***

**Christoph's ruling: touch nothing. The design session supplies a replacement file and he
places it.** Nothing in `christoph/` was written, edited or removed by this session.

### The survey — one file is defective, not eleven

| file | header |
|---|---|
| `christoph/open/009-s009a-read-the-screen-at-working-width.md` | `**Status** RUNNING` ✓ |
| `christoph/done/001` | `**Status** WRITTEN` ✓ |
| `christoph/done/002` | `**Status** DONE` ✓ |
| `christoph/done/003` | `**Status** WRITTEN` ✓ |
| `christoph/done/004` | `**Status** WRITTEN` ✓ |
| `christoph/done/005` | `**Status** REVIEWED — answered by events, awaiting Christoph's confirmation` ✓ |
| `christoph/done/006` | `**Status** REVIEWED — answered by events, awaiting Christoph's confirmation` ✓ |
| `christoph/done/007` | `**Status** REVIEWED — superseded, awaiting Christoph's confirmation` ✓ |
| `christoph/done/008` | `**Status** REVIEWED — performed in conversation, awaiting Christoph's confirmation` ✓ |
| `christoph/done/012b` | `**Status** RUNNING` ✓ |
| **`christoph/done/012-uat-first-five-minutes.md`** | **`**State** OPEN`** ✗ |

### The exact defect, for whoever authors the replacement

**Three faults in one file**, `christoph/done/012-uat-first-five-minutes.md`:

1. **The key is `**State**`. It must be `**Status**`** — `HANDOFF-PROTOCOL.md` v1.1 rules the
   key name, and `CLAUDE.md` v1.1 says *"The key is `**Status**`, never `**State**`."*
2. **The value is `OPEN`, which is outside the five.** `WRITTEN · HANDED OFF · RUNNING ·
   REVIEWED · DONE` is the whole vocabulary.
3. **`**Path** `christoph/open/012-uat-first-five-minutes.md`` is stale** — the file is in
   `christoph/done/`. Retired under copy-verify-retire; the header did not follow.

**The correct value is not knowable from the repo.** Whether it is `REVIEWED` or `DONE` is
Christoph's to report — `HANDOFF-PROTOCOL.md` rule 2. The other four `christoph/done/` UATs use
`REVIEWED — <qualifier>, awaiting Christoph's confirmation`, which is the shape a replacement
would most plausibly take, **but that is a pattern, not an answer.**

**No test covers `christoph/`, so nothing is red either way.** This file is a live defect
against a written rule with no enforcement behind it.

---

## Part 8 — the commit split

**Twelve commits. Nothing pushed** — the GitHub repo named `momentum` maps to the archived tree
and that decision is still open (`handoff/inbox/017` now exists and is unread by this session).

| # | commit | subject |
|---|---|---|
| 1 | `1b2b838` | Seven more allowlist entries, which is S009's prediction measured |
| 2 | `9f85b91` | 015: a UAT named in a done-note must exist as a file |
| 3 | `82d027d` | S009a: measure the panel against the tile, and declare the twelve stages |
| 4 | `55f0817` | 016 part 2: stop scanning 1.8 GB of tape on every run |
| 5 | `b4cc386` | 016 part 3: derive the legacy-path exemption instead of listing prefixes |
| 6 | `c10b4dc` | 016 parts 5b and 5c: the observations ledger, and the trigger |
| 7 | `52722fd` | 016 parts 4, 5a and 6: CLAUDE.md v1.2, v1.3 and v1.4 |
| 8 | `b95e863` | 016 part 1: verify.ps1 — four facts, and no opinion about them |
| 9 | `924b854` | Handoff paperwork: S009a's task file and done-note, inbox 016 and 017 |
| 10 | `5842c3a` | 012's done-note, which was written and never committed |
| 11 | `244e0e2` | Record the design session's supplied edits, unmodified |
| 12 | `e9dd8d1` | Record Christoph's `christoph/` and `accepted/` files, unmodified |

### Two things about the split that are findings, not decoration

**The allowlist had to go FIRST.** `test_adoption_log_complete` fails on a tracked file with no
allowlist row, so committing 015's and S009a's files before their entries would have made two
commits red in isolation. **I got this wrong on the first attempt**, made both commits, noticed,
and reset — nothing was pushed. `test_the_allowlist_does_not_rot` keys on **disk** existence,
not git, so the entries can land before the files are tracked.

**Commit 7 originally preceded commit 6, and that was a real defect.** `CLAUDE.md` v1.3
describes `docs/observations/OBSERVATIONS.md` and `tests/test_observations_ledger.py` — so in
the original order it named two files that did not exist yet, and
`test_claude_md_pointers_resolve` failed **only at that one commit**:

```
CLAUDE.md:213  `docs/observations/OBSERVATIONS.md`
CLAUDE.md:222  `tests/test_observations_ledger.py`
```

**Found by checking out every commit and running the suite at each one**, which is not something
the exit tests asked for and is the only reason it was caught. Fixed by cherry-picking the two
in the opposite order; `git diff main reorder` was empty, so the content is identical and only
the order changed.

**Per-commit results after the reorder** (`c10b4dc` 3 failed/141 passed, `52722fd` 3 failed/141
passed, `b95e863` 2 failed/142 passed): the count no longer *rises* at any commit. The
residual failures are inherited from `cfa491d` and clear as the later commits land — the last
of them, `test_uat_has_a_file`, clears at commit 12 when `christoph/open/009` is recorded.

### Not committed by me, and deliberately labelled

Commits 11 and 12 record other people's files **unmodified**. `christoph/done/012` is committed
**carrying its defect**, stated in the commit message rather than silently corrected. Before
recording, I verified by sha256 that `handoff/accepted/013d` and `accepted/S009` are still
byte-identical to their done-notes, so 013d's own acceptance-is-a-copy property survives the
`013d` inbox-header edit that arrived with them.

---

## Exit tests

| Test | Result |
|---|---|
| **Green** | **`144 passed`, 0 failed, at the moment `verify.ps1` ran.** From `3 failed, 125 passed` before this task. Both failures 016 targeted are cleared. **Writing this note then took the suite to `1 failed, 143 passed` — see below. That is 015's rule working, not a regression.** |
| **Refusal A** | **PASS** — set `OBS-001` to `review-by 2026-08-01`: `AssertionError: OBS-001 review-by 2026-08-01 (11 days ago)`. Reverted |
| **Refusal B** | **PASS** — deleted the row instead: `the ledger has 12 rows; it was seeded with 13 and the count may never go down`. **Deletion is not a route to green.** Reverted |
| **Refusal C** | **PASS, with a stated limit** — see below. Reverted |
| **UAT** | **Christoph.** Run `.\verify.ps1` and read it cold. Criterion: can you tell, without asking anyone, whether the four facts match what a done-note claimed? **Write the record to `christoph/open/`** |

### Refusal C in full, because one of the three is a limit rather than a pass

| probe | result |
|---|---|
| `tools/_refusal_c_probe.py` with the legacy path | **RED.** `tools/_refusal_c_probe.py:1 SNAP = "claude/regime-snapshots/"` |
| `config/_refusal_c_probe.yaml` — the shape a live pointer really takes | **RED.** `config/_refusal_c_probe.yaml:1 regime_dir: claude/regime-snapshots/` |
| `docs/_refusal_c_probe.md` with a **genuine** `**Status** DONE` header | **GREEN — exempt.** The stated limit |

**All three probes were removed; `git status` is clean.**

### The counts

```
before this task           : 3 failed, 125 passed in 128.27s
after, when verify.ps1 ran : 144 passed in 2.44s
after writing this note    : 1 failed, 143 passed in 2.53s
```

**+18 passed, and a 51× faster suite.**

### The one failure, and why I did not clear it

**`test_every_declared_uat_exists_as_a_file` fires on THIS NOTE.** Its exit table names a UAT
and nothing in `christoph/` declares `**Task** 016`:

```
016-verification-harness-and-observations-ledger.md  ->  needs a file declaring **Slice**/**Task** 016
```

**This is `015`'s rule working, on the second note in a row.** It fired on `S009a` the same way,
and that one cleared when the design session authored
`christoph/open/009-s009a-read-the-screen-at-working-width.md` and Christoph placed it — which
is the loop closing exactly as designed.

**I cannot clear it and must not.** The design session authors the UAT file; Claude Code never
writes to `christoph/`. **It is red until that file exists**, deliberately, in the same way
`test_open_questions.py` is red while a question is open.

**Note the interaction with part 7:** 016's own UAT is what turns the suite red, and 016's own
part 7 was the instruction to write into `christoph/` that Christoph ruled out. The two are the
same boundary seen from both sides, on the same day.

---

## Anything that was wrong on contact

**1 · The task's own baseline number was already stale.** 016 says the tree is at *"126 tests,
2 failed, 124 passed"*. By the time it ran, `S009a` had landed and it was **128 tests, 3 failed,
125 passed.** **This does not undermine the task — it is the task's own argument.** Three
different numbers for one tree across three documents is precisely why `verify.ps1` exists,
and 016 was written from a stale reading of a tree it could not see.

**2 · Part 7 collided with two governing documents.** Raised before acting; Christoph ruled the
instruction wrong. See part 7.

**3 · Part 5b's OBS-013 was already settled when it was written.** Recorded as a reading
*"unverified"* on 2026-08-12, the same morning `S009a` measured it. Handled as a `PROMOTED` row
with a resolution rather than by editing the finding.

**4 · One of Part 5b's twelve rows is a finding about a test this task did not touch.** OBS-012
says `git ls-files` reports staged files as present. **`tests/test_no_secrets.py::
test_claude_config_is_not_tracked` uses `git ls-files` today**, so the row's *"what would settle
it"* names a live instance. **Not fixed — 016 forbids acting on a seeded row**, and it is
recorded with its review-by date.

**5 · Part 1's 100-second warning has never been observed firing.** The suite is now 2.44 s
because part 2 landed first. The code path is written and untested by execution, and saying so
is cheaper than implying otherwise.

**6 · Five self-reference traps in one session.** Two in this task — `test_no_secrets`'s guard
failing on its own banned-word list, and the legacy-path test's hardcode check containing the
string it forbids — plus `CLAUDE.md`'s history row re-creating the broken pointer **twice**.
**Every one was fixed positionally rather than by an exclusion**, and the recurrence rate
suggests the rule should be stated up front rather than rediscovered: *a check whose subject
includes its own definition must be scoped to where the defect could live, not to the file.*

**7 · `handoff/accepted/012b-uat-basis-correction.md` accepts a `christoph/` item.** `CLAUDE.md`
describes `handoff/accepted/` as a byte-identical copy of **a done-note**, and 012b is a
`christoph/` file with no `handoff/done/` counterpart. **Not touched** — it is Christoph's file
and this may be intended. Flagged because nothing else would notice it.

---

## Files

| file | change |
|---|---|
| `verify.ps1` | **new** — part 1 |
| `tests/test_no_secrets.py` | `records`/`records_truncated` skip + guard — part 2 |
| `tests/test_regime_snapshot_path.py` | derived exemption + three guards — part 3 |
| `CLAUDE.md` | v1.2 pointer fix, v1.3 observations convention, v1.4 retention — parts 4, 5a, 6 |
| `docs/observations/OBSERVATIONS.md` | **new**, 13 rows — part 5b |
| `tests/test_observations_ledger.py` | **new**, 11 tests — part 5c |
| `tests/test_adoption_log_complete.py` | seven allowlist entries |
| `christoph/**` | **UNTOUCHED.** Recorded in git, never edited |

---

**Paste this into chat. `016` stays `RUNNING` until it lands there.**
