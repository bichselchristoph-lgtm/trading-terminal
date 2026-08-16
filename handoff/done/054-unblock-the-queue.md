---
id: 054
title: Unblock the queue — the isolation ruling, the two parts that never arrived, and verify-output's last hop
type: task
class: admin
task_version_executed: 1.0
originates: 052 v4.0 (never reached the tree) - 040 v1.2 Part 0 - 043 v1.2 Part 2 - 053 done-note
closes: B-034 (corrected, not as claimed)
owner: claude-code
tree: D:\Dev\momentum
branch: 054-unblock-the-queue (merged 053-ledger-and-mechanisms on top of main, see report)
bugs:
  - id: B-034
    action: correct
    status: NEW
    note: >-
      Closed as stated, but the guard's second site was found independently:
      034 fixed test_launches_as_a_program.py and correctly left 021's copy
      (tests/test_keepuptodate_scale.py) for this task, but a THIRD copy in
      live/tests/test_attach_is_reachable_by_key.py's no_broker_socket() had
      the same hole and nobody had named it. Found by grepping for the pattern
      across the tree, not by 040 naming it.
  - id: NEW
    action: raise
    status: NEW
    priority: 1
    title: 054 Part 5b instructed an evidence-carry violation
    spec: PROCESS-SPEC
    summary: >-
      Part 5b said to add a staleness banner under the frontmatter of
      handoff/inbox/006 and 007. Both are EVIDENCE-CARRIED (EVIDENCE-CARRY.md
      rows 181-182, hash-verified byte-identical against momentum-harness),
      not adopted documents open to annotation.
    actual: >-
      tests/test_evidence_carry_intact.py went red the moment the banner was
      inserted. The edit was reverted; the finding is recorded instead as
      OBS-076, which does not touch either file.
    expected: >-
      A task instruction and a structural invariant pointed opposite ways.
      Evidence integrity is the one this project states in the strongest
      terms (never clean, dedupe, reformat, prune or regenerate), so it won.
      Whether 006/007 should be refused outright, or annotated by a companion
      file rather than in place, is Christoph's decision - not made here.
  - id: NEW
    action: confirm
    status: NEW
    priority: 2
    title: verify-output.md now reaches Drive - confirmed by reading the manifest
    spec: PROCESS-SPEC
    summary: >-
      054 Part 4's fix (rename .txt to .md rather than widen the .md-only
      export filter) was applied and then verified end to end.
    actual: >-
      MANIFEST-momentum-code-handoff.md lists verify-output.md with a hash and
      byte count - no longer under "not exported". REVIEWED is reachable by
      its own definition for the first time since 023.
    expected: no further action - this is the fix landing, recorded for the audit trail.
  - id: NEW
    action: raise
    status: NEW
    priority: 2
    title: OBS-068 (verify.ps1 / PowerShell 5.1) - nothing documents the shell requirement
    spec: PROCESS-SPEC
    summary: >-
      Report-only per Part 6. CLAUDE.md's "Running things" section never shows
      a verify.ps1 invocation line at all, let alone one naming pwsh.
    actual: >-
      A session or person typing the natural command hits the default
      powershell.exe (5.1) and gets a silent-looking parse crash - loud on the
      console, but nothing routes a reader to the fix. pwsh is NOT guaranteed
      present: it ships with nothing, must be separately installed, and is
      present on this machine as a fact, not a guarantee. tools/register-sync-task.ps1
      explicitly reaches for powershell.exe (5.1) for the scheduled sync task -
      harmless today only because sync.ps1 has zero non-ASCII bytes.
    expected: >-
      Not decided here, per Part 6. Three options stand as OBS-068 already
      named them: add a BOM, replace the 78 non-ASCII bytes with ASCII, or
      document pwsh as required. The byte count is unchanged at 78 after this
      task's edits (confirmed), so OBS-068's analysis still applies unmodified.
  - id: NEW
    action: raise
    status: NEW
    priority: 3
    title: Cross-branch Drive drift makes an export test fail independent of any task
    spec: PROCESS-SPEC
    summary: >-
      tests/test_export_scope_is_derived.py::test_destination_contains_nothing_outside_its_source
      fails because momentum-code-handoff in Drive holds ALLOCATIONS.md and
      done/053-....md - files that exist on the unmerged 053 branch but not on
      main, which this branch was built from before merging 053 on top.
    actual: >-
      Pre-existing, confirmed by running the same test against the pre-054
      tree (git stash) - same failure, same two files. Not caused or fixed by
      054; will clear once 053 merges to main and its export output matches
      what main's checkout produces.
    expected: no fix here - flagged so it is not mistaken for a regression.
---

**Status** REVIEWED

# 054 — unblock the queue

**Read this cold.** Six parts, one branch, no worktree. Two things did not go the way the task
predicted: `006`/`007`'s banner (evidence, not editable) and the export drift (pre-existing, not
caused here).

> **THIS NOTE NEEDS TO BE PASTED TO CHAT.** It lands in a repository the design session cannot
> read.

---

## Branch, and confirmation main was not committed to

**`054-unblock-the-queue`**, in the main checkout, no worktree — created from `main`, then merged
`053-ledger-and-mechanisms` into it once it became clear this task's own text assumed 053's fixes
already existed on the branch (the "you moved it to `handoff/` and then found..." framing in Part 4
describes work that only exists on 053's unmerged branch). `git status` on `main` was never touched;
`main` remains where the last session left it, one commit ahead of `origin/main` — that commit is
Christoph's own (`5e80960`, the worktree-out-of-repo ruling), not this session's.

---

## Part 1 — the isolation ruling

**Followed, not built.** Main checkout, task branch, push the branch, never commit to `main`, no
worktree by any route. `.claude/settings.json` was not touched.

---

## Part 2 — 040's Part 0, executed

**Two sites carried the ineffective guard, not one.** `040` named `021`'s copy
(`tests/test_keepuptodate_scale.py`); grepping the pattern across the tree found a second,
independent site: `live/tests/test_attach_is_reachable_by_key.py`'s `no_broker_socket()` context
manager. `034`'s own fix (`test_launches_as_a_program.py`) was the third and only effective one.

**Both fixed with the same two-part guard 034 used**: `socket.socket.connect` for the synchronous
path, plus `asyncio.base_events.BaseEventLoop.create_connection` for asyncio — patched on
`BaseEventLoop` so it covers the selector and proactor loops both.

**The guard seen failing before the fix, on this machine, not asserted:**

```
ConnectionRefusedError: [WinError 1225] The remote computer refused the network connection
```

At both sites, with only the synchronous patch in place, an `asyncio.base_events.BaseEventLoop.create_connection`
call to port 7496 reached the real Windows network stack — the exact hole `OBS-040` measured, now
reproduced on demand rather than only observed once during `034`. After adding the asyncio-level
patch, the same call is caught with the guard's own `AssertionError`, at both sites.

**Both files now carry a positive control proving this**, not just the two lines by inspection:
`test_importing_the_probe_connects_to_no_broker_port` gained a second `proof_async` case, and
`test_nothing_in_this_suite_opens_a_broker_socket` gained an `asyncio.run(_dial())` check inside the
same `pytest.raises`. `70` tests across all three guard-owning files pass.

---

## Part 3 — 043's Part 2, executed

**What was already true, on `main` before this task:** `handoff/questions/` existed (created under
`044`, not `053` — `053`'s own answer to `044-q1` lives only on its unmerged branch). The folder
convention, the `NNN-<short-name>.md` naming, and the copy-and-keep / answered-by-next-task closing
mechanic were all already in place and followed.

**What was missing, and built:**

- **The minimum header fields.** `044-duplicate-ledger-ids.md` had frontmatter `status: OPEN` but no
  `**Raised by**` or `**Blocks**` body line. **Not `**Status** OPEN` as `043`'s example literally
  shows** — the file already carries `**Status** RUNNING`, the CLAUDE.md five-state handoff
  vocabulary (tracking the handoff of the *task* that raised the question), and a second `**Status**`
  line would have collided two different vocabularies behind one bold word. Added `**Raised by**
  044` and `**Blocks** no` instead — both values already stated in the file's own body, not
  invented. `tests/test_question_file_shape.py` enforces the shape, seen firing on a planted defect
  and restored.
- **The outbound pair.** `handoff/questions/` → `momentum-code-questions`, added to
  `export-handoff.ps1`'s `$exports`, deliberately overlapping the recursive `handoff/` pair — `043`
  asked for it "joining `020`'s export pairs", not replacing the first. **Not auto-created if the
  Drive folder is missing** — checked with `Test-Path` before the pair is added to the array at all,
  per `043`'s instruction that folder creation is Christoph's. The folder already existed (created
  alongside `momentum-christoph-open`), so the pair ran. `tests/test_export_scope_is_derived.py`
  updated from two destinations to three, its own guard against a quiet widening.
- **`verify.ps1` section 9**, reporting the open-question count by name with a `(blocks)` suffix. Ran
  clean: `open questions 1 - 044-duplicate-ledger-ids`.

**Not touched**, correctly out of scope: `043` Parts 1, 3, 4 (the `christoph/open/` inbound pair, the
inbound run record, worktree count in `verify.ps1`) — `054` names only Part 2.

---

## Part 4 — `verify-output` reaches Drive, confirmed by reading the manifest

**Fixed at the filename, per instruction, not by widening the export filter.** `verify.ps1` now
writes `handoff/verify-output.md`. Ran `verify.ps1` then the export, then read the manifest directly:

```
MANIFEST-momentum-code-handoff.md:156:
| `verify-output.md` | 2599F6A7B28FDBAAA6323FC577DDF30E3E66D30E670303BC3B3599501689A320 | 7828 |
```

**No longer under "not exported".** `REVIEWED` is reachable by its own definition for the first time
since `023` — the folder move (`053` Part 2) got it inside an exported path; the extension change
(`054` Part 4) got it inside the exported *type*.

**Only one verification-record file remains on disk.** Both stale artifacts — the original repo-root
`verify-output.txt` and `053`'s intermediate `handoff/verify-output.txt` — were deleted from disk
(both were gitignored generated files, never tracked; nothing was lost). `.gitignore` keeps both
retired paths ignored, with the reason written beside each, so a stale copy regenerated on another
machine or branch cannot present itself to git as new work.

---

## Part 5 — two corrections from 052 v4.0

**5a — `SPEC.md`'s mockup section replaced.**

Before:
```
**Mockup mapping** (files keep their historical numbers):
```

After (the panel-group table kept unchanged below it — this replaces only the framing sentence, not
the mapping itself):
```
**Mockup mapping. TWO SETS EXIST AND THEY DO NOT MIX.**

    docs/specs/mockups/       LOCAL, first generation, numbered 01-07.
                               Referenced by tests and by HTML cross-links.
                               These filenames are pointers and do not change.

    Trading Terminal/Mockups/  Second generation, numbered within type and named
    (Google Drive)             for the spec they serve. Current, and what a
                               product spec cites.

A first-generation mockup predates Textual, the TRADE consolidation, the deletion of the
conviction dial and the deletion of the regime surface. Citing one in a live instruction is a
staleness finding, not a rename.
```

`tests/test_spec_pointers.py`, `tests/test_regime_prompt_invariants.py` and
`tests/test_resupplied_docs_are_repaired.py` all still pass against the edit (the two `6/9` failures
elsewhere in `test_regime_prompt_invariants.py` are pre-existing and unrelated — see bugs block).

**5b — NOT done, and this is a divergence from the task text, not an oversight.** `handoff/inbox/006`
and `007` are **evidence-carried** (`EVIDENCE-CARRY.md` rows 181–182, hash-verified byte-identical
against `momentum-harness`), not adopted documents. The instructed edit — add a banner under the
frontmatter — was applied, immediately turned `tests/test_evidence_carry_intact.py` red, and was
reverted. **The finding is recorded as `OBS-076` instead**, which touches neither file. See the bugs
block for the full reasoning; this is a defensible choice made and recorded, not a question left
open, per project instructions on when a fork needs a decision versus when it doesn't.

---

## Part 6 — `verify.ps1` and the default shell (report only, not fixed)

**What fails.** `verify.ps1` does not parse under Windows PowerShell 5.1 (`powershell.exe`) — 5
parse errors, cascading from an unbalanced string caused by a BOM-less UTF-8 file being read as
ANSI. `OBS-068` already recorded this in full, including the byte-level cause (78 non-ASCII bytes —
em-dashes and `·` — no BOM). **Confirmed unchanged after this task's edits**: still 78 non-ASCII
bytes, still no BOM, despite every edit this session made to the file. `pwsh` (PowerShell 7) parses
it with zero errors.

**Whether `pwsh` is guaranteed present: no.** It is present on this machine
(`C:\Program Files\PowerShell\7\pwsh.exe`) as a fact about this machine, not a guarantee — PowerShell
7 ships with nothing and must be separately installed; only Windows PowerShell 5.1 ships with every
Windows image.

**What invokes `verify.ps1` blindly.** Nothing runs it unattended today — the Scheduled Task
(`tools/register-sync-task.ps1`) only runs `sync.ps1`, and explicitly via `powershell.exe` (5.1),
which is harmless only because `sync.ps1` has zero non-ASCII bytes (`OBS-068`'s own finding).
**The more likely failure is a person, not automation**: `CLAUDE.md`'s "Running things" section
never shows a `verify.ps1` invocation line at all, let alone one naming `pwsh` — unlike `sync.ps1`,
which gets an explicit one-word command. A reader who types the natural `.\verify.ps1` or
`powershell -File verify.ps1` from habit hits the untargeted default and gets a loud but
unexplained crash with no doc pointing at the fix.

**Not fixed, per Part 6's instruction.** `OBS-068`'s three options stand as recorded: add a BOM,
replace the 78 bytes with ASCII, or document `pwsh` as required.

---

## What I could not do, and why

**1. `006`/`007`'s staleness banner was not landed in place.** Evidence-carry integrity took
precedence over the task text; `OBS-076` records the finding without touching either file. Whether
these two tasks are refused outright or annotated by a companion document is Christoph's decision.

**2. The cross-branch Drive drift test cannot be made green from here.**
`test_destination_contains_nothing_outside_its_source` fails because Drive's `momentum-code-handoff`
holds `053`'s output (`ALLOCATIONS.md`, its done-note), which `main` — and therefore this branch —
does not have until `053` merges. Confirmed pre-existing by running the identical test against the
pre-`054` tree; not a regression, not this task's to fix.

**3. Nothing was committed to `main`.** Work is on `054-unblock-the-queue`, which contains
`053-ledger-and-mechanisms` merged in (see branch note above) plus this task's own commits, for
Christoph to merge.

**Empty is suspicious, so stated plainly: nothing else was blocked.** Every other part of this task
ran to completion and was verified, not merely asserted.
