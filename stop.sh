#!/bin/bash
# Stop all VPS services
REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

echo "Stopping all services..."
pkill -f "telegram_messenger/bot.py"  2>/dev/null && echo "  ✅ OpenClaw bot stopped"    || echo "  — OpenClaw bot was not running"
pkill -f "claude_agents/heartbeat.py" 2>/dev/null && echo "  ✅ Heartbeat stopped"       || echo "  — Heartbeat was not running"
pkill -f "polymarket_flipper/main.py" 2>/dev/null && echo "  ✅ Polymarket bot stopped"  || echo "  — Polymarket bot was not running"
pkill -f "kalshi_flipper/main.py"     2>/dev/null && echo "  ✅ Kalshi bot stopped"      || echo "  — Kalshi bot was not running"
pkill -f "oddpool/main.py"            2>/dev/null && echo "  ✅ Oddpool stopped"          || echo "  — Oddpool was not running"
echo "Done."
