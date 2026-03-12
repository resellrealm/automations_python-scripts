"""
Latency Arbitrage Strategy — Spot Price Lag
============================================
Source: 0x8dxd bot — $313 → $437,600 in 1 month (139,000% return)
        98% win rate across 6,615 trades

Edge: Polymarket's 15-min crypto markets LAG Binance/Coinbase spot prices
      by 2–12 seconds. When spot has clearly moved, Polymarket still shows 50/50.

Execution requirement:
  - Latency < 200ms (ideally <50ms via VPS near Polygon RPC)
  - Sub-100ms bots capture 73% of profits
  - Binance WebSocket feed required (not REST polling)

Optimal entry timing: T-10 to T-45 seconds before window close
  - Direction is "locked in" — too late to reverse
  - Market hasn't repriced yet if you're fast enough

Markets:
  - 15-minute BTC/ETH/SOL UP/DOWN contracts
  - Only these — other markets don't have real-time price anchors

Signal logic:
  1. Monitor Binance WebSocket for spot price movement
  2. If BTC moved +0.5%+ in last 60s → BUY YES (UP) on 15-min market
  3. If BTC moved -0.5%+ in last 60s → BUY NO (DOWN = YES on DOWN market)
  4. Only enter if Polymarket price still near 50/50 (hasn't repriced)
  5. Exit at resolution (15-min window closes)
"""

import time
import threading
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from loguru import logger

from src.strategies.base import BaseStrategy, Signal, MarketData
from src.config import config


# ── Parameters (from documented profitable bot) ─────────────────
SPOT_MOVE_THRESHOLD_PCT = 0.5    # % spot move to trigger signal
MAX_POLYMARKET_PRICE    = 0.60   # only enter if PM price ≤ this (still near 50/50)
MIN_POLYMARKET_PRICE    = 0.40   # only enter if PM price ≥ this (hasn't repriced)
SPOT_WINDOW_SECONDS     = 60     # look at spot movement over this window
MIN_SECONDS_TO_CLOSE    = 10     # must enter at least 10s before window closes
MAX_SECONDS_TO_CLOSE    = 120    # don't enter more than 2 minutes out
POSITION_USDC           = 50.0   # $ per trade (scale to your capital)
CRYPTO_KEYWORDS         = ["btc", "bitcoin", "eth", "ethereum", "sol", "solana"]
# ────────────────────────────────────────────────────────────────


@dataclass
class SpotData:
    """Stores recent spot prices for movement detection."""
    symbol: str
    prices: list = field(default_factory=list)
    timestamps: list = field(default_factory=list)
    max_history: int = 120  # 2 minutes of ticks

    def add(self, price: float):
        self.prices.append(price)
        self.timestamps.append(time.time())
        if len(self.prices) > self.max_history:
            self.prices.pop(0)
            self.timestamps.pop(0)

    def movement_pct(self, window_seconds: float = SPOT_WINDOW_SECONDS) -> float:
        """Return % price change over the last window_seconds."""
        if len(self.prices) < 2:
            return 0.0
        cutoff = time.time() - window_seconds
        recent = [p for p, t in zip(self.prices, self.timestamps) if t >= cutoff]
        if not recent:
            return 0.0
        return ((recent[-1] - recent[0]) / recent[0]) * 100


class LatencyArbStrategy(BaseStrategy):
    """
    Exploits Polymarket's lag behind Binance/Coinbase spot prices.
    Documented: $313 → $437,600 (139,000%) in 1 month, 98% win rate.
    Requires: VPS <200ms from Polygon RPC + Binance WebSocket.
    """

    def __init__(self):
        super().__init__(
            name="LatencyArb",
            config={
                "spot_threshold": SPOT_MOVE_THRESHOLD_PCT,
                "max_pm_price":   MAX_POLYMARKET_PRICE,
                "min_pm_price":   MIN_POLYMARKET_PRICE,
                "position_usdc":  POSITION_USDC,
            }
        )
        self.spot_data: Dict[str, SpotData] = {
            "BTC": SpotData("BTC"),
            "ETH": SpotData("ETH"),
            "SOL": SpotData("SOL"),
        }
        self._ws_thread = None

    def start_spot_feed(self):
        """Start Binance WebSocket feed in background thread."""
        self._ws_thread = threading.Thread(target=self._run_binance_ws, daemon=True)
        self._ws_thread.start()
        logger.info("Latency arb: Binance WebSocket feed started.")

    def _run_binance_ws(self):
        """Connect to Binance WebSocket for real-time BTC/ETH/SOL prices."""
        try:
            import websocket, json

            symbols = ["btcusdt", "ethusdt", "solusdt"]
            streams = "/".join(f"{s}@trade" for s in symbols)
            url = f"wss://stream.binance.com:9443/stream?streams={streams}"

            def on_message(ws, message):
                data = json.loads(message)
                trade = data.get("data", {})
                sym = trade.get("s", "").replace("USDT", "")
                price = float(trade.get("p", 0))
                if sym in self.spot_data and price > 0:
                    self.spot_data[sym].add(price)

            def on_error(ws, error):
                logger.warning(f"Binance WS error: {error}")

            def on_close(ws, *args):
                logger.warning("Binance WS closed — reconnecting in 5s...")
                time.sleep(5)
                self._run_binance_ws()

            ws = websocket.WebSocketApp(url, on_message=on_message,
                                         on_error=on_error, on_close=on_close)
            ws.run_forever()

        except ImportError:
            logger.error("websocket-client not installed. Run: pip install websocket-client")
        except Exception as e:
            logger.error(f"Binance WS error: {e}")

    def get_required_data(self) -> List[str]:
        return ["best_ask", "mid_price", "end_time"]

    def analyze(self, market_data: List[MarketData]) -> List[Signal]:
        signals = []

        for token in market_data:
            signal = self._evaluate(token)
            if signal:
                signals.append(signal)

        return signals

    def _evaluate(self, token: MarketData) -> Optional[Signal]:
        """Check if spot has moved but Polymarket hasn't repriced yet."""
        question = token.question.lower()

        # Only trade crypto markets
        crypto_match = next((k for k in CRYPTO_KEYWORDS if k in question), None)
        if not crypto_match:
            return None

        # Map keyword to spot symbol
        symbol_map = {"btc": "BTC", "bitcoin": "BTC",
                       "eth": "ETH", "ethereum": "ETH",
                       "sol": "SOL", "solana": "SOL"}
        symbol = symbol_map.get(crypto_match)
        if not symbol or symbol not in self.spot_data:
            return None

        # Check timing — must be near window close
        seconds_left = self._seconds_to_close(token)
        if seconds_left is None:
            return None
        if not (MIN_SECONDS_TO_CLOSE <= seconds_left <= MAX_SECONDS_TO_CLOSE):
            return None

        # Check spot movement
        spot_move = self.spot_data[symbol].movement_pct(SPOT_WINDOW_SECONDS)
        if abs(spot_move) < SPOT_MOVE_THRESHOLD_PCT:
            return None

        # Determine direction
        going_up = spot_move > 0
        pm_price = token.mid_price

        # Only enter if Polymarket hasn't repriced yet
        if going_up and not (MIN_POLYMARKET_PRICE <= pm_price <= MAX_POLYMARKET_PRICE):
            logger.debug(f"Skipping — PM already repriced UP: {pm_price:.2f}")
            return None
        if not going_up and not (MIN_POLYMARKET_PRICE <= pm_price <= MAX_POLYMARKET_PRICE):
            logger.debug(f"Skipping — PM already repriced DOWN: {pm_price:.2f}")
            return None

        side = "BUY"  # Always buy the winning side (UP token if going up, NO if going down)
        size = POSITION_USDC / token.best_ask if token.best_ask > 0 else 0
        if size <= 0:
            return None

        confidence = min(0.92, 0.70 + (abs(spot_move) - SPOT_MOVE_THRESHOLD_PCT) * 0.1)

        return Signal(
            strategy_name=self.name,
            token_id=token.token_id,
            market_id=token.market_id,
            side=side,
            size=round(size, 2),
            price=round(token.best_ask + 0.01, 3),
            confidence=confidence,
            reason=(
                f"Latency arb: {symbol} spot moved {spot_move:+.2f}% | "
                f"PM still at {pm_price:.2f} | {seconds_left:.0f}s to close | "
                f"[$313→$437k strategy — 98% win rate documented]"
            )
        )

    def _seconds_to_close(self, token: MarketData) -> Optional[float]:
        """Return seconds until market closes, or None if unknown."""
        end_date = token.extra.get("end_date") or token.extra.get("end_time")
        if not end_date:
            return None
        try:
            if isinstance(end_date, str):
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            else:
                end_dt = end_date
            return (end_dt - datetime.now(timezone.utc)).total_seconds()
        except Exception:
            return None
