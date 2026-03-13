# Silver Tier Specification: AI Employee Integrations

## Overview

The Silver Tier builds upon the Bronze Tier foundation by implementing additional watchers and integrations to create a functional AI assistant. This tier focuses on expanding the perception layer with multiple data sources and adding action capabilities through MCP servers.

## Requirements from Hackathon Document

Based on the "Personal AI Employee Hackathon 0_ Building Autonomous FTEs in 2026.md" document, the Silver Tier requirements are:

### Silver Tier: Functional Assistant (20-30 hours)

- [ ] All Bronze requirements plus:
- [ ] Two or more Watcher scripts (Gmail + WhatsApp + LinkedIn)
- [ ] Automatically post on LinkedIn about business to generate sales
- [ ] Claude reasoning loop that creates `Plan.md` files
- [ ] One working MCP server for external action (e.g., sending emails)
- [ ] Human-in-the-loop approval workflow for sensitive actions
- [ ] Basic scheduling via cron or Task Scheduler
- [ ] **All AI functionality implemented as Agent Skills**

## Agent Skills Architecture

**Critical Requirement**: All AI functionality MUST be implemented as Agent Skills per hackathon requirements. This ensures:
- Modular, reusable components
- Clear capability boundaries
- Easy testing and debugging
- Consistent interface patterns

### Agent Skills Pattern

```python
# Example: Agent Skill for Gmail operations
class GmailSkills:
    @skill
    def read_emails(self, query: str) -> list:
        """Read emails matching query"""
        pass
    
    @skill
    def send_email(self, to: str, subject: str, body: str) -> bool:
        """Send an email"""
        pass
```

### Skill Categories

1. **Perception Skills** (Watchers)
   - `gmail.read_emails()`
   - `whatsapp.read_messages()`
   - `linkedin.check_connections()`
   - `filesystem.watch_drop_folder()`

2. **Action Skills** (MCP Servers)
   - `email.send_email()`
   - `email.create_draft()`
   - `browser.navigate()`
   - `browser.click_element()`
   - `linkedin.post_update()`
   - `linkedin.send_message()`

3. **Reasoning Skills** (Planning)
   - `planning.create_plan()`
   - `planning.validate_plan()`
   - `approval.request_approval()`
   - `approval.check_status()`

4. **Utility Skills**
   - `vault.move_file()`
   - `vault.read_file()`
   - `vault.write_file()`
   - `dashboard.update_status()`

## Technical Specifications

### 1. Enhanced Watcher System

#### 1.1 Gmail Watcher
- **Purpose**: Monitor Gmail for new important emails
- **Technology**: Google API with OAuth 2.0
- **Frequency**: Poll every 2 minutes
- **Trigger**: Unread emails marked as important
- **Action**: Create structured `.md` files in `Needs_Action/Gmail/`

**Features:**
- OAuth 2.0 authentication with refresh tokens
- Email parsing with header extraction
- Priority classification (high, medium, low)
- Mark emails as read after processing
- Error handling for API quotas

#### 1.2 WhatsApp Watcher
- **Purpose**: Monitor WhatsApp for urgent business messages
- **Technology**: Playwright with WhatsApp Web
- **Frequency**: Poll every 30 seconds
- **Trigger**: Unread messages with keywords ('urgent', 'asap', 'invoice', 'payment', 'help', 'task', Urdu equivalents)
- **Action**: Create structured `.md` files in `Needs_Action/WhatsApp/`

**Features:**
- Persistent session storage
- Keyword detection in multiple languages (English + Urdu)
- Message thread identification
- Error handling for session timeouts

#### 1.3 LinkedIn Watcher
- **Purpose**: Monitor LinkedIn for business opportunities and connections
- **Technology**: Playwright with LinkedIn Web
- **Frequency**: Poll every 5 minutes
- **Trigger**: New connection requests, messages, or relevant posts
- **Action**: Create structured `.md` files in `Needs_Action/LinkedIn/`

**Features:**
- Business opportunity detection
- Connection management
- Content monitoring
- Automated response to basic inquiries

#### 1.4 File System Watcher (Enhanced)
- **Purpose**: Continue monitoring Inbox folder with enhanced capabilities
- **Technology**: watchdog library
- **Frequency**: Event-driven
- **Trigger**: New files dropped in Inbox
- **Action**: Create structured `.md` files in `Needs_Action/FileDrop/`

**Enhancements:**
- Support for multiple file types
- Content preview for document processing
- Enhanced security scanning
- Better quarantine handling

### 2. MCP Server Integration

#### 2.1 Email MCP Server
- **Purpose**: Send emails via Gmail API
- **Technology**: Node.js MCP server with Google APIs
- **Capabilities**:
  - Send emails with attachments
  - Create draft emails
  - Search and read emails
  - Manage labels and folders

#### 2.2 Browser MCP Server
- **Purpose**: Automate web interactions
- **Technology**: Node.js MCP server with Playwright
- **Capabilities**:
  - Navigate to web pages
  - Click elements and buttons
  - Fill forms and input fields
  - Take screenshots
  - Extract data from web pages

#### 2.3 LinkedIn MCP Server
- **Purpose**: Automate LinkedIn interactions for business growth and sales generation
- **Technology**: Node.js MCP server with Playwright
- **Capabilities**:
  - **Post updates to LinkedIn** (including sales-focused content)
  - **Generate and post business promotion content**
  - **Schedule posts for optimal engagement times**
  - Send connection requests
  - Like and comment on posts
  - Send messages to connections
  - **Track post engagement metrics**

**Sales-Focused Features:**
- Auto-generate posts from business milestones
- Create content from completed projects (with client permission)
- Post about services offered
- Share industry insights with business call-to-action
- Engage with potential leads' content

### 3. Enhanced Reasoning Loop

#### 3.1 Plan Generation
- **Purpose**: Create detailed action plans in `Plans/` folder
- **Format**: Structured `.md` files with YAML frontmatter
- **Content**: Step-by-step execution plans with checkpoints

**Plan File Structure:**
```markdown
---
type: action_plan
task_id: unique_identifier
created: ISO_timestamp
status: pending/in-progress/completed/failed
estimated_duration: minutes
priority: high/medium/low
author: ai_employee
---

# Action Plan: [Task Description]

## Objective
[Clear objective statement]

## Prerequisites
- [ ] Item 1
- [ ] Item 2

## Steps
1. [Step 1 with details]
2. [Step 2 with details]
3. [Step 3 with details]

## Dependencies
- Task ID: [dependent_task_id]

## Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Approval Required
- [ ] Human approval needed for sensitive actions
- [ ] Budget approval for payments over threshold

## Rollback Plan
[Steps to undo actions if needed]
```

#### 3.2 Enhanced Dashboard Updates
- **Purpose**: More detailed status reporting
- **Frequency**: After each task completion
- **Content**: Task statistics, completion rates, performance metrics

### 4. Human-in-the-Loop (HITL) Enhancement

#### 4.1 Approval Workflow
- **Purpose**: Expanded approval system for various action types
- **Categories**:
  - Financial (payments, transfers)
  - Communications (emails, social posts)
  - Data access (sensitive information)
  - System changes (configuration, permissions)

#### 4.2 Approval File Structure
```markdown
---
type: approval_request
action: payment/email/social_post/data_access
action_id: unique_action_identifier
created: ISO_timestamp
expires: ISO_timestamp
status: pending/approved/rejected
requestor: ai_employee
urgency: high/medium/low
category: financial/communication/data/system
---

# Approval Request

## Action Details
- **Type**: [action type]
- **Target**: [destination/target]
- **Amount**: [if financial]
- **Content Preview**: [first 200 characters]

## Business Justification
[Reason for requesting approval]

## Risk Assessment
- **Financial Risk**: [low/medium/high]
- **Reputation Risk**: [low/medium/high]
- **Security Risk**: [low/medium/high]

## Approval Options
1. **Approve**: Move file to `/Approved/` folder
2. **Reject**: Move file to `/Rejected/` folder with reason
3. **Modify**: Edit this file and move to `/Pending_Approval/` again

## Auto-Reject
This request will auto-reject on [expiration_time] if no action taken.
```

### 5. Scheduling System

#### 5.1 Task Scheduler
- **Purpose**: Schedule recurring tasks and periodic actions
- **Technology**:
  - cron (Linux/macOS)
  - Task Scheduler (Windows)
  - Or cross-platform solution like APScheduler

#### 5.2 Scheduled Tasks
- Daily business summary generation
- Weekly LinkedIn post scheduling
- Monthly expense tracking
- Quarterly review preparation

### 6. Security Enhancements

#### 6.1 Permission Boundaries
| Action Category | Auto-Approve Threshold | Require Approval |
|----------------|------------------------|------------------|
| Email replies | To known contacts | New contacts, bulk sends |
| Payments | < $50 recurring | All new payees, > $100 |
| Social media | Scheduled posts | Replies, DMs, sensitive topics |
| File operations | Create, read | Delete, move outside vault |

#### 6.2 Credential Management
- Secure storage of API keys and tokens
- OAuth token refresh mechanisms
- Session management for web automation
- Environment variable usage for sensitive data

## Acceptance Criteria

### Functional Requirements
- [ ] Gmail watcher successfully monitors and creates action files
- [ ] WhatsApp watcher detects messages and creates action files
- [ ] LinkedIn watcher monitors activity and creates action files
- [ ] Email MCP server can send emails
- [ ] Browser MCP server can automate web tasks
- [ ] LinkedIn MCP server can post updates
- [ ] Plan generation works correctly with proper format
- [ ] Approval workflow functions as specified
- [ ] Scheduling system works across platforms

### Non-Functional Requirements
- [ ] System maintains 99% uptime during business hours
- [ ] Response time for new items < 30 seconds
- [ ] Error handling for API failures and network issues
- [ ] Secure credential management
- [ ] Proper logging and audit trails

## Success Metrics
- [ ] 95% of tasks processed without human intervention
- [ ] Average response time to new items < 15 seconds
- [ ] Zero unauthorized actions performed
- [ ] 100% of sensitive actions properly routed through approval workflow

## Integration Points
- Gmail API integration
- WhatsApp Web automation
- LinkedIn Web automation
- MCP server communication
- Vault file system operations
- External service APIs