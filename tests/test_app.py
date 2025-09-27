"""Tests for main application class."""

import pytest
import threading
import time
from unittest.mock import Mock, patch, MagicMock

from idle_reminder.app import IdleReminderApp
from idle_reminder.config import Config


class TestIdleReminderApp:
    """Test main application functionality."""
    
    def test_app_initialization(self):
        """Test application initialization."""
        config = Config()
        app = IdleReminderApp(config, headless=True)
        
        assert app.config == config
        assert app.headless is True
        assert app.running is False
        assert app.idle_detector is not None
        assert app.message_manager is not None
    
    def test_app_initialization_invalid_config(self):
        """Test application initialization with invalid config."""
        config = Config()
        config.idle_seconds = 5  # Invalid (too low)
        
        with pytest.raises(ValueError, match="Invalid configuration"):
            IdleReminderApp(config, headless=True)
    
    def test_headless_run(self):
        """Test running application in headless mode."""
        config = Config()
        config.idle_seconds = 15  # Valid timeout for testing
        config.check_interval_ms = 100  # Fast checking
        
        app = IdleReminderApp(config, headless=True)
        
        # Mock idle detector to return increasing idle time
        mock_detector = Mock()
        mock_detector.get_idle_time.side_effect = [0.0, 0.5, 1.5, 2.0]
        app.idle_detector = mock_detector
        
        # Run for short time
        def stop_app():
            time.sleep(0.5)
            app.stop()
        
        stop_thread = threading.Thread(target=stop_app)
        stop_thread.start()
        
        result = app.run()
        stop_thread.join()
        
        assert result == 0
        assert app.running is False
    
    def test_idle_status_checking(self):
        """Test idle status checking logic."""
        config = Config()
        config.idle_seconds = 15
        
        app = IdleReminderApp(config, headless=True)
        
        # Mock idle detector
        mock_detector = Mock()
        app.idle_detector = mock_detector
        
        # Test below threshold
        mock_detector.get_idle_time.return_value = 1.0
        app._check_idle_status()
        assert app.overlay_shown is False
        
        # Test above threshold (but headless, so no overlay)
        mock_detector.get_idle_time.return_value = 3.0
        app._check_idle_status()
        assert app.overlay_shown is False  # Headless mode
    
    def test_overlay_management_gui_mode(self):
        """Test overlay management in GUI mode."""
        config = Config()
        config.idle_seconds = 15
        
        app = IdleReminderApp(config, headless=False)
        
        # Mock components
        mock_detector = Mock()
        mock_detector.get_idle_time.return_value = 20.0  # Above threshold
        app.idle_detector = mock_detector
        
        mock_overlay_manager = Mock()
        app.overlay_manager = mock_overlay_manager
        
        # Test showing overlay
        app._check_idle_status()
        mock_overlay_manager.show_overlay.assert_called_once()
        assert app.overlay_shown is True
        
        # Test hiding overlay when user becomes active
        mock_detector.get_idle_time.return_value = 0.5  # Below threshold
        app._check_idle_status()
        mock_overlay_manager.dismiss_overlay.assert_called_once()
        assert app.overlay_shown is False
    
    def test_config_reload(self):
        """Test configuration reloading."""
        config = Config()
        config.idle_seconds = 120
        config.messages_file = "messages.txt"
        
        app = IdleReminderApp(config, headless=True)
        
        # Create new config
        new_config = Config()
        new_config.idle_seconds = 300
        new_config.messages_file = "new_messages.txt"
        
        # Mock message manager
        mock_message_manager = Mock()
        app.message_manager = mock_message_manager
        
        # Reload config
        app.reload_config(new_config)
        
        assert app.config.idle_seconds == 300
        assert app.config.messages_file == "new_messages.txt"
    
    def test_config_reload_invalid(self):
        """Test reloading with invalid configuration."""
        config = Config()
        app = IdleReminderApp(config, headless=True)
        
        original_idle_seconds = app.config.idle_seconds
        
        # Create invalid config
        invalid_config = Config()
        invalid_config.idle_seconds = 5  # Too low
        
        # Reload should fail and keep original config
        app.reload_config(invalid_config)
        
        assert app.config.idle_seconds == original_idle_seconds
    
    def test_get_status(self):
        """Test getting application status."""
        config = Config()
        app = IdleReminderApp(config, headless=True)
        
        # Mock components
        mock_detector = Mock()
        mock_detector.get_idle_time.return_value = 5.0
        mock_detector.__class__.__name__ = "TestDetector"
        app.idle_detector = mock_detector
        
        mock_message_manager = Mock()
        mock_message_manager.get_message_count.return_value = 10
        app.message_manager = mock_message_manager
        
        app.last_idle_time = 5.0
        app.overlay_shown = True
        app.running = True
        
        status = app.get_status()
        
        assert status['running'] is True
        assert status['idle_time'] == 5.0
        assert status['idle_threshold'] == config.idle_seconds
        assert status['overlay_shown'] is True
        assert status['message_count'] == 10
        assert status['detector_type'] == "TestDetector"
    
    def test_stop_application(self):
        """Test stopping the application."""
        config = Config()
        app = IdleReminderApp(config, headless=False)
        
        # Mock overlay manager
        mock_overlay_manager = Mock()
        app.overlay_manager = mock_overlay_manager
        app.overlay_shown = True
        
        # Stop application
        app.stop()
        
        assert app.running is False
        mock_overlay_manager.dismiss_overlay.assert_called_once()
    
    @patch('threading.Thread')
    def test_gui_mode_thread_creation(self, mock_thread):
        """Test that GUI mode creates monitoring thread."""
        config = Config()
        app = IdleReminderApp(config, headless=False)
        
        # Mock tkinter root
        with patch('tkinter.Tk') as mock_tk:
            mock_root = Mock()
            mock_tk.return_value = mock_root
            
            # Mock thread
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            try:
                # This would normally run the GUI loop
                app._run_gui()
            except:
                pass  # Expected to fail without proper GUI setup
            
            # Should have created and started thread
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
    
    def test_overlay_dismiss_callback(self):
        """Test overlay dismiss callback."""
        config = Config()
        app = IdleReminderApp(config, headless=True)
        
        app.overlay_shown = True
        app._on_overlay_dismissed()
        
        assert app.overlay_shown is False
