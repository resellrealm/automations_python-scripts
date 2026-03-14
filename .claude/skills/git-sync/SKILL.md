---
name: git-sync
description: Pull the latest code from GitHub, show what changed, and optionally restart any bots that had their files updated. Use after pushing changes from your Mac to make the VPS run the new code.
allowed-tools: Bash, Read
argument-hint: "[restart]"
---

Pull latest code from GitHub and optionally restart updated bots.

Argument: $ARGUMENTS (blank = pull only, "restart" = pull + restart affected bots)

Steps:

1. **Show current state before pull:**
   ```bash
   git log --oneline -3
   git status --short
   ```

2. **Pull latest:**
   ```bash
   git pull xvin1ty main
   ```

3. **Show what changed:**
   ```bash
   git diff HEAD@{1} HEAD --name-only
   ```

4. **If argument includes "restart" — restart bots whose files changed:**
   - If `polymarket_flipper/` files changed:
     ```bash
     pkill -f "polymarket_flipper/main.py" 2>/dev/null
     nohup python polymarket_flipper/main.py >> polymarket_flipper/bot.log 2>&1 &
     ```
   - If `apprenticeship_applier/` files changed:
     ```bash
     pkill -f "apprenticeship_applier/main.py" 2>/dev/null
     ```
   - If `telegram_messenger/` files changed:
     ```bash
     pkill -f "telegram_messenger/bot.py" 2>/dev/null
     nohup python telegram_messenger/bot.py >> telegram_messenger/openclaw.log 2>&1 &
     ```

5. **Verify running processes:**
   ```bash
   ps aux | grep -E "main\.py|bot\.py" | grep -v grep
   ```

6. Reply with:
   - What commit was pulled
   - Which files changed
   - Which bots were restarted (if restart mode)
   - Current status of each bot
