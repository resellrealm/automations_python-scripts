"""
Crypto Scalper — Binance spot scalping bot
==========================================
Signals: RSI(6,12,24) + Bollinger Bands + VWAP + Volume surge
Sizing:  Confidence-tiered £0.50 / £0.75 / £1.00 / £1.50
Risk:    2x ATR stop loss | 3x ATR take profit | 2h timeout
Daily:   Max £5 loss | max 30 trades/day

Usage:
  python main.py              # live trading
  python main.py --dry-run    # simulate, no real orders
  python main.py --report     # 30-day P&L table
  python main.py --balance    # bankroll status
  python main.py --once       # one scan then exit
"""
import sys
import time
import signal
import logging
import argparse

from config import (
    SYMBOLS, POLL_INTERVAL_SECONDS, MAX_OPEN_TRADES,
    MAX_TRADES_PER_DAY, MAX_HOLD_MINUTES, LOG_FILE,
)
import database as db
import bankroll as br
from signals import fetch_signal
from executor import open_trade, close_trade, get_current_price

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s [%(levelname)s] %(message)s",
    handlers = [logging.StreamHandler(), logging.FileHandler(LOG_FILE)],
)
logger = logging.getLogger(__name__)

_running = True


def _handle_signal(sig, frame):
    global _running
    logger.info("Shutdown signal — stopping after current cycle.")
    _running = False


signal.signal(signal.SIGINT,  _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# ── SL / TP / Timeout monitor ─────────────────────────────────────────

def manage_open_trades(dry_run: bool):
    open_trades = db.get_open_trades()
    stale_ids   = {t["id"] for t in db.get_stale_trades(MAX_HOLD_MINUTES)}

    for trade in open_trades:
        symbol = trade["symbol"]
        price  = get_current_price(symbol)

        if price is None:
            continue

        if trade["id"] in stale_ids:
            logger.info(f"TIMEOUT #{trade['id']} {symbol} | price={price:.6f}")
            close_trade(trade, price, "TIMEOUT", dry_run=dry_run)
            continue

        direction = trade["direction"]
        sl        = trade["sl_price"]
        tp        = trade["tp_price"]

        if direction == "LONG":
            if price <= sl:
                close_trade(trade, price, "SL", dry_run=dry_run)
            elif price >= tp:
                close_trade(trade, price, "TP", dry_run=dry_run)
        else:
            if price >= sl:
                close_trade(trade, price, "SL", dry_run=dry_run)
            elif price <= tp:
                close_trade(trade, price, "TP", dry_run=dry_run)


# ── Signal scan ───────────────────────────────────────────────────────

def scan_signals(dry_run: bool) -> int:
    trades       = 0
    open_symbols = {t["symbol"] for t in db.get_open_trades()}

    for symbol in SYMBOLS:
        if symbol in open_symbols:
            continue
        if db.count_open_trades() >= MAX_OPEN_TRADES:
            break
        if db.count_today_trades() >= MAX_TRADES_PER_DAY:
            break

        sig = fetch_signal(symbol)
        if sig is None:
            continue

        logger.info(
            f"SIGNAL {sig.symbol} {sig.direction} | conf={sig.confidence:.3f} | "
            f"£{br.size_for_confidence(sig.confidence):.2f} | {sig.reason[:100]}"
        )

        tid = open_trade(sig, dry_run=dry_run)
        if tid:
            trades += 1

    return trades


# ── Main cycle ────────────────────────────────────────────────────────

def run_cycle(dry_run: bool) -> int:
    if br.is_stopped_today():
        logger.warning("Daily loss limit — skipping cycle.")
        return 0
    if br.is_in_cooldown():
        logger.warning("Cooldown active — skipping cycle.")
        return 0

    logger.info(
        f"Cycle | open={db.count_open_trades()}/{MAX_OPEN_TRADES} | "
        f"trades_today={db.count_today_trades()}/{MAX_TRADES_PER_DAY} | "
        f"{br.status_line()}"
    )

    manage_open_trades(dry_run)
    new_trades = scan_signals(dry_run)
    db.snapshot_balance(br.get_balance(), note=f"cycle new={new_trades}")

    logger.info(f"Cycle done | new_trades={new_trades} | {br.status_line()}")
    return new_trades


# ── Entry point ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Crypto Scalper — RSI+BB+VWAP on Binance")
    parser.add_argument("--dry-run", action="store_true", help="Simulate, no real orders")
    parser.add_argument("--report",  action="store_true", help="Print 30-day P&L")
    parser.add_argument("--balance", action="store_true", help="Show bankroll status")
    parser.add_argument("--once",    action="store_true", help="One scan then exit")
    args = parser.parse_args()

    db.init_db()

    if args.report:
        db.print_report()
        return

    if args.balance:
        print(f"\n{br.status_line()}\n")
        return

    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(
        f"\n{'='*60}\n"
        f"  Crypto Scalper — {mode}\n"
        f"  Exchange: Binance (spot, longs only)\n"
        f"  Symbols: {', '.join(SYMBOLS)}\n"
        f"  Signals: RSI(6,12,24) + BB + VWAP + Volume\n"
        f"  Sizing:  £0.50 / £0.75 / £1.00 / £1.50 by confidence\n"
        f"  Risk:    2x ATR SL | 3x ATR TP | {MAX_HOLD_MINUTES}m timeout\n"
        f"  Poll:    every {POLL_INTERVAL_SECONDS}s\n"
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

    logger.info("Crypto Scalper stopped.")


if __name__ == "__main__":
    main()
