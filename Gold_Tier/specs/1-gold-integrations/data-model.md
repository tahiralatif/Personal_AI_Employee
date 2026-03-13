# Gold Tier Data Model

## Overview
This document defines the data models used in the Gold Tier of the AI Employee system. It includes enhanced data structures for Odoo integration, social media platforms, audit logging, and cross-domain operations.

---

## Enhanced File Structures

### 1. Odoo Accounting Action File Structure
Location: `Needs_Action/Accounting/`

```yaml
---
type: accounting
source: odoo
action_type: invoice_created  # invoice_created, payment_received, expense_flagged, overdue_payment
created: "2026-03-12T10:30:00Z"
priority: "high"          # high, medium, low
status: "pending"         # pending, in-progress, completed, failed
domain: "business"
odoo_id: "unique_odoo_identifier"
amount: 5000.00
currency: "PKR"
customer_id: 123
customer_name: "ABC Corporation"
due_date: "2026-03-26"
---

# Accounting Event Details

## Invoice Information
- **Invoice Number**: INV/2026/00123
- **Customer**: ABC Corporation
- **Amount**: PKR 5,000.00
- **Due Date**: March 26, 2026
- **Items**:
  1. Item 1 - PKR 3,000.00
  2. Item 2 - PKR 2,000.00

## Suggested Actions
- [ ] Send invoice to customer
- [ ] Schedule payment follow-up
- [ ] Record in accounting ledger
- [ ] Flag for approval if amount > threshold
```

### 2. Facebook Action File Structure
Location: `Needs_Action/Social/Facebook/`

```yaml
---
type: social_media
platform: facebook
action_type: post_engagement  # post_engagement, comment_received, mention_received
created: "2026-03-12T10:30:00Z"
priority: "medium"        # high, medium, low
status: "pending"         # pending, in-progress, completed, failed
domain: "business"
post_id: "facebook_post_id"
engagement_type: comment
engagement_count: 15
---

# Facebook Activity Details

## Post Information
- **Post ID**: 123456789
- **Content**: "Excited to announce our new product..."
- **Published**: 2026-03-12T09:00:00Z
- **Engagement**:
  - Likes: 45
  - Comments: 15
  - Shares: 8
  - Reach: 2,500

## Recent Comments
1. User 1: "Great product! How much does it cost?"
2. User 2: "Is this available in Lahore?"

## Suggested Actions
- [ ] Respond to comments
- [ ] Thank users for engagement
- [ ] Create follow-up post
- [ ] Analyze engagement metrics
```

### 3. Instagram Action File Structure
Location: `Needs_Action/Social/Instagram/`

```yaml
---
type: social_media
platform: instagram
action_type: media_posted  # media_posted, story_posted, engagement_spike
created: "2026-03-12T10:30:00Z"
priority: "medium"        # high, medium, low
status: "pending"         # pending, in-progress, completed, failed
domain: "business"
media_id: "instagram_media_id"
media_type: image         # image, carousel, video, story
engagement_count: 234
---

# Instagram Activity Details

## Media Information
- **Media ID**: 987654321
- **Type**: Image
- **Caption**: "Behind the scenes at our office..."
- **Hashtags**: #business #entrepreneur #pakistan
- **Published**: 2026-03-12T08:00:00Z
- **Engagement**:
  - Likes: 189
  - Comments: 34
  - Saves: 45
  - Reach: 3,200
  - Impressions: 4,500

## Top Comments
1. User 1: "Love this! 😍"
2. User 2: "Where are you based?"

## Suggested Actions
- [ ] Respond to comments
- [ ] Analyze hashtag performance
- [ ] Schedule similar content
- [ ] Track engagement trends
```

### 4. Twitter (X) Action File Structure
Location: `Needs_Action/Social/Twitter/`

```yaml
---
type: social_media
platform: twitter
action_type: mention_received  # mention_received, tweet_posted, engagement_spike
created: "2026-03-12T10:30:00Z"
priority: "high"          # high, medium, low
status: "pending"         # pending, in-progress, completed, failed
domain: "business"
tweet_id: "twitter_tweet_id"
mention_type: direct      # direct, retweet, quote
---

# Twitter Activity Details

## Tweet Information
- **Tweet ID**: 1234567890123456789
- **Author**: @username
- **Content**: "@yourhandle Great service! Highly recommended."
- **Published**: 2026-03-12T10:15:00Z
- **Engagement**:
  - Likes: 12
  - Retweets: 3
  - Replies: 2
  - Impressions: 850

## Suggested Actions
- [ ] Respond to mention
- [ ] Retweet with comment
- [ ] Thank user
- [ ] Track sentiment
```

### 5. Enhanced CEO Briefing Structure
Location: `Briefings/`

```yaml
---
type: ceo_briefing
period: weekly
period_start: "2026-03-04"
period_end: "2026-03-10"
generated: "2026-03-11T07:00:00Z"
generated_by: ai_employee
domain: "business"
priority: high
status: completed
---

# CEO Briefing: Week of March 4-10, 2026

## Executive Summary
**Overall Status**: 🟢 Strong Performance

This week showed strong revenue growth with PKR 450,000 in new invoices. Social media engagement increased 25% across all platforms. One bottleneck identified in payment collection.

---

## Revenue Analysis

### Weekly Revenue
| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| New Invoices | PKR 450,000 | PKR 380,000 | +18.4% |
| Payments Received | PKR 420,000 | PKR 350,000 | +20.0% |
| Outstanding | PKR 180,000 | PKR 210,000 | -14.3% |

### Revenue by Source
| Client/Project | Amount | % of Total |
|----------------|--------|------------|
| Client A | PKR 200,000 | 44.4% |
| Client B | PKR 150,000 | 33.3% |
| Product Sales | PKR 100,000 | 22.3% |

### Payment Trends
- **Average Payment Time**: 18 days (target: 15 days) ⚠️
- **On-Time Payment Rate**: 78% (target: 90%) ⚠️
- **Overdue Invoices**: 3 (total: PKR 85,000)

---

## Expense Analysis

### Weekly Expenses
| Category | Amount | Budget | Variance |
|----------|--------|--------|----------|
| Salaries | PKR 250,000 | PKR 250,000 | On Budget |
| Software | PKR 45,000 | PKR 40,000 | +12.5% ⚠️ |
| Marketing | PKR 60,000 | PKR 50,000 | +20.0% ⚠️ |
| Office | PKR 35,000 | PKR 35,000 | On Budget |
| **Total** | **PKR 390,000** | **PKR 375,000** | **+4.0%** |

### Unusual Expenses Flagged
1. **Adobe Creative Cloud**: PKR 15,000 (no team activity in 45 days)
   - Recommendation: Cancel subscription
2. **LinkedIn Premium**: PKR 12,000 (cost increased 20%)
   - Recommendation: Review necessity

---

## Social Media Performance

### Platform Overview
| Platform | Posts | Engagement | Reach | Followers |
|----------|-------|------------|-------|-----------|
| Facebook | 5 | 234 | 12,500 | 3,450 |
| Instagram | 7 | 567 | 18,200 | 5,230 |
| Twitter | 12 | 189 | 8,500 | 2,100 |
| LinkedIn | 3 | 145 | 6,800 | 1,890 |

### Top Performing Content
1. **Instagram**: "Behind the scenes" post - 234 engagements
2. **Facebook**: Product announcement - 189 engagements
3. **Twitter**: Industry insight thread - 145 engagements

### Lead Generation
- **Total Leads**: 23 (up from 18 last week)
- **Qualified Leads**: 12
- **Converted**: 3 (PKR 150,000 value)

---

## Task Completion

### Weekly Tasks
| Status | Count | % |
|--------|-------|---|
| Completed | 45 | 90% |
| In Progress | 3 | 6% |
| Pending | 2 | 4% |

### Bottlenecks Identified
| Task | Expected | Actual | Delay | Reason |
|------|----------|--------|-------|--------|
| Client B Proposal | 2 days | 5 days | +3 days | Waiting for requirements |
| Payment Follow-up | 1 day | 3 days | +2 days | Client unresponsive |

---

## Proactive Suggestions

### Cost Optimization
1. **Cancel Adobe Creative Cloud**: PKR 15,000/month savings
   - No team activity in 45 days
   - [ACTION] Move to Pending_Approval for cancellation

2. **Renegotiate LinkedIn Premium**: PKR 12,000/month
   - Cost increased 20% without additional value
   - [ACTION] Contact sales for better rate

### Revenue Improvement
1. **Follow up on overdue invoices**: PKR 85,000 outstanding
   - 3 invoices overdue by > 30 days
   - [ACTION] Send payment reminder emails

2. **Upsell to Client A**: Potential PKR 100,000
   - Client A showed interest in additional services
   - [ACTION] Schedule consultation call

### Process Automation
1. **Automate payment reminders**: Save 2 hours/week
   - Currently manual follow-up on overdue invoices
   - [ACTION] Create automated reminder workflow

---

## Critical Alerts
🔴 **High Priority**:
- 3 invoices overdue by > 30 days (PKR 85,000)
- Software costs 12.5% over budget

🟡 **Medium Priority**:
- Client B proposal delayed by 3 days
- LinkedIn Premium cost increase

🟢 **Low Priority**:
- Team requesting new project management tool

---

## Next Week Priorities
1. Collect overdue payments (PKR 85,000 target)
2. Submit Client B proposal
3. Review and cancel unused subscriptions
4. Launch new Instagram campaign

---

*Generated autonomously by AI Employee on 2026-03-11 at 7:00 AM*
```

### 6. Audit Log Entry Structure
Location: `Audit_Logs/YYYY-MM-DD.jsonl`

```json
{
  "timestamp": "2026-03-12T10:30:00Z",
  "action_type": "odoo.create_invoice",
  "actor": "ai_employee",
  "actor_type": "agent",
  "agent_name": "OdooAgent",
  "domain": "business",
  "subdomain": "accounting",
  "parameters": {
    "customer_id": 123,
    "customer_name": "ABC Corporation",
    "items": [
      {"name": "Service 1", "quantity": 1, "price": 3000},
      {"name": "Service 2", "quantity": 2, "price": 1000}
    ],
    "due_date": "2026-03-26"
  },
  "approval_status": "approved",
  "approval_type": "auto",
  "approved_by": null,
  "approved_at": null,
  "approval_file": null,
  "result": "success",
  "result_data": {
    "invoice_id": "INV/2026/00123",
    "amount": 5000,
    "state": "draft"
  },
  "error_message": "",
  "error_code": null,
  "execution_time_ms": 1250,
  "retry_count": 0,
  "fallback_used": false,
  "session_id": "session_abc123",
  "correlation_id": "corr_xyz789",
  "previous_hash": "sha256_of_previous_entry",
  "current_hash": "sha256_of_current_entry"
}
```

### 7. Task State File Structure (Ralph Wiggum)
Location: `Plans/TASK_STATE_<task_id>.md`

```yaml
---
type: task_state
task_id: "task_20260312_103000_001"
created: "2026-03-12T10:30:00Z"
updated: "2026-03-12T10:45:00Z"
status: "in_progress"  # pending, in_progress, completed, failed, cancelled
progress: 60            # percentage (0-100)
current_step: 3
total_steps: 5
max_iterations: 10
current_iteration: 2
domain: "business"
priority: "high"
---

# Task State: Process Overdue Invoices

## Task Description
Process all overdue invoices and send payment reminders

## Current Status
- **Progress**: 60%
- **Current Step**: Sending reminder emails
- **Iteration**: 2 of 10
- **Status**: In Progress

## Steps
| # | Step | Status | Started | Completed | Notes |
|---|------|--------|---------|-----------|-------|
| 1 | Fetch overdue invoices from Odoo | ✅ Completed | 10:30:00 | 10:32:00 | Found 3 invoices |
| 2 | Generate reminder email templates | ✅ Completed | 10:32:00 | 10:35:00 | 3 templates created |
| 3 | Send reminder emails | 🔄 In Progress | 10:35:00 | - | 2 of 3 sent |
| 4 | Log actions to audit trail | ⏳ Pending | - | - | - |
| 5 | Update invoice status in Odoo | ⏳ Pending | - | - | - |

## Failed Steps
None

## Recovery Point
Step 2 completed successfully - can resume from Step 3

## Last Error
None

## Next Action
Continue with Step 3: Send remaining reminder email

## Metadata
- **Agent**: OdooAgent
- **Session**: session_abc123
- **Correlation ID**: corr_xyz789
```

### 8. Cross-Domain Task Structure
Location: `Needs_Action/Cross_Domain/`

```yaml
---
type: cross_domain_task
task_id: "cross_20260312_103000_001"
created: "2026-03-12T10:30:00Z"
priority: "high"
status: "pending"
domains_involved: ["business", "personal"]
primary_domain: "business"
related_tasks: ["task_001", "task_002"]
---

# Cross-Domain Task: Client Payment & Personal Banking

## Task Description
Client payment received in business account needs to be recorded in accounting and personal finance tracking

## Domains Involved
1. **Business** (Primary)
   - Record payment in Odoo
   - Mark invoice as paid
   - Generate receipt

2. **Personal** (Secondary)
   - Update personal finance tracker
   - Categorize as business income
   - Calculate tax provision

## Related Tasks
- Task 001: Send invoice (completed)
- Task 002: Track payment (in progress)

## Coordination Required
- Business domain must complete first
- Personal domain depends on business completion
- Both domains must log to same correlation ID

## Suggested Actions
- [ ] Process business domain tasks
- [ ] Wait for business completion
- [ ] Process personal domain tasks
- [ ] Verify cross-domain consistency
```

### 9. Social Media Analytics Structure
Location: `Reports/Social_Analytics_YYYY-MM.md`

```yaml
---
type: social_analytics
period: monthly
period_start: "2026-03-01"
period_end: "2026-03-31"
generated: "2026-03-31T23:59:00Z"
domain: "business"
---

# Social Media Analytics: March 2026

## Platform Summary

### Facebook
| Metric | Value | Change vs Last Month |
|--------|-------|---------------------|
| Posts | 22 | +10% |
| Total Engagement | 1,234 | +25% |
| Reach | 45,000 | +15% |
| Page Likes | 3,450 | +120 |
| Click-Through Rate | 2.3% | +0.5% |

### Instagram
| Metric | Value | Change vs Last Month |
|--------|-------|---------------------|
| Posts | 28 | +15% |
| Total Engagement | 2,567 | +35% |
| Reach | 68,000 | +28% |
| Followers | 5,230 | +340 |
| Engagement Rate | 4.9% | +0.8% |

### Twitter
| Metric | Value | Change vs Last Month |
|--------|-------|---------------------|
| Tweets | 45 | +20% |
| Total Engagement | 890 | +18% |
| Impressions | 32,000 | +22% |
| Followers | 2,100 | +85 |
| Engagement Rate | 2.8% | +0.3% |

### LinkedIn
| Metric | Value | Change vs Last Month |
|--------|-------|---------------------|
| Posts | 12 | +5% |
| Total Engagement | 567 | +12% |
| Reach | 25,000 | +10% |
| Connections | 1,890 | +45 |
| Engagement Rate | 2.3% | +0.2% |

## Content Performance

### Top Posts by Engagement
1. **Instagram** - "Behind the scenes" (234 engagements)
2. **Facebook** - Product announcement (189 engagements)
3. **Twitter** - Industry thread (145 engagements)
4. **LinkedIn** - Company milestone (123 engagements)

### Best Posting Times
- **Facebook**: Tuesday-Thursday, 10 AM - 12 PM
- **Instagram**: Daily, 7 PM - 9 PM
- **Twitter**: Weekdays, 12 PM - 2 PM
- **LinkedIn**: Tuesday-Thursday, 8 AM - 10 AM

## Lead Generation
| Platform | Leads | Qualified | Converted | Revenue |
|----------|-------|-----------|-----------|---------|
| Facebook | 45 | 23 | 8 | PKR 200,000 |
| Instagram | 67 | 34 | 12 | PKR 300,000 |
| Twitter | 23 | 12 | 4 | PKR 100,000 |
| LinkedIn | 34 | 18 | 6 | PKR 150,000 |
| **Total** | **169** | **87** | **30** | **PKR 750,000** |

## Recommendations
1. Increase Instagram posting frequency (highest ROI)
2. Optimize Twitter posting time for better engagement
3. Create more video content (2x engagement rate)
4. Invest in Facebook ads for lead generation
```

### 10. Odoo Data Structures

### Invoice Structure (from Odoo)
```json
{
  "id": 12345,
  "name": "INV/2026/00123",
  "partner_id": {
    "id": 67,
    "name": "ABC Corporation"
  },
  "invoice_date": "2026-03-12",
  "due_date": "2026-03-26",
  "state": "draft",  // draft, posted, paid, cancelled
  "amount_total": 5000.00,
  "amount_residual": 5000.00,  // amount due
  "currency_id": {
    "id": 1,
    "name": "PKR"
  },
  "invoice_line_ids": [
    {
      "product_id": {"id": 1, "name": "Service 1"},
      "quantity": 1,
      "price_unit": 3000.00,
      "price_subtotal": 3000.00
    },
    {
      "product_id": {"id": 2, "name": "Service 2"},
      "quantity": 2,
      "price_unit": 1000.00,
      "price_subtotal": 2000.00
    }
  ]
}
```

### Payment Structure (from Odoo)
```json
{
  "id": 8901,
  "name": "PMT/2026/00456",
  "payment_date": "2026-03-15",
  "amount": 5000.00,
  "payment_type": "inbound",  // inbound (customer), outbound (vendor)
  "partner_id": {
    "id": 67,
    "name": "ABC Corporation"
  },
  "state": "posted",  // draft, posted, cancelled
  "reconciled_invoice_ids": [12345]
}
```

### Expense Structure (from Odoo)
```json
{
  "id": 2345,
  "name": "Office Supplies",
  "date": "2026-03-10",
  "total_amount": 3500.00,
  "currency_id": {
    "id": 1,
    "name": "PKR"
  },
  "employee_id": {
    "id": 12,
    "name": "John Doe"
  },
  "product_id": {
    "id": 45,
    "name": "Office Expenses"
  },
  "state": "approved",  // draft, reported, approved, done, cancelled
  "description": "Monthly office supplies purchase"
}
```

## Configuration Data Model

### 11. Gold Tier System Configuration
```yaml
# Gold Tier specific configuration
ODOO_CONFIG:
  url: "http://localhost:8069"
  database: "production"
  username: "admin"
  api_key: "encrypted_api_key"

FACEBOOK_CONFIG:
  app_id: "facebook_app_id"
  app_secret: "encrypted_app_secret"
  access_token: "encrypted_access_token"
  page_id: "facebook_page_id"

INSTAGRAM_CONFIG:
  user_id: "instagram_user_id"
  access_token: "encrypted_access_token"

TWITTER_CONFIG:
  api_key: "encrypted_api_key"
  api_secret: "encrypted_api_secret"
  access_token: "encrypted_access_token"
  access_token_secret: "encrypted_access_token_secret"

SOCIAL_MEDIA_SETTINGS:
  post_approval_threshold: 1000  # posts reaching > 1000 people need approval
  auto_respond_enabled: true
  cross_post_enabled: true
  default_platforms: ["facebook", "instagram", "twitter", "linkedin"]

ACCOUNTING_SETTINGS:
  invoice_approval_threshold: 500  # invoices >= 500 need approval
  payment_approval_threshold: 1000  # payments >= 1000 need approval
  expense_flag_threshold: 2000  # flag expenses >= 2000
  overdue_days_threshold: 30  # flag invoices overdue > 30 days

AUDIT_LOGGING:
  enabled: true
  retention_days: 90
  format: "jsonl"
  hash_chain: true
  export_formats: ["json", "csv", "pdf"]

RALPH_WIGGUM_SETTINGS:
  max_iterations: 10
  progress_tracking: true
  recovery_point_enabled: true
  state_file_directory: "Plans/"

ERROR_RECOVERY:
  max_retries: 5
  base_delay: 1  # seconds
  max_delay: 60  # seconds
  exponential_backoff: true
  jitter_enabled: true
  circuit_breaker_threshold: 5
  circuit_breaker_timeout: 300  # seconds

CEO_BRIEFING:
  schedule: "0 7 * * 1"  # Every Monday at 7 AM
  include_revenue: true
  include_expenses: true
  include_social_media: true
  include_tasks: true
  include_suggestions: true
  include_alerts: true
```

## File Naming Conventions

### 12. Generated File Names
- **Accounting Action Files**: `ACCOUNTING_yyyymmdd_hhmmss_type.md`
- **Facebook Action Files**: `FACEBOOK_yyyymmdd_hhmmss_type.md`
- **Instagram Action Files**: `INSTAGRAM_yyyymmdd_hhmmss_type.md`
- **Twitter Action Files**: `TWITTER_yyyymmdd_hhmmss_type.md`
- **CEO Briefings**: `YYYY-MM-DD_Day_Briefing.md`
- **Audit Logs**: `Audit_Logs/YYYY-MM-DD.jsonl`
- **Task State Files**: `TASK_STATE_taskid.md`
- **Cross-Domain Tasks**: `CROSS_DOMAIN_yyyymmdd_hhmmss.md`
- **Social Analytics**: `Social_Analytics_YYYY-MM.md`
- **Financial Reports**: `Financial_Report_YYYY-MM.md`

These data models provide the structure for all Gold Tier functionality while maintaining compatibility with Silver Tier foundations.
