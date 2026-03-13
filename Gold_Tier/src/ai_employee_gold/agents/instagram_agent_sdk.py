"""Instagram Agent using OpenAI Agents SDK + Gemini API."""
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


# ==================== INSTAGRAM TOOLS ====================

@function_tool()
def instagram_post_media(
    image_url: str,
    caption: str,
    hashtags: Optional[List[str]] = None
) -> str:
    """
    Post media to Instagram.
    
    Args:
        image_url: Image URL to post
        caption: Post caption
        hashtags: Optional list of hashtags
    
    Returns:
        Result of post operation
    """
    from ..integrations.instagram_integration import instagram
    
    if not instagram.access_token:
        return "Error: Instagram not connected"
    
    try:
        # Add hashtags to caption
        if hashtags:
            hashtag_str = " ".join([f"#{tag}" for tag in hashtags])
            caption = f"{caption}\n\n{hashtag_str}"
        
        media_id = instagram.post_to_instagram(image_url, caption)
        
        if media_id:
            return f"Successfully posted to Instagram. Media ID: {media_id}"
        else:
            return "Failed to post to Instagram"
    except Exception as e:
        return f"Error posting to Instagram: {str(e)}"


@function_tool()
def instagram_post_story(
    image_url: str,
    sticker_text: Optional[str] = None
) -> str:
    """
    Post Instagram story.
    
    Args:
        image_url: Image URL for story
        sticker_text: Optional sticker text
    
    Returns:
        Result of story post
    """
    from ..integrations.instagram_integration import instagram
    
    if not instagram.access_token:
        return "Error: Instagram not connected"
    
    try:
        story_id = instagram.post_story(image_url, sticker_text or "")
        
        if story_id:
            return f"Successfully posted Instagram story. Story ID: {story_id}"
        else:
            return "Failed to post Instagram story"
    except Exception as e:
        return f"Error posting story: {str(e)}"


@function_tool()
def instagram_get_engagement(media_id: str) -> str:
    """
    Get engagement metrics for Instagram media.
    
    Args:
        media_id: Instagram media ID
    
    Returns:
        Engagement metrics
    """
    from ..integrations.instagram_integration import instagram
    
    if not instagram.access_token:
        return "Error: Instagram not connected"
    
    try:
        insights = instagram.get_media_insights(
            media_id,
            ["impressions", "reach", "engagement", "saved"]
        )
        
        if insights:
            impressions = insights.get("impressions", 0)
            reach = insights.get("reach", 0)
            engagement = insights.get("engagement", 0)
            saved = insights.get("saved", 0)
            
            return (
                f"Instagram Media {media_id}:\n"
                f"- Impressions: {impressions}\n"
                f"- Reach: {reach}\n"
                f"- Engagement: {engagement}\n"
                f"- Saved: {saved}"
            )
        else:
            return f"Could not retrieve engagement for media {media_id}"
    except Exception as e:
        return f"Error getting engagement: {str(e)}"


@function_tool()
def instagram_generate_summary(period: str = "week") -> str:
    """
    Generate Instagram activity summary.
    
    Args:
        period: Summary period
    
    Returns:
        Summary of Instagram activity
    """
    from ..integrations.instagram_integration import instagram
    
    if not instagram.access_token:
        return "Error: Instagram not connected"
    
    try:
        media_list = instagram.get_media_list(limit=25)
        account = instagram.get_account_summary()
        
        return (
            f"Instagram Summary ({period}):\n"
            f"- Posts: {len(media_list)}\n"
            f"- Followers: {account.get('followers_count', 0)}\n"
            f"- Following: {account.get('follows_count', 0)}\n"
            f"- Total Media: {account.get('media_count', 0)}\n"
            f"- Recent Posts: {min(5, len(media_list))}"
        )
    except Exception as e:
        return f"Error generating summary: {str(e)}"


@function_tool()
def instagram_optimize_hashtags(topic: str, count: int = 30) -> str:
    """
    Optimize hashtags for topic.
    
    Args:
        topic: Post topic
        count: Number of hashtags
    
    Returns:
        Optimized hashtag list
    """
    hashtag_db = {
        "business": ["business", "entrepreneur", "success", "motivation", "marketing"],
        "tech": ["technology", "innovation", "tech", "startup", "digital"],
        "lifestyle": ["lifestyle", "inspiration", "life", "motivation", "success"],
        "product": ["newproduct", "launch", "innovation", "quality", "shopping"]
    }
    
    selected = []
    for key, tags in hashtag_db.items():
        if key in topic.lower():
            selected.extend(tags)
    
    while len(selected) < count:
        selected.extend(["trending", "viral", "explore", "fyp", "instagood"])
    
    hashtags = selected[:count]
    
    return f"Optimized hashtags for '{topic}': {', '.join(hashtags)}"


# ==================== INSTAGRAM AGENT ====================

instagram_agent = Agent(
    name="Instagram Agent",
    instructions="""
You are an Instagram marketing specialist. Your duties include:

1. **Posting Content**:
   - Post high-quality images with engaging captions
   - Post stories for behind-the-scenes content
   - Use optimal hashtag strategies (20-30 hashtags)

2. **Engagement Monitoring**:
   - Track impressions, reach, and engagement
   - Monitor saves (indicates valuable content)
   - Analyze which content performs best

3. **Hashtag Strategy**:
   - Mix popular and niche hashtags
   - Use 20-30 relevant hashtags per post
   - Rotate hashtag sets to avoid shadowban

4. **Best Practices**:
   - Post consistently (1-2 times per day)
   - Use Stories daily
   - Engage with followers' comments
   - Post during peak hours (7-9 PM)

Focus on visual storytelling and authentic engagement.
""",
    tools=[
        instagram_post_media,
        instagram_post_story,
        instagram_get_engagement,
        instagram_generate_summary,
        instagram_optimize_hashtags
    ],
    model=model
)


# ==================== RUNNER FUNCTIONS ====================

async def run_instagram_agent(input_text: str) -> str:
    """Run Instagram agent with input."""
    result = await Runner.run(
        starting_agent=instagram_agent,
        input=input_text,
        run_config=config
    )
    return result.final_output


def run_instagram_agent_sync(input_text: str) -> str:
    """Run Instagram agent synchronously."""
    return asyncio.run(run_instagram_agent(input_text))


if __name__ == "__main__":
    result = run_instagram_agent_sync("Post an image about our team meeting")
    print(result)
