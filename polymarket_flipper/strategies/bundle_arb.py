"""
Bundle Arbitrage — Guaranteed Profit
=====================================
Scans ALL active markets constantly.
Buys YES + NO whenever their combined cost < $1.00 minus fees.

This is the #1 documented Polymarket strategy — $40M+ extracted platform-wide.
No prediction needed. No direction. Pure maths.

Payout is ALWAYS $1.00 (one side resolves YES, the other NO).
If you pay less than $1.00 for both sides combined → locked profit.

Fee tiers:
  Non-crypto markets: ~0% fee (most events, sports, politics)
  Crypto markets:     dynamic, up to 3.15% at 50% price point
  → For crypto: only enter if bundle ≤ 0.93 (covers worst-case fees)
  → For non-crypto: enter if bundle ≤ 0.97

Edge: 2.7-second average window. Bot polls every 15s.
At our scale (£3-10/trade), we're slow — but we catch the ones that last.
"""
from dataclasses import dataclass
from typing import Optional
import logging

from market_feed import TokenInfo

logger = logging.getLogger(__name__)

# Non-crypto: 0% fee → need bundle ≤ 0.97 (3% profit floor)
BUNDLE_MAX_NON_CRYPTO = 0.97

# Crypto: up to 3.15% fee per leg → need bigger cushion
BUNDLE_MAX_CRYPTO     = 0.93

CRYPTO_KEYWORDS = {
    "btc", "bitcoin", "eth", "ethereum", "sol", "solana",
    "crypto", "price", "above", "below", "will reach",
    "matic", "polygon", "xrp", "ripple", "doge",
}

MIN_VOLUME     = 5_000   # $5k min volume — avoid dead markets
MIN_LIQUIDITY  = 1_000   # $1k min liquidity on each side


@dataclass
class BundleSignal:
    yes_token:     TokenInfo
    no_token:      TokenInfo
    bundle_cost:   float
    profit_margin: float      # e.g. 0.031 → 3.1% guaranteed
    fee_adjusted:  float      # profit after estimated fees
    is_crypto:     bool
    confidence:    float
    reason:        str


class BundleArbDetector:
    """
    Fires whenever YES + NO cost < $1.00 after fees on ANY market.
    No crash required. Runs on everything.
    """

    def _is_crypto(self, question: str) -> bool:
        q = question.lower()
        return any(kw in q for kw in CRYPTO_KEYWORDS)

    def evaluate(self, yes_tok: TokenInfo, no_tok: TokenInfo) -> Optional[BundleSignal]:
        yes_ask = yes_tok.best_ask
        no_ask  = no_tok.best_ask

        # Must have valid prices on both sides
        if yes_ask <= 0 or no_ask <= 0:
            return None

        # Volume/liquidity gates — avoid thin markets where fill is impossible
        if yes_tok.volume_24h < MIN_VOLUME:
            return None
        if yes_tok.liquidity < MIN_LIQUIDITY:
            return None

        # Sanity: prices must be between 1¢ and 99¢
        if not (0.01 < yes_ask < 0.99 and 0.01 < no_ask < 0.99):
            return None

        bundle = round(yes_ask + no_ask, 4)
        is_crypto = self._is_crypto(yes_tok.question)

        threshold = BUNDLE_MAX_CRYPTO if is_crypto else BUNDLE_MAX_NON_CRYPTO

        if bundle >= threshold:
            return None

        # Calculate profit margin
        gross_margin = round((1.0 - bundle) / bundle, 4)

        # Estimated fee impact
        # Non-crypto: ~0.5% total (both legs conservative)
        # Crypto: ~3.15% per leg at mid price, less toward extremes
        if is_crypto:
            # Dynamic fee approximation: 3.15% × 2 × min(price, 1-price) × 2
            yes_fee = 0.0315 * min(yes_ask, 1 - yes_ask) * 2
            no_fee  = 0.0315 * min(no_ask,  1 - no_ask)  * 2
            total_fee_pct = yes_fee + no_fee
        else:
            total_fee_pct = 0.005  # ~0.5% conservative estimate

        fee_cost = round(bundle * total_fee_pct, 4)
        net_profit = round((1.0 - bundle - fee_cost) / bundle, 4)

        if net_profit <= 0:
            logger.debug(
                f"Bundle {bundle:.3f} on '{yes_tok.question[:40]}' — "
                f"profit wiped by fees (net={net_profit:.4f})"
            )
            return None

        # Confidence: higher when margin is larger and volume is higher
        confidence = min(0.97, 0.80 + (gross_margin * 3) + min(0.05, yes_tok.volume_24h / 500_000))

        return BundleSignal(
            yes_token     = yes_tok,
            no_token      = no_tok,
            bundle_cost   = bundle,
            profit_margin = gross_margin,
            fee_adjusted  = net_profit,
            is_crypto     = is_crypto,
            confidence    = confidence,
            reason=(
                f"BundleArb: YES={yes_ask:.3f} + NO={no_ask:.3f} = {bundle:.3f} "
                f"| gross={gross_margin*100:.2f}% net={net_profit*100:.2f}% "
                f"| {'CRYPTO' if is_crypto else 'non-crypto'} "
                f"| vol=${yes_tok.volume_24h:,.0f}"
            )
        )
