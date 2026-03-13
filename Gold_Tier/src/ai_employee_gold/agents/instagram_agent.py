"""Instagram Agent for Gold Tier AI Employee.

Agent Skills:
- post_media - Post image/carousel to Instagram
- post_story - Post Instagram story
- get_engagement - Get media engagement
- generate_summary - Generate Instagram summary
- optimize_hashtags - Optimize hashtags for reach
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ..integrations.instagram_integration import instagram
from ..core.vault import vault
from ..core.audit_logger import audit_logger
from ..core.error_recovery import health_monitor, HealthStatus

logger = logging.getLogger(__name__)


class InstagramAgent:
    """Autonomous Instagram Agent."""
    
    def __init__(self):
        """Initialize Instagram Agent."""
        self.name = "InstagramAgent"
        self.version = "1.0.0"
        self.domain = "business"
        self.subdomain = "social_media"
        self.instagram = instagram
        
        self.total_actions = 0
        self.successful_actions = 0
        self.failed_actions = 0
        self.start_time = datetime.now()
        
        logger.info(f"Instagram Agent initialized: {self.name} v{self.version}")
    
    # ==================== AGENT SKILLS ====================
    
    def post_media(
        self,
        image_url: str,
        caption: str,
        hashtags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Agent Skill: Post media to Instagram.
        
        Args:
            image_url: Image URL to post
            caption: Post caption
            hashtags: Optional list of hashtags
            
        Returns:
            Result dictionary
        """
        self.total_actions += 1
        
        try:
            if not self.instagram.access_token:
                return {"success": False, "error": "Instagram not connected"}
            
            # Add hashtags to caption
            if hashtags:
                hashtag_str = " ".join([f"#{tag}" for tag in hashtags])
                caption = f"{caption}\n\n{hashtag_str}"
            
            # Post to Instagram
            media_id = self.instagram.post_to_instagram(image_url, caption)
            
            if media_id:
                self.successful_actions += 1
                
                audit_logger.log(
                    action_type="instagram_agent.post_media",
                    actor=self.name,
                    actor_type="agent",
                    domain=self.domain,
                    subdomain=self.subdomain,
                    target=f"Instagram post: {caption[:50]}...",
                    parameters={
                        "image_url": image_url,
                        "caption": caption,
                        "hashtags": hashtags
                    },
                    result="success",
                    result_data={"media_id": media_id}
                )
                
                return {
                    "success": True,
                    "media_id": media_id,
                    "message": "Media posted successfully"
                }
            else:
                self.failed_actions += 1
                return {"success": False, "error": "Failed to post media"}
                
        except Exception as e:
            self.failed_actions += 1
            return {"success": False, "error": str(e)}
    
    def post_story(
        self,
        image_url: str,
        sticker_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """Agent Skill: Post Instagram story.
        
        Args:
            image_url: Image URL
            sticker_text: Optional sticker text
            
        Returns:
            Result dictionary
        """
        self.total_actions += 1
        
        try:
            if not self.instagram.access_token:
                return {"success": False, "error": "Instagram not connected"}
            
            story_id = self.instagram.post_story(image_url, sticker_text or "")
            
            if story_id:
                self.successful_actions += 1
                return {
                    "success": True,
                    "story_id": story_id,
                    "message": "Story posted successfully"
                }
            else:
                self.failed_actions += 1
                return {"success": False, "error": "Failed to post story"}
                
        except Exception as e:
            self.failed_actions += 1
            return {"success": False, "error": str(e)}
    
    def get_engagement(self, media_id: str) -> Dict[str, Any]:
        """Agent Skill: Get engagement metrics.
        
        Args:
            media_id: Instagram media ID
            
        Returns:
            Engagement metrics
        """
        self.total_actions += 1
        
        try:
            if not self.instagram.access_token:
                return {"success": False, "error": "Instagram not connected"}
            
            insights = self.instagram.get_media_insights(
                media_id,
                ["impressions", "reach", "engagement", "saved"]
            )
            
            if insights:
                self.successful_actions += 1
                return {
                    "success": True,
                    "media_id": media_id,
                    "impressions": insights.get("impressions", 0),
                    "reach": insights.get("reach", 0),
                    "engagement": insights.get("engagement", 0),
                    "saved": insights.get("saved", 0)
                }
            else:
                self.failed_actions += 1
                return {"success": False, "error": "Failed to get engagement"}
                
        except Exception as e:
            self.failed_actions += 1
            return {"success": False, "error": str(e)}
    
    def generate_summary(self, period: str = "week") -> Dict[str, Any]:
        """Agent Skill: Generate Instagram summary.
        
        Args:
            period: Summary period
            
        Returns:
            Summary dictionary
        """
        try:
            if not self.instagram.access_token:
                return {"success": False, "error": "Instagram not connected"}
            
            # Get media list
            media_list = self.instagram.get_media_list(limit=25)
            
            # Get account summary
            account = self.instagram.get_account_summary()
            
            summary = {
                "success": True,
                "period": period,
                "posts_count": len(media_list),
                "followers": account.get("followers_count", 0),
                "following": account.get("follows_count", 0),
                "total_media": account.get("media_count", 0),
                "recent_media": media_list[:5]
            }
            
            self.successful_actions += 1
            return summary
            
        except Exception as e:
            self.failed_actions += 1
            return {"success": False, "error": str(e)}
    
    def optimize_hashtags(
        self,
        topic: str,
        count: int = 30
    ) -> Dict[str, Any]:
        """Agent Skill: Optimize hashtags for topic.
        
        Args:
            topic: Post topic
            count: Number of hashtags
            
        Returns:
            Optimized hashtag list
        """
        # Popular business hashtags
        hashtag_db = {
            "business": ["business", "entrepreneur", "success", "motivation", "marketing"],
            "tech": ["technology", "innovation", "tech", "startup", "digital"],
            "lifestyle": ["lifestyle", "inspiration", "life", "motivation", "success"],
            "product": ["newproduct", "launch", "innovation", "quality", "shopping"]
        }
        
        # Select relevant hashtags
        selected = []
        for key, tags in hashtag_db.items():
            if key in topic.lower():
                selected.extend(tags)
        
        # Add generic if not enough
        while len(selected) < count:
            selected.extend(["trending", "viral", "explore", "fyp", "instagood"])
        
        # Limit to count
        hashtags = selected[:count]
        
        self.successful_actions += 1
        
        return {
            "success": True,
            "hashtags": hashtags,
            "count": len(hashtags),
            "topic": topic
        }
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get agent status."""
        uptime = datetime.now() - self.start_time
        
        return {
            "name": self.name,
            "version": self.version,
            "uptime_seconds": int(uptime.total_seconds()),
            "statistics": {
                "total_actions": self.total_actions,
                "successful_actions": self.successful_actions,
                "failed_actions": self.failed_actions,
                "success_rate": self.successful_actions / max(1, self.total_actions)
            },
            "instagram_connected": bool(self.instagram.access_token)
        }


# Global Instagram Agent instance
instagram_agent = InstagramAgent()
