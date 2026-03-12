"""
Event Matcher
=============
Finds markets on Polymarket and Kalshi that describe the same real-world event.

Matching approach (fast, no AI needed):
  1. Normalise both titles (lowercase, remove punctuation, strip common words)
  2. Extract meaningful keywords (length >= 4)
  3. Count shared keywords — if >= MATCH_MIN_SHARED_WORDS → likely same event
  4. Score by overlap ratio for ranking

Examples that will match:
  Kalshi:      "Will the Fed cut rates in March 2026?"
  Polymarket:  "Will Fed cut interest rates at March 2026 meeting?"
  → shared: ["will", "rates", "march", "2026"] → match ✓

  Kalshi:      "Who wins Love Island 2026?"
  Polymarket:  "Love Island 2026 winner"
  → shared: ["love", "island", "2026"] → match ✓
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional
from itertools import product

from fetcher import MarketSnapshot
from config import MATCH_MIN_SHARED_WORDS, MATCH_MIN_WORD_LENGTH

logger = logging.getLogger(__name__)

# Words to ignore when matching
STOP_WORDS = {
    "will", "the", "a", "an", "in", "on", "at", "by", "of", "to",
    "for", "be", "is", "are", "was", "that", "this", "with", "from",
    "and", "or", "not", "does", "have", "has", "had", "its", "which",
    "what", "who", "when", "how", "than", "more", "less", "over",
    "under", "most", "least", "after", "before", "about", "whether",
}


@dataclass
class ArbMatch:
    """Two markets on different platforms describing the same event."""
    poly_market:    MarketSnapshot
    kalshi_market:  MarketSnapshot
    shared_words:   List[str]
    overlap_score:  float     # 0-1, higher = more confident match

    # Arb prices (best combination)
    buy_yes_on:     str       # "polymarket" or "kalshi"
    yes_cost:       float     # price to buy YES on winning platform
    no_cost:        float     # price to buy NO on other platform
    bundle_cost:    float     # yes_cost + no_cost
    gross_edge:     float     # 1.0 - bundle_cost
    net_edge:       float     # gross_edge - fees
    fee_total:      float

    @property
    def profitable(self) -> bool:
        return self.net_edge > 0


def _normalise(title: str) -> List[str]:
    """Extract meaningful keywords from a title."""
    title = title.lower()
    title = re.sub(r"[^a-z0-9\s]", " ", title)
    words = title.split()
    return [w for w in words if len(w) >= MATCH_MIN_WORD_LENGTH and w not in STOP_WORDS]


def _calc_fees(poly: MarketSnapshot, kalshi_price: float, kalshi_contracts: int = 1) -> float:
    """Total fees for one arb: one Polymarket leg + one Kalshi leg."""
    poly_fee   = poly.yes_ask * 0.0315 if poly.is_crypto else 0.0
    kalshi_fee = 0.07 * kalshi_contracts * kalshi_price * (1 - kalshi_price)
    return round(poly_fee + kalshi_fee, 6)


def _best_arb(poly: MarketSnapshot, kalshi: MarketSnapshot) -> Tuple[str, float, float, float]:
    """
    Find the best YES+NO combination across the two platforms.

    Option 1: Buy YES on Poly + Buy NO on Kalshi
      cost = poly.yes_ask + kalshi.no_ask

    Option 2: Buy YES on Kalshi + Buy NO on Poly
      cost = kalshi.yes_ask + poly.no_ask

    Returns (buy_yes_on, yes_cost, no_cost, bundle_cost)
    """
    opt1_cost = poly.yes_ask + kalshi.no_ask
    opt2_cost = kalshi.yes_ask + poly.no_ask

    if opt1_cost <= opt2_cost:
        return "polymarket", poly.yes_ask, kalshi.no_ask, opt1_cost
    else:
        return "kalshi", kalshi.yes_ask, poly.no_ask, opt2_cost


def match_markets(
    poly_markets: List[MarketSnapshot],
    kalshi_markets: List[MarketSnapshot],
) -> List[ArbMatch]:
    """
    Cross-match Polymarket and Kalshi markets.
    Returns all pairs that appear to be the same event, sorted by net_edge desc.
    """
    # Pre-compute keywords for all markets
    poly_kw   = {m: set(_normalise(m.title)) for m in poly_markets}
    kalshi_kw = {m: set(_normalise(m.title)) for m in kalshi_markets}

    matches = []

    for pm, pk in product(poly_markets, kalshi_markets):
        shared = poly_kw[pm] & kalshi_kw[pk]
        if len(shared) < MATCH_MIN_SHARED_WORDS:
            continue

        overlap = len(shared) / max(len(poly_kw[pm] | kalshi_kw[pk]), 1)

        # Calculate arb
        buy_yes_on, yes_cost, no_cost, bundle_cost = _best_arb(pm, pk)
        gross_edge = round(1.0 - bundle_cost, 4)

        if gross_edge <= 0:
            continue  # no gross edge

        kalshi_price = pk.yes_ask if buy_yes_on == "kalshi" else pk.no_ask
        fee_total    = _calc_fees(pm, kalshi_price)
        net_edge     = round(gross_edge - fee_total, 4)

        matches.append(ArbMatch(
            poly_market   = pm,
            kalshi_market = pk,
            shared_words  = sorted(shared),
            overlap_score = round(overlap, 4),
            buy_yes_on    = buy_yes_on,
            yes_cost      = yes_cost,
            no_cost       = no_cost,
            bundle_cost   = round(bundle_cost, 4),
            gross_edge    = gross_edge,
            net_edge      = net_edge,
            fee_total     = round(fee_total, 6),
        ))

    # Sort by net edge descending
    matches.sort(key=lambda m: m.net_edge, reverse=True)
    logger.info(f"Matched {len(matches)} event pairs across platforms.")
    return matches


def filter_profitable(matches: List[ArbMatch], min_net_edge: float = 0.02) -> List[ArbMatch]:
    """Return only matches with net_edge above threshold."""
    return [m for m in matches if m.net_edge >= min_net_edge]
