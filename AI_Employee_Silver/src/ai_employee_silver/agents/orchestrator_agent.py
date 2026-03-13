"""
Orchestrator Agent for AI Employee System

Main coordinator agent that routes tasks to existing sub-agents
using handoffs.

Powered by Gemini via OpenAI Agents SDK.
"""

from agents import Agent, Runner, RunConfig, OpenAIChatCompletionsModel, AsyncOpenAI, handoff
from openai.types.responses import ResponseTextDeltaEvent
import os
import asyncio
from dotenv import load_dotenv
 # =====================================================================
    # IMPORT EXISTING AGENTS (already configured with tools)
    # =====================================================================
    
    # Import existing agents from their files
from .gmail_agent import run_gmail_agent
from .whatsapp_agent import run_whatsapp_agent
from .linkedin_agent import run_linkedin_agent

load_dotenv()


async def run_orchestrator():
    """Run Orchestrator Agent - Main coordinator with handoffs to existing agents."""
    
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
    
   
    
    # =====================================================================
    # CREATE HANDOFFS (using existing agents' capabilities)
    # =====================================================================
    
    # 📧 Gmail Agent Handoff
    gmail_handoff = handoff(
        agent=Agent(
            name="GmailAgent",
            instructions="""You are a Gmail AI Agent.

YOUR AUTONOMOUS DUTIES:
1. Check for new emails with attachments
2. Save attachments to Inbox folder
3. Create action files for emails
4. Request human approval before processing
5. Mark emails as read after processing

WORKFLOW:
1. Use read_emails(query="is:unread has:attachment")
2. For each email:
   - Get details with get_email_details
   - Save attachments with save_attachment_to_inbox
   - Create action file with create_email_action_file
   - Request approval with request_approval
   - Mark as read with mark_email_read
3. Report summary

Be autonomous and thorough.
""",
            # Tools are imported in gmail_agent.py - agent will use them
        ),
        tool_name="transfer_to_gmail",
        description="Transfer to Gmail Agent for email tasks (read emails, save attachments, create action files)"
    )
    
    # 💬 WhatsApp Agent Handoff
    whatsapp_handoff = handoff(
        agent=Agent(
            name="WhatsAppAgent",
            instructions="""You are a WhatsApp AI Agent.

YOUR AUTONOMOUS DUTIES:
1. Monitor WhatsApp messages every 30 seconds
2. Detect task keywords (English & Urdu)
3. Create action files for detected tasks
4. Send approval requests to human
5. Send notifications

WORKFLOW:
1. Use monitor_whatsapp_messages(limit=10)
2. For each message:
   - Analyze with detect_task_keywords
   - If task detected:
     * Create task file with create_whatsapp_task_file
     * Request approval with request_approval or send_approval_request
3. Report summary

TASK KEYWORDS:
- English: please, need, urgent, task, action, required, must, should
- Urdu: meharbani, zaroori, kaam, chahiye, bhejo, taiyar

Be autonomous and support multilingual messages.
""",
            # Tools are imported in whatsapp_agent.py - agent will use them
        ),
        tool_name="transfer_to_whatsapp",
        description="Transfer to WhatsApp Agent for message monitoring, task detection (English/Urdu), and approvals"
    )
    
    # 💼 LinkedIn Agent Handoff
    linkedin_handoff = handoff(
        agent=Agent(
            name="LinkedInAgent",
            instructions="""You are a LinkedIn AI Agent.

YOUR AUTONOMOUS DUTIES:
1. Check for scheduled posts every 2 minutes
2. Publish posts when scheduled time arrives
3. Track engagement metrics
4. Request approval before publishing
5. Move published posts to Done folder

WORKFLOW:
1. Use read_scheduled_posts()
2. For each post ready to publish:
   - Request approval with request_approval
   - If approved: publish with publish_linkedin_post
   - Track engagement with get_post_engagement
   - Move to Done with move_post_to_done
3. Report summary

Be autonomous and professional.
""",
            # Tools are imported in linkedin_agent.py - agent will use them
        ),
        tool_name="transfer_to_linkedin",
        description="Transfer to LinkedIn Agent for post management, publishing, and engagement tracking"
    )
    
    # =====================================================================
    # ORCHESTRATOR AGENT (with handoffs)
    # =====================================================================
    
    agent = Agent(
        name="OrchestratorAgent",
        instructions="""You are the Main Orchestrator AI Agent for the AI Employee system.

## Your Role:
You coordinate all sub-agents and route tasks to the appropriate specialist using handoffs.

## Available Handoffs:

### 📧 GmailAgent
**Use for:** Email tasks
**Examples:**
- "Check my emails"
- "Save attachments from Gmail"
- "Process unread emails"

### 💬 WhatsAppAgent
**Use for:** WhatsApp message monitoring and task detection
**Examples:**
- "Check WhatsApp messages"
- "Any new tasks from WhatsApp?"
- "Monitor my WhatsApp"

### 💼 LinkedInAgent
**Use for:** LinkedIn post management
**Examples:**
- "Post on LinkedIn"
- "Check scheduled posts"
- "Publish my content"

## Routing Logic:

1. **Analyze user request**
2. **Determine task type:**
   - Email/Gmail → transfer_to_gmail
   - WhatsApp → transfer_to_whatsapp
   - LinkedIn → transfer_to_linkedin
3. **Use appropriate handoff**
4. **Let specialist agent handle autonomously**

## Handle Yourself When:

- "System status" - Provide overall status
- "Help" - Show available commands
- "What can you do?" - Explain capabilities
- General questions

## Response Guidelines:

1. Identify task type quickly
2. Use handoff seamlessly
3. Preserve context
4. Be professional and helpful
""",
        handoffs=[gmail_handoff, whatsapp_handoff, linkedin_handoff]
    )
    
    # Interactive loop
    history = []
    
    print("🎯 " + "="*60)
    print("Orchestrator Agent Ready (with Handoffs)")
    print("="*60)
    print("\nI coordinate all AI Employee agents:")
    print("\nAvailable Handoffs:")
    print("  📧 GmailAgent - Email & attachments")
    print("  💬 WhatsAppAgent - Messages & task detection (EN/UR)")
    print("  💼 LinkedInAgent - Posts & engagement")
    print("\nTry these commands:")
    print("  - 'Check my emails' (→ Gmail)")
    print("  - 'Any WhatsApp tasks?' (→ WhatsApp)")
    print("  - 'Post on LinkedIn' (→ LinkedIn)")
    print("  - 'System status' (handled by Orchestrator)")
    print("\nType 'exit' to quit.\n")
    print("="*60)
    
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "exit":
                print("\n👋 Orchestrator Agent signing off. Goodbye!")
                break
            
            # Add user message to history
            history.append({"role": "user", "content": user_input})
            
            # Run agent with handoffs
            print("\n🤖 Agent: ", end="", flush=True)
            
            result = Runner.run_streamed(
                starting_agent=agent,
                input=history,
                run_config=config
            )
            
            # Stream response
            
            
            async for event in result.stream_events():
                if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                    print(event.data.delta, end="", flush=True)
            
            print("\n")
            
            # Update history with agent response
            history = result.to_input_list()
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Orchestrator Agent signing off.")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again.")


if __name__ == "__main__":
    print("Starting Orchestrator Agent with Handoffs...\n")
    asyncio.run(run_orchestrator())
