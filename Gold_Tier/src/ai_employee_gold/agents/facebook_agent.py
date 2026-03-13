"""Facebook Agent for Gold Tier AI Employee.

This agent provides Agent Skills for Facebook operations:
- post_update - Post to Facebook page
- get_engagement - Get post engagement metrics
- generate_summary - Generate Facebook activity summary
- schedule_post - Schedule post for later
- get_page_info - Get page information
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

from ..integrations.facebook_integration import facebook
from ..core.vault import vault
from ..core.audit_logger import audit_logger
from ..core.error_recovery import health_monitor, HealthStatus
from ..config.settings import settings

logger = logging.getLogger(__name__)


class FacebookAgent:
    """Autonomous Facebook Agent.
    
    This agent has full access to Facebook tools and can:
    - Create and schedule posts
    - Monitor engagement metrics
    - Generate activity summaries
    - Respond to comments (with approval)
    
    All posting actions are logged and may require approval
    for sensitive content.
    """
    
    def __init__(self):
        """Initialize Facebook Agent."""
        self.name = "FacebookAgent"
        self.version = "1.0.0"
        self.domain = "business"
        self.subdomain = "social_media"
        
        # Facebook integration
        self.facebook = facebook
        
        # Posting limits
        self.max_posts_per_day = 5
        self.posts_today = 0
        self.last_reset_date = datetime.now().date()
        
        # Approval settings
        self.require_approval_for_posting = False  # Set to True for strict mode
        
        # Statistics
        self.total_actions = 0
        self.successful_actions = 0
        self.failed_actions = 0
        self.start_time = datetime.now()
        
        logger.info(f"Facebook Agent initialized: {self.name} v{self.version}")
    
    # ==================== AGENT SKILLS ====================
    
    def post_update(
        self,
        message: str,
        image_url: Optional[str] = None,
        schedule_time: Optional[str] = None,
        requires_approval: bool = False
    ) -> Dict[str, Any]:
        """Agent Skill: Post update to Facebook page.
        
        Args:
            message: Post message content
            image_url: Optional image URL to include
            schedule_time: Optional schedule time (ISO format)
            requires_approval: Whether approval is needed
            
        Returns:
            Result dictionary with post_id or error
            
        Example:
            >>> agent.post_update(
            ...     message="Exciting news! Check out our latest product.",
            ...     image_url="https://example.com/image.jpg"
            ... )
        """
        self.total_actions += 1
        start_time = datetime.now()
        
        try:
            # Check daily limit
            self._check_daily_limit()
            
            # Check if approval needed
            if requires_approval:
                return self._request_post_approval(message, image_url, schedule_time)
            
            # Check if Facebook is connected
            if not self.facebook.access_token:
                return {"success": False, "error": "Facebook not connected"}
            
            # Post to Facebook
            if schedule_time:
                # Schedule post (simplified - would use Facebook's scheduling API)
                result = self._schedule_facebook_post(message, image_url, schedule_time)
            else:
                # Post immediately
                post_id = self.facebook.post_to_facebook(message, image_url)
                
                if post_id:
                    result = {
                        "success": True,
                        "post_id": post_id,
                        "message": "Post created successfully",
                        "scheduled": False
                    }
                else:
                    result = {
                        "success": False,
                        "error": "Failed to create post"
                    }
            
            if result.get("success"):
                self.successful_actions += 1
                self.posts_today += 1
                
                # Audit log
                execution_time = int((datetime.now() - start_time).total_seconds() * 1000)
                audit_logger.log(
                    action_type="facebook_agent.post_update",
                    actor=self.name,
                    actor_type="agent",
                    domain=self.domain,
                    subdomain=self.subdomain,
                    target=f"Facebook post: {message[:50]}...",
                    parameters={
                        "message": message,
                        "image_url": image_url,
                        "scheduled": schedule_time is not None
                    },
                    result="success",
                    result_data=result,
                    execution_time_ms=execution_time
                )
                
                logger.info(f"Facebook post created: {post_id}")
            else:
                self.failed_actions += 1
                logger.error(f"Failed to post to Facebook: {result.get('error')}")
            
            return result
            
        except Exception as e:
            self.failed_actions += 1
            logger.error(f"Error in post_update: {e}")
            return {"success": False, "error": str(e)}
    
    def get_engagement(self, post_id: str) -> Dict[str, Any]:
        """Agent Skill: Get engagement metrics for a post.
        
        Args:
            post_id: Facebook post ID
            
        Returns:
            Engagement metrics dictionary
            
        Example:
            >>> metrics = agent.get_engagement("123456789")
            >>> print(f"Likes: {metrics['likes']}, Comments: {metrics['comments']}")
        """
        self.total_actions += 1
        
        try:
            if not self.facebook.access_token:
                return {"success": False, "error": "Facebook not connected"}
            
            engagement = self.facebook.get_post_engagement(post_id)
            
            if engagement:
                self.successful_actions += 1
                
                return {
                    "success": True,
                    "post_id": post_id,
                    "likes": engagement.get("likes", {}).get("summary", {}).get("total_count", 0),
                    "comments": engagement.get("comments", {}).get("summary", {}).get("total_count", 0),
                    "shares": engagement.get("shares", {}).get("count", 0),
                    "reactions": engagement.get("reactions", {}).get("summary", {}).get("total_count", 0)
                }
            else:
                self.failed_actions += 1
                return {"success": False, "error": "Failed to get engagement"}
                
        except Exception as e:
            self.failed_actions += 1
            return {"success": False, "error": str(e)}
    
    def generate_summary(
        self,
        period: str = "week"
    ) -> Dict[str, Any]:
        """Agent Skill: Generate Facebook activity summary.
        
        Args:
            period: Summary period (day, week, month)
            
        Returns:
            Summary dictionary with metrics
            
        Example:
            >>> summary = agent.generate_summary(period="week")
            >>> print(f"Posts: {summary['posts']}, Engagement: {summary['total_engagement']}")
        """
        try:
            if not self.facebook.access_token:
                return {"success": False, "error": "Facebook not connected"}
            
            # Get recent posts
            posts = self.facebook.get_page_posts(limit=25)
            
            # Calculate metrics
            total_likes = 0
            total_comments = 0
            total_shares = 0
            total_reach = 0
            
            for post in posts:
                total_likes += post.get("likes", {}).get("summary", {}).get("total_count", 0)
                total_comments += post.get("comments", {}).get("summary", {}).get("total_count", 0)
                total_shares += post.get("shares", {}).get("count", 0)
            
            # Get page insights
            insights = self.facebook.get_page_insights(metric="page_impressions")
            
            summary = {
                "success": True,
                "period": period,
                "posts_count": len(posts),
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_shares": total_shares,
                "total_engagement": total_likes + total_comments + total_shares,
                "total_reach": total_reach,
                "average_engagement_per_post": (total_likes + total_comments + total_shares) / max(1, len(posts)),
                "recent_posts": posts[:5]  # Return last 5 posts
            }
            
            self.successful_actions += 1
            return summary
            
        except Exception as e:
            self.failed_actions += 1
            return {"success": False, "error": str(e)}
    
    def schedule_post(
        self,
        message: str,
        schedule_time: str,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Agent Skill: Schedule post for later publishing.
        
        Args:
            message: Post message content
            schedule_time: Schedule time (ISO format: YYYY-MM-DDTHH:MM:SS)
            image_url: Optional image URL
            
        Returns:
            Result dictionary
            
        Example:
            >>> agent.schedule_post(
            ...     message="Monday motivation!",
            ...     schedule_time="2026-03-16T09:00:00",
            ...     image_url="https://example.com/motivation.jpg"
            ... )
        """
        self.total_actions += 1
        
        try:
            # Validate schedule time
            schedule_dt = datetime.fromisoformat(schedule_time)
            
            if schedule_dt < datetime.now():
                return {"success": False, "error": "Schedule time must be in the future"}
            
            # Save scheduled post to Plans folder
            scheduled_post = {
                "type": "scheduled_facebook_post",
                "message": message,
                "image_url": image_url,
                "scheduled_time": schedule_time,
                "created": datetime.now().isoformat(),
                "status": "scheduled"
            }
            
            # Create file in Plans folder
            plans_path = vault.paths.plans / f"FACEBOOK_SCHEDULED_{schedule_dt.strftime('%Y%m%d_%H%M%S')}.md"
            
            content = f"""---
type: scheduled_facebook_post
scheduled_time: {schedule_time}
created: {datetime.now().isoformat()}
status: scheduled
platform: facebook
---

# Scheduled Facebook Post

## Content
{message}

## Image
{image_url or 'None'}

## Scheduled Time
{schedule_dt.strftime('%Y-%m-%d %H:%M:%S')}

## Status
Scheduled - Will be posted automatically
"""
            
            plans_path.write_text(content)
            
            self.successful_actions += 1
            
            return {
                "success": True,
                "message": "Post scheduled successfully",
                "scheduled_time": schedule_time,
                "file": str(plans_path)
            }
            
        except Exception as e:
            self.failed_actions += 1
            return {"success": False, "error": str(e)}
    
    def get_page_info(self) -> Dict[str, Any]:
        """Agent Skill: Get Facebook page information.
        
        Returns:
            Page information dictionary
            
        Example:
            >>> info = agent.get_page_info()
            >>> print(f"Page: {info['name']}, Likes: {info['likes']}")
        """
        try:
            if not self.facebook.access_token:
                return {"success": False, "error": "Facebook not connected"}
            
            # Get page info
            response = requests.get(
                f"{self.facebook.base_url}/me",
                params={
                    "access_token": self.facebook.access_token,
                    "fields": "id,name,username,about,website,emails,phone,location,fan_count"
                }
            )
            
            if response.status_code == 200:
                page_info = response.json()
                
                self.successful_actions += 1
                
                return {
                    "success": True,
                    "page_id": page_info.get("id"),
                    "name": page_info.get("name"),
                    "username": page_info.get("username"),
                    "about": page_info.get("about"),
                    "website": page_info.get("website"),
                    "likes": page_info.get("fan_count"),
                    "location": page_info.get("location")
                }
            else:
                self.failed_actions += 1
                return {"success": False, "error": "Failed to get page info"}
                
        except Exception as e:
            self.failed_actions += 1
            return {"success": False, "error": str(e)}
    
    # ==================== HELPER METHODS ====================
    
    def _check_daily_limit(self):
        """Check and reset daily post counter if needed."""
        today = datetime.now().date()
        
        if self.last_reset_date != today:
            self.posts_today = 0
            self.last_reset_date = today
    
    def _schedule_facebook_post(
        self,
        message: str,
        image_url: Optional[str],
        schedule_time: str
    ) -> Dict[str, Any]:
        """Schedule Facebook post (placeholder for actual scheduling API)."""
        # In real implementation, would use Facebook's scheduled_posts endpoint
        # For now, save to Plans folder
        return self.schedule_post(message, schedule_time, image_url)
    
    def _request_post_approval(
        self,
        message: str,
        image_url: Optional[str],
        schedule_time: Optional[str]
    ) -> Dict[str, Any]:
        """Request approval for post."""
        # Create approval request file
        approval_content = f"""---
type: approval_request
action: facebook.post_update
created: {datetime.now().isoformat()}
expires: {datetime.now().replace(hour=23, minute=59, second=59).isoformat()}
status: pending
urgency: normal
category: communication
risk_level: low
---

# Facebook Post Approval Request

## Post Content
{message}

## Image
{image_url or 'None'}

## Scheduled Time
{schedule_time or 'Immediate'}

## Approval Required
This post requires approval before publishing.

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder with reason.
"""
        
        # Write approval file
        approval_file = vault.paths.pending_approval / f"APPROVAL_FACEBOOK_POST_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        approval_file.write_text(approval_content)
        
        logger.info(f"Approval request created: {approval_file}")
        
        return {
            "success": False,
            "requires_approval": True,
            "approval_file": str(approval_file),
            "message": "Post requires approval before publishing"
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status and statistics."""
        uptime = datetime.now() - self.start_time
        
        return {
            "name": self.name,
            "version": self.version,
            "domain": self.domain,
            "subdomain": self.subdomain,
            "uptime_seconds": int(uptime.total_seconds()),
            "statistics": {
                "total_actions": self.total_actions,
                "successful_actions": self.successful_actions,
                "failed_actions": self.failed_actions,
                "success_rate": self.successful_actions / max(1, self.total_actions)
            },
            "posting_limits": {
                "max_per_day": self.max_posts_per_day,
                "posts_today": self.posts_today,
                "remaining_today": self.max_posts_per_day - self.posts_today
            },
            "facebook_connected": bool(self.facebook.access_token)
        }


# Global Facebook Agent instance
facebook_agent = FacebookAgent()
