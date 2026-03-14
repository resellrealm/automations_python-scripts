"""
Configuration — Polymarket Flipper (£30 starting bankroll)
===========================================================
Trade sizing is DYNAMIC — see bankroll.py.
All risk percentages are applied to current balance, not hardcoded £ amounts.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Starting bankroll ──────────────────────────────────────────────
STARTING_BALANCE_GBP  = 30.0   # your initial deposit
GBP_TO_USDC           = float(os.getenv("GBP_TO_USDC", "1.27"))  # update via .env

# ── Risk rules (% of balance) ──────────────────────────────────────
RISK_PCT_PER_TRADE    = 0.10   # 10% of balance per trade
DAILY_LOSS_PCT        = 0.10   # stop day if down 10% of today's starting balance
MAX_OPEN_TRADES       = 3      # max concurrent open positions
TARGET_TRADES_PER_DAY = 8

# ── API credentials ────────────────────────────────────────────────
CLOB_API_URL   = os.getenv("CLOB_API_URL", "https://clob.polymarket.com")
GAMMA_API_URL  = os.getenv("GAMMA_API_URL", "https://gamma-api.polymarket.com")
PRIVATE_KEY    = os.getenv("POLYMARKET_PRIVATE_KEY", "")
API_KEY        = os.getenv("POLYMARKET_API_KEY", "")
API_SECRET     = os.getenv("POLYMARKET_API_SECRET", "")
API_PASSPHRASE = os.getenv("POLYMARKET_API_PASSPHRASE", "")

# ── Strategy toggles ───────────────────────────────────────────────
ENABLE_FLASH_CRASH = True
ENABLE_ORDERBOOK   = True
ENABLE_NO_BIAS     = True

# ── Flash crash params ─────────────────────────────────────────────
FLASH_CRASH_THRESHOLD_PCT = 12.0   # % YES drop (lowered from 15 → more signals)
FLASH_BUNDLE_MAX          = 0.95   # bundle ≤ this = locked profit
FLASH_MIN_YES             = 0.05
FLASH_MAX_YES             = 0.90
FLASH_MIN_VOLUME          = 10_000  # $10k min volume (avoid thin markets)
FLASH_COOLDOWN_SECONDS    = 300     # don't re-enter same market within 5 min

# ── Orderbook mismatch params ──────────────────────────────────────
OB_MIN_EDGE           = 0.025  # ≥2.5¢ net edge after fee (was 3¢)
OB_IMBALANCE_RATIO    = 2.0    # lowered from 2.5x → more signals
OB_SECONDS_MIN        = 5
OB_SECONDS_MAX        = 600    # widened to 10 min (was 5 min)
OB_MIN_VOLUME         = 5_000

# ── NO bias params ─────────────────────────────────────────────────
NO_MIN_PRICE     = 0.55
NO_MAX_PRICE     = 0.85
NO_MIN_VOLUME    = 2_000   # lowered from $5k → more signals at small balance
NO_MIN_LIQUIDITY = 1_000   # lowered from $2k
NO_AVOID_HOURS   = 24
NO_SKIP_KEYWORDS = [
    "btc", "bitcoin", "eth", "ethereum", "sol", "solana",
    "crypto", "price", "above", "below", "will reach",
]

# ── Minimum edge filter (applies to all strategies) ───────────────
MIN_NET_EDGE = 0.025   # skip any trade with <2.5% net edge

# ── Polling ────────────────────────────────────────────────────────
POLL_INTERVAL_SECONDS = 30

# ── Taker fee ──────────────────────────────────────────────────────
TAKER_FEE = 0.0315  # 3.15% Polymarket taker fee
