# Python Automation Scripts

Two AI-powered automation tools designed to run on your VPS with Kimi AI.

---

## Tools

| Tool | What it does |
|------|-------------|
| `email_autoreplier/` | Reads Gmail inbox, auto-replies with Kimi AI, escalates to you when needed |
| `apprenticeship_applier/` | Scrapes UK apprenticeship listings and auto-applies with tailored cover letters |

---

## Setup

### 1. Clone & install dependencies

```bash
# Email Auto-Replier
cd email_autoreplier
pip install -r requirements.txt

# Apprenticeship Applier
cd ../apprenticeship_applier
pip install -r requirements.txt
playwright install chromium   # Install the headless browser
```

### 2. Configure each tool

```bash
# For each tool, copy the example env file and fill it in:
cp email_autoreplier/.env.example email_autoreplier/.env
cp apprenticeship_applier/.env.example apprenticeship_applier/.env
```

---

## Email Auto-Replier Setup

### Get Gmail OAuth2 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or use an existing one)
3. Go to **APIs & Services → Enable APIs** → search for and enable **Gmail API**
4. Go to **APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID**
5. Application type: **Desktop App**
6. Download the JSON — paste the `client_id` and `client_secret` into your `.env`
7. Under **OAuth consent screen**, add your Gmail address as a test user

### Fill in `.env`

```env
AI_API_URL=https://api.moonshot.cn/v1/chat/completions
AI_API_KEY=your_kimi_api_key
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret
YOUR_NAME=Your Name
YOUR_EMAIL=you@gmail.com
YOUR_ROLE=Personal Assistant
REPLY_TONE=professional and friendly
POLL_INTERVAL_MINUTES=5
```

### First Run (OAuth login)

```bash
cd email_autoreplier
python main.py --once
```

A browser window will open for you to log into Google. After that, a `token.json` is saved and all future runs are automatic.

### Running Commands

```bash
# Process inbox once and exit
python main.py --once

# Run as daemon (polls every 5 minutes forever)
python main.py

# Show emails that need your attention
python main.py --queue

# Show stats (how many replied vs escalated)
python main.py --stats
```

### Running as a VPS Service (systemd)

```bash
# Create service file
sudo nano /etc/systemd/system/email-replier.service
```

```ini
[Unit]
Description=Email Auto-Replier
After=network.target

[Service]
WorkingDirectory=/path/to/python-scripts/email_autoreplier
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable email-replier
sudo systemctl start email-replier
sudo journalctl -u email-replier -f   # View live logs
```

---

## Apprenticeship Applier Setup

### Fill in your profile

Edit `apprenticeship_applier/user_profile.json` with ALL your real details:
- Personal info (name, DOB, address, phone)
- Education and qualifications
- Work experience
- Skills and interests
- CV file path

### Fill in `.env`

```env
AI_API_URL=https://api.moonshot.cn/v1/chat/completions
AI_API_KEY=your_kimi_api_key
SEARCH_KEYWORDS=software,IT,data,developer
SEARCH_LOCATION=London
GOVUK_EMAIL=youremail@gmail.com
GOVUK_PASSWORD=your_findapprenticeship_password
MAX_APPLICATIONS_PER_RUN=10
DRY_RUN=false
HEADLESS=true
```

> **Note:** `GOVUK_EMAIL` and `GOVUK_PASSWORD` are for your account on
> [findapprenticeship.service.gov.uk](https://www.findapprenticeship.service.gov.uk) — register there if you don't have one.

### Running Commands

```bash
cd apprenticeship_applier

# Find new listings and save them (no applications yet)
python main.py --scrape-only

# Test run — generate cover letters but don't submit
python main.py --apply --dry-run

# Apply to up to 10 jobs
python main.py --apply

# Apply to just 3 jobs this run
python main.py --apply --limit 3

# Show stats
python main.py --report
```

### Running via Cron (VPS)

```bash
crontab -e
```

```cron
# Check for new apprenticeships and apply — runs every day at 9am
0 9 * * * cd /path/to/python-scripts/apprenticeship_applier && python3 main.py --apply >> logs/cron.log 2>&1
```

---

## AI Configuration (Kimi AI on VPS)

Both tools connect to Kimi AI via an OpenAI-compatible API endpoint.

**If using the official Moonshot API:**
```env
AI_API_URL=https://api.moonshot.cn/v1/chat/completions
AI_API_KEY=your_key_from_platform.moonshot.cn
AI_MODEL=moonshot-v1-8k
```

**If using your self-hosted VPS:**
```env
AI_API_URL=http://YOUR_VPS_IP:PORT/v1/chat/completions
AI_API_KEY=your_local_api_key_or_leave_empty
AI_MODEL=your_model_name
```

---

## File Structure

```
python-scripts/
├── shared/
│   ├── kimi_client.py          # Kimi AI API wrapper
│   └── logger.py               # Rotating file logger
│
├── email_autoreplier/
│   ├── main.py                 # Entry point
│   ├── gmail_client.py         # Gmail OAuth2
│   ├── ai_handler.py           # AI reply + escalation decisions
│   ├── email_processor.py      # Core processing loop
│   ├── escalation_queue.py     # Human review queue
│   ├── database.py             # SQLite tracking
│   ├── config.py               # Settings
│   ├── requirements.txt
│   └── .env.example
│
├── apprenticeship_applier/
│   ├── main.py                 # Entry point
│   ├── scraper.py              # gov.uk scraper
│   ├── applier.py              # Playwright form-filler
│   ├── ai_cover_letter.py      # AI cover letter generator
│   ├── profile_manager.py      # User profile loader
│   ├── database.py             # SQLite tracking
│   ├── config.py               # Settings
│   ├── user_profile.json       # YOUR personal details (fill this in!)
│   ├── requirements.txt
│   └── .env.example
│
└── README.md
```

---

## Output Files

| File / Folder | What's in it |
|---------------|-------------|
| `email_autoreplier/emails.db` | All processed emails + actions taken |
| `email_autoreplier/escalation_queue.json` | Emails waiting for your reply |
| `email_autoreplier/logs/` | Rotating log files |
| `apprenticeship_applier/applications.db` | All jobs found + application status |
| `apprenticeship_applier/cover_letters/` | AI-generated cover letters |
| `apprenticeship_applier/screenshots/` | Screenshots of submitted applications |
| `apprenticeship_applier/logs/` | Rotating log files |

---

## Troubleshooting

**Gmail login fails:**
→ Make sure your Gmail account has 2FA enabled and you're using the OAuth client ID/secret (not an app password).
→ Check you added your email as a "Test user" in Google Cloud Console.

**Apprenticeship form not filling correctly:**
→ Set `HEADLESS=false` in `.env` to see the browser
→ Run `--dry-run` first to test without submitting

**Kimi AI errors:**
→ Check your `AI_API_KEY` is correct
→ Try `AI_MODEL=moonshot-v1-32k` if responses are being cut off

**CAPTCHA blocked:**
→ Set `HEADLESS=false`, run the applier, and solve the CAPTCHA manually when prompted
