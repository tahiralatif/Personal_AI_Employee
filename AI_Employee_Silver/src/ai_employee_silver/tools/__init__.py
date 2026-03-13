"""
Tools module for AI Employee System.
"""

from .gmail_tools import (
    read_emails,
    get_email_details,
    save_attachment_to_inbox,
    create_email_action_file,
    mark_email_read
)

from .whatsapp_tools import (
    monitor_whatsapp_messages,
    send_whatsapp_message,
    detect_task_keywords,
    create_whatsapp_task_file,
    send_approval_request
)

from .linkedin_tools import (
    read_scheduled_posts,
    publish_linkedin_post,
    get_post_engagement,
    move_post_to_done
)

from .approval_tools import (
    request_approval,
    check_approval_status,
    approve_task,
    reject_task,
    list_pending_approvals
)

__all__ = [
    # Gmail
    "read_emails",
    "get_email_details",
    "save_attachment_to_inbox",
    "create_email_action_file",
    "mark_email_read",
    
    # WhatsApp
    "monitor_whatsapp_messages",
    "send_whatsapp_message",
    "detect_task_keywords",
    "create_whatsapp_task_file",
    "send_approval_request",
    
    # LinkedIn
    "read_scheduled_posts",
    "publish_linkedin_post",
    "get_post_engagement",
    "move_post_to_done",
    
    # Approval
    "request_approval",
    "check_approval_status",
    "approve_task",
    "reject_task",
    "list_pending_approvals"
]
