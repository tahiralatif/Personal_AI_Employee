"""
Gmail Tools for AI Employee System

Tools for Gmail Agent to interact with Gmail API.
"""

import os
import base64
from pathlib import Path
from datetime import datetime
from agents import function_tool
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


@function_tool()
def read_emails(query: str = "is:unread", limit: int = 10) -> str:
    """
    Read emails from Gmail.
    
    Args:
        query: Gmail search query (e.g., "is:unread", "has:attachment")
        limit: Maximum number of emails to fetch
    
    Returns:
        List of emails with subject, sender, and body
    """
    try:
        # Load credentials from token.json
        token_path = Path(__file__).parent.parent.parent.parent / "token.json"
        
        if not token_path.exists():
            return "Error: Gmail credentials not found. Please run OAuth flow first."
        
        creds = Credentials.from_authorized_user_file(str(token_path))
        service = build("gmail", "v1", credentials=creds)
        
        # Search emails
        results = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=limit
        ).execute()
        
        messages = results.get("messages", [])
        
        if not messages:
            return "No emails found."
        
        emails = []
        for msg in messages:
            message = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"]
            ).execute()
            
            headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}
            
            emails.append({
                "id": msg["id"],
                "subject": headers.get("Subject", "No Subject"),
                "from": headers.get("From", "Unknown"),
                "date": headers.get("Date", "Unknown")
            })
        
        return f"Found {len(emails)} emails:\n\n" + "\n\n".join([
            f"ID: {e['id']}\nSubject: {e['subject']}\nFrom: {e['from']}\nDate: {e['date']}"
            for e in emails
        ])
    
    except Exception as e:
        return f"Error reading emails: {str(e)}"


@function_tool()
def get_email_details(email_id: str) -> str:
    """
    Get full details of a specific email.
    
    Args:
        email_id: Gmail message ID
    
    Returns:
        Full email content including body and attachments
    """
    try:
        token_path = Path(__file__).parent.parent.parent.parent / "token.json"
        creds = Credentials.from_authorized_user_file(str(token_path))
        service = build("gmail", "v1", credentials=creds)
        
        message = service.users().messages().get(
            userId="me",
            id=email_id,
            format="full"
        ).execute()
        
        # Extract headers
        headers = {h["name"]: h["value"] for h in message["payload"]["headers"]}
        
        # Extract body
        body = ""
        if "parts" in message["payload"]:
            for part in message["payload"]["parts"]:
                if part["mimeType"] == "text/plain" and "data" in part["body"]:
                    body_data = part["body"]["data"]
                    body = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")
                    break
        elif "body" in message["payload"] and "data" in message["payload"]["body"]:
            body_data = message["payload"]["body"]["data"]
            body = base64.urlsafe_b64decode(body_data).decode("utf-8", errors="ignore")
        
        # Extract attachments info
        attachments = []
        if "parts" in message["payload"]:
            for part in message["payload"]["parts"]:
                if part.get("filename") and part["body"].get("attachmentId"):
                    attachments.append({
                        "filename": part["filename"],
                        "attachmentId": part["body"]["attachmentId"],
                        "size": part["body"].get("size", 0)
                    })
        
        result = f"""
From: {headers.get('From', 'Unknown')}
To: {headers.get('To', 'Unknown')}
Subject: {headers.get('Subject', 'No Subject')}
Date: {headers.get('Date', 'Unknown')}

--- Body ---
{body if body else '*No plain text body*'}

--- Attachments ---
{chr(10).join([f"- {a['filename']} ({a['size']} bytes)" for a in attachments]) if attachments else '*No attachments*'}
""".strip()
        
        return result
    
    except Exception as e:
        return f"Error getting email details: {str(e)}"


@function_tool()
def save_attachment_to_inbox(email_id: str, attachment_id: str) -> str:
    """
    Save email attachment to Inbox folder.
    
    Args:
        email_id: Gmail message ID
        attachment_id: Attachment ID from email
    
    Returns:
        Path to saved file
    """
    try:
        token_path = Path(__file__).parent.parent.parent.parent / "token.json"
        creds = Credentials.from_authorized_user_file(str(token_path))
        service = build("gmail", "v1", credentials=creds)
        
        # Get attachment
        attachment = service.users().messages().attachments().get(
            userId="me",
            messageId=email_id,
            id=attachment_id
        ).execute()
        
        # Get vault path
        vault_path = Path(os.getenv("VAULT_PATH")).expanduser()
        inbox_path = vault_path / "Inbox"
        inbox_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = attachment.get("filename", f"attachment_{attachment_id}")
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        file_path = inbox_path / f"GMAIL_{timestamp}_{safe_filename}"
        
        # Decode and save
        file_data = base64.urlsafe_b64decode(attachment["data"])
        
        with open(file_path, "wb") as f:
            f.write(file_data)
        
        return f"✓ Attachment saved to: {file_path}"
    
    except Exception as e:
        return f"✗ Error saving attachment: {str(e)}"


@function_tool()
def create_email_action_file(email_details: str, priority: str = "medium") -> str:
    """
    Create action file in Needs_Action folder for email.
    
    Args:
        email_details: Email content and metadata
        priority: Task priority (low, medium, high, urgent)
    
    Returns:
        Path to created action file
    """
    try:
        vault_path = Path(os.getenv("VAULT_PATH")).expanduser()
        needs_action_path = vault_path / "Needs_Action"
        needs_action_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = needs_action_path / f"EMAIL_{timestamp}.md"
        
        content = f"""---
type: gmail_email
received: {datetime.now().isoformat()}
priority: {priority}
status: pending_approval
---

# Email Task

## Email Details
{email_details}

## Required Actions
- [ ] Review email content
- [ ] Process attachments if any
- [ ] Create plan in /Plans/
- [ ] Execute plan
- [ ] Move to /Done/ when complete

## Approval Required
⚠️ **This task requires human approval before proceeding.**

Reply with: APPROVE or REJECT

---
*Automatically generated by AI Employee - Gmail Agent*
"""
        
        file_path.write_text(content, encoding="utf-8")
        
        return f"✓ Action file created: {file_path}"
    
    except Exception as e:
        return f"✗ Error creating action file: {str(e)}"


@function_tool()
def mark_email_read(email_id: str) -> str:
    """
    Mark email as read in Gmail.
    
    Args:
        email_id: Gmail message ID
    
    Returns:
        Success or error message
    """
    try:
        token_path = Path(__file__).parent.parent.parent.parent / "token.json"
        creds = Credentials.from_authorized_user_file(str(token_path))
        service = build("gmail", "v1", credentials=creds)
        
        service.users().messages().modify(
            userId="me",
            id=email_id,
            body={"removeLabelIds": ["UNREAD"]}
        ).execute()
        
        return f"✓ Email marked as read: {email_id}"
    
    except Exception as e:
        return f"✗ Error marking email as read: {str(e)}"
