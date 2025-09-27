#!/bin/bash
# macOS build script for Idle Security Reminder

set -e

echo "Building Idle Security Reminder for macOS..."

# Create build directory
mkdir -p build
mkdir -p dist

# Create spec file for PyInstaller
cat > idle_reminder.spec << 'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/idle_reminder/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.yaml', '.'),
        ('messages.txt', '.'),
        ('src/idle_reminder', 'idle_reminder'),
    ],
    hiddenimports=[
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='idle-reminder',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='idle-reminder',
)

app = BUNDLE(
    coll,
    name='Idle Security Reminder.app',
    icon=None,
    bundle_identifier='com.company.idle-security-reminder',
    version='1.0.0',
    info_plist={
        'CFBundleName': 'Idle Security Reminder',
        'CFBundleDisplayName': 'Idle Security Reminder',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': 'True',
        'LSUIElement': '1',  # Hide from dock by default
        'NSAppleEventsUsageDescription': 'This app needs to monitor system idle time for security reminders.',
        'NSSystemAdministrationUsageDescription': 'This app needs to display security overlays.',
    },
)
EOF

# Build with PyInstaller
echo "Running PyInstaller..."
pyinstaller --clean idle_reminder.spec

# Create DMG structure
echo "Creating DMG structure..."
mkdir -p dist/dmg
cp -R "dist/Idle Security Reminder.app" dist/dmg/
cp README.md dist/dmg/
cp config.yaml dist/dmg/
cp messages.txt dist/dmg/

# Create Applications symlink for DMG
ln -sf /Applications dist/dmg/Applications

# Create DMG background and setup
mkdir -p dist/dmg/.background
cat > dist/dmg/.DS_Store_template << 'EOF'
# This would contain DMG window settings
# In practice, this is a binary file created by Disk Utility
EOF

# Create create-dmg script
cat > scripts/create_dmg.sh << 'EOF'
#!/bin/bash
# Create DMG for macOS distribution

DMG_NAME="idle-reminder-macos"
VOLUME_NAME="Idle Security Reminder"
SOURCE_DIR="dist/dmg"
DMG_PATH="dist/${DMG_NAME}.dmg"

# Remove existing DMG
rm -f "${DMG_PATH}"

# Create temporary DMG
hdiutil create -srcfolder "${SOURCE_DIR}" -volname "${VOLUME_NAME}" -fs HFS+ \
    -fsargs "-c c=64,a=16,e=16" -format UDRW -size 100m "dist/temp.dmg"

# Mount the temporary DMG
DEVICE=$(hdiutil attach -readwrite -noverify -noautoopen "dist/temp.dmg" | \
    egrep '^/dev/' | sed 1q | awk '{print $1}')

# Set DMG window properties
echo '
   tell application "Finder"
     tell disk "'${VOLUME_NAME}'"
           open
           set current view of container window to icon view
           set toolbar visible of container window to false
           set statusbar visible of container window to false
           set the bounds of container window to {400, 100, 900, 400}
           set theViewOptions to the icon view options of container window
           set arrangement of theViewOptions to not arranged
           set icon size of theViewOptions to 72
           set position of item "Idle Security Reminder.app" of container window to {150, 200}
           set position of item "Applications" of container window to {350, 200}
           close
           open
           update without registering applications
           delay 5
     end tell
   end tell
' | osascript

# Unmount the DMG
hdiutil detach ${DEVICE}

# Convert to final DMG
hdiutil convert "dist/temp.dmg" -format UDZO -imagekey zlib-level=9 -o "${DMG_PATH}"

# Clean up
rm -f "dist/temp.dmg"

echo "DMG created: ${DMG_PATH}"
EOF

chmod +x scripts/create_dmg.sh

# Create PKG installer structure
echo "Creating PKG installer structure..."
mkdir -p dist/pkg/root/Applications
mkdir -p dist/pkg/scripts
mkdir -p dist/pkg/resources

# Copy app to PKG structure
cp -R "dist/Idle Security Reminder.app" "dist/pkg/root/Applications/"

# Create postinstall script for PKG
cat > dist/pkg/scripts/postinstall << 'EOF'
#!/bin/bash

# Set proper permissions
chmod -R 755 "/Applications/Idle Security Reminder.app"

# Create config directory in user's home
USER_HOME=$(eval echo ~$USER)
CONFIG_DIR="$USER_HOME/.idle-reminder"
mkdir -p "$CONFIG_DIR"

# Copy default config if not exists
if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    cp "/Applications/Idle Security Reminder.app/Contents/MacOS/config.yaml" "$CONFIG_DIR/"
fi

if [ ! -f "$CONFIG_DIR/messages.txt" ]; then
    cp "/Applications/Idle Security Reminder.app/Contents/MacOS/messages.txt" "$CONFIG_DIR/"
fi

echo "Idle Security Reminder installed successfully"
exit 0
EOF

chmod +x dist/pkg/scripts/postinstall

# Create component property list
cat > dist/pkg/component.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>BundleHasStrictIdentifier</key>
    <true/>
    <key>BundleIsRelocatable</key>
    <false/>
    <key>BundleIsVersionChecked</key>
    <true/>
    <key>BundleOverwriteAction</key>
    <string>upgrade</string>
    <key>RootRelativeBundlePath</key>
    <string>Idle Security Reminder.app</string>
</dict>
</plist>
EOF

# Create distribution XML
cat > dist/pkg/distribution.xml << 'EOF'
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>Idle Security Reminder</title>
    <organization>com.company.idle-security-reminder</organization>
    <domains enable_localSystem="true"/>
    <options customize="never" require-scripts="false"/>
    <choices-outline>
        <line choice="default">
            <line choice="com.company.idle-security-reminder.app"/>
        </line>
    </choices-outline>
    <choice id="default"/>
    <choice id="com.company.idle-security-reminder.app" visible="false">
        <pkg-ref id="com.company.idle-security-reminder.app"/>
    </choice>
    <pkg-ref id="com.company.idle-security-reminder.app" version="1.0.0" auth="root">idle-reminder-component.pkg</pkg-ref>
</installer-gui-script>
EOF

# Build component package
if command -v pkgbuild &> /dev/null; then
    echo "Building component package..."
    pkgbuild --root dist/pkg/root \
             --component-plist dist/pkg/component.plist \
             --scripts dist/pkg/scripts \
             --identifier com.company.idle-security-reminder.app \
             --version 1.0.0 \
             dist/idle-reminder-component.pkg

    # Build product package
    echo "Building product package..."
    productbuild --distribution dist/pkg/distribution.xml \
                 --package-path dist \
                 --resources dist/pkg/resources \
                 dist/idle-reminder-installer.pkg
else
    echo "pkgbuild not found, PKG installer structure created in dist/pkg/"
fi

# Create Jamf deployment script
cat > dist/deploy-jamf.sh << 'EOF'
#!/bin/bash
# Jamf deployment script for Idle Security Reminder

# This script should be uploaded to Jamf Pro as a policy script

# Variables
APP_NAME="Idle Security Reminder.app"
INSTALL_PATH="/Applications/$APP_NAME"
PKG_URL="https://your-server.com/packages/idle-reminder-installer.pkg"
CONFIG_URL="https://your-server.com/config/idle-reminder-config.yaml"

# Download and install PKG
echo "Downloading Idle Security Reminder..."
curl -L "$PKG_URL" -o "/tmp/idle-reminder-installer.pkg"

echo "Installing Idle Security Reminder..."
installer -pkg "/tmp/idle-reminder-installer.pkg" -target /

# Download enterprise config if available
if curl --output /dev/null --silent --head --fail "$CONFIG_URL"; then
    echo "Downloading enterprise configuration..."
    curl -L "$CONFIG_URL" -o "/tmp/config.yaml"
    
    # Deploy config to all user directories
    for user_dir in /Users/*; do
        if [ -d "$user_dir" ] && [ "$(basename "$user_dir")" != "Shared" ]; then
            user_config_dir="$user_dir/.idle-reminder"
            mkdir -p "$user_config_dir"
            cp "/tmp/config.yaml" "$user_config_dir/"
            chown -R "$(basename "$user_dir")" "$user_config_dir"
        fi
    done
fi

# Set up LaunchAgent for auto-start (optional)
LAUNCH_AGENT_PLIST="/Library/LaunchAgents/com.company.idle-security-reminder.plist"
cat > "$LAUNCH_AGENT_PLIST" << 'PLIST_EOF'
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
</dict>
</plist>
PLIST_EOF

chmod 644 "$LAUNCH_AGENT_PLIST"

# Clean up
rm -f "/tmp/idle-reminder-installer.pkg"
rm -f "/tmp/config.yaml"

echo "Idle Security Reminder deployment completed"
EOF

chmod +x dist/deploy-jamf.sh

# Create signing and notarization instructions
cat > dist/SIGNING_INSTRUCTIONS.md << 'EOF'
# macOS Code Signing and Notarization

## Prerequisites
1. Apple Developer Account
2. Developer ID Application certificate installed in Keychain
3. App-specific password for notarization

## Code Signing
```bash
# Sign the application
codesign --force --options runtime --deep --sign "Developer ID Application: Your Name (TEAM_ID)" "dist/Idle Security Reminder.app"

# Verify signing
codesign --verify --verbose "dist/Idle Security Reminder.app"
spctl --assess --verbose "dist/Idle Security Reminder.app"
```

## Notarization
```bash
# Create ZIP for notarization
ditto -c -k --keepParent "dist/Idle Security Reminder.app" "dist/idle-reminder.zip"

# Submit for notarization
xcrun notarytool submit "dist/idle-reminder.zip" \
    --apple-id "your-apple-id@example.com" \
    --password "app-specific-password" \
    --team-id "TEAM_ID" \
    --wait

# Staple the notarization
xcrun stapler staple "dist/Idle Security Reminder.app"

# Verify notarization
spctl --assess --verbose "dist/Idle Security Reminder.app"
```

## DMG Signing
```bash
# Sign the DMG
codesign --force --sign "Developer ID Application: Your Name (TEAM_ID)" "dist/idle-reminder-macos.dmg"

# Notarize the DMG
xcrun notarytool submit "dist/idle-reminder-macos.dmg" \
    --apple-id "your-apple-id@example.com" \
    --password "app-specific-password" \
    --team-id "TEAM_ID" \
    --wait

# Staple the DMG
xcrun stapler staple "dist/idle-reminder-macos.dmg"
```
EOF

echo "macOS build completed!"
echo "Available artifacts:"
echo "  - dist/Idle Security Reminder.app (Application bundle)"
echo "  - dist/dmg/ (DMG contents)"
echo "  - dist/pkg/ (PKG installer structure)"
if [ -f "dist/idle-reminder-component.pkg" ]; then
    echo "  - dist/idle-reminder-installer.pkg (PKG installer)"
fi
echo "  - dist/deploy-jamf.sh (Jamf deployment script)"
echo "  - dist/SIGNING_INSTRUCTIONS.md (Code signing guide)"
echo ""
echo "Next steps:"
echo "  1. Run scripts/create_dmg.sh to create DMG"
echo "  2. Follow dist/SIGNING_INSTRUCTIONS.md for code signing"
echo "  3. Test the application on a clean macOS system"
