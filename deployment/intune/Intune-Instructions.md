# Microsoft Intune Deployment Instructions

## Overview
Deploy Idle Security Reminder as a Win32 app through Microsoft Intune for cloud-managed Windows devices.

## Prerequisites
- Microsoft Intune subscription
- Intune Administrator role
- Microsoft Win32 Content Prep Tool
- Target devices enrolled in Intune

## Step 1: Prepare Application Package

1. Create a folder with all application files:
   ```
   idle-reminder-package\
   ├── idle-reminder.exe
   ├── _internal\              (PyInstaller dependencies)
   ├── config.yaml
   ├── messages.txt
   ├── deploy-idle-reminder.ps1 (install script)
   └── detection.ps1           (detection script)
   ```

2. Download Microsoft Win32 Content Prep Tool from Microsoft
3. Create .intunewin package:
   ```cmd
   IntuneWinAppUtil.exe -c "C:\path\to\idle-reminder-package" -s "deploy-idle-reminder.ps1" -o "C:\output"
   ```

## Step 2: Create Win32 App in Intune

1. Sign in to Microsoft Endpoint Manager admin center
2. Go to **Apps** > **All apps** > **Add**
3. Select **Windows app (Win32)**
4. Upload the .intunewin file

### App Information
- **Name**: Idle Security Reminder
- **Description**: Desktop security awareness tool that displays reminders during idle time
- **Publisher**: Enterprise Security Team
- **Category**: Security

### Program Settings
- **Install command**: 
  ```
  powershell.exe -ExecutionPolicy Bypass -File "deploy-idle-reminder.ps1"
  ```
- **Uninstall command**: 
  ```
  powershell.exe -ExecutionPolicy Bypass -File "deploy-idle-reminder.ps1" -Uninstall
  ```
- **Install behavior**: System
- **Device restart behavior**: No specific action

### Requirements
- **Operating system architecture**: x64
- **Minimum operating system**: Windows 10 1809
- **Additional requirements**: PowerShell 5.0 or later

### Detection Rules
**Rule type**: Registry
- **Key path**: `HKEY_LOCAL_MACHINE\SOFTWARE\IdleSecurityReminder`
- **Value name**: Version
- **Detection method**: String comparison
- **Operator**: Equals
- **Value**: 1.0.0

### Dependencies
None required

### Supersedence
Configure if updating from previous version

## Step 3: Create Detection Script

Create `detection.ps1`:
```powershell
# Intune detection script for Idle Security Reminder
$RegPath = "HKLM:\SOFTWARE\IdleSecurityReminder"
$ExePath = "$env:ProgramFiles\Idle Security Reminder\idle-reminder.exe"

if ((Test-Path $RegPath) -and (Test-Path $ExePath)) {
    $Version = Get-ItemProperty -Path $RegPath -Name "Version" -ErrorAction SilentlyContinue
    if ($Version.Version -eq "1.0.0") {
        Write-Output "Idle Security Reminder 1.0.0 is installed"
        exit 0
    }
}
exit 1
```

## Step 4: Assign to Groups

1. Go to **Assignments** tab
2. Add groups:
   - **Required**: IT Security Group, All Workstations
   - **Available for enrolled devices**: Optional user groups
   - **Uninstall**: Groups that should not have the app

### Assignment Settings
- **Delivery optimization**: Download in background
- **End user experience**: Hide installation progress
- **Grace period**: 3 days

## Step 5: Configure Compliance Policy (Optional)

Create a compliance policy to ensure the app is installed:

1. Go to **Devices** > **Compliance policies** > **Create Policy**
2. Platform: Windows 10 and later
3. Add custom compliance setting:
   ```powershell
   # Check if Idle Security Reminder is running
   $Process = Get-Process -Name "idle-reminder" -ErrorAction SilentlyContinue
   if ($Process) { return $true } else { return $false }
   ```

## Step 6: Monitor Deployment

### Device Status
- Go to **Apps** > **All apps** > **Idle Security Reminder**
- Check **Device install status** and **User install status**

### Reporting
- **Installation status**: Success/Failed/In Progress
- **Error codes**: Common Win32 app error codes
- **Device compliance**: If compliance policy is configured

## Advanced Configuration

### Configuration Profiles

Deploy enterprise configuration via Configuration Profile:

1. **Settings Catalog** profile type
2. Add custom OMA-URI settings:
   ```
   OMA-URI: ./Device/Vendor/MSFT/Registry/HKLM/SOFTWARE/IdleSecurityReminder/IdleSeconds
   Data type: Integer
   Value: 120
   ```

### Conditional Access

Require app installation for device access:
1. Create Conditional Access policy
2. Add device compliance requirement
3. Include compliance policy that checks for app

### App Protection Policies

If needed, create app protection policy:
- Prevent data transfer from managed apps to Idle Security Reminder
- Configure based on organizational data protection requirements

## Troubleshooting

### Common Issues

1. **Installation fails with 0x87D1041C**
   - Check PowerShell execution policy
   - Verify script syntax

2. **Detection fails**
   - Verify registry key creation
   - Check file paths in detection script

3. **App not starting**
   - Check scheduled task creation
   - Verify user permissions

### Log Locations
- **Intune Management Extension**: `C:\ProgramData\Microsoft\IntuneManagementExtension\Logs\`
- **Application logs**: `C:\ProgramData\Microsoft\IntuneManagementExtension\Logs\idle-reminder-install.log`
- **Windows Event Log**: Applications and Services Logs > Microsoft > Windows > DeviceManagement-Enterprise-Diagnostics-Provider

### PowerShell Remediation Scripts

Create remediation script to fix common issues:
```powershell
# Detection script
$TaskExists = Get-ScheduledTask -TaskName "IdleSecurityReminder" -ErrorAction SilentlyContinue
if (-not $TaskExists) { exit 1 } else { exit 0 }

# Remediation script  
$ExePath = "$env:ProgramFiles\Idle Security Reminder\idle-reminder.exe"
if (Test-Path $ExePath) {
    $Action = New-ScheduledTaskAction -Execute $ExePath
    $Trigger = New-ScheduledTaskTrigger -AtLogOn
    $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries
    $Principal = New-ScheduledTaskPrincipal -GroupId "Users" -RunLevel Limited
    Register-ScheduledTask -TaskName "IdleSecurityReminder" -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal -Force
}
```

## Security Considerations

- App runs with user privileges only
- No sensitive data stored locally
- Network communication uses HTTPS only
- Complies with organizational security policies
- Regular security updates through Intune deployment
