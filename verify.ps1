# verify.ps1 — four facts about this tree, and no opinion about them.
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
# exit-code-as-verdict. Four sections of raw fact, and the reading belongs to
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
Write-Host 'verify.ps1 states four facts and draws no conclusion from them.'
Write-Host 'The reading belongs to the design session.'
