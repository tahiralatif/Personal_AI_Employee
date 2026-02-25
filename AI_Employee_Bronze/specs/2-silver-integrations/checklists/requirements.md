# Silver Tier Requirements Checklist

## Overview

This document provides validation checklists for Silver Tier development. Use these checklists to ensure completeness before moving to the next phase or releasing.

---

## Pre-Development Checklist

Before starting Silver Tier development, verify:

- [ ] **Bronze Tier is complete and working**
  - [ ] All 41 Bronze Tier tasks completed
  - [ ] File watcher tested and functional
  - [ ] Vault structure created
  - [ ] Dashboard.md updating correctly
  - [ ] Logs being written to Logs/ folder

- [ ] **Development environment ready**
  - [ ] Python 3.12+ installed
  - [ ] uv package manager installed
  - [ ] Git configured
  - [ ] Code editor set up (VS Code recommended)

- [ ] **API accounts created**
  - [ ] Google Cloud Console account
  - [ ] Meta Business account (for WhatsApp)
  - [ ] LinkedIn Developer account
  - [ ] All accounts verified and active

- [ ] **Specifications reviewed**
  - [ ] spec.md read and understood
  - [ ] plan.md timeline confirmed
  - [ ] tasks.md breakdown reviewed
  - [ ] data-model.md entities understood
  - [ ] research.md decisions acknowledged

---

## Phase 1: Setup Checklist

- [ ] **Project structure created**
  - [ ] `AI_Employee_Silver/` folder exists
  - [ ] `src/ai_employee_silver/` folder exists
  - [ ] `tests/` folder exists
  - [ ] `.silver/data/` folder exists

- [ ] **Dependencies installed**
  - [ ] `google-api-python-client` installed
  - [ ] `APScheduler` installed
  - [ ] `filelock` installed
  - [ ] `python-dotenv` installed
  - [ ] All dependencies in `pyproject.toml`

- [ ] **Configuration files created**
  - [ ] `.env.example` with all API templates
  - [ ] `.gitignore` updated for Silver Tier
  - [ ] `README.md` with Silver Tier overview

- [ ] **Git setup**
  - [ ] Branch created: `feature/silver-integrations`
  - [ ] Initial commit pushed

---

## Phase 2: Gmail Integration Checklist

- [ ] **GmailWatcher class implemented**
  - [ ] Class created in `src/ai_employee_silver/gmail_watcher.py`
  - [ ] OAuth 2.0 authentication flow working
  - [ ] Credentials loaded from `.env`
  - [ ] Token stored securely in `.silver/tokens/`

- [ ] **Email fetching working**
  - [ ] Polling every 60 seconds
  - [ ] New emails detected correctly
  - [ ] Attachments extracted properly
  - [ ] Metadata captured (sender, subject, date)

- [ ] **File saving working**
  - [ ] Attachments saved to `Inbox/` folder
  - [ ] Filenames are unique (no collisions)
  - [ ] Email metadata preserved in `.silver/data/emails/`

- [ ] **Error handling implemented**
  - [ ] Rate limit detection working
  - [ ] Queue created when quota exceeded
  - [ ] Retry logic implemented (max 3 retries)
  - [ ] Errors logged to `Logs/` folder

- [ ] **Testing complete**
  - [ ] Unit tests written (10+ tests)
  - [ ] Integration tests written (3+ tests)
  - [ ] All tests passing
  - [ ] Test coverage >80%

- [ ] **Documentation updated**
  - [ ] Gmail API setup guide in README
  - [ ] Troubleshooting section added
  - [ ] Code comments added

---

## Phase 3: WhatsApp Monitoring Checklist

- [ ] **WhatsAppMonitor class implemented**
  - [ ] Class created in `src/ai_employee_silver/whatsapp_monitor.py`
  - [ ] WhatsApp Business API authentication working
  - [ ] Webhook receiver implemented
  - [ ] Polling fallback implemented

- [ ] **Message processing working**
  - [ ] Messages fetched every 30 seconds
  - [ ] Task keyword detection working (NLP lite)
  - [ ] Keywords configurable in `.env`
  - [ ] Non-task messages filtered out

- [ ] **Task file creation working**
  - [ ] Task files created in `Needs_Action/`
  - [ ] Contact name resolved from phone number
  - [ ] Message content preserved
  - [ ] Timestamp recorded (UTC)

- [ ] **Media handling working**
  - [ ] Images downloaded and saved to `Inbox/`
  - [ ] Documents downloaded and saved to `Inbox/`
  - [ ] Voice notes handled (saved or transcribed)
  - [ ] Media linked in task file

- [ ] **Testing complete**
  - [ ] Unit tests written (12+ tests)
  - [ ] Integration tests written (3+ tests)
  - [ ] All tests passing
  - [ ] Test coverage >80%

- [ ] **Documentation updated**
  - [ ] WhatsApp Business API setup guide in README
  - [ ] Twilio alternative documented
  - [ ] Troubleshooting section added

---

## Phase 4: LinkedIn Auto-Posting Checklist

- [ ] **LinkedInPoster class implemented**
  - [ ] Class created in `src/ai_employee_silver/linkedin_poster.py`
  - [ ] LinkedIn API OAuth 2.0 authentication working
  - [ ] Token stored securely

- [ ] **Post creation working**
  - [ ] Text posts supported
  - [ ] Image posts supported (up to 5 images)
  - [ ] Article posts supported (via URL)
  - [ ] Content validation before posting

- [ ] **Scheduling working**
  - [ ] Posts read from `Plans/` folder
  - [ ] Scheduled time respected (within 5 minutes)
  - [ ] Timezone handling correct (UTC storage, local display)

- [ ] **Human approval workflow working**
  - [ ] Posts move to `Pending_Approval/` first
  - [ ] User notification implemented
  - [ ] Approval changes status to "approved"
  - [ ] Rejection moves post back to `Needs_Action/`

- [ ] **Post tracking working**
  - [ ] Post status tracked (draft, pending, approved, published, failed)
  - [ ] Post URL saved after publishing
  - [ ] Engagement metrics fetched (likes, comments, shares)
  - [ ] Metrics logged to `.silver/data/linkedin/`

- [ ] **Error handling implemented**
  - [ ] Content policy violations detected
  - [ ] API errors handled gracefully
  - [ ] Failed posts moved to `Needs_Action/` with error details
  - [ ] Retry logic implemented

- [ ] **Testing complete**
  - [ ] Unit tests written (10+ tests)
  - [ ] Integration tests written (3+ tests)
  - [ ] All tests passing
  - [ ] Test coverage >80%

- [ ] **Documentation updated**
  - [ ] LinkedIn API setup guide in README
  - [ ] Content policy guidelines documented
  - [ ] Troubleshooting section added

---

## Phase 5: Scheduler Checklist

- [ ] **ScheduleManager class implemented**
  - [ ] Class created in `src/ai_employee_silver/scheduler.py`
  - [ ] APScheduler integrated
  - [ ] Background scheduler running

- [ ] **Cron scheduling working**
  - [ ] Cron expressions parsed correctly
  - [ ] Standard cron format supported: `minute hour day month weekday`
  - [ ] Special strings supported: `@yearly`, `@monthly`, `@weekly`, `@daily`, `@hourly`

- [ ] **Task creation working**
  - [ ] Task files created at scheduled times
  - [ ] Task template applied correctly
  - [ ] Target folder configurable (default: `Needs_Action/`)

- [ ] **Timezone handling working**
  - [ ] All times stored in UTC
  - [ ] Display converted to local timezone
  - [ ] Timezone configurable in `.env`
  - [ ] DST (Daylight Saving Time) handled correctly

- [ ] **Holiday policy working**
  - [ ] Holiday list configurable
  - [ ] Skip policy implemented
  - [ ] Reschedule policies implemented (next day, next weekday)

- [ ] **Schedule persistence working**
  - [ ] Schedules survive restarts
  - [ ] Schedule modifications saved (add, remove, update)
  - [ ] Run count tracked correctly

- [ ] **Testing complete**
  - [ ] Unit tests written (10+ tests)
  - [ ] Integration tests written (3+ tests)
  - [ ] All tests passing
  - [ ] Test coverage >80%

- [ ] **Documentation updated**
  - [ ] Cron expression examples in README
  - [ ] Holiday configuration documented
  - [ ] Troubleshooting section added

---

## Phase 6: MCP Coordination Checklist

- [ ] **MCPServer class implemented**
  - [ ] Class created in `src/ai_employee_silver/mcp_server.py`
  - [ ] MCP SDK integrated
  - [ ] Server registration working

- [ ] **File locking working**
  - [ ] filelock library integrated
  - [ ] Lock files created in `.silver/locks/`
  - [ ] Concurrent writes prevented
  - [ ] Lock timeout implemented (prevent deadlocks)

- [ ] **Inter-agent communication working**
  - [ ] Agents can read vault files
  - [ ] Agents can write vault files (with locking)
  - [ ] Agents can signal each other (via status files)

- [ ] **Agent status tracking working**
  - [ ] Heartbeat implemented (every 30 seconds)
  - [ ] Status updated (online, offline, busy)
  - [ ] Dead agent detection working

- [ ] **Conflict resolution working**
  - [ ] First-come-first-served policy implemented
  - [ ] Lock wait queue implemented
  - [ ] Timeout for lock acquisition

- [ ] **Testing complete**
  - [ ] Unit tests written (8+ tests)
  - [ ] Integration tests written (2+ servers)
  - [ ] All tests passing
  - [ ] Test coverage >80%

- [ ] **Documentation updated**
  - [ ] MCP setup guide in README
  - [ ] File locking mechanism documented
  - [ ] Troubleshooting section added

---

## Phase 7: Integration Testing Checklist

- [ ] **End-to-end testing**
  - [ ] All integrations running together
  - [ ] No conflicts between services
  - [ ] Vault access coordinated correctly
  - [ ] Dashboard updates from all sources

- [ ] **Performance testing**
  - [ ] 1000+ emails/day processed without issues
  - [ ] 500+ WhatsApp messages/day processed
  - [ ] 50+ LinkedIn posts/day handled
  - [ ] Memory usage <500MB
  - [ ] CPU usage <50% during normal operation

- [ ] **Load testing**
  - [ ] Concurrent API calls handled
  - [ ] Rate limits respected across services
  - [ ] Queue management working under load

- [ ] **Error scenario testing**
  - [ ] Gmail API down → queued and retried
  - [ ] WhatsApp API down → queued and retried
  - [ ] LinkedIn API down → posts queued
  - [ ] Network interruption → graceful handling
  - [ ] Vault file locked by another process → wait and retry

- [ ] **Security audit**
  - [ ] All credentials in `.env` only
  - [ ] `.env` excluded from Git
  - [ ] Tokens encrypted at rest
  - [ ] API scopes minimal (read-only where possible)
  - [ ] No hardcoded credentials in code
  - [ ] File permissions correct (`.env` is 600)

- [ ] **User acceptance testing**
  - [ ] Real-world scenarios tested
  - [ ] Feedback collected
  - [ ] Critical bugs fixed
  - [ ] Usability improvements implemented

---

## Phase 8: Polish & Release Checklist

- [ ] **Code quality**
  - [ ] No debug statements left in code
  - [ ] No unused imports
  - [ ] No dead code
  - [ ] Consistent code style (PEP 8)
  - [ ] Type hints on all public interfaces
  - [ ] Docstrings on all classes and methods

- [ ] **Documentation complete**
  - [ ] Main README.md updated with Silver Tier features
  - [ ] Quick Start Guide created (`docs/QUICKSTART.md`)
  - [ ] Troubleshooting Guide created (`docs/TROUBLESHOOTING.md`)
  - [ ] API Setup Guide created (`docs/API_SETUP.md`)
  - [ ] All code examples tested

- [ ] **Git hygiene**
  - [ ] All changes committed
  - [ ] Commit messages follow convention: `[silver] type: description`
  - [ ] Branch pushed to remote
  - [ ] Pull request created to `develop` branch

- [ ] **Release preparation**
  - [ ] Version number updated (v1.0.0)
  - [ ] Release notes written
  - [ ] Changelog updated
  - [ ] Tag created: `v1.0.0-silver`

- [ ] **Post-release**
  - [ ] GitHub release published
  - [ ] Users notified (if applicable)
  - [ ] Documentation published
  - [ ] Support channel ready for questions

---

## Per-Feature Validation Checklists

### Gmail Integration Validation

Run these tests to validate Gmail integration:

- [ ] Send test email with attachment → Verify attachment in `Inbox/` within 60 seconds
- [ ] Send email with 5 attachments → Verify all 5 attachments saved
- [ ] Send 100 emails in 1 minute → Verify rate limit handling
- [ ] Disconnect internet → Verify queue creation
- [ ] Reconnect internet → Verify queue processing
- [ ] Revoke OAuth token → Verify re-authentication flow
- [ ] Check logs → Verify all operations logged

### WhatsApp Integration Validation

Run these tests to validate WhatsApp integration:

- [ ] Send text message with task keyword → Verify task file in `Needs_Action/`
- [ ] Send text message without task keyword → Verify no task created
- [ ] Send image message → Verify image saved to `Inbox/` and task created
- [ ] Send message from group → Verify group info captured
- [ ] Send 50 messages in 1 minute → Verify rate limit handling
- [ ] Check logs → Verify all operations logged

### LinkedIn Integration Validation

Run these tests to validate LinkedIn integration:

- [ ] Create post with scheduled time → Verify post published at scheduled time
- [ ] Create post with image → Verify image posted correctly
- [ ] Create post, approve manually → Verify approval workflow working
- [ ] Create post, reject manually → Verify rejection workflow working
- [ ] Simulate API error → Verify post moved to `Needs_Action/` with error
- [ ] Check engagement metrics → Verify metrics fetched and logged

### Scheduler Validation

Run these tests to validate scheduler:

- [ ] Create schedule for 1 minute from now → Verify task created on time
- [ ] Create schedule with holiday → Verify holiday policy applied
- [ ] Change timezone → Verify schedule adjusts correctly
- [ ] Restart service → Verify schedule persists and next run correct
- [ ] Create 100 schedules → Verify all schedules run correctly

### MCP Coordination Validation

Run these tests to validate MCP coordination:

- [ ] Start 2 MCP servers → Verify both can access vault
- [ ] Both servers write to same file → Verify no corruption (locking works)
- [ ] Kill one server → Verify other server continues
- [ ] Check heartbeat → Verify status updates correctly

---

## Security Checklist

- [ ] **Credential Storage**
  - [ ] All API credentials in `.env` file only
  - [ ] `.env` file has permissions 600 (owner read/write only)
  - [ ] `.env` excluded from Git (in `.gitignore`)
  - [ ] Tokens encrypted before storage
  - [ ] No credentials in logs

- [ ] **API Security**
  - [ ] OAuth scopes minimal (only what's needed)
  - [ ] Token refresh implemented (no long-lived tokens)
  - [ ] API calls use HTTPS only
  - [ ] Rate limits respected (no abuse)

- [ ] **Data Security**
  - [ ] Vault files have appropriate permissions
  - [ ] Logs don't contain sensitive data
  - [ ] Email content stored locally only
  - [ ] No data sent to external servers (except API calls)

- [ ] **Code Security**
  - [ ] No hardcoded credentials in code
  - [ ] Input validation on all user inputs
  - [ ] SQL injection prevention (if using database)
  - [ ] File path traversal prevention

---

## Performance Checklist

- [ ] **Memory Usage**
  - [ ] Baseline memory <200MB
  - [ ] Memory under load <500MB
  - [ ] No memory leaks (tested with long-running process)

- [ ] **CPU Usage**
  - [ ] Baseline CPU <10%
  - [ ] CPU under load <50%
  - [ ] No infinite loops or busy-waiting

- [ ] **Disk Usage**
  - [ ] Log rotation implemented (max 10MB per log)
  - [ ] Old logs archived/deleted
  - [ ] Attachment storage monitored

- [ ] **Network Usage**
  - [ ] API calls batched where possible
  - [ ] Unnecessary polling avoided
  - [ ] Bandwidth usage documented

---

## Sign-Off

### Development Team

- [ ] **Lead Developer**: All code reviewed and approved
- [ ] **QA Engineer**: All tests passing, coverage >80%
- [ ] **Security Engineer**: Security audit passed
- [ ] **Technical Writer**: Documentation complete

### Product Team

- [ ] **Product Manager**: All user stories implemented
- [ ] **UX Reviewer**: User experience validated
- [ ] **Beta Tester**: Real-world testing completed

### Release Approval

- [ ] **Project Owner**: Silver Tier v1.0.0 approved for release
- [ ] **Release Date**: _______________
- [ ] **Release Notes**: Published to GitHub

---

**Version**: 1.0  
**Created**: 2026-02-25  
**Last Updated**: 2026-02-25  
**Next Review**: Before each Silver Tier release
