# PaperclipAI + Kimi/Claude CLI - Quick Start

## 1. Deploy to VPS (One Command)

```bash
# SSH to your VPS
ssh your-vps-ip

# Navigate to your python-scripts folder
cd ~/python-scripts/paperclip_setup

# Run the installer
./scripts/install.sh
```

This installs:
- PaperclipAI with embedded database
- Kimi CLI adapter
- Claude CLI adapter  
- Dev Agency company config
- Systemd service

## 2. Start Paperclip

```bash
# Start the service
paperclip-ctl start

# Check it's running
paperclip-ctl status

# View logs
paperclip-ctl logs
```

## 3. Access Dashboard

From your Mac:
```bash
# Port forward to access dashboard
ssh -L 3000:localhost:3000 your-vps-ip

# Open http://localhost:3000 in browser
```

## 4. Build Your First App

### Option A: Via Dashboard
1. Go to http://localhost:3000
2. Click "New Task"
3. Enter: "Build a personal finance tracker with expense categories"
4. Watch agents coordinate and build it

### Option B: Via CLI
```bash
paperclip-ctl ticket "Build a habit tracker with streaks and reminders"
```

## 5. How It Works

When you create a ticket, here's what happens:

```
You: "Build a habit tracker"
  ↓
CEO Agent (Claude): Plans architecture, creates sub-tasks
  ↓
CTO Agent (Claude): Designs tech stack, API contracts
  ↓
├─→ Backend Lead (Claude): Designs database schema
│   └─→ Backend Dev (Kimi): Implements API routes
│
└─→ Frontend Lead (Claude): Designs UI components
    └─→ Frontend Dev (Kimi): Implements React code
  ↓
QA Agent (Kimi): Tests the app
  ↓
DevOps Agent (Kimi): Deploys to Vercel
  ↓
You: Review the live app
```

## 6. Monitor Progress

```bash
# Watch agents work in real-time
paperclip-ctl logs

# Or check the dashboard for:
# - Active tickets
# - Agent status
# - Budget usage
# - Recent deployments
```

## 7. Project Output

Completed apps are saved to:
```
~/projects/
└── habit-tracker/
    ├── src/
    ├── package.json
    └── README.md
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Agents stuck | Check `paperclip-ctl logs` for errors |
| CLI not found | Verify `which kimi` and `which claude` |
| Permission denied | Run `chmod +x ~/.paperclip/agents/*/adapter.sh` |
| Port 3000 in use | Edit `~/.paperclip/.env` change `PAPERCLIP_PORT` |
| Budget exceeded | Agents auto-pause, approve increase in dashboard |

## Agent Budgets (Monthly)

| Agent | Budget | Role |
|-------|--------|------|
| CEO | $50 | Strategy |
| CTO | $40 | Architecture |
| Frontend Lead | $30 | Design |
| Frontend Dev | $25 | Implementation |
| Backend Lead | $30 | API Design |
| Backend Dev | $25 | Implementation |
| QA | $20 | Testing |
| DevOps | $20 | Deployment |

**Total per month: ~$240** (adjust in config if needed)

## Next Steps

1. **Add your app ideas** to the ticket queue
2. **Customize the company** in `~/.paperclip/companies/autonomous-app-studio/config.json`
3. **Add more skills** by creating new `SKILL.md` files
4. **Create templates** for common app types

## File Structure on VPS

```
~/.paperclip/
├── agents/
│   ├── kimi-cli/
│   │   ├── adapter.sh
│   │   └── manifest.json
│   └── claude-cli/
│       ├── adapter.sh
│       └── manifest.json
├── companies/
│   └── autonomous-app-studio/
│       └── config.json
├── skills/
│   ├── kimi-cli/SKILL.md
│   ├── claude-cli/SKILL.md
│   └── app-development/SKILL.md
├── data/           # Database files
├── .env            # Configuration
└── logs/           # Agent logs

~/projects/         # Where apps are built
└── [app-name]/
    └── ...
```

Happy autonomous building! 🤖
