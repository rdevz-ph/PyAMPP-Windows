param(
    [string]$TargetPhpPath
)

$ErrorActionPreference = 'Stop'

function Test-IsAdmin {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdmin)) {
    Write-Error "Administrator privileges required to modify system PATH."
    exit 1
}

if (-not $TargetPhpPath -or -not (Test-Path -LiteralPath $TargetPhpPath)) {
    Write-Error "Valid PHP path required."
    exit 1
}

function Clean-PhpPaths {
    param([string]$PathValue)
    if ([string]::IsNullOrWhiteSpace($PathValue)) { return '' }
    
    # Remove any existing paths that contain php.exe or are common PHP locations
    $parts = $PathValue -split ';' | ForEach-Object { $_.Trim() } | Where-Object {
        $_ -and 
        (Test-Path -Path $_) -and
        -not (Test-Path -Path (Join-Path $_ "php.exe")) -and
        $_ -inotlike "*php*"
    }
    ($parts | Select-Object -Unique) -join ';'
}

# Backup current paths
$backupDir = Join-Path $env:USERPROFILE 'PyAMPP_Path_Backups'
if (-not (Test-Path $backupDir)) { New-Item -ItemType Directory -Path $backupDir | Out-Null }
$timestamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$machinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
$backupFile = Join-Path $backupDir "backup_$timestamp.txt"
"UserPath: $userPath`nMachinePath: $machinePath" | Set-Content $backupFile

# Clean and Update
$cleanUserPath = Clean-PhpPaths -PathValue $userPath
$cleanMachinePath = Clean-PhpPaths -PathValue $machinePath

# Add new PHP path to the start of Machine Path
$newMachinePath = "$TargetPhpPath;$cleanMachinePath"

[Environment]::SetEnvironmentVariable('Path', $cleanUserPath, 'User')
[Environment]::SetEnvironmentVariable('Path', $newMachinePath, 'Machine')

Write-Host "SUCCESS: Global PHP set to $TargetPhpPath"
