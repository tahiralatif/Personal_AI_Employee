# Silver Tier Data Model

## Overview

This document defines the data entities, their attributes, and relationships for the Silver Tier AI Employee system. Silver Tier extends Bronze Tier's data model with additional entities for external API integrations.

---

## Core Entities

### 1. EmailMessage

Represents an email fetched from Gmail with attachments.

```python
class EmailMessage:
    id: str                    # Unique email ID (Gmail message ID)
    thread_id: str             # Gmail thread ID
    subject: str               # Email subject line
    sender: str                # Sender email address
    sender_name: str           # Sender display name
    recipients: list[str]      # List of recipient email addresses
    received_at: datetime      # Email received timestamp (UTC)
    body_text: str             # Plain text body
    body_html: str             # HTML body (optional)
    attachments: list[Attachment]  # List of attachments
    labels: list[str]          # Gmail labels (e.g., INBOX, IMPORTANT)
    is_read: bool              # Read/unread status
    processed_at: datetime     # When system processed this email
    status: str                # pending, processed, failed, skipped
    error_message: str         # Error details if failed
```

**Storage**: Metadata stored in `.silver/data/emails/`, attachments saved to `Inbox/`

**Indexes**: `received_at`, `sender`, `status`

---

### 2. Attachment

Represents a file attachment from an email.

```python
class Attachment:
    id: str                    # Unique attachment ID
    email_id: str              # Parent email ID (foreign key)
    filename: str              # Original filename
    saved_filename: str        # Saved filename in Inbox/
    mime_type: str             # MIME type (e.g., application/pdf)
    size_bytes: int            # File size in bytes
    content_id: str            # Content-ID for inline attachments
    saved_path: str            # Absolute path in Inbox/
    saved_at: datetime         # When saved to Inbox/
    checksum: str              # SHA256 hash for integrity
```

**Storage**: Files saved to `Inbox/`, metadata in `.silver/data/attachments/`

**Relationships**: Many-to-One with EmailMessage

---

### 3. WhatsAppMessage

Represents a WhatsApp message (text or media).

```python
class WhatsAppMessage:
    id: str                    # Unique message ID (WhatsApp message ID)
    contact_phone: str         # Sender's phone number
    contact_name: str          # Contact name (if available)
    message_type: str          # text, image, document, audio, video
    content: str               # Text content (for text messages)
    media_url: str             # URL to download media (if media message)
    media_filename: str        # Filename for media attachment
    media_saved_path: str      # Local path in Inbox/ (if saved)
    received_at: datetime      # Message received timestamp (UTC)
    is_from_group: bool        # True if from WhatsApp group
    group_id: str              # WhatsApp group ID (if applicable)
    group_name: str            # Group name (if applicable)
    is_task: bool              # Whether identified as a task
    task_keywords: list[str]   # Matched keywords (please, need, urgent, etc.)
    processed_at: datetime     # When system processed this message
    status: str                # pending, processed, failed, skipped
    error_message: str         # Error details if failed
```

**Storage**: Metadata in `.silver/data/whatsapp/`, media saved to `Inbox/`

**Indexes**: `received_at`, `contact_phone`, `is_task`

---

### 4. LinkedInPost

Represents a scheduled LinkedIn post.

```python
class LinkedInPost:
    id: str                    # Unique post ID (generated)
    content: str               # Post content (text)
    media_paths: list[str]     # Paths to media files (images, documents)
    post_type: str             # text, image, article, video
    scheduled_at: datetime     # Scheduled publish time (UTC)
    published_at: datetime     # Actual publish time (if published)
    post_url: str              # LinkedIn post URL (after publishing)
    post_id: str               # LinkedIn post ID (after publishing)
    status: str                # draft, pending_approval, approved, scheduled, published, failed
    engagement_metrics: dict   # {likes: int, comments: int, shares: int}
    metrics_fetched_at: datetime  # When metrics were last fetched
    error_message: str         # Error details if failed
    approval_requested_at: datetime  # When approval was requested
    approved_at: datetime      # When human approved
    approved_by: str           # Who approved (username)
```

**Storage**: Metadata in `.silver/data/linkedin/`, media in `Plans/`

**Indexes**: `scheduled_at`, `status`

---

### 5. ScheduledTask

Represents a recurring task with cron schedule.

```python
class ScheduledTask:
    id: str                    # Unique task ID (generated)
    name: str                  # Task name/description
    cron_expression: str       # Cron expression (e.g., "0 9 * * 1")
    timezone: str              # Timezone for scheduling (e.g., "Asia/Karachi")
    task_template: str         # Template for generated task file
    target_folder: str         # Where to create task file (Needs_Action/)
    is_active: bool            # Whether schedule is active
    start_date: datetime       # First occurrence date
    end_date: datetime         # Last occurrence date (optional)
    last_run_at: datetime      # Last time task was created
    next_run_at: datetime      # Next scheduled run time
    run_count: int             # Total times task has been created
    created_tasks: list[str]   # List of created task file paths
    holiday_policy: str        # skip, reschedule_next_day, reschedule_next_weekday
    created_at: datetime       # When schedule was created
    updated_at: datetime       # When schedule was last updated
```

**Storage**: `.silver/data/schedules/`

**Indexes**: `next_run_at`, `is_active`, `timezone`

---

### 6. MCPServer

Represents an MCP server connection and status.

```python
class MCPServer:
    id: str                    # Unique server ID (generated)
    name: str                  # Server display name
    server_type: str           # gmail, whatsapp, linkedin, custom
    endpoint_url: str          # MCP server endpoint
    status: str                # online, offline, busy, error
    last_heartbeat: datetime   # Last heartbeat timestamp
    capabilities: list[str]    # List of supported capabilities
    active_tasks: list[str]    # Currently processing task IDs
    completed_tasks: int       # Total tasks completed
    failed_tasks: int          # Total tasks failed
    connected_at: datetime     # When server connected
    disconnected_at: datetime  # When server disconnected (if applicable)
    error_message: str         # Error details if in error state
    config: dict               # Server-specific configuration
```

**Storage**: `.silver/data/mcp/`

**Indexes**: `status`, `server_type`, `last_heartbeat`

---

### 7. APICredential

Represents API credentials for external services.

```python
class APICredential:
    id: str                    # Unique credential ID (generated)
    service_name: str          # gmail, whatsapp, linkedin
    credential_type: str       # oauth2, api_key, bearer_token
    client_id: str             # OAuth client ID (encrypted)
    client_secret: str         # OAuth client secret (encrypted)
    access_token: str          # Current access token (encrypted)
    refresh_token: str         # Refresh token (encrypted)
    token_expires_at: datetime # When access token expires
    scopes: list[str]          # OAuth scopes granted
    is_valid: bool             # Whether credentials are valid
    last_validated_at: datetime # When validity was last checked
    created_at: datetime       # When credentials were added
    updated_at: datetime       # When credentials were last updated
```

**Storage**: Encrypted in `.env` (never in vault or database)

**Security**: All sensitive fields encrypted at rest

---

### 8. TaskQueue

Represents a queued task waiting for API availability.

```python
class TaskQueue:
    id: str                    # Unique queue item ID (generated)
    task_type: str             # email_fetch, whatsapp_fetch, linkedin_post, etc.
    payload: dict              # Task-specific data
    priority: int              # Priority level (1=highest, 5=lowest)
    status: str                # queued, processing, completed, failed, retrying
    created_at: datetime       # When added to queue
    scheduled_for: datetime    # When to process (for delayed tasks)
    processed_at: datetime     # When processing started
    completed_at: datetime     # When processing completed
    retry_count: int           # Number of retry attempts
    max_retries: int           # Maximum retry attempts (default: 3)
    error_message: str         # Error details if failed
    next_retry_at: datetime    # When to retry (if retrying)
```

**Storage**: `.silver/data/queue/`

**Indexes**: `status`, `priority`, `scheduled_for`

---

### 9. APIRateLimit

Tracks API rate limits and quotas.

```python
class APIRateLimit:
    id: str                    # Unique ID (generated)
    service_name: str          # gmail, whatsapp, linkedin
    limit_type: str            # requests_per_second, requests_per_day, quota_units
    limit_value: int           # Maximum allowed value
    current_value: int         # Current usage count
    reset_at: datetime         # When limit resets
    is_exceeded: bool          # Whether limit is exceeded
    queued_count: int          # Number of tasks waiting for limit reset
    last_checked_at: datetime  # When limit was last checked
```

**Storage**: `.silver/data/rate_limits/`

**Indexes**: `service_name`, `is_exceeded`

---

### 10. ActivityLog

Represents a logged activity (extends Bronze Tier logging).

```python
class ActivityLog:
    id: str                    # Unique log ID (generated)
    timestamp: datetime        # When activity occurred
    service_name: str          # gmail, whatsapp, linkedin, scheduler, mcp
    activity_type: str         # email_fetched, message_processed, post_published, etc.
    entity_type: str           # EmailMessage, WhatsAppMessage, LinkedInPost, etc.
    entity_id: str             # ID of the related entity
    action: str                # create, read, update, delete
    status: str                # success, failure, warning, skipped
    details: dict              # Additional context (JSON)
    error_message: str         # Error details if failed
    duration_ms: int           # How long the operation took (milliseconds)
    user: str                  # System or username (for audit)
```

**Storage**: `Logs/YYYY-MM-DD.log` (Bronze Tier) + `.silver/data/logs/` (detailed)

**Indexes**: `timestamp`, `service_name`, `activity_type`, `status`

---

## Entity Relationships

```
┌─────────────────┐
│  EmailMessage   │
│                 │
│  - attachments ─┼───────< Attachment
│                 │
└─────────────────┘

┌─────────────────┐
│ WhatsAppMessage │
│                 │
│  - media        │ (saved to Inbox/)
│                 │
└─────────────────┘

┌─────────────────┐
│  LinkedInPost   │
│                 │
│  - media_paths  │ (stored in Plans/)
│                 │
└─────────────────┘

┌─────────────────┐
│  ScheduledTask  │
│                 │
│  - created_tasks│ (references task files in Needs_Action/)
│                 │
└─────────────────┘

┌─────────────────┐
│   MCPServer     │
│                 │
│  - active_tasks │ (references tasks being processed)
│                 │
└─────────────────┘

┌─────────────────┐
│  TaskQueue      │
│                 │
│  - payload      │ (references entity to process)
│                 │
└─────────────────┘

┌─────────────────┐
│  APIRateLimit   │
│                 │
│  - service_name │ (references APICredential.service_name)
│                 │
└─────────────────┘

┌─────────────────┐
│  ActivityLog    │
│                 │
│  - entity_id    │ (polymorphic: references any entity)
│  - service_name │ (references service that performed action)
│                 │
└─────────────────┘
```

---

## Data Flow Diagrams

### Email Processing Flow

```
Gmail API
    ↓
[EmailMessage] ← fetched
    ↓
[Attachment] ← extracted
    ↓
Inbox/ ← saved
    ↓
Bronze Tier detects
    ↓
Needs_Action/ ← action file created
```

### WhatsApp Processing Flow

```
WhatsApp Business API
    ↓
[WhatsAppMessage] ← received
    ↓
Task keyword detection
    ↓
[is_task = true]
    ↓
Needs_Action/ ← task file created
```

### LinkedIn Posting Flow

```
Plans/ ← post created
    ↓
[LinkedInPost] ← scheduled
    ↓
Pending_Approval/ ← human approval
    ↓
LinkedIn API ← published
    ↓
Done/ ← moved with post URL
```

### Scheduled Task Flow

```
[ScheduledTask] ← configured
    ↓
Cron scheduler
    ↓
Scheduled time arrives
    ↓
Needs_Action/ ← task file created
    ↓
[ScheduledTask].run_count++
```

---

## Database Schema (Optional - If Using SQLite)

```sql
-- Email Messages
CREATE TABLE email_messages (
    id TEXT PRIMARY KEY,
    thread_id TEXT,
    subject TEXT,
    sender TEXT,
    sender_name TEXT,
    received_at TIMESTAMP,
    body_text TEXT,
    is_read BOOLEAN,
    processed_at TIMESTAMP,
    status TEXT,
    error_message TEXT
);

-- Attachments
CREATE TABLE attachments (
    id TEXT PRIMARY KEY,
    email_id TEXT,
    filename TEXT,
    saved_filename TEXT,
    mime_type TEXT,
    size_bytes INTEGER,
    saved_path TEXT,
    saved_at TIMESTAMP,
    checksum TEXT,
    FOREIGN KEY (email_id) REFERENCES email_messages(id)
);

-- WhatsApp Messages
CREATE TABLE whatsapp_messages (
    id TEXT PRIMARY KEY,
    contact_phone TEXT,
    contact_name TEXT,
    message_type TEXT,
    content TEXT,
    media_url TEXT,
    media_saved_path TEXT,
    received_at TIMESTAMP,
    is_task BOOLEAN,
    processed_at TIMESTAMP,
    status TEXT,
    error_message TEXT
);

-- LinkedIn Posts
CREATE TABLE linkedin_posts (
    id TEXT PRIMARY KEY,
    content TEXT,
    post_type TEXT,
    scheduled_at TIMESTAMP,
    published_at TIMESTAMP,
    post_url TEXT,
    status TEXT,
    engagement_metrics TEXT,
    error_message TEXT
);

-- Scheduled Tasks
CREATE TABLE scheduled_tasks (
    id TEXT PRIMARY KEY,
    name TEXT,
    cron_expression TEXT,
    timezone TEXT,
    task_template TEXT,
    is_active BOOLEAN,
    next_run_at TIMESTAMP,
    run_count INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Activity Logs
CREATE TABLE activity_logs (
    id TEXT PRIMARY KEY,
    timestamp TIMESTAMP,
    service_name TEXT,
    activity_type TEXT,
    entity_type TEXT,
    entity_id TEXT,
    action TEXT,
    status TEXT,
    details TEXT,
    error_message TEXT,
    duration_ms INTEGER
);
```

---

## Data Retention Policy

| Entity | Retention Period | Archive Strategy |
|--------|------------------|------------------|
| EmailMessage | 90 days | Delete after 90 days |
| Attachment | 90 days | Delete with parent email |
| WhatsAppMessage | 30 days | Delete after 30 days |
| LinkedInPost | 1 year | Archive after 1 year |
| ScheduledTask | Indefinite | Keep until manually deleted |
| MCPServer | Indefinite | Keep while server registered |
| TaskQueue | 7 days | Delete completed/failed after 7 days |
| APIRateLimit | Indefinite | Keep while service configured |
| ActivityLog | 1 year | Archive to cold storage after 1 year |

---

## Security Considerations

### Sensitive Data

| Data Type | Storage | Encryption |
|-----------|---------|------------|
| OAuth tokens | .env only | AES-256 |
| Client secrets | .env only | AES-256 |
| Access tokens | .env only | AES-256 |
| Email content | .silver/data/ | None (local only) |
| WhatsApp messages | .silver/data/ | None (local only) |
| Activity logs | Logs/ | None (local only) |

### Access Control

- All API credentials stored in `.env` (never in vault or Git)
- `.env` file permissions: `600` (owner read/write only)
- Vault files: Standard user permissions
- Logs: Standard user permissions

---

## Data Migration (From Bronze Tier)

Silver Tier is **backward compatible** with Bronze Tier:

- ✅ Bronze Tier vault structure: Unchanged
- ✅ Bronze Tier action files: Compatible
- ✅ Bronze Tier logs: Extended with Silver Tier metadata
- ✅ Bronze Tier Dashboard: Enhanced with Silver Tier stats

**No migration required** - Silver Tier adds to existing Bronze Tier data.

---

**Version**: 1.0  
**Created**: 2026-02-25  
**Next Step**: /sp.quickstart → Generate quick start guide
