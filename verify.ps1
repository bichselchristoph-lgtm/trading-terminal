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
# IT NEVER MODIFIES ANYTHING. No writes, no `git add`, no fixture creation. If
# a section cannot be computed it prints why and continues to the next one; a
# script that aborts halfway is one that reports less the more wrong things are.

$ErrorActionPreference = 'Continue'
$python = 'C:\venvs\trading\Scripts\python.exe'
$repo   = $PSScriptRoot
$start  = Get-Date

function Section($n, $title) {
    Write-Host ''
    Write-Host ('=' * 72)
    Write-Host "  $n. $title"
    Write-Host ('=' * 72)
}

Write-Host ''
Write-Host "verify.ps1  --  $repo"
Write-Host "run at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss K')"

# --- 1. the suite -----------------------------------------------------------
Section 1 'SUITE — the pytest summary line, verbatim'

if (-not (Test-Path $python)) {
    Write-Host "CANNOT COMPUTE: $python not found. There is no ``python`` on PATH."
    $suiteSeconds = $null
} else {
    $t0 = Get-Date
    $out = & $python -m pytest --color=no 2>&1 | Out-String
    $suiteSeconds = ((Get-Date) - $t0).TotalSeconds
    # The last line matching pytest's summary shape. Printed verbatim, and NOT
    # translated into a verdict.
    $summary = ($out -split "`n" | Where-Object { $_ -match '^=+ .*(passed|failed|error|no tests ran).* =+\s*$' } | Select-Object -Last 1)
    if ($summary) { Write-Host $summary.Trim() }
    else {
        Write-Host 'CANNOT COMPUTE: no pytest summary line found. Last 15 lines follow:'
        ($out -split "`n" | Select-Object -Last 15) | ForEach-Object { Write-Host "  $_" }
    }
    $failed = ($out -split "`n" | Where-Object { $_ -match '^FAILED |^ERROR ' })
    if ($failed) {
        Write-Host ''
        Write-Host 'named failures:'
        $failed | ForEach-Object { Write-Host "  $($_.Trim())" }
    }
}

# --- 2. uncommitted ---------------------------------------------------------
Section 2 'GIT STATUS — every uncommitted path'

$status = & git -C $repo status --short 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "CANNOT COMPUTE: git status failed: $status" }
elseif (-not $status) { Write-Host '(clean — no uncommitted paths)' }
else { $status | ForEach-Object { Write-Host "  $_" } }

# --- 3. HEAD ----------------------------------------------------------------
Section 3 'HEAD — the commit this output describes'

$head = & git -C $repo log -1 --format="%H %s" 2>&1
if ($LASTEXITCODE -ne 0) { Write-Host "CANNOT COMPUTE: git log failed: $head" }
else { Write-Host "  $head" }

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
    Write-Host "CANNOT COMPUTE: $python not found."
} else {
    $tmp = Join-Path ([System.IO.Path]::GetTempPath()) 'verify_rehash.py'
    Set-Content -Path $tmp -Value $rehash -Encoding UTF8
    & $python $tmp $repo 2>&1 | ForEach-Object { Write-Host "  $_" }
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

$exportScript = Join-Path $repo 'export-handoff.ps1'
if (-not (Test-Path $exportScript)) {
    Write-Host "CANNOT COMPUTE: export-handoff.ps1 not found at $exportScript"
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
        Write-Host 'CANNOT COMPUTE: could not parse $driveRoot / $exports out of export-handoff.ps1.'
        Write-Host '  The table was reformatted or removed. This section is now checking nothing.'
    } else {
        $driveRoot = $rootM.Groups[1].Value
        Write-Host "  drive root  $driveRoot$(if (Test-Path $driveRoot) { '' } else { '   (NOT PRESENT on this machine)' })"
        Write-Host "  live HEAD   $head"
        $seenHeads = @{}

        foreach ($m in $rows) {
            $srcDir  = Join-Path $repo ($m.Groups[1].Value)
            $dstDir  = Join-Path $driveRoot ($m.Groups[2].Value)
            $recurse = $m.Groups[3].Value -eq 'true'
            $leaf    = Split-Path $dstDir -Leaf
            $man     = Join-Path $dstDir "MANIFEST-$leaf.md"

            Write-Host ''
            Write-Host "  [$leaf]"
            Write-Host "    source            $srcDir"

            # Live count of the source, computed here and not taken from anything
            # the export wrote. Same .md rule the export applies.
            if (Test-Path $srcDir) {
                $liveCount = @(Get-ChildItem -LiteralPath $srcDir -File -Recurse:$recurse |
                               Where-Object { $_.Extension -eq '.md' }).Count
                Write-Host "    live files        $liveCount"
            } else {
                Write-Host '    live files        CANNOT COMPUTE: source folder missing'
            }

            # "If a manifest is missing, say so and continue."
            if (-not (Test-Path $man)) {
                Write-Host "    manifest          MISSING — no MANIFEST-$leaf.md in $dstDir"
                Write-Host '                      (the export has not run against this destination,'
                Write-Host '                       or the mirror is not present on this machine)'
                continue
            }

            $mtext = Get-Content $man -Raw
            $mHead  = ([regex]'(?m)^\*\*HEAD\*\*\s+(.+?)\s*$').Match($mtext)
            $mStamp = ([regex]'(?m)^\*\*exported\*\*\s+(.+?)\s*$').Match($mtext)
            $mCount = ([regex]'(?m)^\*\*files\*\*\s+(\d+)').Match($mtext)
            $mTree  = ([regex]'(?m)^\*\*working tree\*\*\s+(.+?)\s*$').Match($mtext)

            Write-Host ("    manifest HEAD     " + $(if ($mHead.Success)  { $mHead.Groups[1].Value }  else { 'CANNOT COMPUTE: no **HEAD** line' }))
            Write-Host ("    exported at       " + $(if ($mStamp.Success) { $mStamp.Groups[1].Value } else { 'CANNOT COMPUTE: no **exported** line' }))
            Write-Host ("    manifest files    " + $(if ($mCount.Success) { $mCount.Groups[1].Value } else { 'CANNOT COMPUTE: no **files** line' }))
            Write-Host ("    tree at export    " + $(if ($mTree.Success)  { $mTree.Groups[1].Value }  else { 'CANNOT COMPUTE: no **working tree** line' }))

            if ($mHead.Success) { $seenHeads[$leaf] = $mHead.Groups[1].Value }
        }

        # "If the two manifests disagree with each other, print both rather than
        # picking one." This is the drift the one-script decision exists to
        # prevent: both mirrors must reflect the same HEAD, and a well-formed
        # value answering a different question would otherwise be invisible.
        $distinct = @($seenHeads.Values | Sort-Object -Unique)
        Write-Host ''
        if ($seenHeads.Count -lt 2) {
            Write-Host "  manifests read: $($seenHeads.Count) of $($rows.Count). No cross-manifest comparison possible."
        } elseif ($distinct.Count -eq 1) {
            Write-Host "  both manifests carry the same HEAD: $($distinct[0])"
        } else {
            Write-Host '  THE MANIFESTS CARRY DIFFERENT HEADs. Both are printed; neither is preferred:'
            foreach ($k in ($seenHeads.Keys | Sort-Object)) {
                Write-Host "    $k -> $($seenHeads[$k])"
            }
        }
    }
}

# --- runtime ----------------------------------------------------------------
$elapsed = ((Get-Date) - $start).TotalSeconds
Write-Host ''
Write-Host ('-' * 72)
Write-Host ("verify.ps1 runtime: {0:N1}s" -f $elapsed)
if ($null -ne $suiteSeconds) {
    Write-Host ("  of which pytest: {0:N1}s" -f $suiteSeconds)
    if ($suiteSeconds -gt 100) {
        # Stated because a 2-minute default cap currently fails a 128s suite by
        # 8 seconds, and to anyone who has not seen it before that reads as a
        # hang rather than as a slow scan.
        Write-Host ''
        Write-Host ("  NOTE: the suite took {0:N1}s, over 100s. A 2-minute default timeout" -f $suiteSeconds)
        Write-Host '        fails a 128s suite by 8 seconds and reads as a hang. If this is'
        Write-Host '        unexpected, something large has landed under a directory the'
        Write-Host '        scans walk.'
    }
}
Write-Host ''
Write-Host 'verify.ps1 states five facts and draws no conclusion from them.'
Write-Host 'The reading belongs to the design session.'
