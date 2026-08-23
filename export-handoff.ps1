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
#
# ---------------------------------------------------------------------------
# 037. THE COPIER NEVER FAILED. IT WAS NEVER RUN.
#
# Between 2026-08-13T22:12:59+02:00 and 2026-08-14T13:5x it was not invoked
# once, and nothing anywhere said so. The only artifact this script produced
# lived INSIDE the destination and was written ONLY on success, so three
# distinct states -- ran and copied nothing, never ran at all, ran and died --
# all presented as the same unchanged manifest.
#
# So: every invocation now leaves a run record OUTSIDE both destinations, on
# success and on failure alike, and `verify.ps1` prints how old the last
# success is. The copy failing was never the bug. The failure being invisible
# was.

# 037. TWO PARAMETERS, AND BOTH EXIST FOR THE TESTS. Nothing in normal use
# passes either -- the real values are the literals below, unchanged. They are
# here because the refusals (destination unreachable, source unreachable)
# cannot be demonstrated against the real Drive folder without damaging it, and
# a refusal nobody has ever executed is a refusal nobody has seen. That is the
# same class of claim this task exists to stop accepting.
param(
    [string] $DriveRootOverride,
    [string] $RunRecordOverride
)

$ErrorActionPreference = 'Stop'

$repo      = $PSScriptRoot
$driveRoot = 'D:\claude-googledrive-sync'
if ($DriveRootOverride) { $driveRoot = $DriveRootOverride }

# 037 part 2a. THE RUN RECORD LIVES IN THE REPOSITORY ROOT, and the location is
# the whole point: it is outside `handoff/`, outside `christoph/done/` and
# outside `D:\claude-googledrive-sync`, so it survives every failure it has to
# report. A record that only existed in the destination could not report that
# it failed to reach the destination -- it would be the smoke alarm wired to
# the burning wall.
#
# It is TRACKED, not gitignored. Two reasons: `tests/test_export_run_record.py`
# must have a subject on a fresh clone (an absent record is red, per 2c), and
# `git log -p export-run-record.md` is then the attempt history for free.
# The cost, stated rather than discovered: an export run after a commit leaves
# the tree dirty until the next commit picks the record up.
$runRecord = Join-Path $repo 'export-run-record.md'
if ($RunRecordOverride) { $runRecord = $RunRecordOverride }

# POWERSHELL 7+ REQUIRED, checked here rather than discovered at line 83.
# `[IO.Path]::GetRelativePath` and the `utf8NoBOM` encoding are .NET Core APIs
# and do not exist in Windows PowerShell 5.1. Run under 5.1 the script gets 60
# lines in, then dies with `Method invocation failed ... does not contain a
# method named 'GetRelativePath'` -- which reads as a broken script rather than
# as the wrong host. Found on 2026-08-13 by invoking it as `powershell` instead
# of `pwsh`.
#
# 037: this one throw stays OUTSIDE the try/catch below and deliberately writes
# no run record. Under 5.1 the `utf8NoBOM` the record writer uses does not
# exist either, so the recovery path would fail in the same way as the thing it
# is recovering from -- and it would do it while overwriting a good record.
if ($PSVersionTable.PSVersion.Major -lt 7) {
    throw @"
export-handoff.ps1 requires PowerShell 7+; this host is $($PSVersionTable.PSVersion).

It uses [IO.Path]::GetRelativePath and -Encoding utf8NoBOM, both .NET Core only.
Run it with `pwsh`, not `powershell`.
"@
}

function Format-Names {
    # 037. A BOUND, AND IT SAYS SO. The first run against an empty destination
    # copies 118 files, and naming all of them produced a 12,000-character
    # `outcome` line that no reader and no parser wants. The cap is 12 and the
    # remainder is COUNTED OUT LOUD -- "... and 106 more". A silent truncation
    # would read as "that was everything", which is the exact shape of failure
    # this task exists to remove.
    param([string[]] $Names, [int] $Cap = 12)
    if ($Names.Count -le $Cap) { return ($Names -join ', ') }
    return (($Names[0..($Cap - 1)]) -join ', ') + ", ... and $($Names.Count - $Cap) more"
}

function Read-LastSuccess {
    # Carried forward verbatim across runs. A failed run must not lose the
    # timestamp of the last good one -- that gap is the only thing that says
    # how long the design session has been reading stale files.
    param([string] $Path)
    #
    # `^\s*` and not `^`. The first cut of this function used a bare `^` while
    # Write-RunRecord indented the fields four spaces to render them as a
    # markdown code block -- so the anchor never matched, and EVERY failed run
    # silently rewrote `last_success` to `never`. That is the precise fault this
    # whole task exists to remove, reintroduced inside the fix for it, and it
    # was found by actually executing the refusal rather than by reading the
    # code. The fields are now at column zero AND the anchor tolerates
    # whitespace; either alone would be enough, which is the point.
    if (-not (Test-Path -LiteralPath $Path)) { return 'never' }
    $m = ([regex]'(?m)^\s*last_success\s*:\s*(.+?)\s*$').Match((Get-Content -LiteralPath $Path -Raw))
    if ($m.Success) { return $m.Groups[1].Value }
    return 'never'
}

function Write-RunRecord {
    # ISO-8601 with offset, matching the manifest's `exported` stamp rather than
    # the `yyyy-MM-dd HH:mm:ss` the task text sketched. Both this file and the
    # manifests are parsed by verify.ps1 and by a test; two timestamp formats in
    # one mechanism is one format too many, and an offset-less stamp is
    # ambiguous across the DST change this project has already tripped over in
    # session logic.
    param(
        [string] $Path,
        [string] $Attempt,
        [string] $Success,
        [string] $Outcome,
        [string] $Head
    )
    $body = @"
# export-handoff.ps1 -- run record

**Not a report and not a manifest.** It answers one question: *did the export
run, and did it work.* Written on EVERY invocation, before the copy and again
after, so a run killed mid-copy leaves ``last_attempt`` moved and
``last_success`` stale -- which is exactly the signature to look for.

Deliberately outside ``handoff/``, ``christoph/done/`` and the Drive root. A run
record inside the destination cannot report a failure to reach the destination.

``verify.ps1`` section 5 prints the age of ``last_success``.
``tests/test_export_run_record.py`` goes red if this file stops existing or
stops parsing.

The four fields below are at COLUMN ZERO and must stay there. Indenting them to
render as a markdown code block is what broke ``Read-LastSuccess`` on the first
cut of this file.

last_attempt : $Attempt

last_success : $Success

outcome      : $Outcome

head         : $Head
"@
    Set-Content -LiteralPath $Path -Value $body -Encoding utf8NoBOM
}

$stamp       = Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz'
$prevSuccess = Read-LastSuccess $runRecord
$head        = 'unknown -- git log not reached'

try {
    # git -C rather than Push-Location: with $ErrorActionPreference = 'Stop' a throw
    # between Push and Pop leaves the caller's location changed. verify.ps1 already
    # uses git -C for this reason.
    $head  = (& git -C $repo log -1 --format="%H %s") | Out-String
    $head  = $head.Trim()
    if ($LASTEXITCODE -ne 0) { throw "git log failed in $repo" }

    # 037: read BEFORE the first run-record write, deliberately. The record is
    # tracked, so writing it dirties the tree -- and a `working tree` field that
    # says DIRTY on every single export has stopped carrying information. Read
    # here, the field describes the source tree, which is what a reader of the
    # manifest is actually asking about. A record left uncommitted by a PREVIOUS
    # run does show up, correctly: that is a real uncommitted change.
    #
    # AND the run record is excluded from the count by name. This script
    # modifies that one file on every single invocation, so counting it makes
    # `working tree` say DIRTY forever and stop carrying information -- the
    # signal-degradation this field exists to avoid, caused by the fix for a
    # different one. The carve-out is exactly one path, it is the path this
    # script writes, and it is named in the output rather than hidden: a
    # tree whose only uncommitted change is the record reads `clean (bar this
    # script's own run record)`, not `clean`.
    #
    # The commit order that follows from this, and it terminates: commit the
    # work, run the export, then commit the record. The record is in neither
    # export source, so committing it afterwards changes nothing that needs
    # exporting. Committing it BEFORE the export is the infinite regress.
    $allDirty  = @(& git -C $repo status --short)
    $recLeaf   = Split-Path $runRecord -Leaf
    $dirty     = @($allDirty | Where-Object { $_ -notmatch [regex]::Escape($recLeaf) + '\s*$' })
    $treeState = if ($dirty.Count) {
        "DIRTY -- $($dirty.Count) uncommitted paths"
    } elseif ($allDirty.Count) {
        "clean (bar this script's own run record, uncommitted)"
    } else { 'clean' }

    # 064 Part C. A COUNT ON THE HEAD LINE, AND THE PATHS BELOW IT. Before this,
    # a dirty tree asserted a commit hash as the manifest's basis and buried the
    # only evidence against that assertion -- how many paths, which ones -- one
    # line down, behind a field a skimming reader has no reason to open. The
    # count now rides on the line making the claim, so it cannot be missed by
    # skimming past `**working tree**`; the paths themselves are named below it,
    # reusing $dirty rather than re-deriving it, so this can never disagree with
    # the count that produced $treeState.
    #
    # Clean tree: $headForManifest is exactly $head and $dirtySection is empty,
    # so the manifest body is byte-identical to what it rendered before this
    # change -- verified by re-running against a clean tree, not asserted.
    $headForManifest = if ($dirty.Count) { "$head + $($dirty.Count) uncommitted paths (listed below)" } else { $head }
    $dirtySection    = if ($dirty.Count) {
        "**uncommitted paths** ($($dirty.Count))`n" +
        (($dirty | ForEach-Object { "- ``$($_.Trim())``" }) -join "`n") + "`n"
    } else { '' }

    # Before the copy. If the process is killed from here on, this is what is
    # left behind, and it says so.
    Write-RunRecord -Path $runRecord -Attempt $stamp -Success $prevSuccess `
                    -Outcome 'IN PROGRESS -- this run wrote no completion. If you are reading this, it was killed mid-run.' `
                    -Head $head

    # CORRECTION vs the task text: the parent must ALREADY EXIST and is never
    # created. The task's script called New-Item -Force on the destination, which
    # creates the whole chain including D:\claude-googledrive-sync -- so on a
    # machine where Drive is not set up, the export would report success into an
    # ordinary local folder that nobody syncs. That is the same silent failure the
    # task exists to end, wearing a different hat.
    if (-not (Test-Path -LiteralPath $driveRoot -PathType Container)) {
        throw @"
0 new - destination unreachable: $driveRoot

The Drive root is NOT created automatically, deliberately. If it were, this
script would happily export into an ordinary local folder that no Drive mirror
is watching, report success, and the design session would keep reading nothing.
Set up the Drive mirror first -- that is Christoph's, and is not this script's
job.
"@
    }

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
    # 054 Part 3 / 043 Part 2. A THIRD pair, deliberately overlapping the first:
    # handoff/questions/ already travels inside the recursive handoff/ -> 
    # momentum-code-handoff pair. This one duplicates it into a folder Christoph
    # reads for open questions specifically -- 043 asked for it by name, "joining
    # 020's export pairs", not replacing the recursive one. Reported as a
    # deliberate overlap rather than fixed as an inefficiency: de-duplicating it
    # is a scope decision 054 does not make.
    #
    # UNLIKE the other two, this destination is NOT auto-created if missing.
    # 043: "Christoph creates the Drive folder. If it does not exist when this
    # runs, report and skip Part 2's pair rather than creating it -- folder
    # creation is his." Folder-creation-on-his-behalf was never actually
    # exercised for the other two pairs either (both already existed when 020
    # ran); this is the first time the question is asked on purpose.
    $exports = @(
        @{ Src = Join-Path $repo 'handoff';        Dst = Join-Path $driveRoot 'momentum-code-handoff';    Recurse = $true  },
        @{ Src = Join-Path $repo 'christoph\done'; Dst = Join-Path $driveRoot 'momentum-christoph-done';  Recurse = $false }
    )
    if (Test-Path -LiteralPath (Join-Path $driveRoot 'momentum-code-questions')) {
        $exports += @{ Src = Join-Path $repo 'handoff\questions'; Dst = Join-Path $driveRoot 'momentum-code-questions'; Recurse = $false }
    } else {
        Write-Host "momentum-code-questions: skipped - Drive folder does not exist. Christoph creates it, not this script."
    }

    # 037 part 3. Accumulated so the run record's one-line outcome can NAME what
    # moved. "1 copied" tells a reader something happened; it does not tell them
    # whether the thing they are waiting for is the thing that moved.
    $allNew = [System.Collections.Generic.List[string]]::new()

    foreach ($e in $exports) {
        $leaf = Split-Path $e.Dst -Leaf

        if (-not (Test-Path -LiteralPath $e.Src)) {
            throw "0 new - source unreachable: $($e.Src) (destination $leaf)"
        }
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
        $newHere = [System.Collections.Generic.List[string]]::new()
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
            if ($needed) {
                Copy-Item -LiteralPath $f.FullName -Destination $target -Force
                $copied++
                $newHere.Add($rel) | Out-Null
                $allNew.Add("$leaf/$($rel -replace '\\','/')") | Out-Null
            }
            else { $skipped++ }

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

        $manifest = Join-Path $e.Dst "MANIFEST-$leaf.md"

        # Distinct filenames, not two files both called MANIFEST.md. The design
        # session locates Drive files by searching filenames across the whole
        # account, so two files sharing a name are two results it cannot tell apart.
        $body = @"
# MANIFEST -- $leaf

**source** ``$($e.Src)``
**exported** $stamp
**HEAD** $headForManifest
**working tree** $treeState
$dirtySection**files** $($files.Count) ($copied copied, $skipped unchanged)
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

        # 037 part 3. THE FOUR LINES MUST NOT READ ALIKE, and until now two of
        # them did: "N files (0 copied, 103 unchanged)" was the same sentence
        # whether anything had happened or not, and the two unreachable cases
        # printed nothing at all on stdout -- they threw to stderr and left the
        # success line simply absent, which is the hardest kind of output to
        # notice.
        if ($copied) {
            Write-Host "$leaf`: $copied new - $(Format-Names $newHere)"
        } else {
            Write-Host "$leaf`: 0 new - up to date ($($files.Count) files unchanged)"
        }
        if ($notExported.Count) {
            Write-Host "  not exported (non-.md): $($notExported -join ', ')"
        }
    }

    $outcome = if ($allNew.Count) { "$($allNew.Count) new - $(Format-Names $allNew)" } else { '0 new - up to date' }
    $done    = Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz'
    Write-RunRecord -Path $runRecord -Attempt $stamp -Success $done -Outcome $outcome -Head $head

    Write-Host "HEAD $head"
    Write-Host "working tree $treeState"
    Write-Host "run record $runRecord (last_success $done)"
}
catch {
    # 037 part 2a. A FAILURE THAT LEAVES NO RECORD IS THE BUG REPEATING ITSELF.
    # `last_attempt` moves, `last_success` does not, and the reason is written
    # down in a file that is not in the folder that could not be reached.
    #
    # The first line of the message only: the two unreachable throws carry a
    # long explanation for the human on the console, and a run record whose
    # `outcome` field runs to nine lines stops being parseable by 2c's test.
    $reason = ($_.Exception.Message -split "`r?`n")[0].Trim()
    Write-RunRecord -Path $runRecord -Attempt $stamp -Success $prevSuccess `
                    -Outcome "FAILED - $reason" -Head $head

    Write-Host "EXPORT FAILED - $reason"
    Write-Host "run record $runRecord (last_success still $prevSuccess)"
    Write-Error $_.Exception.Message -ErrorAction Continue
    exit 1
}
