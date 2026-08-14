# verify.ps1 — five facts about this tree, and no opinion about them.
#
# Four became five under 020 part 3, which added the export freshness check.
# The count is in the name of the thing, so it is maintained rather than left
# saying "four" while printing five.
#
# 016 part 1. Christoph cannot verify what he carries. A done-note is
# machine-to-machine communication passing through a human who can see that it
# arrived and that all of it arrived, but not whether 179 hashes verified or a
# suite really passed. On 2026-08-12 two notes could not be checked against each
# other or against the tree: `015` claimed `103 passed, 1 failed`, `012` claimed
# `2 failed, 102 passed`, and the tree was at `126 tests, 2 failed, 124 passed`.
# Neither note described this tree. Nothing was contradicted and nothing was
# confirmed.
#
# THIS SCRIPT DOES NOT INTERPRET. No "all good", no green/red, no
# exit-code-as-verdict. Five sections of raw fact, and the reading belongs to
# the design session. Its whole value is that it does not have an opinion — a
# script that says "PASS" is one more claim to verify, not a way of verifying
# claims.
#
# IT MODIFIES NOTHING IN THE TREE, WITH EXACTLY ONE EXEMPTION. No `git add`, no
# fixture creation, no edits. **It writes `verify-output.txt` in the repo root
# and nothing else** (023). That file is gitignored, overwritten each run, and
# is the artifact the design session reads instead of a pasted transcript.
#
# The exemption is named here rather than left to be discovered, because until
# 023 this line read "IT NEVER MODIFIES ANYTHING" without qualification, and a
# reader who finds an unexplained write is right to distrust the rest of it.
#
# If a section cannot be computed it prints why and continues to the next one; a
# script that aborts halfway is one that reports less the more wrong things are.

$ErrorActionPreference = 'Continue'
$python = 'C:\venvs\trading\Scripts\python.exe'
$repo   = $PSScriptRoot
$start  = Get-Date

# 023. TEE, NOT REDIRECT. The console output is unchanged in content -- Christoph
# may still glance at it, and a task that silences a familiar tool is a task that
# gets worked around. `Say` prints exactly what `Write-Host` printed and also
# keeps the line, so the same text reaches both places from one source.
#
# THE OUTPUT FILE IS THE ONLY WRITE THIS SCRIPT MAKES. That exemption is stated
# here because the header three lines up promises the opposite, and a reader who
# finds a write with no explanation is right to distrust the rest.
$outFile = Join-Path $repo 'verify-output.txt'
$script:Captured = [System.Collections.Generic.List[string]]::new()
function Say {
    param([string]$msg = '')
    $script:Captured.Add($msg) | Out-Null
    Write-Host $msg
}

# HEAD captured at the START as well as in section 3. If they differ the tree
# moved mid-run, which is the 2026-08-12 catch, and it should be LOUD rather than
# latent -- the file is read out of context by a party that was not present.
# CAPTURED FIRST, SELECTED AFTER. `git ... | Select-Object -First 1` stops the
# pipeline as soon as it has its one object, which terminates git early and can
# leave $LASTEXITCODE non-zero on a command that actually succeeded. Written that
# way first, it reported `CANNOT COMPUTE:` in front of a HEAD it had just read
# correctly -- and then compared that string against a clean one at the end and
# announced THE TREE MOVED. A false alarm on the loudest line in the file.
function Get-Head($repoPath) {
    $raw = & git -C $repoPath rev-parse HEAD 2>&1
    if ($LASTEXITCODE -ne 0) { return "CANNOT COMPUTE: $raw" }
    return ($raw | Select-Object -First 1)
}
$headAtStart = Get-Head $repo

function Section($n, $title) {
    Say ''
    Say ('=' * 72)
    Say "  $n. $title"
    Say ('=' * 72)
}

Say ''
Say "verify.ps1  --  $repo"
Say "run at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss K')"
Say "HEAD at start  $headAtStart"
# Where a "tree moved mid-run" warning is inserted into the FILE's header, if
# section 3 disagrees with the line above. Recorded now because by the time we
# know, these lines have already gone to the console.
$headerEnd = $script:Captured.Count

# --- 1. the suite -----------------------------------------------------------
Section 1 'SUITE — the pytest summary line, verbatim'

if (-not (Test-Path $python)) {
    Say "CANNOT COMPUTE: $python not found. There is no ``python`` on PATH."
    $suiteSeconds = $null
} else {
    $t0 = Get-Date
    $out = & $python -m pytest --color=no 2>&1 | Out-String
    $suiteSeconds = ((Get-Date) - $t0).TotalSeconds
    # The last line matching pytest's summary shape. Printed verbatim, and NOT
    # translated into a verdict.
    $summary = ($out -split "`n" | Where-Object { $_ -match '^=+ .*(passed|failed|error|no tests ran).* =+\s*$' } | Select-Object -Last 1)
    if ($summary) { Say $summary.Trim() }
    else {
        Say 'CANNOT COMPUTE: no pytest summary line found. Last 15 lines follow:'
        ($out -split "`n" | Select-Object -Last 15) | ForEach-Object { Say "  $_" }
    }
    $failed = ($out -split "`n" | Where-Object { $_ -match '^FAILED |^ERROR ' })
    if ($failed) {
        Say ''
        Say 'named failures:'
        $failed | ForEach-Object { Say "  $($_.Trim())" }
    }
}

# --- 2. uncommitted ---------------------------------------------------------
Section 2 'GIT STATUS — every uncommitted path'

$status = & git -C $repo status --short 2>&1
if ($LASTEXITCODE -ne 0) { Say "CANNOT COMPUTE: git status failed: $status" }
elseif (-not $status) { Say '(clean — no uncommitted paths)' }
else { $status | ForEach-Object { Say "  $_" } }

# --- 3. HEAD ----------------------------------------------------------------
Section 3 'HEAD — the commit this output describes'

$head = & git -C $repo log -1 --format="%H %s" 2>&1
if ($LASTEXITCODE -ne 0) { Say "CANNOT COMPUTE: git log failed: $head" }
else { Say "  $head" }

# --- 4. evidence re-hash ----------------------------------------------------
Section 4 'EVIDENCE — sha256 recomputed from EVIDENCE-CARRY.md'

# INDEPENDENT PATH, DELIBERATELY. 014's reasoning: this must not call the test
# suite's own code, because a bug in the test would then mask a real drift and
# both would agree. The manifest walk is reimplemented here rather than
# importing test_evidence_carry_intact.
$rehash = @'
import hashlib, pathlib, re, sys
repo = pathlib.Path(sys.argv[1])
manifest = repo / "EVIDENCE-CARRY.md"
if not manifest.exists():
    print("CANNOT COMPUTE: EVIDENCE-CARRY.md is missing"); raise SystemExit(0)
row = re.compile(r"^\|\s*\d{4}-\d{2}-\d{2}\s*\|\s*`(?P<rel>[^`]+)`\s*\|[^|]*\|\s*`(?P<sha>[0-9a-f]{64})`", re.M)
rows = list(row.finditer(manifest.read_text(encoding="utf-8")))
missing, mismatch = [], []
for m in rows:
    rel, want = m.group("rel"), m.group("sha")
    p = repo / rel
    if not p.exists():
        missing.append(rel); continue
    got = hashlib.sha256(p.read_bytes()).hexdigest()
    if got != want:
        mismatch.append((rel, want, got))
print(f"{len(rows)} rows checked, {len(mismatch)} mismatches, {len(missing)} missing")
for rel, want, got in mismatch:
    print(f"  MISMATCH {rel}"); print(f"    recorded {want}"); print(f"    on disk  {got}")
for rel in missing:
    print(f"  MISSING  {rel}")
'@

if (-not (Test-Path $python)) {
    Say "CANNOT COMPUTE: $python not found."
} else {
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) 'verify_rehash.py'
    Set-Content -Path $tmp -Value $rehash -Encoding UTF8
    & $python $tmp $repo 2>&1 | ForEach-Object { Say "  $_" }
    Remove-Item $tmp -ErrorAction SilentlyContinue
}

# --- 5. export freshness ----------------------------------------------------
Section 5 'EXPORT — what each Drive mirror says, beside what this tree says'

# 020 part 3. SYNC FAILURE IS SILENT. A stale file in the mirror looks identical
# to a current one, and the design session would read it and believe it — the
# same shape as the stale RUNNING the export exists to end. Trading one silent
# failure for another is no gain.
#
# NO VERDICT, consistent with the rest of this script. The manifest's HEAD and
# the live HEAD are printed beside each other; whether they should match is the
# design session's reading, not this script's.
#
# The destinations are PARSED OUT OF export-handoff.ps1 rather than restated
# here. A second copy of the table would drift, and the drift would be invisible.
# The script is never dot-sourced — running it would perform an export, and
# verify.ps1 never modifies anything.

# 037 part 2b. THE RUN RECORD GOES FIRST, because the manifests below cannot
# answer the question it answers. A manifest lives INSIDE a destination and is
# written ONLY on success, so "ran and copied nothing", "never ran at all" and
# "ran and died" all leave the same unchanged file — which is how fifteen hours
# passed on 2026-08-14 with nobody able to tell the three apart. The run record
# lives in the repository root and is written on every invocation.
#
# STILL NO VERDICT, consistent with the rest of this script. An age in hours and
# a count of newer source files are facts. What they mean is the reading, and
# the reading belongs to the design session.
$runRecord     = Join-Path $repo 'export-run-record.md'
$lastSuccessAt = $null
if (-not (Test-Path $runRecord)) {
    Say '  run record        MISSING — no export-run-record.md in the repo root'
    Say '                    (the export has never run against this tree, or the copier'
    Say '                     stopped writing it — tests/test_export_run_record.py covers'
    Say '                     the second case and would be red)'
} else {
    $rtext = Get-Content $runRecord -Raw
    $rAtt  = ([regex]'(?m)^\s*last_attempt\s*:\s*(.+?)\s*$').Match($rtext)
    $rSuc  = ([regex]'(?m)^\s*last_success\s*:\s*(.+?)\s*$').Match($rtext)
    $rOut  = ([regex]'(?m)^\s*outcome\s*:\s*(.+?)\s*$').Match($rtext)

    $now = [datetimeoffset]::Now
    $ageOf = {
        param($m)
        if (-not $m.Success) { return 'CANNOT COMPUTE: field absent' }
        $v = $m.Groups[1].Value
        if ($v -eq 'never') { return 'never' }
        [datetimeoffset]$parsed = [datetimeoffset]::MinValue
        if (-not [datetimeoffset]::TryParse($v, [ref]$parsed)) { return "$v   (UNPARSEABLE)" }
        $d = $now - $parsed
        "$v   ({0}h {1:00}m ago)" -f [int]$d.TotalHours, $d.Minutes
    }

    Say "  drive export      last attempt $(& $ageOf $rAtt)"
    Say "                    last success $(& $ageOf $rSuc)"
    Say ("                    outcome      " + $(if ($rOut.Success) { $rOut.Groups[1].Value } else { 'CANNOT COMPUTE: no outcome line' }))

    if ($rSuc.Success -and $rSuc.Groups[1].Value -ne 'never') {
        [datetimeoffset]$tmp = [datetimeoffset]::MinValue
        if ([datetimeoffset]::TryParse($rSuc.Groups[1].Value, [ref]$tmp)) { $lastSuccessAt = $tmp }
    }
    Say ''
}

$exportScript = Join-Path $repo 'export-handoff.ps1'
if (-not (Test-Path $exportScript)) {
    Say "CANNOT COMPUTE: export-handoff.ps1 not found at $exportScript"
} else {
    $src = Get-Content $exportScript -Raw
    # SINGLE-QUOTED here-strings, deliberately. In a double-quoted PowerShell
    # string `$repo` expands — backslash is not an escape character here — so
    # `\$repo` in a pattern silently becomes `\D:\Dev\momentum` and matches
    # nothing. Caught on the first run of this section.
    $rowRe = [regex]@'
@\{\s*Src\s*=\s*Join-Path\s+\$repo\s+'([^']+)'\s*;\s*Dst\s*=\s*Join-Path\s+\$driveRoot\s+'([^']+)'\s*;\s*Recurse\s*=\s*\$(true|false)
'@
    $rootRe = [regex]@'
\$driveRoot\s*=\s*'([^']+)'
'@

    $rootM = $rootRe.Match($src)
    $rows  = $rowRe.Matches($src)

    if (-not $rootM.Success -or $rows.Count -eq 0) {
        Say 'CANNOT COMPUTE: could not parse $driveRoot / $exports out of export-handoff.ps1.'
        Say '  The table was reformatted or removed. This section is now checking nothing.'
    } else {
        $driveRoot = $rootM.Groups[1].Value
        Say "  drive root  $driveRoot$(if (Test-Path $driveRoot) { '' } else { '   (NOT PRESENT on this machine)' })"
        Say "  live HEAD   $head"
        $seenHeads = @{}

        foreach ($m in $rows) {
            $srcDir  = Join-Path $repo ($m.Groups[1].Value)
            $dstDir  = Join-Path $driveRoot ($m.Groups[2].Value)
            $recurse = $m.Groups[3].Value -eq 'true'
            $leaf    = Split-Path $dstDir -Leaf
            $man     = Join-Path $dstDir "MANIFEST-$leaf.md"

            Say ''
            Say "  [$leaf]"
            Say "    source            $srcDir"

            # Live count of the source, computed here and not taken from anything
            # the export wrote. Same .md rule the export applies.
            if (Test-Path $srcDir) {
                $live = @(Get-ChildItem -LiteralPath $srcDir -File -Recurse:$recurse |
                          Where-Object { $_.Extension -eq '.md' })
                Say "    live files        $($live.Count)"

                # 037 part 2b. THE CONTENT-BASED STALENESS SIGNAL, and the
                # reason it is not a clock. "The last success was 15 hours ago"
                # is unalarming on a Sunday and alarming on a Thursday, and a
                # check that cannot tell those apart is a check that gets
                # ignored. "Four source files are newer than the last success"
                # means the same thing on both days: four things the design
                # session cannot read.
                if ($null -ne $lastSuccessAt) {
                    $newer = @($live | Where-Object { [datetimeoffset]$_.LastWriteTime -gt $lastSuccessAt })
                    if ($newer.Count) {
                        $names = ($newer | Sort-Object LastWriteTime |
                                  ForEach-Object { [IO.Path]::GetRelativePath($srcDir, $_.FullName) })
                        $shown = if ($names.Count -le 8) { $names -join ', ' }
                                 else { (($names[0..7]) -join ', ') + ", ... and $($names.Count - 8) more" }
                        Say "    newer than export  $($newer.Count) — $shown"
                    } else {
                        Say '    newer than export  0'
                    }
                }
            } else {
                Say '    live files        CANNOT COMPUTE: source folder missing'
            }

            # "If a manifest is missing, say so and continue."
            if (-not (Test-Path $man)) {
                Say "    manifest          MISSING — no MANIFEST-$leaf.md in $dstDir"
                Say '                      (the export has not run against this destination,'
                Say '                       or the mirror is not present on this machine)'
                continue
            }

            $mtext = Get-Content $man -Raw
            $mHead  = ([regex]'(?m)^\*\*HEAD\*\*\s+(.+?)\s*$').Match($mtext)
            $mStamp = ([regex]'(?m)^\*\*exported\*\*\s+(.+?)\s*$').Match($mtext)
            $mCount = ([regex]'(?m)^\*\*files\*\*\s+(\d+)').Match($mtext)
            $mTree  = ([regex]'(?m)^\*\*working tree\*\*\s+(.+?)\s*$').Match($mtext)

            Say ("    manifest HEAD     " + $(if ($mHead.Success)  { $mHead.Groups[1].Value }  else { 'CANNOT COMPUTE: no **HEAD** line' }))
            Say ("    exported at       " + $(if ($mStamp.Success) { $mStamp.Groups[1].Value } else { 'CANNOT COMPUTE: no **exported** line' }))
            Say ("    manifest files    " + $(if ($mCount.Success) { $mCount.Groups[1].Value } else { 'CANNOT COMPUTE: no **files** line' }))
            Say ("    tree at export    " + $(if ($mTree.Success)  { $mTree.Groups[1].Value }  else { 'CANNOT COMPUTE: no **working tree** line' }))

            if ($mHead.Success) { $seenHeads[$leaf] = $mHead.Groups[1].Value }
        }

        # "If the two manifests disagree with each other, print both rather than
        # picking one." This is the drift the one-script decision exists to
        # prevent: both mirrors must reflect the same HEAD, and a well-formed
        # value answering a different question would otherwise be invisible.
        $distinct = @($seenHeads.Values | Sort-Object -Unique)
        Say ''
        if ($seenHeads.Count -lt 2) {
            Say "  manifests read: $($seenHeads.Count) of $($rows.Count). No cross-manifest comparison possible."
        } elseif ($distinct.Count -eq 1) {
            Say "  both manifests carry the same HEAD: $($distinct[0])"
        } else {
            Say '  THE MANIFESTS CARRY DIFFERENT HEADs. Both are printed; neither is preferred:'
            foreach ($k in ($seenHeads.Keys | Sort-Object)) {
                Say "    $k -> $($seenHeads[$k])"
            }
        }
    }
}

# --- runtime ----------------------------------------------------------------
$elapsed = ((Get-Date) - $start).TotalSeconds
Say ''
Say ('-' * 72)
Say ("verify.ps1 runtime: {0:N1}s" -f $elapsed)
if ($null -ne $suiteSeconds) {
    Say ("  of which pytest: {0:N1}s" -f $suiteSeconds)
    if ($suiteSeconds -gt 100) {
        # Stated because a 2-minute default cap currently fails a 128s suite by
        # 8 seconds, and to anyone who has not seen it before that reads as a
        # hang rather than as a slow scan.
        Say ''
        Say ("  NOTE: the suite took {0:N1}s, over 100s. A 2-minute default timeout" -f $suiteSeconds)
        Say '        fails a 128s suite by 8 seconds and reads as a hang. If this is'
        Say '        unexpected, something large has landed under a directory the'
        Say '        scans walk.'
    }
}
Say ''
Say 'verify.ps1 states five facts and draws no conclusion from them.'
Say 'The reading belongs to the design session.'

# --- the file ---------------------------------------------------------------
# 023 part 1. The only write this script makes.
#
# OVERWRITTEN, never appended. The file describes ONE run of ONE tree at ONE
# HEAD; a growing file invites reading a stale section as current, which is the
# exact confusion the verification gate exists to prevent.

$headAtEnd = Get-Head $repo

if ($headAtEnd -ne $headAtStart) {
    # LOUD, and in the header rather than at the bottom. A reader who opens this
    # file out of context must not have to reach the end to learn that the tree
    # moved underneath it -- every section above describes a different commit
    # from every section below, and which is which is not recoverable.
    $moved = @(
        ''
        '!! THE TREE MOVED DURING THIS RUN. Sections above and below the change'
        "!! describe different commits, and this file cannot say which is which."
        "!!   HEAD at start  $headAtStart"
        "!!   HEAD at end    $headAtEnd"
        '!! Re-run verify.ps1 against a still tree before reading anything below.'
    )
    $script:Captured.InsertRange($headerEnd, [string[]]$moved)
    $moved | ForEach-Object { Write-Host $_ }   # console too, at the point we learn it
}

try {
    Set-Content -LiteralPath $outFile -Value $script:Captured -Encoding utf8NoBOM
    Write-Host ''
    Write-Host "written to $outFile"
} catch {
    # Never fatal. The console output is already complete, and a script that
    # dies at the last line reports less than one that says what it could not do.
    Write-Host ''
    Write-Host "CANNOT WRITE $outFile : $_"
    Write-Host 'The console output above is complete and unaffected.'
}
