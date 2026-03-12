"""
Orderbook Mismatch Strategy
============================
Detects when order book is heavily imbalanced (one side dominates)
combined with a spread that gives a real edge after the 3.15% taker fee.

Logic:
  - Heavy bid imbalance (bid_vol >> ask_vol) → price likely to rise → BUY
  - Entry when spread creates ≥3¢ edge vs fair value
  - Only enter T-10s to T-300s before close (directional locked in)
  - Fee-aware: only enter if edge > 3.15% taker cost

Edge source: Retail market orders hitting stale limit orders near window close.
"""
from dataclasses import dataclass
from typing import Optional
import logging

from market_feed import TokenInfo, bid_ask_volume, fetch_orderbook
from config import (
    OB_MIN_SPREAD_EDGE, OB_IMBALANCE_RATIO,
    OB_SECONDS_TO_CLOSE_MIN, OB_SECONDS_TO_CLOSE_MAX,
)

logger = logging.getLogger(__name__)

TAKER_FEE = 0.0315  # 3.15% Polymarket taker fee


@dataclass
class OrderbookSignal:
    token:       TokenInfo
    direction:   str        # "BUY"
    fair_value:  float      # estimated fair price
    entry_price: float      # best_ask (lift to fill)
    edge:        float      # after fee
    imbalance:   float      # bid_vol / ask_vol
    seconds_left: float
    confidence:  float
    reason:      str


class OrderbookMismatchDetector:
    """
    Fires when heavy imbalance + spread creates net-positive edge after fees.
    Target: ~4-6 signals/day on liquid crypto markets.
    """

    def evaluate(self, token: TokenInfo, seconds_left: float) -> Optional[OrderbookSignal]:
        if not (OB_SECONDS_TO_CLOSE_MIN <= seconds_left <= OB_SECONDS_TO_CLOSE_MAX):
            return None

        # Re-fetch live orderbook for freshest data
        book = fetch_orderbook(token.token_id)
        if not book:
            return None

        bid_vol, ask_vol = bid_ask_volume(book, levels=5)
        if ask_vol <= 0:
            return None

        imbalance = bid_vol / ask_vol

        if imbalance < OB_IMBALANCE_RATIO:
            return None  # not enough directional pressure

        # Fair value estimate from imbalance weighting
        mid   = token.mid_price
        # Heavy bids → fair value slightly above mid
        fair  = round(mid + (mid * 0.01 * min(imbalance - OB_IMBALANCE_RATIO, 3)), 4)
        entry = token.best_ask

        if entry <= 0:
            return None

        edge_gross = fair - entry
        edge_net   = edge_gross - (entry * TAKER_FEE)

        if edge_net < OB_MIN_SPREAD_EDGE:
            logger.debug(
                f"OB mismatch: imbalance={imbalance:.1f} but edge_net={edge_net:.4f} < {OB_MIN_SPREAD_EDGE}"
            )
            return None

        confidence = min(0.80, 0.55 + (imbalance / 10) + (edge_net * 2))

        return OrderbookSignal(
            token        = token,
            direction    = "BUY",
            fair_value   = fair,
            entry_price  = round(entry + 0.005, 4),  # lift 0.5¢ to fill
            edge         = round(edge_net, 4),
            imbalance    = round(imbalance, 2),
            seconds_left = seconds_left,
            confidence   = confidence,
            reason=(
                f"OB imbalance {imbalance:.1f}x | "
                f"fair={fair:.3f} entry={entry:.3f} | "
                f"net edge={edge_net*100:.2f}¢ after {TAKER_FEE*100:.1f}% fee | "
                f"{seconds_left:.0f}s to close"
            )
        )
