"""
Base Watcher Class for AI Employee Silver Tier.

All watchers inherit from this base class to ensure consistent behavior
and interface across the perception layer.

Agent Skills Pattern: Each watcher exposes its read operations as skills.
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class BaseWatcher(ABC):
    """
    Abstract base class for all watchers in the AI Employee system.
    
    Watchers are the perception layer - they monitor external sources
    and create structured action files in the vault's Needs_Action folder.
    
    Agent Skills:
        - check_for_updates(): Check for new items from the source
        - create_action_file(): Create structured markdown file for AI processing
    """
    
    def __init__(
        self,
        vault_path: str | Path,
        check_interval: int = 60,
        name: str | None = None
    ):
        """
        Initialize the base watcher.
        
        Args:
            vault_path: Path to the AI Employee vault
            check_interval: Seconds between checks (default: 60)
            name: Watcher name (defaults to class name)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / "Needs_Action"
        self.check_interval = check_interval
        self.name = name or self.__class__.__name__
        self.logger = logging.getLogger(self.name)
        self.processed_ids: set[str] = set()
        self.is_running = False
        self._setup_logging()
        
    def _setup_logging(self) -> None:
        """Configure logging for the watcher."""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    @abstractmethod
    def check_for_updates(self) -> list[dict[str, Any]]:
        """
        Check for new items from the external source.
        
        Returns:
            List of new items to process, each as a dictionary with at least:
            - id: Unique identifier for the item
            - type: Source type (e.g., 'email', 'whatsapp', 'linkedin')
            - data: Item content/data
            
        Agent Skill: This method is exposed as a perception skill.
        """
        pass
    
    @abstractmethod
    def parse_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """
        Parse a raw item into a structured format.
        
        Args:
            item: Raw item data from the source
            
        Returns:
            Structured item data ready for action file creation
            
        Agent Skill: This method is exposed as a parsing skill.
        """
        pass
    
    @abstractmethod
    def create_action_file(self, item: dict[str, Any]) -> Path:
        """
        Create a structured markdown action file in Needs_Action folder.
        
        Args:
            item: Parsed item data
            
        Returns:
            Path to the created action file
            
        Agent Skill: This method is exposed as a file creation skill.
        
        File Format:
        ```markdown
        ---
        type: <item_type>
        source: <source_name>
        id: <unique_id>
        received: <ISO_timestamp>
        priority: <high|medium|low>
        status: pending
        ---
        
        ## Content
        <item content>
        
        ## Suggested Actions
        - [ ] Action 1
        - [ ] Action 2
        ```
        """
        pass
    
    def _ensure_directories(self) -> None:
        """Ensure the Needs_Action directory structure exists."""
        self.needs_action.mkdir(parents=True, exist_ok=True)
        # Create source-specific subdirectories
        for source in ["Gmail", "WhatsApp", "LinkedIn", "FileDrop", "Finance"]:
            (self.needs_action / source).mkdir(exist_ok=True)
    
    def _generate_filename(
        self,
        source: str,
        item_id: str,
        prefix: str = ""
    ) -> str:
        """
        Generate a unique filename for an action file.
        
        Args:
            source: Source name (e.g., 'Gmail', 'WhatsApp')
            item_id: Unique item identifier
            prefix: Optional prefix for the filename
            
        Returns:
            Filename with .md extension
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_id = "".join(
            c for c in (item_id[:50] if item_id else "unknown")
            if c.isalnum() or c in "-_"
        ).strip()
        
        if prefix:
            return f"{prefix}_{source}_{safe_id}_{timestamp}.md"
        return f"{source}_{safe_id}_{timestamp}.md"
    
    def _create_action_file_content(
        self,
        item: dict[str, Any],
        content: str,
        suggested_actions: list[str] | None = None
    ) -> str:
        """
        Create the markdown content for an action file.
        
        Args:
            item: Parsed item data (must include type, id, priority)
            content: Main content body
            suggested_actions: List of suggested action items
            
        Returns:
            Complete markdown content string
        """
        timestamp = datetime.now().isoformat()
        
        # Build YAML frontmatter
        frontmatter = f"""---
type: {item.get('type', 'unknown')}
source: {item.get('source', self.name)}
id: {item.get('id', 'unknown')}
received: {timestamp}
priority: {item.get('priority', 'medium')}
status: pending
"""
        
        # Add optional fields
        if 'from' in item:
            frontmatter += f"from: {item['from']}\n"
        if 'subject' in item:
            frontmatter += f"subject: {item['subject']}\n"
        if 'keywords' in item:
            frontmatter += f"keywords: {', '.join(item['keywords'])}\n"
            
        frontmatter += "---\n\n"
        
        # Build body
        body = f"## Content\n\n{content}\n\n"
        
        # Add suggested actions
        if suggested_actions:
            body += "## Suggested Actions\n\n"
            for action in suggested_actions:
                body += f"- [ ] {action}\n"
        else:
            body += "## Suggested Actions\n\n"
            body += "- [ ] Review and categorize\n"
            body += "- [ ] Create action plan\n"
            body += "- [ ] Execute or delegate\n"
        
        # Add processing notes
        body += "\n\n## Processing Notes\n\n"
        body += f"- Received by: {self.name}\n"
        body += f"- Timestamp: {timestamp}\n"
        body += "- Status: Awaiting AI processing\n"
        
        return frontmatter + body
    
    def mark_processed(self, item_id: str) -> None:
        """
        Mark an item as processed to avoid duplicates.
        
        Args:
            item_id: Unique identifier of the item
        """
        self.processed_ids.add(item_id)
        self.logger.debug(f"Marked item {item_id} as processed")
    
    def is_processed(self, item_id: str) -> bool:
        """
        Check if an item has already been processed.
        
        Args:
            item_id: Unique identifier of the item
            
        Returns:
            True if item has been processed, False otherwise
        """
        return item_id in self.processed_ids
    
    def clear_processed_cache(self) -> None:
        """Clear the processed items cache."""
        self.processed_ids.clear()
        self.logger.info("Cleared processed items cache")
    
    @abstractmethod
    def mark_as_read(self, item: dict[str, Any]) -> None:
        """
        Mark the item as read in the source system.
        
        Args:
            item: Item to mark as read
            
        This should be implemented by each watcher to handle
        source-specific read marking (e.g., Gmail API, WhatsApp session).
        """
        pass
    
    def run(self) -> None:
        """
        Run the watcher in a continuous loop.
        
        This is the main entry point for running a watcher.
        It will continuously check for updates and create action files.
        
        Agent Skill: This method orchestrates the perception workflow.
        """
        self.is_running = True
        self._ensure_directories()
        self.logger.info(f"Starting {self.name} (interval: {self.check_interval}s)")
        
        try:
            while self.is_running:
                try:
                    items = self.check_for_updates()
                    
                    for item in items:
                        item_id = item.get('id')
                        
                        if item_id and self.is_processed(item_id):
                            self.logger.debug(f"Skipping already processed: {item_id}")
                            continue
                        
                        # Parse the item
                        parsed_item = self.parse_item(item)
                        
                        # Create action file
                        action_file = self.create_action_file(parsed_item)
                        self.logger.info(f"Created action file: {action_file.name}")
                        
                        # Mark as processed
                        if item_id:
                            self.mark_processed(item_id)
                        
                        # Mark as read in source
                        self.mark_as_read(item)
                    
                except Exception as e:
                    self.logger.error(f"Error processing items: {e}", exc_info=True)
                    # Backoff on error
                    time.sleep(5)
                
                # Wait for next check
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info(f"{self.name} stopped by user")
        finally:
            self.is_running = False
            self.logger.info(f"{self.name} stopped")
    
    def stop(self) -> None:
        """Stop the watcher loop."""
        self.is_running = False
        self.logger.info(f"Stopping {self.name}")
    
    # =========================================================================
    # Agent Skills Interface
    # =========================================================================
    
    def get_skills(self) -> dict[str, callable]:
        """
        Return a dictionary of skills exposed by this watcher.
        
        Returns:
            Dictionary mapping skill names to callable functions
            
        Example:
            {
                'check_updates': self.check_for_updates,
                'create_action_file': self.create_action_file,
                'mark_processed': self.mark_processed,
            }
        """
        return {
            f"{self.name.lower()}.check_updates": self.check_for_updates,
            f"{self.name.lower()}.create_action_file": self.create_action_file,
            f"{self.name.lower()}.mark_processed": self.mark_processed,
        }
