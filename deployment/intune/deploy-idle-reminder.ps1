# Microsoft Intune deployment script for Idle Security Reminder
# This script is designed to be packaged as a Win32 app in Intune

param(
    [string]$InstallPath = "$env:ProgramFiles\Idle Security Reminder",
    [string]$ConfigUrl = "",  # URL to download enterprise config
    [switch]$Uninstall = $false
)

# Logging function
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    Write-Host $logMessage
    
    # Log to Intune-friendly location
    $logPath = "$env:ProgramData\Microsoft\IntuneManagementExtension\Logs\idle-reminder-install.log"
    $logDir = Split-Path $logPath -Parent
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    Add-Content -Path $logPath -Value $logMessage
}

function Install-IdleReminder {
    try {
        Write-Log "Starting Idle Security Reminder installation via Intune"
        
        # Create installation directory
        if (-not (Test-Path $InstallPath)) {
            New-Item -ItemType Directory -Path $InstallPath -Force | Out-Null
            Write-Log "Created installation directory: $InstallPath"
        }
        
        # Copy application files from current directory (Intune package)
        $sourceFiles = Get-ChildItem -Path "." -Exclude "*.ps1", "*.xml", "*.json"
        foreach ($file in $sourceFiles) {
            Copy-Item -Path $file.FullName -Destination $InstallPath -Recurse -Force
            Write-Log "Copied: $($file.Name)"
        }
        
        # Download enterprise configuration if URL provided
        if ($ConfigUrl) {
            try {
                Write-Log "Downloading enterprise configuration from: $ConfigUrl"
                $webClient = New-Object System.Net.WebClient
                $webClient.DownloadFile($ConfigUrl, "$InstallPath\config.yaml")
                Write-Log "Enterprise configuration downloaded successfully"
            } catch {
                Write-Log "Failed to download enterprise config: $($_.Exception.Message)" -Level "WARN"
            }
        }
        
        # Create scheduled task for current user context
        $TaskName = "IdleSecurityReminder"
        $ExePath = "$InstallPath\idle-reminder.exe"
        
        # Remove existing task if it exists
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
        
        # Create new task that runs for all users
        $Action = New-ScheduledTaskAction -Execute $ExePath
        $Trigger = New-ScheduledTaskTrigger -AtLogOn
        $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -MultipleInstances IgnoreNew
        $Principal = New-ScheduledTaskPrincipal -GroupId "Users" -RunLevel Limited
        
        Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force
        Write-Log "Scheduled task created: $TaskName"
        
        # Set appropriate permissions
        $Acl = Get-Acl $InstallPath
        $AccessRule = New-Object System.Security.AccessControl.FileSystemAccessRule("Users", "ReadAndExecute", "ContainerInherit,ObjectInherit", "None", "Allow")
        $Acl.SetAccessRule($AccessRule)
        Set-Acl -Path $InstallPath -AclObject $Acl
        Write-Log "Permissions configured for Users group"
        
        # Create registry entries for detection and uninstall
        $UninstallKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\IdleSecurityReminder"
        if (-not (Test-Path $UninstallKey)) {
            New-Item -Path $UninstallKey -Force | Out-Null
        }
        
        Set-ItemProperty -Path $UninstallKey -Name "DisplayName" -Value "Idle Security Reminder"
        Set-ItemProperty -Path $UninstallKey -Name "DisplayVersion" -Value "1.0.0"
        Set-ItemProperty -Path $UninstallKey -Name "Publisher" -Value "Enterprise Security Team"
        Set-ItemProperty -Path $UninstallKey -Name "InstallDate" -Value (Get-Date -Format "yyyyMMdd")
        Set-ItemProperty -Path $UninstallKey -Name "InstallLocation" -Value $InstallPath
        Set-ItemProperty -Path $UninstallKey -Name "UninstallString" -Value "powershell.exe -ExecutionPolicy Bypass -File `"$InstallPath\uninstall.ps1`""
        Set-ItemProperty -Path $UninstallKey -Name "QuietUninstallString" -Value "powershell.exe -ExecutionPolicy Bypass -File `"$InstallPath\uninstall.ps1`" -Silent"
        Set-ItemProperty -Path $UninstallKey -Name "NoModify" -Value 1 -Type DWord
        Set-ItemProperty -Path $UninstallKey -Name "NoRepair" -Value 1 -Type DWord
        
        # Create Intune detection registry key
        $DetectionKey = "HKLM:\SOFTWARE\IdleSecurityReminder"
        if (-not (Test-Path $DetectionKey)) {
            New-Item -Path $DetectionKey -Force | Out-Null
        }
        Set-ItemProperty -Path $DetectionKey -Name "Version" -Value "1.0.0"
        Set-ItemProperty -Path $DetectionKey -Name "InstallDate" -Value (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        
        # Create uninstall script
        $UninstallScript = @"
param([switch]`$Silent = `$false)

if (-not `$Silent) {
    Write-Host "Uninstalling Idle Security Reminder..."
}

try {
    # Stop any running instances
    Get-Process -Name "idle-reminder" -ErrorAction SilentlyContinue | Stop-Process -Force
    
    # Remove scheduled task
    Unregister-ScheduledTask -TaskName "IdleSecurityReminder" -Confirm:`$false -ErrorAction SilentlyContinue
    
    # Remove installation directory
    if (Test-Path "$InstallPath") {
        Remove-Item -Path "$InstallPath" -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    # Remove registry entries
    Remove-Item -Path "$UninstallKey" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "$DetectionKey" -Force -ErrorAction SilentlyContinue
    
    if (-not `$Silent) {
        Write-Host "Idle Security Reminder uninstalled successfully"
    }
    exit 0
} catch {
    if (-not `$Silent) {
        Write-Host "Uninstall failed: `$(`$_.Exception.Message)"
    }
    exit 1
}
"@
        
        Set-Content -Path "$InstallPath\uninstall.ps1" -Value $UninstallScript
        Write-Log "Uninstall script created"
        
        Write-Log "Idle Security Reminder installation completed successfully"
        exit 0
        
    } catch {
        Write-Log "Installation failed: $($_.Exception.Message)" -Level "ERROR"
        exit 1
    }
}

function Uninstall-IdleReminder {
    try {
        Write-Log "Starting Idle Security Reminder uninstallation"
        
        # Stop any running instances
        Get-Process -Name "idle-reminder" -ErrorAction SilentlyContinue | Stop-Process -Force
        Write-Log "Stopped running instances"
        
        # Remove scheduled task
        Unregister-ScheduledTask -TaskName "IdleSecurityReminder" -Confirm:$false -ErrorAction SilentlyContinue
        Write-Log "Removed scheduled task"
        
        # Remove installation directory
        if (Test-Path $InstallPath) {
            Remove-Item -Path $InstallPath -Recurse -Force
            Write-Log "Removed installation directory"
        }
        
        # Remove registry entries
        $UninstallKey = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\IdleSecurityReminder"
        $DetectionKey = "HKLM:\SOFTWARE\IdleSecurityReminder"
        
        Remove-Item -Path $UninstallKey -Force -ErrorAction SilentlyContinue
        Remove-Item -Path $DetectionKey -Force -ErrorAction SilentlyContinue
        Write-Log "Removed registry entries"
        
        Write-Log "Idle Security Reminder uninstalled successfully"
        exit 0
        
    } catch {
        Write-Log "Uninstallation failed: $($_.Exception.Message)" -Level "ERROR"
        exit 1
    }
}

# Main execution
if ($Uninstall) {
    Uninstall-IdleReminder
} else {
    Install-IdleReminder
}
