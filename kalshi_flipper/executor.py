"""Order executor — places Kalshi orders with risk management."""

import logging
from typing import Optional
from config import RISK_PER_TRADE_USD, DAILY_LOSS_USD, GBP_TO_USD
import database as db

logger = logging.getLogger(__name__)


def check_limits() -> bool:
    """Return True if we can still trade today."""
    if db.is_stopped():
        logger.warning("Daily loss limit hit — no new trades.")
        return False
    daily = db.get_daily()
    if daily["pnl_usd"] <= -DAILY_LOSS_USD:
        logger.warning(f"Daily loss limit reached: ${daily['pnl_usd']:.2f}")
        db.mark_stopped()
        return False
    return True


def place_trade(client, ticker: str, side: str, strategy: str,
                reason: str, dry_run: bool = False) -> Optional[int]:
    """
    Place a single Kalshi order sized to £5 risk.
    Returns DB trade ID on success, None on failure.
    """
    if not check_limits():
        return None

    try:
        # Get current price to calculate contracts
        market_data = client.get_market(ticker)
        market      = market_data.get("market", market_data)

        if side == "yes":
            price_cents = market.get("yes_ask", 50)
        else:
            price_cents = 100 - market.get("yes_bid", 50)

        if not price_cents or price_cents <= 0:
            logger.warning(f"No valid price for {ticker} side={side}")
            return None

        contracts = client.calc_contracts(RISK_PER_TRADE_USD, price_cents)
        cost      = (price_cents / 100) * contracts
        fee       = client.calc_fee(contracts, price_cents)

        logger.info(
            f"[{'DRY RUN' if dry_run else 'LIVE'}] {strategy} | "
            f"BUY {side.upper()} {ticker} | "
            f"{contracts} contracts @ {price_cents}¢ = ${cost:.2f} + ${fee:.2f} fee | "
            f"{reason[:70]}"
        )

        if dry_run:
            return db.log_open(strategy, ticker, side, contracts, price_cents, reason)

        resp = client.place_order(
            ticker     = ticker,
            side       = side,
            count      = contracts,
            order_type = "market",
        )
        logger.info(f"Order placed: {resp.get('order', {}).get('order_id', 'unknown')}")
        return db.log_open(strategy, ticker, side, contracts, price_cents, reason)

    except Exception as e:
        logger.error(f"place_trade error {ticker}: {e}")
        return None


def place_no_bundle(client, legs: list, strategy: str,
                    reason: str, dry_run: bool = False) -> int:
    """
    Place NO orders on all legs of a bundle arb.
    Splits £5 budget across all legs equally.
    Returns number of legs successfully placed.
    """
    if not check_limits():
        return 0

    budget_per_leg = RISK_PER_TRADE_USD / max(len(legs), 1)
    placed = 0

    for leg in legs:
        ticker      = leg["ticker"]
        price_cents = leg["no_price_cents"]
        contracts   = client.calc_contracts(budget_per_leg, price_cents)

        logger.info(
            f"[{'DRY RUN' if dry_run else 'LIVE'}] NO bundle leg | "
            f"BUY NO {ticker} | {contracts}c @ {price_cents}¢ | {reason[:50]}"
        )

        if dry_run:
            db.log_open(strategy, ticker, "no", contracts, price_cents, reason)
            placed += 1
            continue

        try:
            client.place_order(ticker=ticker, side="no", count=contracts)
            db.log_open(strategy, ticker, "no", contracts, price_cents, reason)
            placed += 1
        except Exception as e:
            logger.error(f"Bundle leg failed {ticker}: {e}")

    return placed


def close_resolved(client, dry_run: bool = False):
    """Check open trades and close any that have resolved."""
    open_trades = db.get_open_trades()
    if not open_trades:
        return

    for trade in open_trades:
        try:
            market_data = client.get_market(trade["ticker"])
            market      = market_data.get("market", market_data)
            result      = market.get("result")  # "yes" | "no" | None

            if result is None:
                continue  # still open

            won = (result == trade["side"])
            exit_cents = 100 if won else 0
            pnl = ((exit_cents - trade["entry_cents"]) / 100) * trade["contracts"]

            logger.info(
                f"CLOSED trade#{trade['id']} {trade['ticker']} {trade['side'].upper()} | "
                f"result={result.upper()} | {'WON' if won else 'LOST'} | "
                f"P&L: ${pnl:+.2f}"
            )

            if not dry_run:
                db.log_close(trade["id"], exit_cents, pnl, GBP_TO_USD)

            # Check daily loss limit after close
            daily = db.get_daily()
            if daily["pnl_usd"] <= -DAILY_LOSS_USD:
                logger.warning(f"⛔ Daily loss limit hit: ${daily['pnl_usd']:.2f} — stopping.")
                db.mark_stopped()

        except Exception as e:
            logger.error(f"close_resolved error trade#{trade['id']}: {e}")
