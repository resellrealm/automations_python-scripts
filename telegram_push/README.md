# telegram_push — Proactive VPS Notifier

Pushes messages TO your Telegram from any script on the VPS.
No polling. No waiting for you to message first. Just instant push.

---

## Setup (one time)

```bash
# Copy example env (or reuse your existing .env in repo root)
cp telegram_push/.env.example .env
# Fill in TELEGRAM_BOT_TOKEN and TELEGRAM_USER_ID

# Test it works
python telegram_push/push.py --test
```

If you see the test message on your phone — done. Every bot and task on the VPS can now notify you.

---

## Use in any Python script

```python
from telegram_push import notify

notify("Hello from VPS!")
```

```python
from telegram_push import notify_task_start, notify_task_done, notify_task_failed

notify_task_start("Scrape Jobs", cmd="python apprenticeship_applier/main.py --scrape-only")
# ... run task ...
notify_task_done("Scrape Jobs", output="Found 47 listings", duration_s=480)
```

```python
from telegram_push import notify_bot_crash, notify_bot_restarted

notify_bot_crash("Polymarket Bot", log_tail=last_log_lines)
notify_bot_restarted("Polymarket Bot", pid=new_pid)
```

```python
from telegram_push import notify_daily_stop

notify_daily_stop(balance_gbp=28.50, loss_gbp=1.50)
```

---

## CLI (from shell / cron / bash scripts)

```bash
# Send any message
python telegram_push/push.py "Cron job finished"

# Task notifications
python telegram_push/push.py --task-start "Scrape Jobs" --cmd "python ..."
python telegram_push/push.py --task-done  "Scrape Jobs" --output "Found 47"
python telegram_push/push.py --task-fail  "Scrape Jobs" --error "Timeout after 60s"

# Bot crash alert
python telegram_push/push.py --crash "Polymarket Bot" --output "last 5 log lines here"

# Test
python telegram_push/push.py --test
```

---

## Already integrated into

| Script | When it notifies you |
|---|---|
| `vps_tasks/task_runner.py` | Task starts + task done/failed |
| `claude_agents/heartbeat.py` | Bot crashes + restarts |
| `polymarket_flipper/bankroll.py` | Daily loss limit hit |

---

## How it works

```python
requests.post(
    f"https://api.telegram.org/bot{TOKEN}/sendMessage",
    json={"chat_id": YOUR_ID, "text": message}
)
```

That's it. Direct HTTP call to Telegram's API. Completely separate from the OpenClaw bot.
The OpenClaw bot RESPONDS when you message it.
This module PUSHES when the VPS wants to tell you something.
