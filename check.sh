#!/bin/bash
# Check which VPS services are running
echo ""
echo "======================================================"
echo "  VPS Service Status"
echo "======================================================"

check() {
    local name="$1"
    local pattern="$2"
    if pgrep -f "$pattern" > /dev/null 2>&1; then
        PID=$(pgrep -f "$pattern" | head -1)
        echo "  🟢 $name (PID $PID)"
    else
        echo "  🔴 $name — NOT RUNNING"
    fi
}

check "OpenClaw Bot"     "telegram_messenger/bot.py"
check "Heartbeat"        "claude_agents/heartbeat.py"
check "Polymarket Bot"   "polymarket_flipper/main.py"
check "Kalshi Bot"       "kalshi_flipper/main.py"
check "Oddpool"          "oddpool/main.py"

echo ""
echo "Recent OpenClaw log:"
tail -5 telegram_messenger/openclaw.log 2>/dev/null || echo "  (no log yet)"
echo "======================================================"
echo ""
