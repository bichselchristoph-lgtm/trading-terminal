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
bugs:
  - id: B-101
    action: confirm
    status: "Confirmed and named for the first time. `test_the_inbound_sync_reports_no_refusals` has been red on `handoff_inbox: 3` for at least fifteen hours (verify.ps1's own last-success gap). The three differing files are named in this note's test #3: `040-for-code-task-readonly-stop-and-accounting-probe.md`, `043-for-code-task-third-pair-and-two-instruments.md`, `052-for-code-task-product-spec-pointer.md`. Not resolved here — resolution is a ruling on which side (Drive or tree) is current for each, not a code fix, and this task's own scope forbids acting on it."
  - id: B-108
    action: confirm
    status: "Same finding as B-101 -- the task's own text names both ids against the same `handoff_inbox: 3` divergence, and nothing in this session's investigation found a second, distinct instance to attach separately to B-108. Recorded against both ids as instructed rather than guessing a split that isn't evidenced."
  - id: NEW
    action: raise
    status: "`tools/now.py`'s `done` bucket is derived from filename presence alone ('a file exists in handoff/done/', its own inline comment) and never reads the file's own `**Status**` header. Task 084's done-note declares `**Status** RUNNING` and states its live measurement was not taken (TWS unreachable) -- `NOW.md` reports `h084` as `done` regardless, so a task that correctly reported itself unfinished is counted as finished with the open item surfaced nowhere `NOW.md` itself shows. Not fixed here -- §5 forbids changing `tools/now.py`/`NOW.md`."
  - id: NEW
    action: raise
    status: "`test_handoff_state_declared.py`'s `STATE_HEADER_FROM=49` watermark comment states pre-watermark task files 'keep the old behaviour... editing them now would rewrite a record rather than fix a defect' -- language describing a full exemption, the same shape `test_donenote_bugs_block.py`'s own `FROM_TASK` watermark actually implements (a full `notes_in_scope()` filter). This watermark does not: `STATE_HEADER_FROM` only toggles frontmatter-stripping inside `declared_state()` and never removes the 10 pre-49 files from `task_files()`'s scope, so they still fail `test_every_task_file_declares_a_state` despite the comment's own claim. Not fixed here -- §5 forbids editing any test."
---

**Status** RUNNING

# 086 — what is actually failing, named file by file

**This note needs to be pasted to chat.**

Gate checked first: `handoff/inbox/086-for-code-task-triage-the-twelve.md` existed
and no `086-*.md` existed in `handoff/done/` at task start.

**No file was edited to produce this note.** `verify.ps1`'s own failure-delta
section, re-run after this note was written, still reports `unchanged 12, new 0,
fixed 0` — see the closing sequence.

---

## The twelve, one at a time

### 1. `test_export_scope_is_derived.py::test_destination_contains_nothing_outside_its_source[1]`

**Asserts** (read from the body, not the name): the Drive-mirrored
`D:\claude-googledrive-sync\momentum-christoph-done` folder must contain no
file that is not either a `.md` file currently present in `christoph/done/` or
the destination's own `MANIFEST-*.md`.

**Failing files**, both inside the Drive folder, **outside the git repository
entirely**:
- `.gitkeep`
- `018-for-christoph-task--check--screenshot.png`

**Bucket: neither Fixable nor Frozen as the task's own table defines them —
closest to Frozen in effect, for a different reason.** `source_relpaths()`
(the permitted-set builder) globs `*.md` only, by design — so a `.gitkeep`
placeholder or a `.png` asset can never be "permitted" regardless of whether a
same-named file sits in `christoph/done/`. Both stray files are leftovers from
before the export was scoped to `.md`-only (`export-handoff.ps1`'s own current
run confirms this: `not exported (non-.md): .gitkeep`) — at some point the
script copied more than markdown, and the export is additive and never
deletes, so those two files are now permanently stuck in Drive. **This guard
cannot go green as written unless a person manually deletes those two files
from the Drive folder** — outside this repo, outside git, and outside what
`export-handoff.ps1` will ever do to a destination.

---

### 2. `test_handoff_state_declared.py::test_every_task_file_declares_a_state`

**Asserts**: every live (non-evidence-carried) file in `handoff/inbox/` and
`handoff/done/` must carry a `**Status**` header in its first 20 body lines
(frontmatter is stripped from that window only for files numbered
`>= STATE_HEADER_FROM` = **49**).

**30 failing files, all `handoff/inbox/*.md`, all already exported to Drive**
(confirmed against `MANIFEST-momentum-code-handoff.md` — every one of the 30
has a manifest row). They split into two groups for two different reasons:

**Below the watermark (10 files, task numbers < 49):**
```
021-for-code-keepuptodate-at-scale.md          025-for-code-regime-snapshot-sync.md
022-for-code-secrets-hygiene.md                026-for-code-inbox-sync-from-drive.md
023-for-code-verify-writes-a-file.md           027-for-code-observations-ledger-catchup.md
024-for-code-subagent-roster.md                035-for-code-bug-pdl-and-atr14.md
                                                037-for-code-bug-drive-export-stopped.md
                                                038-for-code-spec-sessions-levels-units-windows.md
```
**Bucket: Wrong test — the watermark's own comment doesn't match what the
code does.** `STATE_HEADER_FROM`'s comment reads: *"Files below it keep the
old behaviour: they are pre-convention documents the other half of the loop
authored and has already read, and editing them now would rewrite a record
rather than fix a defect."* That sentence describes a FULL exemption — the
same shape `test_donenote_bugs_block.py`'s `FROM_TASK` watermark actually
implements (`notes_in_scope()` filters `>= FROM_TASK`, fully excluding
older notes). **This watermark does not do that.** `STATE_HEADER_FROM` is
read in exactly one place, `declared_state()`, and it only decides whether
frontmatter is stripped before the 20-line window is measured — it never
removes these 10 files from `task_files()`, so they are still required to
declare a state they predate. The comment describes an intent the
implementation does not carry out.

**At or above the watermark (20 files, task numbers >= 49):**
```
057  058  059  060  061  062  063  064  065  066
067  068  069  070  071  072  073  075  076  077
```
(full names: `handoff/inbox/057-for-code-task-verify-output-one-name.md` through
`handoff/inbox/077-for-code-task-levels-rail.md`, exactly the 20 numbers above)

**Bucket: Frozen.** These ARE correctly subject to the full requirement as
designed — genuinely post-convention, genuinely never got a body `**Status**`
header written into them, and all already exported. Editing any of them now
would create the tracked/Drive byte-sync divergence `test_donenote_bugs_block.py`'s
058 exemption was built to avoid creating a second time. Permanent red, and
it hides a new file with the identical defect behind it.

---

### 3. `test_inbound_run_record_has_no_conflicts.py::test_the_inbound_sync_reports_no_refusals`

**Asserts**: the last inbound sync run record (`sync-run-record.md`) reports
zero refused/differing pairs across every configured Drive pair.

**Failing**: `handoff_inbox: 3` — named, by this session's own `sync.ps1` run
this turn (§3 of the task asked for exactly this, and it had never been done):
```
040-for-code-task-readonly-stop-and-accounting-probe.md
043-for-code-task-third-pair-and-two-instruments.md
052-for-code-task-product-spec-pointer.md
```
This is **B-101 and B-108**, and neither has had its files named until this
note. Each pair differs because the tracked repo copy and Drive's copy of the
same handed-off file disagree in content — `sync.ps1` correctly refuses to
overwrite rather than guess which is current.

**Bucket: neither Fixable-by-edit nor Frozen — this needs a ruling, not a
patch.** The test's own message is explicit: *"Resolve by ruling, never by
overwriting... Do not add an exemption here."* Someone (Christoph, or the
design session that authored both copies) has to decide which side is
current for each of the three files; this session cannot make that call and
was not asked to here.

---

### 4. `test_observations_ledger.py::test_every_retired_uat_has_a_register_row`

**Asserts**: every `.md` file in `christoph/done/` (a retired UAT) must have
a row in `docs/observations/OBSERVATIONS.md`'s UAT review register.

**The register is behind, not the test** — confirmed by reading, per §3's own
question. `retired_uats()` currently counts **39** files in `christoph/done/`
(this count moved mid-session: Christoph retired eight more — 038 through
046 — while this task was running, visible in `export-handoff.ps1`'s own
"8 new" report for `momentum-christoph-done`). The register holds **14**
rows, covering UAT numbers `001` through `012b` only — the earliest batch,
never extended. **26 retired UATs, `013` through `046`, have no row**:
```
013-s010-check-against-your-charts.md          034-for-christoph-decision-the-rolling-window-unit.md
014-for-christoph-account-parameters.md        035-for-christoph-task-claude-permissions-and-databento-history.md
015 for christoph attach qqq.md                036-for-christoph-task-uat-060-panels-render-once.md
018-for-christoph-task-check-atr14-and-pdl.md  037-for-christoph-task-second-checkout-and-its-deny.md
021-for-christoph-task-52-week-basis.md        038-for-christoph-task-uat-070-context-block.md
023-for-christoph-task-third-drive-pair.md     039-for-christoph-decision-two-stage-attach.md
024-for-christoph-decision-read-only-api.md    040-for-christoph-task-tracker-sheet-script.md
025-for-christoph-decision-percent-loss-limits.md  042-for-christoph-decision-live-rows.md
026-for-christoph-decision-trades-max-day.md   043-for-christoph-task-uat-two-stage-attach.md
027-for-christoph-decision-52wl.md             044-for-christoph-task-uat-083-rvol-anchor.md
028-for-christoph-decision-type-dollar.md      045-for-christoph-task-uat-084-curve-cache.md
029-for-christoph-decision-006-007-visual-contract.md  046-for-christoph-decision-adr-window.md
031-for-christoph-decision-ledger-persistence.md
032-for-christoph-decision-gapped-over.md
```
**Bucket: Fixable.** `docs/observations/OBSERVATIONS.md` is not `handoff/`
and is not frozen — rows are meant to be added at done-note review, per this
project's own convention. This session did not write to `christoph/` (§5
forbids it and the register lives outside it anyway) and did not add rows,
per this task's own "fix nothing."

---

### 5. `test_observations_ledger.py::test_refusal_b_a_retired_uat_with_no_destination_is_red`

**Asserts**: `unaccounted()` — the exact function the real check calls —
correctly flags a synthetic fake UAT with no register row, AND (its second
half) the real retired set is fully accounted for.

**Same root cause as #4, not independent.** The second assertion
(`assert not unaccounted(retired_uats(), reg)`) fails for the identical
reason: the register is behind by the same 26 files. This is a positive-control
test whose own control half re-trips the #4 gap rather than a second, distinct
finding.

**Bucket: Fixable**, same as #4.

---

### 6. `test_regime_prompt_invariants.py::test_no_bare_six_of_nine`

**Asserts**: `docs/specs/REGIME-PROMPT.md` must never use a bare, unexplained
`6 of 9` figure (in any spelling — `6 of 9`, `6/9`, `6 / 9`) without a
following `unavailable:` line naming its exclusions.

**Failing**: one line —
```
docs/specs/REGIME-PROMPT.md  line 369: health:       "6/9 fresh"
```

**Bucket: Fixable.** A real, nameable defect (the same Amendment-1-§A1.5
error the test's own docstring names, propagated a fourth time) in a file
this project's own re-supply convention treats as tree-side-editable for
exactly this kind of defect fix. Not touched here — this task forbids it.

---

### 7. `test_regime_prompt_invariants.py::test_no_bare_six_of_nine_anywhere_in_specs`

**Asserts**: the same rule, swept across every `.md`/`.html`/`.yaml`/`.yml`
under `docs/specs/` (excluding the frozen `docs/specs/mockups/`, exempted by
name for a stated reason in the test itself).

**Failing**: two lines, one of them #6's own offender restated by the wider
sweep, plus a second file:
```
docs/specs/RE-SUPPLY.md      line 123: `health: "6/9 fresh"`. Ruled a real defect in the delivered text, to be fixed **
docs/specs/REGIME-PROMPT.md  line 369: health:       "6/9 fresh"
```
**Bucket: Fixable**, same defect class as #6, in two files rather than one.
Worth noting: `RE-SUPPLY.md`'s own line already reads as though it was
mid-sentence documenting the fix ("Ruled a real defect in the delivered
text, to be fixed **") — this looks like a spec excerpt quoting the
violation as an example, cut off exactly where the bold marker opens, not a
live second instance in force. Reported as seen; not investigated further,
since this task forbids acting on it either way.

---

### 8. `test_regime_snapshot_could_not_do.py::test_the_format_still_lacks_a_key`

**Asserts** (read the body — the name is misleading, exactly as §2 item 1
warned it might be): this is a **deliberate tripwire**, not a defect check.
It passes only while `REGIME-PROMPT.md`'s documented `could_not_do:` example
entries carry no `id:` key — the precondition under which the real rule-15
recurrence-grouping matcher cannot be built soundly (027 part 2's own
finding). It is *designed* to go red the moment an `id:` appears, as the
signal to come back and build that matcher.

**Currently red because `REGIME-PROMPT.md` now documents an `id:` on its
`could_not_do:` example.** Per the test's own words, quoted directly:
*"This test failing is the GOOD outcome."*

**Bucket: none of the three.** This is not Fixable (there is no defect),
not Frozen (nothing here is copy-and-keep), and not a stale assertion
whose premise a ruling overtook — it is a working tripwire firing exactly
as designed, currently signalling that the rule-15 grouping feature is now
buildable. The test's own instructions: implement the recurrence grouping,
confirm it fires correctly, delete this tripwire, and say so in that
task's done-note. Not this task's to do.

---

### 9–11. `test_task_file_shape.py` — the trio

**`test_every_task_file_declares_a_class`** asserts every task file's
frontmatter parses as valid YAML and declares a `class:`.
**`test_admin_tasks_name_what_they_unblock`** asserts every `class: admin`
task also names what it `unblocks:`.
**`test_no_task_file_names_a_destination`** asserts no task file's
frontmatter names an output destination (053's ROUTING IS PROTOCOL rule —
the channel comes from `config/sync.yaml`, never from task prose).

**All three share the identical pair of offending files** — the helper that
parses frontmatter fails the same way for all three checks:
```
056-for-code-task-two-false-guards.md          — frontmatter is not valid YAML
  (a colon inside prose on line 15 — "...which tasks are ready. Rule 16: this
  counts in the..." — breaks the YAML mapping; not a destination/class/unblocks
  defect specifically, the file cannot be parsed as frontmatter AT ALL)
062-for-code-task-tws-order-test-instrument.md — no frontmatter block at all
```

**Bucket: Frozen.** Both are historical `handoff/inbox/*.md` files and both
are already exported (confirmed against the manifest). Editing either —
even to fix a genuinely broken YAML colon — creates the same tracked/Drive
byte-sync divergence #2's Frozen group describes. Permanent red across all
three tests; a new task file with a genuinely broken frontmatter would be
invisible behind these two already-red offenders.

---

### 12. `test_uat_has_a_file.py::test_every_declared_uat_exists_as_a_file`

**Asserts**: every done-note that names a UAT/Task id in its exit table must
have a corresponding file in `christoph/` declaring that Slice/Task id (or
its exit row must read `UAT | ... | None`, which is a valid declaration).

**6 failing done-notes**:
```
handoff/done/017-active-tree-gets-a-remote.md                 -> needs a file declaring Slice/Task 017
handoff/done/020-drive-export-of-handoff-and-christoph-done.md -> needs a file declaring Slice/Task 020
handoff/done/037-drive-export-stopped.md                       -> needs a file declaring Slice/Task 037
handoff/done/039-risk-and-trade-classification.md              -> needs a file declaring Slice/Task 039
handoff/done/042-four-deltas.md                                -> needs a file declaring Slice/Task 042
handoff/done/069-retire-means-retired.md                       -> needs a file declaring Slice/Task 069
```

**Bucket: neither Fixable-by-this-session nor Frozen — an authorship
boundary, not a copy-and-keep one.** The test's own message says exactly who
closes this: *"THE FIX IS TO AUTHOR THE FILE — the design session authors it
and Christoph saves it to `christoph/open/`."* This session cannot write to
`christoph/` (CLAUDE.md's own convention, restated in `test_observations_ledger.py`'s
comments too) and did not author anything here, per this task's own scope.

---

## Four specific checks, §3

**The duplicate `043-` UAT.** At task start, `christoph/open/` held two files
both beginning `043-`: `043-for-christoph-task-uat-080-two-stage-attach.md`
and `043-for-christoph-task-uat-two-stage-attach.md`. **Mid-session, Christoph
retired the second one** — `043-for-christoph-task-uat-two-stage-attach.md`
now sits in `christoph/done/`; `043-for-christoph-task-uat-080-two-stage-attach.md`
remains in `christoph/open/`. Both paths reported above; **neither deleted**,
per §3's own instruction. This is the same duplicate-numbering shape
`handoff/questions/044-duplicate-ledger-ids.md` already tracks as an open
question — not a new instance, the same one, one file down.

**`test_the_inbound_sync_reports_no_refusals`.** Covered above as test #3 —
the three differing files are `040-for-code-task-readonly-stop-and-accounting-probe.md`,
`043-for-code-task-third-pair-and-two-instruments.md`,
`052-for-code-task-product-spec-pointer.md` (B-101/B-108, named for the
first time here).

**The `test_task_file_shape` trio.** Covered above as tests #9–11 — both
offenders (`056`, `062`) are historical `handoff/inbox/*.md` files, both
already exported, both Frozen: the guard can never go green as written and
sits ahead of any new file that arrives with the identical malformed-YAML
or missing-frontmatter defect.

**`test_every_retired_uat_has_a_register_row`.** Covered above as test #4 —
**the register is behind, not the test.** 26 of 39 retired UATs (`013`
through `046`) have no row; the register was populated once, for the
earliest batch (`001`–`012b`), and never extended as later UATs retired.

---

## Part 4 — `NOW.md` reports `h084` as done; the done-note says `RUNNING`

**Read directly, per the task's own instruction: `tools/now.py` derives
`done` as "a file exists in `handoff/done/`" — literally, by filename
presence alone.** Its own inline comment says so verbatim (`done  a file
exists in handoff/done/`). Nothing in the derivation reads the file's own
`**Status**` header, its frontmatter, or any other content.

**Task 084's own done-note declares `**Status** RUNNING`** and states
plainly, in its own Part 3, that the live wall-time measurement — the
task's stated whole point — was not taken because TWS was unreachable.

**Confirmed: a task that correctly reported itself unfinished is being
counted as finished, and the owed measurement is flagged nowhere `NOW.md`
itself surfaces.** `NOW.md`'s `done` bucket makes no distinction between "a
done-note exists and says DONE" and "a done-note exists and says RUNNING
with a stated open item." Anyone reading only `NOW.md`'s `done` list (not
the note itself) would believe 084 needs nothing further.

**Not changed.** Per §5, `tools/now.py`, `NOW.md`, and `verify.ps1` are all
left exactly as they stood.

---

## What was NOT done, per §5

No file was edited to satisfy any test. Nothing was deleted — the duplicate
`043-` files, the stray Drive files, both malformed task files, all left
exactly as found. `verify.ps1`, `NOW.md`, and every test file are untouched.
Nothing is marked DONE that is not — this note's own header reads `RUNNING`
below.

---

## Exit condition, §6

No Green/Refusal/UAT tests — none apply, per the task's own instruction: no
production code changes, no behaviour to pin. The exit condition is this
list.

**The suite reports `unchanged 12, new 0, fixed 0` after this task**,
confirmed by re-running `verify.ps1` as the closing action (below) — this
task changed nothing the suite can see.

---

## Closing sequence

`verify.ps1` runs as the last action, not pasted or summarised here.
`export-handoff.ps1` was run mid-task (at the user's direction) rather than
only at the end this time — it caught up `086`'s own inbox file and eight
UATs Christoph retired while this task was running; re-run again after this
done-note is written, per the standing convention. Commit/push follow,
scoped to this task's own files only.

**This note needs to be pasted to chat.**
