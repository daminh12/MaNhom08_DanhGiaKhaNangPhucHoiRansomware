param(
    [ValidateSet('Setup', 'Backup', 'Snapshots', 'Check', 'Verify')]
    [string]$Action = 'Backup',
    [string]$RunId = ''
)
$ErrorActionPreference = 'Stop'
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$dc = @('compose', '-f', 'compose.yaml', '-f', 'compose.backup.yaml')
function Invoke-Docker([string[]]$DockerArgs) {
    & docker @DockerArgs
    if ($LASTEXITCODE -ne 0) { throw "Docker failed with exit $LASTEXITCODE" }
}
function New-LabRunId { return 'p2-' + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ') + '-' + [Guid]::NewGuid().ToString('N').Substring(0, 12) }
function Copy-DbInputs([string]$Id) {
    Invoke-Docker ($dc + @('cp', 'SOURCE/backup/db_dump.sh', 'db:/tmp/group08_phase2_db.sh'))
    Invoke-Docker ($dc + @('cp', 'secrets/db_backup_password.txt', "db:/tmp/group08-$Id.secret"))
}
Push-Location $repoRoot
try {
    if (-not (Test-Path 'secrets/db_root_password.txt')) { throw 'Run Phase 1 setup first.' }
    if ($Action -eq 'Setup') {
        $encoding = New-Object Text.UTF8Encoding($false)
        $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
        try {
            foreach ($name in @('db_backup_password.txt', 'restic_password.txt')) {
                $path = Join-Path 'secrets' $name
                if (-not (Test-Path $path)) {
                    if (($name -eq 'restic_password.txt') -and (Test-Path 'backups/restic/config')) { throw 'Existing repository has no local password file; recover the original secret. Nothing was reset.' }
                    $bytes = New-Object byte[] 32
                    $rng.GetBytes($bytes)
                    [IO.File]::WriteAllText((Join-Path $repoRoot $path), [BitConverter]::ToString($bytes).Replace('-', '').ToLowerInvariant(), $encoding)
                }
                if ([IO.File]::ReadAllText((Join-Path $repoRoot $path)) -notmatch '^[a-f0-9]{64}$') { throw 'Unexpected credential format; refusing to replace it.' }
            }
        } finally { $rng.Dispose() }
        New-Item -ItemType Directory -Force backups/runs | Out-Null
        Invoke-Docker ($dc + @('build', 'backup'))
        $setupId = New-LabRunId
        try {
            Copy-DbInputs $setupId
            Invoke-Docker ($dc + @('exec', '-T', 'db', 'sh', '/tmp/group08_phase2_db.sh', 'provision', $setupId))
        } finally {
            & docker @dc exec -T db sh /tmp/group08_phase2_db.sh cleanup $setupId
        }
        if (Test-Path 'backups/restic/config') { Invoke-Docker ($dc + @('run', '--rm', '--no-deps', 'backup', 'check')) }
        else { Invoke-Docker ($dc + @('run', '--rm', '--no-deps', 'backup', 'init')) }
    } elseif ($Action -eq 'Backup') {
        if (-not (Test-Path 'backups/restic/config')) { throw 'Run -Action Setup first.' }
        if ($RunId) { throw 'Backup generates a fresh RunId; -RunId is only for Verify.' }
        $id = New-LabRunId
        $runPath = Join-Path 'backups/runs' $id
        New-Item -ItemType Directory -Path (Join-Path $runPath 'payload') | Out-Null
        $phase = 'dump_or_copy'
        try {
            Copy-DbInputs $id
            Invoke-Docker ($dc + @('exec', '-T', 'db', 'sh', '/tmp/group08_phase2_db.sh', 'dump', $id))
            foreach ($file in @('database.sql', 'metadata.json')) {
                Invoke-Docker ($dc + @('cp', "db:/tmp/group08-$id/$file", "$runPath/payload/$file"))
            }
            $phase = 'backup_container'
            Invoke-Docker ($dc + @('run', '--rm', '--no-deps', 'backup', 'snapshot', '--run-id', $id))
        } catch {
            $resultPath = Join-Path $runPath 'result.json'
            if (-not (Test-Path $resultPath)) {
                $result = @{run_id=$id; status='FAILED'; phase=$phase; snapshot_id=$null; error='Controller did not receive a verified result; inspect console output.'} | ConvertTo-Json
                [IO.File]::WriteAllText((Join-Path $repoRoot $resultPath), $result, (New-Object Text.UTF8Encoding($false)))
            }
            throw
        } finally {
            & docker @dc exec -T db sh /tmp/group08_phase2_db.sh cleanup $id
        }
    } elseif ($Action -eq 'Verify') {
        if ($RunId -notmatch '^p2-[A-Za-z0-9_-]{1,76}$') { throw 'Verify requires a valid -RunId from result.json.' }
        Invoke-Docker ($dc + @('run', '--rm', '--no-deps', 'backup', 'verify', '--run-id', $RunId))
    } else {
        Invoke-Docker ($dc + @('run', '--rm', '--no-deps', 'backup', $Action.ToLowerInvariant()))
    }
} finally { Pop-Location }
