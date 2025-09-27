"""Main application class for Idle Security Reminder."""

import logging
import threading
import time
import tkinter as tk
from typing import Optional

from .config import Config
from .idle_detector import IdleDetectorFactory
from .messages import MessageManager
from .overlay import OverlayManager

logger = logging.getLogger(__name__)


class IdleReminderApp:
    """Main application class."""
    
    def __init__(self, config: Config, headless: bool = False):
        self.config = config
        self.headless = headless
        self.running = False
        
        # Validate configuration
        if not self.config.validate():
            raise ValueError("Invalid configuration")
        
        # Initialize components
        self.idle_detector = IdleDetectorFactory.create()
        self.message_manager = MessageManager(self.config.messages_file)
        
        if not self.headless:
            self.overlay_manager = OverlayManager(self.config)
        else:
            self.overlay_manager = None
        
        # State tracking
        self.last_idle_time = 0.0
        self.overlay_shown = False
        self.main_thread = None
        
        logger.info("Idle Security Reminder initialized")
        logger.info(f"Idle threshold: {self.config.idle_seconds} seconds")
        logger.info(f"Check interval: {self.config.check_interval_ms} ms")
        logger.info(f"Messages loaded: {self.message_manager.get_message_count()}")
    
    def run(self) -> int:
        """Run the main application loop."""
        try:
            self.running = True
            
            if self.headless:
                return self._run_headless()
            else:
                return self._run_gui()
                
        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            return 0
        except Exception as e:
            logger.error(f"Application error: {e}")
            return 1
        finally:
            self.stop()
    
    def _run_gui(self) -> int:
        """Run with GUI (Tkinter) event loop."""
        # Create hidden root window for Tkinter
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        root.title("Idle Security Reminder")
        
        # Start monitoring in background thread
        self.main_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.main_thread.start()
        
        # Setup periodic check in main thread
        def check_status():
            if self.running:
                root.after(self.config.check_interval_ms, check_status)
        
        check_status()
        
        try:
            # Run Tkinter event loop
            root.mainloop()
        except Exception as e:
            logger.error(f"GUI error: {e}")
            return 1
        
        return 0
    
    def _run_headless(self) -> int:
        """Run in headless mode (for testing)."""
        logger.info("Running in headless mode")
        
        try:
            while self.running:
                self._check_idle_status()
                time.sleep(self.config.check_interval_ms / 1000.0)
        except KeyboardInterrupt:
            pass
        
        return 0
    
    def _monitor_loop(self) -> None:
        """Background monitoring loop."""
        logger.debug("Starting idle monitoring loop")
        
        while self.running:
            try:
                self._check_idle_status()
                time.sleep(self.config.check_interval_ms / 1000.0)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1.0)  # Prevent tight error loop
    
    def _check_idle_status(self) -> None:
        """Check current idle status and show overlay if needed."""
        try:
            current_idle_time = self.idle_detector.get_idle_time()
            
            # Debug logging (only occasionally to avoid spam)
            if int(time.time()) % 30 == 0:  # Log every 30 seconds
                logger.debug(f"Current idle time: {current_idle_time:.1f}s")
            
            # Check if we should show overlay
            if (current_idle_time >= self.config.idle_seconds and 
                not self.overlay_shown and 
                not self.headless):
                
                self._show_security_reminder()
            
            # Check if user became active (overlay should be dismissed)
            elif (current_idle_time < self.config.idle_seconds and 
                  self.overlay_shown):
                
                self._hide_security_reminder()
            
            self.last_idle_time = current_idle_time
            
        except Exception as e:
            logger.error(f"Error checking idle status: {e}")
    
    def _show_security_reminder(self) -> None:
        """Show security reminder overlay."""
        if self.overlay_shown or self.headless:
            return
        
        try:
            message = self.message_manager.get_next_message()
            logger.info(f"Showing security reminder after {self.last_idle_time:.1f}s idle")
            
            self.overlay_manager.show_overlay(
                message,
                on_dismiss=self._on_overlay_dismissed
            )
            
            self.overlay_shown = True
            
        except Exception as e:
            logger.error(f"Failed to show security reminder: {e}")
    
    def _hide_security_reminder(self) -> None:
        """Hide security reminder overlay."""
        if not self.overlay_shown or self.headless:
            return
        
        try:
            logger.debug("User became active, dismissing overlay")
            self.overlay_manager.dismiss_overlay()
            self.overlay_shown = False
            
        except Exception as e:
            logger.error(f"Failed to hide security reminder: {e}")
    
    def _on_overlay_dismissed(self) -> None:
        """Handle overlay dismissal."""
        logger.debug("Overlay dismissed by user")
        self.overlay_shown = False
    
    def stop(self) -> None:
        """Stop the application."""
        logger.info("Stopping Idle Security Reminder")
        self.running = False
        
        # Dismiss any active overlay
        if self.overlay_manager and self.overlay_shown:
            try:
                self.overlay_manager.dismiss_overlay()
            except Exception as e:
                logger.warning(f"Error dismissing overlay on stop: {e}")
        
        # Wait for background thread to finish
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=2.0)
    
    def reload_config(self, new_config: Config) -> None:
        """Reload configuration at runtime."""
        logger.info("Reloading configuration")
        
        # Validate new config
        if not new_config.validate():
            logger.error("Invalid new configuration, keeping current config")
            return
        
        # Update configuration
        old_messages_file = self.config.messages_file
        self.config = new_config
        
        # Reload messages if file changed
        if old_messages_file != new_config.messages_file:
            self.message_manager = MessageManager(new_config.messages_file)
        else:
            self.message_manager.reload_messages()
        
        logger.info("Configuration reloaded successfully")
    
    def get_status(self) -> dict:
        """Get current application status."""
        return {
            'running': self.running,
            'idle_time': self.last_idle_time,
            'idle_threshold': self.config.idle_seconds,
            'overlay_shown': self.overlay_shown,
            'message_count': self.message_manager.get_message_count(),
            'detector_type': self.idle_detector.__class__.__name__
        }
