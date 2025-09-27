#!/bin/bash
# Linux deployment script for Idle Security Reminder
# Supports multiple Linux distributions (Ubuntu, RHEL, SUSE, etc.)

set -e

# Configuration
INSTALL_DIR="/opt/idle-reminder"
BIN_DIR="/usr/local/bin"
CONFIG_DIR="/etc/idle-reminder"
SYSTEMD_DIR="/etc/systemd/user"
DESKTOP_DIR="/usr/share/applications"
LOG_FILE="/var/log/idle-reminder-install.log"

# Script parameters
PACKAGE_URL="${1:-}"
CONFIG_URL="${2:-}"
ENABLE_AUTOSTART="${3:-true}"

# Logging function
log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_message "ERROR" "This script must be run as root"
    exit 1
fi

# Detect Linux distribution
detect_distro() {
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        DISTRO="$ID"
        VERSION="$VERSION_ID"
    elif [[ -f /etc/redhat-release ]]; then
        DISTRO="rhel"
    elif [[ -f /etc/debian_version ]]; then
        DISTRO="debian"
    else
        DISTRO="unknown"
    fi
    
    log_message "INFO" "Detected distribution: $DISTRO $VERSION"
}

# Install dependencies
install_dependencies() {
    log_message "INFO" "Installing dependencies for $DISTRO"
    
    case "$DISTRO" in
        ubuntu|debian)
            apt-get update
            apt-get install -y python3 python3-tk python3-pip curl wget
            ;;
        rhel|centos|fedora)
            if command -v dnf &> /dev/null; then
                dnf install -y python3 python3-tkinter python3-pip curl wget
            else
                yum install -y python3 python3-tkinter python3-pip curl wget
            fi
            ;;
        suse|opensuse*)
            zypper install -y python3 python3-tk python3-pip curl wget
            ;;
        arch)
            pacman -S --noconfirm python python-pip tk curl wget
            ;;
        *)
            log_message "WARN" "Unknown distribution, attempting generic installation"
            ;;
    esac
}

# Download and extract application
install_application() {
    log_message "INFO" "Installing Idle Security Reminder"
    
    # Create directories
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$SYSTEMD_DIR"
    
    # Download package if URL provided
    if [[ -n "$PACKAGE_URL" ]]; then
        log_message "INFO" "Downloading package from: $PACKAGE_URL"
        
        if [[ "$PACKAGE_URL" == *.tar.gz ]]; then
            wget -O "/tmp/idle-reminder.tar.gz" "$PACKAGE_URL"
            tar -xzf "/tmp/idle-reminder.tar.gz" -C "$INSTALL_DIR" --strip-components=1
        elif [[ "$PACKAGE_URL" == *.deb ]]; then
            wget -O "/tmp/idle-reminder.deb" "$PACKAGE_URL"
            dpkg -i "/tmp/idle-reminder.deb" || apt-get install -f -y
            return 0
        elif [[ "$PACKAGE_URL" == *.rpm ]]; then
            wget -O "/tmp/idle-reminder.rpm" "$PACKAGE_URL"
            if command -v dnf &> /dev/null; then
                dnf install -y "/tmp/idle-reminder.rpm"
            else
                yum install -y "/tmp/idle-reminder.rpm"
            fi
            return 0
        else
            log_message "ERROR" "Unsupported package format"
            exit 1
        fi
    else
        # Copy from local package directory
        if [[ -d "./idle-reminder" ]]; then
            cp -r ./idle-reminder/* "$INSTALL_DIR/"
        else
            log_message "ERROR" "No package found to install"
            exit 1
        fi
    fi
    
    # Set permissions
    chmod +x "$INSTALL_DIR/idle-reminder"
    chown -R root:root "$INSTALL_DIR"
    
    # Create symlink
    ln -sf "$INSTALL_DIR/idle-reminder" "$BIN_DIR/idle-reminder"
    
    log_message "INFO" "Application installed to $INSTALL_DIR"
}

# Configure application
configure_application() {
    log_message "INFO" "Configuring application"
    
    # Copy default configuration
    if [[ -f "$INSTALL_DIR/config.yaml" ]]; then
        cp "$INSTALL_DIR/config.yaml" "$CONFIG_DIR/"
    fi
    
    if [[ -f "$INSTALL_DIR/messages.txt" ]]; then
        cp "$INSTALL_DIR/messages.txt" "$CONFIG_DIR/"
    fi
    
    # Download enterprise configuration if URL provided
    if [[ -n "$CONFIG_URL" ]]; then
        log_message "INFO" "Downloading enterprise configuration from: $CONFIG_URL"
        if curl -f -s -o "$CONFIG_DIR/config.yaml" "$CONFIG_URL"; then
            log_message "INFO" "Enterprise configuration downloaded successfully"
        else
            log_message "WARN" "Failed to download enterprise configuration"
        fi
    fi
    
    # Set configuration permissions
    chmod 644 "$CONFIG_DIR"/*
    chown -R root:root "$CONFIG_DIR"
}

# Create systemd user service
create_systemd_service() {
    if [[ "$ENABLE_AUTOSTART" == "true" ]]; then
        log_message "INFO" "Creating systemd user service"
        
        cat > "$SYSTEMD_DIR/idle-reminder.service" << EOF
[Unit]
Description=Idle Security Reminder
After=graphical-session.target

[Service]
Type=simple
ExecStart=$INSTALL_DIR/idle-reminder --config $CONFIG_DIR/config.yaml
Restart=on-failure
RestartSec=5
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
EOF
        
        chmod 644 "$SYSTEMD_DIR/idle-reminder.service"
        
        # Enable for all users
        systemctl --global enable idle-reminder.service
        
        log_message "INFO" "Systemd service created and enabled"
    fi
}

# Create desktop entry
create_desktop_entry() {
    log_message "INFO" "Creating desktop entry"
    
    cat > "$DESKTOP_DIR/idle-reminder.desktop" << EOF
[Desktop Entry]
Type=Application
Name=Idle Security Reminder
Comment=Desktop security awareness tool
Exec=$INSTALL_DIR/idle-reminder
Icon=security-high
Categories=Security;Utility;
StartupNotify=false
NoDisplay=true
X-GNOME-Autostart-enabled=true
EOF
    
    chmod 644 "$DESKTOP_DIR/idle-reminder.desktop"
    
    # Update desktop database
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$DESKTOP_DIR"
    fi
    
    log_message "INFO" "Desktop entry created"
}

# Configure for different desktop environments
configure_autostart() {
    if [[ "$ENABLE_AUTOSTART" == "true" ]]; then
        log_message "INFO" "Configuring autostart for desktop environments"
        
        # Create autostart directory structure
        mkdir -p /etc/xdg/autostart
        
        # Copy desktop file to autostart
        cp "$DESKTOP_DIR/idle-reminder.desktop" /etc/xdg/autostart/
        
        # For user-specific autostart, create template
        mkdir -p /etc/skel/.config/autostart
        cp "$DESKTOP_DIR/idle-reminder.desktop" /etc/skel/.config/autostart/
        
        # Configure for existing users
        for user_home in /home/*; do
            if [[ -d "$user_home" ]]; then
                username=$(basename "$user_home")
                autostart_dir="$user_home/.config/autostart"
                
                mkdir -p "$autostart_dir"
                cp "$DESKTOP_DIR/idle-reminder.desktop" "$autostart_dir/"
                chown -R "$username:$username" "$autostart_dir"
                
                log_message "INFO" "Autostart configured for user: $username"
            fi
        done
    fi
}

# Create uninstall script
create_uninstall_script() {
    log_message "INFO" "Creating uninstall script"
    
    cat > "$INSTALL_DIR/uninstall.sh" << 'EOF'
#!/bin/bash
# Uninstall script for Idle Security Reminder

echo "Uninstalling Idle Security Reminder..."

# Stop any running instances
pkill -f idle-reminder || true

# Disable and remove systemd service
systemctl --global disable idle-reminder.service 2>/dev/null || true
rm -f /etc/systemd/user/idle-reminder.service

# Remove autostart entries
rm -f /etc/xdg/autostart/idle-reminder.desktop
rm -f /etc/skel/.config/autostart/idle-reminder.desktop

# Remove from user autostart directories
for user_home in /home/*; do
    if [[ -d "$user_home/.config/autostart" ]]; then
        rm -f "$user_home/.config/autostart/idle-reminder.desktop"
    fi
done

# Remove application files
rm -rf /opt/idle-reminder
rm -f /usr/local/bin/idle-reminder
rm -f /usr/share/applications/idle-reminder.desktop

# Remove configuration (optional - comment out to preserve)
# rm -rf /etc/idle-reminder

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications
fi

echo "Idle Security Reminder uninstalled successfully"
EOF
    
    chmod +x "$INSTALL_DIR/uninstall.sh"
    log_message "INFO" "Uninstall script created at $INSTALL_DIR/uninstall.sh"
}

# Main installation function
main() {
    log_message "INFO" "=== Idle Security Reminder Installation Started ==="
    
    # Detect distribution
    detect_distro
    
    # Install dependencies
    install_dependencies
    
    # Install application
    install_application
    
    # Configure application
    configure_application
    
    # Create systemd service
    create_systemd_service
    
    # Create desktop entry
    create_desktop_entry
    
    # Configure autostart
    configure_autostart
    
    # Create uninstall script
    create_uninstall_script
    
    log_message "INFO" "=== Idle Security Reminder Installation Completed ==="
    
    # Start service for current user if in graphical session
    if [[ -n "$DISPLAY" && -n "$USER" && "$USER" != "root" ]]; then
        log_message "INFO" "Starting service for current user"
        sudo -u "$USER" systemctl --user start idle-reminder.service 2>/dev/null || true
    fi
    
    echo ""
    echo "Installation completed successfully!"
    echo "The application will start automatically on next login."
    echo "To start manually: idle-reminder"
    echo "To uninstall: sudo $INSTALL_DIR/uninstall.sh"
    echo ""
}

# Error handling
trap 'log_message "ERROR" "Installation failed at line $LINENO"; exit 1' ERR

# Run main function
main "$@"
