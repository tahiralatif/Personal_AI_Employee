"""
Watcher modules for AI Employee Silver Tier.

Watchers are the perception layer of the AI Employee system.
They monitor external sources and create action files in the vault.

Agent Skills Pattern: Each watcher exposes its operations as skills.

Available Watchers:
    - GmailWatcher: Monitor Gmail for important emails
    - WhatsAppWatcher: Monitor WhatsApp for urgent messages
    - LinkedInWatcher: Monitor LinkedIn for business opportunities
    - FileSystemWatcher: Monitor Inbox folder for file drops
"""

from .base_watcher import BaseWatcher
from .gmail_watcher import GmailWatcher
from .whatsapp_watcher import WhatsAppWatcher
from .linkedin_watcher import LinkedInWatcher
from .file_system_watcher import FileSystemWatcher

__all__ = [
    "BaseWatcher",
    "GmailWatcher",
    "WhatsAppWatcher",
    "LinkedInWatcher",
    "FileSystemWatcher",
]
