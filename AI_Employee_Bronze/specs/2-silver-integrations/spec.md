# Silver Tier AI Employee - Integrations

## Feature Description

Build upon the Bronze Tier foundation to create an automated AI employee system that integrates with external services (Gmail, WhatsApp, LinkedIn) to automatically collect tasks, process them using AI, and maintain an Obsidian vault as its brain and dashboard. The system operates on a hybrid model - local processing with optional cloud integrations, always maintaining human-in-the-loop for sensitive actions.

**Key Difference from Bronze:**
- **Bronze**: Manual file drop → Automatic processing
- **Silver**: Automatic file collection → Automatic processing

---

## User Scenarios & Testing

### User Story 1 - Gmail Integration (Priority: P1)

User configures the system to monitor their Gmail account for emails with attachments. When a new email arrives with an attachment (invoice, document, etc.), the system automatically saves it to the Inbox folder, and the Bronze Tier watcher processes it as usual.

**Why this priority**: Email is the most common business communication channel. Automating email attachment processing eliminates the most frequent manual task from Bronze Tier.

**Independent Test**: Can be fully tested by sending a test email with attachment and verifying the attachment is saved to Inbox and processed into Needs_Action within 60 seconds.

**Acceptance Scenarios**:

1. **Given** a Gmail account is configured, **When** a new email with attachment arrives, **Then** the attachment is saved to Inbox/ within 60 seconds with proper naming
2. **Given** an email is processed, **When** the system saves the attachment, **Then** an action file is created in Needs_Action/ with email metadata (sender, subject, received date)
3. **Given** multiple attachments in one email, **When** the email is processed, **Then** each attachment is saved separately with unique filenames

---

### User Story 2 - WhatsApp Business Monitoring (Priority: P1)

User connects their WhatsApp Business account to monitor incoming messages. When a message contains text that looks like a task (keywords: "please", "need", "urgent", "task", etc.), the system creates a task file in Needs_Action with the message content.

**Why this priority**: WhatsApp is widely used for business communication in many regions. Automating message-to-task conversion captures tasks that would otherwise be lost.

**Independent Test**: Can be fully tested by sending a WhatsApp message to the business number and verifying a task file is created in Needs_Action within 120 seconds.

**Acceptance Scenarios**:

1. **Given** WhatsApp Business API is configured, **When** a message is received, **Then** the system evaluates if it's a task within 30 seconds
2. **Given** a message is identified as a task, **When** the system processes it, **Then** a task file is created in Needs_Action/ with contact name, message content, and timestamp
3. **Given** a message contains media (image, document), **When** the message is processed, **Then** media is saved to Inbox/ and linked in the task file

---

### User Story 3 - LinkedIn Auto-Posting (Priority: P2)

User creates content in the vault (e.g., achievements, updates, articles) and marks them for LinkedIn posting. The system automatically posts to LinkedIn at scheduled times and logs the post status in the vault.

**Why this priority**: Professional networking requires consistent presence. Automating posting saves time while maintaining control over content.

**Independent Test**: Can be fully tested by creating a post in Plans/ folder with scheduled time and verifying it's posted to LinkedIn at the scheduled time.

**Acceptance Scenarios**:

1. **Given** a post is created in Plans/ with LinkedIn metadata, **When** the scheduled time arrives, **Then** the post is published to LinkedIn within 5 minutes
2. **Given** a post is published, **When** the system confirms success, **Then** the post file is moved to Done/ with post URL and engagement metrics
3. **Given** a post fails to publish, **When** the system detects failure, **Then** the file is moved to Needs_Action/ with error details for manual review

---

### User Story 4 - Scheduled Task Execution (Priority: P2)

User creates recurring tasks (daily reports, weekly reviews, monthly summaries) that the system automatically triggers at specified intervals. The system creates task files in Needs_Action at the scheduled times.

**Why this priority**: Many business tasks are recurring. Automating schedule-based task creation ensures nothing is forgotten.

**Independent Test**: Can be fully tested by creating a scheduled task and verifying it appears in Needs_Action at the scheduled time.

**Acceptance Scenarios**:

1. **Given** a schedule is configured (e.g., "every Monday at 9 AM"), **When** the scheduled time arrives, **Then** a task file is created in Needs_Action/ within 5 minutes
2. **Given** a recurring task is created, **When** the task is completed, **Then** the next occurrence is automatically scheduled
3. **Given** a scheduled task conflicts with a holiday, **When** the system detects the conflict, **Then** the task is rescheduled to the next working day

---

### User Story 5 - MCP Server Coordination (Priority: P3)

User can run multiple AI agents (via MCP servers) that coordinate through the vault. One agent might handle email, another handles WhatsApp, another handles analysis - all sharing the same vault.

**Why this priority**: Complex workflows may require multiple specialized AI agents. MCP provides a standard way to coordinate them.

**Independent Test**: Can be fully tested by running two MCP servers and verifying they can both read/write to the vault without conflicts.

**Acceptance Scenarios**:

1. **Given** multiple MCP servers are running, **When** they access the vault simultaneously, **Then** file locks prevent conflicts
2. **Given** an MCP server completes a task, **When** it updates the vault, **Then** the Dashboard reflects the change within 10 seconds
3. **Given** an MCP server needs human approval, **When** it moves a task to Pending_Approval/, **Then** the user is notified

---

### Edge Cases

- **What happens when Gmail API quota is exceeded?** → Queue emails locally, process when quota resets
- **How does the system handle WhatsApp API downtime?** → Retry with exponential backoff, log failures
- **What if LinkedIn post fails due to content policy?** → Move to Needs_Action/ with error, notify user
- **How are timezone changes handled for scheduled tasks?** → Store all times in UTC, convert to local for display
- **What if multiple services try to modify the same file?** → File locking mechanism prevents conflicts
- **How are API credential rotations handled?** → Credentials in .env, hot-reload supported

---

## Requirements

### Functional Requirements

- **FR-S001**: System MUST connect to Gmail API and fetch new emails every 60 seconds
- **FR-S002**: System MUST save email attachments to Inbox/ with metadata (sender, subject, date)
- **FR-S003**: System MUST connect to WhatsApp Business API and fetch new messages every 30 seconds
- **FR-S004**: System MUST analyze WhatsApp messages for task keywords and create task files
- **FR-S005**: System MUST connect to LinkedIn API and publish scheduled posts
- **FR-S006**: System MUST support cron-style scheduling for recurring tasks
- **FR-S007**: System MUST create task files for scheduled events at the specified time
- **FR-S008**: System MUST support MCP server protocol for multi-agent coordination
- **FR-S009**: System MUST implement file locking to prevent concurrent modification conflicts
- **FR-S010**: System MUST retry failed API calls with exponential backoff (max 3 retries)
- **FR-S011**: System MUST log all API interactions to Logs/ folder with timestamps
- **FR-S012**: System MUST support multiple Gmail/WhatsApp/LinkedIn accounts (configurable)
- **FR-S013**: System MUST validate API responses and handle errors gracefully
- **FR-S014**: System MUST queue tasks locally when APIs are unavailable
- **FR-S015**: System MUST notify user of critical failures (email/WhatsApp down)

---

### Non-functional Requirements

- **NFR-S001**: System MUST process emails within 60 seconds of receipt
- **NFR-S002**: System MUST process WhatsApp messages within 30 seconds of receipt
- **NFR-S003**: System MUST post to LinkedIn within 5 minutes of scheduled time
- **NFR-S004**: System MUST support 1000+ emails per day without performance degradation
- **NFR-S005**: System MUST support 500+ WhatsApp messages per day without performance degradation
- **NFR-S006**: System MUST support 50+ scheduled posts per day
- **NFR-S007**: System MUST store API credentials securely in .env (never in vault or Git)
- **NFR-S008**: System MUST comply with Gmail API Terms of Service
- **NFR-S009**: System MUST comply with WhatsApp Business Policy
- **NFR-S010**: System MUST comply with LinkedIn API Terms of Service
- **NFR-S011**: System MUST work offline and sync when connection is restored
- **NFR-S012**: System MUST use less than 500MB RAM during normal operation
- **NFR-S013**: System MUST start within 10 seconds of launch command
- **NFR-S014**: System MUST provide health status endpoint for monitoring

---

### Key Entities

- **EmailMessage**: Represents an email from Gmail with attachments
- **WhatsAppMessage**: Represents a WhatsApp message with media
- **LinkedInPost**: Represents a scheduled LinkedIn post
- **ScheduledTask**: Represents a recurring task with cron schedule
- **MCPServer**: Represents an MCP server connection
- **APICredential**: Represents API credentials for external services
- **TaskQueue**: Represents queued tasks waiting for API availability

---

## Success Criteria

### Measurable Outcomes

- **SC-S001**: User can configure Gmail integration in under 10 minutes
- **SC-S002**: Email attachments are saved to Inbox within 60 seconds of receipt (95% of cases)
- **SC-S003**: WhatsApp messages are processed within 30 seconds of receipt (95% of cases)
- **SC-S004**: LinkedIn posts are published at scheduled time (99% accuracy)
- **SC-S005**: System handles 1000+ emails/day without manual intervention
- **SC-S006**: No API credentials are stored in vault or committed to Git
- **SC-S007**: All API interactions are logged with timestamps
- **SC-S008**: System recovers from API failures within 5 minutes (auto-retry)
- **SC-S009**: Scheduled tasks are created at correct time (100% accuracy)
- **SC-S010**: Multiple MCP servers can coordinate without file conflicts

---

## Assumptions

- User has a Gmail account with API access enabled
- User has WhatsApp Business API access (or will use alternative)
- User has LinkedIn account with API access enabled
- User has stable internet connection for cloud integrations
- User has Bronze Tier installed and working
- User understands API rate limits and quotas
- User will configure credentials in .env file

---

## Dependencies

- **Bronze Tier**: File watcher, vault structure, action file generation
- **Gmail API**: For email fetching (google-api-python-client)
- **WhatsApp Business API**: For message monitoring (meta-business-sdk)
- **LinkedIn API**: For post publishing (linkedin-api-client)
- **APScheduler**: For scheduled task execution
- **MCP SDK**: For multi-agent coordination
- **Python 3.12+**: Required for async support
- **Internet Connection**: Required for API calls

---

## Out of Scope

- **Email sending** (read-only for Silver, sending in Gold Tier)
- **WhatsApp message sending** (read-only for Silver)
- **LinkedIn connection management** (only posting in Silver)
- **Payment automation** (Gold Tier)
- **CEO Briefing generation** (Gold Tier)
- **Cloud deployment** (Platinum Tier)
- **Multi-user support** (single user in Silver)
- **Mobile app** (web viewing only)
- **Custom integrations** (only Gmail, WhatsApp, LinkedIn in Silver)
- **AI model training** (uses existing models)

---

## Clarifications

### Session 2026-02-25

- **Q**: Should Silver Tier work independently or depend on Bronze? → **A**: Depends on Bronze for file processing, Silver only adds collection layer
- **Q**: What happens if Gmail API quota is exceeded? → **A**: Queue locally, process when quota resets, notify user
- **Q**: Can user have multiple Gmail accounts? → **A**: Yes, configurable in .env with multiple credential sets
- **Q**: How to handle WhatsApp without Business API? → **A**: Use webhook-based alternative or manual forward mechanism
- **Q**: Should LinkedIn posts be auto-approved? → **A**: No, posts go to Pending_Approval/ first, user confirms before publishing
- **Q**: What timezone for scheduled tasks? → **A**: Store in UTC, display in user's local timezone from .env
- **Q**: How to handle API credential rotation? → **A**: Hot-reload .env file, no restart required

---

## Tier Roadmap Context

```
Bronze Tier (Current):  ✅ File monitoring + Action file generation
                        ✅ Manual file drop → Automatic processing

Silver Tier (Next):     🆕 Gmail integration (auto-collect)
                        🆕 WhatsApp monitoring (auto-collect)
                        🆕 LinkedIn posting (auto-publish)
                        🆕 Scheduled tasks (cron-based)
                        🆕 MCP coordination (multi-agent)

Gold Tier (Future):     💰 Payment automation
                        📧 Email sending
                        📊 CEO Briefing generation

Platinum (Dream):       ☁️ Cloud 24/7 deployment
                        🤖 Multi-agent coordination
                        🌐 Full automation
```

---

**Specification Version**: 1.0
**Created**: 2026-02-25
**Based on**: Bronze Tier v1.0 (working foundation)
**Next Step**: /sp.plan → Generate implementation plan
