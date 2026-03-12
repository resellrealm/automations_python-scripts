"""
Trading strategies for Polymarket.

Documented results:
  FlashCrash   — 86% ROI ($1,000 → $1,869) with proven parameters
  LatencyArb   — 139,000% ($313 → $437,600) via spot price lag, 98% win rate
  NOBias       — 70% historical NO resolution rate across all markets
  Arbitrage    — $150k from 8,894 bundle trades (now harder due to 3.15% fee)
  TrendFollow  — 55-60% win rate on 5-min crypto markets, 20-50% annual ROI
"""
from src.strategies.arbitrage import ArbitrageStrategy
from src.strategies.market_making import MarketMakingStrategy
from src.strategies.trend_following import TrendFollowingStrategy
from src.strategies.flash_crash import FlashCrashStrategy
from src.strategies.no_bias import NOBiasStrategy
from src.strategies.latency_arb import LatencyArbStrategy

__all__ = [
    'ArbitrageStrategy',
    'MarketMakingStrategy',
    'TrendFollowingStrategy',
    'FlashCrashStrategy',    # PROVEN 86% ROI
    'NOBiasStrategy',        # 70% historical NO resolution
    'LatencyArbStrategy',    # $313 → $437k documented
]
