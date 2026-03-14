"""
Flash Crash Strategy — Locked Profit (86% documented ROI)
==========================================================
Buy YES + NO bundle when YES crashes ≥12% and YES+NO sum ≤ 0.95.
Payout is always $1.00 → guaranteed profit when bundle cost < $1.00.

Changes from original:
  - Threshold lowered 15% → 12% (more signals, still high conviction)
  - Volume filter: skip markets with <$10k volume (thin = unreliable)
  - Cooldown: don't re-enter same market within 5 minutes
"""
import time
from dataclasses import dataclass
from typing import Optional
import logging

from market_feed import TokenInfo
from config import (
    FLASH_CRASH_THRESHOLD_PCT, FLASH_BUNDLE_MAX,
    FLASH_MIN_YES, FLASH_MAX_YES,
    FLASH_MIN_VOLUME, FLASH_COOLDOWN_SECONDS,
)

logger = logging.getLogger(__name__)


@dataclass
class FlashSignal:
    yes_token:     TokenInfo
    no_token:      TokenInfo
    drop_pct:      float
    bundle_cost:   float
    profit_margin: float
    confidence:    float
    reason:        str


class FlashCrashDetector:
    def __init__(self):
        self._prev:     dict = {}   # token_id → last yes_ask
        self._cooldown: dict = {}   # market_id → last_entry_time

    def evaluate(self, yes_tok: TokenInfo, no_tok: TokenInfo) -> Optional[FlashSignal]:
        yes_ask = yes_tok.best_ask
        no_ask  = no_tok.best_ask

        if not (FLASH_MIN_YES < yes_ask < FLASH_MAX_YES):
            return None

        # Volume filter — avoid thin markets
        if yes_tok.volume_24h < FLASH_MIN_VOLUME:
            return None

        # Cooldown — don't re-enter same market too quickly
        last = self._cooldown.get(yes_tok.market_id, 0)
        if time.time() - last < FLASH_COOLDOWN_SECONDS:
            return None

        prev = self._prev.get(yes_tok.token_id)
        self._prev[yes_tok.token_id] = yes_ask

        if prev is None or prev <= 0:
            return None

        drop_pct = ((prev - yes_ask) / prev) * 100
        if drop_pct < FLASH_CRASH_THRESHOLD_PCT:
            return None

        bundle = yes_ask + no_ask
        if bundle > FLASH_BUNDLE_MAX:
            logger.debug(f"Flash: crash {drop_pct:.1f}% but bundle={bundle:.3f} > {FLASH_BUNDLE_MAX}")
            return None

        self._cooldown[yes_tok.market_id] = time.time()

        margin     = round((1.0 - bundle) / bundle, 4)
        confidence = min(0.95, 0.70 + margin * 5)

        return FlashSignal(
            yes_token     = yes_tok,
            no_token      = no_tok,
            drop_pct      = drop_pct,
            bundle_cost   = bundle,
            profit_margin = margin,
            confidence    = confidence,
            reason=(
                f"FlashCrash: YES dropped {drop_pct:.1f}% "
                f"| bundle={bundle:.3f}≤{FLASH_BUNDLE_MAX} "
                f"| locked profit={margin*100:.2f}% "
                f"| vol=${yes_tok.volume_24h:,.0f}"
            )
        )
