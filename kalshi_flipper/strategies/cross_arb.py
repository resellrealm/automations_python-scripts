"""
Cross-Platform Arbitrage — Kalshi vs Polymarket
================================================
Same real-world event priced differently on both platforms.
Buy cheap on one, the outcome pays on both.

Example:
  "Will Fed cut rates in March?"
  Kalshi YES = 0.42
  Polymarket YES = 0.51
  → Buy YES on Kalshi (cheap), hold. If it resolves YES: profit.
  → Or: buy YES Kalshi + buy NO Polymarket = locked profit regardless of outcome

Documented: one dev made $764 in a single day on BTC hourly cross-arb.
GitHub refs: CarlosIbCu/polymarket-kalshi-btc-arbitrage-bot
             taetaehoho/poly-kalshi-arb
"""

import requests
import logging
from dataclasses import dataclass
from typing import Optional, List

from config import CROSS_ARB_MIN_EDGE, KALSHI_FEE_MULTIPLIER

logger = logging.getLogger(__name__)

POLYMARKET_GAMMA = "https://gamma-api.polymarket.com"
POLYMARKET_CLOB  = "https://clob.polymarket.com"


@dataclass
class CrossArbSignal:
    event_title:   str
    kalshi_ticker: str
    poly_token_id: str
    kalshi_price:  float   # YES price on Kalshi
    poly_price:    float   # YES price on Polymarket
    edge:          float   # gap after fees
    action:        str     # "buy_kalshi" or "buy_poly"
    confidence:    float
    reason:        str


class CrossArbDetector:
    """
    Finds the same event on both platforms and checks for price divergence.
    Currently focused on Fed rate decisions and BTC/ETH direction markets.
    """

    def __init__(self):
        self._poly_cache = {}  # keyword → list of markets

    def _fetch_poly_markets(self, keyword: str) -> list:
        if keyword in self._poly_cache:
            return self._poly_cache[keyword]
        try:
            r = requests.get(
                f"{POLYMARKET_GAMMA}/markets",
                params={"active": "true", "closed": "false",
                        "limit": 50, "search": keyword},
                timeout=8,
            )
            if r.ok:
                data = r.json()
                self._poly_cache[keyword] = data if isinstance(data, list) else data.get("markets", [])
                return self._poly_cache[keyword]
        except Exception as e:
            logger.debug(f"Poly fetch error: {e}")
        return []

    def _poly_price(self, token_id: str) -> float:
        """Fetch best ask for a Polymarket token."""
        try:
            r = requests.get(
                f"{POLYMARKET_CLOB}/price",
                params={"token_id": token_id, "side": "buy"},
                timeout=5,
            )
            if r.ok:
                return float(r.json().get("price", 0))
        except Exception:
            pass
        return 0.0

    def _kalshi_fee(self, price: float) -> float:
        return KALSHI_FEE_MULTIPLIER * price * (1 - price)

    def find_signals(self, kalshi_markets: list, keywords: List[str]) -> List[CrossArbSignal]:
        """
        Check Kalshi markets against matching Polymarket markets.
        keywords: event-specific search terms e.g. ["fed rate", "bitcoin", "trump"]
        """
        signals = []

        for km in kalshi_markets:
            title_lower = km.title.lower()

            for kw in keywords:
                if kw.lower() not in title_lower:
                    continue

                poly_markets = self._fetch_poly_markets(kw)
                for pm in poly_markets:
                    pm_q = (pm.get("question") or "").lower()

                    # Check if both markets are about the same event
                    if not self._same_event(title_lower, pm_q):
                        continue

                    # Get Polymarket price
                    tokens = pm.get("tokens", []) or pm.get("clob_token_ids", [])
                    if not tokens:
                        continue
                    tok_id = tokens[0] if isinstance(tokens[0], str) else tokens[0].get("token_id", "")
                    poly_p = self._poly_price(tok_id)
                    if not poly_p:
                        continue

                    kalshi_p = km.yes_mid
                    if not kalshi_p:
                        continue

                    # Fee-adjusted gap
                    kalshi_fee = self._kalshi_fee(kalshi_p)
                    gap = abs(poly_p - kalshi_p) - kalshi_fee

                    if gap < CROSS_ARB_MIN_EDGE:
                        continue

                    if kalshi_p < poly_p:
                        action = "buy_kalshi"   # Kalshi is cheaper
                        edge   = poly_p - kalshi_p - kalshi_fee
                    else:
                        action = "buy_poly"     # Polymarket is cheaper
                        edge   = kalshi_p - poly_p - kalshi_fee

                    confidence = min(0.82, 0.55 + gap * 3)

                    signals.append(CrossArbSignal(
                        event_title   = km.title,
                        kalshi_ticker = km.ticker,
                        poly_token_id = tok_id,
                        kalshi_price  = kalshi_p,
                        poly_price    = poly_p,
                        edge          = round(edge, 4),
                        action        = action,
                        confidence    = confidence,
                        reason=(
                            f"Cross-arb: {km.title[:50]} | "
                            f"Kalshi={kalshi_p:.2f} Poly={poly_p:.2f} | "
                            f"gap={gap*100:.1f}¢ after fees | {action}"
                        )
                    ))

        return signals

    def _same_event(self, kalshi_title: str, poly_question: str) -> bool:
        """Rough check if two market titles refer to the same event."""
        # Look for shared meaningful keywords (3+ chars)
        k_words = set(w for w in kalshi_title.split() if len(w) >= 4)
        p_words = set(w for w in poly_question.split() if len(w) >= 4)
        shared  = k_words & p_words
        return len(shared) >= 2
