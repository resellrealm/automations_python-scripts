#!/bin/bash
# ============================================================
# Cron Setup — Polymarket Flipper Trade Reports
# ============================================================
# Run this script ONCE to print the crontab lines to add.
# Then do: crontab -e  and paste the lines shown below.
#
# Usage: bash reports/cron_setup.sh
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLIPPER_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON="$(which python3 || which python)"

echo ""
echo "======================================================"
echo "  Polymarket Flipper — Crontab Lines"
echo "======================================================"
echo ""
echo "Add these lines to your crontab (run: crontab -e):"
echo ""
echo "# Daily report at midnight (reads yesterday's trades, sends Telegram, moves file)"
echo "0 0 * * * cd $FLIPPER_DIR && $PYTHON -m reports.daily_report >> logs/cron.log 2>&1"
echo ""
echo "# Weekly report on Sunday midnight (aggregates week, sends Telegram, archives)"
echo "0 0 * * 0 cd $FLIPPER_DIR && $PYTHON -m reports.weekly_report >> logs/cron.log 2>&1"
echo ""
echo "======================================================"
echo ""
echo "Required .env variables for Telegram:"
echo "  TELEGRAM_BOT_TOKEN=your_bot_token"
echo "  TELEGRAM_USER_ID=your_chat_id"
echo ""
echo "Test now:"
echo "  cd $FLIPPER_DIR && $PYTHON -m reports.daily_report"
echo "  cd $FLIPPER_DIR && $PYTHON -m reports.weekly_report"
echo ""
