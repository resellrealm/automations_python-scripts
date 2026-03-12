"""
Kalshi Flipper — Configuration
£5/trade, £5/day hard limit
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Risk limits (hardcoded) ───────────────────────────────────
RISK_PER_TRADE_GBP   = 5.0
DAILY_LOSS_LIMIT_GBP = 5.0
TARGET_TRADES_PER_DAY = 8
GBP_TO_USD           = 1.27

RISK_PER_TRADE_USD  = RISK_PER_TRADE_GBP * GBP_TO_USD    # ~$6.35
DAILY_LOSS_USD      = DAILY_LOSS_LIMIT_GBP * GBP_TO_USD  # ~$6.35

# ── Kalshi API credentials ────────────────────────────────────
# Get from: kalshi.com → Account → API Keys
# Auth uses RSA key pair — generate with:
#   openssl genrsa -out kalshi_private.pem 2048
#   openssl rsa -in kalshi_private.pem -pubout -out kalshi_public.pem
# Then upload kalshi_public.pem in Kalshi account settings
KALSHI_API_URL      = os.getenv("KALSHI_API_URL", "https://trading-api.kalshi.com/trade-api/v2")
KALSHI_KEY_ID       = os.getenv("KALSHI_KEY_ID", "")         # Key ID shown in account settings
KALSHI_PRIVATE_KEY  = os.getenv("KALSHI_PRIVATE_KEY_PATH", "kalshi_private.pem")

# ── Strategy toggles ──────────────────────────────────────────
ENABLE_NO_BUNDLE    = True   # Multi-outcome NO bundle arb (Reality TV, elections)
ENABLE_CROSS_ARB    = True   # Kalshi vs Polymarket same event
ENABLE_RESOLUTION   = True   # Buy winner before market settles

# ── NO bundle params ──────────────────────────────────────────
# Profit condition: sum of YES prices across all outcomes > 1.0
NO_BUNDLE_MIN_EDGE  = 0.01   # minimum 1¢ edge after fees to enter
NO_BUNDLE_MIN_OUTCOMES = 3   # only run on markets with 3+ outcomes

# ── Cross-platform arb params ─────────────────────────────────
CROSS_ARB_MIN_EDGE  = 0.04   # 4¢ min gap between Kalshi and Polymarket price

# ── Resolution lag params ─────────────────────────────────────
RESOLUTION_MIN_PRICE = 0.88  # only buy if winner is below this (leaving room for profit)
RESOLUTION_MAX_PRICE = 0.97  # don't buy if already near $1.00

# ── Kalshi fee formula ────────────────────────────────────────
# fee = 0.07 × contracts × price × (1 - price)
# Max fee at 50/50 = 1.75¢/contract
# At 80¢: fee = 0.07 × 1 × 0.80 × 0.20 = 1.12¢/contract (very cheap)
KALSHI_FEE_MULTIPLIER = 0.07

# ── Polling ───────────────────────────────────────────────────
POLL_INTERVAL_SECONDS = 45
