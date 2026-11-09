# Windows PowerShell 5.1+. Creates local-only credentials; never overwrites them.
$ErrorActionPreference = 'Stop'
$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$secretDir = Join-Path $repoRoot 'secrets'
$envFile = Join-Path $repoRoot '.env'
if ((Test-Path $envFile) -or (Test-Path $secretDir)) {
    throw 'Config or secrets already exist. Nothing was overwritten. Reuse the existing lab config; review partial setup manually.'
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
