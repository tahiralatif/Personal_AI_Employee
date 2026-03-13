"""
WhatsApp Tools for AI Employee System

Tools for WhatsApp Agent to interact with WhatsApp via Twilio.
"""

import os
from datetime import datetime
from pathlib import Path
from agents import function_tool
from twilio.rest import Client


@function_tool()
def monitor_whatsapp_messages(limit: int = 10) -> str:
    """
    Monitor WhatsApp messages from Twilio.
    
    Args:
        limit: Maximum number of messages to fetch
    
    Returns:
        List of recent WhatsApp messages
    """
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        
        if not all([account_sid, auth_token, whatsapp_number]):
            return "Error: Twilio credentials not configured in .env"
        
        client = Client(account_sid, auth_token)
        
        # Fetch messages sent TO the WhatsApp number (incoming messages)
        messages = client.messages.list(
            to=f"whatsapp:{whatsapp_number}",
            limit=limit
        )
        
        if not messages:
            return "No new WhatsApp messages."
        
        msg_list = []
        for msg in messages:
            msg_list.append({
                "sid": msg.sid,
                "from": msg.from_.replace("whatsapp:", ""),
                "body": msg.body,
                "date": str(msg.date_sent),
                "status": msg.status
            })
        
        result = f"Found {len(msg_list)} WhatsApp messages:\n\n"
        for m in msg_list:
            result += f"""
---
From: {m['from']}
Date: {m['date']}
Message: {m['body']}
---
"""
        
        return result
    
    except Exception as e:
        return f"Error monitoring WhatsApp: {str(e)}"


@function_tool()
def send_whatsapp_message(to_number: str, message: str) -> str:
    """
    Send WhatsApp message via Twilio.
    
    Args:
        to_number: Recipient's phone number (with country code, e.g., +923151082542)
        message: Message text to send
    
    Returns:
        Message SID if sent successfully
    """
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        
        if not all([account_sid, auth_token, whatsapp_number]):
            return "Error: Twilio credentials not configured"
        
        client = Client(account_sid, auth_token)
        
        message_obj = client.messages.create(
            from_=f"whatsapp:{whatsapp_number}",
            body=message,
            to=f"whatsapp:{to_number}"
        )
        
        return f"✓ Message sent successfully! SID: {message_obj.sid}"
    
    except Exception as e:
        return f"✗ Error sending WhatsApp message: {str(e)}"


@function_tool()
def detect_task_keywords(message: str) -> str:
    """
    Detect if message contains task keywords.
    Supports both English and Urdu keywords.
    
    Args:
        message: WhatsApp message text
    
    Returns:
        Analysis result with detected keywords
    """
    # English keywords
    en_keywords = [
        "please", "need", "urgent", "task", "action",
        "required", "must", "should", "remind", "todo",
        "do this", "complete", "finish", "send", "prepare"
    ]
    
    # Urdu keywords (transliterated)
    ur_keywords = [
        "meharbani", "baraaye", "zaroori", "kaam", "action",
        "chahiye", "bhejo", "taiyar", "complete"
    ]
    
    message_lower = message.lower()
    
    # Detect English keywords
    detected_en = [k for k in en_keywords if k in message_lower]
    
    # Detect Urdu keywords
    detected_ur = [k for k in ur_keywords if k in message_lower]
    
    result = []
    
    if detected_en:
        result.append(f"English keywords detected: {', '.join(detected_en)}")
    
    if detected_ur:
        result.append(f"Urdu keywords detected: {', '.join(detected_ur)}")
    
    if detected_en or detected_ur:
        result.append("\n✓ TASK DETECTED - Action required!")
        return "\n".join(result)
    else:
        return "No task keywords detected. This appears to be a regular message."


@function_tool()
def create_whatsapp_task_file(message_data: str, from_number: str) -> str:
    """
    Create task file in Needs_Action folder for WhatsApp message.
    
    Args:
        message_data: WhatsApp message content
        from_number: Sender's phone number
    
    Returns:
        Path to created task file
    """
    try:
        vault_path = Path(os.getenv("VAULT_PATH")).expanduser()
        needs_action_path = vault_path / "Needs_Action"
        needs_action_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_number = "".join(c for c in from_number if c.isdigit())[-4:]
        file_path = needs_action_path / f"WHATSAPP_{timestamp}_{safe_number}.md"
        
        content = f"""---
type: whatsapp_message
from_number: {from_number}
received: {datetime.now().isoformat()}
priority: medium
status: pending_approval
---

# WhatsApp Task

## Message Details
- **From:** {from_number}
- **Received:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Message Content
{message_data}

## Required Actions
- [ ] Review message content
- [ ] Determine required action
- [ ] Create plan in /Plans/
- [ ] Execute plan
- [ ] Move to /Done/ when complete

## Approval Required
⚠️ **This task requires human approval before proceeding.**

Reply with: APPROVE or REJECT

---
*Automatically generated by AI Employee - WhatsApp Agent*
"""
        
        file_path.write_text(content, encoding="utf-8")
        
        return f"✓ Task file created: {file_path}"
    
    except Exception as e:
        return f"✗ Error creating task file: {str(e)}"


@function_tool()
def send_approval_request(to_number: str, task_description: str) -> str:
    """
    Send approval request notification via WhatsApp.
    
    Args:
        to_number: Recipient's phone number
        task_description: Description of task requiring approval
    
    Returns:
        Success or error message
    """
    try:
        message = f"""
⚠️ *Approval Required*

📋 Task:
{task_description[:500]}

Reply with:
✅ APPROVE - to proceed
❌ REJECT - to discard

---
AI Employee System
""".strip()
        
        return send_whatsapp_message(to_number, message)
    
    except Exception as e:
        return f"✗ Error sending approval request: {str(e)}"
