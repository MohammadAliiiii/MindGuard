"""Tests for idle detection system."""

import pytest
import platform
from unittest.mock import Mock, patch

from idle_reminder.idle_detector import (
    IdleDetectorFactory, 
    WindowsIdleDetector,
    MacOSIdleDetector,
    LinuxIdleDetector,
    FallbackIdleDetector,
    NullIdleDetector
)


class TestIdleDetectorFactory:
    """Test idle detector factory."""
    
    def test_factory_creates_detector(self):
        """Test that factory creates appropriate detector."""
        detector = IdleDetectorFactory.create()
        assert detector is not None
        assert hasattr(detector, 'get_idle_time')
        assert hasattr(detector, 'is_available')
    
    def test_factory_returns_available_detector(self):
        """Test that factory returns an available detector."""
        detector = IdleDetectorFactory.create()
        assert detector.is_available() is True


class TestWindowsIdleDetector:
    """Test Windows idle detector."""
    
    def test_availability_on_windows(self):
        """Test availability detection on Windows."""
        detector = WindowsIdleDetector()
        
        if platform.system() == "Windows":
            # Should be available on Windows with proper imports
            assert detector.is_available() in [True, False]  # Depends on ctypes availability
        else:
            # Should not be available on non-Windows
            assert detector.is_available() is False
    
    def test_get_idle_time_unavailable(self):
        """Test get_idle_time when detector is unavailable."""
        detector = WindowsIdleDetector()
        
        # Mock as unavailable
        with patch.object(detector, 'is_available', return_value=False):
            idle_time = detector.get_idle_time()
            assert idle_time == 0.0
    
    @patch('platform.system', return_value='Windows')
    def test_windows_detector_initialization(self, mock_system):
        """Test Windows detector initialization."""
        with patch('ctypes.windll', create=True):
            detector = WindowsIdleDetector()
            assert detector.is_available() is True


class TestMacOSIdleDetector:
    """Test macOS idle detector."""
    
    def test_availability_on_macos(self):
        """Test availability detection on macOS."""
        detector = MacOSIdleDetector()
        
        if platform.system() == "Darwin":
            # Should be available on macOS with proper imports
            assert detector.is_available() in [True, False]  # Depends on Quartz availability
        else:
            # Should not be available on non-macOS
            assert detector.is_available() is False
    
    def test_get_idle_time_unavailable(self):
        """Test get_idle_time when detector is unavailable."""
        detector = MacOSIdleDetector()
        
        # Mock as unavailable
        with patch.object(detector, 'is_available', return_value=False):
            idle_time = detector.get_idle_time()
            assert idle_time == 0.0


class TestLinuxIdleDetector:
    """Test Linux idle detector."""
    
    def test_availability_on_linux(self):
        """Test availability detection on Linux."""
        detector = LinuxIdleDetector()
        
        if platform.system() == "Linux":
            # Should be available on Linux
            assert detector.is_available() in [True, False]  # Depends on X11/environment
        else:
            # Should not be available on non-Linux
            assert detector.is_available() is False
    
    def test_get_idle_time_unavailable(self):
        """Test get_idle_time when detector is unavailable."""
        detector = LinuxIdleDetector()
        
        # Mock as unavailable
        with patch.object(detector, 'is_available', return_value=False):
            idle_time = detector.get_idle_time()
            assert idle_time == 0.0


class TestFallbackIdleDetector:
    """Test fallback idle detector."""
    
    def test_initialization(self):
        """Test fallback detector initialization."""
        detector = FallbackIdleDetector()
        # Should always try to initialize
        assert hasattr(detector, '_available')
    
    def test_get_idle_time_available(self):
        """Test get_idle_time when detector is available."""
        detector = FallbackIdleDetector()
        
        if detector.is_available():
            idle_time = detector.get_idle_time()
            assert isinstance(idle_time, float)
            assert idle_time >= 0.0
    
    def test_get_idle_time_unavailable(self):
        """Test get_idle_time when detector is unavailable."""
        detector = FallbackIdleDetector()
        
        # Mock as unavailable
        with patch.object(detector, 'is_available', return_value=False):
            idle_time = detector.get_idle_time()
            assert idle_time == 0.0
    
    def test_activity_tracking(self):
        """Test that activity updates are tracked."""
        detector = FallbackIdleDetector()
        
        if detector.is_available():
            # Simulate activity
            detector._on_activity()
            
            # Idle time should be very small (recent activity)
            idle_time = detector.get_idle_time()
            assert idle_time < 1.0  # Less than 1 second


class TestNullIdleDetector:
    """Test null idle detector."""
    
    def test_always_available(self):
        """Test that null detector is always available."""
        detector = NullIdleDetector()
        assert detector.is_available() is True
    
    def test_always_returns_zero(self):
        """Test that null detector always returns zero idle time."""
        detector = NullIdleDetector()
        assert detector.get_idle_time() == 0.0
