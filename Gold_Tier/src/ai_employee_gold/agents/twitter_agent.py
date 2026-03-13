"""Twitter (X) Agent for Gold Tier AI Employee.

Agent Skills:
- post_tweet - Post tweet to Twitter
- post_thread - Post tweet thread
- monitor_mentions - Monitor Twitter mentions
- get_engagement - Get tweet engagement
- generate_summary - Generate Twitter summary
- auto_respond - Auto-respond to mentions (with approval)
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from ..integrations.twitter_integration import twitter
from ..core.vault import vault
from ..core.audit_logger import audit_logger
from ..core.error_recovery import health_monitor, HealthStatus

logger = logging.getLogger(__name__)


class TwitterAgent:
    """Autonomous Twitter (X) Agent."""
    
    def __init__(self):
        """Initialize Twitter Agent."""
        self.name = "TwitterAgent"
        self.version = "1.0.0"
        self.domain = "business"
        self.subdomain = "social_media"
        self.twitter = twitter
        
        self.total_actions = 0
        self.successful_actions = 0
        self.failed_actions = 0
        self.start_time = datetime.now()
        
        # Tweet limits
        self.max_tweets_per_day = 10
        self.tweets_today = 0
        self.last_reset_date = datetime.now().date()
        
        logger.info(f"Twitter Agent initialized: {self.name} v{self.version}")
    
    # ==================== AGENT SKILLS ====================
    
    def post_tweet(
        self,
        text: str,
        media_urls: Optional[List[str]] = None,
        in_reply_to: Optional[str] = None
    ) -> Dict[str, Any]:
        """Agent Skill: Post tweet to Twitter.
        
        Args:
            text: Tweet text (max 280 characters)
            media_urls: Optional media URLs
            in_reply_to: Optional tweet ID to reply to
            
        Returns:
            Result dictionary
        """
        self.total_actions += 1
        self._check_daily_limit()
        
        try:
            if not all([twitter.api_key, twitter.api_secret, 
                       twitter.access_token, twitter.access_secret]):
                return {"success": False, "error": "Twitter not connected"}
            
            # Check character limit
            if len(text) > 280:
                return {"success": False, "error": "Tweet exceeds 280 characters"}
            
            # Post tweet
            tweet_id = twitter.post_tweet(text, media_urls)
            
            if tweet_id:
                self.successful_actions += 1
                self.tweets_today += 1
                
                audit_logger.log(
                    action_type="twitter_agent.post_tweet",
                    actor=self.name,
                    actor_type="agent",
                    domain=self.domain,
                    subdomain=self.subdomain,
                    target=f"Tweet: {text[:50]}...",
                    parameters={
                        "text": text,
                        "media_urls": media_urls,
                        "in_reply_to": in_reply_to
                    },
                    result="success",
                    result_data={"tweet_id": tweet_id}
                )
                
                return {
                    "success": True,
                    "tweet_id": tweet_id,
                    "message": "Tweet posted successfully"
                }
            else:
                self.failed_actions += 1
                return {"success": False, "error": "Failed to post tweet"}
                
        except Exception as e:
            self.failed_actions += 1
            return {"success": False, "error": str(e)}
    
    def post_thread(self, tweets: List[str]) -> Dict[str, Any]:
        """Agent Skill: Post tweet thread.
        
        Args:
            tweets: List of tweet texts
            
        Returns:
            Result dictionary with thread IDs
        """
        self.total_actions += 1
        
        try:
            if not all([twitter.api_key, twitter.api_secret,
                       twitter.access_token, twitter.access_secret]):
                return {"success": False, "error": "Twitter not connected"}
            
            if not tweets:
                return {"success": False, "error": "No tweets provided"}
            
            thread_ids = []
            previous_tweet_id = None
            
            for i, tweet_text in enumerate(tweets):
                # First tweet or reply to previous
                if previous_tweet_id:
                    result = self.post_tweet(tweet_text, in_reply_to=previous_tweet_id)
                else:
                    result = self.post_tweet(tweet_text)
                
                if result.get("success"):
                    thread_ids.append(result["tweet_id"])
                    previous_tweet_id = result["tweet_id"]
                else:
                    return {
                        "success": False,
                        "error": f"Failed at tweet {i+1}: {result.get('error')}",
                        "posted_count": len(thread_ids)
                    }
            
            self.successful_actions += 1
            
            return {
                "success": True,
                "thread_ids": thread_ids,
                "tweet_count": len(thread_ids),
                "message": f"Thread of {len(thread_ids)} tweets posted successfully"
            }
                
        except Exception as e:
            self.failed_actions += 1
            return {"success": False, "error": str(e)}
    
    def monitor_mentions(self, limit: int = 10) -> Dict[str, Any]:
        """Agent Skill: Monitor Twitter mentions.
        
        Args:
            limit: Number of mentions to retrieve
            
        Returns:
            List of mentions
        """
        self.total_actions += 1
        
        try:
            if not all([twitter.api_key, twitter.api_secret,
                       twitter.access_token, twitter.access_secret]):
                return {"success": False, "error": "Twitter not connected"}
            
            mentions = twitter.search_tweets(f"@yourusername", limit)
            
            self.successful_actions += 1
            
            return {
                "success": True,
                "mentions": mentions,
                "count": len(mentions),
                "limit": limit
            }
                
        except Exception as e:
            self.failed_actions += 1
            return {"success": False, "error": str(e)}
    
    def get_engagement(self, tweet_id: str) -> Dict[str, Any]:
        """Agent Skill: Get tweet engagement.
        
        Args:
            tweet_id: Tweet ID
            
        Returns:
            Engagement metrics
        """
        self.total_actions += 1
        
        try:
            if not all([twitter.api_key, twitter.api_secret,
                       twitter.access_token, twitter.access_secret]):
                return {"success": False, "error": "Twitter not connected"}
            
            engagement = twitter.get_tweet_engagement(tweet_id)
            
            if engagement:
                self.successful_actions += 1
                return {
                    "success": True,
                    "tweet_id": tweet_id,
                    "likes": engagement.get("like_count", 0),
                    "retweets": engagement.get("retweet_count", 0),
                    "replies": engagement.get("reply_count", 0),
                    "impressions": engagement.get("impression_count", 0)
                }
            else:
                self.failed_actions += 1
                return {"success": False, "error": "Failed to get engagement"}
                
        except Exception as e:
            self.failed_actions += 1
            return {"success": False, "error": str(e)}
    
    def generate_summary(self, period: str = "week") -> Dict[str, Any]:
        """Agent Skill: Generate Twitter summary.
        
        Args:
            period: Summary period
            
        Returns:
            Summary dictionary
        """
        try:
            if not all([twitter.api_key, twitter.api_secret,
                       twitter.access_token, twitter.access_secret]):
                return {"success": False, "error": "Twitter not connected"}
            
            # Get recent tweets
            tweets = twitter.get_tweets(limit=25)
            
            # Get followers
            followers = twitter.get_followers(limit=1)
            
            # Calculate metrics
            total_likes = 0
            total_retweets = 0
            total_replies = 0
            
            for tweet in tweets:
                metrics = tweet.get("public_metrics", {})
                total_likes += metrics.get("like_count", 0)
                total_retweets += metrics.get("retweet_count", 0)
                total_replies += metrics.get("reply_count", 0)
            
            summary = {
                "success": True,
                "period": period,
                "tweets_count": len(tweets),
                "total_likes": total_likes,
                "total_retweets": total_retweets,
                "total_replies": total_replies,
                "total_engagement": total_likes + total_retweets + total_replies,
                "followers_count": len(followers),
                "recent_tweets": tweets[:5]
            }
            
            self.successful_actions += 1
            return summary
            
        except Exception as e:
            self.failed_actions += 1
            return {"success": False, "error": str(e)}
    
    def auto_respond(
        self,
        mention: Dict[str, Any],
        response_template: str,
        requires_approval: bool = True
    ) -> Dict[str, Any]:
        """Agent Skill: Auto-respond to mention.
        
        Args:
            mention: Mention data
            response_template: Response template
            requires_approval: Whether approval needed
            
        Returns:
            Result dictionary
        """
        self.total_actions += 1
        
        try:
            if requires_approval:
                return self._request_response_approval(mention, response_template)
            
            # Extract mention ID
            mention_id = mention.get("id")
            mention_author = mention.get("author_id")
            
            # Create response
            response = response_template.format(
                username=f"@{mention_author}",
                mention_text=mention.get("text", "")
            )
            
            # Post as reply
            result = self.post_tweet(response, in_reply_to=mention_id)
            
            return result
                
        except Exception as e:
            self.failed_actions += 1
            return {"success": False, "error": str(e)}
    
    # ==================== HELPER METHODS ====================
    
    def _check_daily_limit(self):
        """Check and reset daily tweet counter."""
        today = datetime.now().date()
        
        if self.last_reset_date != today:
            self.tweets_today = 0
            self.last_reset_date = today
    
    def _request_response_approval(
        self,
        mention: Dict[str, Any],
        response_template: str
    ) -> Dict[str, Any]:
        """Request approval for response."""
        approval_content = f"""---
type: approval_request
action: twitter.auto_respond
created: {datetime.now().isoformat()}
status: pending
category: communication
---

# Twitter Response Approval

## Mention
{mention.get('text', 'N/A')}

## Proposed Response
{response_template}

## Approval
Move to /Approved to send, /Rejected to decline.
"""
        
        approval_file = vault.paths.pending_approval / f"APPROVAL_TWITTER_RESPONSE_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        approval_file.write_text(approval_content)
        
        return {
            "success": False,
            "requires_approval": True,
            "approval_file": str(approval_file)
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
            "tweet_limits": {
                "max_per_day": self.max_tweets_per_day,
                "tweets_today": self.tweets_today,
                "remaining_today": self.max_tweets_per_day - self.tweets_today
            },
            "twitter_connected": bool(all([
                twitter.api_key, twitter.api_secret,
                twitter.access_token, twitter.access_secret
            ]))
        }


# Global Twitter Agent instance
twitter_agent = TwitterAgent()
