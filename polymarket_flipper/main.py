"""
Polymarket Flipper — £5/trade, £5/day limit, ~8 trades/day
============================================================
Strategies:
  1. Flash Crash  — buy YES+NO bundle when YES crashes ≥15% and sum ≤ 0.95 (86% ROI proven)
  2. OB Mismatch  — heavy orderbook imbalance + spread edge after 3.15% fee
  3. NO Bias      — 70% historical NO resolution on non-crypto markets

Usage:
  python main.py              # live trading
  python main.py --dry-run    # simulate only, no real orders
  python main.py --report     # print 30-day P&L report
  python main.py --once       # run one scan cycle and exit
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
    RISK_PER_TRADE_USDC, DAILY_LOSS_USDC,
)
import database as db
from market_feed import (
    fetch_crypto_15min_markets, fetch_all_markets,
    market_to_tokens, fetch_orderbook, build_token_info, seconds_to_close,
)
from executor import place_buy, calc_shares
from resolver import resolve_open_positions
from strategies.flash_crash import FlashCrashDetector
from strategies.orderbook_mismatch import OrderbookMismatchDetector
from strategies.no_bias import NOBiasDetector

# ── Logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(message)s",
    handlers = [
        logging.StreamHandler(),
        logging.FileHandler("flipper.log"),
    ]
)
logger = logging.getLogger(__name__)

# ── Strategy instances ────────────────────────────────────────────
flash_detector = FlashCrashDetector()
ob_detector    = OrderbookMismatchDetector()
no_detector    = NOBiasDetector()

# ── Graceful shutdown ─────────────────────────────────────────────
_running = True

def _handle_signal(sig, frame):
    global _running
    logger.info("Shutdown signal received — stopping after current cycle.")
    _running = False

signal.signal(signal.SIGINT, _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


def scan_flash_crash(markets: list, dry_run: bool) -> int:
    """Scan 15-min crypto markets for flash crash opportunities."""
    trades = 0
    market_tokens = defaultdict(dict)  # market_id → {YES: TokenInfo, NO: TokenInfo}

    for market in markets:
        tokens = market_to_tokens(market)
        for tok in tokens:
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

        # £5 = 20 shares (flash crash buys both legs)
        per_leg_shares = calc_shares(sig.yes_token.best_ask) / 2

        logger.warning(
            f"🚨 FLASH CRASH | {yes_tok.question[:60]} | "
            f"drop={sig.drop_pct:.1f}% bundle={sig.bundle_cost:.3f} "
            f"profit={sig.profit_margin*100:.2f}%"
        )

        # YES leg
        tid = place_buy(
            token_id  = yes_tok.token_id,
            price     = yes_tok.best_ask,
            shares    = round(per_leg_shares, 2),
            strategy  = "FlashCrash",
            market_id = market_id,
            reason    = sig.reason,
            dry_run   = dry_run,
        )
        # NO leg
        if tid:
            place_buy(
                token_id  = no_tok.token_id,
                price     = no_tok.best_ask,
                shares    = round(per_leg_shares, 2),
                strategy  = "FlashCrash_NO",
                market_id = market_id,
                reason    = f"NO leg — paired flash crash | {sig.reason[:60]}",
                dry_run   = dry_run,
            )
            trades += 1

    return trades


def scan_orderbook(markets: list, dry_run: bool) -> int:
    """Scan markets for orderbook imbalance opportunities."""
    trades = 0
    for market in markets:
        sec_left = seconds_to_close(market)
        if sec_left is None:
            continue

        tokens = market_to_tokens(market)
        for tok in tokens:
            if not tok["token_id"] or tok["outcome"].upper() != "YES":
                continue
            book = fetch_orderbook(tok["token_id"])
            info = build_token_info(market, tok, book)

            sig = ob_detector.evaluate(info, sec_left)
            if not sig:
                continue

            shares = calc_shares(sig.entry_price)
            logger.info(
                f"📊 OB MISMATCH | {info.question[:60]} | "
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
    """Scan broad market set for NO bias opportunities."""
    trades = 0
    for market in markets:
        tokens = market_to_tokens(market)
        for tok in tokens:
            if not tok["token_id"] or tok["outcome"].upper() != "YES":
                continue  # we look at YES token to infer NO price

            book = fetch_orderbook(tok["token_id"])
            info = build_token_info(market, tok, book)

            sig = no_detector.evaluate(info)
            if not sig:
                continue

            # Buy NO side — use 1-yes price as proxy entry
            no_entry = round(sig.no_mid + 0.01, 4)
            shares   = calc_shares(no_entry)

            logger.info(
                f"📉 NO BIAS | {info.question[:60]} | "
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


def run_cycle(dry_run: bool) -> int:
    """One full scan cycle. Returns number of trades opened."""
    if db.is_stopped_today():
        logger.warning("Daily loss limit hit — skipping cycle.")
        return 0

    daily = db.get_daily()
    trades_today = daily["trades"]
    logger.info(
        f"Cycle start | trades today={trades_today}/{TARGET_TRADES_PER_DAY} | "
        f"P&L: ${daily['pnl_usdc']:+.2f}"
    )

    # Resolve any open positions first
    resolve_open_positions(dry_run=dry_run)

    total = 0

    if ENABLE_FLASH_CRASH:
        crypto_markets = fetch_crypto_15min_markets()
        total += scan_flash_crash(crypto_markets, dry_run)

    if ENABLE_ORDERBOOK:
        crypto_markets = fetch_crypto_15min_markets()
        total += scan_orderbook(crypto_markets, dry_run)

    if ENABLE_NO_BIAS:
        all_markets = fetch_all_markets(limit=150)
        total += scan_no_bias(all_markets, dry_run)

    logger.info(f"Cycle done | new trades={total}")
    return total


def main():
    parser = argparse.ArgumentParser(description="Polymarket Flipper — £5/trade")
    parser.add_argument("--dry-run", action="store_true", help="Simulate only, no real orders")
    parser.add_argument("--report",  action="store_true", help="Print 30-day P&L and exit")
    parser.add_argument("--once",    action="store_true", help="Run one cycle and exit")
    args = parser.parse_args()

    db.init_db()

    if args.report:
        db.print_report()
        return

    mode = "DRY RUN" if args.dry_run else "LIVE"
    logger.info(
        f"{'='*60}\n"
        f"  Polymarket Flipper — {mode}\n"
        f"  Risk: £5/trade (~${RISK_PER_TRADE_USDC:.2f} USDC)\n"
        f"  Daily limit: £5 loss (${DAILY_LOSS_USDC:.2f} USDC)\n"
        f"  Target: ~{TARGET_TRADES_PER_DAY} trades/day\n"
        f"{'='*60}"
    )

    if args.once:
        run_cycle(dry_run=args.dry_run)
        return

    while _running:
        try:
            run_cycle(dry_run=args.dry_run)
        except Exception as e:
            logger.error(f"Cycle error: {e}", exc_info=True)

        if not _running:
            break
        logger.debug(f"Sleeping {POLL_INTERVAL_SECONDS}s...")
        time.sleep(POLL_INTERVAL_SECONDS)

    logger.info("Polymarket Flipper stopped.")


if __name__ == "__main__":
    main()
