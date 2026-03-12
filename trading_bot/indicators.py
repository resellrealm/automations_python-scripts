"""
Technical Indicators
Pure pandas/numpy — no TA-Lib dependency needed.
Patterns borrowed from freqtrade-strategies community repos.
"""

import pandas as pd
import numpy as np


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    return series.rolling(window=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Returns (macd_line, signal_line, histogram)."""
    fast_ema   = ema(series, fast)
    slow_ema   = ema(series, slow)
    macd_line  = fast_ema - slow_ema
    signal_line = ema(macd_line, signal)
    histogram  = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series, period: int = 20, std: float = 2.0):
    """Returns (upper, middle, lower)."""
    middle = sma(series, period)
    stddev = series.rolling(window=period).std()
    upper  = middle + std * stddev
    lower  = middle - std * stddev
    return upper, middle, lower


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range — used for position sizing and stop placement."""
    high, low, close = df["high"], df["low"], df["close"]
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(com=period - 1, min_periods=period).mean()


def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add all indicators to an OHLCV dataframe."""
    df = df.copy()
    close = df["close"]

    df["ema_9"]   = ema(close, 9)
    df["ema_21"]  = ema(close, 21)
    df["ema_50"]  = ema(close, 50)
    df["rsi"]     = rsi(close, 14)
    df["macd"], df["macd_signal"], df["macd_hist"] = macd(close)
    df["bb_upper"], df["bb_mid"], df["bb_lower"] = bollinger_bands(close)
    df["atr"]     = atr(df)

    # Volume moving average
    df["vol_ma"]  = sma(df["volume"], 20)
    df["vol_spike"] = df["volume"] > df["vol_ma"] * 1.5

    return df
