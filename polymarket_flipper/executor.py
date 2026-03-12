"""
Order executor — places market orders via py-clob-client.
Handles £5/trade sizing, open position tracking, and P&L close.
"""
import logging
from typing import Optional
from dataclasses import dataclass

from config import (
    RISK_PER_TRADE_USDC, DAILY_LOSS_USDC,
    PRIVATE_KEY, API_KEY, API_SECRET, API_PASSPHRASE,
    CLOB_API_URL, GBP_TO_USDC,
)
import database as db

logger = logging.getLogger(__name__)


@dataclass
class OrderResult:
    success:  bool
    order_id: str = ""
    filled:   float = 0.0
    price:    float = 0.0
    error:    str = ""


def _get_client():
    """Return authenticated py-clob-client ClobClient."""
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import ApiCreds
        creds = ApiCreds(
            api_key        = API_KEY,
            api_secret     = API_SECRET,
            api_passphrase = API_PASSPHRASE,
        )
        return ClobClient(
            host      = CLOB_API_URL,
            chain_id  = 137,     # Polygon mainnet
            key       = PRIVATE_KEY,
            creds     = creds,
        )
    except ImportError:
        logger.error("py-clob-client not installed. Run: pip install py-clob-client")
        return None
    except Exception as e:
        logger.error(f"CLOB client init error: {e}")
        return None


def calc_shares(price: float) -> float:
    """Calculate shares to buy for £5 risk at given price."""
    if price <= 0:
        return 0
    usdc = RISK_PER_TRADE_USDC      # ~$6.35
    shares = usdc / price
    return round(shares, 2)


def place_buy(token_id: str, price: float, shares: float,
              strategy: str, market_id: str, reason: str,
              dry_run: bool = False) -> Optional[int]:
    """
    Place a market buy order. Returns DB trade_id on success, None on failure.
    Respects daily loss limit — will not open if limit hit.
    """
    if db.is_stopped_today():
        logger.warning("Daily loss limit reached — no new trades.")
        return None

    daily = db.get_daily()
    if abs(daily["pnl_usdc"]) >= DAILY_LOSS_USDC and daily["pnl_usdc"] < 0:
        logger.warning(f"Daily loss limit hit: ${daily['pnl_usdc']:.2f}")
        db.mark_daily_stopped()
        return None

    cost = round(price * shares, 4)
    logger.info(
        f"[{'DRY RUN' if dry_run else 'LIVE'}] BUY {shares} shares @ {price:.4f} "
        f"= ${cost:.2f} | {strategy} | {reason[:80]}"
    )

    if dry_run:
        return db.log_trade_open(strategy, market_id, token_id, "BUY", shares, price, reason)

    client = _get_client()
    if not client:
        return None

    try:
        from py_clob_client.clob_types import MarketOrderArgs, OrderType
        order = MarketOrderArgs(
            token_id = token_id,
            amount   = cost,
        )
        resp = client.create_market_order(order)
        order_id = resp.get("orderID", "")
        filled   = float(resp.get("takingAmount", cost) or cost)
        act_price = filled / shares if shares else price

        logger.info(f"Order placed: {order_id} | filled={filled:.4f}")
        return db.log_trade_open(strategy, market_id, token_id, "BUY", shares, act_price, reason)

    except Exception as e:
        logger.error(f"Order error: {e}")
        return None


def close_position(trade: dict, exit_price: float, dry_run: bool = False):
    """
    Close a position at exit_price. Calculates P&L and logs to DB.
    Called at resolution or manual exit.
    """
    pnl = round((exit_price - trade["entry_price"]) * trade["size"], 4)
    pnl_gbp = pnl / GBP_TO_USDC

    logger.info(
        f"CLOSE trade#{trade['id']} | entry={trade['entry_price']:.4f} "
        f"exit={exit_price:.4f} | P&L: ${pnl:+.4f} (£{pnl_gbp:+.4f})"
    )

    db.log_trade_close(trade["id"], exit_price, pnl, GBP_TO_USDC)

    # Check if daily loss limit now hit
    daily = db.get_daily()
    if daily["pnl_usdc"] <= -DAILY_LOSS_USDC:
        logger.warning(
            f"⛔ Daily loss limit reached: ${daily['pnl_usdc']:.2f} | "
            f"£{daily['pnl_gbp']:.2f} — STOPPING for today."
        )
        db.mark_daily_stopped()
