# register-sync-task.ps1 -- create the 15-minute inbound sync as a Windows
# Scheduled Task. 045 Part 2.
#
# ============================================================================
# CHRISTOPH RUNS THIS. IT IS NOT RUN BY A CLAUDE SESSION.
#
#   Right-click PowerShell -> Run as Administrator, then:
#       D:\Dev\momentum\tools\register-sync-task.ps1
#
# Registering a scheduled task writes to the machine, outside the repository.
# That is a system change, and system changes are Christoph's.
# ============================================================================
#
# WHY A SCHEDULED RUN AT ALL, AND WHY THIS OVERTURNS 037.
#
# `037` ruled out a daemon, and its reasoning was sound at the time: *a missed
# export is visible in verify.ps1; a background process that fails quietly is
# not.* THE OBJECTION WAS TO SILENCE.
#
# `043` gave the inbound copier a run record. A scheduled run that dies now
# leaves `last_attempt` moved and `last_success` stale -- the exact signature --
# and `verify.ps1` section 6 prints both. **The silence is gone, so the
# objection is spent.**
#
# And `verify.ps1` alone cannot carry this. It runs at the end of a task, which
# is the same broken clock the trigger exists to fix: an instrument pointed at
# the thing it is meant to detect the absence of. Four UAT files sat in Drive on
# 2026-08-15 precisely because nothing runs between tasks.
#
# INBOUND ONLY. The export is NOT scheduled and must not be -- `037` settled
# that it runs as a task's last action, after the commit, and a scheduled export
# would race a session mid-commit.

param(
    [string] $TaskName = 'momentum-inbound-sync',
    [int]    $EveryMinutes = 15,
    [switch] $Remove
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$log  = Join-Path $repo 'sync-scheduled.log'

if ($Remove) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "removed scheduled task '$TaskName'"
    exit 0
}

# **Logs to a file, not to a console nobody is watching** (045 Part 2). The run
# record answers *did it work*; this answers *what did it say* when the record
# says it did not.
$inner = "& '$repo\sync.ps1' *>&1 | Out-File -FilePath '$log' -Append -Encoding utf8"
$action = New-ScheduledTaskAction -Execute 'powershell.exe' `
    -Argument "-NoProfile -NonInteractive -ExecutionPolicy Bypass -Command `"$inner`"" `
    -WorkingDirectory $repo

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes $EveryMinutes)

# **No `-RunLevel Highest`.** The sync copies files between two folders this
# user already owns. A scheduled job that runs elevated for no reason is a
# standing offer to whatever it executes.
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 10)

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Settings $settings -Description `
    'momentum: pull Drive-held handoff and UAT files into the tree every 15 minutes (045 Part 2). Inbound only; never the export.' `
    -Force | Out-Null

Write-Host "registered '$TaskName' -- every $EveryMinutes minutes"
Write-Host "  runs   $repo\sync.ps1"
Write-Host "  logs   $log"
Write-Host ''
Write-Host 'Check it worked:'
Write-Host "  Get-ScheduledTask -TaskName '$TaskName'"
Write-Host "  Get-ScheduledTaskInfo -TaskName '$TaskName'   # LastRunTime, LastTaskResult"
Write-Host ''
Write-Host 'And read the run record, which is the thing that says whether it WORKED:'
Write-Host "  verify.ps1 section 6, or $repo\sync-run-record.md"
