---
name: task-status
description: Check the status of background tasks running on the VPS. Use when you want to know if a task you started is done yet, still running, or failed. Answers "are you done yet?" type questions.
allowed-tools: Bash, Read
argument-hint: ""
---

Check the status of all VPS background tasks.

Steps:

1. **Read task status file:**
   ```bash
   python vps_tasks/task_runner.py --status
   ```

2. **Also check for any running task_runner processes:**
   ```bash
   ps aux | grep task_runner | grep -v grep
   ```

3. **For any task that shows "running", verify it's actually still alive:**
   - Cross-reference PID from tasks.json against running processes
   - If PID is gone but status still says "running" → mark it as unknown/stale

4. **Reply clearly:**
   - ⏳ Still running: "Still going — started X minutes ago"
   - ✅ Done: "Finished at HH:MM. Exit code 0 (success). [show output tail]"
   - ❌ Failed: "Failed at HH:MM. Exit code N. Error: [show error]"
   - 📭 No tasks: "No background tasks recorded. Use /task-heartbeat to start one."

5. **If a task just completed**, show the last few lines of its output

6. Offer: "Type /task-heartbeat to run a new task, or /bot-status for full VPS health."
