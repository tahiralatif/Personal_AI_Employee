# 🏆 Platinum Tier: Always-On Cloud + Local Executive

**Tagline**: *Production-ready AI Employee with Cloud-Local architecture*

---

## 🎯 **Platinum Tier Objectives**

Build upon Gold Tier by adding:

1. **Cloud 24/7 Deployment** - Always-on watchers + orchestrator
2. **Work-Zone Specialization** - Cloud/Local domain ownership
3. **Vault Sync** - Git/Syncthing for synchronization
4. **Security Boundaries** - Secrets never sync
5. **Odoo on Cloud VM** - Self-hosted with HTTPS
6. **A2A Communication** - Agent-to-Agent messaging

---

## 🏗️ **Architecture**

```
┌─────────────────────────────────────────────────────────────┐
│                    CLOUD VM (Oracle/AWS)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Cloud Agents (Draft-Only)                           │  │
│  │  - Email Triage                                      │  │
│  │  - Draft Replies                                     │  │
│  │  - Social Post Drafts                                │  │
│  │  - Social Scheduling                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                          │ Vault Sync (Git/Syncthing)       │
│                          │ /Updates/, /Signals/              │
└──────────────────────────┼───────────────────────────────────┘
                           │
┌──────────────────────────┼───────────────────────────────────┐
│                    LOCAL MACHINE                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Local Agents (Approval + Execution)                 │  │
│  │  - Approvals                                         │  │
│  │  - WhatsApp Session                                  │  │
│  │  - Payments/Banking                                  │  │
│  │  - Final Send/Post Actions                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                          │                                   │
│                    Obsidian Vault                            │
│                    /Approved/, /Done/                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 **Platinum Tier Requirements**

### **Phase 1: Cloud Deployment**
- [ ] Deploy Cloud Agent on Oracle/AWS VM
- [ ] Setup always-on watchers
- [ ] Health monitoring
- [ ] Auto-restart on failure

### **Phase 2: Work-Zone Specialization**
- [ ] Cloud owns: Email triage, draft replies, social drafts
- [ ] Local owns: Approvals, WhatsApp, payments, banking
- [ ] Draft-only mode for Cloud
- [ ] Approval workflow for Local

### **Phase 3: Vault Sync**
- [ ] Git-based vault sync (recommended)
- [ ] OR Syncthing setup
- [ ] /Updates/ folder for Cloud→Local
- [ ] /Signals/ folder for Local→Cloud
- [ ] Claim-by-move rule for /In_Progress/

### **Phase 4: Security**
- [ ] Secrets never sync (.env, tokens, sessions)
- [ ] Cloud never stores banking credentials
- [ ] Cloud never stores WhatsApp sessions
- [ ] Encrypted sync for sensitive data

### **Phase 5: Odoo on Cloud**
- [ ] Deploy Odoo Community on Cloud VM
- [ ] HTTPS setup
- [ ] Automated backups
- [ ] Health monitoring
- [ ] Cloud Agent: Draft-only accounting
- [ ] Local Agent: Approval for posting

### **Phase 6: A2A Communication**
- [ ] Replace file handoffs with A2A messages
- [ ] Keep vault as audit record
- [ ] Real-time agent communication
- [ ] Message queuing

---

## 🚀 **Quick Start**

### **Prerequisites:**
- Oracle Cloud account (or AWS)
- Domain name (for HTTPS)
- Gold Tier complete
- Odoo experience

### **Step 1: Cloud VM Setup**
```bash
# Oracle Cloud Free Tier
# 1. Create VM (Ubuntu 22.04)
# 2. Open ports: 80, 443, 8069 (Odoo)
# 3. SSH into VM
ssh ubuntu@your-vm-ip

# 4. Install Docker
curl -fsSL https://get.docker.com | sh

# 5. Install Odoo
docker run -d -p 8069:8069 odoo:latest
```

### **Step 2: Deploy Cloud Agent**
```bash
# On Cloud VM
cd /opt
git clone <your-repo> Personal_AI_Employee
cd Personal_AI_Employee/Platinum_Tier

# Setup environment
copy .env.example .env
# Edit .env - add cloud-specific config

# Install dependencies
uv sync

# Run cloud agent
python -m src.ai_employee_platinum.cloud_agent
```

### **Step 3: Setup Vault Sync**
```bash
# Option A: Git-based sync
# Local machine
cd AI_Employee_Vault
git init
git remote add origin <your-git-repo>
git push -u origin main

# Cloud VM
cd /opt/Personal_AI_Employee/Vault
git clone <your-git-repo> .

# Setup auto-sync cron
crontab -e
# Add: */5 * * * * cd /opt/Personal_AI_Employee/Vault && git pull
```

### **Step 4: Security Setup**
```bash
# NEVER commit .env files
# NEVER commit credentials.json
# NEVER commit token.json

# Add to .gitignore
.env
*.json
!package.json
sessions/
*.session
```

---

## 📊 **Platinum vs Gold**

| Feature | Gold Tier | Platinum Tier |
|---------|-----------|---------------|
| **Deployment** | Local only | Cloud + Local |
| **Operation** | 24/7 on local machine | 24/7 on cloud |
| **Agents** | 7 autonomous agents | Cloud (draft) + Local (approve) |
| **Vault Sync** | Single vault | Multi-vault sync |
| **Security** | Local secrets | Separated secrets |
| **Odoo** | Local Odoo | Cloud Odoo + Local approval |
| **Use Case** | Personal automation | Production business automation |

---

## 🎯 **Success Criteria**

### **Minimum Passing Gate:**
```
Email arrives while Local is offline
→ Cloud drafts reply
→ Cloud writes approval file
→ When Local returns, user approves
→ Local executes send via MCP
→ Logs action
→ Moves task to /Done
```

### **Full Completion:**
- [ ] Cloud VM deployed and running 24/7
- [ ] Work-zone specialization implemented
- [ ] Vault sync working (Git or Syncthing)
- [ ] Security boundaries enforced
- [ ] Odoo on cloud with HTTPS
- [ ] A2A communication working
- [ ] Demo passes minimum passing gate

---

## 📁 **Folder Structure**

```
Platinum_Tier/
├── src/ai_employee_platinum/
│   ├── cloud_agent.py          # Cloud-only agent
│   ├── local_agent.py          # Local-only agent
│   ├── vault_sync.py           # Vault synchronization
│   ├── security_manager.py     # Security boundaries
│   └── a2a_communication.py    # Agent-to-Agent messaging
├── specs/
│   └── platinum-spec.md        # Full specifications
├── docs/
│   ├── DEPLOYMENT.md           # Cloud deployment guide
│   ├── SECURITY.md             # Security guidelines
│   └── TROUBLESHOOTING.md      # Troubleshooting guide
├── tests/
│   └── test_platinum.py        # Platinum tier tests
├── scripts/
│   ├── deploy_cloud.sh         # Cloud deployment script
│   └── setup_vault_sync.sh     # Vault sync setup
├── .env.example
└── README.md                   # This file
```

---

## 🔧 **Resources**

### **Cloud Providers:**
- [Oracle Cloud Free Tier](https://www.oracle.com/cloud/free/)
- [AWS Free Tier](https://aws.amazon.com/free/)

### **Vault Sync:**
- [Git for Vault Sync](https://help.obsidian.md/Advanced+topics/Using+Git+for+sync)
- [Syncthing](https://syncthing.net/)

### **Security:**
- [Never Commit Secrets](https://www.gitguardian.com/secrets-detection)
- [Encrypted Sync](https://www.veracrypt.fr/)

---

## 📞 **Need Help?**

- **Gold Tier Docs**: Check `../Gold_Tier/docs/`
- **Silver Tier Docs**: Check `../AI_Employee_Silver/docs/`
- **Testing Guide**: Check `docs/TESTING_GUIDE.md` (coming soon)

---

**Status**: 🏗️ In Development
**Estimated Time**: 60+ hours
**Priority**: After Gold Tier Testing

---

**Last Updated**: 2026-03-13
**Next Step**: Complete Gold Tier Testing → Start Platinum Tier
