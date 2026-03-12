"""
Systematic NO Bias Strategy
============================
~70% of Polymarket markets historically resolve NO.
Source: On-chain analysis of 95M+ transactions (Apr 2024 – Dec 2025)

Best markets: political milestones, regulatory events, company announcements.
Avoid: crypto price direction, markets near resolution.
"""
from dataclasses import dataclass
from typing import Optional
import logging

from market_feed import TokenInfo
from config import (
    NO_MIN_PRICE, NO_MAX_PRICE, NO_MIN_VOLUME,
    NO_MIN_LIQUIDITY, NO_AVOID_HOURS, NO_SKIP_KEYWORDS,
)

logger = logging.getLogger(__name__)


@dataclass
class NOBiasSignal:
    token:      TokenInfo
    yes_mid:    float
    no_mid:     float
    confidence: float
    reason:     str


class NOBiasDetector:
    """
    Buys NO on markets where retail over-estimates YES probability.
    70% historical NO resolution creates systematic edge.
    """

    def evaluate(self, token: TokenInfo) -> Optional[NOBiasSignal]:
        q = token.question.lower()

        # Skip crypto/price markets (too efficient, latency-sensitive)
        if any(kw in q for kw in NO_SKIP_KEYWORDS):
            return None

        yes_mid = token.mid_price
        no_mid  = round(1.0 - yes_mid, 4)

        # Filter to sweet spot
        if not (NO_MIN_PRICE <= no_mid <= NO_MAX_PRICE):
            return None

        # Liquidity gate
        if token.liquidity < NO_MIN_LIQUIDITY:
            return None

        # Volume gate
        if token.volume_24h < NO_MIN_VOLUME:
            return None

        # Skip markets near resolution
        if token.end_time:
            from datetime import datetime, timezone
            hours_left = (token.end_time - datetime.now(timezone.utc)).total_seconds() / 3600
            if hours_left < NO_AVOID_HOURS:
                return None

        # Confidence: higher when YES is lower (more overpriced)
        base  = 0.55
        bonus = max(0, (0.45 - yes_mid) * 0.8)
        liq_b = min(0.10, token.liquidity / 100000)
        conf  = min(0.88, base + bonus + liq_b)

        return NOBiasSignal(
            token      = token,
            yes_mid    = yes_mid,
            no_mid     = no_mid,
            confidence = conf,
            reason=(
                f"NOBias: YES={yes_mid:.2f}→NO={no_mid:.2f} | "
                f"70% historical NO resolution | vol=${token.volume_24h:,.0f}"
            )
        )
