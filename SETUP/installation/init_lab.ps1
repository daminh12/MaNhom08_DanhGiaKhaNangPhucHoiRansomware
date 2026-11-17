# Windows PowerShell 5.1+. Creates local-only credentials; never overwrites them.
$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$secretDir = Join-Path $repoRoot 'secrets'
$envFile = Join-Path $repoRoot '.env'
if ((Test-Path $envFile) -or (Test-Path $secretDir)) {
    throw 'Config or secrets already exist. Nothing was overwritten. Reuse the existing lab config; review partial setup manually.'
}
# A fresh checkout may still point to an existing lab on the same Docker daemon.
# Inspect before creating any files; never replace credentials for an old volume.
$sourceVolumeNames = @(& docker volume ls --format '{{.Name}}')
if ($LASTEXITCODE -ne 0) {
    throw 'Cannot inspect Docker volumes. No config or secrets were created. Make Docker Desktop ready and retry the checks.'
}
$sourceContainerIds = @(& docker ps --all --quiet --filter 'label=com.docker.compose.project=group08-lab')
if ($LASTEXITCODE -ne 0) {
    throw 'Cannot inspect lab containers. No config or secrets were created. Make Docker Desktop ready and retry the checks.'
}
if (($sourceVolumeNames -contains 'group08-lab_db_data') -or ($sourceContainerIds.Count -gt 0)) {
    throw 'Existing group08-lab Docker resources found. No config or secrets were created. Recover the original lab config and secrets before continuing; do not remove data volumes to rerun init.'
}
$encoding = New-Object System.Text.UTF8Encoding($false)
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
    New-Item -ItemType Directory -Path $secretDir | Out-Null
    foreach ($file in @('db_root_password.txt', 'db_app_password.txt')) {
        $bytes = New-Object byte[] 32
        $rng.GetBytes($bytes)
        $password = [BitConverter]::ToString($bytes).Replace('-', '').ToLowerInvariant()
        [System.IO.File]::WriteAllText((Join-Path $secretDir $file), $password, $encoding)
    }
    [System.IO.File]::WriteAllText($envFile, "WEB_PORT=8080`n", $encoding)
} finally {
    $rng.Dispose()
}
Write-Host 'Lab config created. Credentials stay in secrets/. Do not commit or share that directory.'
Write-Host 'Next: docker compose up -d --build --wait --wait-timeout 180'
