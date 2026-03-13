"""
Init file for the watchers module.

This module contains all the watcher implementations for the AI Employee system.
"""

from .base_watcher import BaseWatcher
from .gmail_watcher import GmailWatcher, create_gmail_watcher

__all__ = [
    'BaseWatcher',
    'GmailWatcher',
    'create_gmail_watcher'
]