"""Tests for configuration management."""

import pytest
import tempfile
from pathlib import Path
import yaml

from idle_reminder.config import Config


class TestConfig:
    """Test configuration loading and validation."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = Config()
        
        assert config.idle_seconds == 120
        assert config.messages_file == "messages.txt"
        assert config.theme == "light"
        assert config.log_level == "INFO"
        assert config.multi_monitor is True
        assert config.show_report_button is False
    
    def test_load_valid_config(self):
        """Test loading valid configuration from file."""
        config_data = {
            'idle_seconds': 300,
            'messages_file': 'custom_messages.txt',
            'theme': 'dark',
            'log_level': 'DEBUG'
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            config = Config.load(config_path)
            
            assert config.idle_seconds == 300
            assert config.messages_file == 'custom_messages.txt'
            assert config.theme == 'dark'
            assert config.log_level == 'DEBUG'
        finally:
            config_path.unlink()
    
    def test_load_nonexistent_config(self):
        """Test loading configuration from non-existent file."""
        config_path = Path('nonexistent.yaml')
        config = Config.load(config_path)
        
        # Should use defaults
        assert config.idle_seconds == 120
        assert config.messages_file == "messages.txt"
    
    def test_theme_application(self):
        """Test theme color application."""
        config_data = {'theme': 'high_contrast'}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            config = Config.load(config_path)
            
            assert config.theme == 'high_contrast'
            assert config.background_color == '#000000'
            assert config.text_color == '#FFFF00'
        finally:
            config_path.unlink()
    
    def test_save_config(self):
        """Test saving configuration to file."""
        config = Config()
        config.idle_seconds = 180
        config.theme = 'dark'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_path = Path(f.name)
        
        try:
            config.save(config_path)
            
            # Load and verify
            loaded_config = Config.load(config_path)
            assert loaded_config.idle_seconds == 180
            assert loaded_config.theme == 'dark'
        finally:
            if config_path.exists():
                config_path.unlink()
    
    def test_config_validation_valid(self):
        """Test validation of valid configuration."""
        config = Config()
        assert config.validate() is True
    
    def test_config_validation_invalid_idle_seconds(self):
        """Test validation with invalid idle_seconds."""
        config = Config()
        config.idle_seconds = 5  # Too low
        assert config.validate() is False
    
    def test_config_validation_invalid_font_scale(self):
        """Test validation with invalid font_scale."""
        config = Config()
        config.font_scale = 0  # Must be positive
        assert config.validate() is False
    
    def test_config_validation_invalid_report_endpoint(self):
        """Test validation with invalid report endpoint."""
        config = Config()
        config.report_endpoint = "http://example.com"  # Should be HTTPS
        assert config.validate() is False
    
    def test_config_validation_localhost_endpoint(self):
        """Test validation with localhost endpoint."""
        config = Config()
        config.report_endpoint = "http://localhost:8080"
        config.allow_local_network_reporting = True
        assert config.validate() is True
