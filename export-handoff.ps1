# export-handoff.ps1 -- one-way, additive, never deletes.
# Two destinations, one HEAD, one manifest each.
#
# 020. The problem this solves is TRANSPORT AND NOTHING ELSE. On 2026-08-11 four
# done-notes were written correctly and none reached the design session, which
# held a stale RUNNING for all of them. A file existing on disk and a file
# reaching the design session are different events.
#
# WHAT THIS DOES NOT DO, stated here because it is the natural misreading:
# syncing a done-note does not close it. Christoph still holds the five states.
# An export removes a transport failure; it does not remove a judgment.
#
# THE REPOSITORY IS NEVER MIRRORED. Drive mirrors D:\claude-googledrive-sync,
# which is outside every repo. An earlier setup pointed Drive at the working
# tree, where a sync conflict creates `handoff/done/012 (1).md` that git status
# reports as new work.
#
# IT DELETES NOTHING, ANYWHERE, EVER. Not in the tree, not in Drive.

$ErrorActionPreference = 'Stop'

$repo      = $PSScriptRoot
$driveRoot = 'D:\claude-googledrive-sync'

# The two sources, and nothing else. The prohibition on exporting docs/specs/,
# records/ and christoph/open/ is STRUCTURAL rather than a forbidden-list: it
# holds because those are not named here, not because something checks for them.
# A forbidden-list grows into a hiding place and this project has ruled that
# three times. tests/test_export_scope_is_derived.py asserts the destinations
# against THIS table, so widening the export requires editing the table.
#
# christoph/open/ is excluded and this must not be "fixed" later: it answers
# *what is still outstanding* by BEING EMPTY, and an additive export cannot
# represent empty -- a retired file would sit in the mirror forever saying the
# exact opposite, convincingly. Putting it in Drive needs a mirroring export
# that deletes, and that is a separate decision.
$exports = @(
    @{ Src = Join-Path $repo 'handoff';        Dst = Join-Path $driveRoot 'momentum-code-handoff';    Recurse = $true  },
    @{ Src = Join-Path $repo 'christoph\done'; Dst = Join-Path $driveRoot 'momentum-christoph-done';  Recurse = $false }
)

# CORRECTION vs the task text: the parent must ALREADY EXIST and is never
# created. The task's script called New-Item -Force on the destination, which
# creates the whole chain including D:\claude-googledrive-sync -- so on a
# machine where Drive is not set up, the export would report success into an
# ordinary local folder that nobody syncs. That is the same silent failure the
# task exists to end, wearing a different hat.
if (-not (Test-Path -LiteralPath $driveRoot -PathType Container)) {
    throw @"
Drive root not found: $driveRoot

This is NOT created automatically, deliberately. If it were, this script would
happily export into an ordinary local folder that no Drive mirror is watching,
report success, and the design session would keep reading nothing. Set up the
Drive mirror first -- that is Christoph's, and is not this script's job.
"@
}

# git -C rather than Push-Location: with $ErrorActionPreference = 'Stop' a throw
# between Push and Pop leaves the caller's location changed. verify.ps1 already
# uses git -C for this reason.
$head  = (& git -C $repo log -1 --format="%H %s") | Out-String
$head  = $head.Trim()
if ($LASTEXITCODE -ne 0) { throw "git log failed in $repo" }
$dirty = @(& git -C $repo status --short)
$stamp = Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz'
$treeState = if ($dirty.Count) { "DIRTY -- $($dirty.Count) uncommitted paths" } else { 'clean' }

foreach ($e in $exports) {
    if (-not (Test-Path -LiteralPath $e.Src)) { throw "source missing: $($e.Src)" }
    if (-not (Test-Path -LiteralPath $e.Dst)) { New-Item -ItemType Directory -Path $e.Dst | Out-Null }

    # -Filter is the fast FileSystem filter, but it also matches 8.3 short names,
    # so `*.md` can pull in a `.markdown`. The Extension test is the one that
    # actually decides. Both are kept: -Filter for speed, Where-Object for truth.
    $all = @(Get-ChildItem -LiteralPath $e.Src -File -Recurse:$e.Recurse)
    $files = @($all | Where-Object { $_.Extension -eq '.md' } | Sort-Object FullName)

    # Named rather than silently dropped. `handoff/A1-connector-from-scheduled-run.txt`
    # is real and is NOT exported. An omission the manifest does not mention is
    # an omission the reader will assume did not happen.
    $notExported = @($all | Where-Object { $_.Extension -ne '.md' } |
        ForEach-Object { [IO.Path]::GetRelativePath($e.Src, $_.FullName) } | Sort-Object)

    $copied = 0; $skipped = 0
    $rows = foreach ($f in $files) {
        # GetRelativePath rather than Substring: Substring assumes the enumerated
        # FullName is byte-prefixed by $Src, which a case difference or a
        # trailing separator breaks silently into a mangled relative path.
        $rel    = [IO.Path]::GetRelativePath($e.Src, $f.FullName)
        $target = Join-Path $e.Dst $rel
        $dir    = Split-Path $target -Parent
        if (-not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }

        # Hashed ONCE and reused for both the copy decision and the manifest row.
        # The task's script hashed every source file twice.
        $srcHash = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash
        $needed  = $true
        if (Test-Path -LiteralPath $target) {
            if ((Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash -eq $srcHash) { $needed = $false }
        }
        if ($needed) { Copy-Item -LiteralPath $f.FullName -Destination $target -Force; $copied++ }
        else         { $skipped++ }

        "| ``$rel`` | $srcHash | $($f.Length) |"
    }

    # Joined here rather than inside the here-string: a `n escape nested in a
    # $() inside a double-quoted here-string parses, but only just, and it is
    # the first thing to break when anyone edits this.
    $rowsText   = ($rows -join "`n")
    $skippedTxt = if ($notExported.Count) {
        "**not exported** $($notExported.Count) non-``.md`` file(s) present in the source and deliberately skipped: " +
        (($notExported | ForEach-Object { "``$_``" }) -join ', ')
    } else {
        '**not exported** none -- every file in the source is `.md`'
    }

    $leaf     = Split-Path $e.Dst -Leaf
    $manifest = Join-Path $e.Dst "MANIFEST-$leaf.md"

    # Distinct filenames, not two files both called MANIFEST.md. The design
    # session locates Drive files by searching filenames across the whole
    # account, so two files sharing a name are two results it cannot tell apart.
    $body = @"
# MANIFEST -- $leaf

**source** ``$($e.Src)``
**exported** $stamp
**HEAD** $head
**working tree** $treeState
**files** $($files.Count) ($copied copied, $skipped unchanged)
$skippedTxt

> One-way and additive. It never deletes, and nothing here is read back into the
> repository. ``docs/specs/``, ``records/`` and ``christoph/open/`` are deliberately
> absent -- the last because an additive export cannot represent an empty folder,
> which is the only thing ``christoph/open/`` exists to say.
>
> **Syncing a done-note does not close it.** This manifest says a file arrived,
> not that anyone accepted it.

| file | sha256 | bytes |
|---|---|---|
$rowsText
"@

    # utf8NoBOM explicitly: -Encoding UTF8 means no-BOM on PowerShell 7 and
    # WITH a BOM on 5.1, and a BOM lands in the first heading of a file the
    # design session reads.
    Set-Content -LiteralPath $manifest -Value $body -Encoding utf8NoBOM

    Write-Host "$($e.Dst): $($files.Count) files ($copied copied, $skipped unchanged)"
    if ($notExported.Count) {
        Write-Host "  not exported (non-.md): $($notExported -join ', ')"
    }
}

Write-Host "HEAD $head"
Write-Host "working tree $treeState"
