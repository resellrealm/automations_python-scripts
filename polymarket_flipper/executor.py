"""
Order executor — places market orders via py-clob-client.
Dynamic sizing from bankroll.py — trade size scales with balance.
"""
import logging
from typing import Optional
from dataclasses import dataclass

from config import (
    PRIVATE_KEY, API_KEY, API_SECRET, API_PASSPHRASE,
    CLOB_API_URL, GBP_TO_USDC, MAX_OPEN_TRADES, TAKER_FEE,
    MAX_TRADES_PER_DAY,
)
import database as db
import bankroll as br
import trade_logger as tl

logger = logging.getLogger(__name__)


@dataclass
class OrderResult:
    success:  bool
    order_id: str  = ""
    filled:   float = 0.0
    price:    float = 0.0
    error:    str  = ""


def _get_client():
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import ApiCreds
        creds = ApiCreds(
            api_key        = API_KEY,
            api_secret     = API_SECRET,
            api_passphrase = API_PASSPHRASE,
        )
        return ClobClient(
            host     = CLOB_API_URL,
            chain_id = 137,
            key      = PRIVATE_KEY,
            creds    = creds,
        )
    except ImportError:
        logger.error("py-clob-client not installed. Run: pip install py-clob-client")
        return None
    except Exception as e:
        logger.error(f"CLOB client init error: {e}")
        return None


def calc_shares(price: float, strategy: str = "OBMismatch", confidence: float = 1.0) -> float:
    """
    Calculate shares for current bankroll-sized trade at given price.
    Dynamic: scales with balance as bankroll grows.
    Confidence (0–1) reduces size proportionally (floor 50%).
    """
    if price <= 0:
        return 0
    usdc = br.trade_size_usdc(strategy, GBP_TO_USDC, confidence=confidence)
    shares = usdc / price
    return round(shares, 2)


def place_buy(
    token_id: str,
    price:    float,
    shares:   float,
    strategy: str,
    market_id: str,
    reason:   str,
    dry_run:  bool = False,
) -> Optional[int]:
    """
    Place a buy order. Returns DB trade_id on success.
    Checks: daily loss limit, max open trades, min price.
    """
    # ── Guards ────────────────────────────────────────────────────
    if br.is_stopped_today():
        logger.warning("Daily loss limit reached — no new trades.")
        return None

    if br.is_in_cooldown():
        logger.warning("Post-loss cooldown active — no new trades.")
        return None

    if db.count_today_trades() >= MAX_TRADES_PER_DAY:
        logger.info(f"Daily trade cap ({MAX_TRADES_PER_DAY}) reached — no new trades today.")
        return None

    if db.count_open_trades() >= MAX_OPEN_TRADES:
        logger.debug(f"Max open trades ({MAX_OPEN_TRADES}) reached — skipping.")
        return None

    if price <= 0 or shares <= 0:
        return None

    cost_usdc  = round(price * shares, 4)
    cost_gbp   = round(cost_usdc / GBP_TO_USDC, 2)

    if not br.can_add_exposure(cost_gbp):
        logger.warning(
            f"Exposure limit — £{cost_gbp:.2f} would push total above "
            f"70% of balance (currently £{br.get_open_exposure_gbp():.2f} open). Skipping."
        )
        return None

    logger.info(
        f"[{'DRY RUN' if dry_run else 'LIVE'}] BUY {shares:.2f} @ {price:.4f} "
        f"= ${cost_usdc:.2f} / £{cost_gbp:.2f} | {strategy} | {reason[:80]}"
    )

    if dry_run:
        tid = db.log_trade_open(strategy, market_id, token_id, "BUY", shares, price, reason)
        if tid:
            tl.log_open(tid, strategy, market_id, token_id, "BUY", shares, price, reason)
        return tid

    client = _get_client()
    if not client:
        return None

    try:
        from py_clob_client.clob_types import MarketOrderArgs
        order = MarketOrderArgs(token_id=token_id, amount=cost_usdc)
        resp  = client.create_market_order(order)
        order_id  = resp.get("orderID", "")
        filled    = float(resp.get("takingAmount", cost_usdc) or cost_usdc)
        act_price = filled / shares if shares else price

        logger.info(f"Order placed: {order_id} | filled=${filled:.4f}")
        tid = db.log_trade_open(strategy, market_id, token_id, "BUY", shares, act_price, reason)
        if tid:
            tl.log_open(tid, strategy, market_id, token_id, "BUY", shares, act_price, reason)
        return tid

    except Exception as e:
        logger.error(f"Order error: {e}")
        return None


def close_position(trade: dict, exit_price: float, dry_run: bool = False):
    """
    Close a position. Updates bankroll with actual P&L.
    """
    size = trade["size"]
    entry = trade["entry_price"]

    # Gross P&L
    gross_pnl_usdc = round((exit_price - entry) * size, 4)

    # Deduct taker fee on exit leg
    fee_usdc = round(exit_price * size * TAKER_FEE, 4)
    net_pnl_usdc = round(gross_pnl_usdc - fee_usdc, 4)

    net_pnl_gbp = round(net_pnl_usdc / GBP_TO_USDC, 4)
    won = net_pnl_usdc > 0

    logger.info(
        f"CLOSE trade#{trade['id']} | entry={entry:.4f} exit={exit_price:.4f} "
        f"| gross=${gross_pnl_usdc:+.4f} fee=${fee_usdc:.4f} net=${net_pnl_usdc:+.4f} "
        f"(£{net_pnl_gbp:+.4f})"
    )

    db.log_trade_close(trade["id"], exit_price, net_pnl_usdc, GBP_TO_USDC)
    br.record_trade_result(net_pnl_gbp, won=won)
    tl.log_close(trade["id"], trade.get("strategy", ""), exit_price, net_pnl_usdc, net_pnl_gbp, won)

    if br.is_stopped_today():
        logger.warning(
            f"⛔ Daily loss limit hit — stopping for today.\n"
            f"   {br.status_line()}"
        )
