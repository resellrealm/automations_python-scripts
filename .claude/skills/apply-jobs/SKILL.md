---
name: apply-jobs
description: Trigger the apprenticeship applier — scrape new listings, generate AI cover letters, and optionally auto-apply. Runs in background and texts you when done.
allowed-tools: Bash, Read
argument-hint: "[scrape-only|dry-run|apply <limit>]"
---

Run the apprenticeship applier on the VPS.

Argument: $ARGUMENTS (scrape-only | dry-run | apply | apply 5)

Steps:

1. **Decide mode from argument:**
   - No argument or "scrape-only" → just scrape, no applying
   - "dry-run" → scrape + generate cover letters, don't submit
   - "apply" or "apply N" → actually apply (limit to N, default 5)

2. **Build the command:**
   - scrape-only: `python apprenticeship_applier/main.py --scrape-only`
   - dry-run: `python apprenticeship_applier/main.py --dry-run`
   - apply: `python apprenticeship_applier/main.py --apply --limit 5`

3. **Run via task_runner (background + Telegram notification when done):**
   ```bash
   nohup python vps_tasks/task_runner.py \
     --name "Apply Jobs (mode)" \
     --cmd "python apprenticeship_applier/main.py --apply --limit 5" \
     >> vps_tasks/runner.log 2>&1 &
   ```

4. **Check current job DB stats first:**
   ```bash
   python apprenticeship_applier/main.py --report
   ```

5. Reply with:
   - How many jobs are in the DB (found/applied/pending)
   - That the task is running in background
   - "You'll get a Telegram message when done"
   - Reminder: first run needs GOV.UK One Login OTP — check Telegram for the code prompt

Note: GOV.UK login sends an OTP to your email. If the applier asks for it via Telegram, reply with the 6-digit code.
