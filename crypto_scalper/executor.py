"""
Order Executor — Crypto Scalper
=================================
Places market orders via ccxt (Binance spot).
SL/TP managed by main loop polling price — avoids OCO minimum notional issues.
Shorts skipped in spot mode (set defaultType=future in config to enable).
"""
import logging
from typing import Optional

import ccxt

from config import (
    BINANCE_API_KEY, BINANCE_API_SECRET, EXCHANGE_ID, USE_SANDBOX,
    ATR_SL_MULTIPLIER, ATR_TP_MULTIPLIER, GBP_TO_USDT,
    MAX_OPEN_TRADES, MAX_TRADES_PER_DAY,
)
import database as db
import bankroll as br
from signals import Signal

logger = logging.getLogger(__name__)

_exchange: Optional[object] = None


def _get_exchange():
    global _exchange
    if _exchange is not None:
        return _exchange
    try:
        cls = getattr(ccxt, EXCHANGE_ID)
        params = {
            "apiKey": BINANCE_API_KEY,
            "secret": BINANCE_API_SECRET,
            "options": {"defaultType": "spot"},
            "enableRateLimit": True,
        }
        if USE_SANDBOX:
            params["urls"] = {"api": "https://testnet.binance.vision/api"}
        _exchange = cls(params)
    except Exception as e:
        logger.error(f"Exchange init error: {e}")
    return _exchange


def _sl_tp(signal: Signal) -> tuple:
    entry = signal.entry_price
    atr   = signal.atr
    if signal.direction == "LONG":
        return entry - ATR_SL_MULTIPLIER * atr, entry + ATR_TP_MULTIPLIER * atr
    else:
        return entry + ATR_SL_MULTIPLIER * atr, entry - ATR_TP_MULTIPLIER * atr


def _guards_ok(size_gbp: float) -> bool:
    if br.is_stopped_today():
        logger.warning("Daily loss limit — no new trades.")
        return False
    if br.is_in_cooldown():
        logger.warning("Cooldown active — no new trades.")
        return False
    if db.count_today_trades() >= MAX_TRADES_PER_DAY:
        logger.info(f"Daily cap ({MAX_TRADES_PER_DAY}) reached.")
        return False
    if db.count_open_trades() >= MAX_OPEN_TRADES:
        logger.debug(f"Max open trades ({MAX_OPEN_TRADES}) reached.")
        return False
    return size_gbp > 0


def open_trade(signal: Signal, dry_run: bool = False) -> Optional[int]:
    size_gbp  = br.size_for_confidence(signal.confidence)
    size_usdt = br.size_usdt(signal.confidence)

    if not _guards_ok(size_gbp):
        return None

    sl, tp = _sl_tp(signal)

    logger.info(
        f"[{'DRY' if dry_run else 'LIVE'}] {signal.direction} {signal.symbol} "
        f"@ {signal.entry_price:.6f} | conf={signal.confidence:.3f} | "
        f"£{size_gbp:.2f} / ${size_usdt:.2f} | SL={sl:.6f} TP={tp:.6f}"
    )

    order_id = ""

    if not dry_run:
        exchange = _get_exchange()
        if not exchange:
            return None

        if signal.direction == "SHORT":
            logger.warning(f"SHORT on {signal.symbol} skipped — spot mode (longs only).")
            return None

        try:
            qty   = round(size_usdt / signal.entry_price, 6)
            order = exchange.create_market_buy_order(signal.symbol, qty)
            order_id = str(order.get("id", ""))
            if order.get("average"):
                avg_price = float(order["average"])
                signal    = Signal(
                    symbol=signal.symbol, direction=signal.direction,
                    confidence=signal.confidence, entry_price=avg_price,
                    atr=signal.atr, reason=signal.reason, votes=signal.votes,
                )
                sl, tp = _sl_tp(signal)
        except ccxt.InsufficientFunds as e:
            logger.error(f"Insufficient funds {signal.symbol}: {e}")
            return None
        except ccxt.InvalidOrder as e:
            logger.warning(f"Invalid order {signal.symbol} (below min notional?): {e}")
            return None
        except Exception as e:
            logger.error(f"Order error {signal.symbol}: {e}", exc_info=True)
            return None

    return db.log_trade_open(
        symbol      = signal.symbol,
        direction   = signal.direction,
        size_gbp    = size_gbp,
        size_usdt   = size_usdt,
        entry_price = signal.entry_price,
        sl_price    = sl,
        tp_price    = tp,
        confidence  = signal.confidence,
        atr         = signal.atr,
        reason      = signal.reason[:300],
        order_id    = order_id,
    )


def close_trade(trade: dict, exit_price: float, exit_reason: str, dry_run: bool = False):
    entry     = trade["entry_price"]
    size_usdt = trade["size_usdt"]
    direction = trade["direction"]

    if direction == "LONG":
        pnl_usdt = (exit_price - entry) / entry * size_usdt
    else:
        pnl_usdt = (entry - exit_price) / entry * size_usdt

    pnl_gbp = round(pnl_usdt / GBP_TO_USDT, 4)

    logger.info(
        f"CLOSE #{trade['id']} {trade['symbol']} {direction} | "
        f"entry={entry:.6f} exit={exit_price:.6f} | "
        f"{exit_reason} | P&L: ${pnl_usdt:+.4f} / £{pnl_gbp:+.4f}"
    )

    if not dry_run:
        exchange = _get_exchange()
        if exchange and direction == "LONG":
            try:
                qty = round(size_usdt / entry, 6)
                exchange.create_market_sell_order(trade["symbol"], qty)
            except Exception as e:
                logger.error(f"Close order error {trade['symbol']}: {e}")

    db.log_trade_close(trade["id"], exit_price, exit_reason, pnl_gbp)
    br.record_trade_result(pnl_gbp, won=pnl_gbp > 0)


def get_current_price(symbol: str) -> Optional[float]:
    exchange = _get_exchange()
    if not exchange:
        return None
    try:
        ticker = exchange.fetch_ticker(symbol)
        bid    = ticker.get("bid") or 0
        ask    = ticker.get("ask") or 0
        if bid and ask:
            return (bid + ask) / 2.0
        return ticker.get("last")
    except Exception as e:
        logger.warning(f"Price fetch error {symbol}: {e}")
        return None
