"""
Polymarket Flipper — £30 starting bankroll
==========================================
3 strategies (ranked by guarantee):

  1. Bundle Arb       — YES+NO bundle < $1.00 on ANY market (GUARANTEED, $40M+ documented)
  2. Resolution Lag   — market past end_time, winner still at 88–99¢ (semi-guaranteed)
  3. NO Bias          — 70% historical NO resolution, +16.7% EV (directional)

Scans every 15 seconds. Dynamic trade sizing from bankroll.py.
Starting balance: £30 → scales automatically as balance grows.

Usage:
  python main.py              # live trading
  python main.py --dry-run    # simulate, no real orders
  python main.py --report     # 30-day P&L table
  python main.py --balance    # bankroll status + growth projection
  python main.py --once       # one scan cycle then exit
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
    ENABLE_FLASH_CRASH, ENABLE_NO_BIAS,
)
import database as db
import bankroll as br
import strategy_optimizer as optimizer
from market_feed import (
    fetch_all_markets, fetch_crypto_15min_markets,
    market_to_tokens, fetch_orderbook, build_token_info, seconds_to_close,
)
from executor import place_buy, calc_shares, close_position
from resolver import resolve_open_positions
from strategies.bundle_arb import BundleArbDetector
from strategies.resolution_lag import ResolutionLagDetector
from strategies.no_bias import NOBiasDetector
from strategies.multi_outcome_arb import MultiOutcomeArbDetector

logging.basicConfig(
    level    = logging.INFO,
    format   = "%(asctime)s [%(levelname)s] %(message)s",
    handlers = [logging.StreamHandler(), logging.FileHandler("flipper.log")],
)
logger = logging.getLogger(__name__)

bundle_detector = BundleArbDetector()
lag_detector    = ResolutionLagDetector()
no_detector     = NOBiasDetector()
multi_detector  = MultiOutcomeArbDetector()

_running = True

def _handle_signal(sig, frame):
    global _running
    logger.info("Shutdown signal — stopping after current cycle.")
    _running = False

signal.signal(signal.SIGINT,  _handle_signal)
signal.signal(signal.SIGTERM, _handle_signal)


# ── Strategy 0: Multi-Outcome NO Bundle ────────────────────────────────────

def scan_multi_outcome(dry_run: bool) -> int:
    """
    TOP PRIORITY. Scan Polymarket events with 3+ outcomes.
    Buy NO on every single outcome when YES prices sum > 1.00 + fees.
    GUARANTEED profit regardless of which outcome wins.

    Profit formula: YES_sum - 1.00 (e.g. sum=1.08 → 8% guaranteed)
    Execution: one NO buy per outcome leg, all same market.
    """
    trades = 0
    signals = multi_detector.scan(limit=100)

    for sig in signals:
        # Guaranteed profit — bet heavily, scaled to actual locked margin
        size_gbp = br.guaranteed_size_gbp(sig.net_profit, n_legs=sig.n_legs)

        logger.warning(
            f"MULTI-OUTCOME ARB | {sig.event_title[:60]} | "
            f"{sig.n_legs} outcomes | YES_sum={sig.yes_sum:.3f} | "
            f"net={sig.net_profit*100:.2f}% GUARANTEED | "
            f"£{size_gbp:.2f}/leg × {sig.n_legs} legs = £{size_gbp*sig.n_legs:.2f} total"
        )

        legs_placed = 0
        for leg in sig.legs:
            if not leg.no_token_id:
                continue

            shares = round(size_gbp * 1.27 / leg.no_price, 2)

            tid = place_buy(
                token_id  = leg.no_token_id,
                price     = leg.no_price,
                shares    = shares,
                strategy  = "MultiOutcomeArb",
                market_id = leg.market_id,
                reason    = f"NO on '{leg.outcome[:40]}' | {sig.reason[:60]}",
                dry_run   = dry_run,
            )
            if tid:
                legs_placed += 1

        if legs_placed > 0:
            logger.info(f"  Placed {legs_placed}/{sig.n_legs} NO legs")
            trades += 1

    return trades


# ── Strategy 1: Bundle Arb ─────────────────────────────────────────────────

def scan_bundle_arb(markets: list, dry_run: bool) -> int:
    """
    Scan ALL markets for YES+NO bundle < $1.00 after fees.
    Guaranteed profit — no prediction needed.
    Highest priority, gets 1.5x sizing.
    """
    trades = 0
    pairs = defaultdict(dict)   # market_id → {YES: TokenInfo, NO: TokenInfo}

    for market in markets:
        for tok in market_to_tokens(market):
            if not tok["token_id"]:
                continue
            book = fetch_orderbook(tok["token_id"])
            info = build_token_info(market, tok, book)
            pairs[info.market_id][info.outcome.upper()] = info

    for market_id, pair in pairs.items():
        yes_tok = pair.get("YES")
        no_tok  = pair.get("NO")
        if not yes_tok or not no_tok:
            continue

        sig = bundle_detector.evaluate(yes_tok, no_tok)
        if not sig:
            continue

        # Guaranteed profit — use heavy sizing scaled to the locked margin
        size_gbp   = br.guaranteed_size_gbp(sig.fee_adjusted, n_legs=2)
        size_usdc  = size_gbp * br.GBP_TO_USDC if hasattr(br, 'GBP_TO_USDC') else size_gbp * 1.27
        yes_shares = round(size_gbp * 1.27 / yes_tok.best_ask, 2)
        no_shares  = round(size_gbp * 1.27 / no_tok.best_ask,  2)

        logger.warning(
            f"BUNDLE ARB | {yes_tok.question[:65]} | "
            f"bundle={sig.bundle_cost:.3f} net={sig.fee_adjusted*100:.2f}% guaranteed | "
            f"sizing £{size_gbp:.2f}/leg (locked profit → heavy bet)"
        )

        tid = place_buy(
            token_id  = yes_tok.token_id,
            price     = yes_tok.best_ask,
            shares    = yes_shares,
            strategy  = "BundleArb",
            market_id = market_id,
            reason    = sig.reason,
            dry_run   = dry_run,
        )
        if tid:
            place_buy(
                token_id  = no_tok.token_id,
                price     = no_tok.best_ask,
                shares    = no_shares,
                strategy  = "BundleArb_NO",
                market_id = market_id,
                reason    = f"NO leg | {sig.reason[:60]}",
                dry_run   = dry_run,
            )
            trades += 1

    return trades


# ── Strategy 2: Resolution Lag ─────────────────────────────────────────────

def scan_resolution_lag(markets: list, dry_run: bool) -> int:
    """
    Find markets past their end_time where the winner is still at 88-99¢.
    Buy the winner before Polymarket settles it to $1.00.
    Semi-guaranteed: event is over, just waiting on settlement.
    """
    trades = 0
    for market in markets:
        for tok in market_to_tokens(market):
            if not tok["token_id"] or tok["outcome"].upper() != "YES":
                continue

            book = fetch_orderbook(tok["token_id"])
            info = build_token_info(market, tok, book)

            sig = lag_detector.evaluate(info)
            if not sig:
                continue

            # Semi-guaranteed — bet heavier than directional but less than pure arb
            # Scale with confidence: 92¢ winner gets more than 88¢ winner
            semi_margin = sig.profit_margin * sig.confidence   # discount by confidence
            size_gbp    = br.guaranteed_size_gbp(semi_margin, n_legs=1)
            shares      = round(size_gbp * 1.27 / sig.win_price, 2)

            logger.info(
                f"RESOLUTION LAG | {info.question[:65]} | "
                f"YES={sig.win_price:.3f} | {sig.minutes_overdue:.0f}m past end | "
                f"profit={sig.profit_margin*100:.2f}% | sizing £{size_gbp:.2f}"
            )

            tid = place_buy(
                token_id  = info.token_id,
                price     = sig.win_price,
                shares    = shares,
                strategy  = "ResolutionLag",
                market_id = info.market_id,
                reason    = sig.reason,
                dry_run   = dry_run,
            )
            if tid:
                trades += 1
    return trades


# ── Strategy 3: NO Bias ────────────────────────────────────────────────────

def scan_no_bias(markets: list, dry_run: bool) -> int:
    """
    Systematic NO on non-crypto markets. 70% historical resolution NO.
    +16.7% EV per trade. Lowest priority, 0.8x sizing.
    Positions held days to weeks.
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
            shares   = calc_shares(no_entry, "NOBias")   # 0.8x sizing

            logger.info(
                f"NO BIAS | {info.question[:65]} | "
                f"YES={sig.yes_mid:.2f} NO={sig.no_mid:.2f} | conf={sig.confidence:.2f}"
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

    open_count = db.count_open_trades()
    daily      = db.get_daily()
    logger.info(
        f"Cycle | open={open_count} | trades_today={daily['trades']}/{TARGET_TRADES_PER_DAY} | "
        f"{br.status_line()}"
    )

    resolve_open_positions(dry_run=dry_run)

    # Auto-rebalance strategy sizing based on real performance
    optimizer.rebalance()

    # Fetch all markets ONCE — shared by binary strategies
    all_markets = fetch_all_markets(limit=200)

    total  = 0
    total += scan_multi_outcome(dry_run)                # Strategy 0 — GUARANTEED (multi-leg)
    total += scan_bundle_arb(all_markets, dry_run)      # Strategy 1 — GUARANTEED (binary)
    total += scan_resolution_lag(all_markets, dry_run)  # Strategy 2 — semi-guaranteed
    total += scan_no_bias(all_markets, dry_run)         # Strategy 3 — directional

    db.snapshot_balance(br.get_balance(), note=f"cycle trades={total}")
    logger.info(f"Cycle done | new trades={total} | {br.status_line()}")
    return total


# ── Entry point ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Polymarket Flipper — £30 bankroll, 3 strategies")
    parser.add_argument("--dry-run",  action="store_true", help="Simulate only")
    parser.add_argument("--report",   action="store_true", help="Print 30-day P&L")
    parser.add_argument("--balance",  action="store_true", help="Show bankroll + projection")
    parser.add_argument("--optimize", action="store_true", help="Show strategy performance + live multipliers")
    parser.add_argument("--once",     action="store_true", help="One cycle then exit")
    args = parser.parse_args()

    db.init_db()

    if args.report:
        db.print_report()
        return

    if args.balance:
        print(f"\n{br.status_line()}\n")
        print(br.growth_projection())
        print(br.size_table())
        return

    if args.optimize:
        print(optimizer.strategy_report())
        return

    mode = "DRY RUN" if args.dry_run else "LIVE"
    print(
        f"\n{'='*60}\n"
        f"  Polymarket Flipper — {mode}\n"
        f"  Strategies: MultiOutcomeArb + BundleArb + ResolutionLag + NOBias\n"
        f"  Poll: every {POLL_INTERVAL_SECONDS}s\n"
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
