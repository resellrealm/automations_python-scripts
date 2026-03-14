"""
Crypto Momentum Strategy — 5-min & 15-min Polymarket Markets
=============================================================
Polymarket runs continuous Up/Down binary markets for:
  5-min:  BTC, ETH, SOL, XRP, DOGE, BNB, HYPE (288 markets/coin/day)
  15-min: BTC, ETH, SOL, XRP               (96 markets/coin/day)

Edge: YES/NO prices hover near 0.50. When momentum pushes them to
0.44 or lower (NO heavily favoured) or 0.56+ (YES heavily favoured),
there's a directional signal worth fading or following.

Two sub-strategies:
  1. Bundle Arb  — if YES + NO < 0.97 after fees → guaranteed profit
  2. Momentum    — if YES drifts to 0.56+ (strong up) or 0.44- (strong down)
                   → bet WITH momentum (crowd usually right in 5-min windows)

Supported coins and their Polymarket slugs:
  BTC   → bitcoin-5m / bitcoin-15m
  ETH   → ethereum-5m / ethereum-15m
  SOL   → solana-5m / solana-15m
  XRP   → xrp-5m / xrp-15m
  DOGE  → dogecoin-5m         (5-min only)
  BNB   → bnb-5m              (5-min only)
  HYPE  → hyperliquid-5m      (5-min only)

NOTE: Polymarket minimum order is $5 USDC (~£3.94).
Sub-£4 trades will be rejected by the CLOB.
At £1 max sizing, trades are below minimum — use --dry-run until
minimum is raised or budget allows £4+ per trade.
"""
from dataclasses import dataclass
from typing import Optional
import logging

from market_feed import TokenInfo
from config import TAKER_FEE

logger = logging.getLogger(__name__)

# Coins with 5-min markets
CRYPTO_5MIN_COINS = ["BTC", "ETH", "SOL", "XRP", "DOGE", "BNB", "HYPE"]

# Coins with 15-min markets
CRYPTO_15MIN_COINS = ["BTC", "ETH", "SOL", "XRP"]

# Keywords to detect crypto 5-min / 15-min markets by question text
FIVEMIN_KEYWORDS  = ["5-minute", "5 minute", "5min", "5-min up or down"]
FIFTEENMIN_KEYWORDS = ["15-minute", "15 minute", "15min", "15-min up or down"]

# Momentum threshold — YES must drift this far from 0.50 to trigger
MOMENTUM_THRESHOLD = 0.56   # YES >= 0.56 → bet YES (strong up momentum)
                             # YES <= 0.44 → bet NO  (strong down momentum)

# Bundle arb threshold for crypto markets (higher fee than standard)
BUNDLE_MAX_CRYPTO = 0.97    # YES + NO must be <= 0.97 after 3.15% fee

# Min confidence to trade a momentum signal
MIN_MOMENTUM_CONF = 0.45


@dataclass
class CryptoMomentumSignal:
    market_id:   str
    question:    str
    timeframe:   str            # "5m" or "15m"
    coin:        str            # BTC, ETH, etc.
    direction:   str            # "YES" or "NO"
    yes_price:   float
    no_price:    float
    signal_type: str            # "bundle_arb" or "momentum"
    confidence:  float          # 0.0 – 1.0
    reason:      str


class CryptoMomentumDetector:
    """
    Scans 5-minute and 15-minute crypto markets for:
      1. Bundle arb (YES + NO < $0.97)
      2. Momentum drift (YES > 0.56 or YES < 0.44)
    """

    def _detect_timeframe(self, question: str) -> Optional[str]:
        q = question.lower()
        if any(kw in q for kw in FIVEMIN_KEYWORDS):
            return "5m"
        if any(kw in q for kw in FIFTEENMIN_KEYWORDS):
            return "15m"
        return None

    def _detect_coin(self, question: str) -> Optional[str]:
        q = question.upper()
        for coin in CRYPTO_5MIN_COINS:
            if coin in q:
                return coin
        return None

    def evaluate_pair(
        self,
        yes_token: TokenInfo,
        no_token:  TokenInfo,
    ) -> Optional[CryptoMomentumSignal]:
        """
        Evaluate a YES/NO pair from a crypto 5-min or 15-min market.
        Returns a signal if bundle arb or momentum threshold is hit.
        """
        question  = yes_token.question
        timeframe = self._detect_timeframe(question)
        if not timeframe:
            return None

        coin = self._detect_coin(question)
        if not coin:
            return None

        yes_price = yes_token.best_ask
        no_price  = no_token.best_ask

        if yes_price <= 0 or no_price <= 0:
            return None

        # ── Bundle arb check ─────────────────────────────────────────
        bundle = yes_price + no_price
        fee_cost = bundle * TAKER_FEE
        net_bundle = bundle + fee_cost

        if net_bundle < BUNDLE_MAX_CRYPTO:
            margin = round(1.0 - net_bundle, 4)
            return CryptoMomentumSignal(
                market_id   = yes_token.market_id,
                question    = question[:80],
                timeframe   = timeframe,
                coin        = coin,
                direction   = "BOTH",   # buy both legs
                yes_price   = yes_price,
                no_price    = no_price,
                signal_type = "bundle_arb",
                confidence  = 1.0,       # guaranteed
                reason      = (
                    f"CryptoBundle: {coin} {timeframe} | "
                    f"bundle={bundle:.3f} net={net_bundle:.3f} margin={margin*100:.2f}%"
                ),
            )

        # ── Momentum check ────────────────────────────────────────────
        mid = yes_token.mid_price
        if mid <= 0:
            return None

        if mid >= MOMENTUM_THRESHOLD:
            # Strong YES momentum — bet YES
            drift      = mid - 0.50
            confidence = min(0.85, MIN_MOMENTUM_CONF + drift * 2)
            return CryptoMomentumSignal(
                market_id   = yes_token.market_id,
                question    = question[:80],
                timeframe   = timeframe,
                coin        = coin,
                direction   = "YES",
                yes_price   = yes_price,
                no_price    = no_price,
                signal_type = "momentum",
                confidence  = round(confidence, 3),
                reason      = (
                    f"CryptoMomentum: {coin} {timeframe} | "
                    f"YES={mid:.3f} drifted {drift*100:.1f}% above 0.50 → follow momentum"
                ),
            )

        anti_threshold = 1.0 - MOMENTUM_THRESHOLD  # 0.44
        if mid <= anti_threshold:
            # Strong NO momentum — bet NO
            drift      = 0.50 - mid
            confidence = min(0.85, MIN_MOMENTUM_CONF + drift * 2)
            return CryptoMomentumSignal(
                market_id   = yes_token.market_id,
                question    = question[:80],
                timeframe   = timeframe,
                coin        = coin,
                direction   = "NO",
                yes_price   = yes_price,
                no_price    = no_price,
                signal_type = "momentum",
                confidence  = round(confidence, 3),
                reason      = (
                    f"CryptoMomentum: {coin} {timeframe} | "
                    f"YES={mid:.3f} drifted {drift*100:.1f}% below 0.50 → follow NO"
                ),
            )

        return None
