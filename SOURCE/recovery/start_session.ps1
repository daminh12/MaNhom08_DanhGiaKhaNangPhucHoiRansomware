# Dot-source at repository root: . .\SOURCE\recovery\start_session.ps1
# Starts an evidence transcript and checks tools; never starts/stops services.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
if ((Get-Location).Path.TrimEnd('\') -ne $repoRoot.TrimEnd('\')) {
    throw 'Open PowerShell at repository root before starting a session.'
}
function Invoke-Checked {
    param([string]$Exe, [string[]]$Arguments)
    # Use only documented commands. Never pass a password on a command line.
    Write-Host ('> ' + $Exe + ' ' + ($Arguments -join ' '))
    & $Exe @Arguments
    $commandExit = $LASTEXITCODE
    Write-Host ('exit=' + $commandExit)
    if ($commandExit -ne 0) { throw "Command $Exe failed, exit=$commandExit" }
}
function Invoke-Recovery {
    param([string[]]$LabArgs)
    Invoke-Checked -Exe 'powershell.exe' -Arguments (@(
        '-NoProfile','-ExecutionPolicy','Bypass','-File','.\SOURCE\recovery\run_lab.ps1'
    ) + $LabArgs)
}
function New-LabRunId {
    param([ValidateSet('p3','p4')][string]$Phase, [string]$Label)
    if ($Label -notmatch '^[a-z0-9-]{1,20}$') { throw 'Use a short lowercase run label.' }
    return $Phase + '-' + $Label + '-' + [guid]::NewGuid().ToString('N').Substring(0,12)
}
$session = 'win-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0,6)
$sessionDir = Join-Path $repoRoot ('work\sessions\' + $session)
New-Item -ItemType Directory -Path $sessionDir | Out-Null
Copy-Item -Path (Join-Path $repoRoot 'docs\templates\windows\*.csv') -Destination $sessionDir
Start-Transcript -Path (Join-Path $sessionDir 'powershell.txt') -NoClobber | Out-Host
Write-Host ('Session evidence: ' + $sessionDir)
Write-Host ('UTC: ' + [DateTime]::UtcNow.ToString('o'))
Write-Host ('Local: ' + (Get-Date).ToString('o'))
Invoke-Checked -Exe 'git' -Arguments @('status','--short','--branch')
Invoke-Checked -Exe 'git' -Arguments @('rev-parse','HEAD')
Invoke-Checked -Exe 'py' -Arguments @('-3','--version')
Invoke-Checked -Exe 'docker' -Arguments @('version')
Invoke-Checked -Exe 'docker' -Arguments @('compose','version')
Invoke-Checked -Exe 'docker' -Arguments @('info','--format','{{.OSType}}')
Write-Host 'Check output and disk capacity. This session helper does NOT grant a preflight PASS.'
Write-Host 'Keep this terminal open during Guided. End with Stop-Transcript.'
