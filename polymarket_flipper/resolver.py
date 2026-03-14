"""
Position resolver — checks open positions and closes them at resolution.
Polls CLOB for current price of open positions; closes expired ones.

Two close triggers:
  1. Market resolved: price >= 0.98 (WIN at $1.00) or <= 0.02 (LOSS at $0.00)
  2. Stale timeout: position held longer than MAX_HOLD_HOURS — force exit at mid price
"""
import logging
from datetime import datetime, timezone

import database as db
from config import MAX_HOLD_HOURS
from market_feed import fetch_price, fetch_orderbook, parse_orderbook_prices
from executor import close_position

logger = logging.getLogger(__name__)


def resolve_open_positions(dry_run: bool = False):
    """
    For each open position:
      - Fetch current mid price
      - If market resolved (price near 0 or 1), close at that price
      - If position held longer than MAX_HOLD_HOURS, force-close at current mid
    """
    open_trades = db.get_open_trades()
    if not open_trades:
        return

    # ── Stale position exit ─────────────────────────────────────────
    stale = db.get_stale_positions(MAX_HOLD_HOURS)
    stale_ids = {t["id"] for t in stale}
    for trade in stale:
        try:
            book     = fetch_orderbook(trade["token_id"])
            bid, ask = parse_orderbook_prices(book)
            mid      = round((bid + ask) / 2, 4) if bid and ask else trade["entry_price"]
            logger.warning(
                f"STALE EXIT trade#{trade['id']} | strategy={trade['strategy']} | "
                f"held {MAX_HOLD_HOURS}h+ | entry={trade['entry_price']:.3f} mid={mid:.3f}"
            )
            close_position(trade, mid, dry_run=dry_run)
        except Exception as e:
            logger.error(f"Stale exit error for trade#{trade['id']}: {e}")

    # ── Normal resolution check ─────────────────────────────────────
    for trade in open_trades:
        if trade["id"] in stale_ids:
            continue   # already handled above
        try:
            book     = fetch_orderbook(trade["token_id"])
            bid, ask = parse_orderbook_prices(book)
            mid      = round((bid + ask) / 2, 4) if bid and ask else 0.0

            exit_price = mid
            resolved   = False

            if mid >= 0.98:
                logger.info(f"Trade#{trade['id']} resolved WIN — price={mid:.4f}")
                exit_price = 1.0
                resolved   = True
            elif mid <= 0.02:
                logger.info(f"Trade#{trade['id']} resolved LOSS — price={mid:.4f}")
                exit_price = 0.0
                resolved   = True

            if resolved:
                close_position(trade, exit_price, dry_run=dry_run)

        except Exception as e:
            logger.error(f"Resolver error for trade#{trade['id']}: {e}")
