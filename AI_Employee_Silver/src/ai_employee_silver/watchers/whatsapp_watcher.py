"""
WhatsApp Watcher for AI Employee Silver Tier.

This watcher monitors WhatsApp for urgent business messages using Playwright.
It inherits from BaseWatcher and wraps the existing WhatsApp integration.

Agent Skills:
    - whatsapp.check_updates(): Check for new messages
    - whatsapp.create_action_file(): Create action file for message
    - whatsapp.mark_processed(): Mark message as processed
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Optional

from .base_watcher import BaseWatcher
from ..integrations.whatsapp_playwright import WhatsAppPlaywrightMonitor, WhatsAppMessage as WAMessage
from ..config.settings import get_settings
from ..utils.logger import get_logger


class WhatsAppWatcher(BaseWatcher):
    """
    WhatsApp watcher implementing the BaseWatcher interface.
    
    This class wraps the existing WhatsApp Playwright integration and provides
    a consistent interface for the AI Employee system.
    """
    
    def __init__(
        self,
        vault_path: str | Path,
        check_interval: int = 30,  # 30 seconds
        name: str = "WhatsAppWatcher",
        session_path: Optional[str] = None
    ):
        """
        Initialize WhatsApp Watcher.
        
        Args:
            vault_path: Path to the AI Employee vault
            check_interval: Seconds between checks (default: 30)
            name: Watcher name
            session_path: Path to store WhatsApp session
        """
        super().__init__(vault_path, check_interval, name)
        
        # Create existing WhatsApp watcher
        self.settings = get_settings()
        
        # Initialize WhatsApp Playwright monitor directly
        self.wa_monitor = WhatsAppPlaywrightMonitor(
            settings=self.settings,
            logger=get_logger()
        )
        
        # Override session path if provided
        if session_path:
            self.wa_monitor.session_path = Path(session_path)
        
        # Keyword detection (English + Urdu)
        self.english_keywords = [
            'urgent', 'asap', 'invoice', 'payment', 'help', 'task',
            'emergency', 'important', 'needed', 'required', 'please'
        ]
        self.urdu_keywords = [
            'فوری', 'ادھار', 'بل', 'مدد', 'کام',
            'ضروری', 'برائے مہربانی', 'پیمنٹ'
        ]
    
    def check_for_updates(self) -> list[dict[str, Any]]:
        """
        Check for new WhatsApp messages with keywords.
        
        Returns:
            List of new message items to process
        """
        try:
            # Connect if needed
            if not self.wa_monitor.page:
                if not self.wa_monitor.connect():
                    self.logger.error("WhatsApp connection failed")
                    return []
            
            # Fetch messages using existing watcher
            messages = self.wa_monitor.poll_messages()
            
            # Filter messages with keywords
            items = []
            for msg in messages:
                if self._has_keywords(msg.text):
                    items.append({
                        'id': msg.message_id,
                        'type': 'whatsapp',
                        'source': 'WhatsApp',
                        'data': msg,
                        'priority': 'high',
                        'keywords': self._detect_keywords(msg.text)
                    })
            
            self.logger.info(f"Found {len(items)} urgent WhatsApp messages")
            return items
            
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            return []
    
    def parse_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """
        Parse WhatsApp message into structured format.
        
        Args:
            item: Message item from check_for_updates
            
        Returns:
            Structured message data
        """
        msg = item['data']
        
        return {
            'id': item['id'],
            'type': 'whatsapp',
            'source': 'WhatsApp',
            'from': msg.from_number,
            'from_name': msg.from_name,
            'text': msg.text,
            'received': msg.timestamp.isoformat() if msg.timestamp else datetime.now().isoformat(),
            'has_media': msg.has_media,
            'media_type': msg.media_type,
            'priority': item.get('priority', 'high'),
            'keywords': item.get('keywords', [])
        }
    
    def create_action_file(self, item: dict[str, Any]) -> Path:
        """
        Create action file for WhatsApp message in Needs_Action/WhatsApp/.
        
        Args:
            item: Parsed message data
            
        Returns:
            Path to created action file
        """
        try:
            # Ensure directory exists
            whatsapp_dir = self.needs_action / "WhatsApp"
            whatsapp_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_number = "".join(c for c in str(item['from']) if c.isdigit())[-4:]
            filename = f"WHATSAPP_{timestamp}_{safe_number}.md"
            filepath = whatsapp_dir / filename
            
            # Build content
            content = self._build_action_file_content(item)
            
            # Write file
            filepath.write_text(content, encoding='utf-8')
            
            self.logger.info(f"Created action file: {filename}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            fallback_path = self.needs_action / "WhatsApp" / f"WHATSAPP_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            fallback_path.write_text(f"# Error creating action file\n\nError: {e}\n", encoding='utf-8')
            return fallback_path
    
    def _build_action_file_content(self, item: dict[str, Any]) -> str:
        """
        Build markdown content for action file.
        
        Args:
            item: Parsed message data
            
        Returns:
            Markdown content string
        """
        # YAML frontmatter
        frontmatter = f"""---
type: whatsapp_message
source: WhatsApp
id: {item['id']}
from: {item['from']}
from_name: {item.get('from_name', 'Unknown')}
received: {item['received']}
priority: {item['priority']}
status: pending
has_media: {str(item['has_media']).lower()}
keywords: {', '.join(item['keywords']) if item['keywords'] else ''}
---

# WhatsApp Message: {item.get('from_name', item['from'])}

## Details
- **From:** {item.get('from_name', 'Unknown')} ({item['from']})
- **Received:** {item['received']}
- **Priority:** {item['priority'].upper()}
- **Keywords Detected:** {', '.join(item['keywords']) if item['keywords'] else 'None'}

## Message Content

{item['text'] if item['text'] else '*No text content available*'}

## Media
{self._format_media_info(item)}

## Suggested Actions
- [ ] Review message content
- [ ] {self._suggest_action(item)}
- [ ] Create plan if needed
- [ ] Move to /Done/ when complete

---
*Generated by AI Employee Silver Tier - WhatsApp Watcher*
"""
        return frontmatter
    
    def _format_media_info(self, item: dict[str, Any]) -> str:
        """Format media information."""
        if not item['has_media']:
            return "- No media attached"
        
        media_type = item.get('media_type', 'unknown')
        return f"- 📎 Media type: {media_type.upper()}"
    
    def _suggest_action(self, item: dict[str, Any]) -> str:
        """Suggest action based on message content."""
        text_lower = (item.get('text') or '').lower()
        
        if any(word in text_lower for word in ['invoice', 'payment', 'bill', 'ادھار', 'بل']):
            return "Process payment request"
        elif any(word in text_lower for word in ['help', 'urgent', 'emergency', 'فوری', 'مدد']):
            return "Respond urgently"
        elif any(word in text_lower for word in ['task', 'needed', 'required', 'کام']):
            return "Create task from message"
        else:
            return "Reply to sender"
    
    def _has_keywords(self, text: Optional[str]) -> bool:
        """
        Check if text contains keywords.
        
        Args:
            text: Message text
            
        Returns:
            True if keywords found
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check English keywords
        for keyword in self.english_keywords:
            if keyword in text_lower:
                return True
        
        # Check Urdu keywords
        for keyword in self.urdu_keywords:
            if keyword in text:
                return True
        
        return False
    
    def _detect_keywords(self, text: Optional[str]) -> list[str]:
        """
        Detect which keywords are present in text.
        
        Args:
            text: Message text
            
        Returns:
            List of detected keywords
        """
        if not text:
            return []
        
        detected = []
        text_lower = text.lower()
        
        # Check English keywords
        for keyword in self.english_keywords:
            if keyword in text_lower:
                detected.append(keyword)
        
        # Check Urdu keywords
        for keyword in self.urdu_keywords:
            if keyword in text:
                detected.append(keyword)
        
        return detected
    
    def mark_as_read(self, item: dict[str, Any]) -> None:
        """
        Mark message as read (session-based).
        
        Args:
            item: Message item to mark as read
        """
        try:
            # WhatsApp Web handles read status automatically when accessed
            self.logger.debug(f"WhatsApp message {item['id']} processed")
        except Exception as e:
            self.logger.error(f"Error marking message as read: {e}")
    
    def get_skills(self) -> dict[str, callable]:
        """
        Return Agent Skills exposed by this watcher.
        
        Returns:
            Dictionary of skill names to callables
        """
        base_skills = super().get_skills()
        
        # Add WhatsApp-specific skills
        whatsapp_skills = {
            'whatsapp.check_messages': self.check_for_updates,
            'whatsapp.parse_message': self.parse_item,
            'whatsapp.create_message_action': self.create_action_file,
            'whatsapp.detect_keywords': self._detect_keywords,
            'whatsapp.has_keywords': self._has_keywords,
        }
        
        return {**base_skills, **whatsapp_skills}
