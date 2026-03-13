"""
Gmail Watcher for AI Employee Silver Tier.

This watcher monitors Gmail for new important emails and creates action files.
It inherits from BaseWatcher and wraps the existing Gmail integration.

Agent Skills:
    - gmail.check_updates(): Check for new emails
    - gmail.create_action_file(): Create action file for email
    - gmail.mark_processed(): Mark email as processed
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from .base_watcher import BaseWatcher
from ..integrations.gmail_watcher import GmailWatcher as ExistingGmailWatcher
from ..config.settings import Settings, get_settings
from ..utils.logger import get_logger


class GmailWatcher(BaseWatcher):
    """
    Gmail watcher implementing the BaseWatcher interface.
    
    This class wraps the existing Gmail integration and provides
    a consistent interface for the AI Employee system.
    """
    
    def __init__(
        self,
        vault_path: str | Path,
        check_interval: int = 120,  # 2 minutes
        name: str = "GmailWatcher"
    ):
        """
        Initialize Gmail Watcher.
        
        Args:
            vault_path: Path to the AI Employee vault
            check_interval: Seconds between checks (default: 120)
            name: Watcher name
        """
        super().__init__(vault_path, check_interval, name)
        
        # Create existing Gmail watcher
        self.settings = get_settings()
        self.existing_watcher = ExistingGmailWatcher(
            settings=self.settings,
            logger=get_logger()
        )
        
        # Priority keywords for classification
        self.priority_keywords = {
            'high': ['urgent', 'asap', 'emergency', 'critical', 'important', 'priority'],
            'medium': ['action required', 'review', 'approval', 'deadline'],
            'low': ['info', 'notification', 'update', 'newsletter']
        }
    
    def check_for_updates(self) -> list[dict[str, Any]]:
        """
        Check for new important emails.
        
        Returns:
            List of new email items to process
        """
        try:
            # Authenticate if needed
            if not self.existing_watcher.service:
                if not self.existing_watcher.authenticate():
                    self.logger.error("Gmail authentication failed")
                    return []
            
            # Fetch messages using existing watcher
            messages = self.existing_watcher.fetch_messages(max_results=10)
            
            # Convert to standard format
            items = []
            for msg in messages:
                items.append({
                    'id': msg.message_id,
                    'type': 'email',
                    'source': 'Gmail',
                    'data': msg,
                    'priority': self._classify_priority(msg.subject, msg.body)
                })
            
            self.logger.info(f"Found {len(items)} new emails")
            return items
            
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            return []
    
    def parse_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """
        Parse email item into structured format.
        
        Args:
            item: Email item from check_for_updates
            
        Returns:
            Structured email data
        """
        msg = item['data']
        
        return {
            'id': item['id'],
            'type': 'email',
            'source': 'Gmail',
            'from': msg.sender,
            'subject': msg.subject,
            'date': msg.date.isoformat() if msg.date else datetime.now().isoformat(),
            'body': msg.body,
            'has_attachments': msg.has_attachments(),
            'attachments': [
                {
                    'filename': att.filename,
                    'size': att.size,
                    'mime_type': att.mime_type
                }
                for att in msg.attachments
            ],
            'priority': item.get('priority', 'medium'),
            'thread_id': msg.thread_id
        }
    
    def create_action_file(self, item: dict[str, Any]) -> Path:
        """
        Create action file for email in Needs_Action/Gmail/.
        
        Args:
            item: Parsed email data
            
        Returns:
            Path to created action file
        """
        try:
            # Ensure directory exists
            gmail_dir = self.needs_action / "Gmail"
            gmail_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_subject = self._sanitize_string(item['subject'])[:50] or "NoSubject"
            filename = f"EMAIL_{timestamp}_{safe_subject}.md"
            filepath = gmail_dir / filename
            
            # Build content
            content = self._build_action_file_content(item)
            
            # Write file
            filepath.write_text(content, encoding='utf-8')
            
            self.logger.info(f"Created action file: {filename}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            # Fallback to generic filename
            fallback_path = self.needs_action / "Gmail" / f"EMAIL_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            fallback_path.write_text(f"# Error creating action file\n\nError: {e}\n", encoding='utf-8')
            return fallback_path
    
    def _build_action_file_content(self, item: dict[str, Any]) -> str:
        """
        Build markdown content for action file.
        
        Args:
            item: Parsed email data
            
        Returns:
            Markdown content string
        """
        # YAML frontmatter
        frontmatter = f"""---
type: email
source: Gmail
id: {item['id']}
from: {item['from']}
subject: {item['subject']}
received: {item['date']}
priority: {item['priority']}
status: pending
has_attachments: {str(item['has_attachments']).lower()}
---

# Email: {item['subject']}

## Details
- **From:** {item['from']}
- **Received:** {item['date']}
- **Priority:** {item['priority'].upper()}

## Content

{item['body'] if item['body'] else '*No plain text content available*'}

## Attachments
{self._format_attachments(item['attachments'])}

## Suggested Actions
- [ ] Review email content
- [ ] {self._suggest_action(item)}
- [ ] Create plan if needed
- [ ] Move to /Done/ when complete

---
*Generated by AI Employee Silver Tier - Gmail Watcher*
"""
        return frontmatter
    
    def _format_attachments(self, attachments: list[dict]) -> str:
        """Format attachments list."""
        if not attachments:
            return "- No attachments"
        
        lines = []
        for att in attachments:
            lines.append(f"- 📎 `{att['filename']}` ({self._format_size(att['size'])})")
        return "\n".join(lines)
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f}{unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f}TB"
    
    def _suggest_action(self, item: dict[str, Any]) -> str:
        """Suggest action based on email content."""
        if item['has_attachments']:
            return "Process attachments"
        
        body_lower = (item.get('body') or '').lower()
        if 'question' in body_lower or '?' in item['subject']:
            return "Reply to sender"
        elif 'forward' in body_lower or 'FYI' in item['subject']:
            return "Forward to relevant party"
        else:
            return "Archive after processing"
    
    def _classify_priority(self, subject: str, body: str) -> str:
        """
        Classify email priority based on keywords.
        
        Args:
            subject: Email subject
            body: Email body
            
        Returns:
            Priority level: 'high', 'medium', or 'low'
        """
        text = f"{subject} {body}".lower()
        
        # Check high priority
        for keyword in self.priority_keywords['high']:
            if keyword in text:
                return 'high'
        
        # Check medium priority
        for keyword in self.priority_keywords['medium']:
            if keyword in text:
                return 'medium'
        
        # Check low priority
        for keyword in self.priority_keywords['low']:
            if keyword in text:
                return 'low'
        
        return 'medium'  # Default
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string for filename."""
        if not text:
            return ""
        # Remove/replace unsafe characters
        unsafe = '<>:"/\\|?*'
        for char in unsafe:
            text = text.replace(char, '_')
        return text.strip(' _.')
    
    def mark_as_read(self, item: dict[str, Any]) -> None:
        """
        Mark email as read in Gmail.
        
        Args:
            item: Email item to mark as read
        """
        try:
            # Use existing watcher to mark as read
            # Note: Current implementation doesn't have this method
            # Would need to add: self.existing_watcher.mark_as_read(item['id'])
            self.logger.debug(f"Email {item['id']} processed (mark as read not implemented)")
        except Exception as e:
            self.logger.error(f"Error marking email as read: {e}")
    
    def get_skills(self) -> dict[str, callable]:
        """
        Return Agent Skills exposed by this watcher.
        
        Returns:
            Dictionary of skill names to callables
        """
        base_skills = super().get_skills()
        
        # Add Gmail-specific skills
        gmail_skills = {
            'gmail.check_emails': self.check_for_updates,
            'gmail.parse_email': self.parse_item,
            'gmail.create_email_action': self.create_action_file,
            'gmail.classify_priority': self._classify_priority,
        }
        
        return {**base_skills, **gmail_skills}
