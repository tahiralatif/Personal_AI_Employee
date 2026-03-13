"""
Gmail Agent for AI Employee System

Autonomous agent that monitors Gmail, processes emails with attachments,
and creates action files with human approval workflow.

Powered by Gemini via OpenAI Agents SDK.
"""

from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel, AsyncOpenAI
from openai.types.responses import ResponseTextDeltaEvent
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from ..tools.gmail_tools import (
    read_emails,
    get_email_details,
    save_attachment_to_inbox,
    create_email_action_file,
    mark_email_read
)
from ..tools.approval_tools import request_approval


async def run_gmail_agent():
    """Run Gmail Agent - Autonomous email processing with approval workflow."""
    
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
    
    # Define Gmail Agent
    agent = Agent(
        name="GmailAgent",
        instructions="""You are a Gmail AI Agent for the AI Employee system.

## Your Responsibilities:
1. Monitor Gmail for new emails, especially those with attachments
2. Read and analyze email content
3. Save attachments to Inbox folder
4. Create action files in Needs_Action folder
5. Request human approval before taking any action
6. Mark emails as read after processing

## Available Tools:
- read_emails: Fetch emails from Gmail (use query parameter for filtering)
- get_email_details: Get full content of a specific email
- save_attachment_to_inbox: Save email attachments to Inbox
- create_email_action_file: Create action files for tasks
- mark_email_read: Mark processed emails as read
- request_approval: Request human approval for tasks

## Workflow:
1. Check for new emails with: read_emails(query="is:unread has:attachment")
2. For each email:
   a. Get full details with get_email_details
   b. If attachments exist, save them with save_attachment_to_inbox
   c. Create action file with create_email_action_file
   d. Request approval with request_approval
   e. Mark as read with mark_email_read
3. Report back to user with summary

## Important Rules:
- ALWAYS request approval before processing emails
- Save ALL attachments to Inbox folder
- Create action files for ALL emails with tasks
- Be thorough and professional
- Support multiple languages (English, Urdu)

## Response Format:
- Provide clear summaries of actions taken
- Include file paths for created files
- Mention if approval is pending
""",
        tools=[
            read_emails,
            get_email_details,
            save_attachment_to_inbox,
            create_email_action_file,
            mark_email_read,
            request_approval
        ]
    )
    
    # Interactive loop
    history = []
    
    print("📧 " + "="*60)
    print("Gmail Agent Ready")
    print("="*60)
    print("\nI can help you:")
    print("✓ Monitor Gmail for new emails")
    print("✓ Save attachments to Inbox")
    print("✓ Create action files automatically")
    print("✓ Request approval before processing")
    print("\nTry these commands:")
    print("  - 'Check for new emails'")
    print("  - 'Process unread emails with attachments'")
    print("  - 'Show me recent emails'")
    print("\nType 'exit' to quit.\n")
    print("="*60)
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                print("\n👋 Gmail Agent signing off. Goodbye!")
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
            

            
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    print(event.data.delta, end="", flush=True)
            
            print("\n")
            
            # Update history with agent response
            history = result.to_input_list()
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Gmail Agent signing off.")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again.")


if __name__ == "__main__":
    print("Starting Gmail Agent...\n")
    asyncio.run(run_gmail_agent())
