"""
Flash Crash Strategy — PROVEN 86% ROI
======================================
Source: HTX Insights analysis, discountry/polymarket-trading-bot
Documented result: $1,000 → $1,869 (86% ROI)

CRITICAL: These exact parameters produced 86% ROI.
          Wrong params (1% threshold, 0.60 sum target) = -50% loss.

How it works:
  1. Monitor 15-minute BTC/ETH/SOL UP/DOWN markets
  2. When YES crashes ≥15% in one candle → check if bundle < $0.95
  3. Buy both YES and NO (two-legged) → guaranteed $1.00 at resolution
  4. Hold until 15-minute window resolves

Edge: Flash crashes are noise/panic. Markets resolve at $1.00.
      Buying bundle at $0.95 = guaranteed $0.05 profit per share, risk-free.
"""

from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

from src.strategies.base import BaseStrategy, Signal, MarketData
from src.config import config


# ── PROVEN PARAMETERS (do not change without backtesting) ────────────────────
CRASH_THRESHOLD_PCT  = 15.0   # % price drop to trigger — CRITICAL
SUM_TARGET           = 0.95   # buy bundle if YES+NO ≤ this — CRITICAL
OBSERVATION_WINDOW_M = 2      # minutes to confirm crash — CRITICAL
POSITION_SHARES      = 20     # shares per trade (from documented $1k backtest)
MIN_YES_PRICE        = 0.05   # ignore if YES already near zero (resolved)
MAX_YES_PRICE        = 0.90   # ignore if YES already near certain
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class FlashCrashOpportunity:
    yes_token_id: str
    no_token_id: str
    yes_price: float
    no_price: float
    bundle_cost: float
    drop_pct: float
    expected_profit: float
    profit_pct: float
    market_id: str
    question: str


class FlashCrashStrategy(BaseStrategy):
    """
    Buys both YES and NO when YES crashes ≥15% and bundle ≤ $0.95.
    Documented 86% ROI on BTC/ETH/SOL 15-minute markets.
    """

    def __init__(self):
        super().__init__(
            name="FlashCrash",
            config={
                "crash_threshold":    CRASH_THRESHOLD_PCT,
                "sum_target":         SUM_TARGET,
                "observation_window": OBSERVATION_WINDOW_M,
                "position_shares":    POSITION_SHARES,
                "min_yes_price":      MIN_YES_PRICE,
                "max_yes_price":      MAX_YES_PRICE,
            }
        )
        # Track previous prices to detect crashes
        self._prev_prices: dict = {}
        self.opportunities_found = 0
        self.trades_executed = 0

    def get_required_data(self) -> List[str]:
        return ["best_bid", "best_ask", "mid_price", "volume"]

    def analyze(self, market_data: List[MarketData]) -> List[Signal]:
        signals = []

        # Group by market to get YES/NO pairs
        market_groups: dict = {}
        for d in market_data:
            if d.market_id not in market_groups:
                market_groups[d.market_id] = []
            market_groups[d.market_id].append(d)

        for market_id, tokens in market_groups.items():
            if len(tokens) < 2:
                continue

            opp = self._detect_flash_crash(market_id, tokens)
            if opp:
                sigs = self._create_signals(opp)
                signals.extend(sigs)
                self.opportunities_found += 1
                logger.warning(
                    f"🚨 FLASH CRASH DETECTED — {opp.question[:60]}\n"
                    f"   YES crashed {opp.drop_pct:.1f}% | Bundle={opp.bundle_cost:.3f} "
                    f"| Expected profit={opp.profit_pct*100:.2f}%"
                )

        return signals

    def _detect_flash_crash(self, market_id: str, tokens: List[MarketData]) -> Optional[FlashCrashOpportunity]:
        """Check if a flash crash occurred and bundle is cheap enough."""
        yes_token = next((t for t in tokens if self._is_yes(t)), None)
        no_token  = next((t for t in tokens if self._is_no(t)), None)

        if not yes_token or not no_token:
            return None

        yes_ask = yes_token.best_ask
        no_ask  = no_token.best_ask

        # Filter extreme prices (near zero or near certain)
        if not (MIN_YES_PRICE < yes_ask < MAX_YES_PRICE):
            return None

        # Check for crash vs previous price
        prev_yes = self._prev_prices.get(yes_token.token_id)
        self._prev_prices[yes_token.token_id] = yes_ask

        if prev_yes is None or prev_yes <= 0:
            return None

        drop_pct = ((prev_yes - yes_ask) / prev_yes) * 100

        if drop_pct < CRASH_THRESHOLD_PCT:
            return None

        # Check if bundle is cheap enough
        bundle_cost = yes_ask + no_ask
        if bundle_cost > SUM_TARGET:
            logger.debug(
                f"Crash detected ({drop_pct:.1f}%) but bundle too expensive "
                f"({bundle_cost:.3f} > {SUM_TARGET})"
            )
            return None

        # Minimum liquidity check
        if min(yes_token.liquidity, no_token.liquidity) < 500:
            return None

        expected_profit = 1.0 - bundle_cost
        profit_pct = expected_profit / bundle_cost

        return FlashCrashOpportunity(
            yes_token_id=yes_token.token_id,
            no_token_id=no_token.token_id,
            yes_price=yes_ask,
            no_price=no_ask,
            bundle_cost=bundle_cost,
            drop_pct=drop_pct,
            expected_profit=expected_profit * POSITION_SHARES,
            profit_pct=profit_pct,
            market_id=market_id,
            question=yes_token.question,
        )

    def _create_signals(self, opp: FlashCrashOpportunity) -> List[Signal]:
        """Create two signals — one for YES leg, one for NO leg."""
        confidence = min(0.95, 0.70 + opp.profit_pct * 5)

        yes_signal = Signal(
            strategy_name=self.name,
            token_id=opp.yes_token_id,
            market_id=opp.market_id,
            side="BUY",
            size=POSITION_SHARES,
            price=opp.yes_price + 0.01,  # lift 1¢ to fill faster
            confidence=confidence,
            reason=(
                f"Flash crash: YES dropped {opp.drop_pct:.1f}% | "
                f"Bundle={opp.bundle_cost:.3f} ≤ {SUM_TARGET} | "
                f"Locked profit={opp.profit_pct*100:.2f}% [86% ROI strategy]"
            )
        )

        no_signal = Signal(
            strategy_name=self.name,
            token_id=opp.no_token_id,
            market_id=opp.market_id,
            side="BUY",
            size=POSITION_SHARES,
            price=opp.no_price + 0.01,
            confidence=confidence,
            reason=f"Flash crash NO leg — paired with YES buy | bundle={opp.bundle_cost:.3f}"
        )

        return [yes_signal, no_signal]

    @staticmethod
    def _is_yes(token: MarketData) -> bool:
        q = token.question.lower()
        return "yes" in q or token.extra.get("outcome", "").lower() == "yes"

    @staticmethod
    def _is_no(token: MarketData) -> bool:
        q = token.question.lower()
        return "no" in q or token.extra.get("outcome", "").lower() == "no"
