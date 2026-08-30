[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$runtimeDir = Join-Path $projectRoot ".run"
$backendPidFile = Join-Path $runtimeDir "backend.json"
$frontendPidFile = Join-Path $runtimeDir "frontend.json"
$pythonPath = Join-Path $projectRoot "backend\.venv\Scripts\python.exe"

function Stop-TrackedProcess {
    param(
        [Parameter(Mandatory = $true)][string]$RecordPath,
        [Parameter(Mandatory = $true)][string]$ExpectedExecutable,
        [Parameter(Mandatory = $true)][string]$ExpectedCommandToken,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if (-not (Test-Path -LiteralPath $RecordPath)) {
        Write-Host "No launcher-owned $Name process is recorded; nothing was stopped."
        return
    }

    try {
        $record = Get-Content -LiteralPath $RecordPath -Raw | ConvertFrom-Json
        $trackedPid = [int]$record.pid
    }
    catch {
        throw "The $Name PID record is invalid. No process was stopped."
    }

    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $trackedPid"
    if ($null -eq $process) {
        Remove-Item -LiteralPath $RecordPath -Force
        Write-Host "Removed the stale $Name PID record."
        return
    }

    $expectedPath = [System.IO.Path]::GetFullPath($ExpectedExecutable)
    if (
        [string]::IsNullOrWhiteSpace($process.ExecutablePath) -or
        $process.ExecutablePath -ine $expectedPath -or
        [string]::IsNullOrWhiteSpace($process.CommandLine) -or
        $process.CommandLine.IndexOf(
            $ExpectedCommandToken,
            [StringComparison]::OrdinalIgnoreCase
        ) -lt 0
    ) {
        throw "Safety check failed for tracked $Name PID $trackedPid. No process was stopped."
    }

    Stop-Process -Id $trackedPid -Force
    Wait-Process -Id $trackedPid -Timeout 10 -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $RecordPath -Force
    Write-Host "Stopped CourtSniper $Name (PID $trackedPid)."
}

if (Test-Path -LiteralPath $backendPidFile) {
    try {
        $runStatus = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/run-sniper/status" -TimeoutSec 3
        if ($runStatus.run.state -eq "running") {
            Write-Host "Stopping the active CourtSniper run before stopping the backend..."
            Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/api/run-sniper/stop" -TimeoutSec 15 | Out-Null
        }
    }
    catch {
        Write-Warning "The active-run check was unavailable; launcher-owned processes will still be validated before stopping."
    }
}

$nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
if ($null -ne $nodeCommand) {
    $frontendStopParameters = @{
        RecordPath = $frontendPidFile
        ExpectedExecutable = $nodeCommand.Source
        ExpectedCommandToken = "vite.js"
        Name = "frontend"
    }
    Stop-TrackedProcess @frontendStopParameters
}
elseif (Test-Path -LiteralPath $frontendPidFile) {
    throw "Node.js is no longer available in PATH, so the frontend PID cannot be safely validated. No frontend process was stopped."
}
else {
    Write-Host "No launcher-owned frontend process is recorded; nothing was stopped."
}

if (Test-Path -LiteralPath $pythonPath -PathType Leaf) {
    $backendStopParameters = @{
        RecordPath = $backendPidFile
        ExpectedExecutable = $pythonPath
        ExpectedCommandToken = "src.api:app"
        Name = "backend"
    }
    Stop-TrackedProcess @backendStopParameters
}
elseif (Test-Path -LiteralPath $backendPidFile) {
    throw "Backend Python is missing, so the backend PID cannot be safely validated. No backend process was stopped."
}
else {
    Write-Host "No launcher-owned backend process is recorded; nothing was stopped."
}

Write-Host "CourtSniper launcher-owned services are stopped."
