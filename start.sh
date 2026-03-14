#!/bin/bash
# ============================================================
# Start all VPS services
# Usage: bash start.sh
# ============================================================

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

echo ""
echo "======================================================"
echo "  Starting OpenClaw VPS Services"
echo "======================================================"
echo ""

# Check .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env not found. Run: bash setup.sh"
    exit 1
fi

# Load .env to check for token
source .env 2>/dev/null || true

if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ "$TELEGRAM_BOT_TOKEN" = "your_bot_token_here" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN not set in .env"
    echo "   Edit .env first: nano .env"
    exit 1
fi

# Kill any already-running instances
echo "Stopping any existing processes..."
pkill -f "telegram_messenger/bot.py" 2>/dev/null || true
pkill -f "claude_agents/heartbeat.py" 2>/dev/null || true
sleep 1

# Start OpenClaw Telegram bot
echo "Starting OpenClaw bot..."
nohup python telegram_messenger/bot.py \
    >> telegram_messenger/openclaw.log 2>&1 &
BOT_PID=$!
echo "  ✅ OpenClaw bot started (PID $BOT_PID)"

# Start heartbeat daemon (monitors + restarts trading bots)
echo "Starting heartbeat daemon..."
nohup python claude_agents/heartbeat.py \
    >> heartbeat.log 2>&1 &
HB_PID=$!
echo "  ✅ Heartbeat started (PID $HB_PID)"

sleep 2

echo ""
echo "======================================================"
echo "  All services started!"
echo ""
echo "  Check logs:"
echo "    tail -f telegram_messenger/openclaw.log"
echo "    tail -f heartbeat.log"
echo ""
echo "  Check running:  bash check.sh"
echo "  Stop all:       bash stop.sh"
echo "======================================================"
echo ""
