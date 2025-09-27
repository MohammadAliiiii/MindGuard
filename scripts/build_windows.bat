@echo off
REM Windows build script for Idle Security Reminder

echo Building Idle Security Reminder for Windows...

REM Create build directory
if not exist build mkdir build
if not exist dist mkdir dist

REM Create spec file for PyInstaller
echo Creating PyInstaller spec file...
(
echo # -*- mode: python ; coding: utf-8 -*-
echo.
echo block_cipher = None
echo.
echo a = Analysis^(
echo     ['src/idle_reminder/__main__.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=[
echo         ^('config.yaml', '.'^),
echo         ^('messages.txt', '.'^),
echo         ^('src/idle_reminder', 'idle_reminder'^),
echo     ],
echo     hiddenimports=[
echo         'pynput.keyboard._win32',
echo         'pynput.mouse._win32',
echo     ],
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=[],
echo     win_no_prefer_redirects=False,
echo     win_private_assemblies=False,
echo     cipher=block_cipher,
echo     noarchive=False,
echo ^)
echo.
echo pyz = PYZ^(a.pure, a.zipped_data, cipher=block_cipher^)
echo.
echo exe = EXE^(
echo     pyz,
echo     a.scripts,
echo     [],
echo     exclude_binaries=True,
echo     name='idle-reminder',
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     console=False,
echo     disable_windowed_traceback=False,
echo     argv_emulation=False,
echo     target_arch=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo     icon=None,
echo ^)
echo.
echo coll = COLLECT^(
echo     exe,
echo     a.binaries,
echo     a.zipfiles,
echo     a.datas,
echo     strip=False,
echo     upx=True,
echo     upx_exclude=[],
echo     name='idle-reminder',
echo ^)
) > idle_reminder.spec

REM Build with PyInstaller
echo Running PyInstaller...
pyinstaller --clean idle_reminder.spec

if errorlevel 1 (
    echo PyInstaller build failed!
    exit /b 1
)

REM Create single-file executable
echo Creating single-file executable...
pyinstaller --onefile --windowed --name idle-reminder-standalone src/idle_reminder/__main__.py

REM Create MSI installer structure
echo Creating MSI installer structure...
mkdir dist\msi
mkdir dist\msi\idle-reminder

REM Copy files for MSI
xcopy /E /I dist\idle-reminder dist\msi\idle-reminder\
copy config.yaml dist\msi\idle-reminder\
copy messages.txt dist\msi\idle-reminder\
copy README.md dist\msi\idle-reminder\

REM Create WiX installer script
echo Creating WiX installer script...
(
echo ^<?xml version="1.0" encoding="UTF-8"?^>
echo ^<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi"^>
echo   ^<Product Id="*" Name="Idle Security Reminder" Language="1033" 
echo            Version="1.0.0" Manufacturer="Enterprise Security Team" 
echo            UpgradeCode="12345678-1234-1234-1234-123456789012"^>
echo     ^<Package InstallerVersion="200" Compressed="yes" InstallScope="perMachine" /^>
echo.
echo     ^<MajorUpgrade DowngradeErrorMessage="A newer version is already installed." /^>
echo     ^<MediaTemplate EmbedCab="yes" /^>
echo.
echo     ^<Feature Id="ProductFeature" Title="Idle Security Reminder" Level="1"^>
echo       ^<ComponentGroupRef Id="ProductComponents" /^>
echo     ^</Feature^>
echo   ^</Product^>
echo.
echo   ^<Fragment^>
echo     ^<Directory Id="TARGETDIR" Name="SourceDir"^>
echo       ^<Directory Id="ProgramFilesFolder"^>
echo         ^<Directory Id="INSTALLFOLDER" Name="Idle Security Reminder" /^>
echo       ^</Directory^>
echo     ^</Directory^>
echo   ^</Fragment^>
echo.
echo   ^<Fragment^>
echo     ^<ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER"^>
echo       ^<Component Id="MainExecutable" Guid="*"^>
echo         ^<File Id="IdleReminderExe" Source="dist\idle-reminder\idle-reminder.exe" 
echo               KeyPath="yes" Checksum="yes" /^>
echo       ^</Component^>
echo       ^<Component Id="ConfigFile" Guid="*"^>
echo         ^<File Id="ConfigYaml" Source="config.yaml" KeyPath="yes" /^>
echo       ^</Component^>
echo       ^<Component Id="MessagesFile" Guid="*"^>
echo         ^<File Id="MessagesTxt" Source="messages.txt" KeyPath="yes" /^>
echo       ^</Component^>
echo     ^</ComponentGroup^>
echo   ^</Fragment^>
echo ^</Wix^>
) > dist\msi\installer.wxs

REM Create Inno Setup script
echo Creating Inno Setup script...
(
echo [Setup]
echo AppName=Idle Security Reminder
echo AppVersion=1.0.0
echo AppPublisher=Enterprise Security Team
echo DefaultDirName={autopf}\Idle Security Reminder
echo DefaultGroupName=Idle Security Reminder
echo OutputDir=dist
echo OutputBaseFilename=idle-reminder-setup
echo Compression=lzma
echo SolidCompression=yes
echo WizardStyle=modern
echo.
echo [Languages]
echo Name: "english"; MessagesFile: "compiler:Default.isl"
echo.
echo [Tasks]
echo Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
echo Name: "startupicon"; Description: "Start with Windows"; GroupDescription: "Startup Options"; Flags: unchecked
echo.
echo [Files]
echo Source: "dist\idle-reminder\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
echo Source: "config.yaml"; DestDir: "{app}"; Flags: ignoreversion
echo Source: "messages.txt"; DestDir: "{app}"; Flags: ignoreversion
echo Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
echo.
echo [Icons]
echo Name: "{group}\Idle Security Reminder"; Filename: "{app}\idle-reminder.exe"
echo Name: "{group}\{cm:UninstallProgram,Idle Security Reminder}"; Filename: "{uninstallexe}"
echo Name: "{autodesktop}\Idle Security Reminder"; Filename: "{app}\idle-reminder.exe"; Tasks: desktopicon
echo.
echo [Registry]
echo Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "IdleSecurityReminder"; ValueData: "{app}\idle-reminder.exe"; Flags: uninsdeletevalue; Tasks: startupicon
echo.
echo [Run]
echo Filename: "{app}\idle-reminder.exe"; Description: "{cm:LaunchProgram,Idle Security Reminder}"; Flags: nowait postinstall skipifsilent
) > dist\idle-reminder.iss

REM Create PowerShell deployment script
echo Creating PowerShell deployment script...
(
echo # PowerShell deployment script for Idle Security Reminder
echo # Run as Administrator for system-wide deployment
echo.
echo param^(
echo     [string]$InstallPath = "$env:ProgramFiles\Idle Security Reminder",
echo     [switch]$AllUsers = $false,
echo     [switch]$StartupTask = $false
echo ^)
echo.
echo Write-Host "Deploying Idle Security Reminder..." -ForegroundColor Green
echo.
echo # Create installation directory
echo if ^(-not ^(Test-Path $InstallPath^)^) {
echo     New-Item -ItemType Directory -Path $InstallPath -Force ^| Out-Null
echo     Write-Host "Created directory: $InstallPath" -ForegroundColor Yellow
echo }
echo.
echo # Copy files
echo $SourcePath = ".\dist\idle-reminder"
echo Copy-Item -Path "$SourcePath\*" -Destination $InstallPath -Recurse -Force
echo Copy-Item -Path ".\config.yaml" -Destination $InstallPath -Force
echo Copy-Item -Path ".\messages.txt" -Destination $InstallPath -Force
echo Write-Host "Files copied to $InstallPath" -ForegroundColor Yellow
echo.
echo # Create scheduled task for startup ^(if requested^)
echo if ^($StartupTask^) {
echo     $TaskName = "IdleSecurityReminder"
echo     $ExePath = Join-Path $InstallPath "idle-reminder.exe"
echo     
echo     # Remove existing task if it exists
echo     Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
echo     
echo     # Create new task
echo     $Action = New-ScheduledTaskAction -Execute $ExePath
echo     $Trigger = New-ScheduledTaskTrigger -AtLogOn
echo     $Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
echo     
echo     if ^($AllUsers^) {
echo         $Principal = New-ScheduledTaskPrincipal -GroupId "Users" -RunLevel Limited
echo     } else {
echo         $Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Limited
echo     }
echo     
echo     Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal
echo     Write-Host "Scheduled task created: $TaskName" -ForegroundColor Yellow
echo }
echo.
echo # Add to PATH ^(optional^)
echo $CurrentPath = [Environment]::GetEnvironmentVariable^("PATH", "Machine"^)
echo if ^($CurrentPath -notlike "*$InstallPath*"^) {
echo     Write-Host "To add to system PATH, run as Administrator:" -ForegroundColor Cyan
echo     Write-Host "[Environment]::SetEnvironmentVariable^('PATH', `"$CurrentPath;$InstallPath`", 'Machine'^)" -ForegroundColor Gray
echo }
echo.
echo Write-Host "Deployment completed successfully!" -ForegroundColor Green
echo Write-Host "Run '$InstallPath\idle-reminder.exe' to start the application" -ForegroundColor Cyan
) > dist\deploy-windows.ps1

echo Windows build completed!
echo Available artifacts:
echo   - dist\idle-reminder\ ^(PyInstaller build^)
echo   - dist\idle-reminder-standalone.exe ^(Single file executable^)
echo   - dist\idle-reminder.iss ^(Inno Setup script^)
echo   - dist\msi\installer.wxs ^(WiX installer script^)
echo   - dist\deploy-windows.ps1 ^(PowerShell deployment script^)
echo.
echo To create installers:
echo   - For Inno Setup: Install Inno Setup and compile dist\idle-reminder.iss
echo   - For MSI: Install WiX Toolset and run: candle dist\msi\installer.wxs ^&^& light installer.wixobj
