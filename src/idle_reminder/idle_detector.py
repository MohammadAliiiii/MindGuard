"""Cross-platform idle time detection."""

import logging
import platform
import time
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)


class IdleDetector(ABC):
    """Abstract base class for idle time detection."""
    
    @abstractmethod
    def get_idle_time(self) -> float:
        """Get the current idle time in seconds."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this detector is available on the current system."""
        pass


class WindowsIdleDetector(IdleDetector):
    """Windows idle time detection using GetLastInputInfo."""
    
    def __init__(self):
        self._available = False
        try:
            import ctypes
            from ctypes import wintypes
            self._kernel32 = ctypes.windll.kernel32
            self._user32 = ctypes.windll.user32
            
            # Define LASTINPUTINFO structure
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [
                    ('cbSize', wintypes.UINT),
                    ('dwTime', wintypes.DWORD)
                ]
            
            self._LASTINPUTINFO = LASTINPUTINFO
            self._available = True
            logger.debug("Windows idle detector initialized")
            
        except ImportError:
            logger.warning("Windows idle detection not available (missing ctypes)")
        except Exception as e:
            logger.warning(f"Windows idle detection initialization failed: {e}")
    
    def is_available(self) -> bool:
        return self._available and platform.system() == "Windows"
    
    def get_idle_time(self) -> float:
        if not self.is_available():
            return 0.0
        
        try:
            lii = self._LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(self._LASTINPUTINFO)
            
            if self._user32.GetLastInputInfo(ctypes.byref(lii)):
                millis = self._kernel32.GetTickCount() - lii.dwTime
                return millis / 1000.0
            else:
                logger.warning("GetLastInputInfo failed")
                return 0.0
                
        except Exception as e:
            logger.error(f"Windows idle detection error: {e}")
            return 0.0


class MacOSIdleDetector(IdleDetector):
    """macOS idle time detection using Quartz."""
    
    def __init__(self):
        self._available = False
        try:
            import Quartz
            self._Quartz = Quartz
            self._available = True
            logger.debug("macOS idle detector initialized")
            
        except ImportError:
            logger.warning("macOS idle detection not available (missing Quartz)")
        except Exception as e:
            logger.warning(f"macOS idle detection initialization failed: {e}")
    
    def is_available(self) -> bool:
        return self._available and platform.system() == "Darwin"
    
    def get_idle_time(self) -> float:
        if not self.is_available():
            return 0.0
        
        try:
            idle_time = self._Quartz.CGEventSourceSecondsSinceLastEventType(
                self._Quartz.kCGEventSourceStateCombinedSessionState,
                self._Quartz.kCGAnyInputEventType
            )
            return float(idle_time)
            
        except Exception as e:
            logger.error(f"macOS idle detection error: {e}")
            return 0.0


class LinuxIdleDetector(IdleDetector):
    """Linux idle time detection using X11."""
    
    def __init__(self):
        self._available = False
        self._display = None
        
        try:
            # Try X11 approach first
            import ctypes
            import ctypes.util
            
            # Load X11 libraries
            x11_lib = ctypes.util.find_library('X11')
            xss_lib = ctypes.util.find_library('Xss')
            
            if x11_lib and xss_lib:
                self._x11 = ctypes.CDLL(x11_lib)
                self._xss = ctypes.CDLL(xss_lib)
                
                # Define XScreenSaverInfo structure
                class XScreenSaverInfo(ctypes.Structure):
                    _fields_ = [
                        ('window', ctypes.c_ulong),
                        ('state', ctypes.c_int),
                        ('kind', ctypes.c_int),
                        ('til_or_since', ctypes.c_ulong),
                        ('idle', ctypes.c_ulong),
                        ('eventMask', ctypes.c_ulong)
                    ]
                
                self._XScreenSaverInfo = XScreenSaverInfo
                
                # Open display
                self._display = self._x11.XOpenDisplay(None)
                if self._display:
                    self._available = True
                    logger.debug("Linux X11 idle detector initialized")
                
        except Exception as e:
            logger.warning(f"Linux X11 idle detection initialization failed: {e}")
        
        # Fallback to environment-based detection
        if not self._available:
            try:
                import os
                if 'DISPLAY' in os.environ or 'WAYLAND_DISPLAY' in os.environ:
                    self._available = True
                    logger.debug("Linux fallback idle detector initialized")
            except Exception as e:
                logger.warning(f"Linux fallback idle detection failed: {e}")
    
    def is_available(self) -> bool:
        return self._available and platform.system() == "Linux"
    
    def get_idle_time(self) -> float:
        if not self.is_available():
            return 0.0
        
        # Try X11 method first
        if self._display:
            try:
                import ctypes
                info = self._XScreenSaverInfo()
                self._xss.XScreenSaverQueryInfo(self._display, 
                                               self._x11.XDefaultRootWindow(self._display),
                                               ctypes.byref(info))
                return info.idle / 1000.0
                
            except Exception as e:
                logger.error(f"Linux X11 idle detection error: {e}")
        
        # Fallback: return 0 (always active)
        # In production, this could be enhanced with other methods
        logger.debug("Using Linux fallback idle detection (always returns 0)")
        return 0.0
    
    def __del__(self):
        """Clean up X11 display connection."""
        if hasattr(self, '_display') and self._display:
            try:
                self._x11.XCloseDisplay(self._display)
            except:
                pass


class FallbackIdleDetector(IdleDetector):
    """Fallback idle detector using pynput for basic activity monitoring."""
    
    def __init__(self):
        self._available = False
        self._last_activity = time.time()
        
        try:
            from pynput import mouse, keyboard
            
            # Set up listeners for activity detection
            self._mouse_listener = mouse.Listener(
                on_move=self._on_activity,
                on_click=self._on_activity,
                on_scroll=self._on_activity
            )
            
            self._keyboard_listener = keyboard.Listener(
                on_press=self._on_activity,
                on_release=self._on_activity
            )
            
            # Start listeners
            self._mouse_listener.start()
            self._keyboard_listener.start()
            
            self._available = True
            logger.debug("Fallback pynput idle detector initialized")
            
        except ImportError:
            logger.warning("Fallback idle detection not available (missing pynput)")
        except Exception as e:
            logger.warning(f"Fallback idle detection initialization failed: {e}")
    
    def _on_activity(self, *args):
        """Update last activity time."""
        self._last_activity = time.time()
    
    def is_available(self) -> bool:
        return self._available
    
    def get_idle_time(self) -> float:
        if not self.is_available():
            return 0.0
        
        return time.time() - self._last_activity
    
    def __del__(self):
        """Clean up listeners."""
        try:
            if hasattr(self, '_mouse_listener'):
                self._mouse_listener.stop()
            if hasattr(self, '_keyboard_listener'):
                self._keyboard_listener.stop()
        except:
            pass


class IdleDetectorFactory:
    """Factory for creating appropriate idle detector for the current platform."""
    
    @staticmethod
    def create() -> IdleDetector:
        """Create the best available idle detector for the current platform."""
        detectors = [
            WindowsIdleDetector(),
            MacOSIdleDetector(),
            LinuxIdleDetector(),
            FallbackIdleDetector()
        ]
        
        for detector in detectors:
            if detector.is_available():
                logger.info(f"Using idle detector: {detector.__class__.__name__}")
                return detector
        
        # This should never happen, but provide a safe fallback
        logger.error("No idle detector available, using null detector")
        return NullIdleDetector()


class NullIdleDetector(IdleDetector):
    """Null idle detector that always returns 0 idle time."""
    
    def is_available(self) -> bool:
        return True
    
    def get_idle_time(self) -> float:
        return 0.0
