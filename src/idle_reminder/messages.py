"""Message management and rotation for security reminders."""

import logging
import random
from pathlib import Path
from typing import List, Optional
import re

logger = logging.getLogger(__name__)


class MessageManager:
    """Manages security reminder messages with rotation."""
    
    def __init__(self, messages_file: str):
        self.messages_file = Path(messages_file)
        self._messages: List[str] = []
        self._current_cycle: List[str] = []
        self._used_messages: set = set()
        self.load_messages()
    
    def load_messages(self) -> None:
        """Load messages from file."""
        try:
            if not self.messages_file.exists():
                logger.warning(f"Messages file {self.messages_file} not found, using default messages")
                self._messages = self._get_default_messages()
                return
            
            with open(self.messages_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Filter out empty lines and sanitize content
            messages = []
            for line in lines:
                line = line.strip()
                if line:
                    # Sanitize message - remove control characters but keep emojis
                    sanitized = self._sanitize_message(line)
                    if sanitized:
                        messages.append(sanitized)
            
            if not messages:
                logger.warning("No valid messages found, using defaults")
                self._messages = self._get_default_messages()
            else:
                self._messages = messages
                logger.info(f"Loaded {len(self._messages)} messages from {self.messages_file}")
            
            # Reset rotation cycle
            self._reset_cycle()
            
        except Exception as e:
            logger.error(f"Failed to load messages from {self.messages_file}: {e}")
            self._messages = self._get_default_messages()
            self._reset_cycle()
    
    def _sanitize_message(self, message: str) -> str:
        """Sanitize message content for safe display."""
        # Remove control characters except newlines and tabs
        # Keep Unicode characters (including emojis)
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', message)
        
        # Limit message length for display
        if len(sanitized) > 500:
            sanitized = sanitized[:497] + "..."
        
        return sanitized.strip()
    
    def _get_default_messages(self) -> List[str]:
        """Get default security messages if file is not available."""
        return [
    "🔒 Always lock your workstation before walking away",
    "🔐 Create strong, unique passwords — never reuse them",
    "📧 Stop. Inspect. Verify every email sender",
    "🌐 Browse only trusted sites; skip unknown links",
    "💾 Backup critical files regularly — data is gold",
    "🔄 Keep your software updated; patches block attackers",
    "📱 Turn on two-factor authentication everywhere you can",
    "🚫 Guard your credentials; they’re keys, not candy",
    "🔍 Suspicious? Report it to IT immediately",
    "💻 Install only approved software on company devices",
    "🕵️ Social engineers exploit trust — verify requests before acting",
    "⏱ Urgency is a weapon. Slow down, double-check",
    "☎️ Call back using known numbers, not the ones in the email",
    "🛑 If it feels off, it probably is — pause before clicking",
    "🧑‍🤝‍🧑 Security is teamwork: your caution protects everyone",
    "✈️ Traveling? Shield your screen and watch your surroundings",
    "🔦 Phishing hides in plain sight — hover over links before clicking",
    "📂 Sensitive data belongs in secure channels only",
    "🎯 Hackers aim for the easiest target — don’t be it",
    "🧩 Small mistakes create big breaches — stay alert",
    "🧟 Hackers love brains on autopilot — stay conscious",
    "🪤 Bait looks tasty… until the trap snaps. Don’t click blindly",
    "🧨 “Act fast!” usually means “Get hacked fast”",
    "🦊 Tricksters sound friendly. Processes keep you safe",
    "🧊 Chill. Verify. Security loves cool heads"
        ]
    
    def _reset_cycle(self) -> None:
        """Reset the message rotation cycle."""
        self._current_cycle = self._messages.copy()
        self._used_messages.clear()
        random.shuffle(self._current_cycle)
        logger.debug(f"Reset message cycle with {len(self._current_cycle)} messages")
    
    def get_next_message(self) -> str:
        """Get the next message in rotation."""
        if not self._messages:
            return "Security reminder: Stay vigilant and follow company policies."
        
        # If we've used all messages, start a new cycle
        if not self._current_cycle:
            self._reset_cycle()
        
        # Get next message from current cycle
        message = self._current_cycle.pop()
        self._used_messages.add(message)
        
        logger.debug(f"Selected message: {message[:50]}...")
        return message
    
    def get_random_message(self) -> str:
        """Get a random message (not part of rotation cycle)."""
        if not self._messages:
            return "Security reminder: Stay vigilant and follow company policies."
        
        return random.choice(self._messages)
    
    def get_message_count(self) -> int:
        """Get total number of available messages."""
        return len(self._messages)
    
    def reload_messages(self) -> None:
        """Reload messages from file."""
        logger.info("Reloading messages from file")
        self.load_messages()
    
    def validate_messages_file(self) -> bool:
        """Validate that the messages file exists and has valid content."""
        if not self.messages_file.exists():
            return False
        
        try:
            with open(self.messages_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return bool(content)
        except Exception:
            return False
