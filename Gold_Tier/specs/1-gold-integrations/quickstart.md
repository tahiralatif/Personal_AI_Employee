# Gold Tier Quick Start Guide

## Prerequisites

Before starting, ensure you have:
- ✅ Silver Tier completed and working
- ✅ Python 3.13 or higher
- ✅ Node.js v24+ LTS
- ✅ Odoo 19+ instance (local or test)
- ✅ Facebook Developer Account
- ✅ Instagram Business Account
- ✅ Twitter Developer Account
- ✅ Claude Code subscription

---

## Step 1: Clone and Setup

```bash
# Navigate to Gold Tier
cd Gold_Tier

# Create virtual environment
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
uv sync

# Copy environment file
copy .env.example .env
```

---

## Step 2: Configure Environment Variables

Edit `.env` file with your credentials:

```bash
# ========================================
# GOLD TIER CONFIGURATION
# ========================================

# Vault Path (from Silver Tier)
VAULT_PATH=D:\Documents\...\AI_Employee_Vault

# Gemini API (from Silver Tier)
GEMINI_API_KEY=your_gemini_api_key
GEMINI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
GEMINI_MODEL=gemini-2.0-flash

# ========================================
# ODOO CONFIGURATION
# ========================================
ODOO_URL=http://localhost:8069
ODOO_DATABASE=production
ODOO_USERNAME=admin
ODOO_API_KEY=your_odoo_api_key

# ========================================
# FACEBOOK CONFIGURATION
# ========================================
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_ACCESS_TOKEN=your_access_token
FACEBOOK_PAGE_ID=your_page_id

# ========================================
# INSTAGRAM CONFIGURATION
# ========================================
INSTAGRAM_USER_ID=your_user_id
INSTAGRAM_ACCESS_TOKEN=your_access_token

# ========================================
# TWITTER CONFIGURATION
# ========================================
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret

# ========================================
# GOLD TIER SETTINGS
# ========================================
ACCOUNTING_APPROVAL_THRESHOLD=500
SOCIAL_POST_APPROVAL_THRESHOLD=1000
AUDIT_LOGGING_ENABLED=true
RALPH_WIGGUM_ENABLED=true
MAX_RETRIES=5
CIRCUIT_BREAKER_THRESHOLD=5
```

---

## Step 3: Set Up Odoo (Local Instance)

### Option A: Docker (Recommended)
```bash
# Pull Odoo 19 image
docker pull odoo:19

# Run Odoo container
docker run -d \
  --name odoo \
  -p 8069:8069 \
  -e ODOO_DATABASE=postgres \
  -e ODOO_DB_USER=odoo \
  -e ODOO_DB_PASSWORD=odoo \
  -v odoo-data:/var/lib/odoo \
  odoo:19
```

### Option B: Use Odoo Online (Test)
- Visit: https://www.odoo.com/trial
- Create free test instance
- Get API credentials from Settings → Users & Companies

### Configure Odoo
1. Login to Odoo as admin
2. Go to Settings → Users & Companies
3. Create API user with accounting permissions
4. Generate API key in user preferences

---

## Step 4: Set Up Facebook Developer App

1. Visit: https://developers.facebook.com/
2. Click "My Apps" → "Create App"
3. Select "Business" app type
4. Fill in app details
5. Add "Facebook Login" product
6. Configure OAuth redirect URI
7. Get App ID and App Secret from Dashboard

### Get Page Access Token
1. Go to Graph API Explorer: https://developers.facebook.com/tools/explorer/
2. Select your app
3. Click "Get Token" → "Get Page Access Token"
4. Select your page
5. Copy access token

### Extend Token (60 days)
1. Go to Access Token Tool
2. Select your app
3. Click "Extend Access Token"
4. Copy new token to `.env`

---

## Step 5: Set Up Instagram Business Account

1. Convert to Business Account:
   - Instagram Settings → Account → Switch to Professional Account
   - Select "Business" category

2. Connect to Facebook Page:
   - Instagram Settings → Account → Linked Accounts → Facebook
   - Select your business page

3. Get Instagram User ID:
   - Use Graph API Explorer
   - Query: `GET /me?fields=instagram_business_account`
   - Copy `id` field

---

## Step 6: Set Up Twitter Developer Account

1. Visit: https://developer.twitter.com/
2. Apply for developer account
3. Create new project and app
4. Get API Key and Secret
5. Generate Access Token and Secret
6. Set app permissions to "Read and Write"

---

## Step 7: Verify Setup

```bash
# Test Odoo connection
python -m src.ai_employee_gold.main test-odoo

# Test Facebook connection
python -m src.ai_employee_gold.main test-facebook

# Test Instagram connection
python -m src.ai_employee_gold.main test-instagram

# Test Twitter connection
python -m src.ai_employee_gold.main test-twitter

# Run all tests
python -m src.ai_employee_gold.main test-all
```

---

## Step 8: Start Gold Tier

### Autonomous Mode (Recommended)
```bash
# Start all agents autonomously
python -m src.ai_employee_gold.autonomous_run
```

### Interactive Mode
```bash
# Odoo agent
python -m src.ai_employee_gold.main odoo

# Social media agents
python -m src.ai_employee_gold.main facebook
python -m src.ai_employee_gold.main instagram
python -m src.ai_employee_gold.main twitter

# Unified social agent
python -m src.ai_employee_gold.main social

# Financial review agent
python -m src.ai_employee_gold.main financial-review

# Audit agent
python -m src.ai_employee_gold.main audit

# Help
python -m src.ai_employee_gold.main help
```

---

## Step 9: Test Gold Tier Features

### Test Odoo Integration
```python
# Create test invoice
python -c "from src.ai_employee_gold.main import create_test_invoice; create_test_invoice()"

# Check outstanding invoices
python -m src.ai_employee_gold.main odoo --command "outstanding"
```

### Test Social Media Posting
```python
# Test Facebook post
python -m src.ai_employee_gold.main facebook --command "post" --content "Test post from Gold Tier!"

# Test Instagram post
python -m src.ai_employee_gold.main instagram --command "post" --image "test.jpg" --caption "Test caption"

# Test Twitter tweet
python -m src.ai_employee_gold.main twitter --command "tweet" --content "Test tweet from Gold Tier!"
```

### Test CEO Briefing
```bash
# Generate test briefing
python -m src.ai_employee_gold.main generate-briefing --period week
```

---

## Step 10: Monitor and Maintain

### Check System Health
```bash
# View system status
python -m src.ai_employee_gold.main status

# View audit logs
python -m src.ai_employee_gold.main audit-log --today

# View agent health
python -m src.ai_employee_gold.main health
```

### View Logs
```bash
# Real-time logs
tail -f AI_Employee_Vault/Logs/gold_tier.log

# Audit logs
tail -f AI_Employee_Vault/Audit_Logs/*.jsonl
```

### Backup Data
```bash
# Backup vault
robocopy AI_Employee_Vault AI_Employee_Vault_Backup /MIR

# Backup audit logs
robocopy AI_Employee_Vault\Audit_Logs D:\Backups\Audit_Logs /MIR
```

---

## Common Commands Reference

### Odoo Commands
```bash
# Create invoice
python -m src.ai_employee_gold.main odoo --command "create-invoice" --customer "ABC Corp" --amount 5000

# Record payment
python -m src.ai_employee_gold.main odoo --command "record-payment" --invoice "INV/2026/00123" --amount 5000

# Get financial summary
python -m src.ai_employee_gold.main odoo --command "financial-summary" --period "month"
```

### Social Media Commands
```bash
# Post to all platforms
python -m src.ai_employee_gold.main social --command "post-all" --content "New product launch!"

# Get analytics
python -m src.ai_employee_gold.main social --command "analytics" --period "week"

# Schedule post
python -m src.ai_employee_gold.main social --command "schedule" --platform "facebook" --time "2026-03-15T10:00:00" --content "Scheduled post"
```

### Audit Commands
```bash
# Export audit log
python -m src.ai_employee_gold.main audit --command "export" --format "csv" --output "audit_report.csv"

# Check compliance
python -m src.ai_employee_gold.main audit --command "compliance-check"
```

---

## Troubleshooting

### Odoo Connection Issues
```bash
# Check Odoo service
docker ps | grep odoo

# Test Odoo connection
python -c "from src.ai_employee_gold.integrations.odoo_integration import OdooIntegration; o = OdooIntegration(); o.connect()"
```

### Social Media API Issues
```bash
# Check token validity
python -m src.ai_employee_gold.main facebook --command "check-token"
python -m src.ai_employee_gold.main instagram --command "check-token"
python -m src.ai_employee_gold.main twitter --command "check-token"

# Refresh tokens
python -m src.ai_employee_gold.main refresh-tokens
```

### Audit Log Issues
```bash
# Verify hash chain
python -m src.ai_employee_gold.main audit --command "verify-chain" --date "2026-03-12"

# Repair corrupted log
python -m src.ai_employee_gold.main audit --command "repair" --date "2026-03-12"
```

---

## Next Steps

1. **Configure Approval Workflows**
   - Set approval thresholds in `.env`
   - Test approval flow with test transactions

2. **Schedule CEO Briefings**
   - Configure schedule in `task_scheduler.py`
   - Test briefing generation

3. **Enable Ralph Wiggum Loop**
   - Configure in `.env`
   - Test with multi-step task

4. **Set Up Monitoring**
   - Configure health checks
   - Set up alerts for critical failures

5. **Deploy to Production**
   - Review security checklist
   - Backup all data
   - Enable audit logging
   - Monitor for 1 week

---

## Support

### Documentation
- Full specs: `specs/1-gold-integrations/spec.md`
- Implementation plan: `specs/1-gold-integrations/plan.md`
- Tasks: `specs/1-gold-integrations/tasks.md`
- Data models: `specs/1-gold-integrations/data-model.md`
- Research: `specs/1-gold-integrations/research.md`

### Getting Help
- Check logs: `AI_Employee_Vault/Logs/gold_tier.log`
- Review audit trail: `AI_Employee_Vault/Audit_Logs/`
- Read troubleshooting: `docs/troubleshooting.md`

---

**Gold Tier Status**: Ready for autonomous operation! 🚀
