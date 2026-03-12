"""
Oddpool — Cross-Platform Prediction Market Arb Scanner
=======================================================
Finds matching events on Polymarket and Kalshi.
Buys YES on the cheaper platform + NO on the other.
One leg always pays $1.00 → guaranteed profit when bundle < $1.00.

Math:
  Buy YES @ 0.42 (Kalshi) + Buy NO @ 0.44 (Polymarket) = $0.86 cost
  Payout = $1.00 regardless of outcome
  Profit = $0.14 (16% return, risk-free)

Usage:
  python main.py              # live trading
  python main.py --dry-run    # scan and log, no real orders
  python main.py --scan-only  # print found arbs, no orders
  python main.py --report     # 30-day P&L report
"""

import sys
import time
import signal
import logging
import argparse

from config import (
    POLL_INTERVAL_SECONDS, MIN_NET_EDGE, MAX_BUNDLE_COST,
    RISK_PER_ARB_USD, DAILY_LOSS_USD,
    KALSHI_API_URL, KALSHI_KEY_ID, KALSHI_PRIVATE_KEY,
)
import database as db
from fetcher import fetch_polymarket_markets, fetch_kalshi_markets
from matcher import match_markets, filter_profitable
from executor import execute_arb

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s [%(levelname)s] %(message)s",
    handlers= [logging.StreamHandler(), logging.FileHandler("oddpool.log")],
)
logger = logging.getLogger(__name__)

# ── Shutdown ──────────────────────────────────────────────────
_running = True
def _stop(sig, frame):
    global _running
    logger.info("Shutdown signal — stopping after cycle.")
    _running = False
signal.signal(signal.SIGINT, _stop)
signal.signal(signal.SIGTERM, _stop)


def _get_kalshi_client():
    """Initialise Kalshi client (lazy import to allow scan-only without creds)."""
    sys.path.insert(0, "..")
    try:
        from kalshi_flipper.kalshi_client import KalshiClient
        return KalshiClient(KALSHI_API_URL, KALSHI_KEY_ID, KALSHI_PRIVATE_KEY)
    except Exception:
        # Local copy fallback
        from kalshi_client import KalshiClient
        return KalshiClient(KALSHI_API_URL, KALSHI_KEY_ID, KALSHI_PRIVATE_KEY)


def _get_poly_client():
    """Initialise Polymarket CLOB client."""
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import ApiCreds
        from config import POLY_PRIVATE_KEY, POLY_API_KEY, POLY_API_SECRET, POLY_API_PASSPHRASE, POLY_CLOB_URL
        creds = ApiCreds(
            api_key=POLY_API_KEY, api_secret=POLY_API_SECRET, api_passphrase=POLY_API_PASSPHRASE
        )
        return ClobClient(host=POLY_CLOB_URL, chain_id=137, key=POLY_PRIVATE_KEY, creds=creds)
    except Exception as e:
        logger.warning(f"Poly client init failed: {e} — running scan-only mode.")
        return None


def print_arbs(matches, limit=20):
    if not matches:
        print("\n  No profitable arbs found this cycle.\n")
        return

    print(f"\n{'='*80}")
    print(f"  PROFITABLE ARB OPPORTUNITIES ({len(matches)} found)")
    print(f"{'='*80}")
    print(f"{'Event':<42} {'YES on':<12} {'Bundle':>7} {'Net Edge':>9} {'Keywords'}")
    print("-" * 80)
    for m in matches[:limit]:
        title = m.poly_market.title[:41]
        kws   = ", ".join(m.shared_words[:4])
        print(
            f"{title:<42} {m.buy_yes_on:<12} "
            f"${m.bundle_cost:>6.3f}  {m.net_edge*100:>7.2f}¢  {kws}"
        )
    print(f"{'='*80}\n")


def run_cycle(poly_client, kalshi_client, dry_run: bool, scan_only: bool) -> int:
    if db.is_stopped():
        logger.warning("Daily limit hit — skipping.")
        return 0

    daily = db.get_daily()
    logger.info(
        f"Cycle | arbs today={daily['arbs']} | "
        f"P&L: ${daily['pnl_usd']:+.2f} (£{daily['pnl_gbp']:+.2f})"
    )

    # Fetch markets from both platforms
    poly_markets   = fetch_polymarket_markets(limit=300)
    kalshi_markets = fetch_kalshi_markets(kalshi_client) if kalshi_client else []

    if not poly_markets or not kalshi_markets:
        logger.warning("Could not fetch markets from one or both platforms.")
        return 0

    # Match and filter
    all_matches        = match_markets(poly_markets, kalshi_markets)
    profitable_matches = filter_profitable(all_matches, min_net_edge=MIN_NET_EDGE)

    logger.info(
        f"Matched {len(all_matches)} pairs | "
        f"{len(profitable_matches)} profitable (net edge ≥ {MIN_NET_EDGE*100:.0f}¢)"
    )

    print_arbs(profitable_matches)

    if scan_only:
        return len(profitable_matches)

    # Execute profitable arbs
    executed = 0
    for arb in profitable_matches:
        if db.is_stopped():
            break
        if arb.bundle_cost > MAX_BUNDLE_COST:
            logger.debug(f"Bundle cost {arb.bundle_cost:.3f} > {MAX_BUNDLE_COST} — skip")
            continue

        success = execute_arb(arb, poly_client, kalshi_client, dry_run=dry_run)
        if success:
            executed += 1

    return executed


def main():
    parser = argparse.ArgumentParser(description="Oddpool — Cross-platform prediction market arb")
    parser.add_argument("--dry-run",    action="store_true", help="Scan + log, no real orders")
    parser.add_argument("--scan-only",  action="store_true", help="Print arbs only, no execution")
    parser.add_argument("--report",     action="store_true", help="30-day P&L report")
    parser.add_argument("--once",       action="store_true", help="One cycle and exit")
    args = parser.parse_args()

    db.init_db()

    if args.report:
        db.print_report()
        return

    mode = "SCAN ONLY" if args.scan_only else ("DRY RUN" if args.dry_run else "LIVE")
    logger.info(
        f"\n{'='*60}\n"
        f"  Oddpool — {mode}\n"
        f"  Risk: £5/arb (~${RISK_PER_ARB_USD:.2f} split across 2 legs)\n"
        f"  Daily limit: £5 loss\n"
        f"  Min net edge: {MIN_NET_EDGE*100:.0f}¢ after fees\n"
        f"  Platforms: Polymarket + Kalshi\n"
        f"{'='*60}"
    )

    poly_client   = None if args.scan_only else _get_poly_client()
    kalshi_client = _get_kalshi_client()

    if args.once:
        run_cycle(poly_client, kalshi_client, dry_run=args.dry_run, scan_only=args.scan_only)
        return

    while _running:
        try:
            run_cycle(poly_client, kalshi_client, dry_run=args.dry_run, scan_only=args.scan_only)
        except Exception as e:
            logger.error(f"Cycle error: {e}", exc_info=True)
        if not _running:
            break
        logger.debug(f"Sleeping {POLL_INTERVAL_SECONDS}s...")
        time.sleep(POLL_INTERVAL_SECONDS)

    logger.info("Oddpool stopped.")


if __name__ == "__main__":
    main()
