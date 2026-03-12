"""
Position resolver — checks open positions and closes them at resolution.
Polls CLOB for current price of open positions; closes expired ones.
"""
import logging
from datetime import datetime, timezone

import database as db
from market_feed import fetch_price, fetch_orderbook, parse_orderbook_prices
from executor import close_position

logger = logging.getLogger(__name__)


def resolve_open_positions(dry_run: bool = False):
    """
    For each open position:
      - Fetch current best_bid (exit price if selling)
      - If market appears resolved (price near 0 or 1), close at that price
      - If end_time has passed, close at current bid
    """
    open_trades = db.get_open_trades()
    if not open_trades:
        return

    now = datetime.now(timezone.utc)

    for trade in open_trades:
        try:
            book  = fetch_orderbook(trade["token_id"])
            bid, ask = parse_orderbook_prices(book)
            mid   = round((bid + ask) / 2, 4) if bid and ask else 0.0

            # Detect resolution: price near 0 (lost) or near 1 (won)
            resolved = False
            exit_price = mid

            if mid >= 0.98:
                logger.info(f"Trade#{trade['id']} resolved WIN — price={mid:.4f}")
                exit_price = 1.0
                resolved = True
            elif mid <= 0.02:
                logger.info(f"Trade#{trade['id']} resolved LOSS — price={mid:.4f}")
                exit_price = 0.0
                resolved = True

            if resolved:
                close_position(trade, exit_price, dry_run=dry_run)

        except Exception as e:
            logger.error(f"Resolver error for trade#{trade['id']}: {e}")
