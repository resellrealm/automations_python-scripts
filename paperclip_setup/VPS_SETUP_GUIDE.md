# PaperclipAI VPS Setup with Kimi + Claude CLI

Complete setup for autonomous app building on your VPS.

## Prerequisites (You Have These ✓)
- Kimi CLI installed and working
- Claude CLI installed and working
- Node.js 18+ installed
- VPS with persistent connection

---

## Step 1: Install Paperclip

```bash
# SSH to your VPS
ssh your-vps

# Install Paperclip (creates ~/.paperclip/)
npx paperclipai onboard --yes

# This sets up:
# - Embedded PostgreSQL database
# - React dashboard (runs on port 3000)
# - API server (runs on port 3001)
# - Default "My First Company"
```

## Step 2: Install Adapters

```bash
# Clone our adapters to VPS
cd ~/python-scripts/paperclip_setup

# Copy adapters to Paperclip's agent directory
mkdir -p ~/.paperclip/agents
cp -r adapters/* ~/.paperclip/agents/

# Make scripts executable
chmod +x ~/.paperclip/agents/kimi-cli/adapter.sh
chmod +x ~/.paperclip/agents/claude-cli/adapter.sh
```

## Step 3: Configure Paperclip

```bash
# Edit company config to add your agents
cp company_configs/dev_agency.json ~/.paperclip/companies/my-apps/config.json

# Set environment variables
echo 'export PAPERCLIP_KIMI_CLI_PATH=/usr/local/bin/kimi' >> ~/.bashrc
echo 'export PAPERCLIP_CLAUDE_CLI_PATH=/usr/local/bin/claude' >> ~/.bashrc
source ~/.bashrc
```

## Step 4: Start Paperclip Daemon

```bash
# Copy systemd service
sudo cp scripts/paperclip.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable paperclip
sudo systemctl start paperclip

# Check status
sudo systemctl status paperclip
```

## Step 5: Access Dashboard

```bash
# Port forward from VPS to local (run on your Mac)
ssh -L 3000:localhost:3000 your-vps

# Open http://localhost:3000 in browser
```

---

## Usage: Creating an App

### Via Dashboard:
1. Go to http://localhost:3000
2. Click "New Task"
3. Enter: "Build a [your app idea]"
4. CEO agent breaks it down
5. Watch agents coordinate via tickets

### Via CLI:
```bash
# Create ticket from command line
paperclip ticket create --title "Build meal tracking app" \
  --description "Full-stack app with photo AI recognition..." \
  --assign-to ceo-agent
```

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Agents not using CLIs | Check `~/.paperclip/agents/*/adapter.sh` paths |
| Permission denied | `chmod +x` on all adapter scripts |
| CLI not found | Verify paths in `~/.paperclip/.env` |
| Heartbeats not running | Check `sudo systemctl status paperclip-heartbeat` |

---

## Architecture

```
Paperclip Server (Port 3000/3001)
├── CEO Agent → Decides architecture
├── Frontend Lead → Uses Claude CLI for UI
├── Backend Lead → Uses Kimi CLI for API
└── QA Agent → Tests and validates

Each agent calls adapters:
  adapter.sh → kimi "prompt" → returns result to agent
  adapter.sh → claude "prompt" → returns result to agent
```
