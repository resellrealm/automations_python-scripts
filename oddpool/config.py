"""
Oddpool — Cross-Platform Prediction Market Arbitrage Scanner
=============================================================
Finds matching events across Polymarket + Kalshi.
Buys YES on one side and NO on the other = guaranteed £1.00 payout.

Profit condition:
  YES_price_A + NO_price_B < 1.00 (before fees)
  i.e. cost of both legs < guaranteed payout
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Risk limits ────────────────────────────────────────────────
RISK_PER_ARB_GBP    = 5.0     # £5 per arb opportunity (split across 2 legs)
DAILY_LOSS_LIMIT_GBP = 5.0
GBP_TO_USD          = 1.27

RISK_PER_ARB_USD    = RISK_PER_ARB_GBP * GBP_TO_USD   # ~$6.35
DAILY_LOSS_USD      = DAILY_LOSS_LIMIT_GBP * GBP_TO_USD

# ── Min edge to execute (after all fees) ──────────────────────
MIN_NET_EDGE        = 0.02    # at least 2¢ profit per dollar after fees
MAX_BUNDLE_COST     = 0.97    # only enter if YES_A + NO_B ≤ 0.97

# ── Polymarket credentials ─────────────────────────────────────
POLY_PRIVATE_KEY    = os.getenv("POLYMARKET_PRIVATE_KEY", "")
POLY_API_KEY        = os.getenv("POLYMARKET_API_KEY", "")
POLY_API_SECRET     = os.getenv("POLYMARKET_API_SECRET", "")
POLY_API_PASSPHRASE = os.getenv("POLYMARKET_API_PASSPHRASE", "")
POLY_CLOB_URL       = "https://clob.polymarket.com"
POLY_GAMMA_URL      = "https://gamma-api.polymarket.com"

# ── Kalshi credentials ─────────────────────────────────────────
KALSHI_API_URL      = os.getenv("KALSHI_API_URL", "https://trading-api.kalshi.com/trade-api/v2")
KALSHI_KEY_ID       = os.getenv("KALSHI_KEY_ID", "")
KALSHI_PRIVATE_KEY  = os.getenv("KALSHI_PRIVATE_KEY_PATH", "kalshi_private.pem")

# ── Fees ───────────────────────────────────────────────────────
# Polymarket: 0% on non-crypto markets, 3.15% on crypto 15-min markets
# Kalshi: 0.07 × contracts × price × (1-price)
POLY_FEE_NONCRYPTO  = 0.00
POLY_FEE_CRYPTO     = 0.0315
KALSHI_FEE_MULT     = 0.07

# ── Matching ───────────────────────────────────────────────────
# Minimum word overlap to consider two market titles the same event
MATCH_MIN_SHARED_WORDS = 3
MATCH_MIN_WORD_LENGTH  = 4    # ignore short words when matching

# ── Polling ────────────────────────────────────────────────────
POLL_INTERVAL_SECONDS = 30
