"""
LinkedIn integration for Silver Tier AI Employee.

This module implements the LinkedInPoster class that:
- Connects to LinkedIn API using OAuth 2.0
- Reads scheduled posts from Plans/ folder
- Publishes posts at scheduled times
- Tracks engagement metrics
- Moves completed posts to Done/
"""

import base64
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

import requests

from ..config.settings import Settings, get_settings
from ..utils.logger import VaultLogger, get_logger


class LinkedInPost:
    """
    Represents a LinkedIn post to be published.

    Attributes:
        post_id: Unique post identifier
        content: Post text content
        image_path: Optional image file path
        scheduled_time: Scheduled publish time
        status: Post status (pending, published, failed)
    """

    def __init__(
        self,
        post_id: str,
        content: str,
        scheduled_time: datetime,
        image_path: Optional[str] = None,
        status: str = "pending"
    ) -> None:
        """Initialize LinkedInPost."""
        self.post_id = post_id
        self.content = content
        self.image_path = image_path
        self.scheduled_time = scheduled_time
        self.status = status
        self.published_url: Optional[str] = None
        self.engagement: Dict[str, int] = {"likes": 0, "comments": 0, "shares": 0}


class LinkedInPoster:
    """
    Manages LinkedIn post publishing.

    Responsibilities:
    - LinkedIn API authentication
    - Read posts from Plans/ folder
    - Publish posts at scheduled times
    - Track engagement metrics
    - Update post status
    """

    def __init__(
        self,
        settings: Optional[Settings] = None,
        logger: Optional[VaultLogger] = None
    ) -> None:
        """Initialize LinkedInPoster."""
        self.settings = settings if settings is not None else get_settings()
        self.logger = logger if logger is not None else get_logger()

        # LinkedIn API configuration
        self.client_id = self.settings.LINKEDIN_CLIENT_ID
        self.client_secret = self.settings.LINKEDIN_CLIENT_SECRET
        self.access_token = self.settings.LINKEDIN_ACCESS_TOKEN
        self.organization_id = self.settings.LINKEDIN_ORGANIZATION_ID
        self.api_version = self.settings.LINKEDIN_API_VERSION

        # API base URL
        self.base_url = "https://api.linkedin.com/v2"

        # Session for HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json"
        })

        # Retry configuration
        self.max_retries = self.settings.MAX_RETRY_ATTEMPTS
        self.initial_delay = self.settings.RETRY_INITIAL_DELAY
        self.max_delay = self.settings.RETRY_MAX_DELAY

        # Running state
        self._running = False

        # Plans folder path
        self.plans_path = Path(self.settings.VAULT_PATH).expanduser() / "Plans"
        self.done_path = Path(self.settings.VAULT_PATH).expanduser() / "Done"
        self.needs_action_path = Path(self.settings.VAULT_PATH).expanduser() / "Needs_Action"

    def authenticate(self) -> bool:
        """
        Verify LinkedIn API authentication.

        Returns:
            True if authenticated, False otherwise
        """
        try:
            if not self.settings.is_linkedin_configured():
                self.logger.warning("LinkedIn API not configured")
                return False

            # Test API connection
            endpoint = f"{self.base_url}/me"
            response = self._retry_request("GET", endpoint)

            if response:
                self.logger.info("LinkedIn API authentication successful")
                return True
            else:
                self.logger.error("LinkedIn API authentication failed")
                return False

        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return False

    def read_scheduled_posts(self) -> List[LinkedInPost]:
        """
        Read scheduled posts from Plans/ folder.

        Returns:
            List of LinkedInPost objects
        """
        posts = []

        try:
            if not self.plans_path.exists():
                self.plans_path.mkdir(parents=True, exist_ok=True)
                return posts

            # Find post files
            for post_file in self.plans_path.glob("*.md"):
                post = self._parse_post_file(post_file)
                if post and post.status == "pending":
                    posts.append(post)

            self.logger.info(f"Found {len(posts)} scheduled posts")
            return posts

        except Exception as e:
            self.logger.error(f"Failed to read scheduled posts: {str(e)}")
            return []

    def _parse_post_file(self, file_path: Path) -> Optional[LinkedInPost]:
        """
        Parse post file into LinkedInPost object.

        Args:
            file_path: Path to post file

        Returns:
            LinkedInPost object or None
        """
        try:
            content = file_path.read_text(encoding='utf-8')

            # Extract YAML frontmatter
            if not content.startswith("---"):
                return None

            parts = content.split("---", 2)
            if len(parts) < 3:
                return None

            frontmatter_text = parts[1].strip()
            body = parts[2].strip()

            # Parse frontmatter
            frontmatter = {}
            for line in frontmatter_text.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    frontmatter[key.strip()] = value.strip()

            # Check if it's a LinkedIn post
            if frontmatter.get("type") != "linkedin_post":
                return None

            # Parse scheduled time
            scheduled_str = frontmatter.get("scheduled_time", "")
            try:
                scheduled_time = datetime.fromisoformat(scheduled_str)
            except (ValueError, TypeError):
                scheduled_time = datetime.now()

            # Get image path if any
            image_path = frontmatter.get("image_path")

            return LinkedInPost(
                post_id=file_path.stem,
                content=body,
                scheduled_time=scheduled_time,
                image_path=image_path,
                status=frontmatter.get("status", "pending")
            )

        except Exception as e:
            self.logger.error(f"Failed to parse post file {file_path}: {str(e)}")
            return None

    def publish_post(self, post: LinkedInPost) -> bool:
        """
        Publish a LinkedIn post.

        Args:
            post: LinkedInPost to publish

        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Publishing post: {post.post_id}")

            # Check if scheduled time has arrived
            if datetime.now() < post.scheduled_time:
                self.logger.debug(f"Post {post.post_id} not yet scheduled")
                return False

            # Create post content
            post_data = self._create_post_payload(post)

            # Publish to LinkedIn
            endpoint = f"{self.base_url}/shares"
            response = self._retry_request("POST", endpoint, json=post_data)

            if response and "id" in response:
                post.published_url = response.get("permalink")
                post.status = "published"
                self.logger.info(f"Post published: {post.published_url}")

                # Update post file
                self._update_post_status(post)

                # Move to Done folder
                self._move_to_done(post)

                return True
            else:
                post.status = "failed"
                self.logger.error(f"Failed to publish post: {response}")
                self._move_to_needs_action(post, str(response))
                return False

        except Exception as e:
            self.logger.error(f"Error publishing post: {str(e)}")
            post.status = "failed"
            self._move_to_needs_action(post, str(e))
            return False

    def _create_post_payload(self, post: LinkedInPost) -> Dict[str, Any]:
        """
        Create LinkedIn API post payload.

        Args:
            post: LinkedInPost object

        Returns:
            API payload dictionary
        """
        # Base text content
        payload = {
            "owner": f"urn:li:organization:{self.organization_id}",
            "subject": "LinkedIn Post",
            "text": {
                "text": post.content[:1300]  # LinkedIn character limit
            },
            "visibility": "PUBLIC"
        }

        # Add image if present
        if post.image_path and os.path.exists(post.image_path):
            image_data = self._upload_image(post.image_path)
            if image_data:
                payload["content"] = {
                    "contentEntities": [
                        {
                            "entityLocation": image_data.get("url"),
                            "thumbnails": [
                                {
                                    "resolvedUrl": image_data.get("url")
                                }
                            ]
                        }
                    ],
                    "title": "Post Image"
                }

        return payload

    def _upload_image(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Upload image to LinkedIn.

        Args:
            image_path: Path to image file

        Returns:
            Image upload response or None
        """
        try:
            # Step 1: Register upload
            endpoint = f"{self.base_url}/images?action=registerUpload"
            register_data = {
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": f"urn:li:organization:{self.organization_id}",
                    "serviceRelationships": [
                        {
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent"
                        }
                    ]
                }
            }

            response = self._retry_request("POST", endpoint, json=register_data)
            if not response:
                return None

            upload_url = response.get("value", {}).get("uploadMechanism", {}).get(
                "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}
            ).get("uploadUrl")

            media_id = response.get("value", {}).get("image")

            if not upload_url or not media_id:
                return None

            # Step 2: Upload image bytes
            with open(image_path, "rb") as f:
                image_bytes = f.read()

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/octet-stream"
            }

            upload_response = requests.put(upload_url, data=image_bytes, headers=headers)
            upload_response.raise_for_status()

            return {"url": media_id}

        except Exception as e:
            self.logger.error(f"Failed to upload image: {str(e)}")
            return None

    def get_engagement_metrics(self, post_id: str) -> Dict[str, int]:
        """
        Get engagement metrics for a post.

        Args:
            post_id: LinkedIn post ID

        Returns:
            Dictionary with likes, comments, shares
        """
        try:
            endpoint = f"{self.base_url}/actions?q=actionSummary&values=(actionType,total)"
            params = {
                "object": f"urn:li:share:{post_id}",
                "actionTypes": "LIKE,COMMENT,SHARE"
            }

            response = self._retry_request("GET", endpoint, params=params)

            if response and "elements" in response:
                metrics = {"likes": 0, "comments": 0, "shares": 0}
                for element in response["elements"]:
                    action_type = element.get("actionType")
                    total = element.get("total", {}).get("count", 0)

                    if action_type == "LIKE":
                        metrics["likes"] = total
                    elif action_type == "COMMENT":
                        metrics["comments"] = total
                    elif action_type == "SHARE":
                        metrics["shares"] = total

                return metrics

            return {"likes": 0, "comments": 0, "shares": 0}

        except Exception as e:
            self.logger.error(f"Failed to get engagement: {str(e)}")
            return {"likes": 0, "comments": 0, "shares": 0}

    def _update_post_status(self, post: LinkedInPost) -> None:
        """Update post file with new status."""
        try:
            # Find original file
            for folder in [self.plans_path, self.done_path, self.needs_action_path]:
                file_path = folder / f"{post.post_id}.md"
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')

                    # Update status in frontmatter
                    lines = content.split("\n")
                    for i, line in enumerate(lines):
                        if line.startswith("status:"):
                            lines[i] = f"status: {post.status}"
                        elif line.startswith("published_url:") and post.published_url:
                            lines[i] = f"published_url: {post.published_url}"

                    # Add engagement if available
                    if hasattr(post, 'engagement'):
                        # Add engagement metrics
                        pass

                    content = "\n".join(lines)
                    file_path.write_text(content, encoding='utf-8')
                    break

        except Exception as e:
            self.logger.error(f"Failed to update post status: {str(e)}")

    def _move_to_done(self, post: LinkedInPost) -> None:
        """Move published post to Done folder."""
        try:
            self.done_path.mkdir(parents=True, exist_ok=True)

            for folder in [self.plans_path, self.needs_action_path]:
                src_path = folder / f"{post.post_id}.md"
                if src_path.exists():
                    dst_path = self.done_path / f"{post.post_id}.md"
                    src_path.rename(dst_path)
                    self.logger.info(f"Moved post to Done: {post.post_id}")
                    break

        except Exception as e:
            self.logger.error(f"Failed to move post to Done: {str(e)}")

    def _move_to_needs_action(self, post: LinkedInPost, error: str) -> None:
        """Move failed post to Needs_Action folder."""
        try:
            self.needs_action_path.mkdir(parents=True, exist_ok=True)

            for folder in [self.plans_path, self.done_path]:
                src_path = folder / f"{post.post_id}.md"
                if src_path.exists():
                    dst_path = self.needs_action_path / f"{post.post_id}.md"

                    # Add error to file
                    content = src_path.read_text(encoding='utf-8')
                    content += f"\n\n## Error\n{error}\n\nFailed at: {datetime.now().isoformat()}"

                    dst_path.write_text(content, encoding='utf-8')
                    src_path.unlink()

                    self.logger.warning(f"Moved failed post to Needs_Action: {post.post_id}")
                    break

        except Exception as e:
            self.logger.error(f"Failed to move post to Needs_Action: {str(e)}")

    def _retry_request(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """Make HTTP request with retry logic."""
        last_exception = None
        delay = self.initial_delay

        for attempt in range(self.max_retries):
            try:
                response = self.session.request(method, url, timeout=30, **kwargs)
                response.raise_for_status()
                return response.json()

            except requests.exceptions.HTTPError as e:
                last_exception = e
                status_code = e.response.status_code

                if status_code == 429 or 500 <= status_code < 600:
                    self.logger.warning(f"HTTP {status_code}, retrying in {delay}s...")
                    time.sleep(delay)
                    delay = min(delay * 2, self.max_delay)
                    continue
                else:
                    self.logger.error(f"HTTP error {status_code}: {str(e)}")
                    return None

            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.warning(f"Request failed (attempt {attempt + 1}): {str(e)}")
                time.sleep(delay)
                delay = min(delay * 2, self.max_delay)

        self.logger.error(f"All {self.max_retries} retries failed")
        return None

    def run_once(self) -> int:
        """
        Run one iteration of post publishing.

        Returns:
            Number of posts published
        """
        try:
            posts = self.read_scheduled_posts()
            published_count = 0

            for post in posts:
                if self.publish_post(post):
                    published_count += 1

            return published_count

        except Exception as e:
            self.logger.error(f"Error in run_once: {str(e)}")
            return 0

    def run_forever(self, check_interval: int = 60) -> None:
        """
        Run LinkedIn poster continuously.

        Args:
            check_interval: Check interval in seconds
        """
        self._running = True
        self.logger.info(f"Starting LinkedIn poster (check interval: {check_interval}s)")

        try:
            while self._running:
                try:
                    self.run_once()
                except Exception as e:
                    self.logger.error(f"Error in publishing loop: {str(e)}")

                time.sleep(check_interval)

        except KeyboardInterrupt:
            self.logger.info("KeyboardInterrupt received, stopping LinkedIn poster")
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop the LinkedIn poster."""
        self.logger.info("Stopping LinkedIn poster...")
        self._running = False
        self.logger.log_event(
            event_type="system_stop",
            detail="LinkedIn poster stopped",
            result="success"
        )


def create_linkedin_poster(
    settings: Optional[Settings] = None,
    logger: Optional[VaultLogger] = None
) -> LinkedInPoster:
    """Factory function to create LinkedInPoster instance."""
    return LinkedInPoster(settings, logger)


if __name__ == "__main__":
    print("Starting LinkedIn Poster (Test Mode)...")

    settings = get_settings()
    logger = get_logger()

    poster = create_linkedin_poster(settings, logger)

    if settings.is_linkedin_configured():
        print("✓ LinkedIn API configured")

        if poster.authenticate():
            print("✓ Authentication successful")

            posts = poster.read_scheduled_posts()
            print(f"✓ Found {len(posts)} scheduled posts")

            published = poster.run_once()
            print(f"✓ Published {published} posts")

            print("\nTo run continuously: python -m src.ai_employee_silver.main start linkedin")
    else:
        print("✗ LinkedIn API not configured")
        print("  Please check credentials in .env")
