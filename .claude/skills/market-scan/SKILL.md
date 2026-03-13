---
name: market-scan
description: Scan Polymarket and Kalshi for arbitrage opportunities right now. Shows profitable YES/NO cross-platform arbs, flash crash opportunities, and NO bundle arbs. Use when user wants to see what money-making opportunities exist.
allowed-tools: Bash, Read
argument-hint: "[--live]"
---

Run the market scanners and report findings.

Steps:
1. Run Oddpool in scan-only mode:
   `cd /root/automations_python-scripts/oddpool && python main.py --scan-only --once 2>&1 | tail -30`

2. Run Polymarket Flipper dry-run cycle:
   `cd /root/automations_python-scripts/polymarket_flipper && python main.py --dry-run --once 2>&1 | tail -20`

3. Run Kalshi Flipper dry-run cycle:
   `cd /root/automations_python-scripts/kalshi_flipper && python main.py --dry-run --once 2>&1 | tail -20`

4. Summarise all opportunities found in a clean table.

If $ARGUMENTS contains --live, remove --dry-run flags to execute real trades.
