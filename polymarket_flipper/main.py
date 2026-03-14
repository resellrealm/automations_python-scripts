"""
Polymarket Flipper — £30 starting bankroll, compounds daily
============================================================
Strategies (in priority order):
  1. Flash Crash  — buy YES+NO bundle when YES drops ≥12%, sum ≤ 0.95 (locked profit)
  2. OB Mismatch  — heavy orderbook imbalance + edge after 3.15% fee
  3. NO Bias      — 70% historical NO resolution on non-crypto markets

Sizing: dynamic — 10% of current balance per trade (scales as you profit)
  £30 start → £3/trade → grows to £5/trade at £50, £10/trade at £100

Usage:
  python main.py              # live trading
  python main.py --dry-run    # simulate, no real orders
  python main.py --report     # 30-day P&L table
  python main.py --balance    # show current bankroll + growth projection
  python main.py --once       # one cycle then exit
"""
import sys
import time
import logging
import argparse
import signal
from collections import defaultdict
from datetime import datetime

from config import (
    POLL_INTERVAL_SECONDS, TARGET_TRADES_PER_DAY,
    ENABLE_FLASH_CRASH, ENABLE_ORDERBOOK, ENABLE_NO_BIAS,
)
import database as db
import bankroll as br
from market_feed import (
    fetch_crypto_15min_markets, fetch_all_markets,
    market_to_tokens, fetch_orderbook, build_token_info, seconds_to_close,
)
from executor import place_buy, calc_shares, close_position
from resolver import resolve_open_positions
from strategies.flash_crash import FlashCrashDetector
from strategies.orderbook_mismatch import OrderbookMismatchDetector
from strategies.no_bias import NOBiasDetector

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s [%(levelname)s] %(message)s",
    handlers = [logging.StreamHandler(), logging.FileHandler("flipper.log")],
)
logger = logging.getLogger(__name__)

flash_detector = FlashCrashDetector()
ob_detector    = OrderbookMismatchDetector()
no_detector    = NOBiasDetector()

_running = True

def _handle_signal(sig, frame):
    global _running
    logger.info("Shutdown signal — stopping after current cycle.")
    _running = False

signal.signal(signal.SIGINT,  _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# ── Strategy scanners ──────────────────────────────────────────────────────

def scan_flash_crash(markets: list, dry_run: bool) -> int:
    """
    Flash Crash — buy YES+NO bundle when YES drops ≥12% and sum ≤ 0.95.
    Highest conviction: guaranteed locked profit. Gets 1.5x sizing.
    Fetches orderbooks only once per market pair.
    """
    trades = 0
    market_tokens = defaultdict(dict)

    for market in markets:
        for tok in market_to_tokens(market):
            if not tok["token_id"]:
                continue
            book = fetch_orderbook(tok["token_id"])
            info = build_token_info(market, tok, book)
            market_tokens[info.market_id][info.outcome.upper()] = info

    for market_id, pair in market_tokens.items():
        yes_tok = pair.get("YES")
        no_tok  = pair.get("NO")
        if not yes_tok or not no_tok:
            continue

        sig = flash_detector.evaluate(yes_tok, no_tok)
        if not sig:
            continue

        logger.warning(
            f"FLASH CRASH | {yes_tok.question[:60]} | "
            f"drop={sig.drop_pct:.1f}% bundle={sig.bundle_cost:.3f} "
            f"profit={sig.profit_margin*100:.2f}%"
        )

        # Split £ allocation across both legs
        yes_shares = calc_shares(sig.yes_token.best_ask, "FlashCrash")
        no_shares  = calc_shares(sig.no_token.best_ask,  "FlashCrash_NO")

        tid = place_buy(
            token_id  = yes_tok.token_id,
            price     = yes_tok.best_ask,
            shares    = yes_shares,
            strategy  = "FlashCrash",
            market_id = market_id,
            reason    = sig.reason,
            dry_run   = dry_run,
        )
        if tid:
            place_buy(
                token_id  = no_tok.token_id,
                price     = no_tok.best_ask,
                shares    = no_shares,
                strategy  = "FlashCrash_NO",
                market_id = market_id,
                reason    = f"NO leg paired | {sig.reason[:60]}",
                dry_run   = dry_run,
            )
            trades += 1

    return trades


def scan_orderbook(markets: list, dry_run: bool) -> int:
    """
    OB Mismatch — heavy bid imbalance + spread edge after fee.
    Reuses already-fetched market list (no duplicate API calls).
    """
    trades = 0
    for market in markets:
        sec_left = seconds_to_close(market)
        if sec_left is None:
            continue

        for tok in market_to_tokens(market):
            if not tok["token_id"] or tok["outcome"].upper() != "YES":
                continue

            book = fetch_orderbook(tok["token_id"])
            info = build_token_info(market, tok, book)

            sig = ob_detector.evaluate(info, sec_left)
            if not sig:
                continue

            shares = calc_shares(sig.entry_price, "OBMismatch")
            logger.info(
                f"OB MISMATCH | {info.question[:60]} | "
                f"imbalance={sig.imbalance:.1f}x edge={sig.edge*100:.2f}¢"
            )

            tid = place_buy(
                token_id  = info.token_id,
                price     = sig.entry_price,
                shares    = shares,
                strategy  = "OBMismatch",
                market_id = info.market_id,
                reason    = sig.reason,
                dry_run   = dry_run,
            )
            if tid:
                trades += 1
    return trades


def scan_no_bias(markets: list, dry_run: bool) -> int:
    """
    NO Bias — 70% historical NO resolution on non-crypto markets.
    Lowest priority, smallest sizing multiplier (0.8x).
    """
    trades = 0
    for market in markets:
        for tok in market_to_tokens(market):
            if not tok["token_id"] or tok["outcome"].upper() != "YES":
                continue

            book = fetch_orderbook(tok["token_id"])
            info = build_token_info(market, tok, book)

            sig = no_detector.evaluate(info)
            if not sig:
                continue

            no_entry = round(sig.no_mid + 0.01, 4)
            shares   = calc_shares(no_entry, "NOBias")

            logger.info(
                f"NO BIAS | {info.question[:60]} | "
                f"YES={sig.yes_mid:.2f} NO={sig.no_mid:.2f}"
            )

            tid = place_buy(
                token_id  = info.token_id,
                price     = no_entry,
                shares    = shares,
                strategy  = "NOBias",
                market_id = info.market_id,
                reason    = sig.reason,
                dry_run   = dry_run,
            )
            if tid:
                trades += 1
    return trades


# ── Main cycle ─────────────────────────────────────────────────────────────

def run_cycle(dry_run: bool) -> int:
    if br.is_stopped_today():
        logger.warning("Daily loss limit hit — skipping cycle.")
        return 0

    open_count   = db.count_open_trades()
    daily        = db.get_daily()
    logger.info(
        f"Cycle | open={open_count} trades_today={daily['trades']}/{TARGET_TRADES_PER_DAY} | "
        f"{br.status_line()}"
    )

    # Resolve open positions first
    resolve_open_positions(dry_run=dry_run)

    total = 0

    # Fetch crypto markets ONCE — shared by flash crash + OB mismatch
    if ENABLE_FLASH_CRASH or ENABLE_ORDERBOOK:
        crypto_markets = fetch_crypto_15min_markets()
        if ENABLE_FLASH_CRASH:
            total += scan_flash_crash(crypto_markets, dry_run)
        if ENABLE_ORDERBOOK:
            total += scan_orderbook(crypto_markets, dry_run)

    if ENABLE_NO_BIAS:
        all_markets = fetch_all_markets(limit=150)
        total += scan_no_bias(all_markets, dry_run)

    # Snapshot balance at end of cycle
    db.snapshot_balance(br.get_balance(), note=f"cycle trades={total}")

    logger.info(f"Cycle done | new trades={total} | {br.status_line()}")
    return total


# ── Entry point ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Polymarket Flipper — £30 starting bankroll")
    parser.add_argument("--dry-run",  action="store_true", help="Simulate only")
    parser.add_argument("--report",   action="store_true", help="Print 30-day P&L table")
    parser.add_argument("--balance",  action="store_true", help="Show bankroll + growth projection")
    parser.add_argument("--once",     action="store_true", help="Run one cycle and exit")
    args = parser.parse_args()

    db.init_db()

    if args.report:
        db.print_report()
        return

    if args.balance:
        print(f"\n{br.status_line()}\n")
        print(br.growth_projection())
        return

    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(
        f"\n{'='*60}\n"
        f"  Polymarket Flipper — {mode}\n"
        f"  {br.status_line()}\n"
        f"{'='*60}\n"
    )

    if args.once:
        run_cycle(dry_run=args.dry_run)
        return

    while _running:
        try:
            run_cycle(dry_run=args.dry_run)
        except Exception as e:
            logger.error(f"Cycle error: {e}", exc_info=True)
        if _running:
            time.sleep(POLL_INTERVAL_SECONDS)

    logger.info("Polymarket Flipper stopped.")


if __name__ == "__main__":
    main()
