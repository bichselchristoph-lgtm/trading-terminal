# 020 — for code — one-way export of `handoff/` and `christoph/done/` to the Drive-synced folders

**Status** WRITTEN · **Date** 2026-08-13 · **Type** infrastructure · **Tree** `D:\Dev\momentum`

> **Number confirmed by Christoph, 2026-08-13.** `019` and `S010` were the highest in the
> inbox; `020` is free. The design session did not infer it — inferring produced three
> collisions.
>
> **Drive reachability is confirmed, not assumed.** On 2026-08-13 a file placed in
> `D:\claude-googledrive-sync\momentum-code-handoff` was found and its contents read from the
> design session within seconds. **Mirrored folders under *Computers* are reachable.**
>
> **The script below is untested.** It was written by a session that cannot run PowerShell.
> **Treat it as the specification, not as working code** — read it, correct it, test it, and
> report every change in the done-note.

---

## The problem

**On 2026-08-11 four done-notes were written correctly and none reached the design session**,
which held a stale `RUNNING` for all of them. *A file existing on disk* and *a file reaching the
design session* are different events, and Christoph is the only party who can see both.
Everything since has been carried by hand.

**What this fixes is transport and nothing else.** The mistakes of 2026-08-12 were mostly not
transport — a wrong folder path, a `_1` duplicate, an inferred task number, a task instructing
writes to a tree that forbids them. **None of those is touched by an export.** This removes the
pasting and kills the stale-`RUNNING` class. That is real and it is narrower than "fewer
mistakes".

---

## Part 1 — Christoph's side, stated here for sequence only

**Drive mirrors the parent folder `D:\claude-googledrive-sync`**, so both destinations below are
covered by one mirror and a third needs no Drive change.

**The repository is never mirrored.** An earlier setup pointed Drive at
`D:\Dev\momentum\handoff\` — inside the working tree — where a sync conflict would create
something like `handoff/done/012 (1).md` that `git status` reports as new work.

**Stale content in Drive was cleared on 2026-08-13**, and it is recorded because the sequence
matters: an old `handoff` mirror from `momentum-harness` frozen at 2026-08-09, plus
`HANDOFF-PROTOCOL.md` v1.0 and its provenance companion as converted Google Docs. **v1.0's rule
4 still listed *"what the note says"* among the mechanical facts, which `013c` removed** — a
superseded spec sitting where someone would read it as current.

**The mirror was unlinked before the Drive copy was deleted**, because deleting a mirrored file
in Drive deletes it locally, and the local folder was `D:\Dev\momentum-harness` — the archive at
`1afcecf`, which every row in `EVIDENCE-CARRY.md` cites as its source path. **Nothing in this
task touches Drive.**

---

## Part 2 — `export-handoff.ps1`, one script, two destinations

**Create `D:\Dev\momentum\export-handoff.ps1`.**

| Source | Destination |
|---|---|
| `D:\Dev\momentum\handoff\` (recursive) | `D:\claude-googledrive-sync\momentum-code-handoff\` |
| `D:\Dev\momentum\christoph\done\` (flat) | `D:\claude-googledrive-sync\momentum-christoph-done\` |

**Manifests get distinct filenames**, not two files both called `MANIFEST.md`:
`MANIFEST-momentum-code-handoff.md` and `MANIFEST-momentum-christoph-done.md`. **The design
session locates Drive files by searching filenames across the whole account**, so two files
sharing a name are two results it cannot tell apart — and a name as generic as `MANIFEST.md`
will collide with something eventually.

**One script, not two, and the reason is not convenience.** Both mirrors must reflect the same
`HEAD`. Run as separate scripts they can drift — one destination at one commit and the other at
another — with nothing saying so. **That is a well-formed value answering a different question,
and it would be invisible.** One invocation, one `HEAD`, two manifests carrying it.

**It copies new and changed `.md` files. It deletes nothing, anywhere, ever.**

### Why `christoph/open/` is excluded, and this must not be "fixed" later

**`christoph/open/` answers *what is still outstanding*, and it answers by being empty.**

**An additive export cannot represent empty.** A retired file would sit in the mirror forever,
saying the exact opposite of what that folder exists to say — and it would say it convincingly.

**`handoff/` and `christoph/done/` are both safe** because nothing is ever removed from either:
`handoff/` is copy-and-keep by rule, and `christoph/done/` is the destination of
copy-verify-retire, never its source.

**If `christoph/open/` is ever wanted in Drive it needs a different mechanism — a mirroring
export that deletes — and that is a separate decision.** Do not add it here.

### The script, to be corrected rather than trusted

```powershell
# export-handoff.ps1 — one-way, additive, never deletes.
# Two destinations, one HEAD, one manifest each.

$ErrorActionPreference = 'Stop'
$repo = 'D:\Dev\momentum'

$exports = @(
    @{ Src = Join-Path $repo 'handoff';         Dst = 'D:\claude-googledrive-sync\momentum-code-handoff';    Recurse = $true  },
    @{ Src = Join-Path $repo 'christoph\done';  Dst = 'D:\claude-googledrive-sync\momentum-christoph-done';  Recurse = $false }
)

Push-Location $repo
$head  = (git log -1 --format="%H %s")
$dirty = (git status --short)
Pop-Location
$stamp = Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz'

foreach ($e in $exports) {
    if (-not (Test-Path $e.Src)) { throw "source missing: $($e.Src)" }
    if (-not (Test-Path $e.Dst)) { New-Item -ItemType Directory -Path $e.Dst -Force | Out-Null }

    $files = if ($e.Recurse) {
        Get-ChildItem -Path $e.Src -Filter *.md -Recurse -File
    } else {
        Get-ChildItem -Path $e.Src -Filter *.md -File
    }

    $copied = 0; $skipped = 0
    foreach ($f in $files) {
        $rel    = $f.FullName.Substring($e.Src.Length).TrimStart('\')
        $target = Join-Path $e.Dst $rel
        $dir    = Split-Path $target -Parent
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }

        $needed = $true
        if (Test-Path $target) {
            if ((Get-FileHash $f.FullName -Algorithm SHA256).Hash -eq
                (Get-FileHash $target     -Algorithm SHA256).Hash) { $needed = $false }
        }
        if ($needed) { Copy-Item $f.FullName $target -Force; $copied++ } else { $skipped++ }
    }

    $rows = $files | Sort-Object FullName | ForEach-Object {
        $rel = $_.FullName.Substring($e.Src.Length).TrimStart('\')
        "| ``$rel`` | $((Get-FileHash $_.FullName -Algorithm SHA256).Hash) | $($_.Length) |"
    }

    @"
# MANIFEST — $(Split-Path $e.Dst -Leaf)

**source** ``$($e.Src)``
**exported** $stamp
**HEAD** $head
**working tree** $(if ($dirty) { "DIRTY — $(($dirty | Measure-Object).Count) uncommitted paths" } else { "clean" })
**files** $($files.Count) ($copied copied, $skipped unchanged)

> One-way and additive. It never deletes, and nothing here is read back into the repository.
> ``docs/specs/``, ``records/`` and ``christoph/open/`` are deliberately absent — the last
> because an additive export cannot represent an empty folder, which is the only thing
> ``christoph/open/`` exists to say.

| file | sha256 | bytes |
|---|---|---|
$($rows -join "`n")
"@ | Set-Content -Path (Join-Path $e.Dst "MANIFEST-$(Split-Path $e.Dst -Leaf).md") -Encoding UTF8

    Write-Host "$($e.Dst): $($files.Count) files ($copied copied, $skipped unchanged)"
}

Write-Host "HEAD $head"
```

### What must never be exported

`docs/specs/` · `records/` · `christoph/open/` · any code, config, test, or `.git` content.

**The sources are the two folders above and nothing else, so the prohibition is structural
rather than a list.** Write a test asserting each destination contains no path outside its
source, **derived from the source rather than from a forbidden-list** — a forbidden-list grows
into a hiding place and this project has ruled that three times.

**`docs/specs/` is the one that matters.** Drive held the specs once and Layer 0 was fully
specified and never built because of it — and a stale v1.0 copy is in Drive right now.

---

## Part 3 — `verify.ps1` gains a fifth section

**Sync failure is silent.** A stale file in the mirror looks identical to a current one, and the
design session would read it and believe it — the same shape as the stale `RUNNING` this task
exists to end. **Trading one silent failure for another is no gain.**

`verify.ps1` prints, as section 5, **for each destination**:

- the manifest's `HEAD` and export timestamp (`MANIFEST-<folder>.md`)
- the live `HEAD`, beside it
- the manifest's file count, beside the live count of that source

**No verdict, consistent with the rest of the script.** Four facts became five; the reading still
belongs to the design session. **If a manifest is missing, say so and continue** — and if the two
manifests disagree with each other, print both rather than picking one.

---

## Part 4 — when it runs

**At the end of every task, after the commit.** Add it to the done-note checklist the way the
suite result already is.

**No watcher, no scheduled job, no filesystem hook.** A missed export is visible in `verify.ps1`;
a background process that fails quietly is not.

**State in the done-note whether the export ran and what `HEAD` it recorded.**

---

## Part 5 — `CLAUDE.md`

Record the export, its one-way direction, both destinations, and **the sentence that is the
natural misreading of this whole task: syncing a done-note does not close it.** Christoph still
holds the five states, `REVIEWED` still needs the verification output, and `DONE` still needs
both parties. **An export removes a transport failure; it does not remove a judgment.**

Record also **why `christoph/open/` is excluded** — in one sentence, because the obvious
"improvement" is to add it.

Increment the version and add its history row. **Read the file for its current version rather
than assuming.**

---

## Do not

- Do not export anything from `docs/specs/`, `records/`, `christoph/open/`, or any code path.
- **Do not delete anything, in either location.**
- Do not read from either Drive folder into the repo. **Nothing enters the tree except through
  the adoption gate.** Add a test asserting no path under `D:\claude-googledrive-sync` is tracked
  by git.
- Do not add a watcher, hook, or scheduled task.
- **Do not configure or touch Google Drive.** That is Christoph's and is not in this task.
- Do not write to `christoph/open/` or `christoph/done/`.
- Do not weaken a test to make it pass. **Report and stop.**

---

## Exit tests

| Test | Who | What |
|---|---|---|
| **Green** | Claude Code | Full suite, count before and after as measured numbers. Export runs; both manifests written; each file count matches its source exactly. |
| **Refusal A** | Claude Code | Put a `.md` in `docs/specs/` and one in `christoph/open/`, then run the export. **Confirm neither appears** in either destination, and the derivation test still passes. Revert. |
| **Refusal B** | Claude Code | Hand-edit one manifest's `HEAD`. **Confirm `verify.ps1` shows the mismatch** rather than reporting the export as current. Revert. |
| **Refusal C** | Claude Code | Run the export twice with no changes. **Confirm the second copies nothing** and both manifests still list every file. |
| **Refusal D** | Claude Code | **Confirm both manifests carry the same `HEAD`** on a single run. This is the drift the one-script decision exists to prevent. |
| **UAT** | Christoph | Open both folders in Drive from a device that is not this machine. **The criterion is whether the notes are there, readable, and whether `MANIFEST.md` tells you when they were exported.** Write the record to `christoph/open/`. |

## Done-note must state

- **Every correction made to the script above.** It was written untested by a session that
  cannot run PowerShell, and the corrections are the useful part of this report.
- Both manifests' `HEAD`, timestamp and file count from the first real export.
- How each destination's scope is derived, and its stated limit.
- Which `CLAUDE.md` version this produced.
- Anything else in this task that was wrong on contact.
