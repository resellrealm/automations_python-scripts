#!/bin/bash
# ============================================================
# VPS Setup — Run this ONCE after cloning the repo
# Usage: bash setup.sh
# ============================================================
set -e

echo ""
echo "======================================================"
echo "  OpenClaw VPS Setup"
echo "======================================================"
echo ""

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

# 1. Install Python dependencies
echo "[1/4] Installing Python packages..."
pip install -q \
    python-telegram-bot \
    requests \
    python-dotenv \
    selenium \
    undetected-chromedriver \
    aiohttp

echo "      Done."

# 2. Create .env from example if it doesn't exist
echo "[2/4] Setting up .env..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "  ⚠️  .env created from template."
    echo "  ➡  You MUST fill in these values before starting:"
    echo ""
    echo "     nano .env"
    echo ""
    echo "  Required:"
    echo "     TELEGRAM_BOT_TOKEN  — from @BotFather"
    echo "     TELEGRAM_USER_ID    — from @userinfobot"
    echo "     AI_API_KEY          — your Moonshot/Kimi API key"
    echo "                           (https://platform.moonshot.cn)"
    echo ""
else
    echo "      .env already exists — skipping."
fi

# 3. Create log directory
echo "[3/4] Creating log dirs..."
mkdir -p vps_tasks
touch heartbeat.log
touch telegram_messenger/openclaw.log
echo "      Done."

# 4. Verify claude CLI
echo "[4/4] Checking Claude CLI..."
if command -v claude &>/dev/null; then
    echo "      Claude CLI found: $(which claude)"
else
    echo ""
    echo "  ⚠️  Claude CLI not found. Install it:"
    echo "     curl -fsSL https://claude.ai/install.sh | bash"
    echo "     claude login"
    echo ""
fi

echo ""
echo "======================================================"
echo "  Setup complete!"
echo ""
echo "  Next steps:"
echo "  1. Fill in your .env:    nano .env"
echo "  2. Start everything:     bash start.sh"
echo "  3. Check it's running:   bash check.sh"
echo "======================================================"
echo ""
