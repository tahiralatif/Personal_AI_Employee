"""Facebook integration module for Gold Tier AI Employee system."""
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from ..config.settings import settings


class FacebookIntegration:
    """Integration with Facebook API for posting and monitoring."""

    def __init__(self):
        self.access_token = settings.FACEBOOK_PAGE_ACCESS_TOKEN
        self.app_id = settings.FACEBOOK_APP_ID
        self.app_secret = settings.FACEBOOK_APP_SECRET
        self.page_id = None  # Will be set after authentication
        self.base_url = "https://graph.facebook.com/v18.0"
        self.logger = logging.getLogger(self.__class__.__name__)

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
        """Get page insights for the Facebook page."""
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


# Global Facebook instance
facebook = FacebookIntegration()