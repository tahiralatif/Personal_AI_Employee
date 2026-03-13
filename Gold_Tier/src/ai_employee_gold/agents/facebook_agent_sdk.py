"""Facebook Agent using OpenAI Agents SDK + Gemini API.

This agent follows the hackathon pattern for Agent Skills implementation.
"""
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


# ==================== FACEBOOK TOOLS ====================

@function_tool()
def facebook_post_update(
    message: str,
    image_url: Optional[str] = None,
    schedule_time: Optional[str] = None
) -> str:
    """
    Post update to Facebook page.
    
    Args:
        message: Post message content
        image_url: Optional image URL to include
        schedule_time: Optional schedule time (ISO format)
    
    Returns:
        Result of post operation
    """
    # Import integration
    from ..integrations.facebook_integration import facebook
    
    if not facebook.access_token:
        return "Error: Facebook not connected"
    
    try:
        post_id = facebook.post_to_facebook(message, image_url)
        
        if post_id:
            return f"Successfully posted to Facebook. Post ID: {post_id}"
        else:
            return "Failed to post to Facebook"
    except Exception as e:
        return f"Error posting to Facebook: {str(e)}"


@function_tool()
def facebook_get_engagement(post_id: str) -> str:
    """
    Get engagement metrics for Facebook post.
    
    Args:
        post_id: Facebook post ID
    
    Returns:
        Engagement metrics (likes, comments, shares)
    """
    from ..integrations.facebook_integration import facebook
    
    if not facebook.access_token:
        return "Error: Facebook not connected"
    
    try:
        engagement = facebook.get_post_engagement(post_id)
        
        if engagement:
            likes = engagement.get("likes", {}).get("summary", {}).get("total_count", 0)
            comments = engagement.get("comments", {}).get("summary", {}).get("total_count", 0)
            shares = engagement.get("shares", {}).get("count", 0)
            
            return f"Post {post_id} - Likes: {likes}, Comments: {comments}, Shares: {shares}"
        else:
            return f"Could not retrieve engagement for post {post_id}"
    except Exception as e:
        return f"Error getting engagement: {str(e)}"


@function_tool()
def facebook_generate_summary(period: str = "week") -> str:
    """
    Generate Facebook activity summary.
    
    Args:
        period: Summary period (day, week, month)
    
    Returns:
        Summary of Facebook activity
    """
    from ..integrations.facebook_integration import facebook
    
    if not facebook.access_token:
        return "Error: Facebook not connected"
    
    try:
        posts = facebook.get_page_posts(limit=25)
        
        total_likes = 0
        total_comments = 0
        total_shares = 0
        
        for post in posts:
            total_likes += post.get("likes", {}).get("summary", {}).get("total_count", 0)
            total_comments += post.get("comments", {}).get("summary", {}).get("total_count", 0)
            total_shares += post.get("shares", {}).get("count", 0)
        
        return (
            f"Facebook Summary ({period}):\n"
            f"- Posts: {len(posts)}\n"
            f"- Total Likes: {total_likes}\n"
            f"- Total Comments: {total_comments}\n"
            f"- Total Shares: {total_shares}\n"
            f"- Total Engagement: {total_likes + total_comments + total_shares}"
        )
    except Exception as e:
        return f"Error generating summary: {str(e)}"


@function_tool()
def facebook_schedule_post(
    message: str,
    schedule_time: str,
    image_url: Optional[str] = None
) -> str:
    """
    Schedule Facebook post for later publishing.
    
    Args:
        message: Post content
        schedule_time: Schedule time (ISO format)
        image_url: Optional image URL
    
    Returns:
        Confirmation of scheduled post
    """
    from ..core.vault import vault
    from datetime import datetime
    
    try:
        # Parse schedule time
        schedule_dt = datetime.fromisoformat(schedule_time)
        
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
"""
        
        plans_path.write_text(content)
        
        return f"Facebook post scheduled for {schedule_time}. File: {plans_path.name}"
    except Exception as e:
        return f"Error scheduling post: {str(e)}"


@function_tool()
def facebook_get_page_info() -> str:
    """
    Get Facebook page information.
    
    Returns:
        Page information (name, likes, about, etc.)
    """
    import requests
    from ..integrations.facebook_integration import facebook
    
    if not facebook.access_token:
        return "Error: Facebook not connected"
    
    try:
        response = requests.get(
            f"{facebook.base_url}/me",
            params={
                "access_token": facebook.access_token,
                "fields": "id,name,username,about,fan_count"
            }
        )
        
        if response.status_code == 200:
            page_info = response.json()
            return (
                f"Facebook Page:\n"
                f"- Name: {page_info.get('name')}\n"
                f"- Username: @{page_info.get('username', 'N/A')}\n"
                f"- Likes: {page_info.get('fan_count', 0)}\n"
                f"- About: {page_info.get('about', 'N/A')}"
            )
        else:
            return f"Failed to get page info: {response.text}"
    except Exception as e:
        return f"Error getting page info: {str(e)}"


# ==================== FACEBOOK AGENT ====================

facebook_agent = Agent(
    name="Facebook Agent",
    instructions="""
You are a Facebook marketing assistant. Your duties include:

1. **Posting Content**:
   - Post updates to Facebook page
   - Include images when provided
   - Schedule posts for optimal engagement times

2. **Monitoring Engagement**:
   - Track likes, comments, and shares
   - Report on post performance
   - Identify top-performing content

3. **Generating Reports**:
   - Create weekly/monthly summaries
   - Track follower growth
   - Analyze engagement trends

4. **Best Practices**:
   - Post during peak hours (9 AM - 1 PM)
   - Use engaging visuals
   - Respond to comments promptly
   - Track metrics for continuous improvement

Always be professional and on-brand. Require approval for sensitive topics.
""",
    tools=[
        facebook_post_update,
        facebook_get_engagement,
        facebook_generate_summary,
        facebook_schedule_post,
        facebook_get_page_info
    ],
    model=model
)


# ==================== RUNNER FUNCTIONS ====================

async def run_facebook_agent(input_text: str) -> str:
    """Run Facebook agent with input."""
    result = await Runner.run(
        starting_agent=facebook_agent,
        input=input_text,
        run_config=config
    )
    return result.final_output


def run_facebook_agent_sync(input_text: str) -> str:
    """Run Facebook agent synchronously."""
    return asyncio.run(run_facebook_agent(input_text))


if __name__ == "__main__":
    # Example usage
    result = run_facebook_agent_sync("Post an update about our new product launch")
    print(result)
