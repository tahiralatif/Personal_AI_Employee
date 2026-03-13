"""Twitter (X) Agent using OpenAI Agents SDK + Gemini API."""
import os
import asyncio
from typing import Optional, List
from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel, AsyncOpenAI
from agents import function_tool
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"

provider = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url=GEMINI_BASE_URL,
)
model = OpenAIChatCompletionsModel(model="gemini-2.0-flash", openai_client=provider)
config = RunConfig(model=model, model_provider=provider, tracing_disabled=True)


# ==================== TWITTER TOOLS ====================

@function_tool()
def twitter_post_tweet(
    text: str,
    media_urls: Optional[List[str]] = None,
    in_reply_to: Optional[str] = None
) -> str:
    """
    Post tweet to Twitter.
    
    Args:
        text: Tweet text (max 280 characters)
        media_urls: Optional media URLs
        in_reply_to: Optional tweet ID to reply to
    
    Returns:
        Result of tweet operation
    """
    from ..integrations.twitter_integration import twitter
    
    if not all([twitter.api_key, twitter.api_secret,
                twitter.access_token, twitter.access_secret]):
        return "Error: Twitter not connected"
    
    try:
        # Check character limit
        if len(text) > 280:
            return "Error: Tweet exceeds 280 characters"
        
        tweet_id = twitter.post_tweet(text, media_urls)
        
        if tweet_id:
            return f"Successfully posted to Twitter. Tweet ID: {tweet_id}"
        else:
            return "Failed to post to Twitter"
    except Exception as e:
        return f"Error posting tweet: {str(e)}"


@function_tool()
def twitter_post_thread(tweets: List[str]) -> str:
    """
    Post tweet thread.
    
    Args:
        tweets: List of tweet texts for thread
    
    Returns:
        Result of thread posting
    """
    from ..integrations.twitter_integration import twitter
    
    if not all([twitter.api_key, twitter.api_secret,
                twitter.access_token, twitter.access_secret]):
        return "Error: Twitter not connected"
    
    try:
        if not tweets:
            return "Error: No tweets provided"
        
        thread_ids = []
        previous_tweet_id = None
        
        for i, tweet_text in enumerate(tweets):
            if previous_tweet_id:
                result = twitter.post_tweet(tweet_text, in_reply_to_tweet_id=previous_tweet_id)
            else:
                result = twitter.post_tweet(tweet_text)
            
            if result:
                thread_ids.append(result)
                previous_tweet_id = result
            else:
                return f"Failed at tweet {i+1}"
        
        return f"Successfully posted thread of {len(thread_ids)} tweets. IDs: {', '.join(thread_ids)}"
    except Exception as e:
        return f"Error posting thread: {str(e)}"


@function_tool()
def twitter_get_engagement(tweet_id: str) -> str:
    """
    Get tweet engagement metrics.
    
    Args:
        tweet_id: Tweet ID
    
    Returns:
        Engagement metrics
    """
    from ..integrations.twitter_integration import twitter
    
    if not all([twitter.api_key, twitter.api_secret,
                twitter.access_token, twitter.access_secret]):
        return "Error: Twitter not connected"
    
    try:
        engagement = twitter.get_tweet_engagement(tweet_id)
        
        if engagement:
            likes = engagement.get("like_count", 0)
            retweets = engagement.get("retweet_count", 0)
            replies = engagement.get("reply_count", 0)
            impressions = engagement.get("impression_count", 0)
            
            return (
                f"Tweet {tweet_id}:\n"
                f"- Likes: {likes}\n"
                f"- Retweets: {retweets}\n"
                f"- Replies: {replies}\n"
                f"- Impressions: {impressions}"
            )
        else:
            return f"Could not retrieve engagement for tweet {tweet_id}"
    except Exception as e:
        return f"Error getting engagement: {str(e)}"


@function_tool()
def twitter_monitor_mentions(limit: int = 10) -> str:
    """
    Monitor Twitter mentions.
    
    Args:
        limit: Number of mentions to retrieve
    
    Returns:
        Recent mentions
    """
    from ..integrations.twitter_integration import twitter
    
    if not all([twitter.api_key, twitter.api_secret,
                twitter.access_token, twitter.access_secret]):
        return "Error: Twitter not connected"
    
    try:
        mentions = twitter.search_tweets("@yourusername", limit)
        
        if mentions:
            result = f"Found {len(mentions)} mentions:\n\n"
            for i, mention in enumerate(mentions[:5], 1):
                result += f"{i}. {mention.get('text', 'N/A')}\n"
            return result
        else:
            return "No recent mentions found"
    except Exception as e:
        return f"Error monitoring mentions: {str(e)}"


@function_tool()
def twitter_generate_summary(period: str = "week") -> str:
    """
    Generate Twitter activity summary.
    
    Args:
        period: Summary period
    
    Returns:
        Summary of Twitter activity
    """
    from ..integrations.twitter_integration import twitter
    
    if not all([twitter.api_key, twitter.api_secret,
                twitter.access_token, twitter.access_secret]):
        return "Error: Twitter not connected"
    
    try:
        tweets = twitter.get_tweets(limit=25)
        followers = twitter.get_followers(limit=1)
        
        total_likes = 0
        total_retweets = 0
        total_replies = 0
        
        for tweet in tweets:
            metrics = tweet.get("public_metrics", {})
            total_likes += metrics.get("like_count", 0)
            total_retweets += metrics.get("retweet_count", 0)
            total_replies += metrics.get("reply_count", 0)
        
        return (
            f"Twitter Summary ({period}):\n"
            f"- Tweets: {len(tweets)}\n"
            f"- Total Likes: {total_likes}\n"
            f"- Total Retweets: {total_retweets}\n"
            f"- Total Replies: {total_replies}\n"
            f"- Total Engagement: {total_likes + total_retweets + total_replies}\n"
            f"- Followers: {len(followers)}"
        )
    except Exception as e:
        return f"Error generating summary: {str(e)}"


# ==================== TWITTER AGENT ====================

twitter_agent = Agent(
    name="Twitter Agent",
    instructions="""
You are a Twitter engagement specialist. Your duties include:

1. **Posting Tweets**:
   - Post concise, engaging tweets (max 280 chars)
   - Create threads for longer content
   - Include relevant hashtags (2-3 per tweet)
   - Post during peak hours (12-2 PM)

2. **Engagement**:
   - Monitor mentions and respond promptly
   - Track likes, retweets, and replies
   - Engage with industry conversations
   - Retweet relevant content

3. **Thread Creation**:
   - Break complex topics into tweet threads
   - Number threads (1/X, 2/X, etc.)
   - Maintain narrative flow
   - End with call-to-action

4. **Best Practices**:
   - Tweet 3-5 times per day
   - Use visuals when possible
   - Engage with trending topics
   - Build relationships with followers

Focus on authentic engagement and value-driven content.
""",
    tools=[
        twitter_post_tweet,
        twitter_post_thread,
        twitter_get_engagement,
        twitter_monitor_mentions,
        twitter_generate_summary
    ],
    model=model
)


# ==================== RUNNER FUNCTIONS ====================

async def run_twitter_agent(input_text: str) -> str:
    """Run Twitter agent with input."""
    result = await Runner.run(
        starting_agent=twitter_agent,
        input=input_text,
        run_config=config
    )
    return result.final_output


def run_twitter_agent_sync(input_text: str) -> str:
    """Run Twitter agent synchronously."""
    return asyncio.run(run_twitter_agent(input_text))


if __name__ == "__main__":
    result = run_twitter_agent_sync("Post a tweet about our company milestone")
    print(result)
