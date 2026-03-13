"""
WhatsApp Agent for AI Employee System

Autonomous agent that monitors WhatsApp messages, detects tasks,
and creates action files with human approval workflow.

Powered by Gemini via OpenAI Agents SDK.
"""

from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel, AsyncOpenAI
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

from ..tools.whatsapp_tools import (
    monitor_whatsapp_messages,
    send_whatsapp_message,
    detect_task_keywords,
    create_whatsapp_task_file,
    send_approval_request
)
from ..tools.approval_tools import request_approval


async def run_whatsapp_agent():
    """Run WhatsApp Agent - Autonomous message monitoring with task detection."""
    
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
    
    # Define WhatsApp Agent
    agent = Agent(
        name="WhatsAppAgent",
        instructions="""You are a WhatsApp AI Agent for the AI Employee system.

## Your Responsibilities:
1. Monitor WhatsApp messages continuously
2. Detect task keywords in messages (English and Urdu)
3. Create action files for detected tasks
4. Send approval requests to human
5. Support multilingual messages (English, Urdu, Hindi)

## Available Tools:
- monitor_whatsapp_messages: Fetch recent WhatsApp messages
- send_whatsapp_message: Send notifications and responses
- detect_task_keywords: Analyze messages for task keywords
- create_whatsapp_task_file: Create action files for tasks
- send_approval_request: Send approval requests via WhatsApp
- request_approval: Create approval requests in vault

## Task Keywords to Detect:

### English:
please, need, urgent, task, action, required, must, should, remind, todo, do this, complete, finish, send, prepare

### Urdu (transliterated):
meharbani, baraaye, zaroori, kaam, chahiye, bhejo, taiyar, complete

## Workflow:
1. Check for new messages: monitor_whatsapp_messages(limit=10)
2. For each message:
   a. Analyze for task keywords: detect_task_keywords
   b. If task detected:
      - Create task file: create_whatsapp_task_file
      - Request approval: request_approval or send_approval_request
   c. If not a task, acknowledge politely
3. Report back to user with summary

## Important Rules:
- Support both English and Urdu messages
- Be friendly and conversational
- ALWAYS request approval for detected tasks
- Send notifications to user's phone
- Keep conversation context

## Response Style:
- Friendly and helpful
- Use emojis appropriately
- Support code-switching (Urdu + English mix)
- Be concise but thorough

## Example Interactions:

User: "Check my WhatsApp messages"
You: "Let me check your recent WhatsApp messages..."

User: "Any new tasks?"
You: "I found 2 new messages. One contains a task request..."
""",
        tools=[
            monitor_whatsapp_messages,
            send_whatsapp_message,
            detect_task_keywords,
            create_whatsapp_task_file,
            send_approval_request,
            request_approval
        ]
    )
    
    # Interactive loop
    history = []
    
    print("💬 " + "="*60)
    print("WhatsApp Agent Ready")
    print("="*60)
    print("\nI can help you:")
    print("✓ Monitor WhatsApp messages 24/7")
    print("✓ Detect tasks in English & Urdu")
    print("✓ Create action files automatically")
    print("✓ Send approval requests")
    print("\nTry these commands:")
    print("  - 'Check my WhatsApp messages'")
    print("  - 'Any new tasks?'")
    print("  - 'Send a message to +923151082542'")
    print("\nType 'exit' to quit.\n")
    print("="*60)
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                print("\n👋 WhatsApp Agent signing off. Goodbye!")
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
            print("\n\n👋 Interrupted. WhatsApp Agent signing off.")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again.")


if __name__ == "__main__":
    print("Starting WhatsApp Agent...\n")
    asyncio.run(run_whatsapp_agent())
