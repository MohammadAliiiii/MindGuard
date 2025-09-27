"""Diagnostics and system information for troubleshooting."""

import json
import logging
import platform
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from .config import Config

logger = logging.getLogger(__name__)


def generate_diagnostics(config_path: Path) -> Dict[str, Any]:
    """Generate comprehensive diagnostics information."""
    diagnostics = {
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'system': get_system_info(),
        'python': get_python_info(),
        'config': get_config_info(config_path),
        'dependencies': get_dependency_info(),
        'environment': get_environment_info()
    }
    
    # Write to file
    try:
        with open('diagnostics.json', 'w', encoding='utf-8') as f:
            json.dump(diagnostics, f, indent=2, default=str)
        logger.info("Diagnostics written to diagnostics.json")
    except Exception as e:
        logger.error(f"Failed to write diagnostics: {e}")
    
    return diagnostics


def get_system_info() -> Dict[str, Any]:
    """Get system information."""
    return {
        'platform': platform.platform(),
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'architecture': platform.architecture(),
        'hostname': platform.node()
    }


def get_python_info() -> Dict[str, Any]:
    """Get Python environment information."""
    return {
        'version': sys.version,
        'version_info': {
            'major': sys.version_info.major,
            'minor': sys.version_info.minor,
            'micro': sys.version_info.micro
        },
        'executable': sys.executable,
        'path': sys.path[:5],  # First 5 entries only
        'prefix': sys.prefix
    }


def get_config_info(config_path: Path) -> Dict[str, Any]:
    """Get configuration information."""
    config_info = {
        'config_file': str(config_path),
        'config_exists': config_path.exists(),
        'config_readable': False,
        'config_valid': False
    }
    
    if config_path.exists():
        try:
            config = Config.load(config_path)
            config_info['config_readable'] = True
            config_info['config_valid'] = config.validate()
            config_info['idle_seconds'] = config.idle_seconds
            config_info['messages_file'] = config.messages_file
            config_info['theme'] = config.theme
            config_info['log_level'] = config.log_level
            config_info['multi_monitor'] = config.multi_monitor
            
            # Check messages file
            messages_path = Path(config.messages_file)
            config_info['messages_file_exists'] = messages_path.exists()
            if messages_path.exists():
                try:
                    with open(messages_path, 'r', encoding='utf-8') as f:
                        lines = [line.strip() for line in f if line.strip()]
                    config_info['message_count'] = len(lines)
                except Exception:
                    config_info['message_count'] = 0
            
        except Exception as e:
            config_info['config_error'] = str(e)
    
    return config_info


def get_dependency_info() -> Dict[str, Any]:
    """Get dependency information."""
    dependencies = {}
    
    # Check required dependencies
    required_deps = [
        'tkinter', 'yaml', 'pynput'
    ]
    
    for dep in required_deps:
        try:
            if dep == 'tkinter':
                import tkinter
                dependencies[dep] = {
                    'available': True,
                    'version': tkinter.TkVersion if hasattr(tkinter, 'TkVersion') else 'unknown'
                }
            elif dep == 'yaml':
                import yaml
                dependencies[dep] = {
                    'available': True,
                    'version': getattr(yaml, '__version__', 'unknown')
                }
            elif dep == 'pynput':
                import pynput
                dependencies[dep] = {
                    'available': True,
                    'version': getattr(pynput, '__version__', 'unknown')
                }
        except ImportError:
            dependencies[dep] = {
                'available': False,
                'error': 'Not installed'
            }
        except Exception as e:
            dependencies[dep] = {
                'available': False,
                'error': str(e)
            }
    
    # Check optional dependencies
    optional_deps = ['screeninfo']
    
    for dep in optional_deps:
        try:
            if dep == 'screeninfo':
                import screeninfo
                dependencies[dep] = {
                    'available': True,
                    'version': getattr(screeninfo, '__version__', 'unknown'),
                    'optional': True
                }
        except ImportError:
            dependencies[dep] = {
                'available': False,
                'error': 'Not installed',
                'optional': True
            }
        except Exception as e:
            dependencies[dep] = {
                'available': False,
                'error': str(e),
                'optional': True
            }
    
    # Check platform-specific dependencies
    system = platform.system()
    if system == 'Windows':
        try:
            import ctypes
            dependencies['ctypes'] = {'available': True, 'platform_specific': 'Windows'}
        except ImportError:
            dependencies['ctypes'] = {'available': False, 'platform_specific': 'Windows'}
    
    elif system == 'Darwin':
        try:
            import Quartz
            dependencies['Quartz'] = {'available': True, 'platform_specific': 'macOS'}
        except ImportError:
            dependencies['Quartz'] = {'available': False, 'platform_specific': 'macOS'}
    
    return dependencies


def get_environment_info() -> Dict[str, Any]:
    """Get environment information."""
    import os
    
    env_info = {
        'display_available': False,
        'desktop_environment': None,
        'user': os.getenv('USER', os.getenv('USERNAME', 'unknown'))
    }
    
    # Check display availability
    if 'DISPLAY' in os.environ:
        env_info['display_available'] = True
        env_info['display'] = os.environ['DISPLAY']
    elif 'WAYLAND_DISPLAY' in os.environ:
        env_info['display_available'] = True
        env_info['wayland_display'] = os.environ['WAYLAND_DISPLAY']
    elif platform.system() == 'Windows':
        env_info['display_available'] = True  # Windows always has display
    elif platform.system() == 'Darwin':
        env_info['display_available'] = True  # macOS always has display
    
    # Desktop environment detection
    desktop_vars = [
        'XDG_CURRENT_DESKTOP', 'DESKTOP_SESSION', 'GDMSESSION',
        'XDG_SESSION_DESKTOP', 'GNOME_DESKTOP_SESSION_ID'
    ]
    
    for var in desktop_vars:
        if var in os.environ:
            env_info['desktop_environment'] = os.environ[var]
            break
    
    return env_info
