"""
Resolution Lag Strategy
========================
Kalshi markets sometimes stay open after the real-world event is decided.

Example:
  - Fed announces "rates held" at 14:00 ET
  - Kalshi "Will Fed cut rates?" market still shows YES at 0.12 (not 0.00 yet)
  - Buy NO at 88¢ → guaranteed $1.00 at settlement = 12¢ profit risk-free

How to detect:
  - Market close_time has passed OR event is known from news
  - Price is not yet at 0.01 or 0.99 (hasn't fully repriced)
  - Volume/activity has dropped (no one trading = settlement soon)

Data sources checked:
  - Market close_time vs current UTC time
  - Price near 0 or near 1 but not quite (0.02-0.15 or 0.85-0.98)
  - For known results: Fed RSS feed, sports APIs (future enhancement)
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, List
import logging

from market_feed import KalshiMarket
from config import RESOLUTION_MIN_PRICE, RESOLUTION_MAX_PRICE

logger = logging.getLogger(__name__)


@dataclass
class ResolutionSignal:
    market:     KalshiMarket
    side:       str           # "yes" or "no"
    entry_price: float        # cents
    expected:   float         # 1.00 at resolution
    edge:       float         # expected - cost
    reason:     str
    confidence: float


class ResolutionLagDetector:
    """
    Detects markets where outcome appears decided but price hasn't hit 0 or 1 yet.

    Two triggers:
      1. close_time has passed (market expired, awaiting settlement)
      2. Price is in the "clearly resolved" zone (≥88¢ or ≤12¢) but not settled
    """

    def evaluate(self, market: KalshiMarket) -> Optional[ResolutionSignal]:
        if market.status != "open":
            return None
        if not market.yes_mid:
            return None

        now          = datetime.now(timezone.utc)
        time_expired = (
            market.close_time is not None and
            market.close_time < now
        )

        # YES looks like a near-certain winner (≥88¢ but not settled yet)
        if RESOLUTION_MIN_PRICE <= market.yes_mid <= RESOLUTION_MAX_PRICE:
            # Only trade post-close (to reduce false positives)
            if not time_expired:
                return None
            entry  = market.yes_ask / 100 if market.yes_ask else market.yes_mid
            edge   = round(1.0 - entry, 4)
            conf   = min(0.88, 0.60 + (market.yes_mid - RESOLUTION_MIN_PRICE) * 2)
            return ResolutionSignal(
                market       = market,
                side         = "yes",
                entry_price  = entry,
                expected     = 1.0,
                edge         = edge,
                confidence   = conf,
                reason=(
                    f"Resolution lag: {market.title[:60]} | "
                    f"YES={market.yes_mid:.2f} post-expiry | "
                    f"edge={edge*100:.1f}¢ | market expired: {time_expired}"
                )
            )

        # NO looks like a near-certain winner (YES ≤ 12¢)
        no_mid = round(1.0 - market.yes_mid, 4)
        if RESOLUTION_MIN_PRICE <= no_mid <= RESOLUTION_MAX_PRICE:
            if not time_expired:
                return None
            no_price = (100 - market.yes_ask) / 100 if market.yes_ask else no_mid
            edge     = round(1.0 - no_price, 4)
            conf     = min(0.88, 0.60 + (no_mid - RESOLUTION_MIN_PRICE) * 2)
            return ResolutionSignal(
                market       = market,
                side         = "no",
                entry_price  = no_price,
                expected     = 1.0,
                edge         = edge,
                confidence   = conf,
                reason=(
                    f"Resolution lag: {market.title[:60]} | "
                    f"NO={no_mid:.2f} post-expiry | "
                    f"edge={edge*100:.1f}¢ | market expired: {time_expired}"
                )
            )

        return None

    def scan(self, markets: List[KalshiMarket]) -> List[ResolutionSignal]:
        signals = []
        for m in markets:
            sig = self.evaluate(m)
            if sig:
                signals.append(sig)
        return signals
