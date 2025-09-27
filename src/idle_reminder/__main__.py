"""Entry point for running the idle reminder as a module."""

import sys
import os

# Add the current directory to Python path for PyInstaller
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    bundle_dir = sys._MEIPASS
    sys.path.insert(0, bundle_dir)

try:
    from .main import main
except ImportError:
    # Fallback for PyInstaller
    from idle_reminder.main import main

if __name__ == "__main__":
    main()
