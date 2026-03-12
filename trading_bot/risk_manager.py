"""
Risk Manager
Position sizing using the 1% rule + ATR-based stop placement.
Pattern from freqtrade community and hummingbot risk controls.
"""

import pandas as pd
from config import Config
from shared.logger import get_logger
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logger = get_logger("risk_manager")


def calculate_position_size(
    balance: float,
    entry_price: float,
    atr: float,
    atr_multiplier: float = 1.5,
) -> dict:
    """
    1% risk rule: never risk more than 1% of portfolio per trade.
    Stop distance = ATR * multiplier (dynamic, adapts to volatility).

    Returns:
        {
            "size": float,         # quantity to buy
            "stop_price": float,   # stoploss price
            "risk_amount": float,  # £/$ risked
            "stop_pct": float,     # stop % from entry
        }
    """
    risk_amount = balance * (Config.RISK_PER_TRADE_PCT / 100)
    stop_distance = atr * atr_multiplier
    stop_price = entry_price - stop_distance
    stop_pct = (stop_distance / entry_price) * 100

    # Cap stop to configured max
    if stop_pct > Config.STOPLOSS_PCT:
        stop_distance = entry_price * (Config.STOPLOSS_PCT / 100)
        stop_price = entry_price - stop_distance
        stop_pct = Config.STOPLOSS_PCT

    size = risk_amount / stop_distance if stop_distance > 0 else 0
    take_profit = entry_price * (1 + Config.TAKE_PROFIT_PCT / 100)

    return {
        "size":         round(size, 6),
        "stop_price":   round(stop_price, 4),
        "take_profit":  round(take_profit, 4),
        "risk_amount":  round(risk_amount, 2),
        "stop_pct":     round(stop_pct, 2),
    }


def check_trailing_stop(entry_price: float, current_price: float, highest_price: float) -> bool:
    """
    Trailing stop: if price pulls back Config.STOPLOSS_PCT from peak, exit.
    Returns True if stop should trigger.
    """
    if not Config.TRAILING_STOP:
        return False
    trail_stop = highest_price * (1 - Config.STOPLOSS_PCT / 100)
    return current_price <= trail_stop


def should_exit(entry_price: float, current_price: float, stop_price: float, take_profit: float) -> str:
    """Returns 'stoploss', 'take_profit', or 'hold'."""
    if current_price <= stop_price:
        return "stoploss"
    if current_price >= take_profit:
        return "take_profit"
    return "hold"
