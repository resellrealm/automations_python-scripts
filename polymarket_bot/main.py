"""
Optimised Polymarket Bot
=========================
4 strategies (choose one in .env):
  flash_crash    — buys during sharp probability drops, sells on recovery
  market_maker   — posts bid/ask quotes to capture spread (~1.2% avg)
  arbitrage      — detects YES+NO bundle < $1.00 (guaranteed profit)
  ai_sentiment   — Kimi AI assesses market questions for mispricing

Patterns from:
  discountry/polymarket-trading-bot
  lorine93s/polymarket-market-maker-bot
  CarlosIbCu/polymarket-kalshi-btc-arbitrage-bot
  Polymarket/agents (official framework)
  eiri0k/PolyMarket-AI-agent-trading

Usage:
    python main.py                 # Run daemon (polls every 30s)
    python main.py --once          # Single scan then exit
    python main.py --scan          # List market opportunities, no trades
    python main.py --report        # Show P&L summary
"""

import sys, os, time, signal, argparse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import Config
from shared.logger import get_logger
from shared.kimi_client import KimiClient
from market_client import PolymarketClient
from strategies import flash_crash_signal, market_maker_quotes, bundle_arbitrage_check, ai_sentiment_signal
import database as db

logger = get_logger("polymarket_bot", log_dir="logs")
_running = True
POLL_INTERVAL = 30  # seconds between scans


def _handle_signal(s, f):
    global _running
    logger.info("Stopping...")
    _running = False


def scan_markets(client: PolymarketClient, ai=None, execute: bool = False) -> list:
    """
    Scan active markets and find opportunities.
    execute=True → place orders. execute=False → report only.
    """
    markets  = client.get_markets(limit=50)
    opps     = []
    strategy = Config.STRATEGY

    open_positions = {p["market_id"]: dict(p) for p in db.get_open_positions()}
    if len(open_positions) >= Config.MAX_OPEN_POSITIONS:
        logger.info(f"Max open positions ({Config.MAX_OPEN_POSITIONS}) reached — skipping new entries.")
        return []

    for market in markets:
        mid = market.get("id", "")
        question = market.get("question", "")[:80]

        # Skip markets already in position
        if mid in open_positions:
            continue

        signal = None
        try:
            if strategy == "flash_crash":
                signal = flash_crash_signal(market, client)
            elif strategy == "market_maker":
                signal = market_maker_quotes(market, client)
            elif strategy == "arbitrage":
                signal = bundle_arbitrage_check(market, client)
            elif strategy == "ai_sentiment" and ai:
                signal = ai_sentiment_signal(market, client, ai)

        except Exception as e:
            logger.debug(f"Strategy error on '{question}': {e}")
            continue

        if not signal:
            continue

        logger.info(
            f"OPPORTUNITY [{signal['strategy']}] — {question}\n"
            f"  Action: {signal['action']} | Size: ${signal['size']} | "
            f"Reason: {signal.get('reason','')}"
        )
        opps.append(signal)

        if execute:
            _execute_signal(client, signal, market)

        time.sleep(0.5)  # polite rate limit

    return opps


def _execute_signal(client: PolymarketClient, signal: dict, market: dict):
    """Execute a trading signal."""
    try:
        action = signal["action"]

        if action == "BUY":
            client.buy(signal["token_id"], signal["price"], signal["size"])
            db.open_position(
                market_id=market.get("id"), question=market.get("question", "")[:120],
                strategy=signal["strategy"], action=action,
                token_id=signal["token_id"], entry_price=signal["price"],
                size=signal["size"], reason=signal.get("reason", ""),
                dry_run=Config.DRY_RUN,
            )

        elif action == "ARB":
            # Buy both YES and NO
            client.buy(signal["yes_token"], signal["yes_price"], signal["size"])
            client.buy(signal["no_token"],  signal["no_price"],  signal["size"])
            db.open_position(
                market_id=market.get("id"), question=market.get("question", "")[:120],
                strategy="arbitrage", action="ARB",
                token_id=signal["yes_token"], entry_price=signal["bundle_cost"],
                size=signal["size"] * 2, reason=signal.get("reason", ""),
                dry_run=Config.DRY_RUN,
            )

        elif action == "QUOTE":
            # Market maker: post both sides
            client.buy(signal["token_id"],  signal["our_bid"], signal["size"])
            client.sell(signal["token_id"], signal["our_ask"], signal["size"])

    except Exception as e:
        logger.error(f"Execution error: {e}")


def check_exit_conditions(client: PolymarketClient):
    """Check open positions for exit conditions (target recovery, stop loss)."""
    open_pos = db.get_open_positions()
    for pos in open_pos:
        try:
            current = client.get_midpoint(pos["token_id"])
            if current <= 0:
                continue

            entry = pos["entry_price"]
            pnl_pct = ((current - entry) / max(entry, 0.01)) * 100

            # Exit if +5% gain or -10% loss
            if pnl_pct >= 5.0:
                client.sell(pos["token_id"], current, pos["size"])
                db.close_position(pos["id"], current)
                logger.info(f"EXIT (take profit) — {pos['question'][:60]} | P&L={pnl_pct:.2f}%")
            elif pnl_pct <= -10.0:
                client.sell(pos["token_id"], current, pos["size"])
                db.close_position(pos["id"], current)
                logger.info(f"EXIT (stop loss) — {pos['question'][:60]} | P&L={pnl_pct:.2f}%")

        except Exception as e:
            logger.debug(f"Exit check error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Polymarket Bot")
    parser.add_argument("--once",   action="store_true", help="Single scan and exit")
    parser.add_argument("--scan",   action="store_true", help="Scan markets, no trades")
    parser.add_argument("--report", action="store_true", help="Show P&L")
    args = parser.parse_args()

    db.init_db()

    if args.report:
        s = db.get_summary()
        print(f"\n{'='*45}")
        print(f"  Polymarket Bot — Results")
        print(f"{'='*45}")
        print(f"  Total trades : {s.get('total', 0)}")
        print(f"  Wins         : {s.get('wins', 0)}")
        print(f"  Total P&L    : ${s.get('total_pnl', 0)}")
        print(f"  Avg P&L %    : {s.get('avg_pnl_pct', 0)}%")
        print(f"  Open         : {s.get('open', 0)}")
        print(f"{'='*45}\n")
        return

    client = PolymarketClient()
    ai     = KimiClient() if Config.STRATEGY == "ai_sentiment" and Config.AI_API_KEY else None

    mode = "[DRY RUN]" if Config.DRY_RUN else "[LIVE]"
    logger.info(f"Polymarket Bot started {mode} | strategy={Config.STRATEGY}")

    if args.scan:
        opps = scan_markets(client, ai, execute=False)
        print(f"\nFound {len(opps)} opportunity/opportunities.\n")
        return

    if args.once:
        check_exit_conditions(client)
        scan_markets(client, ai, execute=True)
        return

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    while _running:
        try:
            check_exit_conditions(client)
            scan_markets(client, ai, execute=True)
        except Exception as e:
            logger.error(f"Cycle error: {e}", exc_info=True)
        if _running:
            logger.info(f"Sleeping {POLL_INTERVAL}s...")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
