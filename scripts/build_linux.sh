#!/bin/bash
# Linux build script for Idle Security Reminder

set -e

echo "Building Idle Security Reminder for Linux..."

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
        'pynput.keyboard._xorg',
        'pynput.mouse._xorg',
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
EOF

# Build with PyInstaller
echo "Running PyInstaller..."
pyinstaller --clean idle_reminder.spec

# Create AppImage structure
echo "Creating AppImage..."
mkdir -p dist/AppImage/idle-reminder.AppDir/usr/bin
mkdir -p dist/AppImage/idle-reminder.AppDir/usr/share/applications
mkdir -p dist/AppImage/idle-reminder.AppDir/usr/share/icons/hicolor/256x256/apps

# Copy executable
cp -r dist/idle-reminder/* dist/AppImage/idle-reminder.AppDir/usr/bin/

# Create desktop file
cat > dist/AppImage/idle-reminder.AppDir/idle-reminder.desktop << 'EOF'
[Desktop Entry]
Type=Application
Name=Idle Security Reminder
Comment=Desktop security awareness tool
Exec=idle-reminder
Icon=idle-reminder
Categories=Security;Utility;
StartupNotify=true
NoDisplay=false
EOF

# Create AppRun script
cat > dist/AppImage/idle-reminder.AppDir/AppRun << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/idle-reminder/idle-reminder" "$@"
EOF

chmod +x dist/AppImage/idle-reminder.AppDir/AppRun

# Create simple icon (text-based)
cat > dist/AppImage/idle-reminder.AppDir/idle-reminder.svg << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" fill="#2E3440"/>
  <text x="128" y="140" font-family="Arial" font-size="48" fill="#88C0D0" text-anchor="middle">🔒</text>
  <text x="128" y="180" font-family="Arial" font-size="16" fill="#D8DEE9" text-anchor="middle">Security</text>
  <text x="128" y="200" font-family="Arial" font-size="16" fill="#D8DEE9" text-anchor="middle">Reminder</text>
</svg>
EOF

cp dist/AppImage/idle-reminder.AppDir/idle-reminder.svg dist/AppImage/idle-reminder.AppDir/usr/share/icons/hicolor/256x256/apps/

# Copy desktop file to applications
cp dist/AppImage/idle-reminder.AppDir/idle-reminder.desktop dist/AppImage/idle-reminder.AppDir/usr/share/applications/

# Try to create AppImage if appimagetool is available
if command -v appimagetool &> /dev/null; then
    echo "Creating AppImage with appimagetool..."
    appimagetool dist/AppImage/idle-reminder.AppDir dist/idle-reminder-linux-x86_64.AppImage
else
    echo "appimagetool not found, creating tar.gz archive instead..."
    cd dist/AppImage
    tar -czf ../idle-reminder-linux-x86_64.tar.gz idle-reminder.AppDir
    cd ../..
fi

# Create .deb package structure
echo "Creating .deb package structure..."
mkdir -p dist/deb/idle-reminder_1.0.0_amd64/DEBIAN
mkdir -p dist/deb/idle-reminder_1.0.0_amd64/usr/bin
mkdir -p dist/deb/idle-reminder_1.0.0_amd64/usr/share/applications
mkdir -p dist/deb/idle-reminder_1.0.0_amd64/usr/share/doc/idle-reminder
mkdir -p dist/deb/idle-reminder_1.0.0_amd64/etc/idle-reminder

# Copy files
cp -r dist/idle-reminder/* dist/deb/idle-reminder_1.0.0_amd64/usr/bin/
cp config.yaml dist/deb/idle-reminder_1.0.0_amd64/etc/idle-reminder/
cp messages.txt dist/deb/idle-reminder_1.0.0_amd64/etc/idle-reminder/
cp README.md dist/deb/idle-reminder_1.0.0_amd64/usr/share/doc/idle-reminder/

# Create control file
cat > dist/deb/idle-reminder_1.0.0_amd64/DEBIAN/control << 'EOF'
Package: idle-reminder
Version: 1.0.0
Section: security
Priority: optional
Architecture: amd64
Depends: python3, python3-tk
Maintainer: Enterprise Security Team <security@company.com>
Description: Idle Security Reminder
 A lightweight desktop application that detects user idle time and displays
 full-screen security reminder overlays for enterprise environments.
 .
 Features cross-platform support, low resource usage, enterprise configuration,
 accessibility features, and secure operation.
EOF

# Create desktop file for .deb
cp dist/AppImage/idle-reminder.AppDir/idle-reminder.desktop dist/deb/idle-reminder_1.0.0_amd64/usr/share/applications/

# Create postinst script
cat > dist/deb/idle-reminder_1.0.0_amd64/DEBIAN/postinst << 'EOF'
#!/bin/bash
set -e

# Create symlink for executable
ln -sf /usr/bin/idle-reminder/idle-reminder /usr/local/bin/idle-reminder

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications
fi

echo "Idle Security Reminder installed successfully"
echo "Run 'idle-reminder' to start the application"
EOF

chmod +x dist/deb/idle-reminder_1.0.0_amd64/DEBIAN/postinst

# Create prerm script
cat > dist/deb/idle-reminder_1.0.0_amd64/DEBIAN/prerm << 'EOF'
#!/bin/bash
set -e

# Remove symlink
rm -f /usr/local/bin/idle-reminder
EOF

chmod +x dist/deb/idle-reminder_1.0.0_amd64/DEBIAN/prerm

# Build .deb package if dpkg-deb is available
if command -v dpkg-deb &> /dev/null; then
    echo "Building .deb package..."
    dpkg-deb --build dist/deb/idle-reminder_1.0.0_amd64 dist/idle-reminder_1.0.0_amd64.deb
else
    echo "dpkg-deb not found, .deb package structure created in dist/deb/"
fi

echo "Linux build completed!"
echo "Available artifacts:"
echo "  - dist/idle-reminder/ (PyInstaller build)"
if [ -f "dist/idle-reminder-linux-x86_64.AppImage" ]; then
    echo "  - dist/idle-reminder-linux-x86_64.AppImage"
elif [ -f "dist/idle-reminder-linux-x86_64.tar.gz" ]; then
    echo "  - dist/idle-reminder-linux-x86_64.tar.gz"
fi
if [ -f "dist/idle-reminder_1.0.0_amd64.deb" ]; then
    echo "  - dist/idle-reminder_1.0.0_amd64.deb"
fi
