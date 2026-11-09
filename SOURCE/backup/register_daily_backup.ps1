param([string]$At = '18:00')
$ErrorActionPreference = 'Stop'
$scriptPath = Join-Path $PSScriptRoot 'backup.ps1'
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -Action Backup"
$trigger = New-ScheduledTaskTrigger -Daily -At $At
$principal = New-ScheduledTaskPrincipal -UserId ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew
# Refuse to overwrite a task that someone already configured.
if (Get-ScheduledTask -TaskName 'Group08-Lab-Backup' -ErrorAction SilentlyContinue) { throw 'Task already exists; review it before changing the schedule.' }
Register-ScheduledTask -TaskName 'Group08-Lab-Backup' -Action $action -Trigger $trigger -Principal $principal -Settings $settings
