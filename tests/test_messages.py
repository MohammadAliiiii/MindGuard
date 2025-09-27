"""Tests for message management."""

import pytest
import tempfile
from pathlib import Path

from idle_reminder.messages import MessageManager


class TestMessageManager:
    """Test message loading and rotation."""
    
    def test_load_messages_from_file(self):
        """Test loading messages from file."""
        messages = [
            "Test message 1",
            "Test message 2",
            "Test message 3"
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for msg in messages:
                f.write(f"{msg}\n")
            messages_path = Path(f.name)
        
        try:
            manager = MessageManager(str(messages_path))
            assert manager.get_message_count() == 3
        finally:
            messages_path.unlink()
    
    def test_load_messages_nonexistent_file(self):
        """Test loading messages from non-existent file."""
        manager = MessageManager("nonexistent.txt")
        assert manager.get_message_count() > 0  # Should use defaults
    
    def test_message_rotation(self):
        """Test message rotation without duplicates."""
        messages = [
            "Message A",
            "Message B", 
            "Message C"
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for msg in messages:
                f.write(f"{msg}\n")
            messages_path = Path(f.name)
        
        try:
            manager = MessageManager(str(messages_path))
            
            # Get all messages in one cycle
            received_messages = set()
            for _ in range(3):
                msg = manager.get_next_message()
                received_messages.add(msg)
            
            # Should have received all unique messages
            assert len(received_messages) == 3
            assert received_messages == set(messages)
        finally:
            messages_path.unlink()
    
    def test_message_cycle_reset(self):
        """Test that message cycle resets after completion."""
        messages = ["Message 1", "Message 2"]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for msg in messages:
                f.write(f"{msg}\n")
            messages_path = Path(f.name)
        
        try:
            manager = MessageManager(str(messages_path))
            
            # Complete one cycle
            for _ in range(2):
                manager.get_next_message()
            
            # Next message should start new cycle
            msg = manager.get_next_message()
            assert msg in messages
        finally:
            messages_path.unlink()
    
    def test_sanitize_messages(self):
        """Test message sanitization."""
        messages_with_control_chars = [
            "Normal message",
            "Message\x00with\x01control\x02chars",
            "Very " + "long " * 100 + "message"  # Over 500 chars
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for msg in messages_with_control_chars:
                f.write(f"{msg}\n")
            messages_path = Path(f.name)
        
        try:
            manager = MessageManager(str(messages_path))
            
            # Should have sanitized messages
            for _ in range(manager.get_message_count()):
                msg = manager.get_next_message()
                # Should not contain control characters
                assert '\x00' not in msg
                assert '\x01' not in msg
                assert '\x02' not in msg
                # Should be truncated if too long
                assert len(msg) <= 500
        finally:
            messages_path.unlink()
    
    def test_empty_file_handling(self):
        """Test handling of empty messages file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Write only whitespace
            f.write("   \n\n  \t  \n")
            messages_path = Path(f.name)
        
        try:
            manager = MessageManager(str(messages_path))
            # Should fall back to defaults
            assert manager.get_message_count() > 0
        finally:
            messages_path.unlink()
    
    def test_reload_messages(self):
        """Test reloading messages from file."""
        initial_messages = ["Initial message"]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for msg in initial_messages:
                f.write(f"{msg}\n")
            messages_path = Path(f.name)
        
        try:
            manager = MessageManager(str(messages_path))
            assert manager.get_message_count() == 1
            
            # Update file
            with open(messages_path, 'w') as f:
                f.write("New message 1\n")
                f.write("New message 2\n")
            
            # Reload
            manager.reload_messages()
            assert manager.get_message_count() == 2
        finally:
            messages_path.unlink()
    
    def test_random_message(self):
        """Test getting random message."""
        messages = ["Message A", "Message B", "Message C"]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for msg in messages:
                f.write(f"{msg}\n")
            messages_path = Path(f.name)
        
        try:
            manager = MessageManager(str(messages_path))
            
            # Get random messages - should be from available set
            for _ in range(10):
                msg = manager.get_random_message()
                assert msg in messages
        finally:
            messages_path.unlink()
    
    def test_validate_messages_file(self):
        """Test messages file validation."""
        # Valid file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("Test message\n")
            valid_path = Path(f.name)
        
        try:
            manager = MessageManager(str(valid_path))
            assert manager.validate_messages_file() is True
        finally:
            valid_path.unlink()
        
        # Invalid file (non-existent)
        manager = MessageManager("nonexistent.txt")
        assert manager.validate_messages_file() is False
