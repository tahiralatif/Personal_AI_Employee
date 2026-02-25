# Silver Tier Quick Start Guide

Get your Silver Tier AI Employee up and running in 5 minutes!

**Prerequisites**: Bronze Tier must be installed and working.

---

## ⏱️ Time Estimate

| Step | Time | Total |
|------|------|-------|
| Prerequisites check | 1 min | 1 min |
| Install Silver Tier | 2 min | 3 min |
| Configure one integration | 2 min | 5 min |

**Total**: 5 minutes for basic setup (one integration)

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Bronze Tier installed and working** (file watcher functional)
- [ ] **Python 3.12+** installed
- [ ] **uv package manager** installed
- [ ] **Git** installed
- [ ] **Internet connection** (for API setup)
- [ ] **At least one API account** (Gmail, WhatsApp Business, or LinkedIn)

### Verify Bronze Tier is Working

```powershell
# Navigate to Bronze Tier
cd "D:\Documents\Tahira's-work\New folder\projects\New folder\Personal_AI_Employee\AI_Employee_Bronze"

# Check vault exists
dir "AI_Employee_Vault\"

# Should show: Inbox/, Needs_Action/, Done/, Plans/, Logs/, Dashboard.md, Company_Handbook.md
```

**If Bronze Tier is not working, stop here and complete Bronze Tier setup first!**

---

## Step 1: Install Silver Tier (2 minutes)

### 1.1 Create Silver Tier Folder

```powershell
# Navigate to project root
cd "D:\Documents\Tahira's-work\New folder\projects\New folder\Personal_AI_Employee"

# Create Silver Tier folder
mkdir AI_Employee_Silver
cd AI_Employee_Silver
```

### 1.2 Initialize Project

```powershell
# Initialize uv project
uv init --name ai-employee-silver

# Add Silver Tier dependencies
uv add google-api-python-client APScheduler filelock python-dotenv

# Create folder structure
mkdir src\ai_employee_silver
mkdir tests\unit
mkdir tests\integration
mkdir .silver\data
```

### 1.3 Create Basic Files

```powershell
# Create __init__.py files
New-Item src\ai_employee_silver\__init__.py
New-Item tests\__init__.py
New-Item tests\unit\__init__.py
New-Item tests\integration\__init__.py

# Create .env.example
New-Item .env.example
```

### 1.4 Verify Installation

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Check dependencies installed
uv pip list

# Should show: google-api-client, APScheduler, filelock, python-dotenv
```

---

## Step 2: Configure Your First Integration (2 minutes)

Choose **ONE** integration to start with (recommended: Gmail).

---

### Option A: Gmail Integration (Recommended)

#### 2A.1: Get Gmail API Credentials (5 minutes - one-time)

1. **Go to Google Cloud Console**: https://console.cloud.google.com/

2. **Create new project**:
   - Click "Select Project" → "New Project"
   - Name: "AI Employee Silver"
   - Click "Create"

3. **Enable Gmail API**:
   - Go to "APIs & Services" → "Library"
   - Search: "Gmail API"
   - Click "Enable"

4. **Create OAuth credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Desktop app"
   - Name: "AI Employee"
   - Click "Create"

5. **Download credentials**:
   - Click "Download" to get `credentials.json`
   - Save to: `AI_Employee_Silver/.silver/credentials/gmail_credentials.json`

#### 2A.2: Configure .env File

```powershell
# Create .env file from example
Copy-Item .env.example .env

# Edit .env file
notepad .env
```

**Add this to `.env`:**

```bash
# =============================================================================
# SILVER TIER CONFIGURATION
# =============================================================================

# Gmail API Configuration
GMAIL_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret_here
GMAIL_REDIRECT_URI=http://localhost:8080

# Bronze Tier Vault Path (SHARED with Bronze)
VAULT_PATH=D:\Documents\Tahira's-work\New folder\projects\New folder\Personal_AI_Employee\AI_Employee_Bronze\AI_Employee_Vault

# Log Level
LOG_LEVEL=INFO
```

**Replace `your_client_id_here` and `your_client_secret_here` with actual values from `gmail_credentials.json`**

#### 2A.3: First-Time Authentication

```powershell
# Run authentication script
uv run python -m src.ai_employee_silver.auth.gmail_auth

# Browser will open - sign in with your Gmail account
# Grant permissions
# Token will be saved automatically
```

#### 2A.4: Test Gmail Integration

```powershell
# Start Silver Tier watcher
uv run python -m src.ai_employee_silver.main watch

# In another terminal, send yourself a test email with attachment
# Wait 60 seconds
# Check Bronze Tier's Inbox/ folder
dir "D:\...\AI_Employee_Bronze\AI_Employee_Vault\Inbox\"
```

**Expected**: Email attachment should appear in Inbox/ within 60 seconds!

---

### Option B: WhatsApp Business Integration

#### 2B.1: Get WhatsApp Business API Access

1. **Go to Meta Business Suite**: https://business.facebook.com/

2. **Create WhatsApp Business Account**:
   - Click "WhatsApp" → "Get Started"
   - Follow business verification process
   - This can take 1-3 days for approval

3. **Get API credentials**:
   - Go to "Business Settings" → "System Users"
   - Create system user with WhatsApp permissions
   - Generate access token

#### 2B.2: Configure .env File

```bash
# WhatsApp Business API Configuration
WHATSAPP_BUSINESS_PHONE_ID=your_phone_id_here
WHATSAPP_BUSINESS_ACCESS_TOKEN=your_access_token_here
WHATSAPP_BUSINESS_API_VERSION=v18.0
```

#### 2B.3: Test WhatsApp Integration

```powershell
# Send a WhatsApp message to your business number
# Wait 30 seconds
# Check Needs_Action/ folder
```

---

### Option C: LinkedIn Integration

#### 2C.1: Get LinkedIn API Credentials

1. **Go to LinkedIn Developer**: https://www.linkedin.com/developers/

2. **Create new app**:
   - Click "Create app"
   - Select your LinkedIn page
   - Fill in app details

3. **Enable APIs**:
   - Go to "Auth" tab
   - Note down Client ID and Client Secret
   - Add redirect URI: `http://localhost:8080`

#### 2C.2: Configure .env File

```bash
# LinkedIn API Configuration
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_REDIRECT_URI=http://localhost:8080
```

#### 2C.3: Test LinkedIn Integration

```powershell
# Create a test post in Plans/ folder
# Run Silver Tier watcher
# Wait for scheduled time
# Check LinkedIn for published post
```

---

## Step 3: Verify Everything Works (1 minute)

### Check Silver Tier Status

```powershell
# Start Silver Tier
uv run python -m src.ai_employee_silver.main status

# Expected output:
# Silver Tier Status
# ─────────────────────────
# Gmail:        ✅ Connected
# WhatsApp:     ⏸️  Not configured
# LinkedIn:     ⏸️  Not configured
# Scheduler:    ✅ Running
# Vault Path:   D:\...\AI_Employee_Vault
```

### Check Bronze Tier Integration

```powershell
# Check Dashboard.md
notepad "D:\...\AI_Employee_Vault\Dashboard.md"

# Should show Silver Tier stats:
# - Email attachments processed: X
# - WhatsApp messages processed: Y
# - LinkedIn posts published: Z
```

### Check Logs

```powershell
# Check today's log
notepad "D:\...\AI_Employee_Vault\Logs\2026-02-25.log"

# Should show Silver Tier entries:
# - Gmail: Fetched 5 emails
# - Attachment saved: invoice.pdf
# - Action file created: FILE_*_invoice.pdf.md
```

---

## 🎯 Quick Test Scenarios

### Test 1: Email Attachment → Task

```
1. Send email with attachment to your Gmail
2. Wait 60 seconds
3. Check: AI_Employee_Vault\Inbox\
4. Verify: Attachment saved
5. Check: AI_Employee_Vault\Needs_Action\
6. Verify: Action file created
```

### Test 2: WhatsApp Message → Task

```
1. Send WhatsApp message: "Please prepare monthly report"
2. Wait 30 seconds
3. Check: AI_Employee_Vault\Needs_Action\
4. Verify: Task file created with message content
```

### Test 3: Scheduled Task

```
1. Create schedule in .silver/config/schedules.json
2. Wait for scheduled time
3. Check: AI_Employee_Vault\Needs_Action\
4. Verify: Task file created automatically
```

---

## 🐛 Troubleshooting

### Problem: Gmail authentication fails

**Solution:**
```powershell
# Delete old token
Remove-Item .silver\tokens\gmail_token.json

# Re-run authentication
uv run python -m src.ai_employee_silver.auth.gmail_auth
```

### Problem: Attachments not appearing in Inbox/

**Solution:**
```powershell
# Check Silver Tier logs
notepad .silver\logs\silver.log

# Check Gmail API quota
# Visit: https://console.cloud.google.com/apis/api/gmail.googleapis.com/quotas

# If quota exceeded, wait for reset or request increase
```

### Problem: WhatsApp messages not processed

**Solution:**
```powershell
# Verify webhook is configured correctly
# Visit: https://developers.facebook.com/apps/{your-app-id}/webhooks/

# Test webhook: Send message with keyword "test"
# Check logs for webhook receipt
```

### Problem: LinkedIn post not published

**Solution:**
```powershell
# Check post status in .silver\data\linkedin\
# If status = "pending_approval", approve manually:
notepad Plans\LINKEDIN_POST_*.md
# Change status from "pending" to "approved"
```

### Problem: Silver Tier slows down Bronze Tier

**Solution:**
```powershell
# Reduce polling frequency in .silver\config\settings.json
# Change:
#   "gmail_poll_interval_seconds": 60  → 120
#   "whatsapp_poll_interval_seconds": 30  → 60
```

---

## 📚 Next Steps

### After Basic Setup:

1. **Configure all integrations** (Gmail + WhatsApp + LinkedIn)
2. **Set up scheduled tasks** (daily reports, weekly reviews)
3. **Customize task detection** (add your own keywords)
4. **Set up MCP servers** (multi-agent coordination)

### Documentation:

- **Full Setup Guide**: See `README.md` for detailed configuration
- **API Setup**: See `docs/API_SETUP.md` for step-by-step API credentials
- **Troubleshooting**: See `docs/TROUBLESHOOTING.md` for common issues
- **Task Reference**: See `specs/2-silver-integrations/tasks.md` for all features

---

## 🚀 Quick Command Reference

| Command | Purpose |
|---------|---------|
| `uv run python -m src.ai_employee_silver.main watch` | Start Silver Tier watcher |
| `uv run python -m src.ai_employee_silver.main status` | Check integration status |
| `uv run python -m src.ai_employee_silver.auth.gmail_auth` | Gmail authentication |
| `uv run python -m src.ai_employee_silver.auth.linkedin_auth` | LinkedIn authentication |
| `uv run python -m src.ai_employee_silver.scheduler test` | Test scheduler |

---

## ✅ Success Criteria

You know Silver Tier is working when:

- ✅ Status shows at least one integration as "Connected"
- ✅ Email attachments appear in Inbox/ within 60 seconds
- ✅ WhatsApp messages create tasks in Needs_Action/ within 30 seconds
- ✅ Scheduled tasks are created at the right time
- ✅ Dashboard.md shows Silver Tier statistics
- ✅ Logs show successful API operations

---

**Congratulations! Silver Tier is ready!** 🎉

**Next**: Configure remaining integrations and customize for your workflow!

---

**Version**: 1.0  
**Created**: 2026-02-25  
**Based on**: Bronze Tier v1.0 + Silver Tier v1.0
