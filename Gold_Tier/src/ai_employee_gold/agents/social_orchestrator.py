"""Unified Social Media Orchestrator with Handoffs.

This orchestrator routes social media tasks to specialist agents:
- Facebook Agent
- Instagram Agent
- Twitter Agent

Uses OpenAI Agents SDK handoff pattern.
"""
import os
import asyncio
from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel, AsyncOpenAI
from agents import handoff
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

# Import specialist agents
from .facebook_agent_sdk import facebook_agent
from .instagram_agent_sdk import instagram_agent
from .twitter_agent_sdk import twitter_agent


# ==================== UNIFIED TOOLS ====================

from agents import function_tool

@function_tool()
def post_to_all_platforms(
    content: str,
    media_urls: list = None,
    platforms: list = None
) -> str:
    """
    Post content to all specified platforms.
    
    Args:
        content: Post content
        media_urls: Optional media URLs
        platforms: List of platforms (facebook, instagram, twitter)
    
    Returns:
        Results from all platforms
    """
    results = {}
    
    if platforms is None:
        platforms = ["facebook", "instagram", "twitter"]
    
    # Post to each platform
    if "facebook" in platforms:
        from .facebook_agent_sdk import facebook_post_update
        results["facebook"] = facebook_post_update(content, media_urls[0] if media_urls else None)
    
    if "instagram" in platforms:
        from .instagram_agent_sdk import instagram_post_media
        results["instagram"] = instagram_post_media(
            media_urls[0] if media_urls else "",
            content
        )
    
    if "twitter" in platforms:
        from .twitter_agent_sdk import twitter_post_tweet
        results["twitter"] = twitter_post_tweet(content, media_urls)
    
    return f"Posted to {len(results)} platforms: {results}"


@function_tool()
def get_unified_analytics(period: str = "week") -> str:
    """
    Get analytics from all platforms.
    
    Args:
        period: Analytics period
    
    Returns:
        Unified analytics from all platforms
    """
    from .facebook_agent_sdk import facebook_generate_summary
    from .instagram_agent_sdk import instagram_generate_summary
    from .twitter_agent_sdk import twitter_generate_summary
    
    facebook_stats = facebook_generate_summary(period)
    instagram_stats = instagram_generate_summary(period)
    twitter_stats = twitter_generate_summary(period)
    
    return f"""
=== Unified Social Media Analytics ({period}) ===

FACEBOOK:
{facebook_stats}

INSTAGRAM:
{instagram_stats}

TWITTER:
{twitter_stats}
"""


@function_tool()
def generate_content_for_topic(topic: str, tone: str = "professional") -> str:
    """
    Generate content for topic optimized for each platform.
    
    Args:
        topic: Content topic
        tone: Content tone (professional, friendly, enthusiastic)
    
    Returns:
        Platform-specific content
    """
    # Platform-specific templates
    templates = {
        "facebook": f"📢 {topic}\n\nLearn more about {topic} and how it can help your business! #Business",
        "instagram": f"✨ {topic}\n\nDouble tap if you agree! 💙 #{topic.replace(' ', '')} #Business",
        "twitter": f"Excited to share insights about {topic}! 🚀 Read more: [link] #{topic.replace(' ', '')}"
    }
    
    if tone == "friendly":
        templates = {k: v + " 😊" for k, v in templates.items()}
    elif tone == "enthusiastic":
        templates = {k: v + " 🔥🎉" for k, v in templates.items()}
    
    return f"""
Generated content for topic: {topic}
Tone: {tone}

FACEBOOK:
{templates['facebook']}

INSTAGRAM:
{templates['instagram']}

TWITTER:
{templates['twitter']}
"""


# ==================== ORCHESTRATOR AGENT ====================

social_media_orchestrator = Agent(
    name="Social Media Orchestrator",
    instructions="""
You are a Social Media Orchestrator. Your role is to:

1. **Route Tasks** to specialist agents:
   - Facebook tasks → Facebook Agent
   - Instagram tasks → Instagram Agent  
   - Twitter tasks → Twitter Agent
   - Cross-platform tasks → Handle directly

2. **Handle Cross-Platform Tasks**:
   - Post to multiple platforms simultaneously
   - Generate unified analytics
   - Create platform-specific content

3. **Platform Selection Guide**:
   - **Facebook**: Business updates, events, long-form content
   - **Instagram**: Visual content, behind-the-scenes, lifestyle
   - **Twitter**: Quick updates, news, engagement, threads

4. **Best Practices**:
   - Maintain consistent brand voice across platforms
   - Optimize content for each platform
   - Track unified analytics
   - Require approval for sensitive topics

When a user request comes in, determine the best platform(s) and either:
- Handle it yourself using unified tools
- Handoff to specialist agent for platform-specific tasks
""",
    handoffs=[
        handoff(
            agent=facebook_agent,
            tool_name="transfer_to_facebook",
            description="Transfer to Facebook specialist for Facebook-specific tasks"
        ),
        handoff(
            agent=instagram_agent,
            tool_name="transfer_to_instagram",
            description="Transfer to Instagram specialist for Instagram-specific tasks"
        ),
        handoff(
            agent=twitter_agent,
            tool_name="transfer_to_twitter",
            description="Transfer to Twitter specialist for Twitter-specific tasks"
        )
    ],
    tools=[
        post_to_all_platforms,
        get_unified_analytics,
        generate_content_for_topic
    ],
    model=model
)


# ==================== RUNNER FUNCTIONS ====================

async def run_social_orchestrator(input_text: str) -> str:
    """Run social media orchestrator with input."""
    result = await Runner.run(
        starting_agent=social_media_orchestrator,
        input=input_text,
        run_config=config
    )
    return result.final_output


def run_social_orchestrator_sync(input_text: str) -> str:
    """Run social media orchestrator synchronously."""
    return asyncio.run(run_social_orchestrator(input_text))


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Example 1: Cross-platform post
    result = run_social_orchestrator_sync(
        "Post about our new product launch to all platforms"
    )
    print("Example 1 - Cross-platform post:")
    print(result)
    print("\n" + "="*60 + "\n")
    
    # Example 2: Platform-specific task (will handoff)
    result = run_social_orchestrator_sync(
        "Post an Instagram story about our team event"
    )
    print("Example 2 - Instagram story (handoff):")
    print(result)
    print("\n" + "="*60 + "\n")
    
    # Example 3: Analytics
    result = run_social_orchestrator_sync(
        "Get analytics from all platforms for this week"
    )
    print("Example 3 - Unified analytics:")
    print(result)
