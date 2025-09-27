"""Logging configuration for Idle Security Reminder."""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from .config import Config


def setup_logging(config: Config) -> None:
    """Setup logging configuration."""
    # Convert log level string to logging constant
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if config.log_file:
        try:
            log_path = Path(config.log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert MB to bytes
            max_bytes = config.max_log_size_mb * 1024 * 1024
            
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_path,
                maxBytes=max_bytes,
                backupCount=3,
                encoding='utf-8'
            )
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            logging.warning(f"Failed to setup file logging: {e}")


class SecurityFilter(logging.Filter):
    """Filter to mask sensitive information in logs."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log record to mask sensitive data."""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            # Mask URLs except domain
            import re
            record.msg = re.sub(
                r'https?://([^/]+)/[^\s]*',
                r'https://\1/***',
                record.msg
            )
        return True
