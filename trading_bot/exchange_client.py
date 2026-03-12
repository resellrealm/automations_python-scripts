"""
Exchange Client
Wraps CCXT — supports Binance, Kraken, Coinbase, Bybit, OKX and 40+ others.
DRY_RUN=true → simulates orders, never touches real money.
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import ccxt
import pandas as pd
from typing import Optional
from config import Config
from shared.logger import get_logger

logger = get_logger("exchange_client")


class ExchangeClient:
    def __init__(self):
        exchange_class = getattr(ccxt, Config.EXCHANGE, None)
        if not exchange_class:
            raise ValueError(f"Unknown exchange: {Config.EXCHANGE}")

        self.exchange = exchange_class({
            "apiKey":  Config.API_KEY,
            "secret":  Config.API_SECRET,
            "enableRateLimit": True,
            "options": {"defaultType": "spot"},
        })
        self.dry_run = Config.DRY_RUN
        if self.dry_run:
            logger.info(f"DRY RUN mode — connected to {Config.EXCHANGE} (no real orders)")
        else:
            logger.info(f"LIVE mode — connected to {Config.EXCHANGE}")

    def get_balance(self) -> float:
        """Return USDT balance."""
        try:
            balance = self.exchange.fetch_balance()
            return float(balance["USDT"]["free"])
        except Exception as e:
            logger.error(f"Balance fetch failed: {e}")
            return 0.0

    def get_ohlcv(self, pair: str, timeframe: str = None, limit: int = 200) -> pd.DataFrame:
        """Fetch OHLCV candles and return as DataFrame with indicator columns."""
        from indicators import add_all_indicators
        tf = timeframe or Config.TIMEFRAME
        try:
            data = self.exchange.fetch_ohlcv(pair, tf, limit=limit)
            df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df = df.set_index("timestamp")
            return add_all_indicators(df)
        except Exception as e:
            logger.error(f"OHLCV fetch failed for {pair}: {e}")
            return pd.DataFrame()

    def get_price(self, pair: str) -> float:
        try:
            ticker = self.exchange.fetch_ticker(pair)
            return float(ticker["last"])
        except Exception as e:
            logger.error(f"Price fetch failed for {pair}: {e}")
            return 0.0

    def place_order(self, pair: str, side: str, size: float, price: float = None) -> dict:
        """
        Place market or limit order.
        DRY_RUN: logs the order but does nothing real.
        """
        order_type = "market" if not price else "limit"
        if self.dry_run:
            order = {
                "id": f"DRY-{pair}-{side}-{size}",
                "symbol": pair, "side": side,
                "size": size, "price": price or self.get_price(pair),
                "status": "simulated",
            }
            logger.info(f"[DRY RUN] {side} {size} {pair} @ {order['price']}")
            return order

        try:
            if order_type == "market":
                order = self.exchange.create_market_order(pair, side, size)
            else:
                order = self.exchange.create_limit_order(pair, side, size, price)
            logger.info(f"Order placed: {side} {size} {pair} @ {price or 'market'} | ID: {order['id']}")
            return order
        except Exception as e:
            logger.error(f"Order failed: {e}")
            raise

    def cancel_order(self, order_id: str, pair: str):
        if self.dry_run:
            logger.info(f"[DRY RUN] Cancel order {order_id}")
            return
        try:
            self.exchange.cancel_order(order_id, pair)
        except Exception as e:
            logger.warning(f"Cancel failed: {e}")
