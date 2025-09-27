#!/usr/bin/env python3
"""Main entry point for the Idle Security Reminder application."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .app import IdleReminderApp
from .config import Config
from .logger import setup_logging
from .diagnostics import generate_diagnostics


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Idle Security Reminder - Desktop security awareness tool"
    )
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        default="config.yaml",
        help="Path to configuration file (default: config.yaml)"
    )
    
    parser.add_argument(
        "--idle", "-i",
        type=int,
        help="Idle timeout in seconds (overrides config)"
    )
    
    parser.add_argument(
        "--messages", "-m",
        type=str,
        help="Path to messages file (overrides config)"
    )
    
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode (no GUI, testing only)"
    )
    
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Generate diagnostics file and exit"
    )
    
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="%(prog)s 1.0.0"
    )
    
    return parser.parse_args()


def main() -> int:
    """Main application entry point."""
    try:
        args = parse_arguments()
        
        # Handle diagnostics mode
        if args.diagnostics:
            config_path = Path(args.config)
            generate_diagnostics(config_path)
            print("Diagnostics written to diagnostics.json")
            return 0
        
        # Load configuration
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Warning: Config file {config_path} not found, using defaults")
        
        config = Config.load(config_path)
        
        # Apply command line overrides
        if args.idle:
            config.idle_seconds = args.idle
        if args.messages:
            config.messages_file = args.messages
        if args.debug:
            config.log_level = "DEBUG"
        
        # Setup logging
        setup_logging(config)
        logger = logging.getLogger(__name__)
        
        logger.info("Starting Idle Security Reminder v1.0.0")
        logger.info(f"Config loaded from: {config_path}")
        logger.info(f"Idle timeout: {config.idle_seconds} seconds")
        
        # Create and run application
        app = IdleReminderApp(config, headless=args.headless)
        return app.run()
        
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.getLogger(__name__).exception("Fatal error occurred")
        return 1


if __name__ == "__main__":
    sys.exit(main())
