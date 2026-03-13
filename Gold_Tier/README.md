# 🏆 Gold Tier: Autonomous Employee

**Project**: Personal AI Employee - Autonomous FTE (Full-Time Equivalent)
**Version**: 0.3.0
**Status**: Building Autonomous Agents with Cross-Domain Integration

---

## 🎯 Gold Tier Objectives

Complete all Silver requirements plus:

1. **Full cross-domain integration** (Personal + Business)
2. **Odoo accounting system** integration via MCP using JSON-RPC APIs
3. **Facebook and Instagram integration** (post messages + summary)
4. **Twitter (X) integration** (post messages + summary)
5. **Multiple MCP servers** for different action types
6. **Weekly Business and Accounting Audit** with CEO Briefing generation
7. **Error recovery and graceful degradation**
8. **Comprehensive audit logging**
9. **Ralph Wiggum loop** for autonomous multi-step task completion
10. **Documentation of architecture** and lessons learned
11. **All AI functionality** implemented as Agent Skills

---

## 📁 Directory Structure

```
Gold_Tier/
├── src/
│   └── ai_employee_gold/
│       ├── config/
│       ├── core/
│       ├── integrations/
│       ├── mcp/
│       ├── agents/
│       └── tools/
├── specs/
├── docs/
├── tests/
├── scripts/
├── .env
├── .env.example
└── README.md
```

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    GOLD TIER AI EMPLOYEE                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  EXTERNAL SOURCES                                               │
│  Gmail │ WhatsApp │ LinkedIn │ Facebook │ Instagram │ Twitter  │
│  │         │           │           │           │           │    │
│  └─────────┼───────────┼───────────┼───────────┼───────────┘    │
│            │           │           │           │                 │
│  PERCEPTION LAYER (Python Watchers)                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │  Gmail  │ │WhatsApp │ │LinkedIn │ │Facebook │ │Twitter  │ │
│  │Watcher  │ │ Watcher │ │ Watcher │ │ Watcher │ │ Watcher │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ │
│            │           │           │           │           │    │
│  OBSIDIAN VAULT (Memory/GUI)                                  │
│  /Inbox/ /Needs_Action/ /Plans/ /Done/ /Logs/ /Accounting/   │
│  Dashboard.md │ Company_Handbook.md │ Business_Goals.md      │
│            │           │           │           │           │    │
│  REASONING LAYER (Brain)                                      │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  CLAUDE CODE OR QWEN (Terminal/PowerShell CCR)         │  │
│  │  Read → Think → Plan → Write → Request Approval        │  │
│  └─────────────────────────────────────────────────────────┘  │
│            │           │           │           │           │    │
│  ACTION LAYER (Hands)                                         │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │  Email  │ │Browser  │ │ Odoo    │ │Social   │ │Custom   │ │
│  │ MCP     │ │ MCP     │ │ MCP     │ │ MCP     │ │ Scripts │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ │
│            │           │           │           │           │    │
│  EXTERNAL ACTIONS: Send Email, Post Social, Payments, ERP   │
│                                                                 │
│  ORCHESTRATION: orchestrator.py + watchdog.py                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.13 or higher
- Node.js v24+ LTS
- Claude Code subscription
- Obsidian v1.10.6+

### Setup
```bash
# Clone the repository
cd Gold_Tier

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your credentials
nano .env

# Start the autonomous system
python -m src.ai_employee_gold.main orchestrator
```

---

## 📋 Gold Tier Requirements Checklist

### ✅ All Silver Tier Requirements
- [x] Obsidian vault with Dashboard.md and Company_Handbook.md
- [x] Two or more Watcher scripts (Gmail + WhatsApp + LinkedIn)
- [x] Claude reasoning loop that creates Plan.md files
- [x] One working MCP server for external action (e.g., sending emails)
- [x] Human-in-the-loop approval workflow for sensitive actions
- [x] Basic scheduling via cron or Task Scheduler
- [x] All AI functionality implemented as Agent Skills

### 🚧 Gold Tier Requirements
- [ ] Full cross-domain integration (Personal + Business)
- [ ] Create accounting system in Odoo Community (self-hosted, local)
- [ ] Integrate Odoo via MCP server using JSON-RPC APIs (Odoo 19+)
- [ ] Integrate Facebook and Instagram (post messages + summary)
- [ ] Integrate Twitter (X) (post messages + summary)
- [ ] Multiple MCP servers for different action types
- [ ] Weekly Business and Accounting Audit with CEO Briefing generation
- [ ] Error recovery and graceful degradation
- [ ] Comprehensive audit logging
- [ ] Ralph Wiggum loop for autonomous multi-step task completion
- [ ] Documentation of architecture and lessons learned
- [ ] All AI functionality implemented as Agent Skills

---

## 📄 License
MIT License