# Jamf Pro Deployment Instructions

## Overview
Deploy Idle Security Reminder on macOS devices managed by Jamf Pro using packages and policies.

## Prerequisites
- Jamf Pro server access
- macOS devices enrolled in Jamf Pro
- Composer or Packages app for creating PKG files
- Administrator privileges in Jamf Pro

## Step 1: Create Installation Package

### Using Jamf Composer
1. Open Jamf Composer
2. Create new package from application bundle
3. Add `Idle Security Reminder.app` to `/Applications/`
4. Add configuration files to appropriate locations
5. Set package identifier: `com.company.idle-security-reminder`
6. Set version: `1.0.0`
7. Build and save PKG file

### Package Contents
```
/Applications/Idle Security Reminder.app/
/Library/LaunchAgents/com.company.idle-security-reminder.plist
```

## Step 2: Upload Package to Jamf Pro

1. Log in to Jamf Pro web interface
2. Go to **Settings** > **Computer Management** > **Packages**
3. Click **New**
4. Upload the PKG file
5. Configure package settings:
   - **Display Name**: Idle Security Reminder
   - **Category**: Security
   - **Priority**: 10
   - **Fill User Template**: Enabled
   - **Fill Existing Users**: Enabled

## Step 3: Create Smart Group (Optional)

Create a smart group to target specific devices:

1. Go to **Computers** > **Smart Computer Groups**
2. Click **New**
3. Configure criteria:
   - **Operating System Version**: greater than or equal to 10.15
   - **Computer Group**: not member of "Idle Reminder Excluded"
   - **Last Check-in**: less than 7 days ago

## Step 4: Create Policy

1. Go to **Computers** > **Policies**
2. Click **New**
3. Configure **General** settings:
   - **Display Name**: Deploy Idle Security Reminder
   - **Category**: Security
   - **Trigger**: Startup, Login, Recurring Check-in
   - **Execution Frequency**: Once per computer

### Packages Tab
- Add the Idle Security Reminder package
- **Action**: Install

### Scripts Tab
Add the deployment script:
- **Script**: Upload `deploy-idle-reminder.sh`
- **Priority**: After
- **Parameter 4**: Enterprise config URL (optional)
- **Parameter 5**: Enable auto-start (true/false)

### Scope Tab
- **Target Computers**: All Computers or specific Smart Group
- **Exclusions**: Add computers that should not receive the app

### User Interaction Tab
- **Start message**: "Installing security software..."
- **Complete message**: "Idle Security Reminder installed successfully"

## Step 5: Create Configuration Profile

Deploy enterprise settings via Configuration Profile:

1. Go to **Computers** > **Configuration Profiles**
2. Click **New**
3. Configure **General** settings:
   - **Name**: Idle Security Reminder Configuration
   - **Category**: Security

### Custom Settings Payload
Add custom plist for application settings:
```xml
<dict>
    <key>idle_seconds</key>
    <integer>120</integer>
    <key>messages_file</key>
    <string>~/.idle-reminder/messages.txt</string>
    <key>theme</key>
    <string>high_contrast</string>
    <key>log_level</key>
    <string>INFO</string>
    <key>show_report_button</key>
    <true/>
    <key>report_endpoint</key>
    <string>https://security.company.com/report</string>
</dict>
```

## Step 6: Monitor Deployment

### Policy Logs
- Go to **Computers** > **Policies** > **Deploy Idle Security Reminder**
- Check **Logs** tab for deployment status

### Inventory Reports
Create Extension Attribute to track installation:
```bash
#!/bin/bash
if [ -d "/Applications/Idle Security Reminder.app" ]; then
    echo "Installed"
else
    echo "Not Installed"
fi
```

### Smart Groups for Monitoring
- **Idle Reminder Installed**: Extension Attribute "Idle Reminder Status" is "Installed"
- **Idle Reminder Missing**: Extension Attribute "Idle Reminder Status" is "Not Installed"

## Advanced Configuration

### Restricted Software
If using Restricted Software records:
1. Go to **Computers** > **Restricted Software**
2. Add exception for Idle Security Reminder
3. **Process Name**: idle-reminder
4. **Action**: Allow

### Self Service Deployment
Make available in Self Service:
1. Edit the policy
2. Check **Make Available in Self Service**
3. Configure Self Service settings:
   - **Button Name**: Install Security Reminder
   - **Description**: Install desktop security awareness tool
   - **Category**: Security

### Maintenance Policy
Create policy for updates:
1. **Trigger**: Recurring Check-in
2. **Frequency**: Once per week
3. **Script**: Check for updates and reinstall if needed

## Troubleshooting

### Common Issues

1. **Permission Denied**
   - Check package ownership and permissions
   - Verify Jamf binary has proper privileges

2. **Application Won't Start**
   - Check LaunchAgent permissions
   - Verify application signature and Gatekeeper settings

3. **Configuration Not Applied**
   - Check Configuration Profile deployment
   - Verify plist format and syntax

### Log Locations
- **Installation logs**: `/var/log/idle-reminder-install.log`
- **Application logs**: `/var/log/idle-reminder.log`
- **Jamf logs**: `/var/log/jamf.log`

### Diagnostic Commands
```bash
# Check installation status
ls -la "/Applications/Idle Security Reminder.app"

# Check LaunchAgent
launchctl list | grep idle-security-reminder

# Check configuration
defaults read com.company.idle-security-reminder

# Test application launch
sudo -u username open "/Applications/Idle Security Reminder.app"
```

## Uninstallation

### Uninstall Script
```bash
#!/bin/bash
# Remove application
rm -rf "/Applications/Idle Security Reminder.app"

# Remove LaunchAgent
rm -f "/Library/LaunchAgents/com.company.idle-security-reminder.plist"

# Remove user configurations
for user_home in /Users/*; do
    if [[ -d "$user_home/.idle-reminder" ]]; then
        rm -rf "$user_home/.idle-reminder"
    fi
done

# Update inventory
jamf recon
```

### Uninstall Policy
1. Create new policy: "Uninstall Idle Security Reminder"
2. Add uninstall script
3. Scope to devices that need removal
4. Set appropriate trigger

## Security Considerations

- Application runs with user privileges only
- LaunchAgent configured for user context
- Configuration files protected with appropriate permissions
- Network communication validated and encrypted
- Regular security updates through policy management
