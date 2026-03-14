---
name: task-heartbeat
description: Run any VPS task in the background. Tracks status in tasks.json and pushes a Telegram notification when done — so you'll know when it finishes without having to ask. Use for long-running tasks like scraping, backtests, report generation.
allowed-tools: Bash, Read, Write
argument-hint: "<task name> | <command to run>"
---

Run a VPS task in the background with completion notification.

Arguments format: `<task name> | <command>`
Example: `scrape apprenticeships | python apprenticeship_applier/main.py --scrape-only`
Example: `daily report | python polymarket_flipper/reports/daily_report.py`
Example: `$ARGUMENTS`

Steps:
1. Parse the argument — split on ` | ` to get task name and command
2. If no ` | ` separator found, ask: "What command should I run for this task?"
3. Run the task via task_runner.py as a **background process** (nohup):
   ```bash
   nohup python vps_tasks/task_runner.py --name "<task name>" --cmd "<command>" >> vps_tasks/runner.log 2>&1 &
   ```
4. Immediately reply: "⏳ Task '<task name>' started in background. I'll push a Telegram message when it's done — you don't need to keep asking."
5. Also show how to check status manually: `/task-status`

Important:
- Always use nohup so the task survives if the session ends
- Never wait for the task to finish — return immediately
- The task_runner.py will push Telegram when done — this is proactive, not polling
- If command fails to start, show the error and suggest checking the log: `tail -20 vps_tasks/runner.log`
