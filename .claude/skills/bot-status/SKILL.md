---
name: bot-status
description: Check the live status of all VPS bots and background tasks. Shows which bots are running, which have crashed, current task statuses, today's P&L, and any errors from the last hour. Your VPS health dashboard.
allowed-tools: Bash, Read
argument-hint: ""
---

Check full VPS health status — bots, tasks, P&L, recent errors.

Steps:

1. **Check which bot processes are running:**
   ```bash
   ps aux | grep -E "polymarket_flipper|kalshi_flipper|oddpool|heartbeat|bot\.py|apprenticeship" | grep -v grep
   ```

2. **Check active background tasks:**
   ```bash
   python vps_tasks/task_runner.py --status
   ```

3. **Get Polymarket bot balance and today's trades:**
   ```bash
   cd polymarket_flipper && python main.py --balance
   ```

4. **Check recent errors from bot logs (last 20 lines each):**
   ```bash
   tail -20 polymarket_flipper/logs/flipper.log 2>/dev/null || echo "No flipper log"
   tail -20 heartbeat.log 2>/dev/null || echo "No heartbeat log"
   ```

5. **Format and reply** with a clean summary:
   - 🟢 Running / 🔴 Dead for each bot
   - ⏳ / ✅ / ❌ for each task
   - Balance + today's P&L
   - Any ERROR lines from logs (highlight these)

If any bot is dead: suggest the restart command:
`nohup python <dir>/main.py >> <dir>/bot.log 2>&1 &`
