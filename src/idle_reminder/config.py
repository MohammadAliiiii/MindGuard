"""Configuration management for Idle Security Reminder."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


@dataclass
class Config:
    """Application configuration."""
    
    # Idle detection
    idle_seconds: int = 120
    check_interval_ms: int = 1000
    
    # Messages
    messages_file: str = "messages.txt"
    
    # Visual appearance
    theme: str = "light"
    background_color: str = "#000000"
    text_color: str = "#FFFFFF"
    font_family: str = "Arial"
    font_scale: float = 1.0
    
    # Reporting
    show_report_button: bool = False
    report_endpoint: str = ""
    
    # System integration
    start_on_boot: bool = False
    
    # Accessibility
    high_contrast_mode: bool = False
    text_to_speech: bool = False
    respect_system_scaling: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "idle_reminder.log"
    max_log_size_mb: int = 5
    
    # Multi-monitor
    multi_monitor: bool = True
    
    # Security
    allow_local_network_reporting: bool = False
    
    # Theme definitions
    themes: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
        "light": {
            "background_color": "#F0F0F0",
            "text_color": "#000000"
        },
        "dark": {
            "background_color": "#1E1E1E",
            "text_color": "#FFFFFF"
        },
        "high_contrast": {
            "background_color": "#000000",
            "text_color": "#FFFF00"
        }
    })
    
    @classmethod
    def load(cls, config_path: Path) -> "Config":
        """Load configuration from YAML file."""
        config = cls()
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f) or {}
                
                # Update config with loaded data
                for key, value in data.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
                
                # Apply theme colors if theme is specified
                if config.theme in config.themes:
                    theme_colors = config.themes[config.theme]
                    if 'background_color' not in data:
                        config.background_color = theme_colors['background_color']
                    if 'text_color' not in data:
                        config.text_color = theme_colors['text_color']
                
            except Exception as e:
                logging.warning(f"Failed to load config from {config_path}: {e}")
        
        return config
    
    def save(self, config_path: Path) -> None:
        """Save configuration to YAML file."""
        data = {
            'idle_seconds': self.idle_seconds,
            'messages_file': self.messages_file,
            'theme': self.theme,
            'background_color': self.background_color,
            'text_color': self.text_color,
            'font_family': self.font_family,
            'font_scale': self.font_scale,
            'show_report_button': self.show_report_button,
            'report_endpoint': self.report_endpoint,
            'start_on_boot': self.start_on_boot,
            'high_contrast_mode': self.high_contrast_mode,
            'text_to_speech': self.text_to_speech,
            'respect_system_scaling': self.respect_system_scaling,
            'log_level': self.log_level,
            'log_file': self.log_file,
            'max_log_size_mb': self.max_log_size_mb,
            'multi_monitor': self.multi_monitor,
            'check_interval_ms': self.check_interval_ms,
            'allow_local_network_reporting': self.allow_local_network_reporting
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, indent=2)
        except Exception as e:
            logging.error(f"Failed to save config to {config_path}: {e}")
    
    def validate(self) -> bool:
        """Validate configuration values."""
        errors = []
        
        if self.idle_seconds < 10:
            errors.append("idle_seconds must be at least 10")
        
        if self.check_interval_ms < 100:
            errors.append("check_interval_ms must be at least 100")
        
        if self.font_scale <= 0:
            errors.append("font_scale must be positive")
        
        if self.max_log_size_mb <= 0:
            errors.append("max_log_size_mb must be positive")
        
        if self.report_endpoint and not self.report_endpoint.startswith('https://'):
            if not (self.allow_local_network_reporting and 
                   (self.report_endpoint.startswith('http://localhost') or 
                    self.report_endpoint.startswith('http://127.0.0.1'))):
                errors.append("report_endpoint must use HTTPS or be localhost with allow_local_network_reporting=true")
        
        if errors:
            for error in errors:
                logging.error(f"Config validation error: {error}")
            return False
        
        return True
