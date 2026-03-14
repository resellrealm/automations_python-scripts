# n8n Workflows

## How to import

1. Open n8n at `http://YOUR_VPS:5678`
2. Click **+** → **Import from file**
3. Select the `.json` file
4. Set up credentials (see notes in each workflow)
5. Click **Activate**

## Workflows

### `email_autoreplier.json`
Checks your Zoho inbox every 5 minutes. Kimi AI auto-replies or sends you a Telegram alert.

**Credentials to create in n8n:**
- `Zoho IMAP` — IMAP, host: `imap.zoho.com`, port: `993`, SSL on
- `Zoho SMTP` — SMTP, host: `smtp.zoho.com`, port: `465`, SSL on
- `OpenClaw Bot` — Telegram, paste your bot token

**n8n Environment Variables** (Settings → Variables):
- `AI_API_URL` — e.g. `http://1.2.3.4:8000/v1`
- `AI_API_KEY` — your Kimi API key
- `TELEGRAM_USER_ID` — your numeric Telegram user ID

### `bot_monitor.json`
Checks every 15 min if your bots are running. Sends Telegram alert if any are down.

**Requires n8n to be on the same VPS as your bots.**
If not: replace the `Execute Command` node with an SSH node.

**Credentials to create:**
- `OpenClaw Bot` — same Telegram bot as above
