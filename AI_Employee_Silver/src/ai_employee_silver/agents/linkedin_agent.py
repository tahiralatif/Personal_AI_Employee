"""
LinkedIn Agent for AI Employee System

Autonomous agent that manages LinkedIn posts, schedules content,
and publishes with human approval workflow.

Powered by Gemini via OpenAI Agents SDK.
"""

from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel, AsyncOpenAI
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from ..tools.linkedin_tools import (
    read_scheduled_posts,
    publish_linkedin_post,
    get_post_engagement,
    move_post_to_done
)
from ..tools.approval_tools import request_approval


async def run_linkedin_agent():
    """Run LinkedIn Agent - Autonomous post management and publishing."""
    
    # Get Gemini API configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    if not GEMINI_API_KEY:
        print("❌ Error: GEMINI_API_KEY not found in .env")
        print("\nPlease add your Gemini API key to .env file:")
        print("GEMINI_API_KEY=your_api_key_here")
        print("\nGet your free API key from: https://aistudio.google.com/apikey")
        return
    
    # Initialize OpenAI client with Gemini
    external_client = AsyncOpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    
    # Configure model
    model = OpenAIChatCompletionsModel(
        model=MODEL_NAME,
        openai_client=external_client
    )
    
    # Run configuration
    config = RunConfig(
        model=model,
        model_provider=external_client,
        tracing_disabled=True
    )
    
    # Define LinkedIn Agent
    agent = Agent(
        name="LinkedInAgent",
        instructions="""You are a LinkedIn AI Agent for the AI Employee system.

## Your Responsibilities:
1. Read scheduled posts from Plans folder
2. Publish posts at scheduled times
3. Track engagement metrics
4. Request approval before publishing
5. Move published posts to Done folder

## Available Tools:
- read_scheduled_posts: Fetch posts from Plans folder
- publish_linkedin_post: Publish to LinkedIn (with or without images)
- get_post_engagement: Track likes, comments, shares
- move_post_to_done: Move published posts to Done folder
- request_approval: Request human approval before publishing

## Workflow:
1. Check for scheduled posts: read_scheduled_posts()
2. For each post:
   a. Check if scheduled time has arrived
   b. Review content for quality
   c. Request approval: request_approval
   d. If approved, publish: publish_linkedin_post
   e. Track engagement: get_post_engagement
   f. Move to Done: move_post_to_done
3. Report back to user with summary

## Content Guidelines:
- Professional tone
- Engaging and valuable content
- Appropriate hashtags (3-5)
- Max 1300 characters for text posts
- Include images when available

## Important Rules:
- ALWAYS request approval before publishing
- Maintain brand voice
- Check scheduled times carefully
- Track and report engagement metrics
- Move posts to Done after publishing

## Response Style:
- Professional and polished
- Marketing-savvy
- Data-driven (mention engagement metrics)
- Strategic thinking

## Example Interactions:

User: "Check scheduled posts"
You: "Let me check your scheduled LinkedIn posts..."

User: "Publish the post about AI"
You: "I'll request approval and then publish the post about AI..."

User: "How did my last post perform?"
You: "Let me check the engagement metrics for your last post..."
""",
        tools=[
            read_scheduled_posts,
            publish_linkedin_post,
            get_post_engagement,
            move_post_to_done,
            request_approval
        ]
    )
    
    # Interactive loop
    history = []
    
    print("💼 " + "="*60)
    print("LinkedIn Agent Ready")
    print("="*60)
    print("\nI can help you:")
    print("✓ Manage scheduled LinkedIn posts")
    print("✓ Publish posts at scheduled times")
    print("✓ Track engagement metrics")
    print("✓ Request approval before publishing")
    print("\nTry these commands:")
    print("  - 'Check scheduled posts'")
    print("  - 'Publish the next post'")
    print("  - 'How did my last post perform?'")
    print("  - 'Create a post about AI trends'")
    print("\nType 'exit' to quit.\n")
    print("="*60)
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                print("\n👋 LinkedIn Agent signing off. Goodbye!")
                break
            
            # Add user message to history
            history.append({"role": "user", "content": user_input})
            
            # Run agent
            print("\n🤖 Agent: ", end="", flush=True)
            
            result = Runner.run_streamed(
                starting_agent=agent,
                input=history,
                run_config=config
            )
            
            # Stream response
            from openai.types.responses import ResponseTextDeltaEvent
            
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    print(event.data.delta, end="", flush=True)
            
            print("\n")
            
            # Update history with agent response
            history = result.to_input_list()
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. LinkedIn Agent signing off.")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again.")


if __name__ == "__main__":
    print("Starting LinkedIn Agent...\n")
    asyncio.run(run_linkedin_agent())
