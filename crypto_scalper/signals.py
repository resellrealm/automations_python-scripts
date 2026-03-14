"""
Signal Engine — RSI(6,12,24) + Bollinger Bands + VWAP + Volume Surge
======================================================================
All indicators vote independently. Confidence = weighted vote sum.
Dual timeframe: 5m generates signal, 15m gates direction agreement.
"""
import logging
from dataclasses import dataclass, field
from typing import Optional, Literal

import numpy as np
import ccxt

from config import (
    TIMEFRAME_FAST, TIMEFRAME_SLOW, CANDLES_NEEDED,
    RSI_SHORT, RSI_MID, RSI_LONG,
    BB_PERIOD, BB_STD, ATR_PERIOD,
    VOLUME_SURGE_MULTIPLIER, RSI_OVERSOLD, RSI_OVERBOUGHT,
    WEIGHTS, MIN_CONFIDENCE, BINANCE_API_KEY, BINANCE_API_SECRET,
    EXCHANGE_ID, USE_SANDBOX,
)

logger = logging.getLogger(__name__)

Direction = Literal["LONG", "SHORT", "NONE"]


@dataclass
class Signal:
    symbol:      str
    direction:   Direction
    confidence:  float
    entry_price: float
    atr:         float
    reason:      str
    votes:       dict = field(default_factory=dict)


# ── Indicator math (pure numpy) ───────────────────────────────────────

def _rsi(closes: np.ndarray, period: int) -> float:
    if len(closes) < period + 1:
        return 50.0
    deltas   = np.diff(closes)
    gains    = np.where(deltas > 0, deltas, 0.0)
    losses   = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = gains[:period].mean()
    avg_loss = losses[:period].mean()
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    return 100.0 - (100.0 / (1.0 + avg_gain / avg_loss))


def _bollinger(closes: np.ndarray, period: int, std_mult: float) -> tuple:
    if len(closes) < period:
        mid = closes[-1]
        return mid, mid, mid
    window = closes[-period:]
    mid    = window.mean()
    std    = window.std()
    return mid - std * std_mult, mid, mid + std * std_mult


def _atr(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int) -> float:
    if len(closes) < 2:
        return 0.0
    trs = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i]  - closes[i - 1]),
        )
        trs.append(tr)
    return float(np.array(trs[-period:]).mean()) if trs else 0.0


def _vwap(highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, volumes: np.ndarray) -> float:
    typical  = (highs + lows + closes) / 3.0
    total_vol = volumes.sum()
    if total_vol == 0:
        return float(closes[-1])
    return float((typical * volumes).sum() / total_vol)


# ── Vote functions (+1 = LONG, -1 = SHORT, 0 = neutral) ──────────────

def _vote_rsi(rsi_val: float, label: str) -> tuple:
    if rsi_val <= RSI_OVERSOLD:
        return 1.0, f"RSI({label})={rsi_val:.1f} oversold"
    if rsi_val >= RSI_OVERBOUGHT:
        return -1.0, f"RSI({label})={rsi_val:.1f} overbought"
    mid        = (RSI_OVERSOLD + RSI_OVERBOUGHT) / 2
    normalized = (rsi_val - mid) / (RSI_OVERBOUGHT - mid)
    return -normalized * 0.4, f"RSI({label})={rsi_val:.1f} neutral"


def _vote_bb(close: float, lower: float, upper: float, mid: float) -> tuple:
    band_width = upper - lower
    if band_width == 0:
        return 0.0, "BB=zero width"
    if close <= lower:
        return 1.0, "BB: at/below lower band"
    if close >= upper:
        return -1.0, "BB: at/above upper band"
    position = (close - mid) / (band_width / 2)
    return -position * 0.5, f"BB: {position*100:.0f}% of band"


def _vote_vwap(close: float, vwap: float) -> tuple:
    if close < vwap:
        spread_pct = (vwap - close) / vwap * 100
        score = min(1.0, spread_pct / 0.5)
        return score, f"VWAP: {spread_pct:.2f}% below VWAP"
    if close > vwap:
        spread_pct = (close - vwap) / vwap * 100
        score = min(1.0, spread_pct / 0.5)
        return -score, f"VWAP: {spread_pct:.2f}% above VWAP"
    return 0.0, "VWAP: at VWAP"


def _vote_volume(volumes: np.ndarray, period: int = 20) -> tuple:
    if len(volumes) < period + 1:
        return 0.0, "Volume: insufficient history"
    avg  = volumes[-period - 1:-1].mean()
    last = volumes[-1]
    if avg > 0 and last >= avg * VOLUME_SURGE_MULTIPLIER:
        return 1.0, f"Volume: surge {last/avg:.1f}x avg"
    return 0.0, "Volume: no surge"


# ── Core builder ──────────────────────────────────────────────────────

def _build_signal(symbol: str, ohlcv_fast: list, ohlcv_slow: list) -> Optional[Signal]:
    if len(ohlcv_fast) < CANDLES_NEEDED or len(ohlcv_slow) < 20:
        return None

    arr_f     = np.array(ohlcv_fast, dtype=float)
    closes_f  = arr_f[:, 4]
    highs_f   = arr_f[:, 2]
    lows_f    = arr_f[:, 3]
    volumes_f = arr_f[:, 5]

    closes_s = np.array(ohlcv_slow, dtype=float)[:, 4]

    price = float(closes_f[-1])

    rsi_s  = _rsi(closes_f, RSI_SHORT)
    rsi_m  = _rsi(closes_f, RSI_MID)
    rsi_l  = _rsi(closes_f, RSI_LONG)
    bb_lo, bb_mid, bb_hi = _bollinger(closes_f, BB_PERIOD, BB_STD)
    vwap   = _vwap(highs_f, lows_f, closes_f, volumes_f)
    atr    = _atr(highs_f, lows_f, closes_f, ATR_PERIOD)

    rsi_slow  = _rsi(closes_s, RSI_MID)
    slow_bias = "LONG" if rsi_slow < 50 else "SHORT"

    raw_votes = {}
    reasons   = []

    for key, rsi_val, label in [
        ("rsi_short", rsi_s, str(RSI_SHORT)),
        ("rsi_mid",   rsi_m, str(RSI_MID)),
        ("rsi_long",  rsi_l, str(RSI_LONG)),
    ]:
        v, r = _vote_rsi(rsi_val, label)
        raw_votes[key] = v
        reasons.append(r)

    v, r = _vote_bb(price, bb_lo, bb_hi, bb_mid)
    raw_votes["bb"] = v
    reasons.append(r)

    v, r = _vote_vwap(price, vwap)
    raw_votes["vwap"] = v
    reasons.append(r)

    v, r = _vote_volume(volumes_f)
    raw_votes["volume"] = v
    reasons.append(r)

    directional_keys = ["rsi_short", "rsi_mid", "rsi_long", "bb", "vwap"]
    weighted_sum = sum(raw_votes[k] * WEIGHTS[k] for k in directional_keys)

    # Volume amplifies in the dominant direction
    if raw_votes["volume"] > 0:
        weighted_sum += WEIGHTS["volume"] * (1.0 if weighted_sum >= 0 else -1.0)

    if weighted_sum > 0:
        direction: Direction = "LONG"
    elif weighted_sum < 0:
        direction = "SHORT"
    else:
        return None

    confidence = abs(weighted_sum)

    if direction != slow_bias:
        confidence *= 0.60
        reasons.append(f"15m disagrees ({slow_bias}) — conf cut to {confidence:.2f}")
    else:
        reasons.append(f"15m agrees ({slow_bias})")

    if confidence < MIN_CONFIDENCE:
        logger.debug(f"{symbol}: conf={confidence:.3f} < {MIN_CONFIDENCE} — skip")
        return None

    return Signal(
        symbol      = symbol,
        direction   = direction,
        confidence  = round(confidence, 4),
        entry_price = price,
        atr         = round(atr, 8),
        reason      = " | ".join(reasons),
        votes       = raw_votes,
    )


# ── Exchange singleton ────────────────────────────────────────────────

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


def fetch_signal(symbol: str) -> Optional[Signal]:
    exchange = _get_exchange()
    if not exchange:
        return None
    try:
        fast = exchange.fetch_ohlcv(symbol, TIMEFRAME_FAST, limit=CANDLES_NEEDED + 5)
        slow = exchange.fetch_ohlcv(symbol, TIMEFRAME_SLOW, limit=30)
    except ccxt.NetworkError as e:
        logger.warning(f"{symbol}: network error — {e}")
        return None
    except ccxt.ExchangeError as e:
        logger.warning(f"{symbol}: exchange error — {e}")
        return None
    except Exception as e:
        logger.error(f"{symbol}: OHLCV fetch failed — {e}")
        return None
    return _build_signal(symbol, fast, slow)
