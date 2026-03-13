"""Twitter/X integration module for Gold Tier AI Employee system."""
import tweepy
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
from ..config.settings import settings


class TwitterIntegration:
    """Integration with Twitter/X API for posting and monitoring."""

    def __init__(self):
        self.api_key = settings.TWITTER_API_KEY
        self.api_secret = settings.TWITTER_API_SECRET
        self.access_token = settings.TWITTER_ACCESS_TOKEN
        self.access_secret = settings.TWITTER_ACCESS_SECRET
        self.client = None
        self.api = None
        self.logger = logging.getLogger(self.__class__.__name__)

        if all([self.api_key, self.api_secret, self.access_token, self.access_secret]):
            self.connect()

    def connect(self) -> bool:
        """Connect to Twitter/X API."""
        try:
            # Initialize tweepy client
            self.client = tweepy.Client(
                consumer_key=self.api_key,
                consumer_secret=self.api_secret,
                access_token=self.access_token,
                access_token_secret=self.access_secret
            )

            # Initialize tweepy API object for older endpoints
            auth = tweepy.OAuthHandler(self.api_key, self.api_secret)
            auth.set_access_token(self.access_token, self.access_secret)
            self.api = tweepy.API(auth)

            # Verify credentials
            me = self.client.get_me()
            if me:
                self.logger.info(f"Successfully connected to Twitter/X account: @{me.data.username}")
                return True
            else:
                self.logger.error("Failed to verify Twitter/X credentials")
                return False
        except Exception as e:
            self.logger.error(f"Error connecting to Twitter/X: {e}")
            return False

    def post_tweet(self, text: str, media_ids: Optional[List[str]] = None) -> Optional[str]:
        """Post a tweet to Twitter/X."""
        try:
            if media_ids:
                # For media, we need to use the API object
                response = self.api.update_status(text, media_ids=media_ids)
            else:
                # For text-only tweets, we can use the client
                response = self.client.create_tweet(text=text)

            tweet_id = getattr(response, 'id', getattr(response.data, 'id', None))
            self.logger.info(f"Tweet posted successfully: {tweet_id}")
            return str(tweet_id) if tweet_id else None
        except Exception as e:
            self.logger.error(f"Error posting tweet: {e}")
            return None

    def get_tweets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent tweets from the account."""
        try:
            tweets = self.client.get_users_tweets(
                id=self.client.get_me().data.id,
                max_results=min(limit, 100),
                tweet_fields=['created_at', 'public_metrics', 'context_annotations']
            )
            if tweets.data:
                return [tweet.data for tweet in tweets.data]
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error getting tweets: {e}")
            return []

    def get_tweet_engagement(self, tweet_id: str) -> Optional[Dict[str, Any]]:
        """Get engagement metrics for a specific tweet."""
        try:
            tweet = self.client.get_tweet(
                id=tweet_id,
                tweet_fields=['public_metrics', 'context_annotations']
            )
            if tweet.data:
                return tweet.data.public_metrics
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error getting tweet engagement: {e}")
            return None

    def search_tweets(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for tweets based on a query."""
        try:
            tweets = self.client.search_recent_tweets(
                query=query,
                max_results=min(limit, 100),
                tweet_fields=['created_at', 'author_id', 'public_metrics']
            )
            if tweets.data:
                return [tweet.data for tweet in tweets.data]
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error searching tweets: {e}")
            return []

    def like_tweet(self, tweet_id: str) -> bool:
        """Like a tweet."""
        try:
            response = self.client.like(tweet_id)
            if response:
                self.logger.info(f"Tweet liked successfully: {tweet_id}")
                return True
            else:
                return False
        except Exception as e:
            self.logger.error(f"Error liking tweet: {e}")
            return False

    def retweet(self, tweet_id: str) -> bool:
        """Retweet a tweet."""
        try:
            response = self.client.retweet(tweet_id)
            if response:
                self.logger.info(f"Tweet retweeted successfully: {tweet_id}")
                return True
            else:
                return False
        except Exception as e:
            self.logger.error(f"Error retweeting: {e}")
            return False

    def reply_to_tweet(self, tweet_id: str, text: str) -> Optional[str]:
        """Reply to a tweet."""
        try:
            response = self.client.create_tweet(text=text, in_reply_to_tweet_id=tweet_id)
            if response.data:
                reply_id = response.data.id
                self.logger.info(f"Reply posted successfully: {reply_id}")
                return str(reply_id)
            else:
                return None
        except Exception as e:
            self.logger.error(f"Error replying to tweet: {e}")
            return None

    def follow_user(self, user_id: str) -> bool:
        """Follow a user."""
        try:
            response = self.client.follow_user(user_id)
            if response:
                self.logger.info(f"User followed successfully: {user_id}")
                return True
            else:
                return False
        except Exception as e:
            self.logger.error(f"Error following user: {e}")
            return False

    def get_followers(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get followers of the account."""
        try:
            user_id = self.client.get_me().data.id
            followers = self.client.get_users_followers(
                id=user_id,
                max_results=min(limit, 1000),
                user_fields=['username', 'name', 'public_metrics', 'verified']
            )
            if followers.data:
                return [user.data for user in followers.data]
            else:
                return []
        except Exception as e:
            self.logger.error(f"Error getting followers: {e}")
            return []

    def get_trends(self) -> List[Dict[str, Any]]:
        """Get trending topics (requires premium access)."""
        try:
            # Note: Twitter API v2 doesn't have a direct trends endpoint
            # This is a simplified implementation
            # For full trend data, you'd need to use premium API or older v1.1 API
            self.logger.info("Trends retrieval requires premium access")
            return []
        except Exception as e:
            self.logger.error(f"Error getting trends: {e}")
            return []


# Global Twitter instance
twitter = TwitterIntegration()