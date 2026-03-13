"""
Approval Tools for AI Employee System

Tools for human-in-the-loop approval workflow.
"""

import os
from datetime import datetime
from pathlib import Path
from agents import function_tool


@function_tool()
def request_approval(task_description: str, priority: str = "medium") -> str:
    """
    Request human approval for a task.
    
    Args:
        task_description: Description of task requiring approval
        priority: Task priority (low, medium, high, urgent)
    
    Returns:
        Approval request status
    """
    try:
        vault_path = Path(os.getenv("VAULT_PATH")).expanduser()
        pending_path = vault_path / "Pending_Approval"
        pending_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = pending_path / f"APPROVAL_{timestamp}.md"
        
        content = f"""---
type: approval_request
requested: {datetime.now().isoformat()}
priority: {priority}
status: pending
---

# Approval Required

## Task Description
{task_description}

## Requested At
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Response Required
Reply with one of:
- ✅ APPROVE - to proceed with this task
- ❌ REJECT - to discard this task
- ⏸️ LATER - to postpone for later

## Timeout
This request will expire in 24 hours if no response is received.

---
*AI Employee System - Approval Manager*
"""
        
        file_path.write_text(content, encoding="utf-8")
        
        # Send WhatsApp notification
        your_number = os.getenv("YOUR_PHONE_NUMBER")
        if your_number:
            from .whatsapp_tools import send_whatsapp_message
            notification = f"""
⚠️ *Approval Required*

📋 Task:
{task_description[:300]}

⏰ Priority: {priority}

Reply: APPROVE or REJECT
""".strip()
            send_whatsapp_message(your_number, notification)
        
        return f"✓ Approval requested! File: {file_path}\n\nNotification sent to: {your_number}"
    
    except Exception as e:
        return f"✗ Error requesting approval: {str(e)}"


@function_tool()
def check_approval_status(task_id: str) -> str:
    """
    Check if approval has been granted for a task.
    
    Args:
        task_id: Task identifier or file name
    
    Returns:
        Approval status (pending/approved/rejected/expired)
    """
    try:
        vault_path = Path(os.getenv("VAULT_PATH")).expanduser()
        pending_path = vault_path / "Pending_Approval"
        
        # Look for response file
        response_patterns = [
            pending_path / f"{task_id}_response.txt",
            pending_path / f"response_{task_id}.txt",
            pending_path / f"{task_id}.response"
        ]
        
        for response_file in response_patterns:
            if response_file.exists():
                response = response_file.read_text().strip()
                response_file.unlink()  # Delete after reading
                return f"Approval status: {response}"
        
        # Check if file still exists in pending
        pending_file = pending_path / task_id
        if pending_file.exists():
            # Check if expired (older than 24 hours)
            age = datetime.now() - datetime.fromtimestamp(pending_file.stat().st_mtime)
            if age.total_seconds() > 86400:  # 24 hours
                return "Approval status: EXPIRED (no response within 24 hours)"
            return "Approval status: PENDING (waiting for response)"
        
        return f"Approval status: NOT FOUND (task_id: {task_id})"
    
    except Exception as e:
        return f"✗ Error checking approval status: {str(e)}"


@function_tool()
def approve_task(task_id: str) -> str:
    """
    Mark a task as approved.
    
    Args:
        task_id: Task identifier
    
    Returns:
        Success or error message
    """
    try:
        vault_path = Path(os.getenv("VAULT_PATH")).expanduser()
        pending_path = vault_path / "Pending_Approval"
        approved_path = vault_path / "Approved"
        
        approved_path.mkdir(parents=True, exist_ok=True)
        
        # Find and move file
        for file in pending_path.glob(f"*{task_id}*"):
            # Add approval metadata
            content = file.read_text(encoding="utf-8")
            content += f"\n\n---\nApproved: {datetime.now().isoformat()}\nStatus: Approved\n"
            
            # Move to Approved
            dst_path = approved_path / file.name
            dst_path.write_text(content, encoding="utf-8")
            file.unlink()
            
            return f"✓ Task approved and moved to Approved: {file.name}"
        
        return f"Task not found in Pending_Approval: {task_id}"
    
    except Exception as e:
        return f"✗ Error approving task: {str(e)}"


@function_tool()
def reject_task(task_id: str, reason: str = "No reason provided") -> str:
    """
    Mark a task as rejected.
    
    Args:
        task_id: Task identifier
        reason: Reason for rejection
    
    Returns:
        Success or error message
    """
    try:
        vault_path = Path(os.getenv("VAULT_PATH")).expanduser()
        pending_path = vault_path / "Pending_Approval"
        rejected_path = vault_path / "Rejected"
        
        rejected_path.mkdir(parents=True, exist_ok=True)
        
        # Find and move file
        for file in pending_path.glob(f"*{task_id}*"):
            # Add rejection metadata
            content = file.read_text(encoding="utf-8")
            content += f"\n\n---\nRejected: {datetime.now().isoformat()}\nStatus: Rejected\nReason: {reason}\n"
            
            # Move to Rejected
            dst_path = rejected_path / file.name
            dst_path.write_text(content, encoding="utf-8")
            file.unlink()
            
            return f"✓ Task rejected and moved to Rejected: {file.name}\n\nReason: {reason}"
        
        return f"Task not found in Pending_Approval: {task_id}"
    
    except Exception as e:
        return f"✗ Error rejecting task: {str(e)}"


@function_tool()
def list_pending_approvals() -> str:
    """
    List all pending approval requests.
    
    Returns:
        List of pending approvals
    """
    try:
        vault_path = Path(os.getenv("VAULT_PATH")).expanduser()
        pending_path = vault_path / "Pending_Approval"
        
        if not pending_path.exists():
            return "No pending approvals."
        
        pending_files = list(pending_path.glob("*.md"))
        
        if not pending_files:
            return "No pending approvals."
        
        result = f"Found {len(pending_files)} pending approval(s):\n\n"
        
        for file in pending_files:
            age = datetime.now() - datetime.fromtimestamp(file.stat().st_mtime)
            age_hours = age.total_seconds() / 3600
            
            # Read first few lines for description
            content = file.read_text(encoding="utf-8")
            description = content.split("\n")[3:5]
            description = " ".join(description)[:100]
            
            result += f"""
---
File: {file.name}
Age: {age_hours:.1f} hours
Description: {description}...
---
"""
        
        result += "\n\nUse check_approval_status(task_id) to check status of specific task."
        
        return result
    
    except Exception as e:
        return f"✗ Error listing pending approvals: {str(e)}"
