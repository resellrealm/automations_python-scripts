---
name: log-tail
description: Read the last N lines of any bot log file. Use when you want to see what a bot is actually doing, check for errors, or debug a problem.
allowed-tools: Bash, Read
argument-hint: "[polymarket|heartbeat|openclaw|apprenticeship|runner|all] [lines]"
---

Tail log files from the VPS bots.

Arguments: `$ARGUMENTS`
Format: `<bot> <lines>` — e.g. "polymarket 50" or "all 20" or just "polymarket"

Log file locations:
- polymarket → `polymarket_flipper/logs/flipper.log`
- heartbeat  → `heartbeat.log`
- openclaw   → `telegram_messenger/openclaw.log`
- apprenticeship → `apprenticeship_applier/applier.log`
- runner     → `vps_tasks/runner.log`
- cron       → `polymarket_flipper/logs/cron.log`

Steps:

1. Parse argument to identify which log(s) and how many lines (default 30)

2. **If "all"** — tail each log briefly (15 lines each):
   ```bash
   for log in polymarket_flipper/logs/flipper.log heartbeat.log telegram_messenger/openclaw.log vps_tasks/runner.log; do
     echo "=== $log ==="; tail -15 "$log" 2>/dev/null || echo "(not found)"; echo
   done
   ```

3. **If specific bot** — tail that log:
   ```bash
   tail -30 polymarket_flipper/logs/flipper.log
   ```

4. **Highlight** any ERROR, WARNING, CRITICAL lines in your reply

5. **If errors found**: Explain what each error means in plain English and suggest a fix

6. If log doesn't exist: tell which file path was expected and how to check if the bot is running
