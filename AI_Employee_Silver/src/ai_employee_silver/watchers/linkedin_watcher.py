"""
LinkedIn Watcher for AI Employee Silver Tier.

This watcher monitors LinkedIn for connection requests, messages, and business opportunities.
It uses Playwright for browser automation and inherits from BaseWatcher.

Agent Skills:
    - linkedin.check_updates(): Check for new LinkedIn activity
    - linkedin.create_action_file(): Create action file for LinkedIn item
    - linkedin.mark_processed(): Mark item as processed
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional

from .base_watcher import BaseWatcher
from ..integrations.linkedin_playwright import LinkedInPlaywrightAutomation
from ..config.settings import get_settings
from ..utils.logger import get_logger


class LinkedInWatcher(BaseWatcher):
    """
    LinkedIn watcher implementing the BaseWatcher interface.
    
    Monitors LinkedIn for:
    - New connection requests
    - Messages
    - Business opportunities
    - Job postings (optional)
    
    Rate limiting is implemented to respect LinkedIn's Terms of Service.
    """
    
    def __init__(
        self,
        vault_path: str | Path,
        check_interval: int = 300,  # 5 minutes (rate limiting)
        name: str = "LinkedInWatcher",
        linkedin_email: Optional[str] = None,
        linkedin_password: Optional[str] = None
    ):
        """
        Initialize LinkedIn Watcher.
        
        Args:
            vault_path: Path to the AI Employee vault
            check_interval: Seconds between checks (default: 300 for rate limiting)
            name: Watcher name
            linkedin_email: LinkedIn email for login
            linkedin_password: LinkedIn password for login
        """
        super().__init__(vault_path, check_interval, name)
        
        # Create LinkedIn automation
        self.settings = get_settings()
        self.linkedin_email = linkedin_email or self.settings.LINKEDIN_EMAIL
        self.linkedin_password = linkedin_password or self.settings.LINKEDIN_PASSWORD
        
        self.li_automation = LinkedInPlaywrightAutomation(
            linkedin_email=self.linkedin_email,
            linkedin_password=self.linkedin_password
        )
        
        # Business opportunity keywords
        self.opportunity_keywords = [
            'hiring', 'opportunity', 'project', 'collaboration',
            'partnership', 'freelance', 'contract', 'consulting',
            'business', 'proposal', 'investment', 'startup'
        ]
        
        # Rate limiting
        self.last_check_time: Optional[datetime] = None
        self.min_check_interval = timedelta(seconds=60)  # Minimum 1 minute between checks
    
    def check_for_updates(self) -> list[dict[str, Any]]:
        """
        Check for new LinkedIn activity.
        
        Returns:
            List of new LinkedIn items to process
        """
        try:
            # Rate limiting check
            if self.last_check_time:
                elapsed = datetime.now() - self.last_check_time
                if elapsed < self.min_check_interval:
                    self.logger.debug(f"Rate limiting: waiting {elapsed.seconds}s")
                    return []
            
            # Note: Actual LinkedIn monitoring requires browser automation
            # This is a placeholder that demonstrates the pattern
            # In production, you would:
            # 1. Navigate to LinkedIn notifications/messages
            # 2. Parse the page for new items
            # 3. Extract connection requests, messages, etc.
            
            items = []
            
            # Simulate checking for new activity
            # In real implementation, this would use Playwright to scrape LinkedIn
            self.logger.info("Checking LinkedIn for new activity...")
            
            # TODO: Implement actual LinkedIn scraping with Playwright
            # For now, return empty list - the structure is in place
            
            self.last_check_time = datetime.now()
            return items
            
        except Exception as e:
            self.logger.error(f"Error checking LinkedIn: {e}")
            return []
    
    def parse_item(self, item: dict[str, Any]) -> dict[str, Any]:
        """
        Parse LinkedIn item into structured format.
        
        Args:
            item: LinkedIn item from check_for_updates
            
        Returns:
            Structured LinkedIn data
        """
        activity_type = item.get('type', 'unknown')
        
        parsed = {
            'id': item['id'],
            'type': activity_type,
            'source': 'LinkedIn',
            'from': item.get('from', 'Unknown'),
            'content': item.get('content', ''),
            'received': item.get('timestamp', datetime.now().isoformat()),
            'priority': self._classify_priority(item),
            'is_opportunity': self._is_business_opportunity(item.get('content', ''))
        }
        
        # Add type-specific fields
        if activity_type == 'connection_request':
            parsed['person_name'] = item.get('name', 'Unknown')
            parsed['person_title'] = item.get('title', '')
            parsed['person_company'] = item.get('company', '')
        elif activity_type == 'message':
            parsed['subject'] = item.get('subject', '')
            parsed['thread_id'] = item.get('thread_id', '')
        elif activity_type == 'job_posting':
            parsed['job_title'] = item.get('job_title', '')
            parsed['company'] = item.get('company', '')
            parsed['location'] = item.get('location', '')
        
        return parsed
    
    def create_action_file(self, item: dict[str, Any]) -> Path:
        """
        Create action file for LinkedIn item in Needs_Action/LinkedIn/.
        
        Args:
            item: Parsed LinkedIn data
            
        Returns:
            Path to created action file
        """
        try:
            # Ensure directory exists
            linkedin_dir = self.needs_action / "LinkedIn"
            linkedin_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename based on type
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            activity_type = item.get('type', 'unknown')
            safe_name = self._sanitize_string(item.get('from', 'Unknown'))[:30]
            
            if activity_type == 'connection_request':
                filename = f"LINKEDIN_CONNECTION_{timestamp}_{safe_name}.md"
            elif activity_type == 'message':
                filename = f"LINKEDIN_MESSAGE_{timestamp}_{safe_name}.md"
            elif activity_type == 'opportunity':
                filename = f"LINKEDIN_OPPORTUNITY_{timestamp}_{safe_name}.md"
            else:
                filename = f"LINKEDIN_{activity_type.upper()}_{timestamp}_{safe_name}.md"
            
            filepath = linkedin_dir / filename
            
            # Build content
            content = self._build_action_file_content(item)
            
            # Write file
            filepath.write_text(content, encoding='utf-8')
            
            self.logger.info(f"Created action file: {filename}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Error creating action file: {e}")
            fallback_path = self.needs_action / "LinkedIn" / f"LINKEDIN_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            fallback_path.write_text(f"# Error creating action file\n\nError: {e}\n", encoding='utf-8')
            return fallback_path
    
    def _build_action_file_content(self, item: dict[str, Any]) -> str:
        """
        Build markdown content for action file.
        
        Args:
            item: Parsed LinkedIn data
            
        Returns:
            Markdown content string
        """
        activity_type = item.get('type', 'unknown')
        
        # YAML frontmatter
        frontmatter = f"""---
type: linkedin_{activity_type}
source: LinkedIn
id: {item['id']}
from: {item.get('from', 'Unknown')}
received: {item.get('received', datetime.now().isoformat())}
priority: {item.get('priority', 'medium')}
status: pending
is_opportunity: {str(item.get('is_opportunity', False)).lower()}
---

# LinkedIn {activity_type.replace('_', ' ').title()}: {item.get('from', 'Unknown')}

## Details
- **Type:** {activity_type.replace('_', ' ').title()}
- **From:** {item.get('from', 'Unknown')}
- **Received:** {item.get('received', 'Unknown')}
- **Priority:** {item.get('priority', 'medium').upper()}
- **Business Opportunity:** {'Yes' if item.get('is_opportunity') else 'No'}

## Content

{item.get('content', '*No content available*')}

## Additional Information
{self._format_additional_info(item)}

## Suggested Actions
- [ ] Review {activity_type.replace('_', ' ')}
- [ ] {self._suggest_action(item)}
- [ ] Create plan if needed
- [ ] Move to /Done/ when complete

---
*Generated by AI Employee Silver Tier - LinkedIn Watcher*
"""
        return frontmatter
    
    def _format_additional_info(self, item: dict[str, Any]) -> str:
        """Format additional information based on type."""
        lines = []
        
        if 'person_name' in item:
            lines.append(f"- **Name:** {item['person_name']}")
        if 'person_title' in item:
            lines.append(f"- **Title:** {item['person_title']}")
        if 'person_company' in item:
            lines.append(f"- **Company:** {item['person_company']}")
        if 'subject' in item:
            lines.append(f"- **Subject:** {item['subject']}")
        if 'job_title' in item:
            lines.append(f"- **Job Title:** {item['job_title']}")
        if 'company' in item:
            lines.append(f"- **Company:** {item['company']}")
        if 'location' in item:
            lines.append(f"- **Location:** {item['location']}")
        
        return "\n".join(lines) if lines else "- No additional information"
    
    def _suggest_action(self, item: dict[str, Any]) -> str:
        """Suggest action based on LinkedIn item type."""
        activity_type = item.get('type', 'unknown')
        
        if activity_type == 'connection_request':
            if item.get('is_opportunity'):
                return "Accept connection and explore opportunity"
            else:
                return "Review profile and decide on acceptance"
        elif activity_type == 'message':
            return "Reply to message"
        elif activity_type == 'opportunity':
            return "Evaluate and create action plan"
        elif activity_type == 'job_posting':
            return "Review job requirements"
        else:
            return "Review and categorize"
    
    def _classify_priority(self, item: dict[str, Any]) -> str:
        """
        Classify LinkedIn item priority.
        
        Args:
            item: LinkedIn item
            
        Returns:
            Priority level: 'high', 'medium', or 'low'
        """
        # Connection requests with opportunities are high priority
        if item.get('is_opportunity'):
            return 'high'
        
        # Messages are medium priority
        if item.get('type') == 'message':
            return 'medium'
        
        # Job postings and other activity are low priority
        return 'low'
    
    def _is_business_opportunity(self, content: str) -> bool:
        """
        Check if content indicates a business opportunity.
        
        Args:
            content: LinkedIn item content
            
        Returns:
            True if business opportunity detected
        """
        if not content:
            return False
        
        content_lower = content.lower()
        
        for keyword in self.opportunity_keywords:
            if keyword in content_lower:
                return True
        
        return False
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize string for filename."""
        if not text:
            return ""
        unsafe = '<>:"/\\|?*'
        for char in unsafe:
            text = text.replace(char, '_')
        return text.strip(' _.')
    
    def mark_as_read(self, item: dict[str, Any]) -> None:
        """
        Mark LinkedIn item as read.
        
        Args:
            item: LinkedIn item to mark as read
        """
        try:
            # LinkedIn read status would be handled via browser automation
            self.logger.debug(f"LinkedIn item {item['id']} processed")
        except Exception as e:
            self.logger.error(f"Error marking LinkedIn item as read: {e}")
    
    def get_skills(self) -> dict[str, callable]:
        """
        Return Agent Skills exposed by this watcher.
        
        Returns:
            Dictionary of skill names to callables
        """
        base_skills = super().get_skills()
        
        # Add LinkedIn-specific skills
        linkedin_skills = {
            'linkedin.check_activity': self.check_for_updates,
            'linkedin.parse_item': self.parse_item,
            'linkedin.create_action_file': self.create_action_file,
            'linkedin.is_opportunity': self._is_business_opportunity,
            'linkedin.classify_priority': self._classify_priority,
        }
        
        return {**base_skills, **linkedin_skills}
