<#
.SYNOPSIS
    Initializes Conda shell and activates the factorio-agent environment when inside the project folder.

.DESCRIPTION
    This script is designed for PowerShell 7+ and should be dot-sourced from your profile.
    It checks for the presence of Conda, initializes the shell hook, and activates the environment
    only when you're working inside the Factorio-Agent project directory.

.NOTES
    Author: Mike
    Tags: Factorio-Agent, QoL, conda_init, env_activation, startup_hook
#>

#region Conda Initialization for Factorio-Agent (QoL)
$condaExe = "$env:USERPROFILE\Conda\Scripts\conda.exe"
if (Test-Path $condaExe) {
    Write-Host "[Factorio-Agent] Initializing Conda shell hook..."
    & $condaExe 'shell.powershell' 'hook' | Out-String | Invoke-Expression
} else {
    Write-Host "[Factorio-Agent] WARNING: Conda executable not found at: $condaExe"
}
#endregion

#region Auto-activate factorio-agent if in project folder
$projectRoot = "D:\Projects\Factorio-Agent"
$currentPath = (Get-Location).Path
if ($currentPath -like "$projectRoot*") {
    Write-Host "[Factorio-Agent] Activating Conda environment: factorio-agent"
    try {
        & $condaExe activate factorio-agent
    } catch {
        Write-Host "[Factorio-Agent] ERROR: Failed to activate Conda environment: $_"
    }
}
#endregion