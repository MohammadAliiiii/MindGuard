# PowerShell script for Windows GPO deployment of Idle Security Reminder
# This script should be run as a Computer Startup Script or User Logon Script

param(
    [string]$SourcePath = "\\domain.com\SYSVOL\domain.com\scripts\idle-reminder",
    [string]$InstallPath = "$env:ProgramFiles\Idle Security Reminder",
    [string]$ConfigSource = "\\domain.com\SYSVOL\domain.com\Policies\idle-reminder\config.yaml",
    [switch]$CreateStartupTask = $true,
    [switch]$ForceReinstall = $false
)

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage
    Add-Content -Path "$env:TEMP\idle-reminder-install.log" -Value $logMessage
}

try {
    Write-Log "Starting Idle Security Reminder deployment"
    
    # Check if already installed and not forcing reinstall
    if ((Test-Path "$InstallPath\idle-reminder.exe") -and -not $ForceReinstall) {
        Write-Log "Idle Security Reminder already installed, skipping installation"
        exit 0
    }
    
    # Create installation directory
    if (-not (Test-Path $InstallPath)) {
        New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
        Write-Log "Created installation directory: $InstallPath"
    }
    
    # Copy application files
    if (Test-Path $SourcePath) {
        Write-Log "Copying files from $SourcePath to $InstallPath"
        Copy-Item -Path "$SourcePath\*" -Destination $InstallPath -Recurse -Force
        Write-Log "Application files copied successfully"
    } else {
        Write-Log "Source path not found: $SourcePath" -Level "ERROR"
        exit 1
    }
    
    # Copy enterprise configuration if available
    if (Test-Path $ConfigSource) {
        Write-Log "Copying enterprise configuration"
        Copy-Item -Path $ConfigSource -Destination "$InstallPath\config.yaml" -Force
        Write-Log "Enterprise configuration applied"
    } else {
        Write-Log "No enterprise configuration found at $ConfigSource" -Level "WARN"
    }
    
    # Create scheduled task for startup
    if ($CreateStartupTask) {
        $TaskName = "IdleSecurityReminder"
        $ExePath = "$InstallPath\idle-reminder.exe"
        
        # Remove existing task if it exists
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        
        # Create new task
        $Action = New-ScheduledTaskAction -Execute $ExePath
        $Trigger = New-ScheduledTaskTrigger -AtLogOn
        $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
        $Principal = New-ScheduledTaskPrincipal -GroupId "Users" -RunLevel Limited
        
        Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force
        Write-Log "Scheduled task created: $TaskName"
    }
    
    # Set appropriate permissions
    $Acl = Get-Acl $InstallPath
    $AccessRule = New-Object System.Security.AccessControl.FileSystemAccessRule("Users", "ReadAndExecute", "ContainerInherit,ObjectInherit", "None", "Allow")
    $Acl.SetAccessRule($AccessRule)
    Set-Acl -Path $InstallPath -AclObject $Acl
    Write-Log "Permissions set for Users group"
    
    # Create registry entry for uninstall information
    $UninstallKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\IdleSecurityReminder"
    if (-not (Test-Path $UninstallKey)) {
        New-Item -Path $UninstallKey -Force | Out-Null
    }
    
    Set-ItemProperty -Path $UninstallKey -Name "DisplayName" -Value "Idle Security Reminder"
    Set-ItemProperty -Path $UninstallKey -Name "DisplayVersion" -Value "1.0.0"
    Set-ItemProperty -Path $UninstallKey -Name "Publisher" -Value "Enterprise Security Team"
    Set-ItemProperty -Path $UninstallKey -Name "InstallLocation" -Value $InstallPath
    Set-ItemProperty -Path $UninstallKey -Name "UninstallString" -Value "powershell.exe -File `"$InstallPath\uninstall.ps1`""
    Set-ItemProperty -Path $UninstallKey -Name "NoModify" -Value 1 -Type DWord
    Set-ItemProperty -Path $UninstallKey -Name "NoRepair" -Value 1 -Type DWord
    
    # Create uninstall script
    $UninstallScript = @"
# Uninstall script for Idle Security Reminder
Write-Host "Uninstalling Idle Security Reminder..."

# Stop any running instances
Get-Process -Name "idle-reminder" -ErrorAction SilentlyContinue | Stop-Process -Force

# Remove scheduled task
Unregister-ScheduledTask -TaskName "IdleSecurityReminder" -Confirm:`$false -ErrorAction SilentlyContinue

# Remove installation directory
Remove-Item -Path "$InstallPath" -Recurse -Force -ErrorAction SilentlyContinue

# Remove registry entry
Remove-Item -Path "$UninstallKey" -Force -ErrorAction SilentlyContinue

Write-Host "Idle Security Reminder uninstalled successfully"
"@
    
    Set-Content -Path "$InstallPath\uninstall.ps1" -Value $UninstallScript
    Write-Log "Uninstall script created"
    
    Write-Log "Idle Security Reminder deployment completed successfully"
    
} catch {
    Write-Log "Deployment failed: $($_.Exception.Message)" -Level "ERROR"
    exit 1
}
