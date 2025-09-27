"""Fullscreen overlay system for displaying security reminders."""

import logging
import tkinter as tk
from tkinter import ttk
import threading
import time
from typing import List, Optional, Callable
import webbrowser
import urllib.parse

try:
    from screeninfo import get_monitors
    SCREENINFO_AVAILABLE = True
except ImportError:
    SCREENINFO_AVAILABLE = False
    logging.warning("screeninfo not available, multi-monitor support limited")

from .config import Config

logger = logging.getLogger(__name__)


class SecurityOverlay:
    """Fullscreen security reminder overlay."""
    
    def __init__(self, config: Config, message: str, on_dismiss: Optional[Callable] = None):
        self.config = config
        self.message = message
        self.on_dismiss = on_dismiss
        self.windows: List[tk.Toplevel] = []
        self.dismissed = False
        self._setup_windows()
    
    def _setup_windows(self) -> None:
        """Setup overlay windows for all monitors."""
        try:
            # Get monitor information
            monitors = self._get_monitors()
            
            for i, monitor in enumerate(monitors):
                window = self._create_overlay_window(monitor, i == 0)  # First window is primary
                self.windows.append(window)
                
        except Exception as e:
            logger.error(f"Failed to setup overlay windows: {e}")
            # Fallback: create single window
            window = self._create_overlay_window(None, True)
            self.windows = [window]
    
    def _get_monitors(self) -> List[dict]:
        """Get monitor information."""
        monitors = []
        
        if SCREENINFO_AVAILABLE and self.config.multi_monitor:
            try:
                for monitor in get_monitors():
                    monitors.append({
                        'x': monitor.x,
                        'y': monitor.y,
                        'width': monitor.width,
                        'height': monitor.height,
                        'is_primary': monitor.is_primary if hasattr(monitor, 'is_primary') else False
                    })
                logger.debug(f"Found {len(monitors)} monitors")
            except Exception as e:
                logger.warning(f"Failed to get monitor info: {e}")
        
        # Fallback to primary monitor
        if not monitors:
            # Use tkinter to get screen dimensions
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            monitors.append({
                'x': 0,
                'y': 0,
                'width': root.winfo_screenwidth(),
                'height': root.winfo_screenheight(),
                'is_primary': True
            })
            root.destroy()
        
        return monitors
    
    def _create_overlay_window(self, monitor: Optional[dict], is_primary: bool) -> tk.Toplevel:
        """Create a single overlay window."""
        # Create root window if needed
        if not hasattr(tk, '_default_root') or tk._default_root is None:
            root = tk.Tk()
            root.withdraw()
        
        # Create overlay window
        window = tk.Toplevel()
        
        # Configure window properties
        window.title("Security Reminder")
        window.configure(bg=self.config.background_color)
        
        # Make window fullscreen and topmost
        window.attributes('-fullscreen', True)
        window.attributes('-topmost', True)
        window.attributes('-alpha', 0.95)  # Slightly transparent
        
        # Position window on specific monitor
        if monitor:
            window.geometry(f"{monitor['width']}x{monitor['height']}+{monitor['x']}+{monitor['y']}")
        
        # Disable window decorations
        window.overrideredirect(True)
        
        # Setup content
        self._setup_window_content(window, is_primary)
        
        # Bind dismiss events
        self._bind_dismiss_events(window)
        
        # Focus and grab
        window.focus_force()
        window.grab_set()
        
        return window
    
    def _setup_window_content(self, window: tk.Toplevel, show_controls: bool) -> None:
        """Setup the content of an overlay window."""
        # Main frame
        main_frame = tk.Frame(window, bg=self.config.background_color)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Calculate font size based on screen size and config
        screen_width = window.winfo_screenwidth()
        base_font_size = max(24, int(screen_width / 60))  # Responsive font size
        font_size = int(base_font_size * self.config.font_scale)
        
        # Message label
        message_label = tk.Label(
            main_frame,
            text=self.message,
            font=(self.config.font_family, font_size, 'bold'),
            fg=self.config.text_color,
            bg=self.config.background_color,
            wraplength=int(screen_width * 0.8),  # Wrap text
            justify=tk.CENTER
        )
        message_label.pack(expand=True)
        
        # Control frame (only on primary window)
        if show_controls:
            control_frame = tk.Frame(main_frame, bg=self.config.background_color)
            control_frame.pack(side=tk.BOTTOM, pady=20)
            
            # Dismiss instruction
            dismiss_label = tk.Label(
                control_frame,
                text="Press any key, click, or move mouse to dismiss",
                font=(self.config.font_family, int(font_size * 0.4)),
                fg=self.config.text_color,
                bg=self.config.background_color
            )
            dismiss_label.pack(pady=10)
            
            # Report button (if enabled)
            if self.config.show_report_button and self.config.report_endpoint:
                report_button = tk.Button(
                    control_frame,
                    text="Report Security Incident",
                    font=(self.config.font_family, int(font_size * 0.3)),
                    command=self._handle_report,
                    bg='#FF4444',
                    fg='white',
                    relief=tk.RAISED,
                    bd=2
                )
                report_button.pack(pady=5)
    
    def _bind_dismiss_events(self, window: tk.Toplevel) -> None:
        """Bind events that should dismiss the overlay."""
        # Keyboard events
        window.bind('<KeyPress>', self._on_dismiss_event)
        window.bind('<Button-1>', self._on_dismiss_event)  # Left click
        window.bind('<Button-2>', self._on_dismiss_event)  # Middle click
        window.bind('<Button-3>', self._on_dismiss_event)  # Right click
        window.bind('<Motion>', self._on_dismiss_event)    # Mouse movement
        
        # Focus events
        window.bind('<FocusOut>', self._on_dismiss_event)
        
        # Make sure window can receive events
        window.focus_set()
    
    def _on_dismiss_event(self, event=None) -> None:
        """Handle dismiss events."""
        if not self.dismissed:
            self.dismissed = True
            logger.debug("Overlay dismissed by user input")
            self.dismiss()
    
    def _handle_report(self) -> None:
        """Handle security incident reporting."""
        try:
            if self.config.report_endpoint.startswith('mailto:'):
                # Email reporting
                webbrowser.open(self.config.report_endpoint)
            elif self.config.report_endpoint.startswith('http'):
                # Web-based reporting
                webbrowser.open(self.config.report_endpoint)
            else:
                logger.warning(f"Invalid report endpoint: {self.config.report_endpoint}")
            
            logger.info("Security incident report initiated")
            
        except Exception as e:
            logger.error(f"Failed to open report endpoint: {e}")
        
        # Dismiss overlay after reporting
        self.dismiss()
    
    def show(self) -> None:
        """Show the overlay."""
        try:
            for window in self.windows:
                window.deiconify()
                window.lift()
                window.focus_force()
            
            logger.debug("Security overlay displayed")
            
            # Text-to-speech if enabled
            if self.config.text_to_speech:
                self._speak_message()
                
        except Exception as e:
            logger.error(f"Failed to show overlay: {e}")
    
    def dismiss(self) -> None:
        """Dismiss the overlay."""
        try:
            for window in self.windows:
                window.grab_release()
                window.destroy()
            
            self.windows.clear()
            logger.debug("Security overlay dismissed")
            
            # Call dismiss callback
            if self.on_dismiss:
                self.on_dismiss()
                
        except Exception as e:
            logger.error(f"Failed to dismiss overlay: {e}")
    
    def _speak_message(self) -> None:
        """Speak the message using text-to-speech (if available)."""
        def speak():
            try:
                import platform
                import subprocess
                
                # Remove emojis for TTS
                clean_message = ''.join(char for char in self.message if ord(char) < 0x1F600 or ord(char) > 0x1F64F)
                
                system = platform.system()
                if system == "Windows":
                    # Use Windows SAPI
                    subprocess.run([
                        'powershell', '-Command',
                        f'Add-Type -AssemblyName System.Speech; '
                        f'$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
                        f'$speak.Speak("{clean_message}")'
                    ], check=False, capture_output=True)
                    
                elif system == "Darwin":
                    # Use macOS say command
                    subprocess.run(['say', clean_message], check=False, capture_output=True)
                    
                elif system == "Linux":
                    # Try espeak or festival
                    try:
                        subprocess.run(['espeak', clean_message], check=False, capture_output=True)
                    except FileNotFoundError:
                        try:
                            subprocess.run(['festival', '--tts'], input=clean_message.encode(), 
                                         check=False, capture_output=True)
                        except FileNotFoundError:
                            logger.warning("No TTS engine found on Linux")
                
            except Exception as e:
                logger.warning(f"Text-to-speech failed: {e}")
        
        # Run TTS in background thread
        tts_thread = threading.Thread(target=speak, daemon=True)
        tts_thread.start()


class OverlayManager:
    """Manages overlay display and lifecycle."""
    
    def __init__(self, config: Config):
        self.config = config
        self.current_overlay: Optional[SecurityOverlay] = None
        self._overlay_lock = threading.Lock()
    
    def show_overlay(self, message: str, on_dismiss: Optional[Callable] = None) -> None:
        """Show security overlay with message."""
        with self._overlay_lock:
            # Dismiss any existing overlay
            if self.current_overlay:
                self.current_overlay.dismiss()
            
            # Create and show new overlay
            try:
                self.current_overlay = SecurityOverlay(
                    self.config, 
                    message, 
                    self._on_overlay_dismissed
                )
                self.current_overlay.show()
                
                # Store dismiss callback
                self._dismiss_callback = on_dismiss
                
            except Exception as e:
                logger.error(f"Failed to show overlay: {e}")
                self.current_overlay = None
    
    def _on_overlay_dismissed(self) -> None:
        """Handle overlay dismissal."""
        with self._overlay_lock:
            self.current_overlay = None
            
            # Call external dismiss callback if set
            if hasattr(self, '_dismiss_callback') and self._dismiss_callback:
                try:
                    self._dismiss_callback()
                except Exception as e:
                    logger.error(f"Error in dismiss callback: {e}")
    
    def is_overlay_visible(self) -> bool:
        """Check if overlay is currently visible."""
        with self._overlay_lock:
            return self.current_overlay is not None
    
    def dismiss_overlay(self) -> None:
        """Manually dismiss current overlay."""
        with self._overlay_lock:
            if self.current_overlay:
                self.current_overlay.dismiss()
