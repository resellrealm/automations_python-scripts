---
name: trade-report
description: Get the Polymarket bot's trading report — today's P&L, open positions, win rate, strategy breakdown, and 30-day history. Use when you want to know how the bot is performing.
allowed-tools: Bash, Read
argument-hint: "[today|30day|balance|optimize]"
---

Get Polymarket Flipper trading performance report.

Argument options: today, 30day, balance, optimize, or blank for full summary.
Argument: $ARGUMENTS

Steps:

1. **Always show balance first:**
   ```bash
   cd polymarket_flipper && python main.py --balance
   ```

2. **If argument is "30day" or blank — show full report:**
   ```bash
   cd polymarket_flipper && python main.py --report
   ```

3. **If argument is "optimize" — show strategy performance + multipliers:**
   ```bash
   cd polymarket_flipper && python main.py --optimize
   ```

4. **Show today's JSONL trade log if it exists:**
   ```bash
   python vps_tasks/task_runner.py --status
   cat polymarket_flipper/logs/trades/$(date +%Y-%m-%d).jsonl 2>/dev/null | tail -20 || echo "No trades today yet"
   ```

5. **Show open positions from DB:**
   ```bash
   cd polymarket_flipper && python -c "import database as db; db.init_db(); trades=db.get_open_trades(); [print(f\"#{t['id']} {t['strategy']} | entry={t['entry_price']:.3f} | size={t['size']:.2f} | {t['opened_at'][:16]}\") for t in trades] or print('No open positions')"
   ```

6. Format a clean reply with:
   - Current balance, day P&L, total P&L
   - Number of open positions
   - Win rate and best strategy
   - Any notable trades from today
