"""
Watcher Coordinator for AI Employee Silver Tier.

Coordinates multiple watchers and integrates with the orchestrator.
Provides unified interface for starting, stopping, and monitoring all watchers.

Agent Skills:
    - watcher.start_all(): Start all watchers
    - watcher.stop_all(): Stop all watchers
    - watcher.get_status(): Get watcher status
"""

import logging
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

from .gmail_watcher import GmailWatcher
from .whatsapp_watcher import WhatsAppWatcher
from .linkedin_watcher import LinkedInWatcher
from .file_system_watcher import FileSystemWatcher
from ..config.settings import get_settings
from ..utils.logger import get_logger


class WatcherCoordinator:
    """
    Coordinates all watchers in the AI Employee system.
    
    Responsibilities:
    - Initialize all watchers
    - Start/stop watchers
    - Monitor watcher health
    - Expose unified Agent Skills interface
    """
    
    def __init__(
        self,
        vault_path: str | Path,
        enable_gmail: bool = True,
        enable_whatsapp: bool = True,
        enable_linkedin: bool = True,
        enable_filesystem: bool = True
    ):
        """
        Initialize Watcher Coordinator.
        
        Args:
            vault_path: Path to the AI Employee vault
            enable_gmail: Enable Gmail watcher
            enable_whatsapp: Enable WhatsApp watcher
            enable_linkedin: Enable LinkedIn watcher
            enable_filesystem: Enable file system watcher
        """
        self.vault_path = Path(vault_path)
        self.settings = get_settings()
        self.logger = get_logger()
        
        # Watcher configuration
        self.enable_gmail = enable_gmail
        self.enable_whatsapp = enable_whatsapp
        self.enable_linkedin = enable_linkedin
        self.enable_filesystem = enable_filesystem
        
        # Initialize watchers
        self.watchers: Dict[str, Any] = {}
        self.threads: Dict[str, threading.Thread] = {}
        self._initialize_watchers()
    
    def _initialize_watchers(self) -> None:
        """Initialize all enabled watchers."""
        try:
            # Gmail Watcher
            if self.enable_gmail and self.settings.is_gmail_configured():
                self.watchers['gmail'] = GmailWatcher(
                    vault_path=self.vault_path,
                    check_interval=self.settings.GMAIL_POLL_INTERVAL
                )
                self.logger.info("Gmail watcher initialized")
            elif self.enable_gmail:
                self.logger.warning("Gmail watcher disabled: credentials not configured")
            
            # WhatsApp Watcher
            if self.enable_whatsapp:
                self.watchers['whatsapp'] = WhatsAppWatcher(
                    vault_path=self.vault_path,
                    check_interval=30  # 30 seconds
                )
                self.logger.info("WhatsApp watcher initialized")
            
            # LinkedIn Watcher
            if self.enable_linkedin and self.settings.is_linkedin_configured():
                self.watchers['linkedin'] = LinkedInWatcher(
                    vault_path=self.vault_path,
                    check_interval=300  # 5 minutes (rate limiting)
                )
                self.logger.info("LinkedIn watcher initialized")
            elif self.enable_linkedin:
                self.logger.warning("LinkedIn watcher disabled: credentials not configured")
            
            # File System Watcher
            if self.enable_filesystem:
                self.watchers['filesystem'] = FileSystemWatcher(
                    vault_path=self.vault_path
                )
                self.logger.info("File system watcher initialized")
            
            self.logger.info(f"Initialized {len(self.watchers)} watchers")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize watchers: {e}")
    
    def start_all(self) -> None:
        """Start all watchers in separate threads."""
        try:
            for name, watcher in self.watchers.items():
                self._start_watcher(name, watcher)
            
            self.logger.info("All watchers started")
            
        except Exception as e:
            self.logger.error(f"Failed to start watchers: {e}")
    
    def _start_watcher(self, name: str, watcher) -> None:
        """
        Start a single watcher in a thread.
        
        Args:
            name: Watcher name
            watcher: Watcher instance
        """
        try:
            # File system watcher uses observer pattern
            if name == 'filesystem':
                watcher.start()
            else:
                # Other watchers use run_forever()
                thread = threading.Thread(
                    target=watcher.run_forever,
                    name=f"{name}_watcher",
                    daemon=True
                )
                thread.start()
                self.threads[name] = thread
            
            self.logger.info(f"{name} watcher started")
            
        except Exception as e:
            self.logger.error(f"Failed to start {name} watcher: {e}")
    
    def stop_all(self) -> None:
        """Stop all watchers."""
        try:
            for name, watcher in self.watchers.items():
                self._stop_watcher(name, watcher)
            
            self.logger.info("All watchers stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop watchers: {e}")
    
    def _stop_watcher(self, name: str, watcher) -> None:
        """
        Stop a single watcher.
        
        Args:
            name: Watcher name
            watcher: Watcher instance
        """
        try:
            if name == 'filesystem':
                watcher.stop()
            else:
                watcher.stop()
                if name in self.threads:
                    self.threads[name].join(timeout=5)
            
            self.logger.info(f"{name} watcher stopped")
            
        except Exception as e:
            self.logger.error(f"Failed to stop {name} watcher: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get status of all watchers.
        
        Returns:
            Dictionary with watcher statuses
        """
        status = {
            'timestamp': datetime.now().isoformat(),
            'watchers': {}
        }
        
        for name, watcher in self.watchers.items():
            status['watchers'][name] = {
                'enabled': True,
                'running': watcher.is_running,
                'processed_count': len(watcher.processed_ids),
                'check_interval': watcher.check_interval
            }
        
        status['total_watchers'] = len(self.watchers)
        status['active_watchers'] = sum(1 for w in self.watchers.values() if w.is_running)
        
        return status
    
    def get_all_skills(self) -> Dict[str, callable]:
        """
        Get all Agent Skills from all watchers.
        
        Returns:
            Dictionary of all watcher skills
        """
        all_skills = {}
        
        for name, watcher in self.watchers.items():
            skills = watcher.get_skills()
            all_skills.update(skills)
        
        # Add coordinator skills
        coordinator_skills = {
            'watcher.start_all': self.start_all,
            'watcher.stop_all': self.stop_all,
            'watcher.get_status': self.get_status,
        }
        all_skills.update(coordinator_skills)
        
        return all_skills
    
    def __enter__(self):
        """Context manager entry."""
        self.start_all()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_all()


def create_watcher_coordinator(
    vault_path: str | Path,
    **kwargs
) -> WatcherCoordinator:
    """
    Factory function to create WatcherCoordinator.
    
    Args:
        vault_path: Path to AI Employee vault
        **kwargs: Additional configuration options
        
    Returns:
        Configured WatcherCoordinator instance
    """
    return WatcherCoordinator(vault_path, **kwargs)


if __name__ == "__main__":
    # Example usage
    print("=== Watcher Coordinator Test ===\n")
    
    settings = get_settings()
    vault_path = settings.VAULT_PATH
    
    # Create coordinator
    coordinator = create_watcher_coordinator(vault_path)
    
    # Get status
    status = coordinator.get_status()
    print(f"Total watchers: {status['total_watchers']}")
    print(f"Active watchers: {status['active_watchers']}")
    
    # Get skills
    skills = coordinator.get_all_skills()
    print(f"\nAvailable Agent Skills: {len(skills)}")
    for skill_name in sorted(skills.keys()):
        print(f"  - {skill_name}")
    
    print("\n=== Test Complete ===")
