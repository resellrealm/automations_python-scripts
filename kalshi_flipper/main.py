"""
Kalshi Flipper — £5/trade, £5/day limit, ~8 trades/day
========================================================
Strategies:
  1. NO Bundle Arb   — multi-outcome markets where YES prices sum > 1.0
                       (Reality TV, elections, sports — $29M extracted in 1 year)
  2. Cross-Platform  — same event priced differently on Kalshi vs Polymarket
  3. Resolution Lag  — buy winner before market settles post-expiry

Usage:
  python main.py              # live trading
  python main.py --dry-run    # simulate, no real orders
  python main.py --report     # 30-day P&L report
  python main.py --once       # one cycle and exit
"""

import sys
import time
import signal
import logging
import argparse

from config import (
    POLL_INTERVAL_SECONDS, TARGET_TRADES_PER_DAY,
    ENABLE_NO_BUNDLE, ENABLE_CROSS_ARB, ENABLE_RESOLUTION,
    RISK_PER_TRADE_USD, DAILY_LOSS_USD,
    KALSHI_API_URL, KALSHI_KEY_ID, KALSHI_PRIVATE_KEY,
    NO_BUNDLE_MIN_OUTCOMES,
)
import database as db
from kalshi_client import KalshiClient
from market_feed import (
    fetch_all_markets, group_by_series,
    find_reality_tv_series, find_multi_outcome_series,
    fetch_series_with_prices,
)
from executor import place_trade, place_no_bundle, close_resolved
from strategies.no_bundle import NOBundleDetector
from strategies.cross_arb import CrossArbDetector
from strategies.resolution_lag import ResolutionLagDetector

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(levelname)s] %(message)s",
    handlers= [logging.StreamHandler(), logging.FileHandler("kalshi_flipper.log")],
)
logger = logging.getLogger(__name__)

# ── Strategy instances ────────────────────────────────────────
no_bundle_det  = NOBundleDetector()
cross_arb_det  = CrossArbDetector()
resolution_det = ResolutionLagDetector()

# ── Graceful shutdown ─────────────────────────────────────────
_running = True
def _stop(sig, frame):
    global _running
    logger.info("Shutdown signal — stopping after cycle.")
    _running = False
signal.signal(signal.SIGINT, _stop)
signal.signal(signal.SIGTERM, _stop)

# Cross-arb keywords to match Kalshi markets against Polymarket
CROSS_ARB_KEYWORDS = [
    "fed rate", "federal reserve", "interest rate",
    "bitcoin", "btc", "ethereum", "eth",
    "election", "trump", "president",
]


def run_no_bundle(client, all_markets, dry_run: bool) -> int:
    trades = 0

    # Reality TV first (highest probability of YES overpricing)
    tv_series = find_reality_tv_series(all_markets)
    other_series = find_multi_outcome_series(all_markets, min_outcomes=NO_BUNDLE_MIN_OUTCOMES)
    all_series = list(dict.fromkeys(tv_series + other_series))  # dedup, TV first

    for series_ticker in all_series:
        series = fetch_series_with_prices(client, series_ticker)
        if not series:
            continue

        # Calculate contracts per leg = £5 split across legs
        contracts_per_leg = max(1, int(RISK_PER_TRADE_USD / max(series.outcome_count, 1) / 0.80))
        sig = no_bundle_det.evaluate(series, contracts_per_leg)
        if not sig:
            continue

        logger.info(
            f"💰 NO BUNDLE | {series.title} | {series.outcome_count} outcomes | "
            f"YES sum={sig.yes_sum:.3f} | net edge={sig.edge_net*100:.2f}¢ | "
            f"profit=${sig.expected_profit:.4f}"
        )

        placed = place_no_bundle(client, sig.legs, "NOBundle", sig.reason, dry_run)
        if placed > 0:
            trades += 1

    return trades


def run_cross_arb(client, all_markets, dry_run: bool) -> int:
    trades = 0
    signals = cross_arb_det.find_signals(all_markets, CROSS_ARB_KEYWORDS)

    for sig in signals:
        logger.info(
            f"🔀 CROSS ARB | {sig.event_title[:50]} | "
            f"Kalshi={sig.kalshi_price:.2f} Poly={sig.poly_price:.2f} | "
            f"edge={sig.edge*100:.1f}¢ | {sig.action}"
        )
        if sig.action == "buy_kalshi":
            tid = place_trade(client, sig.kalshi_ticker, "yes",
                              "CrossArb", sig.reason, dry_run)
            if tid:
                trades += 1
        # buy_poly side would go through polymarket_flipper

    return trades


def run_resolution(client, all_markets, dry_run: bool) -> int:
    trades = 0
    signals = resolution_det.scan(all_markets)

    for sig in signals:
        logger.info(
            f"⏳ RESOLUTION LAG | {sig.market.title[:60]} | "
            f"{sig.side.upper()}={sig.entry_price:.2f} | "
            f"edge={sig.edge*100:.1f}¢"
        )
        tid = place_trade(client, sig.market.ticker, sig.side,
                          "ResolutionLag", sig.reason, dry_run)
        if tid:
            trades += 1

    return trades


def run_cycle(client, dry_run: bool) -> int:
    if db.is_stopped():
        logger.warning("Daily loss limit — skipping cycle.")
        return 0

    daily = db.get_daily()
    logger.info(
        f"Cycle | trades={daily['trades']}/{TARGET_TRADES_PER_DAY} | "
        f"P&L: ${daily['pnl_usd']:+.2f} (£{daily['pnl_gbp']:+.2f})"
    )

    # Close any resolved positions first
    close_resolved(client, dry_run)

    # Fetch all markets once per cycle
    all_markets = fetch_all_markets(client)
    if not all_markets:
        logger.warning("No markets fetched — check API credentials.")
        return 0

    total = 0
    if ENABLE_NO_BUNDLE:
        total += run_no_bundle(client, all_markets, dry_run)
    if ENABLE_CROSS_ARB:
        total += run_cross_arb(client, all_markets, dry_run)
    if ENABLE_RESOLUTION:
        total += run_resolution(client, all_markets, dry_run)

    logger.info(f"Cycle done | new trades={total}")
    return total


def main():
    parser = argparse.ArgumentParser(description="Kalshi Flipper — £5/trade")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--report",  action="store_true")
    parser.add_argument("--once",    action="store_true")
    args = parser.parse_args()

    db.init_db()

    if args.report:
        db.print_report()
        return

    mode = "DRY RUN" if args.dry_run else "LIVE"
    logger.info(
        f"{'='*60}\n"
        f"  Kalshi Flipper — {mode}\n"
        f"  Risk: £5/trade (~${RISK_PER_TRADE_USD:.2f})\n"
        f"  Daily limit: £5 loss (${DAILY_LOSS_USD:.2f})\n"
        f"  Target: ~{TARGET_TRADES_PER_DAY} trades/day\n"
        f"  Strategies: NO bundle | Cross-arb | Resolution lag\n"
        f"{'='*60}"
    )

    client = KalshiClient(KALSHI_API_URL, KALSHI_KEY_ID, KALSHI_PRIVATE_KEY)

    if args.once:
        run_cycle(client, dry_run=args.dry_run)
        return

    while _running:
        try:
            run_cycle(client, dry_run=args.dry_run)
        except Exception as e:
            logger.error(f"Cycle error: {e}", exc_info=True)
        if not _running:
            break
        time.sleep(POLL_INTERVAL_SECONDS)

    logger.info("Kalshi Flipper stopped.")


if __name__ == "__main__":
    main()
