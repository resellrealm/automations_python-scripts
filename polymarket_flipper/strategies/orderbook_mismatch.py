"""
Orderbook Mismatch Strategy
============================
Detects heavy bid imbalance + spread edge after 3.15% taker fee.

Changes from original:
  - Imbalance threshold 2.5x → 2.0x (more signals)
  - Time window widened to 5–600s (was 10–300s)
  - Fair value uses volume-weighted top 5 levels (not just ratio boost)
  - Minimum edge lowered to 2.5¢ (was 3¢) — still well above fee
"""
from dataclasses import dataclass
from typing import Optional
import logging

from market_feed import TokenInfo, bid_ask_volume, fetch_orderbook
from config import (
    OB_MIN_EDGE, OB_IMBALANCE_RATIO,
    OB_SECONDS_MIN, OB_SECONDS_MAX, OB_MIN_VOLUME, TAKER_FEE,
)

logger = logging.getLogger(__name__)


@dataclass
class OrderbookSignal:
    token:        TokenInfo
    direction:    str
    fair_value:   float
    entry_price:  float
    edge:         float
    imbalance:    float
    seconds_left: float
    confidence:   float
    reason:       str


class OrderbookMismatchDetector:
    def evaluate(self, token: TokenInfo, seconds_left: float) -> Optional[OrderbookSignal]:
        if not (OB_SECONDS_MIN <= seconds_left <= OB_SECONDS_MAX):
            return None

        if token.volume_24h < OB_MIN_VOLUME:
            return None

        book = fetch_orderbook(token.token_id)
        if not book:
            return None

        bid_vol, ask_vol = bid_ask_volume(book, levels=5)
        if ask_vol <= 0:
            return None

        imbalance = bid_vol / ask_vol
        if imbalance < OB_IMBALANCE_RATIO:
            return None

        # Volume-weighted fair value from top 5 levels
        bids = book.get("bids", [])[:5]
        asks = book.get("asks", [])[:5]
        total_bid_w = sum(float(b["price"]) * float(b.get("size", 0)) for b in bids)
        total_ask_w = sum(float(a["price"]) * float(a.get("size", 0)) for a in asks)
        total_w     = total_bid_w + total_ask_w
        fair = round(total_bid_w / total_w, 4) if total_w > 0 else token.mid_price

        entry = token.best_ask
        if entry <= 0:
            return None

        edge_gross = fair - entry
        edge_net   = edge_gross - (entry * TAKER_FEE)

        if edge_net < OB_MIN_EDGE:
            logger.debug(f"OB: imbalance={imbalance:.1f}x but edge_net={edge_net:.4f} < {OB_MIN_EDGE}")
            return None

        confidence = min(0.82, 0.55 + (imbalance / 10) + (edge_net * 2))

        return OrderbookSignal(
            token        = token,
            direction    = "BUY",
            fair_value   = fair,
            entry_price  = round(entry + 0.005, 4),
            edge         = round(edge_net, 4),
            imbalance    = round(imbalance, 2),
            seconds_left = seconds_left,
            confidence   = confidence,
            reason=(
                f"OB imbalance {imbalance:.1f}x "
                f"| fair={fair:.3f} entry={entry:.3f} "
                f"| net edge={edge_net*100:.2f}¢ after {TAKER_FEE*100:.1f}% fee "
                f"| {seconds_left:.0f}s to close"
            )
        )
