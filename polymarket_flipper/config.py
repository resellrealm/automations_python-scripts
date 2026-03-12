"""
Configuration — £5/trade, £5/day Polymarket Flipper
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Risk limits (HARDCODED — do not override) ─────────────────────
RISK_PER_TRADE_GBP  = 5.0    # £5 max per trade
DAILY_LOSS_LIMIT_GBP = 5.0   # £5 max total daily loss (hard stop)
TARGET_TRADES_PER_DAY = 8    # aim for ~8 flips/day
GBP_TO_USDC         = 1.27   # approximate rate — update daily

RISK_PER_TRADE_USDC  = RISK_PER_TRADE_GBP * GBP_TO_USDC    # ~$6.35
DAILY_LOSS_USDC      = DAILY_LOSS_LIMIT_GBP * GBP_TO_USDC  # ~$6.35

# ── API credentials ───────────────────────────────────────────────
CLOB_API_URL        = os.getenv("CLOB_API_URL", "https://clob.polymarket.com")
GAMMA_API_URL       = os.getenv("GAMMA_API_URL", "https://gamma-api.polymarket.com")
PRIVATE_KEY         = os.getenv("POLYMARKET_PRIVATE_KEY", "")  # EVM private key
API_KEY             = os.getenv("POLYMARKET_API_KEY", "")
API_SECRET          = os.getenv("POLYMARKET_API_SECRET", "")
API_PASSPHRASE      = os.getenv("POLYMARKET_API_PASSPHRASE", "")

# ── Strategy toggles ──────────────────────────────────────────────
ENABLE_FLASH_CRASH  = True   # 86% ROI documented
ENABLE_ORDERBOOK    = True   # orderbook spread mismatch
ENABLE_NO_BIAS      = True   # 70% historical NO resolution

# ── Flash crash params (PROVEN — do not change) ───────────────────
FLASH_CRASH_THRESHOLD_PCT = 15.0   # % YES price drop to trigger
FLASH_BUNDLE_MAX          = 0.95   # buy when YES+NO sum ≤ this
FLASH_MIN_YES             = 0.05
FLASH_MAX_YES             = 0.90

# ── Orderbook mismatch params ─────────────────────────────────────
OB_MIN_SPREAD_EDGE   = 0.03   # ≥3¢ edge vs fair value
OB_IMBALANCE_RATIO   = 2.5    # bid size / ask size to signal direction
OB_SECONDS_TO_CLOSE_MIN = 10
OB_SECONDS_TO_CLOSE_MAX = 300

# ── NO bias params ────────────────────────────────────────────────
NO_MIN_PRICE         = 0.55
NO_MAX_PRICE         = 0.85
NO_MIN_VOLUME        = 5000
NO_MIN_LIQUIDITY     = 2000
NO_AVOID_HOURS       = 24
NO_SKIP_KEYWORDS     = ["btc", "bitcoin", "eth", "ethereum", "sol", "solana", "crypto", "price", "above", "below"]

# ── Polling ───────────────────────────────────────────────────────
POLL_INTERVAL_SECONDS = 30
