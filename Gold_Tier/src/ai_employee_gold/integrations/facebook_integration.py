"""Facebook integration module for Gold Tier AI Employee system.

Features:
- Post to Facebook (text, image, video, link)
- Schedule posts for later publishing
- Get engagement metrics (likes, comments, shares)
- Get page insights and analytics
- Auto-respond to comments
- Error handling and rate limiting
"""
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
from ..config.settings import settings


class FacebookIntegration:
    """Integration with Facebook API for posting and monitoring.
    
    API Version: Graph API v18.0
    Rate Limit: 200 calls/hour per page
    Authentication: OAuth 2.0 with Page Access Token
    """

    def __init__(self):
        self.access_token = settings.FACEBOOK_PAGE_ACCESS_TOKEN
        self.app_id = settings.FACEBOOK_APP_ID
        self.app_secret = settings.FACEBOOK_APP_SECRET
        self.page_id = None  # Will be set after authentication
        self.base_url = "https://graph.facebook.com/v18.0"
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Rate limiting
        self.call_count = 0
        self.last_reset = datetime.now()
        self.rate_limit = 200  # calls per hour

        if self.access_token:
            self.verify_connection()

    def verify_connection(self) -> bool:
        """Verify connection to Facebook API."""
        try:
            response = requests.get(
                f"{self.base_url}/me",
                params={"access_token": self.access_token, "fields": "id,name"}
            )
            if response.status_code == 200:
                data = response.json()
                self.page_id = data.get("id")
                self.logger.info(f"Successfully connected to Facebook page: {data.get('name', 'Unknown')}")
                return True
            else:
                self.logger.error(f"Failed to connect to Facebook: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error verifying Facebook connection: {e}")
            return False
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits."""
        # Reset counter every hour
        if (datetime.now() - self.last_reset).total_seconds() > 3600:
            self.call_count = 0
            self.last_reset = datetime.now()
        
        if self.call_count >= self.rate_limit:
            self.logger.warning(f"Rate limit reached ({self.rate_limit} calls/hour)")
            return False
        
        self.call_count += 1
        return True
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Optional[Dict]:
        """Make rate-limited API request."""
        if not self._check_rate_limit():
            return None
        
        try:
            url = f"{self.base_url}/{endpoint}"
            if data is None:
                data = {}
            data['access_token'] = self.access_token
            
            if method.upper() == 'GET':
                response = requests.get(url, params=data)
            else:
                response = requests.post(url, data=data)
            
            return response
        except Exception as e:
            self.logger.error(f"API request error: {e}")
            return None

    def post_to_facebook(self, message: str, image_url: Optional[str] = None) -> Optional[str]:
        """Post a message to Facebook page."""
        try:
            if image_url:
                # Upload photo first
                photo_response = requests.post(
                    f"{self.base_url}/{self.page_id}/photos",
                    data={
                        "caption": message,
                        "access_token": self.access_token,
                        "url": image_url
                    }
                )
                if photo_response.status_code == 200:
                    photo_data = photo_response.json()
                    self.logger.info(f"Photo posted to Facebook successfully: {photo_data['id']}")
                    return photo_data['id']
                else:
                    self.logger.error(f"Failed to post photo to Facebook: {photo_response.text}")
                    return None
            else:
                # Post text only
                response = requests.post(
                    f"{self.base_url}/{self.page_id}/feed",
                    data={
                        "message": message,
                        "access_token": self.access_token
                    }
                )
                if response.status_code == 200:
                    post_data = response.json()
                    self.logger.info(f"Post created on Facebook successfully: {post_data['id']}")
                    return post_data['id']
                else:
                    self.logger.error(f"Failed to post to Facebook: {response.text}")
                    return None
        except Exception as e:
            self.logger.error(f"Error posting to Facebook: {e}")
            return None

    def get_page_posts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent posts from the Facebook page."""
        try:
            response = requests.get(
                f"{self.base_url}/{self.page_id}/posts",
                params={
                    "access_token": self.access_token,
                    "fields": "id,message,created_time,likes.summary(true),comments.summary(true)",
                    "limit": limit
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                self.logger.error(f"Failed to get Facebook posts: {response.text}")
                return []
        except Exception as e:
            self.logger.error(f"Error getting Facebook posts: {e}")
            return []

    def get_post_engagement(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get engagement metrics for a specific post."""
        try:
            response = requests.get(
                f"{self.base_url}/{post_id}",
                params={
                    "access_token": self.access_token,
                    "fields": "likes.summary(true),comments.summary(true),shares"
                }
            )
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get post engagement: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting post engagement: {e}")
            return None

    def create_facebook_ad_campaign(self, campaign_data: Dict[str, Any]) -> Optional[str]:
        """Create a Facebook ad campaign."""
        try:
            response = requests.post(
                f"{self.base_url}/{self.page_id}/adcampaigns",
                data={
                    "name": campaign_data.get("name"),
                    "objective": campaign_data.get("objective", "LINK_CLICKS"),
                    "access_token": self.access_token
                }
            )
            if response.status_code == 200:
                campaign_data = response.json()
                self.logger.info(f"Ad campaign created successfully: {campaign_data['id']}")
                return campaign_data['id']
            else:
                self.logger.error(f"Failed to create ad campaign: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error creating ad campaign: {e}")
            return None

    def get_page_insights(self, metric: str = "page_impressions", since: str = None, until: str = None) -> List[Dict[str, Any]]:
        """Get page insights for the Facebook page.
        
        Args:
            metric: Metric to retrieve (page_impressions, page_engagements, etc.)
            since: Start date (ISO format)
            until: End date (ISO format)
        
        Returns:
            List of insight data points
        """
        try:
            params = {
                "metric": metric,
                "access_token": self.access_token
            }
            if since:
                params["since"] = since
            if until:
                params["until"] = until

            response = requests.get(
                f"{self.base_url}/{self.page_id}/insights",
                params=params
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                self.logger.error(f"Failed to get page insights: {response.text}")
                return []
        except Exception as e:
            self.logger.error(f"Error getting page insights: {e}")
            return []
    
    def schedule_post(self, message: str, schedule_time: datetime, image_url: Optional[str] = None) -> Optional[str]:
        """Schedule a post for later publishing.
        
        Args:
            message: Post message content
            schedule_time: When to publish the post
            image_url: Optional image URL to include
        
        Returns:
            Post ID if scheduled successfully, None otherwise
        """
        try:
            # Convert datetime to timestamp
            scheduled_time = int(schedule_time.timestamp())
            
            data = {
                "message": message,
                "published": False,  # Don't publish immediately
                "scheduled_publish_time": scheduled_time
            }
            
            if image_url:
                # Schedule photo post
                data["url"] = image_url
                endpoint = f"{self.page_id}/photos"
            else:
                # Schedule text post
                endpoint = f"{self.page_id}/feed"
            
            response = self._make_request("POST", endpoint, data)
            
            if response and response.status_code == 200:
                post_data = response.json()
                self.logger.info(f"Post scheduled for {schedule_time}: {post_data['id']}")
                return post_data['id']
            else:
                self.logger.error(f"Failed to schedule post: {response.text if response else 'Rate limited'}")
                return None
        except Exception as e:
            self.logger.error(f"Error scheduling post: {e}")
            return None
    
    def post_video(self, video_url: str, title: str, description: str = "") -> Optional[str]:
        """Post a video to Facebook page.
        
        Args:
            video_url: URL of the video file
            title: Video title
            description: Video description
        
        Returns:
            Video ID if posted successfully, None otherwise
        """
        try:
            data = {
                "title": title,
                "description": description,
                "file_url": video_url,
                "published": True
            }
            
            response = self._make_request("POST", f"{self.page_id}/videos", data)
            
            if response and response.status_code == 200:
                video_data = response.json()
                self.logger.info(f"Video posted successfully: {video_data['id']}")
                return video_data['id']
            else:
                self.logger.error(f"Failed to post video: {response.text if response else 'Rate limited'}")
                return None
        except Exception as e:
            self.logger.error(f"Error posting video: {e}")
            return None
    
    def post_link(self, link_url: str, title: str, description: str = "", message: str = "") -> Optional[str]:
        """Post a link to Facebook page.
        
        Args:
            link_url: URL to share
            title: Link title
            description: Link description
            message: Additional message
        
        Returns:
            Post ID if posted successfully, None otherwise
        """
        try:
            data = {
                "link": link_url,
                "name": title,
                "description": description,
                "message": message
            }
            
            response = self._make_request("POST", f"{self.page_id}/feed", data)
            
            if response and response.status_code == 200:
                post_data = response.json()
                self.logger.info(f"Link posted successfully: {post_data['id']}")
                return post_data['id']
            else:
                self.logger.error(f"Failed to post link: {response.text if response else 'Rate limited'}")
                return None
        except Exception as e:
            self.logger.error(f"Error posting link: {e}")
            return None
    
    def get_post_comments(self, post_id: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Get comments on a post.
        
        Args:
            post_id: Post ID to get comments from
            limit: Maximum number of comments to retrieve
        
        Returns:
            List of comment objects
        """
        try:
            params = {
                "access_token": self.access_token,
                "fields": "comments.limit({limit}){{from,message,created_time,id}}".format(limit=limit),
                "limit": "1"
            }
            
            response = self._make_request("GET", post_id, params)
            
            if response and response.status_code == 200:
                data = response.json()
                comments = data.get("comments", {}).get("data", [])
                return comments
            else:
                self.logger.error(f"Failed to get post comments: {response.text if response else 'Rate limited'}")
                return []
        except Exception as e:
            self.logger.error(f"Error getting post comments: {e}")
            return []
    
    def post_comment_reply(self, comment_id: str, message: str) -> Optional[str]:
        """Reply to a comment on a post.
        
        Args:
            comment_id: Comment ID to reply to
            message: Reply message
        
        Returns:
            Comment ID if replied successfully, None otherwise
        """
        try:
            data = {
                "message": message,
                "comment_id": comment_id
            }
            
            response = self._make_request("POST", "me/comments", data)
            
            if response and response.status_code == 200:
                comment_data = response.json()
                self.logger.info(f"Comment reply posted: {comment_data['id']}")
                return comment_data['id']
            else:
                self.logger.error(f"Failed to post comment reply: {response.text if response else 'Rate limited'}")
                return None
        except Exception as e:
            self.logger.error(f"Error posting comment reply: {e}")
            return None
    
    def auto_respond_to_comments(self, post_id: str, keyword_responses: Dict[str, str] = None) -> int:
        """Automatically respond to comments based on keywords.
        
        Args:
            post_id: Post ID to monitor
            keyword_responses: Dictionary of keyword -> response message
        
        Returns:
            Number of auto-responses posted
        """
        if keyword_responses is None:
            # Default responses
            keyword_responses = {
                "price": "Thanks for your interest! Please check our website for pricing details.",
                "contact": "You can reach us at info@example.com or call us at +1-234-567-8900",
                "thanks": "You're welcome! Feel free to ask if you have any questions.",
                "hello": "Hello! How can we help you today?"
            }
        
        comments = self.get_post_comments(post_id)
        responses_count = 0
        
        for comment in comments:
            comment_message = comment.get("message", "").lower()
            comment_id = comment.get("id")
            
            # Check if already replied (simple check - can be enhanced)
            if "replied" in comment:
                continue
            
            # Find matching keyword
            for keyword, response in keyword_responses.items():
                if keyword in comment_message:
                    # Post reply
                    if self.post_comment_reply(comment_id, response):
                        responses_count += 1
                        self.logger.info(f"Auto-responded to comment with keyword: {keyword}")
                    break
        
        self.logger.info(f"Auto-responded to {responses_count} comments on post {post_id}")
        return responses_count
    
    def get_analytics_summary(self, period: str = "week") -> Dict[str, Any]:
        """Get comprehensive analytics summary.
        
        Args:
            period: Time period (day, week, month)
        
        Returns:
            Dictionary with analytics summary
        """
        # Calculate date range
        end_date = datetime.now()
        if period == "day":
            start_date = end_date - timedelta(days=1)
        elif period == "week":
            start_date = end_date - timedelta(days=7)
        elif period == "month":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=7)
        
        # Get metrics
        impressions = self.get_page_insights("page_impressions", start_date.isoformat(), end_date.isoformat())
        engagements = self.get_page_insights("page_engagements", start_date.isoformat(), end_date.isoformat())
        likes = self.get_page_insights("page_fan_adds", start_date.isoformat(), end_date.isoformat())
        
        # Calculate totals
        total_impressions = sum(m.get("values", [{}])[0].get("value", 0) for m in impressions)
        total_engagements = sum(m.get("values", [{}])[0].get("value", 0) for m in engagements)
        total_likes = sum(m.get("values", [{}])[0].get("value", 0) for m in likes)
        
        summary = {
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "impressions": total_impressions,
            "engagements": total_engagements,
            "likes": total_likes,
            "engagement_rate": (total_engagements / total_impressions * 100) if total_impressions > 0 else 0
        }
        
        self.logger.info(f"Analytics summary for {period}: {total_impressions} impressions, {total_engagements} engagements")
        return summary


# Global Facebook instance
facebook = FacebookIntegration()