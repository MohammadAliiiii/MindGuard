"""Pytest configuration and fixtures."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

from idle_reminder.config import Config


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    config_data = """
idle_seconds: 120
messages_file: "test_messages.txt"
theme: "light"
log_level: "INFO"
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_data)
        config_path = Path(f.name)
    
    yield config_path
    
    # Cleanup
    if config_path.exists():
        config_path.unlink()


@pytest.fixture
def temp_messages_file():
    """Create a temporary messages file for testing."""
    messages = [
        "Test security message 1",
        "Test security message 2", 
        "Test security message 3"
    ]
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        for msg in messages:
            f.write(f"{msg}\n")
        messages_path = Path(f.name)
    
    yield messages_path, messages
    
    # Cleanup
    if messages_path.exists():
        messages_path.unlink()


@pytest.fixture
def default_config():
    """Provide a default configuration for testing."""
    return Config()


@pytest.fixture
def mock_idle_detector():
    """Provide a mock idle detector."""
    detector = Mock()
    detector.is_available.return_value = True
    detector.get_idle_time.return_value = 0.0
    return detector


@pytest.fixture
def mock_overlay_manager():
    """Provide a mock overlay manager."""
    manager = Mock()
    manager.is_overlay_visible.return_value = False
    return manager
