param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('backup','restore','drill','web-outage','reject-corrupt')][string]$Action,
    [Parameter(Mandatory=$true)][string]$RunId,
    [string]$BackupId='', [string]$SnapshotId='', [string]$ManifestSha256='',
    [int]$Port=8081, [int]$PostOrders=3,
    [switch]$ReleaseSourceContainers, [switch]$ReturnSource
)
$ErrorActionPreference='Stop'
$script=Join-Path $PSScriptRoot 'controller.py'
$arguments=@($script,$Action,'--run-id',$RunId,'--port',"$Port",'--post-orders',"$PostOrders")
if ($BackupId) {$arguments+=@('--backup-id',$BackupId)}
if ($SnapshotId) {$arguments+=@('--snapshot-id',$SnapshotId)}
if ($ManifestSha256) {$arguments+=@('--manifest-sha256',$ManifestSha256)}
if ($ReleaseSourceContainers) {$arguments+='--release-source-containers'}
if ($ReturnSource) {$arguments+='--return-source'}
# Windows launcher is explicit: unlike Phase 1/2, this observer needs host Python.
if (Get-Command py -ErrorAction SilentlyContinue) {& py -3 @arguments}
elseif (Get-Command python -ErrorAction SilentlyContinue) {& python @arguments}
else {throw 'Install Python 3.10+ on the observer host; Phase 1/2 still require only Docker.'}
exit $LASTEXITCODE
