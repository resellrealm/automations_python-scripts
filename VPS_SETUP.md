# VPS Setup Instructions
Everything you need to get all bots running on your VPS from scratch.

---

## Step 1 — Clone the repo

```bash
cd ~
git clone https://github.com/resellrealm/automations_python-scripts.git python-scripts
cd python-scripts
```

---

## Step 2 — Install Python dependencies

```bash
# Polymarket bot
cd ~/python-scripts/polymarket_flipper
pip install py-clob-client requests python-dotenv

# Telegram messenger (OpenClaw)
cd ~/python-scripts/telegram_messenger
pip install python-telegram-bot requests python-dotenv

# Apprenticeship applier
cd ~/python-scripts/apprenticeship_applier
pip install playwright requests beautifulsoup4 python-dotenv
playwright install chromium
```

---

## Step 3 — Create .env files

### Polymarket bot (`polymarket_flipper/.env`)
```env
PRIVATE_KEY=your_polygon_wallet_private_key
API_KEY=your_polymarket_api_key
API_SECRET=your_polymarket_api_secret
API_PASSPHRASE=your_polymarket_api_passphrase
CLOB_API_URL=https://clob.polymarket.com
```
Get API keys from: polymarket.com → Profile → API Keys

### Telegram bot (`telegram_messenger/.env`)
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_USER_ID=your_numeric_telegram_id
AI_API_URL=http://localhost:8000/v1
AI_API_KEY=your_kimi_api_key
KIMI_MODEL=moonshot-v1-8k
```
- Get bot token: message @BotFather on Telegram → /newbot
- Get your user ID: message @userinfobot on Telegram

### Apprenticeship applier (`apprenticeship_applier/.env`)
```env
GOVUK_EMAIL=your_gov_uk_email
GOVUK_PASSWORD=your_gov_uk_password
TELEGRAM_BOT_TOKEN=same_bot_token_as_above
TELEGRAM_CHAT_ID=same_user_id_as_above
AI_API_URL=http://localhost:8000/v1
AI_API_KEY=your_kimi_api_key
```

### Trade report Telegram env (add to polymarket_flipper/.env)
```env
TELEGRAM_BOT_TOKEN=same_bot_token
TELEGRAM_USER_ID=same_user_id
```

---

## Step 4 — Run the Polymarket bot

```bash
cd ~/python-scripts/polymarket_flipper

# Test it first (no real orders)
python main.py --dry-run --once

# Check balance + trade size table
python main.py --balance

# Run live in background (stays running 24/7)
nohup python main.py >> logs/flipper.log 2>&1 &

# Check it's running
ps aux | grep main.py

# Watch live logs
tail -f logs/flipper.log
```

---

## Step 5 — Run the Telegram bot (OpenClaw)

```bash
cd ~/python-scripts/telegram_messenger

# Test it (run in foreground first)
python bot.py

# Then send yourself a message on Telegram to verify it replies

# Run in background
nohup python bot.py >> openclaw.log 2>&1 &
```

---

## Step 6 — Set up cron jobs (daily + weekly reports)

```bash
cd ~/python-scripts/polymarket_flipper

# See the exact crontab lines to add
bash reports/cron_setup.sh

# Open crontab editor
crontab -e

# Paste these two lines (adjust path if your username is different):
0 0 * * * cd /root/python-scripts/polymarket_flipper && python -m reports.daily_report >> logs/cron.log 2>&1
0 0 * * 0 cd /root/python-scripts/polymarket_flipper && python -m reports.weekly_report >> logs/cron.log 2>&1
```

Test reports right now:
```bash
cd ~/python-scripts/polymarket_flipper
python -m reports.daily_report    # sends Telegram message
python -m reports.weekly_report   # sends Telegram message
```

---

## Step 7 — Run the Apprenticeship Applier

```bash
cd ~/python-scripts/apprenticeship_applier

# Scrape only (no applying)
python main.py --scrape-only

# Generate cover letters but don't submit
python main.py --dry-run

# Apply (limit to 5 at a time to be safe)
python main.py --apply --limit 5
```

On first run: it will open the GOV.UK One Login page, send you a Telegram message asking for the 6-digit OTP from your email. Check your inbox, paste the code back in Telegram. Done — session is saved for next time.

---

## Step 8 — Set up n8n workflows (email auto-replier + bot monitor)

If n8n isn't installed yet:
```bash
npm install -g n8n
nohup n8n >> ~/n8n.log 2>&1 &
```

Open n8n at: `http://YOUR_VPS_IP:5678`

Import workflows:
1. Click **+** → **Import from file**
2. Import `n8n_workflows/email_autoreplier.json`
3. Import `n8n_workflows/bot_monitor.json`

For each workflow, set up credentials (left panel → Credentials):
- **Zoho IMAP**: host=`imap.zoho.com`, port=`993`, SSL=on
- **Zoho SMTP**: host=`smtp.zoho.com`, port=`465`, SSL=on
- **OpenClaw Bot** (Telegram): paste your bot token

Set environment variables in n8n (Settings → Variables):
- `AI_API_URL` = your Kimi endpoint
- `AI_API_KEY` = your Kimi key
- `TELEGRAM_USER_ID` = your numeric Telegram ID

Then **Activate** both workflows.

---

## Keeping everything running

### Check what's running
```bash
ps aux | grep python
```

### Restart a bot that crashed
```bash
# Polymarket
cd ~/python-scripts/polymarket_flipper && nohup python main.py >> logs/flipper.log 2>&1 &

# Telegram bot
cd ~/python-scripts/telegram_messenger && nohup python bot.py >> openclaw.log 2>&1 &
```

### Update to latest code
```bash
cd ~/python-scripts
git pull
# Then restart whatever changed
```

### Check P&L report
```bash
cd ~/python-scripts/polymarket_flipper
python main.py --report      # 30-day trade table
python main.py --balance     # balance + size table + 30-day projection
python main.py --optimize    # strategy win rates + live multipliers
```

---

## Trade log file structure

```
polymarket_flipper/
└── logs/
    ├── trades/
    │   └── 2026-03-14.jsonl   ← today's trades (live)
    ├── weekly/
    │   └── 2026-W11/
    │       └── 2026-03-09.jsonl  ← moved here at midnight
    └── alltime/
        └── weekly_pnl.jsonl   ← one line per week, forever
```

---

## Quick reference

| What | Command |
|---|---|
| Start Polymarket bot | `nohup python polymarket_flipper/main.py >> logs/flipper.log 2>&1 &` |
| Start Telegram bot | `nohup python telegram_messenger/bot.py >> openclaw.log 2>&1 &` |
| Dry run (test) | `python polymarket_flipper/main.py --dry-run --once` |
| Check balance | `python polymarket_flipper/main.py --balance` |
| Manual daily report | `python -m reports.daily_report` (from polymarket_flipper/) |
| See all processes | `ps aux | grep python` |
| Watch live logs | `tail -f polymarket_flipper/logs/flipper.log` |
