"""
NO Bundle Arbitrage Strategy
==============================
Works on multi-outcome markets (Reality TV, elections, sports).

Logic:
  In a "Who wins Love Island?" market with 5 contestants:
  - Exactly ONE will win → exactly ONE NO loses → FOUR NOs win
  - If sum of all YES prices > 1.0 → buying NO on all is profitable

  Example (5 contestants, YES prices sum to 1.08):
    Buy NO on all 5 at ~80¢ each = $4.00 cost
    4 NOs win = $4.00 payout... wait

    Actually the edge is: YES_sum - 1.0 = 0.08 = 8¢ per dollar risked
    Because each YES is overpriced — you buy the cheap side (NO)

Fee impact (Kalshi):
  At 80¢ NO (=20¢ YES price): fee = 0.07 × 1 × 0.80 × 0.20 = 1.12¢/contract
  At 50¢ NO: fee = 0.07 × 1 × 0.50 × 0.50 = 1.75¢/contract

$29M was extracted from this exact strategy on Polymarket in one year.
Kalshi has the same structure on Reality TV markets.
"""

from dataclasses import dataclass
from typing import Optional, List
import logging

from market_feed import MarketSeries, KalshiMarket
from config import NO_BUNDLE_MIN_EDGE, NO_BUNDLE_MIN_OUTCOMES, KALSHI_FEE_MULTIPLIER

logger = logging.getLogger(__name__)


@dataclass
class NOBundleSignal:
    series:        MarketSeries
    yes_sum:       float          # sum of YES prices (must be > 1.0)
    edge_gross:    float          # yes_sum - 1.0
    edge_net:      float          # after fees
    fee_total:     float
    contracts:     int            # contracts per leg
    cost_total:    float          # total USD cost
    expected_profit: float
    confidence:    float
    reason:        str
    legs:          List[dict]     # [{ticker, side, contracts, no_price_cents}]


class NOBundleDetector:
    """
    Scans multi-outcome series for YES price sum > 1.0.
    Fires when net edge (after fees) exceeds threshold.
    """

    def evaluate(self, series: MarketSeries, contracts_per_leg: int = 1) -> Optional[NOBundleSignal]:
        if series.outcome_count < NO_BUNDLE_MIN_OUTCOMES:
            return None

        # Need fresh prices on all legs
        legs_ok = [m for m in series.markets if m.yes_mid > 0]
        if len(legs_ok) < NO_BUNDLE_MIN_OUTCOMES:
            return None

        yes_sum   = sum(m.yes_mid for m in legs_ok)
        edge_gross = round(yes_sum - 1.0, 4)

        if edge_gross <= 0:
            return None  # no overpricing

        # Calculate total fee across all NO legs
        # NO price = 1 - YES price
        total_fee = 0.0
        legs      = []
        for m in legs_ok:
            no_price_cents = int(round((1.0 - m.yes_mid) * 100))
            fee = KALSHI_FEE_MULTIPLIER * contracts_per_leg * (no_price_cents/100) * (m.yes_mid)
            total_fee += fee
            legs.append({
                "ticker":         m.ticker,
                "side":           "no",
                "contracts":      contracts_per_leg,
                "no_price_cents": no_price_cents,
                "yes_mid":        m.yes_mid,
                "fee":            round(fee, 4),
            })

        edge_net = round(edge_gross - total_fee, 4)

        if edge_net < NO_BUNDLE_MIN_EDGE:
            logger.debug(
                f"NO bundle {series.series_ticker}: gross={edge_gross:.4f} "
                f"fee={total_fee:.4f} net={edge_net:.4f} < {NO_BUNDLE_MIN_EDGE}"
            )
            return None

        # Cost = sum of NO prices × contracts
        cost_total = sum(
            (leg["no_price_cents"] / 100) * leg["contracts"]
            for leg in legs
        )
        # At resolution: (N-1) NOs win, 1 loses
        # Payout = (N-1) × contracts × $1.00
        n = len(legs_ok)
        payout = (n - 1) * contracts_per_leg
        expected_profit = round(payout - cost_total - total_fee, 4)

        confidence = min(0.90, 0.65 + edge_net * 5)

        return NOBundleSignal(
            series          = series,
            yes_sum         = round(yes_sum, 4),
            edge_gross      = edge_gross,
            edge_net        = edge_net,
            fee_total       = round(total_fee, 4),
            contracts       = contracts_per_leg,
            cost_total      = round(cost_total, 4),
            expected_profit = expected_profit,
            confidence      = confidence,
            reason=(
                f"NO bundle: {series.title} | "
                f"{n} outcomes | YES sum={yes_sum:.3f} (over by {edge_gross*100:.1f}¢) | "
                f"net edge={edge_net*100:.2f}¢ after fees | "
                f"expected profit=${expected_profit:.4f}"
            ),
            legs = legs,
        )
