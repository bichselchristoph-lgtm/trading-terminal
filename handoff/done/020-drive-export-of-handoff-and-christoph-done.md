# 020 — done — one-way export of `handoff/` and `christoph/done/` to Drive

**Status** RUNNING · **Date** 2026-08-13 · **Type** infrastructure · **Tree** `D:\Dev\momentum`

> **This note needs to be pasted to chat.** Writing it is not reporting it. It lands in a repo
> the design session cannot see — and from this commit onward it also lands in Drive, which the
> design session *can* see. **Those are now two routes to the same file and neither one closes
> anything.** Christoph still holds the five states.

---

## What was built

| File | State |
|---|---|
| `export-handoff.ps1` | **new** — one script, two destinations, one `HEAD` |
| `tests/test_export_scope_is_derived.py` | **new** — 9 tests, scope derived from the sources |
| `verify.ps1` | **modified** — section 5, and "four facts" became "five" in three places |
| `tests/test_adoption_log_complete.py` | **modified** — two `BOOTSTRAP_ALLOWLIST` entries |
| `CLAUDE.md` | **modified** — **v1.5** |
| `docs/observations/OBSERVATIONS.md` | **modified** — OBS-018 |

## The suite, as measured

| When | Result |
|---|---|
| Before any change | **182 passed in 6.86s** |
| After the code, before this note existed | **191 passed in 2.79s** |
| **Final, with this note in the tree** | **190 passed, 1 failed in 3.14s** |

Nine new tests, all in `test_export_scope_is_derived.py`.

### The suite is RED, deliberately, and it is blocked on a person

**`tests/test_uat_has_a_file.py::test_every_declared_uat_exists_as_a_file` fails**, naming this
note:

```
020-drive-export-of-handoff-and-christoph-done.md  ->  needs a file declaring **Slice**/**Task** 020
```

**That is 015's gate working exactly as built, and it went red the moment this note was
written** — the note's exit table declares a UAT, and no file in `christoph/open/` declares
task 020.

**There is no legal route to green from this side of the channel.** The test's own message says
the fix is *"the design session authors it and Christoph saves it to `christoph/open/`"*, and
`CLAUDE.md` plus 020's *Do not* list both forbid this session from writing there. **The two
other exits — deleting the UAT row, or writing the file — are respectively a lie and a
violation.** 020 says: *do not weaken a test to make it pass; report and stop.*

**What clears it:** the design session authors `christoph/open/NNN-020-*.md` declaring
**Task 020**, Christoph saves it, and the suite goes green with no change to any code here.
Its criterion is already written in the task: *open both folders in Drive from a device that is
not this machine — are the notes there, readable, and does the manifest say when they were
exported?*

**The commit was made with the suite red**, which is unusual and is stated rather than
buried. The alternative was to leave 020's work uncommitted and therefore unexported, which
would have left this task's own output stranded in exactly the way 020 exists to prevent.
`verify.ps1` section 1 prints the failure verbatim on every run, so it cannot be forgotten.

**One intermediate red, and it was the gate working on its own author.**
`tests/test_spec_pointers.py::test_claude_md_pointers_resolve` went red at **1 failed, 190
passed** on `CLAUDE.md:204  \`handoff/done/012 (1).md\``. That was an *illustration* of a sync
conflict — a file that must never exist — written in backticks, so the pointer test correctly
read it as a claim about the tree. **Fixed in the prose, not the test**: the name is now given
in quotes and the containing folder in backticks, with a parenthetical saying why. A
hypothetical file must not be spelled like a real one.

## Every correction made to the task's script

The task said it was untested and written by a session that cannot run PowerShell, and that the
corrections are the useful part of the report. **Nine, and one of them was a real hazard.**

**1. The Drive root is never created — this is the one that mattered.** The task's script called
`New-Item -ItemType Directory -Force` on the destination, and `-Force` creates the *whole chain*,
including `D:\claude-googledrive-sync` itself. On a machine where Drive is not set up, that
would create an ordinary local folder nobody syncs, copy 89 files into it, and print success.
**That is the exact failure 020 exists to end, wearing a different hat.** The parent must now
already exist or the script throws with an explanation. Destinations *below* it are still created.

**2. `Push-Location`/`Pop-Location` → `git -C $repo`.** With `$ErrorActionPreference = 'Stop'`,
a throw between the two leaves the caller's working directory changed. `verify.ps1` already uses
`git -C` for this reason.

**3. `-Filter *.md` alone is not an extension test.** The FileSystem provider's filter also
matches 8.3 short names, so `*.md` can pull in a `.markdown`. Kept `-Filter` for speed and added
`Where-Object { $_.Extension -eq '.md' }` as the test that actually decides.

**4. `Substring($e.Src.Length)` → `[IO.Path]::GetRelativePath`.** Substring assumes the
enumerated `FullName` is byte-prefixed by the source path; a case difference or a trailing
separator turns it silently into a mangled relative path.

**5. Every source file was hashed twice** — once for the copy decision, once for the manifest
row. Now hashed once and reused.

**6. `$rows -join "`n"` moved out of the here-string.** A backtick-n nested in a `$()` inside a
double-quoted here-string parses, but only just. Precomputed as `$rowsText`.

**7. `-Encoding UTF8` → `utf8NoBOM`.** `UTF8` means no-BOM on PowerShell 7 and *with* a BOM on
5.1, and the BOM lands in the first heading of a file the design session reads.

**8. `$files.Count` on a scalar.** A single-file source makes `$files` a `FileInfo`, not an
array. All enumerations are now `@()`-wrapped.

**9. Rows sorted by relative path, not `FullName`.** Only cosmetic, and only visible when the
source path length varies.

**And one addition that is not a correction:** each manifest now names the non-`.md` files it
found and skipped. Without it the export silently drops `handoff/A1-connector-from-scheduled-run.txt`
and the manifest reads as complete. **That is OBS-018.**

## The first real export

Both destinations, one invocation, one `HEAD`:

```
D:\claude-googledrive-sync\momentum-code-handoff:   76 files (76 copied, 0 unchanged)
D:\claude-googledrive-sync\momentum-christoph-done: 13 files (13 copied, 0 unchanged)
HEAD a950ae1694f45f11d05cab85456b62e22696e533 Record Christoph's acceptance changes, unmodified
```

| Destination | Manifest | HEAD | Exported | Files |
|---|---|---|---|---|
| `momentum-code-handoff` | `MANIFEST-momentum-code-handoff.md` | `a950ae1` | `2026-08-13T09:49:55+02:00` | **76** |
| `momentum-christoph-done` | `MANIFEST-momentum-christoph-done.md` | `a950ae1` | `2026-08-13T09:49:55+02:00` | **13** |

**Counted independently against the sources: 76 = 76 and 13 = 13.** `find handoff -name '*.md'`
gives 76; `christoph/done/*.md` gives 13. Total under the Drive root afterwards: **92** files =
76 + 13 + 2 manifests + 1 pre-existing `test sync for claude.txt`.

**The working tree was DIRTY at that export** (this task's own files), and both manifests say so.
A final export follows the commit; its `HEAD` is stated at the bottom of this note.

## How each destination's scope is derived, and its limit

**Derived from the source, never from a forbidden-list.** `test_export_scope_is_derived.py`
parses the `$exports` table **out of `export-handoff.ps1` itself** — it does not restate the
source list, because a second copy would drift and the drift would be invisible. For each row it
enumerates the source's `.md` files and asserts the destination contains nothing else.

`verify.ps1` section 5 parses the same table the same way, and never dot-sources the script —
running it would perform an export, and `verify.ps1` never modifies anything.

**One permitted extra per destination: the manifest**, exempted *by name* computed from the
destination folder, so a second stray file cannot hide behind the exemption.

**The stated limits, three of them:**

- **It cannot see a file that was never in the source.** It answers *is anything here that
  should not be*, not *is everything here that should be*. The file-count comparison in
  `verify.ps1` section 5 is what covers the other direction, and it is a count, not a diff.
- **It skips when the Drive root is absent**, so on any machine that is not Christoph's these
  tests prove nothing about the mirror. That is deliberate — the export cannot have leaked into
  a folder that does not exist — but a green suite elsewhere is not evidence about Drive.
- **`test_the_script_never_deletes` is a text check**, not a behavioural one. There is no safe
  way to test the alternative: a test proving deletion works has already deleted something.

## The exit tests

| Test | Result |
|---|---|
| **Green** | **PARTIAL — 190 passed, 1 failed.** Export ran; both manifests written; 76 = 76 and 13 = 13 against the sources. The single failure is `test_uat_has_a_file`, owed to Christoph and unreachable from here — see above. **No test related to this task fails.** |
| **Refusal A** | **Confirmed.** Neither the `docs/specs/` probe nor `christoph/open/013-s010-check-against-your-charts.md` appears in either destination, and **no filename from `docs/specs/` appears at all** (all 17 checked). The derivation test passed **while the probe was present** — 9 passed. Probe reverted. |
| **Refusal B** | **Confirmed.** `MANIFEST-momentum-christoph-done.md`'s `HEAD` hand-edited to `deadbeef… a commit that never happened`. Section 5 printed it beside the live `a950ae1` and then fired **"THE MANIFESTS CARRY DIFFERENT HEADs. Both are printed; neither is preferred"**, listing both. Reverted by re-running the export. |
| **Refusal C** | **Confirmed.** Second run: **0 copied, 76 unchanged / 0 copied, 13 unchanged**, and both manifests still list every file. |
| **Refusal D** | **Confirmed.** Both manifests carry `a950ae1694f45f11d05cab85456b62e22696e533` from one invocation. Section 5 states it explicitly. |
| **UAT** | **Christoph's.** Not written here — the record goes to `christoph/open/`, which this session must never write to. |

### Refusal A was run differently than specified, deliberately

**The task's exit test says to put a `.md` in `christoph/open/`. The same task's *Do not* list
says "Do not write to `christoph/open/` or `christoph/done/`", and `CLAUDE.md` says "Never write
here."** Two prohibitions against one instruction, in the same document.

**Resolved by not writing.** `christoph/open/013-s010-check-against-your-charts.md` already
exists — a real `.md` sitting in the excluded folder — and its absence from both destinations is
exactly the evidence the test wanted, at no cost. The `docs/specs/` half was run as written,
with a probe file created and removed.

**Flagged rather than silently reconciled**, because a task that contradicts itself will do it
again and the next session may resolve it the other way.

## Which `CLAUDE.md` version this produced

**v1.5**, dated 2026-08-13, superseding v1.4. **Read from the file, not assumed.** It records
both destinations, the one-way direction, that the repository itself is never mirrored, why
`christoph/open/` is excluded — *it answers by being empty, and an additive export cannot
represent empty* — and the sentence that is the natural misreading of the whole task:
**syncing a done-note does not close it.**

## What else was wrong on contact

**Nothing else in the task, but two things about the tree:**

**`verify.ps1`'s slow-suite note is now stale.** It warns that "a 2-minute default cap fails a
128s suite by 8 seconds". **This suite runs in 2.79s.** The 128s figure came from the archived
tree. The note is left in place — it is a comment about a hazard, not a claim about this run —
but nobody should read it as describing `momentum`.

**`BOOTSTRAP_ALLOWLIST` grew by two, to 23.** OBS-008 predicted ~11 per slice and this task is
not a slice, so the rate is not evidence either way. A fourth route into the tree —
*"authored here"* — is still an untaken decision, and 020 is not the task that takes it.

## Ledger

**OBS-018**, `OPEN`, review-by 2026-11-13: **the export carries `.md` only**, so
`handoff/A1-connector-from-scheduled-run.txt` and `accepted/.gitkeep` cannot reach the design
session by export — 76 of the 78 files in `handoff/`. The `.txt` is a real handoff artifact. It
is an observation rather than a defect **only because each manifest names what it skipped**; if
that line were ever removed, this becomes a silent omission.

## The export at commit

Stated because `CLAUDE.md` v1.5 now requires it of every task. **Two commits, and the export ran
after each.**

| Commit | Subject | Export |
|---|---|---|
| `424d085` | Record Christoph's open item, unmodified | — |
| `7b48316` | A done-note reaching the design session becomes a mechanism, not a favour | **77 files (1 copied, 76 unchanged) / 13 files (0 copied, 13 unchanged). Working tree clean.** |
| `065d3cc` | The done-note records the export that could not have carried it | superseded by the run below |
| *final* | This note, with the UAT gate recorded | see the line under this table |

`handoff/` went 76 → 77 because this note is the only new `.md` in it — 020's *task* file was
already on disk, untracked, during the first export and was already counted.

**One thing does not terminate and is worth naming rather than hiding.** A note that records
its own export can never be the file that export carried: filling in the `HEAD` above dirties
the tree again. So a **third commit carries this table**, and the mirror's copy of this note is
one commit behind the tree until the export runs after it. **`verify.ps1` section 5 makes that
visible** — it prints the manifest `HEAD` beside the live one and never claims they should
match. It is a property of recording an export inside the thing being exported, not a defect,
and no amount of ordering removes it.

---

**Not pushed.** `D:\Dev\CLAUDE.md` is explicit: the GitHub repo named `momentum` maps to the
**archived** tree, so pushing this one would push the active tree over the archive's history.
That decision is Christoph's and has not been made. `handoff/inbox/017-active-tree-gets-a-remote.md`
is the task that would settle it and it has no done-note.
