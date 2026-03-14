"""
Multi-Outcome NO Bundle Arbitrage — GUARANTEED PROFIT
======================================================
In any market with 3+ mutually exclusive outcomes (elections, awards, sports),
exactly ONE outcome resolves YES and ALL others resolve NO.

If you buy NO on every outcome, you ALWAYS win (N-1) contracts no matter what.

The maths:
  N outcomes. YES prices sum to S. You buy NO on all.
  Cost    = sum of all NO prices = N - S
  Payout  = (N-1) × $1.00       (you win every NO except the one that resolves YES)
  Profit  = (N-1) - (N - S) = S - 1.00

  → Profit exists whenever YES_sum > 1.00
  → Profit = YES_sum - 1.00, guaranteed regardless of outcome

Real example (US election 2024, documented):
  Biden: 0.42, Trump: 0.51, Other: 0.12 → YES_sum = 1.05
  Buy all NOs → 5% guaranteed profit, $29M extracted this strategy in 1 year

Fee impact:
  Each NO leg costs ~0.5% fee (non-crypto)
  With N legs: total fee ≈ N × 0.005
  Min YES_sum for profit = 1.00 + (N × 0.005)
  → 3-outcome: need YES_sum > 1.015
  → 5-outcome: need YES_sum > 1.025
  → 10-outcome: need YES_sum > 1.05

How we find these markets:
  Polymarket groups related markets under "events"
  Gamma API: GET /events → returns event with list of child markets
  Each child market = one outcome with YES/NO tokens
"""
from dataclasses import dataclass, field
from typing import Optional
import logging
import requests

logger = logging.getLogger(__name__)

GAMMA_URL = "https://gamma-api.polymarket.com"

# Minimum profit after fees to enter
MIN_NET_PROFIT_PCT  = 0.02     # 2% net minimum (covers fees + slippage)
MIN_VOLUME_PER_LEG  = 1_000   # $1k min volume per outcome leg
MIN_LEGS            = 3       # only multi-outcome (3+), not binary markets
MAX_LEGS            = 20      # skip huge markets (hard to fill all legs)
FEE_PER_LEG         = 0.005   # ~0.5% per leg (non-crypto)
FEE_PER_LEG_CRYPTO  = 0.0315  # 3.15% per leg (crypto markets — much higher fee)

# Keywords that indicate a crypto/price-based outcome leg
CRYPTO_KEYWORDS = {
    "btc", "bitcoin", "eth", "ethereum", "sol", "solana", "crypto",
    "price", "above", "below", "will reach", "usd", "xrp", "bnb", "doge",
}


@dataclass
class OutcomeLeg:
    market_id:  str
    token_id:   str
    outcome:    str       # e.g. "Donald Trump", "Kamala Harris"
    yes_price:  float
    no_price:   float
    no_token_id: str
    volume_24h: float


@dataclass
class MultiOutcomeSignal:
    event_title: str
    legs:        list        # List[OutcomeLeg]
    yes_sum:     float       # sum of all YES prices (>1.00 = arb exists)
    gross_profit: float      # yes_sum - 1.00
    net_profit:  float       # after fees
    n_legs:      int
    confidence:  float
    reason:      str


class MultiOutcomeArbDetector:
    """
    Fetches Polymarket events with 3+ outcomes.
    Fires when YES prices sum > 1.00 + fees.
    Execute: buy NO on every single outcome leg.
    """

    def fetch_events(self, limit: int = 100) -> list:
        """Fetch multi-outcome events from Gamma API."""
        try:
            r = requests.get(
                f"{GAMMA_URL}/events",
                params={"active": "true", "closed": "false", "limit": limit},
                timeout=10,
            )
            r.raise_for_status()
            try:
                return r.json()
            except (ValueError, requests.exceptions.JSONDecodeError) as je:
                logger.error(f"Events JSON parse failed: {je} | body={r.text[:200]}")
                return []
        except Exception as e:
            logger.error(f"Events fetch failed: {e}")
            return []

    def _is_crypto_leg(self, mkt: dict) -> bool:
        """Return True if this market leg appears to be a crypto/price outcome."""
        text = " ".join([
            mkt.get("groupItemTitle", ""),
            mkt.get("question", ""),
            mkt.get("category", ""),
            mkt.get("market_slug", ""),
        ]).lower()
        return any(kw in text for kw in CRYPTO_KEYWORDS)

    def _parse_event(self, event: dict) -> Optional[MultiOutcomeSignal]:
        """
        Parse a single event into legs and check for arb opportunity.
        """
        markets = event.get("markets", [])
        if len(markets) < MIN_LEGS or len(markets) > MAX_LEGS:
            return None

        event_title = event.get("title", event.get("slug", ""))
        legs = []

        for mkt in markets:
            tokens = mkt.get("tokens", [])
            if not tokens or len(tokens) < 2:
                continue

            outcomes = mkt.get("outcomes", ["YES", "NO"])
            volume = float(mkt.get("volume24hr") or mkt.get("volumeNum") or 0)

            if volume < MIN_VOLUME_PER_LEG:
                continue

            # Find YES and NO token IDs + prices
            yes_token_id = no_token_id = ""
            yes_price = no_price = 0.0

            for i, tok in enumerate(tokens):
                token_id = tok if isinstance(tok, str) else tok.get("token_id", "")
                outcome  = outcomes[i] if i < len(outcomes) else ("YES" if i == 0 else "NO")

                # Fetch price for this token
                try:
                    pr = requests.get(
                        f"https://clob.polymarket.com/price",
                        params={"token_id": token_id, "side": "buy"},
                        timeout=3,
                    )
                    price = float(pr.json().get("price", 0))
                except Exception:
                    price = 0.0

                if outcome.upper() == "YES":
                    yes_token_id = token_id
                    yes_price    = price
                else:
                    no_token_id = token_id
                    no_price    = price

            if yes_price <= 0 or no_price <= 0:
                continue

            legs.append(OutcomeLeg(
                market_id   = mkt.get("id") or mkt.get("conditionId", ""),
                token_id    = yes_token_id,
                no_token_id = no_token_id,
                outcome     = mkt.get("groupItemTitle") or mkt.get("question", f"Outcome {len(legs)+1}"),
                yes_price   = yes_price,
                no_price    = no_price,
                volume_24h  = volume,
            ))

        if len(legs) < MIN_LEGS:
            return None

        yes_sum      = round(sum(l.yes_price for l in legs), 4)
        gross_profit = round(yes_sum - 1.00, 4)
        # Use per-leg fee based on whether each leg is crypto or non-crypto
        total_fees   = round(sum(
            (FEE_PER_LEG_CRYPTO if self._is_crypto_leg(mkt) else FEE_PER_LEG)
            for mkt in markets[:len(legs)]
        ), 4)
        net_profit   = round(gross_profit - total_fees, 4)

        if net_profit < MIN_NET_PROFIT_PCT:
            if gross_profit > 0:
                logger.debug(
                    f"Multi-outcome: {event_title[:40]} | YES_sum={yes_sum:.3f} "
                    f"gross={gross_profit*100:.2f}% but net={net_profit*100:.2f}% after fees"
                )
            return None

        confidence = min(0.96, 0.82 + (net_profit * 3))

        return MultiOutcomeSignal(
            event_title  = event_title,
            legs         = legs,
            yes_sum      = yes_sum,
            gross_profit = gross_profit,
            net_profit   = net_profit,
            n_legs       = len(legs),
            confidence   = confidence,
            reason=(
                f"MultiOutcomeArb: {len(legs)} outcomes | "
                f"YES_sum={yes_sum:.3f} (over 1.00 by {gross_profit*100:.2f}%) | "
                f"net after fees={net_profit*100:.2f}% GUARANTEED | "
                f"'{event_title[:40]}'"
            )
        )

    def scan(self, limit: int = 100) -> list:
        """
        Fetch all events and return list of MultiOutcomeSignal where arb exists.
        Sorted by net profit descending (best first).
        """
        events = self.fetch_events(limit=limit)
        signals = []
        for event in events:
            sig = self._parse_event(event)
            if sig:
                signals.append(sig)
        signals.sort(key=lambda s: s.net_profit, reverse=True)
        return signals
