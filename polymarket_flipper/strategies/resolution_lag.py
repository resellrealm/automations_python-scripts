"""
Resolution Lag Strategy — Semi-Guaranteed Profit
==================================================
Polymarket markets often stay OPEN after the real-world event has already
been decided. The settlement process takes minutes to hours.

During this window:
  - The winning side trades at 85–99¢ (not yet settled to $1.00)
  - The losing side trades at 1–15¢ (not yet settled to $0.00)
  - You can buy the winner at a discount before Polymarket settles it

Example:
  Soccer match ended 30 mins ago. Team A won.
  Polymarket: Team A YES still at 91¢ (not settled yet)
  You buy at 91¢, collect $1.00 at settlement = 9.9% profit

How to detect:
  1. Market end_time has passed (event should be over)
  2. Market is still active/open on Polymarket
  3. One token is trading at ≥85¢ (near certainty but not settled)
  4. Volume is still happening (people are still pricing it)

Risk:
  - Sometimes events are genuinely uncertain past the end_time (delays, OT)
  - Only enter when price is ≥88¢ (high certainty threshold)
  - Skip sports with overtime potential (checked via keywords)

Expected return: 3–15% per trade
Expected hold: minutes to hours
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import logging

from market_feed import TokenInfo

logger = logging.getLogger(__name__)

# Only enter when YES is trading at high confidence range
MIN_WIN_PRICE    = 0.88   # must be ≥88¢ to consider "settled"
MAX_WIN_PRICE    = 0.99   # anything above 99¢ has no margin left
MIN_VOLUME_BURST = 1_000  # $1k min 24h volume (activity still happening)

# Events with genuine overtime/uncertainty risk — skip these
SKIP_OVERTIME_KEYWORDS = [
    "overtime", "extra time", "penalty", "aet",
    "live", "in progress", "suspended",
]

# Markets past end_time by this much are eligible (minutes)
MIN_OVERDUE_MINUTES = 5    # must be at least 5 mins past end_time
MAX_OVERDUE_HOURS   = 48   # ignore if more than 48h past (probably stuck/abandoned)


@dataclass
class ResolutionLagSignal:
    token:          TokenInfo
    win_price:      float       # current ask (discounted winner)
    profit_margin:  float       # $1.00 - win_price
    minutes_overdue: float      # how long past end_time
    confidence:     float
    reason:         str


class ResolutionLagDetector:
    """
    Finds markets where end_time has passed but price hasn't settled to $1.00.
    """

    def evaluate(self, token: TokenInfo) -> Optional[ResolutionLagSignal]:
        if not token.end_time:
            return None

        now = datetime.now(timezone.utc)
        secs_overdue = (now - token.end_time).total_seconds()

        # Must be past end_time
        if secs_overdue < MIN_OVERDUE_MINUTES * 60:
            return None

        # Don't enter stale abandoned markets
        if secs_overdue > MAX_OVERDUE_HOURS * 3600:
            return None

        # Skip markets with overtime risk keywords
        q = token.question.lower()
        if any(kw in q for kw in SKIP_OVERTIME_KEYWORDS):
            return None

        # Check price — looking for near-settled winner
        win_price = token.best_ask
        if not (MIN_WIN_PRICE <= win_price <= MAX_WIN_PRICE):
            return None

        # Must still have activity (not a ghost market)
        if token.volume_24h < MIN_VOLUME_BURST:
            return None

        profit_margin = round(1.0 - win_price, 4)
        minutes_overdue = round(secs_overdue / 60, 1)

        # Confidence: higher when price is higher and market is fresh-overdue
        recency_bonus = max(0, 0.10 - (secs_overdue / 3600) * 0.02)
        confidence = min(0.94, 0.70 + (win_price - MIN_WIN_PRICE) * 2 + recency_bonus)

        return ResolutionLagSignal(
            token           = token,
            win_price       = win_price,
            profit_margin   = profit_margin,
            minutes_overdue = minutes_overdue,
            confidence      = confidence,
            reason=(
                f"ResolutionLag: end_time passed {minutes_overdue:.0f}m ago "
                f"| YES={win_price:.3f} → settles to $1.00 "
                f"| profit={profit_margin*100:.2f}% "
                f"| vol=${token.volume_24h:,.0f}"
            )
        )
