---
name: vps-run
description: Run any shell command on the VPS and get the output. For quick one-off commands that don't need background tracking. Use task-heartbeat instead for long-running tasks.
allowed-tools: Bash, Read
argument-hint: "<shell command>"
---

Run a shell command on the VPS and return the output.

Command to run: $ARGUMENTS

Steps:

1. **Safety check** — refuse if command is destructive:
   - Never run: `rm -rf /`, `DROP TABLE`, `format`, `mkfs`, `dd if=/dev/zero`
   - If command looks dangerous: ask for confirmation before running

2. **Run the command:**
   ```bash
   $ARGUMENTS
   ```

3. **Return the full output** — don't truncate unless very long (>100 lines)

4. **If error**: explain what went wrong and suggest a fix

5. **If the output suggests a long-running process** (e.g. starts a server, runs a loop):
   Warn: "This looks like it will run forever. Use /task-heartbeat instead so it runs in background."

Examples this skill is good for:
- `df -h` — disk space
- `free -m` — RAM usage
- `pip install some-package`
- `sqlite3 polymarket_flipper/flipper.db ".tables"`
- `python -c "import requests; print('ok')"`
- `cat polymarket_flipper/bankroll.json`
