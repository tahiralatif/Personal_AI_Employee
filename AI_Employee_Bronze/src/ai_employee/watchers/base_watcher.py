"""
Base Watcher class for all watcher implementations.

This module provides the abstract base class that all specific watchers
(Gmail, WhatsApp, LinkedIn, File System) will inherit from.
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseWatcher(ABC):
    """
    Abstract base class for all watchers in the AI Employee system.

    All specific watchers (Gmail, WhatsApp, LinkedIn, File System) should
    inherit from this class and implement the abstract methods.
    """

    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the BaseWatcher.

        Args:
            vault_path: Path to the vault directory
            check_interval: Time interval (in seconds) between checks
        """
        self.vault_path = Path(vault_path).expanduser()
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.logger = logging.getLogger(self.__class__.__name__)
        self.processed_ids = set()

        # Create necessary directories if they don't exist
        self.needs_action.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def check_for_updates(self) -> List[Dict[str, Any]]:
        """
        Check for new updates/items to process.

        Returns:
            List of dictionaries containing information about new items to process
        """
        pass

    @abstractmethod
    def create_action_file(self, item: Dict[str, Any]) -> Path:
        """
        Create an action file in the Needs_Action folder for a given item.

        Args:
            item: Dictionary containing item information

        Returns:
            Path to the created action file
        """
        pass

    def run(self):
        """
        Main run loop that continuously checks for updates.

        This method should be called to start the watcher.
        """
        self.logger.info(f'Starting {self.__class__.__name__}')
        while True:
            try:
                items = self.check_for_updates()
                for item in items:
                    if item.get('id') not in self.processed_ids:
                        self.create_action_file(item)
                        self.processed_ids.add(item.get('id', ''))

            except Exception as e:
                self.logger.error(f'Error in {self.__class__.__name__}: {e}')
                # Exponential backoff on error
                time.sleep(min(self.check_interval * 2, 300))  # Max 5 minutes
            else:
                # Normal sleep interval
                time.sleep(self.check_interval)

    def _create_structured_action_file(
        self,
        filename: str,
        content: str,
        category: str = "General"
    ) -> Path:
        """
        Helper method to create a structured action file with consistent format.

        Args:
            filename: Name for the action file
            content: Content to write to the file
            category: Category for the action file (e.g., "Gmail", "WhatsApp", "LinkedIn")

        Returns:
            Path to the created action file
        """
        # Ensure category subfolder exists
        category_path = self.needs_action / category
        category_path.mkdir(exist_ok=True)

        # Create the action file path
        action_file_path = category_path / filename

        # Write the content to the file
        with open(action_file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return action_file_path