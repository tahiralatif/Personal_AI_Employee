# Data Model for Bronze Tier AI Employee - Vault Setup

## Core Entities

### Task File
Represents a file dropped in the Inbox that needs processing.

**Attributes**:
- `original_name`: str - Original filename with extension
- `received_timestamp`: datetime - Time when file was detected
- `size_bytes`: int - Size of the file in bytes
- `priority`: str - Priority level (low, medium, high)
- `status`: str - Current status (pending, processing, completed, error)
- `file_path`: str - Current path of the file in the system

**Validation Rules**:
- `original_name` must not exceed 255 characters
- `size_bytes` must be <= 100MB (104,857,600 bytes)
- `priority` must be one of: low, medium, high
- `status` must be one of: pending, processing, completed, error

### Action File
Structured .md file created in Needs_Action from incoming task files; contains YAML frontmatter with metadata.

**Attributes**:
- `file_name`: str - Name of the action file (based on original_name)
- `yaml_frontmatter`: dict - Contains type, original_name, received timestamp, priority, status
- `content`: str - Additional content extracted from the original file
- `created_timestamp`: datetime - Time when action file was created
- `assigned_to`: str - Who the task is assigned to (default: Claude)

**Validation Rules**:
- `file_name` must have .md extension
- `yaml_frontmatter` must contain all required fields: type, original_name, received, priority, status
- `content` must be valid markdown

### Log Entry
Record of system activity with timestamp, action type, detail, and result.

**Attributes**:
- `timestamp`: datetime - When the event occurred
- `action_type`: str - Type of action (file_detected, file_processed, error, etc.)
- `detail`: str - Details about the action
- `result`: str - Result of the action (success, failure, warning)
- `file_reference`: str - Reference to the file involved (optional)

**Validation Rules**:
- `timestamp` must be in ISO format
- `action_type` must be one of: file_detected, file_processed, error, system_start, system_stop
- `result` must be one of: success, failure, warning

### Dashboard
Central document showing system status, pending tasks, and quick links.

**Attributes**:
- `last_updated`: datetime - Time when dashboard was last updated
- `pending_tasks_count`: int - Number of tasks in Needs_Action folder
- `completed_today`: int - Number of tasks completed today
- `recent_activity`: list - Recent log entries
- `system_status`: str - Current system status (running, stopped, error)

**Validation Rules**:
- `system_status` must be one of: running, stopped, error
- `pending_tasks_count` must be >= 0
- `completed_today` must be >= 0

### Company Handbook
Document containing rules and guidelines for AI agent behavior.

**Attributes**:
- `version`: str - Version of the handbook
- `authorized_actions`: list - Actions the AI is authorized to perform
- `prohibited_actions`: list - Actions the AI is prohibited from performing
- `escalation_procedures`: list - Procedures for when human approval is needed
- `last_updated`: datetime - Time when handbook was last updated

**Validation Rules**:
- `version` must follow semantic versioning
- `authorized_actions`, `prohibited_actions`, and `escalation_procedures` must not be empty

## State Transitions

### Task File States
```
pending → processing → completed
            ↓
          error → retry → processing
```

### Action File States
```
created → assigned → in_progress → completed
                              ↓
                            cancelled
```

## Relationships

- **Task File** → **Action File** (1:1 relationship when a task file is processed)
- **Log Entry** → **Task File** (1:many relationship, many logs for one task)
- **Dashboard** → **Task File** (1:many relationship, dashboard aggregates task info)
- **Company Handbook** → **Action File** (1:many relationship, handbook guides all actions)