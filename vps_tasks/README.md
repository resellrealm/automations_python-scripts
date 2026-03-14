# VPS Tasks — Background Task Runner

Solves the "text me when you're done" problem.

## The Problem

The Telegram bot (OpenClaw) only RESPONDS when you message it — it can't proactively message you.
So if you start a long task (e.g. scrape 200 job listings), you'd have to keep asking "are you done?".

## The Solution

`task_runner.py` runs tasks in the background AND pushes Telegram notifications directly when done.
This works because it calls the Telegram API directly — bypassing the bot's polling loop.

## How It Works

```
You:        "scrape jobs for me"
OpenClaw:   starts task_runner.py in background (nohup)
task_runner: → writes tasks.json: {status: "running"}
             → pushes Telegram: "⏳ Task started: scrape jobs"
             → runs: python apprenticeship_applier/main.py --scrape-only
             → (10 minutes pass)
             → pushes Telegram: "✅ Task complete: scrape jobs"
             → writes tasks.json: {status: "done"}

You (any time): "are you done?"
OpenClaw:   reads tasks.json → "✅ Done at 14:32. Found 47 new jobs."
```

## Usage

```bash
# Start a task (runs in background, notifies when done)
nohup python vps_tasks/task_runner.py \
  --name "scrape jobs" \
  --cmd "python apprenticeship_applier/main.py --scrape-only" \
  >> vps_tasks/runner.log 2>&1 &

# Check status at any time
python vps_tasks/task_runner.py --status

# Clear completed tasks from the list
python vps_tasks/task_runner.py --clear-done
```

## Skills (use from OpenClaw / Claude Code)

| Skill | What it does |
|---|---|
| `/task-heartbeat` | Start a background task + get notified when done |
| `/task-status` | Check "are you done yet?" |
| `/bot-status` | Full VPS health: bots, tasks, P&L, errors |
| `/trade-report` | Polymarket P&L + open positions |
| `/apply-jobs` | Run apprenticeship applier |
| `/git-sync` | Pull latest code, optionally restart bots |
| `/log-tail` | Read bot log files |
| `/vps-run` | Run any shell command |
| `/market-scan-now` | Trigger one Polymarket scan |

## File: tasks.json

```json
{
  "scrape_jobs_1710432000": {
    "name": "scrape jobs",
    "cmd": "python apprenticeship_applier/main.py --scrape-only",
    "status": "done",
    "started": "2026-03-14T12:00:00",
    "finished": "2026-03-14T12:08:32",
    "return_code": 0,
    "output_tail": "Found 47 listings. 12 new."
  }
}
```

## Requirements

Set in your `.env`:
```env
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_USER_ID=your_numeric_id
```
