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
MAX_OPEN_TRADES       = 6      # max concurrent open positions
MAX_TRADES_PER_DAY    = 30     # hard daily cap — micro sizing means more trades per day
MAX_HOLD_HOURS        = 48     # force-close any position held longer than this
MAX_EXPOSURE_PCT      = 0.70   # total open position value never exceeds 70% of balance
MAX_EXPOSURE_GBP      = 15.00  # hard £15 cap on total open positions at any time
MULTIPLIER_MIN        = 0.5    # strategy optimizer multiplier lower bound
MULTIPLIER_MAX        = 2.0    # strategy optimizer multiplier upper bound
COOLDOWN_MINUTES      = 60     # pause after daily stop fires (prevents revenge trading)

# ── API credentials ────────────────────────────────────────────────
CLOB_API_URL   = os.getenv("CLOB_API_URL", "https://clob.polymarket.com")
GAMMA_API_URL  = os.getenv("GAMMA_API_URL", "https://gamma-api.polymarket.com")
PRIVATE_KEY    = os.getenv("POLYMARKET_PRIVATE_KEY", "")
API_KEY        = os.getenv("POLYMARKET_API_KEY", "")
API_SECRET     = os.getenv("POLYMARKET_API_SECRET", "")
API_PASSPHRASE = os.getenv("POLYMARKET_API_PASSPHRASE", "")

# ── Strategy toggles ───────────────────────────────────────────────
ENABLE_FLASH_CRASH = True    # now handled by bundle_arb.py
ENABLE_NO_BIAS     = True

# ── Bundle arb params ──────────────────────────────────────────────
BUNDLE_MAX_NON_CRYPTO = 0.97  # enter when bundle ≤ 0.97 on non-crypto (0% fee)
BUNDLE_MAX_CRYPTO     = 0.93  # enter when bundle ≤ 0.93 on crypto (up to 3.15% fee)
BUNDLE_MIN_VOLUME     = 5_000
BUNDLE_MIN_LIQUIDITY  = 1_000

# ── Resolution lag params ──────────────────────────────────────────
LAG_MIN_WIN_PRICE      = 0.88  # only enter when winner is ≥88¢
LAG_MAX_WIN_PRICE      = 0.99
LAG_MIN_OVERDUE_MINS   = 5
LAG_MAX_OVERDUE_HOURS  = 48
LAG_MIN_VOLUME         = 1_000

# ── NO bias params ─────────────────────────────────────────────────
NO_MIN_PRICE     = 0.55
NO_MAX_PRICE     = 0.85
NO_MIN_VOLUME    = 2_000
NO_MIN_LIQUIDITY = 1_000
NO_AVOID_HOURS   = 24
NO_SKIP_KEYWORDS = [
    "btc", "bitcoin", "eth", "ethereum", "sol", "solana",
    "crypto", "price", "above", "below", "will reach",
]

# ── Polling — every 15s (opportunities last avg 2.7s, we catch slower ones)
POLL_INTERVAL_SECONDS = 15

# ── Strategy thresholds ───────────────────────────────────────────
FLASH_CRASH_THRESHOLD_PCT = 15.0
FLASH_CRASH_MIN_CONFIDENCE = 0.7
ORDERBOOK_IMBALANCE_RATIO = 3.0
RESOLUTION_LAG_WINDOW_HOURS = 24
NO_BIAS_MIN_CONFIDENCE = 0.6

# ── Flash crash params ────────────────────────────────────────────
FLASH_BUNDLE_MAX = 0.95
FLASH_MIN_YES = 0.20
FLASH_MAX_YES = 0.80
FLASH_MIN_VOLUME = 10_000
FLASH_COOLDOWN_SECONDS = 300

# ── Orderbook mismatch params ─────────────────────────────────────
ORDERBOOK_MIN_VOLUME = 5_000
ORDERBOOK_MIN_SPREAD = 0.02
ORDERBOOK_MAX_SPREAD = 0.15

# ── NO bias params ────────────────────────────────────────────────
NO_BIAS_MIN_YES_PRICE = 0.55
NO_BIAS_MAX_YES_PRICE = 0.85
NO_BIAS_MIN_VOLUME = 2_000

# ── Orderbook mismatch params ─────────────────────────────────────
OB_MIN_EDGE = 0.02
OB_IMBALANCE_RATIO = 2.0
OB_SECONDS_MIN = 60
OB_SECONDS_MAX = 3600
OB_MIN_VOLUME = 5_000

# ── Taker fee ──────────────────────────────────────────────────────
TAKER_FEE = 0.0315  # 3.15% worst case (crypto markets at 50% price point)

# ── API validation ────────────────────────────────────────────────
def validate_api_keys() -> bool:
    """Check that required API credentials are set."""
    missing = []
    if not PRIVATE_KEY:
        missing.append("POLYMARKET_PRIVATE_KEY")
    if not API_KEY:
        missing.append("POLYMARKET_API_KEY")
    if not API_SECRET:
        missing.append("POLYMARKET_API_SECRET")
    if not API_PASSPHRASE:
        missing.append("POLYMARKET_API_PASSPHRASE")
    if missing:
        import logging
        logging.getLogger(__name__).error(f"Missing API keys: {', '.join(missing)}")
        return False
    return True
