#!/bin/bash
# Build script for all platforms

set -e

echo "Building Idle Security Reminder for all platforms..."

# Create build directory
mkdir -p build
mkdir -p dist

# Install build dependencies
echo "Installing build dependencies..."
python -m pip install pyinstaller

# Detect platform and run appropriate build
case "$(uname -s)" in
    Linux*)     
        echo "Building for Linux..."
        ./scripts/build_linux.sh
        ;;
    Darwin*)    
        echo "Building for macOS..."
        ./scripts/build_macos.sh
        ;;
    CYGWIN*|MINGW*|MSYS*)
        echo "Building for Windows..."
        ./scripts/build_windows.bat
        ;;
    *)
        echo "Unknown platform: $(uname -s)"
        echo "Attempting generic Linux build..."
        ./scripts/build_linux.sh
        ;;
esac

echo "Build completed successfully!"
echo "Artifacts available in dist/ directory"
