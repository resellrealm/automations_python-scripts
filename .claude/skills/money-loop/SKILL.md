---
name: money-loop
description: Start the autonomous money-making loop. Runs all prediction market bots (Oddpool, Polymarket Flipper, Kalshi Flipper) and monitors them. Use when user wants to start making money or restart the bots.
allowed-tools: Bash, Read, Glob
argument-hint: "[--dry-run]"
---

Start the full autonomous money-making loop.

Steps:
1. Check all bot folders exist and have .env files
2. Run: `cd /root/automations_python-scripts && python claude_agents/orchestrator.py --loop $ARGUMENTS`
3. Report which bots started and their PIDs
4. Confirm the heartbeat is running

If --dry-run passed: add --dry-run flag to orchestrator command.

If any .env file is missing, warn the user which credentials are needed before starting.
