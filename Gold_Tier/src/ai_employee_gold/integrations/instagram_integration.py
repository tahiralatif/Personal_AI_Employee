"""Instagram integration module for Gold Tier AI Employee system."""
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from ..config.settings import settings


class InstagramIntegration:
    """Integration with Instagram API for posting and monitoring."""

    def __init__(self):
        self.access_token = settings.INSTAGRAM_ACCESS_TOKEN
        self.user_id = settings.INSTAGRAM_USER_ID
        self.base_url = "https://graph.instagram.com"
        self.logger = logging.getLogger(self.__class__.__name__)

        if self.access_token:
            self.verify_connection()

    def verify_connection(self) -> bool:
        """Verify connection to Instagram API."""
        try:
            response = requests.get(
                f"{self.base_url}/me",
                params={"access_token": self.access_token, "fields": "id,username,account_type"}
            )
            if response.status_code == 200:
                data = response.json()
                self.user_id = data.get("id", self.user_id)
                self.logger.info(f"Successfully connected to Instagram account: {data.get('username', 'Unknown')}")
                return True
            else:
                self.logger.error(f"Failed to connect to Instagram: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error verifying Instagram connection: {e}")
            return False

    def create_media_container(self, image_url: str, caption: str) -> Optional[str]:
        """Create a media container for Instagram post."""
        try:
            response = requests.post(
                f"{self.base_url}/me/media",
                data={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": self.access_token
                }
            )
            if response.status_code == 200:
                data = response.json()
                container_id = data.get("id")
                self.logger.info(f"Media container created: {container_id}")
                return container_id
            else:
                self.logger.error(f"Failed to create media container: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error creating media container: {e}")
            return None

    def publish_media(self, container_id: str) -> Optional[str]:
        """Publish a media container to Instagram feed."""
        try:
            response = requests.post(
                f"{self.base_url}/me/media_publish",
                data={
                    "creation_id": container_id,
                    "access_token": self.access_token
                }
            )
            if response.status_code == 200:
                data = response.json()
                media_id = data.get("id")
                self.logger.info(f"Media published successfully: {media_id}")
                return media_id
            else:
                self.logger.error(f"Failed to publish media: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error publishing media: {e}")
            return None

    def post_to_instagram(self, image_url: str, caption: str) -> Optional[str]:
        """Post an image to Instagram with caption."""
        # Create media container first
        container_id = self.create_media_container(image_url, caption)
        if not container_id:
            return None

        # Wait a bit for the container to be processed
        import time
        time.sleep(2)

        # Publish the container
        return self.publish_media(container_id)

    def get_media_list(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Get list of media from Instagram account."""
        try:
            response = requests.get(
                f"{self.base_url}/me/media",
                params={
                    "fields": "id,caption,media_type,media_url,permalink,timestamp,username",
                    "limit": limit,
                    "access_token": self.access_token
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            else:
                self.logger.error(f"Failed to get media list: {response.text}")
                return []
        except Exception as e:
            self.logger.error(f"Error getting media list: {e}")
            return []

    def get_media_insights(self, media_id: str, metric_names: List[str]) -> Optional[Dict[str, Any]]:
        """Get insights for a specific media post."""
        try:
            response = requests.get(
                f"{self.base_url}/{media_id}/insights",
                params={
                    "metric": ",".join(metric_names),
                    "access_token": self.access_token
                }
            )
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get media insights: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting media insights: {e}")
            return None

    def get_account_summary(self) -> Optional[Dict[str, Any]]:
        """Get account summary metrics."""
        try:
            response = requests.get(
                f"{self.base_url}/me",
                params={
                    "fields": "id,username,account_type,followers_count,follows_count,media_count",
                    "access_token": self.access_token
                }
            )
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to get account summary: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting account summary: {e}")
            return None

    def create_carousel_container(self, media_urls: List[str], caption: str) -> Optional[str]:
        """Create a carousel media container for Instagram post."""
        try:
            # Create the carousel container
            response = requests.post(
                f"{self.base_url}/me/media",
                data={
                    "children": ",".join([f"ig_image_url={url}" for url in media_urls]),
                    "caption": caption,
                    "media_type": "CAROUSEL",
                    "access_token": self.access_token
                }
            )
            if response.status_code == 200:
                data = response.json()
                container_id = data.get("id")
                self.logger.info(f"Carousel container created: {container_id}")
                return container_id
            else:
                self.logger.error(f"Failed to create carousel container: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error creating carousel container: {e}")
            return None

    def post_story(self, image_url: str, caption: str = "") -> Optional[str]:
        """Post a story to Instagram."""
        try:
            response = requests.post(
                f"{self.base_url}/me/stories",
                data={
                    "image_url": image_url,
                    "caption": caption,
                    "access_token": self.access_token
                }
            )
            if response.status_code == 200:
                data = response.json()
                story_id = data.get("id")
                self.logger.info(f"Story posted successfully: {story_id}")
                return story_id
            else:
                self.logger.error(f"Failed to post story: {response.text}")
                return None
        except Exception as e:
            self.logger.error(f"Error posting story: {e}")
            return None


# Global Instagram instance
instagram = InstagramIntegration()