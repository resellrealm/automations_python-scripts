---
name: market-scan-now
description: Run one Polymarket scan cycle right now (dry-run or live). Shows what signals were found, what trades would be or were placed, and the current strategy state. Good for testing the bot is working.
allowed-tools: Bash, Read
argument-hint: "[dry-run|live]"
---

Trigger one Polymarket scan cycle immediately.

Argument: $ARGUMENTS (dry-run = simulate only, live = real orders, blank = dry-run)

Steps:

1. Default to dry-run unless argument explicitly says "live"

2. **Run one scan cycle:**
   ```bash
   cd polymarket_flipper && python main.py --dry-run --once
   ```
   Or if live:
   ```bash
   cd polymarket_flipper && python main.py --once
   ```

3. **Show the output** — focus on:
   - Any BUNDLE ARB / MULTI-OUTCOME ARB / RESOLUTION LAG signals found
   - Trades placed (or simulated)
   - Current balance and exposure

4. **Show strategy state:**
   ```bash
   cd polymarket_flipper && python main.py --optimize
   ```

5. Reply with:
   - How many signals each strategy found
   - Any trades placed (with strategy, price, size, reason)
   - Whether any risk gates fired (daily cap, exposure limit, daily stop)
   - Current balance

If no signals: explain that's normal — guaranteed arbs appear a few times per day at most.
