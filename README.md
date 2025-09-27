# Idle Security Reminder

A lightweight, cross-platform desktop application that detects user idle time and displays full-screen security reminder overlays for enterprise environments.

## Features

- **Cross-platform**: Windows, macOS, Linux support
- **Low resource usage**: <1% CPU when idle, <50MB memory
- **Enterprise-ready**: Configurable via YAML, centralized deployment support
- **Accessible**: High contrast themes, screen reader support, TTS option
- **Secure**: No telemetry, user-privilege only, minimal logging
- **Multi-monitor support**: Overlays on all screens

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the application:
   ```bash
   python -m idle_reminder
   ```

3. Configure settings in `config.yaml`

## Configuration

Edit `config.yaml` to customize:
- Idle timeout (default: 120 seconds)
- Messages file path
- Visual themes and colors
- Reporting options
- Accessibility settings

## Building

### All Platforms
```bash
make build
```

### Platform-specific
```bash
# Windows
./scripts/build_windows.bat

# macOS
./scripts/build_macos.sh

# Linux
./scripts/build_linux.sh
```

## Enterprise Deployment

See `deployment/` directory for:
- Windows GPO/PowerShell scripts
- macOS Jamf/Munki examples
- Linux package management
- Microsoft Intune policies

