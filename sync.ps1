# sync.ps1 -- pull everything Drive is holding into this tree.
#
# 045 Part 1. ONE WORD, AT THE REPOSITORY ROOT, BESIDE verify.ps1, because that
# is the shape Christoph already knows.
#
# THE DEFECT THIS EXISTS FOR. `tools/sync_from_drive.py` had no trigger of its
# own: it ran when a task ran, because a task running is what made someone
# invoke it. For `handoff/inbox/` that was invisible -- files arrive by the same
# run that consumes them. For `christoph/open/` it is exactly backwards.
# **A UAT arrives BETWEEN tasks, and between tasks nothing runs.** Four UAT files
# sat in Drive on 2026-08-15 while `christoph/open/` held one `.gitkeep`.
#
# AND CHRISTOPH COULD NOT INVOKE IT. Running things is his by design, and **no
# document stated the command.** He was the one party who could have unblocked it
# and nothing told him how. That is the whole reason this file is one word.
#
# IT WRAPS, IT DOES NOT REIMPLEMENT. Every rule -- one-way, additive, never
# overwrite, compare on content not mtime, refuse a number collision -- lives in
# the Python copier and in `config/sync.yaml`. A second implementation of those
# rules is precisely what `026` exists to prevent.

param(
    # One pair id, repeatable. Default: every configured pair.
    [string[]] $Pair,
    # Report what would be copied and copy nothing.
    [switch] $DryRun
)

$ErrorActionPreference = 'Continue'

# **The interpreter is named absolutely and is not discovered.** There is no
# `python` on PATH on this machine, deliberately, and a wrapper that searched for
# one would find whichever came first and run the sync against the wrong
# environment's `yaml`.
$python = 'C:\venvs\trading\Scripts\python.exe'
$repo   = $PSScriptRoot
$tool   = Join-Path $repo 'tools\sync_from_drive.py'

if (-not (Test-Path -LiteralPath $python)) {
    Write-Host "CANNOT RUN: $python not found."
    Write-Host 'There is no `python` on PATH on this machine by design; the venv'
    Write-Host 'interpreter is named in full. If the venv moved, fix it here and'
    Write-Host 'in CLAUDE.md together -- two copies of a path is how one goes stale.'
    exit 2
}
if (-not (Test-Path -LiteralPath $tool)) {
    Write-Host "CANNOT RUN: $tool not found."
    exit 2
}

$argv = @($tool)
foreach ($p in $Pair) { $argv += @('--pair', $p) }
if ($DryRun) { $argv += '--dry-run' }

# **The copier's exit code is passed straight through.** Non-zero means a person
# must look -- a refused file, a differing file, an unreachable source or
# destination. A wrapper that swallowed it would turn every refusal into a
# silent success, which is the failure mode this whole chain is built against.
& $python @argv
$code = $LASTEXITCODE

if ($code -ne 0) {
    Write-Host ''
    Write-Host "sync.ps1: the copier exited $code -- something above needs a person."
    Write-Host 'Nothing was overwritten. A differing file means Drive and the tree'
    Write-Host 'disagree about a document one of them has already been read from;'
    Write-Host 'resolve it by hand rather than by re-running.'
}

exit $code
