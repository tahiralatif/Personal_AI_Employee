# Silver Tier Data Model

## Overview
This document defines the data models used in the Silver Tier of the AI Employee system. It includes enhanced data structures for new watchers, MCP servers, and improved approval workflows.

## Enhanced File Structures

### 1. Gmail Action File Structure
Location: `Needs_Action/Gmail/`

```yaml
---
type: email
from: "sender@example.com"
to: "recipient@example.com"
subject: "Email subject"
received: "2026-03-08T10:30:00Z"
priority: "high"          # high, medium, low
status: "pending"         # pending, in-progress, completed, failed
gmail_id: "unique_gmail_message_id"
thread_id: "thread_identifier"
labels: ["inbox", "important"]
snippet: "Brief preview of email content"
---

# Email Content
[Full email content or summary]

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Archive after processing
- [ ] Flag for follow-up
```

### 2. WhatsApp Action File Structure
Location: `Needs_Action/WhatsApp/`

```yaml
---
type: whatsapp
from: "contact_name_or_number"
received: "2026-03-08T10:30:00Z"
priority: "high"          # high, medium, low
status: "pending"         # pending, in-progress, completed, failed
chat_id: "unique_chat_identifier"
message_id: "unique_message_id"
language: "en"            # en, ur, etc.
keywords_detected: ["urgent", "payment"]
---

## Message Content
[Full message content]

## Contact Info
- **Name**: [Contact name if available]
- **Type**: [personal/business]
- **Relationship**: [client/friend/family/vendor]

## Suggested Actions
- [ ] Reply to sender
- [ ] Create task from message
- [ ] Flag for follow-up
- [ ] Schedule callback
```

### 3. LinkedIn Action File Structure
Location: `Needs_Action/LinkedIn/`

```yaml
---
type: linkedin
from: "contact_name"
received: "2026-03-08T10:30:00Z"
priority: "medium"        # high, medium, low
status: "pending"         # pending, in-progress, completed, failed
post_id: "linkedin_post_id"
activity_type: "connection_request"  # connection_request, message, post_mention
relationship: "potential_client"
business_opportunity: false
---

## Activity Details
[Details of the LinkedIn activity]

## Contact Info
- **Name**: [Contact name]
- **Position**: [Job title]
- **Company**: [Company name]
- **Industry**: [Industry sector]

## Suggested Actions
- [ ] Accept connection request
- [ ] Send welcome message
- [ ] Evaluate business opportunity
- [ ] Schedule follow-up
```

### 4. Enhanced Plan File Structure
Location: `Plans/`

```yaml
---
type: action_plan
task_id: "unique_plan_identifier"
created: "2026-03-08T10:30:00Z"
updated: "2026-03-08T10:45:00Z"
status: "pending"         # pending, in-progress, completed, failed, cancelled
estimated_duration: 45    # minutes
priority: "high"          # high, medium, low
author: "ai_employee"
tags: ["business", "finance", "urgent"]
dependencies: ["task_id_1", "task_id_2"]
parent_task: "parent_task_id"
---

# Action Plan: [Task Description]

## Objective
[Clear objective statement]

## Prerequisites
- [ ] Item 1
- [ ] Item 2
- [ ] Item 3

## Steps
1. [Step 1 with details and estimated time]
2. [Step 2 with details and estimated time]
3. [Step 3 with details and estimated time]

## Resources Needed
- [Resource 1]
- [Resource 2]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Approval Required
- [ ] Human approval needed for sensitive actions
- [ ] Budget approval for payments over threshold
- [ ] Specific approval items

## Rollback Plan
[Steps to undo actions if needed]

## Notes
[Any additional notes or considerations]
```

### 5. Enhanced Approval Request Structure
Location: `Pending_Approval/`

```yaml
---
type: approval_request
action: "payment"         # payment, email, social_post, data_access, system_change
action_id: "unique_action_identifier"
created: "2026-03-08T10:30:00Z"
expires: "2026-03-09T10:30:00Z"
status: "pending"         # pending, approved, rejected
requestor: "ai_employee"
urgency: "high"           # high, medium, low
category: "financial"     # financial, communication, data, system
risk_level: "medium"      # low, medium, high
estimated_cost: 500.00    # if financial action
currency: "USD"           # currency code
approver: ""              # who approved/rejected
rejection_reason: ""      # if rejected
related_tasks: ["task_id_1", "task_id_2"]
---

# Approval Request

## Action Details
- **Type**: [action type]
- **Target**: [destination/target]
- **Amount**: [if financial]
- **Content Preview**: [first 200 characters]

## Business Justification
[Detailed reason for requesting approval]

## Risk Assessment
- **Financial Risk**: [low/medium/high]
- **Reputation Risk**: [low/medium/high]
- **Security Risk**: [low/medium/high]
- **Compliance Risk**: [low/medium/high]

## Alternative Options
1. [Option 1 with pros and cons]
2. [Option 2 with pros and cons]

## Approval Options
1. **Approve**: Move file to `/Approved/` folder
2. **Reject**: Move file to `/Rejected/` folder with reason
3. **Modify**: Edit this file and move to `/Pending_Approval/` again

## Auto-Reject
This request will auto-reject on [expiration_time] if no action taken.

## Related Information
[Any additional context or information]
```

## MCP Server Data Models

### 6. Email MCP Tool Parameters
```json
{
  "name": "send_email",
  "arguments": {
    "to": "recipient@example.com",
    "subject": "Email subject",
    "body": "Email body content",
    "cc": ["cc@example.com"],
    "bcc": ["bcc@example.com"],
    "attachment_paths": ["/path/to/attachment.pdf"],
    "is_html": false
  }
}
```

### 7. Browser MCP Tool Parameters
```json
{
  "name": "click_element",
  "arguments": {
    "url": "https://example.com",
    "selector": "button.submit-btn",
    "timeout": 10000
  }
}
```

### 8. LinkedIn MCP Tool Parameters
```json
{
  "name": "post_update",
  "arguments": {
    "content": "Post content here",
    "visibility": "PUBLIC",  // PUBLIC, CONNECTIONS, PRIVATE
    "hashtags": ["hashtag1", "hashtag2"],
    "image_urls": ["https://example.com/image.jpg"]
  }
}
```

## Enhanced Dashboard Data Model

### 9. Dashboard Statistics
```json
{
  "last_updated": "2026-03-08T10:30:00Z",
  "system_status": "active",  // active, idle, maintenance, error
  "task_summary": {
    "pending": 5,
    "in_progress": 2,
    "awaiting_approval": 3,
    "approved": 1,
    "completed_today": 12,
    "rejected": 0
  },
  "processing_results": {
    "last_run": "2026-03-08T10:25:00Z",
    "total_processed": 8,
    "successful": 7,
    "approval_required": 3,
    "autonomous": 4,
    "failed": 0
  },
  "recent_activity": [
    {
      "timestamp": "2026-03-08T10:28:00Z",
      "action": "Processed email from client",
      "result": "success"
    },
    {
      "timestamp": "2026-03-08T10:25:00Z",
      "action": "Created approval request for payment",
      "result": "pending"
    }
  ],
  "performance_metrics": {
    "avg_response_time": 15.2,
    "task_completion_rate": 98.5,
    "uptime_percentage": 99.9
  }
}
```

## Scheduling Data Model

### 10. Scheduled Task Structure
```yaml
---
type: scheduled_task
task_id: "unique_task_identifier"
created: "2026-03-08T10:30:00Z"
schedule_expression: "0 9 * * *"  # cron format
next_run: "2026-03-09T09:00:00Z"
last_run: "2026-03-08T09:00:00Z"
status: "active"          # active, paused, cancelled, completed
task_type: "daily_summary" # daily_summary, weekly_post, monthly_report, etc.
enabled: true
max_runtime: 300          # seconds
retry_attempts: 3
timeout: 60               # seconds
---

# Scheduled Task: [Task Description]

## Purpose
[Brief description of what the task does]

## Execution Details
- **Schedule**: [Human-readable schedule]
- **Next Run**: [Next execution time]
- **Last Run**: [Previous execution time]
- **Status**: [Current status]

## Parameters
[Any parameters needed for task execution]

## Success Criteria
[How to determine if task executed successfully]

## Failure Handling
[What happens if task fails]
```

## Security and Audit Data Model

### 11. Audit Log Entry
```json
{
  "timestamp": "2026-03-08T10:30:00Z",
  "action_type": "email_send",
  "actor": "ai_employee",
  "target": "recipient@example.com",
  "parameters": {
    "subject": "Invoice #123"
  },
  "approval_status": "approved",  // approved, auto, pending, rejected
  "approved_by": "human_user",
  "result": "success",  // success, failed, partial
  "error_message": "",
  "execution_time": 1250,  // milliseconds
  "session_id": "session_identifier",
  "ip_address": "192.168.1.100",
  "user_agent": "AI Employee v1.0"
}
```

## Configuration Data Model

### 12. System Configuration
```yaml
# config/settings.py equivalent
VAULT_PATH: "~/AI_Employee_Vault"
LOG_LEVEL: "INFO"
MAX_FILE_SIZE: 104857600  # 100MB
WATCHED_FOLDER: "~/AI_Employee_Vault/Inbox"
CHECK_INTERVAL: 10  # seconds
GMAIL_CHECK_INTERVAL: 120  # seconds
WHATSAPP_CHECK_INTERVAL: 30  # seconds
LINKEDIN_CHECK_INTERVAL: 300  # seconds
ENABLE_GMAIL_WATCHER: true
ENABLE_WHATSAPP_WATCHER: true
ENABLE_LINKEDIN_WATCHER: true
ENABLE_FILE_WATCHER: true
APPROVAL_THRESHOLDS:
  PAYMENT_HIGH: 1000  # PKR
  PAYMENT_MEDIUM: 500  # PKR
DEFAULT_APPROVAL_EXPIRY_HOURS: 24
QWEN_MODEL_PATH: "http://localhost:1234"
QWEN_TEMPERATURE: 0.7
QWEN_MAX_TOKENS: 4096
```

## File Naming Conventions

### 13. Generated File Names
- **Gmail Action Files**: `GMAIL_yyyymmdd_hhmmss_uniqueid.md`
- **WhatsApp Action Files**: `WHATSAPP_yyyymmdd_hhmmss_uniqueid.md`
- **LinkedIn Action Files**: `LINKEDIN_yyyymmdd_hhmmss_uniqueid.md`
- **Plan Files**: `PLAN_yyyymmdd_hhmmss_description.md`
- **Approval Requests**: `APPROVAL_yyyymmdd_hhmmss_actiontype.md`
- **Scheduled Tasks**: `SCHEDULED_taskdescription.md`
- **Log Files**: `yyyymmdd.log`

These data models provide the structure for all the enhanced functionality in the Silver tier while maintaining compatibility with the Bronze tier foundations.