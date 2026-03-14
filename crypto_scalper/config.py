"""
Configuration — Crypto Scalper
================================
Confidence-tiered sizing: £0.50 / £0.75 / £1.00 / £1.50
All API credentials loaded from .env — never hardcoded.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Exchange ─────────────────────────────────────────────────────────
EXCHANGE_ID        = "binance"
BINANCE_API_KEY    = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
USE_SANDBOX        = os.getenv("BINANCE_SANDBOX", "false").lower() == "true"

# ── Symbols to scan ──────────────────────────────────────────────────
SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT",
    "XRP/USDT", "ADA/USDT", "DOGE/USDT", "AVAX/USDT",
]

# ── Timeframes ───────────────────────────────────────────────────────
TIMEFRAME_FAST = "5m"
TIMEFRAME_SLOW = "15m"
CANDLES_NEEDED = 50

# ── Indicators ───────────────────────────────────────────────────────
RSI_SHORT               = 6
RSI_MID                 = 12
RSI_LONG                = 24
BB_PERIOD               = 20
BB_STD                  = 2.0
ATR_PERIOD              = 14
VOLUME_SURGE_MULTIPLIER = 2.0

RSI_OVERSOLD   = 30
RSI_OVERBOUGHT = 70

# ── Confidence → position sizing (min_conf, max_conf, £size) ─────────
SIZING_TIERS = [
    (0.45, 0.60, 0.50),
    (0.60, 0.75, 0.75),
    (0.75, 0.90, 1.00),
    (0.90, 1.01, 1.50),
]
MIN_CONFIDENCE = 0.45
GBP_TO_USDT    = float(os.getenv("GBP_TO_USDT", "1.27"))

# ── Risk management ──────────────────────────────────────────────────
ATR_SL_MULTIPLIER  = 2.0
ATR_TP_MULTIPLIER  = 3.0
MAX_OPEN_TRADES    = 5
MAX_TRADES_PER_DAY = 30
DAILY_LOSS_GBP     = 5.00
MAX_HOLD_MINUTES   = 120
COOLDOWN_MINUTES   = 30

# ── Indicator weights (must sum to 1.0) ──────────────────────────────
WEIGHTS = {
    "rsi_short": 0.20,
    "rsi_mid":   0.20,
    "rsi_long":  0.10,
    "bb":        0.20,
    "vwap":      0.20,
    "volume":    0.10,
}
assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "Weights must sum to 1.0"

# ── Polling ──────────────────────────────────────────────────────────
POLL_INTERVAL_SECONDS = 30

# ── Logging ──────────────────────────────────────────────────────────
LOG_FILE = "crypto_scalper.log"


def validate_api_keys() -> bool:
    missing = []
    if not BINANCE_API_KEY:
        missing.append("BINANCE_API_KEY")
    if not BINANCE_API_SECRET:
        missing.append("BINANCE_API_SECRET")
    if missing:
        import logging
        logging.getLogger(__name__).error(f"Missing API keys: {', '.join(missing)}")
        return False
    return True
