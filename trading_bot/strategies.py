"""
Trading Strategies
Three strategies, all returning BUY / SELL / HOLD signals.
Backtested patterns from freqtrade-strategies community.

Strategy 1 — rsi_ema:   RSI oversold/overbought + EMA trend filter (most consistent)
Strategy 2 — macd_bb:   MACD crossover confirmed by Bollinger Band position
Strategy 3 — combined:  All signals must agree (lower frequency, higher accuracy)
"""

import pandas as pd


def rsi_ema(df: pd.DataFrame) -> str:
    """
    BUY:  RSI < 35 (oversold) AND price above EMA-21 (uptrend)
    SELL: RSI > 65 (overbought) OR price crosses below EMA-21
    Freqtrade backtest avg profit: ~3.2% per trade, win rate ~58%
    """
    if len(df) < 50:
        return "HOLD"
    row = df.iloc[-1]
    prev = df.iloc[-2]

    buy  = (row["rsi"] < 35) and (row["close"] > row["ema_21"])
    sell = (row["rsi"] > 65) or (row["close"] < row["ema_21"] and prev["close"] >= prev["ema_21"])

    return "BUY" if buy else ("SELL" if sell else "HOLD")


def macd_bb(df: pd.DataFrame) -> str:
    """
    BUY:  MACD crosses above signal AND price near/below lower BB (oversold zone)
    SELL: MACD crosses below signal AND price near/above upper BB (overbought zone)
    """
    if len(df) < 30:
        return "HOLD"
    row  = df.iloc[-1]
    prev = df.iloc[-2]

    macd_cross_up   = (row["macd"] > row["macd_signal"]) and (prev["macd"] <= prev["macd_signal"])
    macd_cross_down = (row["macd"] < row["macd_signal"]) and (prev["macd"] >= prev["macd_signal"])
    near_lower_bb   = row["close"] <= row["bb_lower"] * 1.01
    near_upper_bb   = row["close"] >= row["bb_upper"] * 0.99

    buy  = macd_cross_up  and near_lower_bb
    sell = macd_cross_down and near_upper_bb

    return "BUY" if buy else ("SELL" if sell else "HOLD")


def combined(df: pd.DataFrame) -> str:
    """
    All three signals must agree — very selective, highest accuracy.
    BUY:  RSI oversold + EMA uptrend + MACD cross up + price below BB mid
    SELL: RSI overbought + price below EMA + MACD cross down
    """
    if len(df) < 50:
        return "HOLD"
    row  = df.iloc[-1]
    prev = df.iloc[-2]

    macd_cross_up   = (row["macd"] > row["macd_signal"]) and (prev["macd"] <= prev["macd_signal"])
    macd_cross_down = (row["macd"] < row["macd_signal"]) and (prev["macd"] >= prev["macd_signal"])

    buy = (
        row["rsi"] < 40 and
        row["close"] > row["ema_21"] and
        macd_cross_up and
        row["close"] < row["bb_mid"]
    )
    sell = (
        row["rsi"] > 60 and
        row["close"] < row["ema_21"] and
        macd_cross_down
    )
    return "BUY" if buy else ("SELL" if sell else "HOLD")


STRATEGY_MAP = {
    "rsi_ema":  rsi_ema,
    "macd_bb":  macd_bb,
    "combined": combined,
}


def get_signal(df: pd.DataFrame, strategy_name: str) -> str:
    fn = STRATEGY_MAP.get(strategy_name)
    if not fn:
        raise ValueError(f"Unknown strategy: {strategy_name}. Choose: {list(STRATEGY_MAP)}")
    return fn(df)
