#!/bin/bash
# Jamf Pro deployment script for Idle Security Reminder on macOS

# Script parameters (configured in Jamf Pro policy)
INSTALL_PATH="/Applications/Idle Security Reminder.app"
CONFIG_URL="${4:-}"  # Parameter 4: Enterprise config URL
ENABLE_AUTOSTART="${5:-true}"  # Parameter 5: Enable auto-start
LOG_PATH="/var/log/idle-reminder-install.log"

# Logging function
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_PATH"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_message "ERROR" "This script must be run as root"
    exit 1
fi

log_message "INFO" "Starting Idle Security Reminder deployment via Jamf"

# Function to install application
install_application() {
    log_message "INFO" "Installing Idle Security Reminder"
    
    # The app bundle should be included in the Jamf policy package
    # Copy from package location to Applications
    if [[ -d "/tmp/idle-reminder-package/Idle Security Reminder.app" ]]; then
        cp -R "/tmp/idle-reminder-package/Idle Security Reminder.app" "/Applications/"
        log_message "INFO" "Application copied to /Applications/"
    else
        log_message "ERROR" "Application bundle not found in package"
        exit 1
    fi
    
    # Set proper ownership and permissions
    chown -R root:admin "$INSTALL_PATH"
    chmod -R 755 "$INSTALL_PATH"
    log_message "INFO" "Permissions set for application"
    
    # Download enterprise configuration if URL provided
    if [[ -n "$CONFIG_URL" ]]; then
        log_message "INFO" "Downloading enterprise configuration from: $CONFIG_URL"
        if curl -f -s -o "$INSTALL_PATH/Contents/MacOS/config.yaml" "$CONFIG_URL"; then
            log_message "INFO" "Enterprise configuration downloaded successfully"
        else
            log_message "WARN" "Failed to download enterprise configuration"
        fi
    fi
}

# Function to configure auto-start
configure_autostart() {
    if [[ "$ENABLE_AUTOSTART" == "true" ]]; then
        log_message "INFO" "Configuring auto-start for all users"
        
        # Create LaunchAgent for all users
        LAUNCH_AGENT_PATH="/Library/LaunchAgents/com.company.idle-security-reminder.plist"
        
        cat > "$LAUNCH_AGENT_PATH" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.company.idle-security-reminder</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/Idle Security Reminder.app/Contents/MacOS/idle-reminder</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/var/log/idle-reminder.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/idle-reminder-error.log</string>
</dict>
</plist>
EOF
        
        # Set proper permissions for LaunchAgent
        chown root:wheel "$LAUNCH_AGENT_PATH"
        chmod 644 "$LAUNCH_AGENT_PATH"
        
        log_message "INFO" "LaunchAgent created at $LAUNCH_AGENT_PATH"
    fi
}

# Function to create user configurations
create_user_configs() {
    log_message "INFO" "Creating user configuration directories"
    
    # Create config directories for existing users
    for user_home in /Users/*; do
        if [[ -d "$user_home" && "$(basename "$user_home")" != "Shared" ]]; then
            username=$(basename "$user_home")
            config_dir="$user_home/.idle-reminder"
            
            # Skip system users
            if [[ "$username" =~ ^(_|daemon|nobody|root)$ ]]; then
                continue
            fi
            
            # Create config directory
            mkdir -p "$config_dir"
            
            # Copy default config if not exists
            if [[ ! -f "$config_dir/config.yaml" ]]; then
                cp "$INSTALL_PATH/Contents/MacOS/config.yaml" "$config_dir/" 2>/dev/null || true
            fi
            
            if [[ ! -f "$config_dir/messages.txt" ]]; then
                cp "$INSTALL_PATH/Contents/MacOS/messages.txt" "$config_dir/" 2>/dev/null || true
            fi
            
            # Set proper ownership
            chown -R "$username:staff" "$config_dir"
            
            log_message "INFO" "Configuration created for user: $username"
        fi
    done
}

# Function to register with system
register_application() {
    log_message "INFO" "Registering application with system"
    
    # Update Launch Services database
    /System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$INSTALL_PATH"
    
    # Create receipt for Jamf inventory
    RECEIPT_PATH="/private/var/db/receipts/com.company.idle-security-reminder.bom"
    RECEIPT_PLIST="/private/var/db/receipts/com.company.idle-security-reminder.plist"
    
    # Create basic receipt plist
    cat > "$RECEIPT_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>InstallDate</key>
    <date>$(date -u +%Y-%m-%dT%H:%M:%SZ)</date>
    <key>PackageFileName</key>
    <string>idle-security-reminder-1.0.0.pkg</string>
    <key>PackageGroups</key>
    <array>
        <string>com.company.idle-security-reminder</string>
    </array>
    <key>PackageIdentifier</key>
    <string>com.company.idle-security-reminder</string>
    <key>PackageVersion</key>
    <string>1.0.0</string>
</dict>
</plist>
EOF
    
    log_message "INFO" "Application registered with system"
}

# Main installation process
main() {
    log_message "INFO" "=== Idle Security Reminder Installation Started ==="
    
    # Check if already installed
    if [[ -d "$INSTALL_PATH" ]]; then
        log_message "INFO" "Application already exists, updating..."
        rm -rf "$INSTALL_PATH"
    fi
    
    # Install application
    install_application
    
    # Configure auto-start
    configure_autostart
    
    # Create user configurations
    create_user_configs
    
    # Register with system
    register_application
    
    # Update Jamf inventory
    jamf recon
    
    log_message "INFO" "=== Idle Security Reminder Installation Completed ==="
    
    # Start application for currently logged in user
    CURRENT_USER=$(stat -f%Su /dev/console)
    if [[ "$CURRENT_USER" != "root" && "$CURRENT_USER" != "_mbsetupuser" ]]; then
        log_message "INFO" "Starting application for current user: $CURRENT_USER"
        sudo -u "$CURRENT_USER" open "$INSTALL_PATH" &
    fi
    
    exit 0
}

# Error handling
trap 'log_message "ERROR" "Installation failed at line $LINENO"; exit 1' ERR

# Run main function
main "$@"
