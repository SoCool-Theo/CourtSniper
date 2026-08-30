[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$backendDir = Join-Path $projectRoot "backend"
$frontendDir = Join-Path $projectRoot "frontend"
$runtimeDir = Join-Path $projectRoot ".run"
$backendPidFile = Join-Path $runtimeDir "backend.json"
$frontendPidFile = Join-Path $runtimeDir "frontend.json"
$backendStdout = Join-Path $runtimeDir "backend.stdout.log"
$backendStderr = Join-Path $runtimeDir "backend.stderr.log"
$frontendStdout = Join-Path $runtimeDir "frontend.stdout.log"
$frontendStderr = Join-Path $runtimeDir "frontend.stderr.log"
$pythonPath = Join-Path $backendDir ".venv\Scripts\python.exe"
$viteScript = Join-Path $frontendDir "node_modules\vite\bin\vite.js"

function Get-BackendState {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/status" -TimeoutSec 2
        if ($response.service -eq "CourtSniper" -and $response.status -eq "online") {
            return "ready"
        }
        return "unexpected"
    }
    catch {
        $responseProperty = $_.Exception.PSObject.Properties["Response"]
        if ($null -ne $responseProperty -and $null -ne $responseProperty.Value) {
            return "unexpected"
        }
        return "offline"
    }
}

function Get-FrontendState {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:5173/" -TimeoutSec 2 -UseBasicParsing
        if (
            $response.StatusCode -eq 200 -and
            $response.Content -match "CourtSniper \| Precision Booking"
        ) {
            return "ready"
        }
        return "unexpected"
    }
    catch {
        $responseProperty = $_.Exception.PSObject.Properties["Response"]
        if ($null -ne $responseProperty -and $null -ne $responseProperty.Value) {
            return "unexpected"
        }
        return "offline"
    }
}

function Write-ProcessRecord {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][System.Diagnostics.Process]$Process,
        [Parameter(Mandatory = $true)][string]$ExecutablePath,
        [Parameter(Mandatory = $true)][string]$CommandToken
    )

    [ordered]@{
        pid = $Process.Id
        executable_path = [System.IO.Path]::GetFullPath($ExecutablePath)
        command_token = $CommandToken
        started_at_utc = [DateTime]::UtcNow.ToString("o")
    } | ConvertTo-Json | Set-Content -LiteralPath $Path -Encoding UTF8
}

function Get-ValidatedTrackedProcess {
    param(
        [Parameter(Mandatory = $true)][string]$RecordPath,
        [Parameter(Mandatory = $true)][string]$ExpectedExecutable,
        [Parameter(Mandatory = $true)][string]$ExpectedCommandToken,
        [Parameter(Mandatory = $true)][string]$Name
    )

    if (-not (Test-Path -LiteralPath $RecordPath)) {
        return $null
    }

    try {
        $record = Get-Content -LiteralPath $RecordPath -Raw | ConvertFrom-Json
        $trackedPid = [int]$record.pid
    }
    catch {
        throw "The $Name PID record is invalid. Remove '$RecordPath' only after confirming no $Name process is running."
    }

    $process = Get-CimInstance Win32_Process -Filter "ProcessId = $trackedPid"
    if ($null -eq $process) {
        Remove-Item -LiteralPath $RecordPath -Force
        return $null
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
        throw "Safety check failed for tracked $Name PID $trackedPid. No process was stopped or replaced."
    }

    return $process
}

function Wait-ForService {
    param(
        [Parameter(Mandatory = $true)][scriptblock]$Probe,
        [Parameter(Mandatory = $true)][System.Diagnostics.Process]$Process,
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$ErrorLog,
        [int]$TimeoutSeconds = 30
    )

    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        if ((& $Probe) -eq "ready") {
            return
        }
        if ($Process.HasExited) {
            $details = ""
            if (Test-Path -LiteralPath $ErrorLog) {
                $details = (Get-Content -LiteralPath $ErrorLog -Tail 20) -join [Environment]::NewLine
            }
            throw "$Name exited before becoming ready. $details"
        }
        Start-Sleep -Milliseconds 500
    }

    throw "$Name did not become ready within $TimeoutSeconds seconds."
}

if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    throw "Backend Python was not found at '$pythonPath'. Create backend/.venv and install requirements first."
}
if (-not (Test-Path -LiteralPath $viteScript -PathType Leaf)) {
    throw "Frontend dependencies are missing. Run 'npm install' in '$frontendDir' first."
}

$nodeCommand = Get-Command node.exe -ErrorAction SilentlyContinue
if ($null -eq $nodeCommand) {
    throw "Node.js was not found in PATH. Install Node.js before starting CourtSniper."
}
$nodePath = $nodeCommand.Source

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

$backendTrackingParameters = @{
    RecordPath = $backendPidFile
    ExpectedExecutable = $pythonPath
    ExpectedCommandToken = "src.api:app"
    Name = "backend"
}
$backendTracked = Get-ValidatedTrackedProcess @backendTrackingParameters
$backendState = Get-BackendState

if ($backendState -eq "unexpected") {
    throw "Port 8000 is occupied by an unexpected service. CourtSniper did not replace it."
}
if ($backendState -eq "offline" -and $null -ne $backendTracked) {
    throw "The tracked backend process is running but its health endpoint is unavailable. Check '$backendStderr'."
}

if ($backendState -eq "ready") {
    Write-Host "CourtSniper backend is already available at http://127.0.0.1:8000"
}
else {
    Remove-Item -LiteralPath $backendStdout, $backendStderr -Force -ErrorAction SilentlyContinue
    $backendStartParameters = @{
        FilePath = $pythonPath
        ArgumentList = @(
            "-m",
            "uvicorn",
            "src.api:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000"
        )
        WorkingDirectory = $backendDir
        WindowStyle = "Hidden"
        RedirectStandardOutput = $backendStdout
        RedirectStandardError = $backendStderr
        PassThru = $true
    }
    $backendProcess = Start-Process @backendStartParameters
    $backendRecordParameters = @{
        Path = $backendPidFile
        Process = $backendProcess
        ExecutablePath = $pythonPath
        CommandToken = "src.api:app"
    }
    Write-ProcessRecord @backendRecordParameters

    try {
        $backendWaitParameters = @{
            Probe = { Get-BackendState }
            Process = $backendProcess
            Name = "Backend"
            ErrorLog = $backendStderr
        }
        Wait-ForService @backendWaitParameters
    }
    catch {
        if (-not $backendProcess.HasExited) {
            Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
        }
        Remove-Item -LiteralPath $backendPidFile -Force -ErrorAction SilentlyContinue
        throw
    }
    Write-Host "Started CourtSniper backend (PID $($backendProcess.Id))."
}

$frontendTrackingParameters = @{
    RecordPath = $frontendPidFile
    ExpectedExecutable = $nodePath
    ExpectedCommandToken = "vite.js"
    Name = "frontend"
}
$frontendTracked = Get-ValidatedTrackedProcess @frontendTrackingParameters
$frontendState = Get-FrontendState

if ($frontendState -eq "unexpected") {
    throw "Port 5173 is occupied by an unexpected service. CourtSniper did not replace it."
}
if ($frontendState -eq "offline" -and $null -ne $frontendTracked) {
    throw "The tracked frontend process is running but its HTTP endpoint is unavailable. Check '$frontendStderr'."
}

if ($frontendState -eq "ready") {
    Write-Host "CourtSniper frontend is already available at http://127.0.0.1:5173"
}
else {
    Remove-Item -LiteralPath $frontendStdout, $frontendStderr -Force -ErrorAction SilentlyContinue
    $frontendStartParameters = @{
        FilePath = $nodePath
        ArgumentList = @(
            "node_modules/vite/bin/vite.js",
            "--host",
            "127.0.0.1",
            "--port",
            "5173"
        )
        WorkingDirectory = $frontendDir
        WindowStyle = "Hidden"
        RedirectStandardOutput = $frontendStdout
        RedirectStandardError = $frontendStderr
        PassThru = $true
    }
    $frontendProcess = Start-Process @frontendStartParameters
    $frontendRecordParameters = @{
        Path = $frontendPidFile
        Process = $frontendProcess
        ExecutablePath = $nodePath
        CommandToken = "vite.js"
    }
    Write-ProcessRecord @frontendRecordParameters

    try {
        $frontendWaitParameters = @{
            Probe = { Get-FrontendState }
            Process = $frontendProcess
            Name = "Frontend"
            ErrorLog = $frontendStderr
        }
        Wait-ForService @frontendWaitParameters
    }
    catch {
        if (-not $frontendProcess.HasExited) {
            Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
        }
        Remove-Item -LiteralPath $frontendPidFile -Force -ErrorAction SilentlyContinue
        throw
    }
    Write-Host "Started CourtSniper frontend (PID $($frontendProcess.Id))."
}

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Warning "Configuring the highest-privilege Windows scheduled task may require running this launcher from an elevated PowerShell window."
}

Write-Host "CourtSniper is ready: http://127.0.0.1:5173"
