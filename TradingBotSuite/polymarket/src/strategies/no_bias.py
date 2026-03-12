"""
Systematic NO Bias Strategy
============================
Edge: ~70% of Polymarket markets historically resolve NO.
Source: On-chain analysis of 95M+ transactions (Apr 2024 – Dec 2025)

Why it works:
  - Markets are created for events that *might* happen — most don't
  - Long-shot bias: retail traders overbet YES on unlikely events
  - Creates consistent edge on NO side in non-crypto, non-election markets

Best markets:  political milestones, regulatory events, company announcements
Avoid:         crypto price direction (efficient), markets near resolution

Parameters:
  min_no_price: 0.55  — at least 55¢ for NO (≈45% implied prob)
  max_no_price: 0.85  — avoid near-certain NO (no edge, low return)
  avoid_within: 24h   — don't enter within 24h of resolution
"""

from typing import List, Optional
from datetime import datetime, timezone, timedelta
from loguru import logger

from src.strategies.base import BaseStrategy, Signal, MarketData
from src.config import config


# ── Parameters ──────────────────────────────────────────────────
MIN_NO_PRICE    = 0.55   # floor: YES must have some real chance
MAX_NO_PRICE    = 0.85   # ceiling: don't buy near-certain NO
MIN_VOLUME_24H  = 5000   # only liquid markets
MIN_LIQUIDITY   = 2000
AVOID_HOURS     = 24     # skip markets resolving within this many hours
POSITION_SIZE   = 0.02   # 2% of total capital per trade
SKIP_KEYWORDS   = [      # these markets are too efficient
    "btc", "bitcoin", "eth", "ethereum", "sol", "solana",
    "crypto", "price", "above", "below",
]
# ────────────────────────────────────────────────────────────────


class NOBiasStrategy(BaseStrategy):
    """
    Bets NO on markets where retail over-estimates the probability of YES.
    70% historical NO resolution rate creates systematic edge.
    """

    def __init__(self):
        super().__init__(
            name="NOBias",
            config={
                "min_no_price":   MIN_NO_PRICE,
                "max_no_price":   MAX_NO_PRICE,
                "min_volume":     MIN_VOLUME_24H,
                "min_liquidity":  MIN_LIQUIDITY,
                "avoid_hours":    AVOID_HOURS,
                "position_size":  POSITION_SIZE,
            }
        )
        self.total_capital = getattr(config.trading, "total_capital", 1000.0)

    def get_required_data(self) -> List[str]:
        return ["best_bid", "best_ask", "mid_price", "volume", "liquidity"]

    def analyze(self, market_data: List[MarketData]) -> List[Signal]:
        signals = []

        for token in market_data:
            signal = self._evaluate(token)
            if signal:
                signals.append(signal)

        return signals

    def _evaluate(self, token: MarketData) -> Optional[Signal]:
        """Evaluate a single token for NO bias opportunity."""
        question = token.question.lower()

        # Skip crypto price markets (too efficient)
        if any(kw in question for kw in SKIP_KEYWORDS):
            return None

        # We want to BUY NO — so we look at the NO token's ask price
        # In Polymarket, NO token price = 1 - YES price approximately
        # If YES mid = 0.35, NO mid ≈ 0.65
        yes_mid = token.mid_price
        no_mid  = 1.0 - yes_mid   # implied NO price

        # Filter: NO must be in the sweet spot (55¢–85¢)
        if not (MIN_NO_PRICE <= no_mid <= MAX_NO_PRICE):
            return None

        # Liquidity filter
        if token.liquidity < MIN_LIQUIDITY:
            return None

        # Volume filter
        if token.volume < MIN_VOLUME_24H:
            return None

        # Skip markets near resolution
        if self._near_resolution(token):
            return None

        # Position size = 2% of capital
        size = (self.total_capital * POSITION_SIZE) / no_mid

        confidence = self._calculate_confidence(yes_mid, token)

        return Signal(
            strategy_name=self.name,
            token_id=token.token_id,
            market_id=token.market_id,
            side="BUY",
            size=round(size, 2),
            price=round(no_mid + 0.01, 3),
            confidence=confidence,
            reason=(
                f"NO bias: YES={yes_mid:.2f} implies NO={no_mid:.2f} | "
                f"70% historical NO resolution rate | vol=${token.volume:,.0f}"
            )
        )

    def _near_resolution(self, token: MarketData) -> bool:
        """Return True if market resolves within AVOID_HOURS."""
        end_date = token.extra.get("end_date")
        if not end_date:
            return False
        try:
            if isinstance(end_date, str):
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            else:
                end_dt = end_date
            hours_left = (end_dt - datetime.now(timezone.utc)).total_seconds() / 3600
            return hours_left < AVOID_HOURS
        except Exception:
            return False

    def _calculate_confidence(self, yes_mid: float, token: MarketData) -> float:
        """Higher confidence when YES price is lower (more overpriced YES)."""
        # YES at 0.20 → high confidence in NO (people betting unlikely event)
        # YES at 0.45 → lower confidence (more balanced)
        base = 0.55
        overestimation_bonus = max(0, (0.45 - yes_mid) * 0.8)
        liquidity_bonus = min(0.1, token.liquidity / 100000)
        return min(0.90, base + overestimation_bonus + liquidity_bonus)
