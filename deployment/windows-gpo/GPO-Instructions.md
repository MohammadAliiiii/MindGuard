# Group Policy Deployment Instructions

## Overview
This guide explains how to deploy Idle Security Reminder using Windows Group Policy Objects (GPO) in an Active Directory environment.

## Prerequisites
- Active Directory Domain Services
- Group Policy Management Console (GPMC)
- Domain Administrator privileges
- Network share accessible by all target computers

## Step 1: Prepare Files

1. Create a network share (e.g., `\\domain.com\SYSVOL\domain.com\scripts\idle-reminder\`)
2. Copy the built application files to the share:
   ```
   \\domain.com\SYSVOL\domain.com\scripts\idle-reminder\
   ├── idle-reminder.exe
   ├── _internal\          (PyInstaller dependencies)
   ├── config.yaml
   └── messages.txt
   ```

3. Copy enterprise configuration:
   ```
   \\domain.com\SYSVOL\domain.com\Policies\idle-reminder\
   └── config.yaml         (Enterprise-specific settings)
   ```

## Step 2: Create Group Policy Object

1. Open Group Policy Management Console
2. Right-click on the target OU (e.g., "Workstations")
3. Select "Create a GPO in this domain, and Link it here"
4. Name: "Deploy Idle Security Reminder"

## Step 3: Configure Computer Startup Script

1. Edit the new GPO
2. Navigate to: `Computer Configuration > Policies > Windows Settings > Scripts (Startup/Shutdown)`
3. Double-click "Startup"
4. Click "Add..." and configure:
   - **Script Name**: `powershell.exe`
   - **Script Parameters**: 
     ```
     -ExecutionPolicy Bypass -File "\\domain.com\SYSVOL\domain.com\scripts\idle-reminder\deploy-idle-reminder.ps1" -SourcePath "\\domain.com\SYSVOL\domain.com\scripts\idle-reminder" -ConfigSource "\\domain.com\SYSVOL\domain.com\Policies\idle-reminder\config.yaml"
     ```

## Step 4: Configure Security Filtering (Optional)

1. In the GPO, go to the "Scope" tab
2. Under "Security Filtering", remove "Authenticated Users"
3. Add specific security groups (e.g., "Workstation Users")

## Step 5: Configure WMI Filtering (Optional)

Create a WMI filter to target specific OS versions:
```wmi
SELECT * FROM Win32_OperatingSystem WHERE Version LIKE "10.%" OR Version LIKE "11.%"
```

## Step 6: Test Deployment

1. Link the GPO to a test OU with a few computers
2. Run `gpupdate /force` on test machines
3. Restart test machines or wait for next startup
4. Verify installation in `C:\Program Files\Idle Security Reminder\`

## Step 7: Monitor Deployment

Check deployment status using:
```powershell
# On target machines
Get-ScheduledTask -TaskName "IdleSecurityReminder"
Get-Process -Name "idle-reminder" -ErrorAction SilentlyContinue
Test-Path "C:\Program Files\Idle Security Reminder\idle-reminder.exe"
```

## Troubleshooting

### Common Issues

1. **Script execution policy**: Ensure PowerShell execution policy allows scripts
2. **Network access**: Verify computers can access the SYSVOL share
3. **Permissions**: Check that computer accounts have read access to script files
4. **Antivirus**: Whitelist the application if blocked by antivirus

### Log Files

Check deployment logs at:
- `%TEMP%\idle-reminder-install.log` (on target machines)
- Event Viewer > Windows Logs > System (GPO processing events)

## Advanced Configuration

### Registry-based Configuration

Deploy additional settings via GPO registry preferences:
```
HKLM\SOFTWARE\IdleSecurityReminder\
├── IdleSeconds (DWORD): 120
├── MessagesFile (String): C:\Program Files\Idle Security Reminder\messages.txt
└── LogLevel (String): INFO
```

### Software Restriction Policies

If using Software Restriction Policies, add exception for:
`C:\Program Files\Idle Security Reminder\idle-reminder.exe`

### Windows Defender Application Control

Create WDAC policy exception if needed:
```xml
<Allow ID="ID_ALLOW_IDLE_REMINDER" FriendlyName="Idle Security Reminder" 
       FileName="idle-reminder.exe" 
       ProductName="Idle Security Reminder" />
```

## Removal

To remove the application:
1. Modify the startup script to include `-Uninstall` parameter
2. Or create a separate GPO with an uninstall script
3. The uninstall script is automatically created at: `C:\Program Files\Idle Security Reminder\uninstall.ps1`
